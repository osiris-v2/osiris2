#include "acero_interfaz.h"
#include "quickjs.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

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

/* ── Sanitizador UTF-8 → ASCII para entrada ODS ──────────────────────────
 * El terminal o el ODS puede introducir comillas tipograficas UTF-8 que
 * QuickJS rechaza con "invalid UTF-8 sequence" o "unexpected character".
 * Sustituye las secuencias multibyte mas comunes por su equivalente ASCII:
 *
 *   U+2018 '  (0xE2 0x80 0x98)  →  '  (0x27)   comilla simple izq
 *   U+2019 '  (0xE2 0x80 0x99)  →  '  (0x27)   comilla simple der / apostrofo
 *   U+201C "  (0xE2 0x80 0x9C)  →  "  (0x22)   comilla doble izq
 *   U+201D "  (0xE2 0x80 0x9D)  →  "  (0x22)   comilla doble der
 *   U+2013 –  (0xE2 0x80 0x93)  →  -  (0x2D)   guion largo
 *   U+2014 —  (0xE2 0x80 0x94)  →  -  (0x2D)   guion em
 *
 * Cualquier otro byte no-ASCII (>= 0x80) se descarta — JS no lo necesita.
 * El buffer de salida nunca supera el tamaño del original. */
static void fgn_sanitizar_js(const char *src, char *dst, size_t dst_max) {
    const unsigned char *s = (const unsigned char *)src;
    size_t out = 0;
    while (*s && out < dst_max - 1) {
        /* Secuencias E2 80 xx — bloque de puntuacion unicode */
        if (s[0] == 0xE2 && s[1] == 0x80) {
            switch (s[2]) {
                case 0x98: case 0x99:           /* ' '  → ' */
                    dst[out++] = '\''; s += 3; break;
                case 0x9C: case 0x9D:           /* " "  → " */
                    dst[out++] = '"';  s += 3; break;
                case 0x93: case 0x94:           /* – —  → - */
                    dst[out++] = '-';  s += 3; break;
                default:
                    s += 3; break;              /* descarta secuencia desconocida */
            }
        } else if (s[0] >= 0x80) {
            /* Cualquier otro multibyte: avanzar segun longitud UTF-8 */
            int skip = (s[0] >= 0xF0) ? 4 :
                       (s[0] >= 0xE0) ? 3 :
                       (s[0] >= 0xC0) ? 2 : 1;
            s += skip;
        } else {
            dst[out++] = (char)s[0];
            s++;
        }
    }
    dst[out] = '\0';
}

// --- MANEJO DE COMANDOS FGN (Cerebro -> Nodo) ---
void manejar_comando_fgn_js(const char *script_fgn) {
    if (!ctx) return;

    /* Sanitizar antes de evaluar — elimina comillas tipograficas y
     * cualquier byte no-ASCII que QuickJS no pueda parsear. */
    size_t len = strlen(script_fgn);
    char *script_limpio = (char *)malloc(len + 1);
    if (!script_limpio) return;
    fgn_sanitizar_js(script_fgn, script_limpio, len + 1);

    /* Diagnostico: mostrar hex de los primeros bytes si hay error de parse */
    printf("\x1b[35m[JS] Script (%zu bytes): ", strlen(script_limpio));
    for (size_t i = 0; i < strlen(script_limpio) && i < 80; i++) {
        unsigned char c = (unsigned char)script_limpio[i];
        if (c >= 32 && c < 127) putchar(c);
        else printf("\\x%02X", c);
    }
    printf("\x1b[0m\n");

    // Evaluacion segura del Bytecode/Script enviado por ODS
    JSValue result = JS_Eval(ctx, script_limpio, strlen(script_limpio),
                             "fgn_input", JS_EVAL_TYPE_GLOBAL);
    free(script_limpio);
    
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