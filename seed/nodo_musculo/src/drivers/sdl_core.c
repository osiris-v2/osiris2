/* PROYECTO OSIRIS - DRIVER DE VIDEO INTEGRADO
 * MODO: PERSISTENCIA SILENCIOSA (CONFIGURACION)
 * ASCII PURO - SIN ACENTOS - DUREZA 256
 */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include "../include/osiris_hw.h"
#include "../include/fgn_runtime.h"

// Encapsulamiento del hardware (Privado del modulo)
static struct {
    SDL_Window* win;
    SDL_Renderer* ren;
    SDL_Texture* tex;
    bool          inicializado;
    bool          visible;      // Control de estado para persistencia
} VidContext = {NULL, NULL, NULL, false, false};

// --- FASE 1: SONDA ---
void probe_video_capacidades(OsirisHardwareMap *map) {
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        map->soporte_sdl2 = false;
        map->soporte_opengl = false;
        return;
    }

    map->soporte_sdl2 = true;
    SDL_DisplayMode dm;
    if (SDL_GetCurrentDisplayMode(0, &dm) == 0) {
        map->pantalla_ancho = (uint16_t)dm.w;
        map->pantalla_alto = (uint16_t)dm.h;
        
        // Prueba rapida de aceleracion
        SDL_Window *test = SDL_CreateWindow("Probe", 0, 0, 1, 1, SDL_WINDOW_OPENGL | SDL_WINDOW_HIDDEN);
        map->soporte_opengl = (test != NULL);
        if (test) SDL_DestroyWindow(test);
    }
    
    SDL_Quit(); 
}

// --- FASE INTERNA: GESTION DE EVENTOS SILENCIOSOS ---
static void gestionar_persistencia_eventos() {
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) {
            // En lugar de cerrar, ocultamos y marcamos Standby
            SDL_HideWindow(VidContext.win);
            VidContext.visible = false;
            printf("[MODO CONFIG] Espejo oculto. Persistencia Uranio activa.\n");
        }
    }
}

// --- FASE 2: MOTOR DE ESPEJO (Dureza 256 con Persistencia) ---
void materializar_mirror_sdl(OsirisHardwareMap *map, uint16_t id_handler) {
    if (!map->soporte_sdl2) return;

    // 1. Inicializacion o Re-activacion
    if (!VidContext.inicializado) {
        SDL_Init(SDL_INIT_VIDEO);
        VidContext.win = SDL_CreateWindow("NODO OSIRIS - FGN", 
                            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 
                            map->pantalla_ancho, map->pantalla_alto, 0);
        
        VidContext.ren = SDL_CreateRenderer(VidContext.win, -1, SDL_RENDERER_ACCELERATED);
        VidContext.tex = SDL_CreateTexture(VidContext.ren, SDL_PIXELFORMAT_ARGB8888, 
                                          SDL_TEXTUREACCESS_STREAMING, 
                                          map->pantalla_ancho, map->pantalla_alto);
        VidContext.inicializado = true;
        VidContext.visible = true;
    }

    // Procesamos eventos para detectar si el usuario intenta cerrar
    gestionar_persistencia_eventos();

    // 2. Acceso via Handler (Secure Pointer Check)
    if (id_handler < MAX_HANDLERS && h_table[id_handler].activo) {
        // Forzamos visibilidad si llega un pulso y estabamos ocultos (Opcional)
        // if (!VidContext.visible) { SDL_ShowWindow(VidContext.win); VidContext.visible = true; }

        void* pixels;
        int pitch;
        
        if (SDL_LockTexture(VidContext.tex, NULL, &pixels, &pitch) == 0) {
            // Sincronizacion fisica de bits: Uranio -> Interfaz
            // La copia ocurre SIEMPRE para mantener el buffer actualizado
            memcpy(pixels, h_table[id_handler].base_fisica, h_table[id_handler].tamano_total);
            SDL_UnlockTexture(VidContext.tex);
            
            // Solo dibujamos en GPU si la ventana es visible (Ahorro de recursos)
            if (VidContext.visible) {
                SDL_RenderCopy(VidContext.ren, VidContext.tex, NULL, NULL);
                SDL_RenderPresent(VidContext.ren);
            }
        }
    }
}