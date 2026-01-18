use serde::{Serialize, Deserialize};

#[repr(C, packed)]
#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
pub struct OsirisPacket {
    pub version: u8,
    pub seed_id: u8,
    pub opcode: u16,
    pub payload_size: u32,
    pub signature: u32,
}

impl OsirisPacket {
    // Añadimos _ para indicar que es intencional que no se use aqui
    pub fn new_rescale_base(_nuevo_tam: u32) -> Self {
        OsirisPacket {
            version: 2,
            seed_id: 1,
            opcode: 5, // OP_RESCALE
            payload_size: 4,
            signature: 0,
        }
    }

    pub fn as_bytes(&self) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(
                (self as *const OsirisPacket) as *const u8,
                std::mem::size_of::<OsirisPacket>(),
            )
        }
    }
}


