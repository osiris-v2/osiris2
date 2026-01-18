#ifndef ODS_MEMORIA_H
#define ODS_MEMORIA_H

#include "ods_definiciones.h"

void ods_mem_inicializar();
int ods_mem_guardar(const char *nombre, const char *valor);
VariableODS* ods_mem_obtener(const char *nombre);
void ods_mem_limpiar();
int ods_mem_total_activos();
VariableODS* ods_mem_obtener_por_indice(int indice);

#endif