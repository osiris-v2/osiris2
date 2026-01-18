#include "../../include/ods_memoria.h"
#include "../../include/ods_ejecutor.h"
#include "../../include/ods_entrada.h"
#include <stdlib.h>

int main() {
    ods_mem_inicializar();
    ods_entrada_inicializar();

    while (1) {
        char *linea = ods_entrada_obtener();
        if (!linea) break;
        if (*linea) ods_ejecutar_linea(linea);
        free(linea);
    }

    ods_mem_limpiar();
    return 0;
}