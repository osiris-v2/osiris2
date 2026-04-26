/* ================================================================
 * PROYECTO OSIRIS - acero_gl_legacy.c
 * DRIVER V-GHOST HUD — RENDER PURO SIN VENTANA PROPIA
 *
 * RESPONSABILIDAD UNICA:
 *   Exponer cargar_driver_gl_legacy() con punteros de funcion
 *   para renderizar y dibujar overlay.
 *   La ventana vive en fgn_wins[FGN_SLOT_HUD] — creada y
 *   destruida por osiris_windows.c, no por este modulo.
 *
 * LO QUE YA NO HACE ESTE ARCHIVO (movido a osiris_windows.c):
 *   - SDL_Init / SDL_CreateWindow / SDL_CreateRenderer
 *   - Gestion de eventos SDL (SDL_PollEvent)
 *   - Variables estaticas de ventana (hud_win, hud_ren)
 *   - Ciclo de vida: lo gestiona el SDL_THREAD via fgn_wins[0]
 *
 * RELACION CON EL LENGUAJE FGN:
 *   OsirisVideoDriver es el precursor del tipo interfaz FGN:
 *     interfaz<ACERO> VideoDriver {
 *         fn iniciar(ancho, alto) -> bool;
 *         fn renderizar_frame(bloque<URANIO>);
 *         fn dibujar_overlay(texto, x, y);
 *         fn cerrar();
 *     }
 *   cargar_driver_gl_legacy() es una implementacion concreta
 *   que el sistema registra en driver_activo al arranque.
 *
 * DUREZA 256 - ASCII PURO
 * ================================================================ */

#include "../../include/acero_interfaz.h"
#include "../../include/fgn_runtime.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

/* ================================================================
 * FUENTE BITMAP 5x7
 * Declarada extern — la definicion maestra esta en osiris_windows.c
 * para evitar duplicar 95 glifos. Si se compila este modulo solo
 * (tests unitarios), descomentar la definicion local aqui.
 * ================================================================ */

/* ================================================================
 * FUNCIONES DE RENDER — operan sobre fgn_wins[FGN_SLOT_HUD]
 * Solo se llaman desde SDL_THREAD (via SDL_CMD_RENDER_HUD).
 * No acceden a ningun estado estatico de ventana.
 * ================================================================ */

/* iniciar() — en el nuevo modelo, la ventana ya existe en slot 0
 * cuando este driver se registra. La funcion solo verifica que
 * el slot este activo y devuelve 1 si todo esta listo.
 * ancho/alto son ignorados — los fija osiris_windows al crear el HUD. */
static int gl_legacy_iniciar(int ancho, int alto) {
    (void)ancho; (void)alto;

    /* El HUD debe haber sido creado por fgn_windows_iniciar() */
    if (!fgn_wins[FGN_SLOT_HUD].activa) {
        printf("\x1b[31m[ACERO] HUD slot 0 no activo — "
               "llamar fgn_windows_iniciar() primero.\x1b[0m\n");
        return 0;
    }

    printf("\x1b[32m[ACERO] Driver V-Ghost vinculado a slot 0.\x1b[0m\n");
    return 1;
}

/* renderizar_frame() — el frame_data de un slot de video puede
 * dirigirse al HUD para debug. En produccion esta funcion no
 * hace nada — el HUD tiene su propio ciclo de render en SDL_THREAD.
 * Se mantiene en la interfaz para compatibilidad con OsirisVideoDriver. */
static void gl_legacy_renderizar(RB_SafePtr frame_data) {
    /* Guardias de seguridad */
    if (!frame_data.data || frame_data.estado == ESTADO_VOID) return;
    if (!fgn_wins[FGN_SLOT_HUD].activa) return;

    /* En el modelo actual el HUD no consume frames de video.
     * Si en Fase 4 se quiere un thumbnail del stream en el HUD,
     * aqui se encola SDL_CMD_RENDER_FRAME hacia slot 0. */
    (void)frame_data;
}

/* dibujar_overlay() — texto adicional sobre el HUD, llamado
 * desde el JS bridge (osiris_dibujar_texto).
 * Encola SDL_CMD_OVERLAY_TXT hacia slot 0 — no toca SDL directamente. */
static void gl_legacy_overlay(const char *texto, int x, int y) {
    if (!texto || !fgn_wins[FGN_SLOT_HUD].activa) return;

    uint8_t color_verde[4] = {0, 255, 180, 255};
    fgn_win_overlay(FGN_SLOT_HUD, (int16_t)x, (int16_t)y,
                    texto, color_verde);
}

/* cerrar() — el HUD tiene FGN_WIN_FLAG_SISTEMA, fgn_win_cerrar()
 * ignora el cierre. Este stub existe para completar la interfaz. */
static void gl_legacy_cerrar(void) {
    /* El HUD no se puede cerrar desde el driver.
     * Solo se cierra en el shutdown ordenado via fgn_windows_cerrar(). */
    printf("\x1b[33m[ACERO] cerrar() ignorado — HUD es slot de sistema.\x1b[0m\n");
}

/* ================================================================
 * EXPORTACION DEL DRIVER
 * ================================================================ */

OsirisVideoDriver cargar_driver_gl_legacy(void) {
    OsirisVideoDriver driver;
    driver.nombre_driver    = "V-GHOST HUD (SDL2 slot-0)";
    driver.iniciar          = gl_legacy_iniciar;
    driver.renderizar_frame = gl_legacy_renderizar;
    driver.dibujar_overlay  = gl_legacy_overlay;
    driver.cerrar           = gl_legacy_cerrar;
    return driver;
}