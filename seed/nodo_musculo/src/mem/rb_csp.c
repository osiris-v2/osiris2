/* * PROYECTO OSIRIS - Implementacion de Nucleo de Memoria
 * Archivo: rb_csp.c
 */

#include "rb_csp.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

// 1. Forja de Bloques Original
RB_SafePtr crear_bloque(uint32_t tam, Hardness dureza) {
    RB_SafePtr ptr;
    ptr.data = malloc(tam);
    ptr.size = tam;
    ptr.hardness = dureza;
    ptr.ref_count = (uint32_t*)malloc(sizeof(uint32_t));
    if (ptr.ref_count) *(ptr.ref_count) = 1;
    
    // Inicializacion de fase para FGN
    ptr.estado = ESTADO_PARTICULA; 
    ptr.coherencia = 1.0;
    
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
        memset(ptr->data, 0, ptr->size); // Blindaje Uranio
        free(ptr->data);
        free(ptr->ref_count);
        ptr->data = NULL;
        ptr->ref_count = NULL;
        ptr->estado = ESTADO_VOID;
        printf("[MEM] Bloque fundido con exito.\n");
    }
}

void rb_rescale(RB_SafePtr* ptr, uint32_t nuevo_tam) {
    if (!ptr || !ptr->data || ptr->estado == ESTADO_BIFURCADO) return;
    void* temp = realloc(ptr->data, nuevo_tam);
    if (temp) {
        ptr->data = temp;
        ptr->size = nuevo_tam;
    }
}

// ====================================================
// FUNCIONES DE FASE (Las que daban error de ld)
// ====================================================

// BIFURCACION: Crea la ilusion de dos particulas compartiendo memoria
void rb_bifurcar_onda(RB_SafePtr* original, RB_SafePtr* alfa, RB_SafePtr* beta) {
    if (!original || original->estado != ESTADO_PARTICULA) return;

    // Alfa y Beta apuntan al mismo bloque fisico
    *alfa = *original;
    *beta = *original;

    // El contador de referencias sube porque ahora hay dos "observadores"
    rb_adquirir(original); 

    alfa->estado = ESTADO_BIFURCADO;
    beta->estado = ESTADO_BIFURCADO;
    alfa->coherencia = 0.5;
    beta->coherencia = 0.5;

    printf("[CUANTICO] Particula bifurcada. Referencias: %u\n", *(original->ref_count));
}

// COLAPSO: Unifica las ondas y reduce las referencias
bool rb_colapsar_observacion(RB_SafePtr* alfa, RB_SafePtr* beta, RB_SafePtr* resultado) {
    if (!alfa || !beta || alfa->data != beta->data) {
        printf("[ERROR] Incoherencia fatal: Las ondas no comparten origen.\n");
        return false;
    }

    // El resultado vuelve a ser una particula solida
    *resultado = *alfa;
    resultado->estado = ESTADO_PARTICULA;
    resultado->coherencia = 1.0;

    // Liberamos una de las referencias ya que volvemos a ser uno
    // (pero no liberamos la memoria porque ref_count todavia sera > 0)
    uint32_t* rc = alfa->ref_count;
    (*rc)--; 

    printf("[MEM] Colapso exitoso. Referencias restantes: %u\n", *rc);
    return true;
}