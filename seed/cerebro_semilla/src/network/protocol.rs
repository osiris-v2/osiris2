// ============================================================
// PROYECTO OSIRIS - protocol.rs
// TABLA DE OPCODES FGN — FASE 3A
// Sincronizado con nodo_musculo/src/main.c dispatch_table
//
// CONVENCION DE GRUPOS:
//   0-29  : Nucleo del protocolo (video, control, ia)
//   30-39 : Drivers de ventana y renderizado SDL
//   40-49 : Motor QuickJS / bytecode FGN
//   50-59 : Respuestas Nodo→Cerebro (canal CONTROL)
//   60-79 : Red y memoria (Fase 3B — reservados)
//   80-255: Extensiones futuras del lenguaje
// ============================================================

use serde::{Serialize, Deserialize};

// --- HEADER DE 16 BYTES (sin cambios desde Fase 2B) ---
#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
#[repr(C, packed)]
pub struct OsirisPacket {
    pub version:      u8,
    pub seed_id:      u8,
    pub opcode:       u8,
    pub signature:    u32,
    pub payload_size: u32,
    pub frame_cnt:    u32,
    pub reservado:    u8,
}

// ── TABLA DE OPCODES ──────────────────────────────────────────────────────
#[allow(dead_code)]
pub mod opcodes {

    // ── GRUPO NUCLEO (existentes, sin cambios) ───────────────────────────
    pub const OP_HWPROBE:      u8 = 1;  // Solicitar HardwareMap al Nodo
    pub const OP_RESCALE:      u8 = 5;  // Redimensionar buffer Uranio
    pub const OP_VIDEO:        u8 = 7;  // Stream MPEG-TS via pipe ffplay
    pub const OP_EXIT:         u8 = 9;  // Cerrar conexion ordenadamente
    pub const OP_PAUSE:        u8 = 10; // Toggle pausa/play del stream
    pub const OP_SKIP:         u8 = 15; // Salto de posicion sin cerrar pipe
    pub const OP_IA_UPDATE:    u8 = 22; // Inyectar ADN al core IA del Nodo

    // ── GRUPO VENTANA / SDL (30-39) ───────────────────────────────────────
    // Renderizado directo sobre SDL2/X11 — sin ffplay como intermediario
    pub const OP_WIN_CREATE:   u8 = 30; // Crear ventana SDL
                                        // payload: WinCreateParams (70 bytes)
    pub const OP_WIN_DESTROY:  u8 = 31; // Destruir ventana SDL activa
    pub const OP_WIN_SHOW:     u8 = 32; // Mostrar ventana si estaba oculta
    pub const OP_WIN_HIDE:     u8 = 33; // Ocultar ventana (persistencia silenciosa)
    pub const OP_RENDER_FRAME: u8 = 34; // Frame RGBA directo a textura SDL
                                        // payload: ancho*alto*4 bytes raw
    pub const OP_OVERLAY_TEXT: u8 = 35; // Texto sobre la ventana SDL
                                        // payload: OverlayParams (136 bytes)
    pub const OP_WIN_CLOSE:    u8 = 36; // Cerrar ventana por slot ID
                                        // payload: u32 slot_id (4 bytes)
    pub const OP_WIN_LIST:     u8 = 37; // Listar slots activos (sin payload)

    // ── GRUPO QUICKJS / BYTECODE FGN (40-49) ─────────────────────────────
    pub const OP_JS_EVAL:      u8 = 40; // Evaluar script JS en QuickJS
                                        // payload: UTF8 hasta 65535 bytes
    pub const OP_JS_LOAD:      u8 = 41; // Cargar bytecode QuickJS precompilado
                                        // payload: bytes de JS_WriteObject
    pub const OP_JS_RESET:     u8 = 42; // Destruir contexto JS y reiniciar limpio

    // ── GRUPO RESPUESTA Nodo→Cerebro (50-59) ─────────────────────────────
    // El Nodo escribe estos en el canal CONTROL como respuesta
    pub const OP_ACK:          u8 = 50; // Confirmacion de opcode ejecutado
                                        // payload: AckPayload (2 bytes)
    pub const OP_DATA_RESPONSE:u8 = 51; // Datos de respuesta (HWPROBE etc)
    pub const OP_JS_RESULT:    u8 = 52; // Resultado del ultimo JS_EVAL

    // ── GRUPO RED (60-62, Fase 3B — reservados) ──────────────────────────
    pub const OP_NET_CONNECT:  u8 = 60;
    pub const OP_NET_SEND:     u8 = 61;
    pub const OP_NET_RECV:     u8 = 62;

    // ── GRUPO MEMORIA SEGURA (70-73, Fase 3B — reservados) ───────────────
    pub const OP_MEM_ALLOC:    u8 = 70;
    pub const OP_MEM_FREE:     u8 = 71;
    pub const OP_MEM_READ:     u8 = 72;
    pub const OP_MEM_WRITE:    u8 = 73;
}

