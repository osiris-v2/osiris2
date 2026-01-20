/* * PROYECTO OSIRIS - Motor de Geometria Numerica
 * Archivo: fgn_math.c
 * Sincronizacion: Hardness / ASCII Puro
 */

#include "fgn_math.h"
#include <stdlib.h>
#include <stdio.h>
#include <math.h>

// Funcion interna para acceso seguro a la memoria de la particula
static Ladrillo3D* FGN_GetBloque(RB_SafePtr safe, uint32_t idx) {
    if (idx >= (safe.size / sizeof(Ladrillo3D))) return NULL;
    return (Ladrillo3D*)((uint8_t*)safe.data + (idx * sizeof(Ladrillo3D)));
}

// Cambiado 'Dureza' por 'Hardness' para coincidir con rb_csp.h
FirmaGeo FGN_Forjar(uint64_t n, Hardness d) {
    FirmaGeo f;
    f.n_id = n;
    f.t_cantidad = 0;
    
    // Usamos su funcion original: crear_bloque
    f.bloques = crear_bloque(32 * sizeof(Ladrillo3D), d);

    uint64_t temp = n;
    uint64_t divisor = 2;

    while (temp > 1 && f.t_cantidad < 32) {
        if (temp % divisor == 0) {
            uint32_t exp = 0;
            while (temp % divisor == 0) { temp /= divisor; exp++; }

            Ladrillo3D* b = FGN_GetBloque(f.bloques, f.t_cantidad);
            if (b) {
                b->x_fase = (double)exp;
                b->y_amplitud = (double)divisor;
                b->z_prof = sqrt(b->y_amplitud * b->x_fase);
                f.t_cantidad++;
            }
        }
        divisor++;
    }

    f.esfericidad = (f.t_cantidad > 5) ? 0.95 : (f.t_cantidad * 0.15);
    f.curvatura = sin((double)n);
    return f;
}

void FGN_ProcesarFase(FirmaGeo* f, double n_mod, double d_mod) {
    if (!f->bloques.data) return;

    double ratio = n_mod / d_mod;
    for (uint32_t i = 0; i < f->t_cantidad; i++) {
        Ladrillo3D* b = FGN_GetBloque(f->bloques, i);
        if (b) {
            b->x_fase *= ratio;
            b->z_prof /= ratio; 
        }
    }
    f->curvatura = cos(f->n_id * ratio);
}

void FGN_SepararOnda(FirmaGeo* original, FirmaGeo* alfa, FirmaGeo* beta) {
    rb_bifurcar_onda(&original->bloques, &alfa->bloques, &beta->bloques);
    alfa->n_id = original->n_id;
    beta->n_id = original->n_id;
    alfa->t_cantidad = original->t_cantidad;
    beta->t_cantidad = original->t_cantidad;
    alfa->curvatura = original->curvatura;
    beta->curvatura = -original->curvatura;
}

void FGN_Colapsar(FirmaGeo* alfa, FirmaGeo* beta, FirmaGeo* resultado) {
    if (rb_colapsar_observacion(&alfa->bloques, &beta->bloques, &resultado->bloques)) {
        resultado->n_id = alfa->n_id;
        resultado->t_cantidad = alfa->t_cantidad;
        resultado->esfericidad = 1.0;
        printf("[MATH] Particula/2 unificada en estructura de Dureza 256.\n");
    }
}

void FGN_Destruir(FirmaGeo* f) {
    rb_liberar(&f->bloques);
}