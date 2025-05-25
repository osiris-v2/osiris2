use tokio::io::{self, AsyncBufReadExt, BufReader};
use tokio_tungstenite::{connect_async, tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::io::Write; // Importa Write para flush síncrono

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "ws://127.0.0.69:8081"; // <--- Port changed here
    let (ws_stream, _) = connect_async(addr).await?;
    println!("Conectado al servidor WebSocket en {}", addr);

    let (mut write, mut read) = ws_stream.split();
    let stdin = io::stdin();
    let mut stdin_reader = BufReader::new(stdin);

    loop {
        let mut input = String::new();

        print!(">>>$ ");
        std::io::stdout().flush().unwrap(); // Uso de flush síncrono

        if let Err(e) = stdin_reader.read_line(&mut input).await {
            eprintln!("Error al leer la entrada estándar: {}", e);
            break;
        }

        let input = input.trim();
        if input.is_empty() {
            continue;
        }

        if let Err(e) = write.send(Message::Text(input.to_string())).await {
            eprintln!("Error al enviar el mensaje: {}", e);
            break;
        }

        if let Some(message) = read.next().await {
            match message {
                Ok(Message::Text(text)) => println!("\n{}", text),
                Ok(msg) => println!("Respuesta del servidor: {:?}", msg),
                Err(e) => eprintln!("Error al recibir mensaje: {:?}", e),
            }
        }
    }

    Ok(())
}
