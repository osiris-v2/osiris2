#include "../../include/acero_interfaz.h"
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>

static SDL_Window* ventana = NULL;
static SDL_GLContext contexto = NULL;

int gl_legacy_iniciar(int ancho, int alto) {
    if (SDL_Init(SDL_INIT_VIDEO) < 0) return 0;

    // Forzamos OpenGL 2.1 para maxima compatibilidad con Fermi (GTX 550 Ti)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1);

    ventana = SDL_CreateWindow("V-GHOST ODS", SDL_WINDOWPOS_CENTERED, 
                               SDL_WINDOWPOS_CENTERED, ancho, alto, 
                               SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN);
    
    contexto = SDL_GL_CreateContext(ventana);
    return (contexto != NULL);
}

void gl_legacy_renderizar(RB_SafePtr frame_data) {
    if (!frame_data.data) return;

    // BLOQUE DE SEGURIDAD URANIO:
    // Solo accedemos si el puntero es valido segun tu sistema rb_csp
    // Aqui se subiria la textura a OpenGL 2.1
}

// Asegurate de que la estructura se cargue asi:
OsirisVideoDriver cargar_driver_gl_legacy() {
    OsirisVideoDriver driver;
    driver.nombre_driver = "OpenGL 2.1 Legacy";
    driver.iniciar = gl_legacy_iniciar;
    driver.renderizar_frame = gl_legacy_renderizar;
    driver.dibujar_overlay = NULL; // Se asignara via JS Bridge despues
    driver.cerrar = NULL;
    return driver;
}