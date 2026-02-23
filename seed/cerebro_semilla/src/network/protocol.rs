// ============================================================
// PROYECTO OSIRIS - protocol.rs
// DEFINICION DEL PAQUETE DE RED OSIRIS
// Sincronizado con la lectura de header en nodo_musculo/src/main.c
// ============================================================

use serde::{Serialize, Deserialize};

// --- FORMATO DEL PAQUETE (16 bytes fijos) ---
//
// Byte 0      : version      - Version del protocolo (actualmente 2)
// Byte 1      : seed_id      - ID de semilla para el signer
// Byte 2      : opcode       - Operacion a ejecutar en el Nodo
// Bytes 3-6   : signature    - HMAC-SHA256 truncado a 4 bytes (u32 LE)
// Bytes 7-10  : payload_size - Tamanio del payload cifrado (u32 LE)
// Bytes 11-14 : frame_cnt    - Contador de frame para XOR keystream (u32 LE)
// Byte  15    : reservado    - Uso futuro (0x00)
//
// FLUJO DE SEGURIDAD POR PAQUETE:
//   Cerebro:
//     1. Construir header con signature=0, frame_cnt=N
//     2. XOR del payload con keystream(session_key, frame_cnt)
//     3. Calcular HMAC sobre header(sig=0) + payload_cifrado
//     4. Escribir HMAC en header.signature
//     5. Enviar header + payload_cifrado
//
//   Nodo:
//     1. Leer header (16 bytes)
//     2. Verificar HMAC(header con sig=0, payload_cifrado) → si falla, descartar
//     3. XOR del payload con keystream(session_key, frame_cnt) → payload limpio
//     4. Dispatch al opcode

#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
#[repr(C, packed)]
pub struct OsirisPacket {
    pub version:      u8,
    pub seed_id:      u8,
    pub opcode:       u8,
    pub signature:    u32,
    pub payload_size: u32,
    pub frame_cnt:    u32,   // antes: padding[0..4] — ahora contador de frame
    pub reservado:    u8,    // antes: padding[4]    — reservado futuro
}

// --- TABLA DE OPCODES ---
pub mod opcodes {
    pub const OP_VIDEO:     u8 = 7;
    pub const OP_RESCALE:   u8 = 5;
    pub const OP_EXIT:      u8 = 9;
    pub const OP_PAUSE:     u8 = 10;
    pub const OP_SKIP:      u8 = 15;
    pub const OP_IA_UPDATE: u8 = 22;
}

impl OsirisPacket {
    pub fn new_video_packet(n: u32, frame_cnt: u32) -> Self {
        Self {
            version:      2,
            seed_id:      1,
            opcode:       opcodes::OP_VIDEO,
            signature:    0,
            payload_size: n,
            frame_cnt,
            reservado:    0,
        }
    }

    pub fn new_rescale_packet(nuevo_tam: u32) -> Self {
        Self {
            version:      2,
            seed_id:      1,
            opcode:       opcodes::OP_RESCALE,
            signature:    0,
            payload_size: nuevo_tam,
            frame_cnt:    0,
            reservado:    0,
        }
    }

    pub fn new_control_packet(opcode: u8) -> Self {
        Self {
            version:      2,
            seed_id:      1,
            opcode,
            signature:    0,
            payload_size: 0,
            frame_cnt:    0,
            reservado:    0,
        }
    }

    /// Serializa el paquete a 16 bytes para envio por TCP.
    pub fn as_bytes(&self) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(
                (self as *const Self) as *const u8,
                std::mem::size_of::<Self>(), // = 16
            )
        }
    }
}