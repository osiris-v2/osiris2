// ============================================================
// PROYECTO OSIRIS - security/signer.rs
// FASE 2B: HMAC-SHA256 por sesion
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

    // Alimentar los bytes del header que NO son la signature
    // Byte 0: version | Byte 1: seed_id | Byte 2: opcode
    mac.update(&[packet.version, packet.seed_id, packet.opcode]);
    // Bytes 7-10: payload_size (en lugar de signature que va en 3-6)
    mac.update(&packet.payload_size.to_be_bytes());
    // Bytes 11-15: padding
    mac.update(&packet.padding);

    // Alimentar el payload completo
    mac.update(payload);

    let result = mac.finalize().into_bytes();

    // Primeros 4 bytes como u32 LE → caben en header.signature
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
    buf[0..4].copy_from_slice(&0x4F534B59u32.to_be_bytes()); // magic "OSKY"
    buf[4..36].copy_from_slice(session_key);
    buf
}