#include "../include/uranio.h"
#include <stdlib.h>
#include <string.h>

RB_SafePtr uranio_crear(size_t tam) {
    RB_SafePtr sptr = {NULL, 0, 0, 0};
    if (tam > 0) {
        sptr.ptr_real = (uint8_t *)malloc(tam);
        if (sptr.ptr_real) {
            sptr.tamanio = tam;
            sptr.posicion = 0;
            // Un simple XOR como checksum basico de integridad
            sptr.checksum = (uint32_t)((uintptr_t)sptr.ptr_real ^ tam);
        }
    }
    return sptr;
}

UranioStatus uranio_escribir(RB_SafePtr *sptr, uint8_t *data, size_t tam) {
    if (!sptr || !sptr->ptr_real) return URANIO_ERROR_NULL;
    
    // Verificacion de limites (El corazon de la seguridad)
    if (sptr->posicion + tam > sptr->tamanio) {
        return URANIO_ERROR_OVERFLOW;
    }

    memcpy(sptr->ptr_real + sptr->posicion, data, tam);
    sptr->posicion += tam;
    return URANIO_OK;
}

void uranio_liberar(RB_SafePtr *sptr) {
    if (sptr && sptr->ptr_real) {
        free(sptr->ptr_real);
        sptr->ptr_real = NULL;
        sptr->tamanio = 0;
    }
}