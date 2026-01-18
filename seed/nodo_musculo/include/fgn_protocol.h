/* PROYECTO OSIRIS - PROTOCOLO FGN (FUEGO DE GIGANTES)
 * ESPECIFICACION DE OPCODES Y ESTRUCTURA DE RAGAFA 96-BITS
 * ASCII PURO - SIN ACENTOS - DUREZA 256
 */

#ifndef FGN_PROTOCOL_H
#define FGN_PROTOCOL_H

#include <stdint.h>

/* --- FIRMA DE INTEGRIDAD --- */
#define OSIRIS_SIG 0x53495249 // "SIRI" en Big Endian

/* --- DICCIONARIO DE OPCODES (8-BIT) --- */

// Fase 1: Sonda y Control
#define OP_SONDA_HW     0x01  // Detectar capacidades y reportar
#define OP_KEEP_ALIVE   0x05  // Latido de sincronia del Doble Vinculo
#define OP_PANIC_FLUSH  0xFF  // Limpieza de h_table y reset de seguridad

// Fase 2: Espejo y Video (Dureza 256)
#define OP_MIRROR_INI   0x10  // Levantar ventana y vincular handler
#define OP_MIRROR_OFF   0x1F  // Persistencia Silenciosa (Standby)
#define OP_SYNC_URANIO  0x44  // Sincronizar base fisica del handler

// Fase 3: Inteligencia y Datos
#define OP_TEXT_INJECT  0x90  // Inyectar texto desde Transcriptor (Python)
#define OP_PRIME_SHIFT  0xA0  // Cambiar semilla de Salto Primo (ASLR)

/* --- ESTRUCTURA DE LA RAFAGA (96 BITS) --- 
 * Esta estructura garantiza que cada instruccion sea compacta
 * y procesable en un solo ciclo del Dispatcher.
 */
#pragma pack(push, 1)
typedef struct {
    uint32_t firma;      // Debe ser OSIRIS_SIG
    uint8_t  opcode;     // Operacion a ejecutar
    uint16_t id_handler; // ID del descriptor en la h_table
    uint32_t payload;    // Datos extra (ej: Semilla o Coordenadas)
    uint8_t  checksum;   // Validacion de integridad de rafaga
} FGN_Opcode96;
#pragma pack(pop)

#endif // FGN_PROTOCOL_H