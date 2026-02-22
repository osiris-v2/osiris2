/* include/fgn_ai_core.h */
#ifndef FGN_AI_CORE_H
#define FGN_AI_CORE_H

#include <stdint.h>
#include "rb_csp.h"

typedef struct {
    uint32_t id_modelo;
    float nivel_resonancia;
    RB_SafePtr* modelo_data; // Puntero seguro al modelo en Uranio
} FGN_AI_Context;

// Inicializa el motor de IA en el bloque de Uranio
FGN_AI_Context* fgn_ai_init();

// Procesa un SafePtr de datos externos contra el modelo
float fgn_ai_analizar(FGN_AI_Context* ctx, RB_SafePtr* datos_entrada);
// include/fgn_ai_core.h
void fgn_ai_actualizar_modelo(FGN_AI_Context* ctx, RB_SafePtr* nuevo_modelo);
void fgn_ai_destruir(FGN_AI_Context* ctx);
#endif