// ── ESTRUCTURAS DE PAYLOAD ────────────────────────────────────────────────

/// OP_WIN_CREATE payload (70 bytes)
#[derive(Debug, Clone, Copy)]
#[repr(C, packed)]
pub struct WinCreateParams {
    pub ancho:  u16,
    pub alto:   u16,
    pub titulo: [u8; 64],  // null-terminated ASCII
    pub flags:  u16,       // 0=normal, 1=fullscreen, 2=borderless
}

/// OP_OVERLAY_TEXT payload (136 bytes)
#[derive(Debug, Clone, Copy)]
#[repr(C, packed)]
pub struct OverlayParams {
    pub x:     i16,
    pub y:     i16,
    pub color: [u8; 4],    // RGBA
    pub size:  u8,          // tamaño de fuente relativo (1-8)
    pub texto: [u8; 128],  // null-terminated UTF8
    pub pad:   u8,
}

/// OP_ACK payload (2 bytes)
#[derive(Debug, Clone, Copy)]
#[repr(C, packed)]
#[allow(dead_code)]
pub struct AckPayload {
    pub opcode_origen: u8,  // opcode que se confirma
    pub resultado:     u8,  // 0=OK, 1=ERROR, 2=PENDIENTE
}

// ── CONSTRUCTORES ─────────────────────────────────────────────────────────
#[allow(dead_code)]
impl OsirisPacket {

    // ── Nucleo ────────────────────────────────────────────────────────────

    pub fn new_video_packet(n: u32, frame_cnt: u32) -> Self {
        Self { version: 2, seed_id: 1, opcode: opcodes::OP_VIDEO,
               signature: 0, payload_size: n, frame_cnt, reservado: 0 }
    }

    pub fn new_rescale_packet(nuevo_tam: u32) -> Self {
        Self { version: 2, seed_id: 1, opcode: opcodes::OP_RESCALE,
               signature: 0, payload_size: nuevo_tam, frame_cnt: 0, reservado: 0 }
    }

    pub fn new_control_packet(opcode: u8) -> Self {
        Self { version: 2, seed_id: 1, opcode,
               signature: 0, payload_size: 0, frame_cnt: 0, reservado: 0 }
    }

    pub fn new_hwprobe_packet() -> Self {
        Self::new_control_packet(opcodes::OP_HWPROBE)
    }

    // ── SDL / Ventana ─────────────────────────────────────────────────────

    pub fn new_win_create(_params: &WinCreateParams) -> Self {
        Self { version: 2, seed_id: 1, opcode: opcodes::OP_WIN_CREATE,
               signature: 0,
               payload_size: std::mem::size_of::<WinCreateParams>() as u32,
               frame_cnt: 0, reservado: 0 }
    }

    pub fn new_render_frame(bytes: u32, frame_cnt: u32) -> Self {
        Self { version: 2, seed_id: 1, opcode: opcodes::OP_RENDER_FRAME,
               signature: 0, payload_size: bytes, frame_cnt, reservado: 0 }
    }

    pub fn new_overlay_text(_params: &OverlayParams) -> Self {
        Self { version: 2, seed_id: 1, opcode: opcodes::OP_OVERLAY_TEXT,
               signature: 0,
               payload_size: std::mem::size_of::<OverlayParams>() as u32,
               frame_cnt: 0, reservado: 0 }
    }

    // ── QuickJS ───────────────────────────────────────────────────────────

    pub fn new_js_eval(script_len: u32) -> Self {
        Self { version: 2, seed_id: 1, opcode: opcodes::OP_JS_EVAL,
               signature: 0, payload_size: script_len, frame_cnt: 0, reservado: 0 }
    }

    pub fn new_js_load(bytecode_len: u32) -> Self {
        Self { version: 2, seed_id: 1, opcode: opcodes::OP_JS_LOAD,
               signature: 0, payload_size: bytecode_len, frame_cnt: 0, reservado: 0 }
    }

    pub fn new_js_reset() -> Self {
        Self::new_control_packet(opcodes::OP_JS_RESET)
    }

    // ── Serialización ─────────────────────────────────────────────────────

    /// Serializa el paquete a 16 bytes exactos para envio TCP.
    pub fn as_bytes(&self) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(
                (self as *const Self) as *const u8,
                std::mem::size_of::<Self>(),
            )
        }
    }

    /// Serializa junto a un payload de estructura packed.
    pub fn with_payload<T: Sized>(opcode_pkt: &Self, payload: &T) -> Vec<u8> {
        let mut buf = Vec::with_capacity(16 + std::mem::size_of::<T>());
        buf.extend_from_slice(opcode_pkt.as_bytes());
        buf.extend_from_slice(unsafe {
            std::slice::from_raw_parts(
                (payload as *const T) as *const u8,
                std::mem::size_of::<T>(),
            )
        });
        buf
    }
}