#ifndef RB_CSP_H
#define RB_CSP_H

#include <stdint.h>

typedef enum { ACERO, DIAMANTE, URANIO } Hardness;

typedef struct {
    void* data;
    uint32_t size;
    Hardness hardness;
    uint32_t* ref_count;
} RB_SafePtr;

RB_SafePtr crear_bloque(uint32_t tam, Hardness dureza);
void rb_adquirir(RB_SafePtr* ptr);
void rb_liberar(RB_SafePtr* ptr);
// FALTA ESTA LÍNEA:
void rb_rescale(RB_SafePtr* ptr, uint32_t nuevo_tam); 

#endif