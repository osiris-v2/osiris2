use tokio::net::TcpListener;
use tokio_tungstenite::{accept_async, tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::error::Error;
use log::{info, error, warn}; // Importar la librería de logs


#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    env_logger::init(); // Inicializar la librería de logs

    let addr = "0.0.0.0:80";
    let listener = TcpListener::bind(addr).await?;
    info!("Servidor WebSocket escuchando en {}", addr);

    while let Ok((stream, _)) = listener.accept().await {
        tokio::spawn(handle_connection(stream));
    }

    Ok(())
}

async fn handle_connection(stream: tokio::net::TcpStream) {
    match accept_async(stream).await {
        Ok(ws_stream) => {
            info!("Nuevo cliente WebSocket conectado.");
            let (mut write, mut read) = ws_stream.split();

            while let Some(result) = read.next().await {
                match result {
                    Ok(msg) => match msg {
                        Message::Text(text) => {
                            info!("Mensaje recibido: {}", text);
                            match handle_command(&text) {
                                Ok(response) => {
                                    if response.is_empty() {
                                        continue; // Ignora las respuestas vacías
                                    }
                                    if let Err(e) = write.send(Message::Text(response)).await {
                                        error!("Error al enviar respuesta: {}", e);
                                    }
                                },
                                Err(e) => { // Manejo de errores reales (si handle_command retorna Err)
                                   error!("Error al procesar el comando: {}", e);
                                    let _ = write.send(Message::Text(format!("Error del servidor: {}", e))).await; // Ignore send errors here
                                }
                            }
                        }
                        Message::Binary(_) => {
                            warn!("Mensaje binario recibido (no soportado)");
                            let _ = write.send(Message::Text("Mensaje binario no soportado".to_string())).await; // Ignore send errors
                        }
                        _ => {
                            warn!("Tipo de mensaje no soportado");
                            let _ = write.send(Message::Text("Tipo de mensaje no soportado".to_string())).await; // Ignore send errors
                        }
                    },
                    Err(e) => {
                        error!("Error al leer del WebSocket: {}", e);
                        break;
                    }
                }
            }
            info!("Cliente WebSocket desconectado.");
        }
        Err(e) => error!("Error al aceptar la conexión WebSocket: {}", e),
    }
}


fn handle_command(command: &str) -> Result<String, String> {
    match command {
        "/date" => Ok(chrono::Local::now().to_rfc3339()),
        "/hello" => Ok("Hola, cliente! 👋".to_string()),
        "/help" => Ok(
            "/date - Obtiene la fecha y hora actual.\n/hello - Saludo de bienvenida.\n/help - Muestra esta ayuda.".to_string()
        ),
        "" => Ok("".to_string()),
        _ => Err(format!("Comando no reconocido: {} 🤔", command)), // El error se devuelve como un Err
    }
}
