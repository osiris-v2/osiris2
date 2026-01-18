/* * PROYECTO OSIRIS - ODS ENTRADA DUAL
 * SINTAXIS FGN | DUREZA 256
 */

#ifndef ODS_ENTRADA_H
#define ODS_ENTRADA_H

// Inicializa los descriptores de archivo y sockets (Mercurio)
void ods_entrada_inicializar();

// Lee una linea, priorizando el Canal Mercurio si hay datos
char* ods_entrada_obtener();

// Indica si la ultima entrada fue remota (para auditoria)
int ods_entrada_es_fantasma();

#endif