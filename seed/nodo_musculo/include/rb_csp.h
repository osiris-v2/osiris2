/* ============================================================
 * PROYECTO OSIRIS - rb_csp.h
 * DEFINICION MAESTRA DE RB_SafePtr (Safe Pointer)
 * Esta es la UNICA definicion valida en todo el proyecto.
 * Todos los modulos deben incluir este header y NO redefinir RB_SafePtr.
 * ASCII PURO - DUREZA 256
 * ============================================================ */

#ifndef RB_CSP_H
#define RB_CSP_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* --- NIVELES DE DUREZA ---
 * Define la politica de gestion para cada bloque de memoria.
 *
 * ACERO    : Memoria temporal. Sin protecciones extra. Para buffers de corta vida.
 * DIAMANTE : Memoria de larga vida. Para estructuras del compilador y handlers.
 * URANIO   : Memoria critica. Se pone a cero antes de liberar (zeroing garantizado).
 */
typedef enum {
    ACERO    = 0,
    DIAMANTE = 1,
    URANIO   = 2
} Hardness;

/* --- ESTADOS DE FASE ---
 * Describe el estado actual del bloque en el ciclo de vida de memoria.
 *
 * ESTADO_PARTICULA  : Bloque normal, un solo propietario.
 * ESTADO_BIFURCADO  : Bloque compartido entre dos observadores (ref_count >= 2).
 * ESTADO_VOID       : Bloque liberado, no acceder.
 */
typedef enum {
    ESTADO_PARTICULA = 0,
    ESTADO_BIFURCADO = 1,
    ESTADO_VOID      = 2
} FaseEstado;

/* --- RB_SafePtr : PUNTERO SEGURO MAESTRO ---
 *
 * Campos:
 *   data       : Puntero real a la memoria en heap.
 *   size       : Capacidad total del bloque en bytes.
 *   hardness   : Politica de gestion (ACERO/DIAMANTE/URANIO).
 *   ref_count  : Contador de referencias activas (heap-allocated).
 *   estado     : Fase actual del bloque.
 *   coherencia : Score de integridad [0.0 - 1.0]. 1.0 = integro, 0.5 = bifurcado.
 *
 * IMPORTANTE: Nunca copiar este struct por valor si ref_count > 1.
 * Usar rb_adquirir() antes de compartir y rb_liberar() al terminar.
 */
typedef struct {
    void*     data;
    uint32_t  size;
    Hardness  hardness;
    uint32_t* ref_count;
    FaseEstado estado;
    double    coherencia;
} RB_SafePtr;

/* --- API DE CICLO DE VIDA --- */

/* Crea un nuevo bloque de memoria con la dureza indicada. ref_count = 1. */
RB_SafePtr crear_bloque(uint32_t tam, Hardness dureza);

/* Incrementa ref_count. Llamar antes de compartir el puntero. */
void rb_adquirir(RB_SafePtr* ptr);

/* Decrementa ref_count. Si llega a 0, libera la memoria (con zeroing si URANIO). */
void rb_liberar(RB_SafePtr* ptr);

/* Redimensiona el bloque. Solo valido en ESTADO_PARTICULA. */
void rb_rescale(RB_SafePtr* ptr, uint32_t nuevo_tam);

/* --- API DE FASE (Bifurcacion / Colapso) --- */

/* Crea dos referencias al mismo bloque fisico. ref_count += 1. */
void rb_bifurcar_onda(RB_SafePtr* original, RB_SafePtr* alfa, RB_SafePtr* beta);

/* Unifica dos referencias bifurcadas en un resultado. ref_count -= 1. */
bool rb_colapsar_observacion(RB_SafePtr* alfa, RB_SafePtr* beta, RB_SafePtr* resultado);

/* --- GETTERS SEGUROS --- */
void*    rb_ptr_get(RB_SafePtr* ptr);
uint32_t rb_ptr_size(RB_SafePtr* ptr);

#endif /* RB_CSP_H */