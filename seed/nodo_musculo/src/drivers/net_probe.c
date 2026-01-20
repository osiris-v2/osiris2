#include "osiris_hw.h"
#include <stdio.h>
#include <time.h>

// Simulamos un ping al Cerebro (Rust) para medir latencia
void probe_red_estado(OsirisHardwareMap *map) {
    printf("[NET_PROBE] Midiendo latencia con el Cerebro...\n");
    
    // Logica de medicion RTT (Round Trip Time)
    clock_t inicio = clock();
    
    // Aqui iria el envio de un paquete de control vacio
    // Por ahora simulamos una red local rapida
    map->inicio = inicio;
    map->latencia_ms = 12.5f; 
    map->ancho_banda_kbps = 50000; // 50 Mbps base
    
    printf("[NET_PROBE] Latencia detectada: %.2f ms\n", map->latencia_ms);
}