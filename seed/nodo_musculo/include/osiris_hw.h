#ifndef OSIRIS_HW_H
#define OSIRIS_HW_H

#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint16_t inicio;
    uint32_t cpu_nucleos;
    uint64_t ram_total_mb;
    uint16_t pantalla_ancho;
    uint16_t pantalla_alto;
    bool soporte_sdl2;
    bool soporte_opengl;
    float latencia_ms;
    uint32_t ancho_banda_kbps;
} OsirisHardwareMap;

// Firmas para los drivers de /src/drivers/
void probe_sistema_base(OsirisHardwareMap *map);
void probe_video_capacidades(OsirisHardwareMap *map);
void probe_red_estado(OsirisHardwareMap *map);

#endif