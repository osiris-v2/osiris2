#ifndef ODS_DEFINICIONES_H
#define ODS_DEFINICIONES_H

#define MAX_ARGUMENTOS 64
#define MAX_ALMACENAMIENTO 256

/* Descriptor de auditoria ligero para variables ODS.
 * NO es un allocator. Solo describe la direccion, limite
 * y firma de integridad de un valor ya alojado en heap.
 * Nombre separado de RB_SafePtr (rb_csp.h) para evitar
 * conflicto de redefinicion si ambos headers se incluyen
 * en el mismo translation unit.
 */
typedef struct {
    void         *ptr;   /* Direccion real en RAM          */
    unsigned long lim;   /* Limite fisico de bytes         */
    unsigned int  hash;  /* Firma de integridad (djb2)     */
} ODS_SafeRef;

/* Objeto de Variable Blindada.
 * safe_ptr es el descriptor de auditoria que lee el operador ~
 */
typedef struct {
    char         *nombre;
    char         *valor;
    unsigned long tamano;
    ODS_SafeRef   safe_ptr;
} VariableODS;

typedef struct {
    VariableODS variables[MAX_ALMACENAMIENTO];
    int total;
} AlmacenamientoODS;

#endif