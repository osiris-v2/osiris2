use tokio::net::TcpListener;
use tokio_tungstenite::{accept_async, tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::fs;
use std::error::Error;
use log::{info, error, warn};
use uuid::Uuid;
use rand::{Rng, thread_rng}; // Añadido para la generación de números aleatorios
use std::io; // Añadido para io::ErrorKind
use serde::Deserialize;
use serde_json::json;

// 2. Define la estructura que coincide con tu JSON
#[derive(Deserialize)]
struct TVChannel {
    canal: String,
    url: String,
    // Los demás campos se pueden omitir si no los usas, 
    // serde los ignorará automáticamente.
}
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
        "/way" => Ok("Sistema ODyN en desarrollo... \n Goyim United Corporation.".to_string()),
        "/listtv" => list_tv_channels(),
        "/help" => Ok(r#"
/date    - Obtiene la fecha y hora actual.
/hello   - Saludo de bienvenida.
/listtv  - Lista los canales de TV disponibles.
/servers - Lista de servidores.
/way     - Who Are You?
Cualquier otro texto será procesado por Goycoin IA (Ollama)."#.to_string()),
        "/servers" => list_servers(),
        "" => Ok("".to_string()),
        
        // CUALQUIER OTRA COSA: Se lo preguntamos a Ollama
        _ => {
            info!("Comando desconocido. Consultando a Ollama: {}", command);
            match preguntar_ollama(command).await {
                Ok(respuesta) => Ok(format!("🤖 IA: {}", respuesta)),
                Err(e) => Err(format!("Error al conectar con Ollama: {}", e)),
            }
        }
    }
}

async fn preguntar_ollama(prompt: &str) -> Result<String, Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();
    
    // Configuramos el prompt de sistema para que sepa quién es
    let full_prompt = format!(
        "  \
        : {}", 
        prompt
    );

    let response = client.post("http://localhost:11434/api/generate")
        .json(&json!({
            "model": "llama3.2:1b",
            "prompt": full_prompt,
            "stream": false
        }))
        .send()
        .await?
        .json::<serde_json::Value>()
        .await?;

    let texto = response["response"].as_str().unwrap_or("No obtuve respuesta del modelo.");
    Ok(texto.to_string())
}

// 4. Añade la función que lee y formatea el JSON
fn list_tv_channels() -> Result<String, String> {
    // Ajusta la ruta al archivo real
    let path = "../../../../com/datas/ffmpeg/activos.json"; 
    
    let data = fs::read_to_string(path)
        .map_err(|e| format!("Error al abrir archivo TV: {}", e))?;

    let channels: Vec<TVChannel> = serde_json::from_str(&data)
        .map_err(|e| format!("Error al procesar JSON de TV: {}", e))?;

    let mut response = String::from("\n📺 LISTA DE CANALES 📺\n");

    for channel in channels {
        response.push_str("--------------------------------\n");
response.push_str(&format!(
    "**CANAL:** {}\n**URL:** <a href='https://osiris000.duckdns.org/app/mitv/tv/player2.php?chn={}' target='_blank' style='color: #ff00ff; font-weight: bold;'>[CLIC PARA VER]</a>\n", 
    channel.canal, 
    channel.url
));
    }
    response.push_str("--------------------------------\n");

    Ok(response)
}

fn list_servers() -> Result<String, String> {
    match fs::read_to_string("../../../../net/rserver.nrl") {
        Ok(content) => Ok(content),
        Err(e) => Err(format!("Error al leer el archivo de servidores: {}", e)),
    }
}



