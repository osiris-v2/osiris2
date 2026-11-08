/* ================================================================
 * PROYECTO OSIRIS - osiris_js_bridge.c
 * PUENTE DE ORQUESTACION Y SCRIPTING (QUICKJS)
 *
 * RESPONSABILIDADES:
 *   1. Inicializar y destruir el runtime y contexto de QuickJS.
 *   2. Exponer funciones nativas de C al entorno JavaScript.
 *   3. Sanitizar de forma estricta las cadenas de entrada (purga de UTF-8
 *      multibyte problemático y comillas tipográficas) antes de evaluar[span_2](start_span)[span_2](end_span).
 *   4. Evaluar scripts o bytecode de forma segura evitando fugas de memoria
 *      y gestionando excepciones de forma limpia[span_3](start_span)[span_3](end_span).
 *
 * DUREZA 256 - ASCII PURO
 * ================================================================ */

#include "acero_interfaz.h"
#include "quickjs.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Referencia al driver de video activo */
extern OsirisVideoDriver driver_activo;

/* Persistencia de motor (Encapsulado para evitar variables globales sueltas) */
static JSRuntime *rt = NULL;
static JSContext *ctx = NULL;

/* --- ACCESO SEGURO AL CONTEXTO --- */
JSContext *obtener_contexto_osiris(void) {
    return ctx; 
}

/* --- FUNCIONES NATIVAS (C -> JS) --- */
static JSValue js_osiris_dibujar_texto(JSContext *ctx, JSValueConst this_val, int argc, JSValueConst *argv) {
    if (argc < 3) return JS_EXCEPTION;

    const char *texto = JS_ToCString(ctx, argv[0]);
    int x, y;
    JS_ToInt32(ctx, &x, argv[1]);
    JS_ToInt32(ctx, &y, argv[2]);

    if (driver_activo.dibujar_overlay && texto) {
        printf("> ODS_JS_EXEC: [%s] @ (%d, %d)\n", texto, x, y);
    }

    if (texto) JS_FreeCString(ctx, texto);
    return JS_UNDEFINED;
}

/* --- INICIALIZACION DEL MOTOR --- */
void inicializar_motor_osiris(void) {
    if (rt || ctx) return; /* Evitar doble inicialización */

    rt = JS_NewRuntime();
    if (!rt) return;

    ctx = JS_NewContext(rt);
    if (!ctx) {
        JS_FreeRuntime(rt);
        rt = NULL;
        return;
    }
    
    JSValue global_obj = JS_GetGlobalObject(ctx);
    
    /* Registro de comandos FGN expuestos a JS */
    JS_SetPropertyStr(ctx, global_obj, "osiris_dibujar_texto",
        JS_NewCFunction(ctx, js_osiris_dibujar_texto, "dibujar_texto", 3));
        
    JS_FreeValue(ctx, global_obj);
    printf("[SISTEMA] Motor QuickJS Inicializado (Dureza 256)\n");
}

/* ── Sanitizador UTF-8 → ASCII Estricto para ODS ──────────────────────────
 * Elimina comillas tipográficas u otros caracteres multibyte que QuickJS
 * rechaza con errores de sintaxis inesperados[span_4](start_span)[span_4](end_span). Convierte bytes especiales
 * a equivalentes ASCII seguros y descarta el resto[span_5](start_span)[span_5](end_span).
 * ======================================================================== */
static void fgn_sanitizar_js(const char *src, char *dst, size_t dst_max) {
    if (!src || !dst || dst_max == 0) return;

    const unsigned char *s = (const unsigned char *)src;
    size_t out = 0;
    while (*s && out < dst_max - 1) {
        if (s[0] == 0xE2 && s[1] == 0x80) {
            switch (s[2]) {
                case 0x98: case 0x99: dst[out++] = '\''; s += 3; break; /* Comilla simple */
                case 0x9C: case 0x9D: dst[out++] = '"';  s += 3; break; /* Comilla doble */
                case 0x93: case 0x94: dst[out++] = '-';  s += 3; break; /* Guiones largos */
                default: s += 3; break;
            }
        } else if (s[0] >= 0x80) {
            int skip = (s[0] >= 0xF0) ? 4 : (s[0] >= 0xE0) ? 3 : (s[0] >= 0xC0) ? 2 : 1;
            s += skip;
        } else {
            dst[out++] = (char)s[0];
            s++;
        }
    }
    dst[out] = '\0';
}

/* --- MANEJO DE COMANDOS FGN (Cerebro -> Nodo) --- */
void manejar_comando_fgn_js(const char *script_fgn) {
    if (!ctx || !script_fgn) return;

    size_t len = strlen(script_fgn);
    char *script_limpio = (char *)malloc(len + 1);
    if (!script_limpio) return;

    /* Purga y saneamiento de la cadena antes de la evaluación */
    fgn_sanitizar_js(script_fgn, script_limpio, len + 1);
    size_t len_limpia = strlen(script_limpio);

    printf("\x1b[35m[JS] Evaluando script limpio (%zu bytes)\x1b[0m\n", len_limpia);

    /* Evaluación de la expresión en el contexto global[span_6](start_span)[span_6](end_span) */
    JSValue result = JS_Eval(ctx, script_limpio, len_limpia,
                             "fgn_input", JS_EVAL_TYPE_GLOBAL);
    
    free(script_limpio);
    
    /* Captura y gestión segura de excepciones del intérprete[span_7](start_span)[span_7](end_span) */
    if (JS_IsException(result)) {
        JSValue exception = JS_GetException(ctx);
        const char *msg = JS_ToCString(ctx, exception);
        printf("\x1b[31m!!! ERROR FGN-JS: %s\x1b[0m\n", msg ? msg : "desconocido");
        if (msg) JS_FreeCString(ctx, msg);
        JS_FreeValue(ctx, exception);
    }
    JS_FreeValue(ctx, result);
}

/* --- CIERRE Y LIBERACION DEL MOTOR --- */
void cerrar_motor_osiris(void) {
    if (ctx) {
        JS_FreeContext(ctx);
        ctx = NULL;
    }
    if (rt) {
        JS_FreeRuntime(rt);
        rt = NULL;
    }
    printf("[SISTEMA] Motor QuickJS cerrado correctamente.\n");
}
