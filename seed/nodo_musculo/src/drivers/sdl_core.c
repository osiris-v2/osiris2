/* ================================================================
 * PROYECTO OSIRIS - sdl_core.c
 * SONDA DE VIDEO Y MOTOR DE ESPEJO VIA SLOTS FGN
 *
 * RESPONSABILIDADES:
 *   1. probe_video_capacidades() — detecta capacidades del HW
 *      sin efectos secundarios. Lee, no crea ventanas.
 *   2. materializar_mirror_sdl() — sincroniza un handler de
 *      h_table con un slot FGN. No crea ventanas propias.
 *      Toda creacion/destruccion pasa por osiris_windows.c.
 *
 * LO QUE YA NO HACE ESTE ARCHIVO:
 *   - VidContext estatico privado (eliminado)
 *   - SDL_CreateWindow / SDL_CreateRenderer / SDL_CreateTexture
 *   - SDL_PollEvent (monopolio del SDL_THREAD en osiris_windows.c)
 *   - gestionar_persistencia_eventos() — el FLUSH_THREAD lo hace
 *
 * INVARIANTE:
 *   materializar_mirror_sdl() es seguro llamar desde cualquier
 *   hilo — solo escribe en bloque DIAMANTE del slot y encola
 *   SDL_CMD_RENDER_FRAME. No toca la API SDL directamente.
 *
 * RELACION CON EL LENGUAJE FGN:
 *   h_table[id] es el namespace fisico del lenguaje.
 *   materializar_mirror_sdl() es el precursor de:
 *     nodo[slot].enviar<OP_RENDER_FRAME>(h_table[id]);
 *
 * DUREZA 256 - ASCII PURO
 * ================================================================ */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include "../include/osiris_hw.h"
#include "../include/fgn_runtime.h"

/* ================================================================
 * FASE 1: SONDA DE VIDEO
 *
 * Lee capacidades del hardware de video sin efectos secundarios.
 * Crea una ventana de prueba minima, lee lo que necesita, destruye.
 *
 * NOTA: SDL_Quit() al final es seguro porque fgn_windows_iniciar()
 * llamara SDL_Init(SDL_INIT_VIDEO) de nuevo cuando arranque.
 * Si SDL ya esta inicializado, SDL_Init() es idempotente.
 *
 * LLAMAR: desde main() antes de fgn_windows_iniciar(), o desde
 * op_hwprobe como parte del probe completo del sistema.
 * ================================================================ */
void probe_video_capacidades(OsirisHardwareMap *map) {
    if (!map) return;

    /* SDL puede estar ya inicializado por fgn_windows_iniciar().
     * SDL_WasInit evita un doble-init que reiniciaria el subsistema. */
    bool sdl_ya_activo = (SDL_WasInit(SDL_INIT_VIDEO) != 0);

    if (!sdl_ya_activo) {
        if (SDL_Init(SDL_INIT_VIDEO) < 0) {
            map->soporte_sdl2   = false;
            map->soporte_opengl = false;
            printf("\x1b[31m[PROBE] SDL_Init fallo: %s\x1b[0m\n", SDL_GetError());
            return;
        }
    }

    map->soporte_sdl2 = true;

    /* Resolución de pantalla principal */
    SDL_DisplayMode dm;
    if (SDL_GetCurrentDisplayMode(0, &dm) == 0) {
        map->pantalla_ancho = (uint16_t)dm.w;
        map->pantalla_alto  = (uint16_t)dm.h;
    }

    /* Prueba de aceleracion: ventana 1x1 oculta con flag OPENGL.
     * Si SDL puede crearla, el driver OpenGL esta disponible. */
    SDL_Window *test = SDL_CreateWindow(
        "probe", 0, 0, 1, 1,
        SDL_WINDOW_OPENGL | SDL_WINDOW_HIDDEN
    );
    map->soporte_opengl = (test != NULL);
    if (test) SDL_DestroyWindow(test);

    /* Actualizar campos FGN con el estado actual del sistema de slots */
    uint8_t slots_activos = 0;
    for (int i = 0; i < MAX_FGN_WINDOWS; i++) {
        if (fgn_wins[i].activa) slots_activos++;
    }
    map->fgn_slots_activos = slots_activos;
    map->fgn_slots_max     = (uint8_t)MAX_FGN_WINDOWS;

    /* Solo cerramos SDL si fuimos nosotros quienes lo abrimos */
    if (!sdl_ya_activo) SDL_Quit();

    printf("\x1b[32m[PROBE] Video: SDL2=%s OpenGL=%s %ux%u slots=%u/%u\x1b[0m\n",
           map->soporte_sdl2   ? "SI" : "NO",
           map->soporte_opengl ? "SI" : "NO",
           map->pantalla_ancho, map->pantalla_alto,
           map->fgn_slots_activos, map->fgn_slots_max);
}


