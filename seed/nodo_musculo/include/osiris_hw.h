/* ================================================================
 * PROYECTO OSIRIS - osiris_hw.h
 * MAPA DE HARDWARE Y NAMESPACE DE HANDLERS FGN
 *
 * RESPONSABILIDADES:
 *   - OsirisHardwareMap: estructura serializable para OP_HWPROBE
 *   - Firmas de las funciones probe_*
 *   - MAX_FGN_WINDOWS y declaracion de h_table (extern)
 *     Los handlers son el namespace fisico del futuro lenguaje FGN.
 *
 * NOTA SOBRE PADDING:
 *   OsirisHardwareMap se envia por red como payload binario.
 *   Se usa __attribute__((packed)) para garantizar que el layout
 *   en el Nodo C coincide con lo que el Cerebro Rust deserializa.
 *   Rust usa #[repr(C, packed)] en el tipo receptor.
 *
 * ESCALADO:
 *   MAX_FGN_WINDOWS vive aqui (no en fgn_runtime.h) porque
 *   osiris_hw.h es el header de bajo nivel que no incluye SDL.
 *   fgn_runtime.h lo reexporta para los modulos SDL.
 *
 * DUREZA 256 - ASCII PURO
 * ================================================================ */

#ifndef OSIRIS_HW_H
#define OSIRIS_HW_H

#include <stdint.h>
#include <stdbool.h>
/* rb_csp.h NO se incluye aqui — osiris_hw.h es un header de bajo nivel
 * incluido por hw_probe.c, net_probe.c y sdl_core.c que no necesitan
 * ni SDL ni RB_SafePtr. OsirisHandler y h_table viven en fgn_runtime.h. */

/* ================================================================
 * MAPA DE HARDWARE
 * Serializado y enviado al Cerebro como respuesta a OP_HWPROBE.
 * El layout debe coincidir con el struct Rust en network/protocol.rs
 * ================================================================ */
typedef struct __attribute__((packed)) {

    /* CPU */
    uint32_t  cpu_nucleos;       /* nproc */

    /* RAM en kB (tal como lo reporta /proc/meminfo MemTotal) */
    uint64_t  ram_total_mb;

    /* Pantalla */
    uint16_t  pantalla_ancho;
    uint16_t  pantalla_alto;

    /* Soporte de subsistemas */
    uint8_t   soporte_sdl2;      /* bool serializado como u8 */
    uint8_t   soporte_opengl;    /* bool serializado como u8 */

    /* Red */
    float     latencia_ms;
    uint32_t  ancho_banda_kbps;

    /* Ventanas FGN activas en el momento del probe */
    uint8_t   fgn_slots_activos; /* cuantos slots estan en uso */
    uint8_t   fgn_slots_max;     /* MAX_FGN_WINDOWS */

    /* Tiempo de conexion activa en segundos */
    uint32_t  uptime_seg;

    /* Reservado para Fase 4 (version del protocolo HW, flags GPU) */
    uint8_t   reservado[6];

} OsirisHardwareMap;

/* ================================================================
 * FIRMAS DE LAS FUNCIONES PROBE
 * Implementadas en hw_probe.c, net_probe.c, sdl_core.c
 * ================================================================ */
void probe_sistema_base(OsirisHardwareMap *map);
void probe_video_capacidades(OsirisHardwareMap *map);
void probe_red_estado(OsirisHardwareMap *map);

/* MAX_HANDLERS y OsirisHandler se declaran en fgn_runtime.h junto
 * con h_table, RB_SafePtr y el resto de la infraestructura de slots.
 * Los modulos que necesiten h_table incluyen fgn_runtime.h, no este header. */

#endif /* OSIRIS_HW_H */