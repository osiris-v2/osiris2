#ifndef ACERO_INTERFAZ_H
#define ACERO_INTERFAZ_H

#include <stdint.h>
#include "rb_csp.h" 

typedef struct {
    char* nombre_driver;
    int (*iniciar)(int ancho, int alto);
    void (*renderizar_frame)(RB_SafePtr frame_data); 
    void (*dibujar_overlay)(const char* texto, int x, int y); // Ajustado para el Bridge JS
    void (*cerrar)();
} OsirisVideoDriver;

// Declarar que existe un driver activo en algun lugar (acero_loader.c)
extern OsirisVideoDriver driver_activo;

#endif