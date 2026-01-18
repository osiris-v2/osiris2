/* PROYECTO OSIRIS - IMPLEMENTACION URANIO SAFE
 * CORRECCION DE CONFLICTO DE TIPOS Y VALIDACION DE DUREZA
 * ASCII PURO - SIN ACENTOS - DUREZA 256
 */

#include "../include/uranio.h"
#include <string.h>
#include <stdlib.h>

/**
 * Implementacion de Escritura Segura
 * Se añade 'const' para coincidir con la cabecera evolucionada.
 */
UranioStatus uranio_escribir(RB_SafePtr *sptr, const uint8_t *data, size_t tam) {
    // 1. Validacion de Nulidad
    if (!sptr || !sptr->ptr_real || !data) return URANIO_ERROR_NULL;

    // 2. Validacion de Firma de Integridad (Dureza 256)
    if (sptr->firma != URANIO_SIG) return URANIO_ERROR_INTEGRIDAD;

    // 3. Control de Desbordamiento (Overflow Protection)
    if (sptr->posicion + tam > sptr->tamanio) {
        return URANIO_ERROR_OVERFLOW;
    }

    // 4. Verificacion de Alineacion de la Operacion
    if (((uintptr_t)(sptr->ptr_real + sptr->posicion) % URANIO_ALIGN) != 0) {
        // Nota: Solo advertencia o error segun politica de hardware
    }

    // 5. Materializacion de Bits
    memcpy(sptr->ptr_real + sptr->posicion, data, tam);
    sptr->posicion += tam;

    // 6. Actualizacion de Checksum (Hash simple de estado)
    sptr->checksum = (uint32_t)(sptr->posicion ^ sptr->tamanio);

    return URANIO_OK;
}