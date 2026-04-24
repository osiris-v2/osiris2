/* ============================================================
 * PROYECTO OSIRIS - MOTOR DE ACUNACION H
 * Integracion con rb_csp.h (Dureza 256)
 * ASCII PURO - SIN REDEFINICIONES - SINTAXIS FGN
 * ============================================================ */

#ifndef OSIRIS_PTA_ENGINE_H
#define OSIRIS_PTA_ENGINE_H

#include "rb_csp.h" // Definicion maestra de SafePtr

/* --- METRICAS FISICAS (RSD) --- */
typedef struct {
    uint64_t flops_netos;
    uint64_t ancho_banda_bps;
    uint64_t memoria_segura_kb;
    uint32_t uptime_segundos;
} RSD_Metrics;

/* --- CONSTANTES DE ESCALADO --- 
 * Basadas en la formula: Suministro_PTA = (CP*0.4)+(AB*0.3)+(PM*0.3)*Uptime
 */
#define PTA_K_CPU 0.4f
#define PTA_K_NET 0.3f
#define PTA_K_MEM 0.3f

/**
 * @brief Calcula el valor H (Acunacion) usando punteros seguros maestros.
 * @param metrics Datos de hardware (RSD).
 * @param pta_ptr Puntero seguro de tipo URANIO para valor critico.
 * @return 0 si exito, negativo en violacion de protocolo.
 */
static inline int32_t Acunar_PTA_H(const RSD_Metrics* metrics, RB_SafePtr* pta_ptr) {
    
    // 1. Validacion de estado de fase del bloque
    if (pta_ptr->estado == ESTADO_VOID || pta_ptr->data == NULL) {
        return -1; 
    }

    // 2. Verificacion de Dureza: Solo URANIO permite valores de capacidad
    if (pta_ptr->hardness != URANIO) {
        return -2;
    }

    // 3. Calculo de Negentropia (Escalado por Recursos de Sistema Disponibles)
    double trabajo_util = (metrics->flops_netos * PTA_K_CPU) + 
                          (metrics->ancho_banda_bps * PTA_K_NET) + 
                          (metrics->memoria_segura_kb * PTA_K_MEM);

    // El valor H es el resultado de la potencia neta por la persistencia
    uint64_t h_final = (uint64_t)(trabajo_util * metrics->uptime_segundos);

    // 4. Escritura en area de datos validada
    uint64_t* data_area = (uint64_t*)rb_ptr_get(pta_ptr);
    if (data_area != NULL) {
        *data_area = h_final;
        // Coherencia 1.0 indica integridad logica total (Dureza 256)
        pta_ptr->coherencia = 1.0; 
        return 0;
    }

    return -3;
}

/* --- INTERFAZ PUBLICA DEL MOTOR DE ACUNACION --- */
/**
 * @brief Ejecuta un ciclo completo de acunacion con validacion de Dureza.
 * @param pta_storage Puntero seguro pre-asignado (Debe ser URANIO).
 * @param metrics Estructura con la lectura de los recursos del Nodo.
 * @return 0 si la acunacion fue exitosa, o un codigo de error negativo si falla.
 */
int32_t Ejecutar_Ciclo_Acunacion(RB_SafePtr* pta_storage, RSD_Metrics metrics);

#endif // OSIRIS_PTA_ENGINE_H