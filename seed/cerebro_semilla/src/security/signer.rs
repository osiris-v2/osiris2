// ============================================================
// PROYECTO OSIRIS - security/signer.rs
// FASE 2B: HMAC-SHA256 por sesion
//
// CONVENCION DE BYTES: todo little-endian (nativo x86)
//   - magic del handshake: to_le_bytes()  → 59 4B 53 4F en cable
//   - signature u32:       from_le_bytes() → primeros 4B del HMAC
//   - payload_size en msg: to_le_bytes()  → igual que en el header
//
// MODELO DE SEGURIDAD:
//   - session_key: 32 bytes aleatorios generados en arranque
//   - Vive SOLO en RAM (nunca en disco, nunca en log)
//   - HMAC calculado sobre: header[0..12] + payload completo
//   - Los 4 primeros bytes del HMAC van en header.signature
//   - Sin session_key no se puede forjar un signature valido
//
// GARANTIA:
//   - Opcode 22 inyectado desde red sin la clave → signature
//     incorrecto → Nodo descarta el paquete sin procesarlo
// ============================================================

use hmac::{Hmac, Mac};
use sha2::Sha256;
use crate::network::protocol::OsirisPacket;

type HmacSha256 = Hmac<Sha256>;

/// Genera la session_key: 32 bytes aleatorios del CSPRNG del SO.
/// Llamar UNA vez al arranque. Guardar en Arc<[u8;32]> en RAM.
/// Nunca serializar ni loggear.
pub fn generar_session_key() -> [u8; 32] {
    let mut key = [0u8; 32];
    // getrandom usa /dev/urandom en Linux — CSPRNG del kernel
    getrandom::getrandom(&mut key).expect("getrandom fallo: entropy no disponible");
    key
}

/// Calcula HMAC-SHA256(session_key, header_parcial || payload)
/// y devuelve los primeros 4 bytes como u32 little-endian.
///
/// header_parcial = los 12 bytes del header SIN los bytes 3..7
/// (los propios bytes de signature se excluyen para evitar
/// dependencia circular — el receptor hace lo mismo).
///
/// Llamar con packet.signature == 0 antes de escribir el resultado.
pub fn generate_signature(
    packet: &OsirisPacket,
    payload: &[u8],
    session_key: &[u8; 32],
) -> u32 {
    let mut mac = HmacSha256::new_from_slice(session_key)
        .expect("HMAC acepta cualquier longitud de clave");

    // Serializar el header de 16 bytes con signature=0
    // Es el mismo layout que #[repr(C, packed)] escribe en memoria:
    //   [version(1), seed_id(1), opcode(1), sig=0(4LE), payload_size(4LE), padding(5)]
    let mut hdr_bytes = [0u8; 16];
    hdr_bytes[0]  = packet.version;
    hdr_bytes[1]  = packet.seed_id;
    hdr_bytes[2]  = packet.opcode;
    // bytes 3..7 = signature → 0x00000000 (excluido del calculo)
    hdr_bytes[7..11].copy_from_slice(&packet.payload_size.to_le_bytes());
    hdr_bytes[11..15].copy_from_slice(&packet.frame_cnt.to_le_bytes());
    hdr_bytes[15] = packet.reservado;

    mac.update(&hdr_bytes); // 16 bytes exactos
    mac.update(payload);    // payload completo

    let result = mac.finalize().into_bytes();
    u32::from_le_bytes([result[0], result[1], result[2], result[3]])
}

/// Verifica que el signature recibido es valido.
/// El Nodo llama a esto tras leer cada header.
/// Si devuelve false: descartar paquete, no ejecutar opcode.
pub fn verificar_signature(
    packet: &OsirisPacket,
    payload: &[u8],
    session_key: &[u8; 32],
) -> bool {
    let esperado = generate_signature(packet, payload, session_key);
    // Comparacion en tiempo constante para evitar timing attacks
    constant_time_eq(packet.signature, esperado)
}

/// Comparacion de u32 en tiempo constante.
/// Evita que un atacante deduzca bytes correctos midiendo tiempo.
#[inline(always)]
fn constant_time_eq(a: u32, b: u32) -> bool {
    let diff = a ^ b;
    // Si diff == 0 → iguales. La operacion no tiene branch.
    diff == 0
}

/// Serializa la session_key para enviarla al Nodo en el handshake.
/// Se envia una sola vez por canal CONTROL al inicio de sesion.
/// Formato: 4 bytes de magic (0x4F534B59 = "OSKY") + 32 bytes de clave
pub fn serializar_handshake(session_key: &[u8; 32]) -> [u8; 36] {
    let mut buf = [0u8; 36];
    buf[0..4].copy_from_slice(&0x4F534B59u32.to_le_bytes()); // magic "OSKY" en LE → bytes: 59 4B 53 4F → Nodo lee 0x4F534B59 en x86
    buf[4..36].copy_from_slice(session_key);
    buf
}


// ============================================================
// XOR CIFRADO POR FRAME — Fase 2B
//
// Keystream = SHA256(session_key || frame_cnt_le) repetido
// El mismo keystream cifra en el Cerebro y descifra en el Nodo.
// El frame_cnt viaja en el header — cada paquete es autonomo.
// ============================================================

use sha2::Digest;

/// Genera el keystream para un frame dado y aplica XOR al payload.
/// Llamar ANTES de calcular el HMAC (en el Cerebro).
/// Llamar DESPUES de verificar el HMAC (en el Nodo).
pub fn xor_payload(payload: &mut [u8], session_key: &[u8; 32], frame_cnt: u32) {
    if payload.is_empty() { return; }

    // Semilla = session_key (32B) || frame_cnt (4B LE)
    let mut seed = [0u8; 36];
    seed[..32].copy_from_slice(session_key);
    seed[32..36].copy_from_slice(&frame_cnt.to_le_bytes());

    // Generar keystream en bloques de 32 bytes (SHA256)
    // SHA256(seed || bloque_idx) para cada bloque de 32 bytes del payload
    let mut offset = 0usize;
    let mut bloque: u32 = 0;

    while offset < payload.len() {
        // keystream_block = SHA256(seed || bloque_le)
        let mut hasher = sha2::Sha256::new();
        hasher.update(&seed);
        hasher.update(&bloque.to_le_bytes());
        let ks = hasher.finalize();

        // XOR hasta 32 bytes
        let remaining = payload.len() - offset;
        let n = remaining.min(32);
        for i in 0..n {
            payload[offset + i] ^= ks[i];
        }

        offset += n;
        bloque += 1;
    }
}