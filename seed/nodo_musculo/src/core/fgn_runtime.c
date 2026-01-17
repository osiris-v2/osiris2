#include "fgn_runtime.h"
#include <stddef.h>

// Definicion fisica de la tabla Uranio
OsirisHandler h_table[MAX_HANDLERS];

void inicializar_handlers() {
    for (int i = 0; i < MAX_HANDLERS; i++) {
        h_table[i].activo = false;
        h_table[i].base_fisica = NULL; 
        h_table[i].tamano_total = 0;
    }
}