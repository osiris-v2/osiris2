use crate::network::protocol::OsirisPacket;

pub fn generate_signature(packet: &OsirisPacket, payload: &[u8]) -> u32 {
    let mut hash: u32 = 0x1337_BEEF; // Semilla de Dureza

    // Operaciones de bit directas
    hash = hash.wrapping_add(packet.opcode as u32);
    hash = hash ^ packet.payload_size; // XOR directo

    for byte in payload {
        hash = hash.wrapping_add(*byte as u32);
        hash = hash.rotate_left(5); // Rotacion directa
    }
    hash
}