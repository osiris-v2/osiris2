#ifndef FGN_MATH_H
#define FGN_MATH_H

#include <stdint.h>
#include "rb_csp.h" // Ruta relativa desde src/math/

typedef struct {
    double x_fase;
    double y_amplitud;
    double z_prof;
} Ladrillo3D;

typedef struct {
    uint64_t n_id;
    RB_SafePtr bloques;
    uint32_t t_cantidad;
    double esfericidad;
    double curvatura;
} FirmaGeo;

// Usamos Hardness (su original) en lugar de Dureza
FirmaGeo FGN_Forjar(uint64_t n, Hardness d);
void FGN_ProcesarFase(FirmaGeo* f, double n_mod, double d_mod);
void FGN_SepararOnda(FirmaGeo* original, FirmaGeo* alfa, FirmaGeo* beta);
void FGN_Colapsar(FirmaGeo* alfa, FirmaGeo* beta, FirmaGeo* resultado);
void FGN_Destruir(FirmaGeo* f);

#endif