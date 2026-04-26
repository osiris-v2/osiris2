#include "../../include/fgn_ai_core.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>

FGN_AI_Context* fgn_ai_init() {
    FGN_AI_Context* ctx = (FGN_AI_Context*)malloc(sizeof(FGN_AI_Context));
    if (!ctx) return NULL;

    ctx->id_modelo = 0;
    ctx->nivel_resonancia = 0.0f;
    ctx->modelo_data = NULL;
    return ctx;
}

void fgn_ai_actualizar_modelo(FGN_AI_Context* ctx, RB_SafePtr* nuevo_modelo) {
    if (!ctx || !nuevo_modelo || !nuevo_modelo->data) return;

    // Si ya teniamos un modelo previo, lo liberamos antes de sobreescribir
    if (ctx->modelo_data != NULL) {
        // Asumimos que guardamos el puntero a la estructura en el heap o la estructura misma
        // Para simplificar y seguir tu rb_csp:
        rb_liberar(ctx->modelo_data);
        free(ctx->modelo_data); 
    }

    // Alocamos espacio en el heap para persistir la ESTRUCTURA del SafePtr
    ctx->modelo_data = (RB_SafePtr*)malloc(sizeof(RB_SafePtr));
    
    // Copiamos la estructura local a la persistente
    *(ctx->modelo_data) = *nuevo_modelo;

    // Incrementamos el conteo de referencias: El Core IA ahora es dueño de este Uranio
    rb_adquirir(ctx->modelo_data);

    ctx->id_modelo++;
    ctx->nivel_resonancia = 1.0f;
    
    printf("\x1b[32m[IA-CORE] ADN vinculado permanentemente. Referencias: %u\n\x1b[0m", 
            *(ctx->modelo_data->ref_count));
}

float fgn_ai_analizar(FGN_AI_Context* ctx, RB_SafePtr* datos_entrada) {
    if (!ctx || !ctx->modelo_data || !datos_entrada || !datos_entrada->data) {
        return 0.0f;
    }

    // Usamos .data que es el miembro REAL de tu RB_SafePtr
    uint8_t* adn = (uint8_t*)ctx->modelo_data->data;
    uint8_t* video = (uint8_t*)datos_entrada->data;

    uint32_t diff_acumulada = 0;
    // Comparamos segun el tamaño del modelo (1024) o el del video, lo que sea menor
    uint32_t limite = (datos_entrada->size < 1024) ? datos_entrada->size : 1024;

    for (uint32_t i = 0; i < limite; i++) {
        diff_acumulada += abs(adn[i] - video[i]);
    }

    float max_error = (float)limite * 255.0f;
    if (max_error > 0) {
        ctx->nivel_resonancia = 1.0f - ((float)diff_acumulada / max_error);
    } else {
        ctx->nivel_resonancia = 0.0f;
    }

    return ctx->nivel_resonancia;
}

void fgn_ai_destruir(FGN_AI_Context* ctx) {
    if (!ctx) return;

    if (ctx->modelo_data) {
        printf("\x1b[33m[IA-CORE] Liberando ADN por desconexion...\x1b[0m\n");
        // Bajamos el contador de referencias
        rb_liberar(ctx->modelo_data);
        // Liberamos el contenedor de la estructura
        free(ctx->modelo_data);
        ctx->modelo_data = NULL;
    }
    
    free(ctx);
    printf("\x1b[31m[IA-CORE] Motor de IA apagado.\x1b[0m\n");
}