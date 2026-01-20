#include "acero_interfaz.h"
#include "quickjs.h"
#include <stdio.h>
#include <string.h>

// Referencia al driver de video
extern OsirisVideoDriver driver_activo;

// PERSISTENCIA DE MOTOR (Encapsulado para evitar basura en main)
static JSRuntime *rt = NULL;
static JSContext *ctx = NULL;

// --- ACCESO SEGURO AL CONTEXTO ---
JSContext *obtener_contexto_osiris(void) {
    return ctx; 
}

// --- FUNCIONES NATIVAS (C -> JS) ---
static JSValue js_osiris_dibujar_texto(JSContext *ctx, JSValueConst this_val, int argc, JSValueConst *argv) {
    // RB_SafePtr: Validacion de entrada antes de procesar
    if (argc < 3) return JS_EXCEPTION;

    const char *texto = JS_ToCString(ctx, argv[0]);
    int x, y;
    JS_ToInt32(ctx, &x, argv[1]);
    JS_ToInt32(ctx, &y, argv[2]);

    if (driver_activo.dibujar_overlay) {
        // El driver legacy de la GTX 550 Ti recibe la orden aqui
        printf("> ODS_JS_EXEC: [%s] @ (%d, %d)\n", texto, x, y);
    }

    JS_FreeCString(ctx, texto);
    return JS_UNDEFINED;
}

// --- INICIALIZACION DEL MOTOR ---
void inicializar_motor_osiris(void) {
    rt = JS_NewRuntime();
    ctx = JS_NewContext(rt);
    
    JSValue global_obj = JS_GetGlobalObject(ctx);
    
    // Registro de comandos FGN
    JS_SetPropertyStr(ctx, global_obj, "osiris_dibujar_texto",
        JS_NewCFunction(ctx, js_osiris_dibujar_texto, "dibujar_texto", 3));
        
    JS_FreeValue(ctx, global_obj);
    printf("[SISTEMA] Motor QuickJS 2025 Inicializado (Dureza 256)\n");
}

// --- MANEJO DE COMANDOS FGN (Cerebro -> Nodo) ---
void manejar_comando_fgn_js(const char *script_fgn) {
    if (!ctx) return;

    // Evaluacion segura del Bytecode/Script enviado por ODS
    JSValue result = JS_Eval(ctx, script_fgn, strlen(script_fgn), "fgn_input", JS_EVAL_TYPE_GLOBAL);
    
    if (JS_IsException(result)) {
        JSValue exception = JS_GetException(ctx);
        const char *msg = JS_ToCString(ctx, exception);
        printf("!!! ERROR FGN-JS: %s\n", msg);
        
        JS_FreeCString(ctx, msg);
        JS_FreeValue(ctx, exception);
    }
    JS_FreeValue(ctx, result);
}

void cerrar_motor_osiris(void) {
    if (ctx) JS_FreeContext(ctx);
    if (rt) JS_FreeRuntime(rt);
}