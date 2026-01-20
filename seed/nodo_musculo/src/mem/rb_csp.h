#ifndef RB_CSP_H
#define RB_CSP_H

#include <stdint.h>
#include <stdbool.h>

// Mantenemos su nomenclatura original para no romper el Nodo
typedef enum { ACERO, DIAMANTE, URANIO } Hardness;

// Definimos los estados de fase para que FGN_Math los reconozca
typedef enum { 
    ESTADO_PARTICULA = 0, 
    ESTADO_BIFURCADO = 1, 
    ESTADO_VOID = 2 
} FaseEstado;

typedef struct {
    void* data;
    uint32_t size;
    Hardness hardness;
    uint32_t* ref_count;
    // Extensiones Osiris
    FaseEstado estado;   
    double coherencia;   
} RB_SafePtr;

// Firmas de funcion
RB_SafePtr crear_bloque(uint32_t tam, Hardness dureza);
void rb_adquirir(RB_SafePtr* ptr);
void rb_liberar(RB_SafePtr* ptr);
void rb_rescale(RB_SafePtr* ptr, uint32_t nuevo_tam);

// Soporte para Particula/2
void rb_bifurcar_onda(RB_SafePtr* original, RB_SafePtr* alfa, RB_SafePtr* beta);
bool rb_colapsar_observacion(RB_SafePtr* alfa, RB_SafePtr* beta, RB_SafePtr* resultado);

#endif