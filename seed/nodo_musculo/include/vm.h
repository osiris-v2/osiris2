#ifndef VM_H
#define VM_H

#include <stdint.h>       // Para uint8_t
#include "rb_csp.h" // Para RB_SafePtr

void osiris_vm_exec(uint8_t* bytecode, RB_SafePtr* block);

#endif