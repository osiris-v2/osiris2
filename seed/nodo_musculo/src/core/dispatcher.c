#include "fgn_runtime.h"
#include <stdio.h>

void despachar_operacion(uint8_t opcode, uint16_t id) {
    // Tabla de saltos para maxima velocidad (Computed Gotos)
    static void* jump_table[] = {
        [0 ... 255] = &&l_default,
        [0x30] = &&l_uranio,
        [0x80] = &&l_mirror
    };

    goto *jump_table[opcode];

l_uranio:
    printf("[DISPATCH] Creando bloque Uranio para ID %u\n", id);
    return;

l_mirror:
    printf("[DISPATCH] Ejecutando Mirroring en ID %u\n", id);
    return;

l_default:
    return;
}