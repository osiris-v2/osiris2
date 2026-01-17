#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "vm.h"
#include "../mem/rb_csp.h"

void osiris_vm_exec(uint8_t* bytecode, RB_SafePtr* block) {
    // Tabla de Saltos (Dureza Diamante)
    static void* dispatch_table[] = {
        &&op_nop,      // 0x00
        &&op_load,     // 0x01
        &&op_telemetry,// 0x02
        &&op_dispatch, // 0x03
        &&op_panic,    // 0x04
        &&op_rescale   // 0x05
    };

    uint8_t* pc = bytecode;
    rb_adquirir(block); // Proteccion del bloque

next_op:
    uint8_t opcode = *pc++;
    if (opcode > 0x05) goto *dispatch_table[4]; // Panic si es invalido

    goto *dispatch_table[opcode];

op_nop:
    goto next_op;

op_load:
    printf("[VM] Bloque cargado para proceso.\n");
    goto next_op;

op_telemetry:
    printf("[VM] Telemetria inyectada.\n");
    goto next_op;

op_dispatch:
    printf("[VM] Despachando a servidor propio.\n");
    goto exit_vm;

op_rescale: {
    uint32_t nuevo_tam;
    memcpy(&nuevo_tam, pc, sizeof(uint32_t));
    
    // Simplemente escalamos el bloque actual. 
    // No tocamos ref_count porque el "dueño" sigue siendo el mismo.
    rb_rescale(block, nuevo_tam);
    
    pc += 4;
    goto next_op;
}

op_panic:
    printf("[CRITICAL] PANIC: Instruccion no autorizada.\n");

exit_vm:
    rb_liberar(block);
}