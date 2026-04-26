#include "osiris_hw.h"
#include <stdio.h>
#include <time.h>

/* Mide latencia RTT simulada hacia el Cerebro.
 * inicio es local — OsirisHardwareMap es un struct serializable
 * y no debe usarse como scratchpad de estado interno. */
void probe_red_estado(OsirisHardwareMap *map) {
    printf("[NET_PROBE] Midiendo latencia con el Cerebro...\n");

    clock_t inicio = clock();

    /* Aqui iria el envio de un paquete de control vacio.
     * Por ahora simulamos una red local rapida. */
    (void)inicio;   /* suprime warning hasta implementar RTT real */

    map->latencia_ms      = 12.5f;
    map->ancho_banda_kbps = 50000;  /* 50 Mbps base */

    printf("[NET_PROBE] Latencia detectada: %.2f ms\n", map->latencia_ms);
}