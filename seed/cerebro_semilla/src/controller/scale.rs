use crate::network::protocol::OsirisPacket;
use crate::security::signer;
use tokio::net::TcpStream;
use tokio::io::AsyncWriteExt;

pub async fn send_rescale_command(addr: &str, nuevo_tam: u32) -> tokio::io::Result<()> {
    let mut packet = OsirisPacket::new_rescale_base(nuevo_tam);
    let payload = nuevo_tam.to_le_bytes();

    // Firmar con Plusvalía Intelectual
    packet.signature = signer::generate_signature(&packet, &payload);

    // Conexión y envío
    let mut stream = TcpStream::connect(addr).await?;
    stream.write_all(packet.as_bytes()).await?;
    stream.write_all(&payload).await?;

    println!("[OK] Paquete de Uranio inyectado en el Nodo {}", addr);
    Ok(())
}