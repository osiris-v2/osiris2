#ifndef ACERO_INTERFAZ_H
#define ACERO_INTERFAZ_H

#include <stdint.h>
#include "rb_csp.h"

typedef struct {
    char* nombre_driver;
    int  (*iniciar)(int ancho, int alto);
    void (*renderizar_frame)(RB_SafePtr frame_data);
    void (*dibujar_overlay)(const char* texto, int x, int y);
    void (*cerrar)(void);
} OsirisVideoDriver;

/* Driver activo — definido en main.c */
extern OsirisVideoDriver driver_activo;

/* Carga el driver V-Ghost HUD (SDL2 slot-0).
 * Implementado en drivers/acero_gl_legacy.c */
OsirisVideoDriver cargar_driver_gl_legacy(void);

#endif /* ACERO_INTERFAZ_H */