/* ================================================================
 * FASE 2: MOTOR DE ESPEJO VIA SLOTS FGN
 *
 * Sincroniza el contenido de h_table[id_handler] con el slot
 * SDL de destino. El caller especifica el slot_destino; si es
 * -1, se usa el primer slot activo no-HUD con textura.
 *
 * FLUJO:
 *   1. Validar handler y slot
 *   2. Verificar que el bloque del handler cabe en el slot
 *   3. memcpy handler -> bloque DIAMANTE del slot
 *   4. Encolar SDL_CMD_RENDER_FRAME — el SDL_THREAD lo renderiza
 *
 * GARANTIAS:
 *   - No toca SDL directamente — seguro desde cualquier hilo
 *   - Si el slot no tiene textura, la funcion es no-op
 *   - Si el handler no esta activo, la funcion es no-op
 *   - El bloque DIAMANTE del slot se sobreescribe atomicamente
 *     (memcpy de bloque contiguo — no hay estado intermedio visible)
 *
 * NOTA SOBRE PERSISTENCIA SILENCIOSA:
 *   El comportamiento anterior (ocultar ventana en SDL_QUIT) ahora
 *   lo gestiona el SDL_THREAD en osiris_windows.c mediante
 *   FGN_WIN_FLAG_PERSISTENTE. Para activarlo en un slot:
 *     fgn_wins[slot].flags |= FGN_WIN_FLAG_PERSISTENTE;
 * ================================================================ */
void materializar_mirror_sdl(OsirisHardwareMap *map, uint16_t id_handler) {
    if (!map || !map->soporte_sdl2) return;

    /* Validar handler */
    if (id_handler >= MAX_HANDLERS) {
        printf("\x1b[31m[MIRROR] id_handler %u fuera de rango "
               "(MAX=%d)\x1b[0m\n", id_handler, MAX_HANDLERS);
        return;
    }

    if (!h_table[id_handler].activo) {
        printf("\x1b[33m[MIRROR] Handler %u inactivo.\x1b[0m\n",
               id_handler);
        return;
    }

    if (!h_table[id_handler].base_fisica ||
         h_table[id_handler].tamano_total == 0) {
        printf("\x1b[31m[MIRROR] Handler %u sin datos fisicos.\x1b[0m\n",
               id_handler);
        return;
    }

    /* Buscar slot destino: primer slot activo no-HUD con textura */
    int slot = -1;
    for (int i = 1; i < MAX_FGN_WINDOWS; i++) {
        if (FGN_SLOT_VALIDO(i) &&
            fgn_wins[i].tex   &&
            fgn_wins[i].visible) {
            slot = i;
            break;
        }
    }

    if (slot < 0) {
        /* No hay slot disponible todavia — puede ocurrir si el Cerebro
         * envia datos antes de que el SDL_THREAD haya procesado
         * SDL_CMD_WIN_CREAR. No es un error — el frame se descarta. */
        return;
    }

    FgnWinEntry *w = &fgn_wins[slot];

    /* Verificar que el handler cabe en el bloque DIAMANTE del slot.
     * Si el handler es mas grande, rescalamos el bloque. */
    uint32_t bytes_handler = h_table[id_handler].tamano_total;

    if (bytes_handler > w->bloque.size) {
        /* El bloque DIAMANTE necesita crecer.
         * rb_rescale solo opera en ESTADO_PARTICULA — guardia incluida. */
        if (w->bloque.estado != ESTADO_PARTICULA) {
            printf("\x1b[31m[MIRROR] Bloque slot %d en estado "
                   "no rescalable (%d).\x1b[0m\n",
                   slot, (int)w->bloque.estado);
            return;
        }
        rb_rescale(&w->bloque, bytes_handler);
        if (!w->bloque.data || w->bloque.size < bytes_handler) {
            printf("\x1b[31m[MIRROR] rb_rescale fallo en slot %d.\x1b[0m\n",
                   slot);
            return;
        }
        printf("\x1b[33m[MIRROR] Bloque slot %d rescalado a %u bytes.\x1b[0m\n",
               slot, bytes_handler);
    }

    /* Sincronizacion fisica: handler -> bloque DIAMANTE del slot.
     * Este memcpy es la unica operacion de escritura en este modulo.
     * El SDL_THREAD leerá el bloque cuando procese SDL_CMD_RENDER_FRAME. */
    memcpy(w->bloque.data,
           h_table[id_handler].base_fisica,
           bytes_handler);

    /* Encolar render — no bloqueante, no toca SDL */
    SdlCmd cmd = {
        .tipo  = SDL_CMD_RENDER_FRAME,
        .slot  = (uint8_t)slot,
        .frame = { .n_bytes = bytes_handler }
    };

    if (!sdl_cmd_push(&cmd)) {
        /* Cola llena — el frame se pierde pero el sistema sigue.
         * En Fase 4 el scheduler FDG gestionara la prioridad. */
        printf("\x1b[33m[MIRROR] Cola llena, frame handler %u descartado.\x1b[0m\n",
               id_handler);
    }
}