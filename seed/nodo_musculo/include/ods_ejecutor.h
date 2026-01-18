/* * PROYECTO OSIRIS - ODS EJECUTOR
 * SINTAXIS FGN | DUREZA 256
 */

#ifndef ODS_EJECUTOR_H
#define ODS_EJECUTOR_H

// Procesa una linea de comando completa
void ods_ejecutar_linea(char *linea);

// Procesa argumentos ya tokenizados (compatible con ops.c original)
void ods_ejecutar_comando(char **args);

#endif