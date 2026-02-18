use tokio::net::TcpListener;
use tokio_tungstenite::{accept_async, tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::fs;
use std::error::Error;
use log::{info, error, warn};
use uuid::Uuid;
use rand::{Rng, thread_rng};
use std::io;
use serde::Deserialize;
use serde_json::json;
use std::sync::Arc;
use tokio::sync::{Semaphore, Mutex, OwnedSemaphorePermit};
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use tokio::task::AbortHandle; 
//use chrono::Local;



// --- CONFIGURACIÓN GLOBAL ---
const MAX_GLOBAL_INSTANCES: usize = 2; 
const AVAILABLE_MODELS: &[&str] = &[
"qwen3:0.6b",
"llama3.2:1b", 
"smollm2:135m",
"smollm2:360m",
"smollm2:1.7b",
"Qwen2.5:1.5b", 
"qwen2:0.5b",
"Qwen2.5:0.5b",
"tinyllama:latest",
"llama3.2:latest",
"tinyllama", 
"dolphin-phi:latest",
"gemma3:270m",
"gemma2:2b",
"deepseek-coder:1.3b",
"deepseek-r1:1.5b",
"huihui_ai/phi4-mini-abliterated:latest"];

static ACTIVE_AI_INSTANCES: AtomicUsize = AtomicUsize::new(0);

struct AiInstanceGuard {
    _permit: OwnedSemaphorePermit,
}
impl AiInstanceGuard {
    fn new(permit: OwnedSemaphorePermit) -> Self {
        ACTIVE_AI_INSTANCES.fetch_add(1, Ordering::SeqCst);
        Self { _permit: permit }
    }
}
impl Drop for AiInstanceGuard {
    fn drop(&mut self) {
        ACTIVE_AI_INSTANCES.fetch_sub(1, Ordering::SeqCst);
    }
}

struct ClientSession {
    context: Vec<i64>,
    model: String,
    is_busy: bool,
    abort_handle: Option<AbortHandle>, 
}

lazy_static::lazy_static! {
    static ref AI_LIMIT_SEM: Arc<Semaphore> = Arc::new(Semaphore::new(MAX_GLOBAL_INSTANCES));
    static ref AI_SESSIONS: Mutex<HashMap<Uuid, ClientSession>> = Mutex::new(HashMap::new());
}

#[derive(Deserialize)]
struct TVChannel {
    canal: String,
    url: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let base_ip = "0.0.0.0";
    let default_port = 8081;
    let min_random_port = 20000;
    let max_random_port = 65000;
    const MAX_BIND_ATTEMPTS: u8 = 10;

    let mut attempts = 0;
    let listener = loop {
        attempts += 1;
        if attempts > MAX_BIND_ATTEMPTS {
            return Err("Falló al enlazar a un puerto disponible.".into());
        }
        let current_port = if attempts == 1 { default_port } else { thread_rng().gen_range(min_random_port..=max_random_port) };
        let addr_str = format!("{}:{}", base_ip, current_port);

        match TcpListener::bind(&addr_str).await {
            Ok(l) => {
                info!("¡Servidor iniciado en: {}!", addr_str);
                break l;
            },
            Err(e) if e.kind() == io::ErrorKind::AddrInUse => {
                warn!("Puerto {} en uso, reintentando...", current_port);
            },
            Err(e) => return Err(e.into()),
        }
    };

    while let Ok((stream, _)) = listener.accept().await {
        tokio::spawn(handle_connection(stream));
    }
    Ok(())
}

async fn handle_connection(stream: tokio::net::TcpStream) {
    let client_id = Uuid::new_v4();
    {
        let mut sessions = AI_SESSIONS.lock().await;
        sessions.insert(client_id, ClientSession { 
            context: Vec::new(), 
            model: AVAILABLE_MODELS[0].to_string(), 
            is_busy: false,
            abort_handle: None
        });
    }

    if let Ok(ws_stream) = accept_async(stream).await {
        let (write, mut read) = ws_stream.split();
        let write_arc = Arc::new(Mutex::new(write));

        while let Some(Ok(msg)) = read.next().await {
            if let Message::Text(text) = msg {
                let text_trimmed = text.trim().to_string(); 
                if text_trimmed.is_empty() { continue; }

                info!("[DEBUG] Cliente {}: {}", client_id, text_trimmed);

                if text_trimmed == "/stop" {
                    let mut sessions = AI_SESSIONS.lock().await;
                    if let Some(s) = sessions.get_mut(&client_id) {
                        if let Some(handle) = s.abort_handle.take() {
                            handle.abort();
                            s.is_busy = false;
                            let _ = write_arc.lock().await.send(Message::Text("🛑 Generación abortada.".into())).await;
                        } else {
                            let _ = write_arc.lock().await.send(Message::Text("⚠️ No hay proceso activo para detener.".into())).await;
                        }
                    }
                    continue;
                }

                let client_busy = {
                    let sessions = AI_SESSIONS.lock().await;
                    sessions.get(&client_id).map(|s| s.is_busy).unwrap_or(false)
                };

                if client_busy {
                    let _ = write_arc.lock().await.send(Message::Text("❌ RECHAZADO: Espera a que termine la respuesta actual.\n".into())).await;
                    continue;
                }

                if text_trimmed.starts_with('/') {
                    let resp = handle_command(&text_trimmed, client_id).await;
                    let _ = write_arc.lock().await.send(Message::Text(resp.unwrap_or_else(|e| format!("Error: {}", e)))).await;
                } else {
                    match AI_LIMIT_SEM.clone().try_acquire_owned() {
                        Ok(permit) => {
                            {
                                let mut sessions = AI_SESSIONS.lock().await;
                                if let Some(s) = sessions.get_mut(&client_id) { s.is_busy = true; }
                            }

                            let write_clone = Arc::clone(&write_arc);
                            let text_for_ai = text_trimmed.clone();

                            let task = tokio::spawn(async move {
                                let _guard = AiInstanceGuard::new(permit);
                                
                                let res = preguntar_ollama_stream(&text_for_ai, client_id, write_clone.clone()).await;
                                
                                if let Err(e) = res {
                                    error!("Error en flujo de IA: {}", e);
                                    let _ = write_clone.lock().await.send(Message::Text(format!("\n⚠️ ERROR: {}. Prueba a usar /clearcontext si el error persiste.", e))).await;
                                }
                                
                                let mut sessions = AI_SESSIONS.lock().await;
                                if let Some(s) = sessions.get_mut(&client_id) { 
                                    s.is_busy = false; 
                                    s.abort_handle = None;
                                }
                            });

                            let mut sessions = AI_SESSIONS.lock().await;
                            if let Some(s) = sessions.get_mut(&client_id) {
                                s.abort_handle = Some(task.abort_handle());
                            }
                        },
                        Err(_) => {
                            let msg = format!("⚠️ SISTEMA SATURADO: Ya hay {} instancias activas. Espera a que alguien termine.\n", MAX_GLOBAL_INSTANCES);
                            let _ = write_arc.lock().await.send(Message::Text(msg)).await;
                        }
                    }
                }
            }
        }
        AI_SESSIONS.lock().await.remove(&client_id);
    }
}

async fn handle_command(command: &str, client_id: Uuid) -> Result<String, String> {
    let parts: Vec<&str> = command.split_whitespace().collect();
    match parts[0] {
        "/clearcontext" => {
            let mut sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get_mut(&client_id) {
                s.context.clear();
                Ok("🧹 Contexto borrado. Generando nueva sesión.".into())
            } else { Err("Sesión no encontrada.".into()) }
        },
        "/model" => {
            let idx: usize = parts.get(1).and_then(|s| s.parse().ok()).ok_or("Uso: /model [N]")?;
            if idx < AVAILABLE_MODELS.len() {
                let mut sessions = AI_SESSIONS.lock().await;
                if let Some(s) = sessions.get_mut(&client_id) {
                    s.model = AVAILABLE_MODELS[idx].to_string();
                    Ok(format!("✅ IA cambiada a: {}. (Contexto conservado)", AVAILABLE_MODELS[idx]))
                } else { Err("Sesión no encontrada.".into()) }
            } else { Err("El índice de modelo no existe.".into()) }
        },
        "/limit" => {
            let active = ACTIVE_AI_INSTANCES.load(Ordering::SeqCst);
            let total = MAX_GLOBAL_INSTANCES;
            Ok(format!("\n📊 ESTADO:\n- Activos: {}\n- Disponibles: {}\n- Límite: {}\n", active, total.saturating_sub(active), total))
        },
        "/models" => {
            let mut list = String::from("\n🤖 MODELOS:\n");
            for (i, m) in AVAILABLE_MODELS.iter().enumerate() {
                list.push_str(&format!("{}: {}\n", i, m));
            }
            Ok(list)
        },
        "/help" => Ok(r#"
📖 COMANDOS DISPONIBLES:
/help         - Muestra esta lista de ayuda.
/stop         - Detiene la generación de la IA inmediatamente.
/clearcontext - Borra el contexto actual de la conversación.
/limit        - Muestra cuántas instancias de IA hay en uso y libres.
/models       - Lista todos los modelos disponibles en el servidor.
/model N      - Cambia al modelo N (ej: /model 1). Mantiene el contexto.
/date         - Muestra la fecha y hora actual del servidor.
/listtv       - Muestra la lista de canales de TV activos y sus enlaces.
/servers      - Muestra la lista de servidores remotos (.nrl).
/way          - Muestra información sobre el sistema ODyN.
/hello        - Test rápido de respuesta del servidor.
"#.into()),
        "/date" => Ok(format!("📅 {}", chrono::Local::now().to_rfc3339())),
        "/hello" => Ok("👋 GoyimAI en línea.".into()),
        "/way" => Ok("Sistema ODyN - Goyim United Corp.".into()),
        "/listtv" => list_tv_channels(),
        "/servers" => list_servers(),
        _ => Err("Comando desconocido. Escribe /help".into())
    }
}

async fn preguntar_ollama_stream(prompt: &str, client_id: Uuid, write_sink: Arc<Mutex<futures_util::stream::SplitSink<tokio_tungstenite::WebSocketStream<tokio::net::TcpStream>, Message>>>) -> Result<(), Box<dyn Error + Send + Sync>> {
    let client = reqwest::Client::builder().timeout(std::time::Duration::from_secs(420)).build()?;
    
    let (ctx, model) = {
        let sessions = AI_SESSIONS.lock().await;
        let s = sessions.get(&client_id).ok_or("Sesión perdida")?;
        (s.context.clone(), s.model.clone())
    };

// Generamos la marca de tiempo de forma no invasiva
        let ahora = chrono::Local::now().format("%d/%m/%Y %H:%M:%S").to_string();

let instrucciones_extra = fs::read_to_string("instrucciones.txt")
    .unwrap_or_else(|_| "Instrucciones por defecto".to_string());

// 2. Lo concatenas en el campo "system"
let body = json!({ 
    "model": model, 
    "prompt": prompt, 
    "stream": true, 
    "context": if ctx.is_empty() { None } else { Some(ctx) }, 
    "system": format!(
        "Eres una IA de GoyCorp. Fecha/Hora actual: {}. \
        Instrucciones de identidad: Ser goyim es una cualidad positiva... \
        Instrucciones adicionales del archivo: \n{}", 
        ahora, 
        instrucciones_extra
    )
});


    let mut res = client.post("http://localhost:11434/api/generate").json(&body).send().await?;

    if !res.status().is_success() {
        let status = res.status();
        let err_text = format!("❌ Error API Ollama ({}). Revisa el modelo: {}", status, model);
        let _ = write_sink.lock().await.send(Message::Text(err_text.clone())).await;
        return Err(err_text.into());
    }

    while let Some(chunk) = res.chunk().await? {
        let text = String::from_utf8_lossy(&chunk);
        for line in text.split('\n') {
            if line.is_empty() { continue; }
            if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(line) {
                if let Some(token) = json_val["response"].as_str() {
                    let _ = write_sink.lock().await.send(Message::Text(token.to_string())).await;
                }
                if json_val["done"].as_bool().unwrap_or(false) {
                    if let Some(new_ctx) = json_val["context"].as_array() {
                        let ctx_vec: Vec<i64> = new_ctx.iter().filter_map(|v| v.as_i64()).collect();
                        let mut sessions = AI_SESSIONS.lock().await;
                        if let Some(s) = sessions.get_mut(&client_id) { s.context = ctx_vec; }
                    }
                    let _ = write_sink.lock().await.send(Message::Text("\n".into())).await;
                }
            }
        }
    }
    Ok(())
}

fn list_tv_channels() -> Result<String, String> {
    let data = fs::read_to_string("../../../../com/datas/ffmpeg/activos.json").map_err(|e| e.to_string())?;
    let channels: Vec<TVChannel> = serde_json::from_str(&data).map_err(|e| e.to_string())?;
    let mut resp = String::from("\n📺 TV:\n");
    for ch in channels {
        resp.push_str(&format!(" <a href='https://osiris000.duckdns.org/app/mitv/tv/player2.php?chn={}' target='_blank'>[VER]</a> **{}**   \n", ch.url, ch.canal));
    }
    Ok(resp)
}

fn list_servers() -> Result<String, String> {
    fs::read_to_string("../../../../net/rserver.nrl").map_err(|e| e.to_string())
}