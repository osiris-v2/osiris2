/* ================================================================
 * PROYECTO OSIRIS - ods_protocol.h
 * PROTOCOLO DE COMUNICACION ODS <-> CEREBRO SEMILLA
 *
 * CRITICO — SINCRONIZACION DE LAYOUT CON RUST:
 *   El struct PaqueteSoberano debe coincidir byte a byte con
 *   la definicion en main.rs:
 *
 *   #[repr(C, packed)]
 *   pub struct PaqueteSoberano {
 *       pub magic:      u16,      // 2 bytes  offset 0
 *       pub hash_verif: u32,      // 4 bytes  offset 2
 *       pub longitud:   u64,      // 8 bytes  offset 6  ← u64, NO unsigned int
 *       pub data:       [u8; 4096]// 4096 bytes offset 14
 *   }
 *
 * TRAMPA CLASICA:
 *   Si longitud se declara como 'unsigned int' (4 bytes) en C,
 *   el campo data[] empieza en offset 10 en C pero en offset 14
 *   en Rust. El Cerebro leerá los primeros 4 bytes del script
 *   como parte alta de longitud → longitud gigante → script
 *   corrupto con bytes de alineación errónea.
 *
 * REGLA: cualquier cambio en este struct debe reflejarse
 * simultaneamente en main.rs PaqueteSoberano.
 *
 * DUREZA 256 - ASCII PURO
 * ================================================================ */

#ifndef ODS_PROTOCOL_H
#define ODS_PROTOCOL_H

#include <stdint.h>

/* Puerto donde el Cerebro escucha comandos ODS */
#define PUERTO_OSIRIS   8087

/* Magic word que identifica un paquete valido */
#define CABECERA_MAGICA 0x256F

/* Layout identico al struct Rust con #[repr(C, packed)] */
#pragma pack(push, 1)
typedef struct {
    uint16_t magic;         /* 0x256F — identificador de paquete    */
    uint32_t hash_verif;    /* Hash de integridad del payload        */
    uint64_t longitud;      /* Bytes validos en data[] — u64 = u64  */
    uint8_t  data[4096];    /* Payload: comando ODS en ASCII puro    */
} PaqueteSoberano;
#pragma pack(pop)

/* Verificacion en tiempo de compilacion — falla si el layout no coincide */
_Static_assert(sizeof(PaqueteSoberano) == 2 + 4 + 8 + 4096,
               "PaqueteSoberano: layout no coincide con Rust. Revisar tipos.");
_Static_assert(__builtin_offsetof(PaqueteSoberano, data) == 14,
               "PaqueteSoberano: data debe estar en offset 14.");

#endif /* ODS_PROTOCOL_H */