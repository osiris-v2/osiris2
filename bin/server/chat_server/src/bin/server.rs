use tokio::net::TcpListener;
use tokio_tungstenite::{accept_async, tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::fs;
//use std::env;
use std::error::Error;
use log::{info, error, warn};
use uuid::Uuid;

/* APP */

/*
struct Config {
    ip: Option<String>,
    port: Option<u16>,
    servers: Option<HashMap<String, String>>,
}
*/

#[tokio::main]

async fn main() -> Result<(), Box<dyn Error>> {


//    match env::current_dir() {
//        Ok(dir) => println!("El servidor se está ejecutando en: {}", dir.display()),
//        Err(e) => eprintln!("Error al obtener el directorio actual: {}", e),
//    }

    // Inicializa la librería de logs
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let addr = "0.0.0.0:8081";  // Dirección y puerto de escucha
    let listener = TcpListener::bind(addr).await?;
    info!("Servidor WebSocket escuchando en {}", addr);

    while let Ok((stream, _)) = listener.accept().await {
        tokio::spawn(handle_connection(stream)); // Procesar cada conexión en un hilo separado
    }

    Ok(())
}

async fn handle_connection(stream: tokio::net::TcpStream) {
    let client_id = Uuid::new_v4(); // Genera un identificador único para el cliente
    info!("\nCliente conectado: {}", client_id);

    match accept_async(stream).await {
        Ok(ws_stream) => {
            let (mut write, mut read) = ws_stream.split();

            while let Some(result) = read.next().await {
                match result {
                    Ok(msg) => match msg {
                        Message::Text(text) => {
                            info!("Cliente {} envió: {}", client_id, text);
                            match handle_command(&text).await {
                                Ok(response) => {
                                    if !response.is_empty() {
                                        if let Err(e) = write.send(Message::Text(response)).await {
                                            error!("Error al enviar respuesta a {}: \n{}", client_id, e);
                                        }
                                    }
                                },
                                Err(e) => {
                                    error!("Error al procesar el comando de {}: {}", client_id, e);
                                    let _ = write.send(Message::Text(format!("Error: {}", e))).await;
                                }
                            }
                        },
                        Message::Binary(_) => {
                            warn!("Cliente {} envió un mensaje binario (no soportado)", client_id);
                            let _ = write.send(Message::Text("Mensaje binario no soportado".to_string())).await;
                        },
                        _ => {
                            warn!("\nCliente {} \nenvió un tipo de mensaje no soportado", client_id);
                            let _ = write.send(Message::Text("Tipo de mensaje no soportado".to_string())).await;
                        }
                    },
                    Err(e) => {
                        error!("\nError al leer del cliente {}: {}", client_id, e);
                        break;
                    }
                }
            }
            info!("Cliente desconectado: {}", client_id);
        },
        Err(e) => error!("\nError al aceptar conexión WebSocket: \n{}", e),
    }
}

async fn handle_command(command: &str) -> Result<String, String> {
    match command {
        "/date" => Ok(chrono::Local::now().to_rfc3339()),

        "/hello" => Ok("Hola, cliente! 👋".to_string()),

        "/help" => Ok(
            "/date - Obtiene la fecha y hora actual.\n\
             /hello - Saludo de bienvenida.\n\
             /servers - Lista de servidores disponibles.".to_string()
        ),

        "/servers" => list_servers(), // Lee el archivo de servidores

        "" => Ok("".to_string()),

        _ => Err(format!("Comando no reconocido: {} 🤔", command)),
    }
}

fn list_servers() -> Result<String, String> {
    match fs::read_to_string("../../../../net/rserver.nrl") {
        Ok(content) => Ok(content),
        Err(e) => Err(format!("Error al leer el archivo de servidores: {}", e)),
    }
}

