/* * PROYECTO OSIRIS - fgn_monitor.c */
#ifndef FGN_MONITOR_C
#define FGN_MONITOR_C

#include <stdio.h>
#include <math.h> // <--- Esto elimina el warning de 'sin' [cite: 2026-01-20]
#include <stdint.h>

void FGN_Vigilar_GPU(FirmaGeo* geo) {
    if (!geo || !geo->bloques.data) return;

    printf("\n\x1b[35m[OSIRIS] VIGILANCIA DE URANIO (DUREZA 256)\x1b[0m\n");
    for (uint32_t i = 0; i < geo->t_cantidad; i++) {
        uintptr_t dir = (uintptr_t)geo->bloques.data + (i * sizeof(Ladrillo3D));
        double fase = sin(geo->curvatura * (double)i); 
        
        printf(" [B%02u] 0x%lx | Fase: %+.3f ", i, dir, fase);
        int len = (int)((fase + 1.0) * 10.0);
        printf("[");
        for(int j=0; j<20; j++) printf(j < len ? "#" : " ");
        printf("]\n");
    }
    printf("\x1b[35m------------------------------------------\x1b[0m\n");
}
#endif