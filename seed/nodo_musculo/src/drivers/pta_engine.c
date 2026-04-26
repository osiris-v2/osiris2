/* ============================================================
 * PROYECTO OSIRIS - MOTOR DE ACUNACION H (Implementacion)
 * Version: 2.12 - Estabilidad Critica y Confianza Inmediata
 * ASCII PURO - SINTAXIS FGN - DUREZA 256
 * ============================================================ */

#include "pta_engine.h"
#include "rb_csp.h"
#include <stdio.h>

/* --- PARAMETROS DE CONFIANZA --- */
/* K_MADUREZ: Define la velocidad de maduracion del Nodo.
 * Valor 1.0: Confianza casi instantanea (Ideal para pruebas).
 * Valor 86400.0: Requiere 24h para validar el 50% de potencia. */
#define K_MADUREZ 1.0

/**
 * @brief Algoritmo de Negentropia Asintotica.
 * El tiempo valida la potencia, pero no puede superarla.
 */
static inline uint64_t Calcular_H_Saturado(const RSD_Metrics* m) {
    // 1. Calculo de Potencia Fisica Nominal (Techo del Valor)
    double potencia_neta = (m->flops_netos * PTA_K_CPU) + 
                           (m->ancho_banda_bps * PTA_K_NET) + 
                           (m->memoria_segura_kb * PTA_K_MEM);

    // 2. Factor de Confianza (u / (u + K))
    // Proteccion contra division por cero: si u=0, factor=0.
    double u = (double)m->uptime_segundos;
    double factor_confianza = (u > 0) ? (u / (u + K_MADUREZ)) : 0.001;

    // 3. Resultado final: La capacidad fisica es el limite asintotico.
    return (uint64_t)(potencia_neta * factor_confianza);
}

/**
 * @brief Ejecuta un ciclo completo de acunacion con validacion de Dureza.
 * @param pta_storage Puntero seguro pre-asignado (Debe ser URANIO).
 * @param metrics Estructura con la lectura de los recursos del Nodo.
 * @return 0 si la acunacion fue exitosa, negativo en fallo de protocolo.
 */
int32_t Ejecutar_Ciclo_Acunacion(RB_SafePtr* pta_storage, RSD_Metrics metrics) {
    
    /* A. Verificacion de Seguridad de Memoria */
    if (pta_storage == NULL || pta_storage->estado == ESTADO_VOID) {
        return -2;
    }

    if (pta_storage->hardness != URANIO) {
        printf("[ERROR] Protocolo requiere memoria URANIO para acunacion.\n");
        return -1;
    }

    /* B. Calculo de Valor H */
    uint64_t h_final = Calcular_H_Saturado(&metrics);

    /* C. Acceso y Escritura Segura */
    uint64_t* data_area = (uint64_t*)rb_ptr_get(pta_storage);
    
    if (data_area != NULL) {
        *data_area = h_final;
        pta_storage->coherencia = 1.0; 
        return 0; 
    }

    return -3; 
}