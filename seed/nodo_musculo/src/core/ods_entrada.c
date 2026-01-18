/* * PROYECTO OSIRIS - ODS ENTRADA DUAL
 * SINTAXIS FGN | DUREZA 256
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <readline/readline.h>
#include <readline/history.h>
#include "../../include/ods_entrada.h"

static int ultima_entrada_fantasma = 0;

void ods_entrada_inicializar() {
    // Aqui se abriria el socket del Canal Mercurio en el futuro
    ultima_entrada_fantasma = 0;
}

char* ods_entrada_obtener() {
    /* * PENSAMIENTO: En la version final, aqui usariamos select() para 
     * vigilar el socket de red y el stdin simultaneamente.
     */
     
    // Por ahora, mantenemos la compatibilidad con el readline de ops.c
    char *linea = readline("> ods>> ");
    
    if (linea && *linea) {
        add_history(linea);
        ultima_entrada_fantasma = 0; // Entrada local
    }
    
    return linea;
}

int ods_entrada_es_fantasma() {
    return ultima_entrada_fantasma;
}