#ifndef URANIO_H
#define URANIO_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define URANIO_ALIGN 32
#define URANIO_SIG   0x5552414E 

typedef struct {
    uint8_t *ptr_real;
    size_t tamanio;
    size_t posicion;
    uint32_t firma;     // Asegurar que este campo existe aqui
    uint32_t checksum;
} RB_SafePtr;

typedef enum {
    URANIO_OK = 0,
    URANIO_ERROR_OVERFLOW = 1,
    URANIO_ERROR_NULL = 2,
    URANIO_ERROR_INTEGRIDAD = 3,
    URANIO_ERROR_ALIGN = 4
} UranioStatus;

// Nota el 'const' en data para coincidir con la implementacion
UranioStatus uranio_escribir(RB_SafePtr *sptr, const uint8_t *data, size_t tam);

#endif