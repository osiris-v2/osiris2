#ifndef URANIO_H
#define URANIO_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// Estructura de Puntero Seguro (RB_SafePtr)
typedef struct {
    uint8_t *ptr_real;      // Direccion fisica de memoria
    size_t tamanio;         // Limite maximo (Dureza 256)
    size_t posicion;        // Cursor de lectura/escritura
    uint32_t checksum;      // Verificacion de integridad
} RB_SafePtr;

// Codigos de error de Uranio
typedef enum {
    URANIO_OK = 0,
    URANIO_ERROR_OVERFLOW = 1,
    URANIO_ERROR_NULL = 2,
    URANIO_ERROR_INTEGRIDAD = 3
} UranioStatus;

// Prototipos de funciones seguras
RB_SafePtr uranio_crear(size_t tam);
UranioStatus uranio_escribir(RB_SafePtr *sptr, uint8_t *data, size_t tam);
UranioStatus uranio_leer(RB_SafePtr *sptr, uint8_t *dest, size_t tam);
void uranio_liberar(RB_SafePtr *sptr);

#endif