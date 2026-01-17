/* ASCII PURO - PROYECTO OSIRIS */
#ifndef FGN_RUNTIME_H
#define FGN_RUNTIME_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>  // Para NULL

#define FIRMA_OSIRIS 0xDEADBEEF
#define MAX_HANDLERS 1024

typedef struct {
    void* base_fisica;
    uint32_t tamano_total;
    bool activo;
} OsirisHandler;

// Declaracion externa para que los drivers la vean
extern OsirisHandler h_table[MAX_HANDLERS];

#endif /* FGN_RUNTIME_H */