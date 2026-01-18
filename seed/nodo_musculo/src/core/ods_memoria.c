/* * PROYECTO OSIRIS - ODS MEMORIA (ESTRATO URANIO)
 * SINTAXIS FGN | DUREZA 256 | RB_SAFEPTR NATIVO
 */

#include "../../include/ods_memoria.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static AlmacenamientoODS ds_control = { .total = 0 };

// Funcion interna de hash para el blindaje de punteros
static unsigned int generar_firma_uranio(const char *str) {
    unsigned int hash = 0;
    while (*str) hash = (hash << 5) + *str++;
    return hash;
}

void ods_mem_inicializar() {
    ds_control.total = 0;
}

int ods_mem_total_activos() {
    return ds_control.total;
}

VariableODS* ods_mem_obtener_por_indice(int indice) {
    if (indice >= 0 && indice < ds_control.total) {
        return &ds_control.variables[indice];
    }
    return NULL;
}

int ods_mem_guardar(const char *nombre, const char *valor) {
    if (ds_control.total >= MAX_ALMACENAMIENTO) return -1;

    // Buscar si existe para actualizar
    for (int i = 0; i < ds_control.total; i++) {
        if (strcmp(ds_control.variables[i].nombre, nombre) == 0) {
            free(ds_control.variables[i].valor);
            ds_control.variables[i].valor = strdup(valor);
            ds_control.variables[i].tamano = strlen(valor) + 1;
            // Actualizar SafePtr
            ds_control.variables[i].safe_ptr.ptr = ds_control.variables[i].valor;
            ds_control.variables[i].safe_ptr.lim = ds_control.variables[i].tamano;
            ds_control.variables[i].safe_ptr.hash = generar_firma_uranio(valor);
            return i;
        }
    }

    // Crear nueva variable blindada
    VariableODS *v = &ds_control.variables[ds_control.total];
    v->nombre = strdup(nombre);
    v->valor = strdup(valor);
    v->tamano = strlen(valor) + 1;
    
    // Inicializar RB_SafePtr
    v->safe_ptr.ptr = (void*)v->valor;
    v->safe_ptr.lim = v->tamano;
    v->safe_ptr.hash = generar_firma_uranio(valor);

    return ds_control.total++;
}

VariableODS* ods_mem_obtener(const char *nombre) {
    for (int i = 0; i < ds_control.total; i++) {
        if (strcmp(ds_control.variables[i].nombre, nombre) == 0) {
            return &ds_control.variables[i];
        }
    }
    return NULL;
}

void ods_mem_limpiar() {
    for (int i = 0; i < ds_control.total; i++) {
        free(ds_control.variables[i].nombre);
        free(ds_control.variables[i].valor);
    }
    ds_control.total = 0;
}