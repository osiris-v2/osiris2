use tokio::net::TcpListener;
use tokio_tungstenite::{accept_async, tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::fs;
use std::error::Error;
use log::{info, error, warn};
use uuid::Uuid;
use rand::{Rng, thread_rng}; // Añadido para la generación de números aleatorios
use std::io; // Añadido para io::ErrorKind

/* APP */

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Inicializa la librería de logs
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let base_ip = "0.0.0.0";
    let default_port = 8081;
    let min_random_port = 20000;
    let max_random_port = 65000;
    const MAX_BIND_ATTEMPTS: u8 = 10; // Límite de intentos para encontrar un puerto

    let mut listener: Option<TcpListener> = None;
    let mut attempts = 0;

    // Bucle para intentar enlazar el puerto
    loop {
        attempts += 1;
        if attempts > MAX_BIND_ATTEMPTS {
            error!("Excedido el número máximo de intentos para encontrar un puerto disponible.");
            return Err("Falló al enlazar a un puerto después de múltiples intentos.".into());
        }

        let current_port = if attempts == 1 {
            default_port // Primer intento con el puerto por defecto
        } else {
            // Intentos subsiguientes con un puerto aleatorio
            thread_rng().gen_range(min_random_port..=max_random_port)
        };

        let addr_str = format!("{}:{}", base_ip, current_port);
        info!("Intento de enlazar a {}", addr_str);

        match TcpListener::bind(&addr_str).await {
            Ok(l) => {
                listener = Some(l);
                break; // Éxito al enlazar, salimos del bucle
            },
            Err(e) => {
                if e.kind() == io::ErrorKind::AddrInUse {
                    warn!("El puerto {} está en uso. Intentando con otro...", current_port);
                    // Continuamos al siguiente intento con un puerto aleatorio
                } else {
                    // Otros errores (permiso, etc.) son críticos
                    error!("Error crítico al intentar enlazar a {}: {}", addr_str, e);
                    return Err(e.into());
                }
            }
        }
    }

    // Si llegamos aquí, listener debe ser Some(TcpListener)
    let listener = listener.unwrap();

    // Imprimir los datos de conexión reales
    let local_addr = listener.local_addr()?;
    info!("¡Servidor WebSocket iniciado y escuchando en: {}", local_addr);
    info!("Dirección IP: {}", local_addr.ip());
    info!("Puerto: {}", local_addr.port());

    while let Ok((stream, _)) = listener.accept().await {
        tokio::spawn(handle_connection(stream)); // Procesar cada conexión en una tarea (hilo asíncrono) separada
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
        "/way" => Ok("Sistema ODyN en desarrollo \n https://github.com/osiris-v2/osiris2 \n Sistema de servidores dinámicos para osiris2 \n Seed server ".to_string()),
        "/help" => Ok("\n\
            /date - Obtiene la fecha y hora actual.\n\
             /hello - Saludo de bienvenida.\n\
             /servers - Lista de servidores disponibles.\n\
             /way - Who Are You?. \n Información sobre la organización o persona que corre el servidor".to_string()), 
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