#ifndef ODS_DEFINICIONES_H
#define ODS_DEFINICIONES_H

#define MAX_ARGUMENTOS 64
#define MAX_ALMACENAMIENTO 256

// Estructura del Puntero Seguro (RB_SafePtr)
typedef struct {
    void *ptr;          // Direccion real en RAM
    unsigned long lim;  // Limite fisico de bytes
    unsigned int hash;  // Firma de integridad Uranio
} RB_SafePtr;

// Objeto de Variable Blindada
typedef struct {
    char *nombre;
    char *valor;
    unsigned long tamano;
    RB_SafePtr safe_ptr; // <--- ESTO ES LO QUE LEE EL OPERADOR ~
} VariableODS;

typedef struct {
    VariableODS variables[MAX_ALMACENAMIENTO];
    int total;
} AlmacenamientoODS;

#endif