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
// Bytes 3-6   : signature    - Hash de integridad del payload (u32 LE)
// Bytes 7-10  : payload_size - Tamanio del payload que sigue (u32 LE)
// Bytes 11-15 : padding      - Relleno para completar 16 bytes
//
// IMPORTANTE: El Nodo C lee el header con esta logica:
//   header[2]          → opcode
//   header[3..7]       → signature (u32 little-endian)
//   header[7..11]      → payload_size (u32 little-endian)
//
// NO usar [7u8; 12] como magic manual — usar OsirisPacket::new_*() siempre.

#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
#[repr(C, packed)]
pub struct OsirisPacket {
    pub version:      u8,
    pub seed_id:      u8,
    pub opcode:       u8,
    pub signature:    u32,
    pub payload_size: u32,
    pub padding:      [u8; 5],
}

// --- TABLA DE OPCODES ---
// Sincronizada con dispatch_table en nodo_musculo/src/main.c
pub mod opcodes {
    pub const OP_VIDEO:     u8 = 7;   // Stream de video (payload = chunk MPEG-TS)
    pub const OP_RESCALE:   u8 = 5;   // Redimensionar buffer Uranio
    pub const OP_EXIT:      u8 = 9;   // Cerrar conexion ordenadamente
    pub const OP_PAUSE:     u8 = 10;  // Play / Pause del stream
    pub const OP_SKIP:      u8 = 15;  // Salto sin cerrar el pipe
    pub const OP_IA_UPDATE: u8 = 22;  // Inyectar modelo IA (bloque ADN)
}

impl OsirisPacket {
    /// Paquete para envio de chunk de video.
    /// opcode = 7, payload_size = n bytes del chunk MPEG-TS que sigue.
    pub fn new_video_packet(n: u32) -> Self {
        Self {
            version:      2,
            seed_id:      1,
            opcode:       opcodes::OP_VIDEO,
            signature:    0,      // Se rellena por signer::generate_signature()
            payload_size: n,
            padding:      [0u8; 5],
        }
    }

    /// Paquete para comando de rescale del buffer Uranio en el Nodo.
    /// payload = 4 bytes con el nuevo tamanio (u32 LE).
    pub fn new_rescale_packet(nuevo_tam: u32) -> Self {
        Self {
            version:      2,
            seed_id:      1,
            opcode:       opcodes::OP_RESCALE,
            signature:    0,
            payload_size: nuevo_tam,
            padding:      [0u8; 5],
        }
    }

    /// Paquete de control simple (pause, skip, exit).
    /// Sin payload adicional.
    pub fn new_control_packet(opcode: u8) -> Self {
        Self {
            version:      2,
            seed_id:      1,
            opcode,
            signature:    0,
            payload_size: 0,
            padding:      [0u8; 5],
        }
    }

    /// Serializa el paquete a bytes para envio por TCP.
    /// Siempre produce exactamente 16 bytes.
    pub fn as_bytes(&self) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(
                (self as *const Self) as *const u8,
                std::mem::size_of::<Self>(), // = 16
            )
        }
    }
}