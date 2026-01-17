#include "rb_csp.h"
#include <stdlib.h>
#include <stdio.h>

RB_SafePtr crear_bloque(uint32_t tam, Hardness dureza) {
    RB_SafePtr ptr;
    ptr.data = malloc(tam);
    ptr.size = tam;
    ptr.hardness = dureza;
    ptr.ref_count = (uint32_t*)malloc(sizeof(uint32_t));
    *(ptr.ref_count) = 1;
    
    return ptr;
}

void rb_adquirir(RB_SafePtr* ptr) {
    if (ptr && ptr->ref_count) {
        (*(ptr->ref_count))++;
    }
}

void rb_liberar(RB_SafePtr* ptr) {
    if (!ptr || !ptr->ref_count || !ptr->data) return;

    (*(ptr->ref_count))--;
    
    if (*(ptr->ref_count) == 0) {
        free(ptr->data);
        free(ptr->ref_count);
        
        // Blindaje: dejamos rastro nulo para evitar el double free
        ptr->data = NULL; 
        ptr->ref_count = NULL;
        printf("[MEM] Bloque fundido con exito.\n");
    }
}


void rb_rescale(RB_SafePtr* ptr, uint32_t nuevo_tam) {
    if (!ptr || !ptr->data) return;

    void* temp = realloc(ptr->data, nuevo_tam);
    if (temp) {
        ptr->data = temp;
        ptr->size = nuevo_tam;
        printf("[MEM] Bloque reescalado a %u bytes.\n", nuevo_tam);
    } else {
        printf("[ERROR] Fallo de memoria al reescalar.\n");
    }
}