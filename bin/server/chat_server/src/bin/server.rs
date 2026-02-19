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

// --- CONFIGURACIÓN GLOBAL ---
const MAX_GLOBAL_INSTANCES: usize = 2;
const MAX_HISTORY_MESSAGES: usize = 20;
const DEFAULT_MODEL_FALLBACK: &str = "llama3.2:latest";
const OLLAMA_URL: &str = "http://localhost:11434";
const OLLAMA_TIMEOUT_SECS: u64 = 500;

static ACTIVE_AI_INSTANCES: AtomicUsize = AtomicUsize::new(0);

// Comandos que responden siempre aunque la IA esté ocupada (is_busy).
// Solo los que devuelven widgets de datos — no bloquean al usuario esperando una respuesta IA.
// /help, /limit, /hello, /way SÍ se bloquean porque son respuestas de texto que podrían
// confundirse con la respuesta IA en curso y desorientar al usuario.
fn es_comando_libre(cmd: &str) -> bool {
    let base = cmd.split_whitespace().next().unwrap_or("");
    matches!(base,
        "/listtv" | "/info" | "/date" | "/servers" | "/models"
    )
}

// --- GUARDS DE SEMÁFORO ---
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

// --- SESIÓN DE CLIENTE ---
struct ClientSession {
    /// Tokens de contexto Ollama (específicos del modelo activo, se resetean al cambiar modelo)
    context: Vec<i64>,
    /// Historial legible conservado incluso al cambiar de modelo
    history_text: Vec<(String, String)>, // (user_msg, assistant_response)
    model: String,
    is_busy: bool,
    abort_handle: Option<AbortHandle>,
    connected_at: chrono::DateTime<chrono::Local>,
    messages_sent: usize,
}

impl ClientSession {
    fn new(model: String) -> Self {
        Self {
            context: Vec::new(),
            history_text: Vec::new(),
            model,
            is_busy: false,
            abort_handle: None,
            connected_at: chrono::Local::now(),
            messages_sent: 0,
        }
    }

    fn add_history(&mut self, user: String, assistant: String) {
        self.history_text.push((user, assistant));
        if self.history_text.len() > MAX_HISTORY_MESSAGES {
            self.history_text.remove(0);
        }
        self.messages_sent += 1;
    }

    fn history_as_text(&self) -> String {
        if self.history_text.is_empty() { return String::new(); }
        let mut out = String::from("\n--- Conversación previa ---\n");
        for (u, a) in &self.history_text {
            out.push_str(&format!("Usuario: {}\nAsistente: {}\n", u, a));
        }
        out.push_str("---\n");
        out
    }
}

// --- ESTRUCTURAS DE DESERIALIZACIÓN ---
#[derive(Deserialize, serde::Serialize, Clone)]
struct TVChannel {
    canal: String,
    url: String,
}

// --- LAZY STATICS ---
lazy_static::lazy_static! {
    static ref AI_LIMIT_SEM: Arc<Semaphore> = Arc::new(Semaphore::new(MAX_GLOBAL_INSTANCES));
    static ref AI_SESSIONS: Mutex<HashMap<Uuid, ClientSession>> = Mutex::new(HashMap::new());
    static ref SERVER_START_TIME: chrono::DateTime<chrono::Local> = chrono::Local::now();
}

// --- PROTOCOLO WIDGET ---
// Envuelve datos en el formato estándar que el cliente reconoce y renderiza como panel flotante:
// { "type": "widget", "widget": "<nombre>", "version": 1, "data": { ... } }
fn widget_msg(widget: &str, version: u32, data: serde_json::Value) -> String {
    json!({
        "type":    "widget",
        "widget":  widget,
        "version": version,
        "data":    data
    }).to_string()
}

// --- HELPERS DE SISTEMA ---

fn leer_ram() -> (u64, u64, u64) {
    // devuelve (total_mb, available_mb, used_mb)
    let meminfo = fs::read_to_string("/proc/meminfo").unwrap_or_default();
    let mut total_kb = 0u64;
    let mut avail_kb = 0u64;
    for line in meminfo.lines() {
        if line.starts_with("MemTotal:")     { total_kb = line.split_whitespace().nth(1).and_then(|v| v.parse().ok()).unwrap_or(0); }
        if line.starts_with("MemAvailable:") { avail_kb  = line.split_whitespace().nth(1).and_then(|v| v.parse().ok()).unwrap_or(0); }
    }
    let total = total_kb / 1024;
    let avail = avail_kb / 1024;
    (total, avail, total.saturating_sub(avail))
}

fn leer_uptime_os() -> u64 {
    fs::read_to_string("/proc/uptime").ok()
        .and_then(|s| s.split_whitespace().next().and_then(|v| v.parse::<f64>().ok()))
        .map(|f| f as u64).unwrap_or(0)
}

fn formatear_duracion(secs: u64) -> String {
    let d = secs / 86400;
    let h = (secs % 86400) / 3600;
    let m = (secs % 3600) / 60;
    if d > 0 { format!("{}d {}h {}m", d, h, m) }
    else if h > 0 { format!("{}h {}m", h, m) }
    else { format!("{}m", m) }
}

/// Heurística de RAM necesaria por nombre de modelo
fn ram_necesaria_mb(modelo: &str) -> u64 {
    if modelo.contains("phi4") || modelo.contains("phi-4")            { 3500 }
    else if modelo.contains("7b") || modelo.contains("8b")            { 5000 }
    else if modelo.contains("3b") || modelo.contains("4b")            { 3000 }
    else if modelo.contains("1.5b") || modelo.contains("1.7b") || modelo.contains("1b") { 1200 }
    else if modelo.contains("360m") || modelo.contains("0.5b") || modelo.contains("0.6b") { 600 }
    else if modelo.contains("135m") || modelo.contains("270m")        { 400 }
    else                                                               { 2000 }
}

// --- OLLAMA HELPERS ---

async fn obtener_modelos_ollama() -> Vec<String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build().unwrap_or_default();
    match client.get(format!("{}/api/tags", OLLAMA_URL)).send().await {
        Ok(res) => res.json::<serde_json::Value>().await.ok()
            .and_then(|j| j["models"].as_array().map(|a|
                a.iter().filter_map(|m| m["name"].as_str().map(|s| s.to_string())).collect()
            )).unwrap_or_default(),
        Err(e) => { warn!("No se pudo contactar Ollama (tags): {}", e); vec![] }
    }
}

/// Modelos actualmente cargados en RAM por Ollama (/api/ps)
async fn obtener_modelos_en_ram() -> Vec<String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build().unwrap_or_default();
    match client.get(format!("{}/api/ps", OLLAMA_URL)).send().await {
        Ok(res) => res.json::<serde_json::Value>().await.ok()
            .and_then(|j| j["models"].as_array().map(|a|
                a.iter().filter_map(|m| m["name"].as_str().map(|s| s.to_string())).collect()
            )).unwrap_or_default(),
        Err(_) => vec![],
    }
}

async fn ollama_disponible() -> bool {
    reqwest::Client::builder().timeout(std::time::Duration::from_secs(3))
        .build().unwrap_or_default()
        .get(format!("{}/api/tags", OLLAMA_URL)).send().await.is_ok()
}

// --- MAIN ---
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info")
    ).init();

    // Inicializar tiempo de arranque del servidor
    let _ = *SERVER_START_TIME;

    if ollama_disponible().await {
        let modelos = obtener_modelos_ollama().await;
        info!("Ollama activo. {} modelo(s) disponible(s).", modelos.len());
        for m in &modelos { info!("  - {}", m); }
    } else {
        warn!("⚠️  Ollama no responde en {}. El servidor iniciará igualmente.", OLLAMA_URL);
    }

    // --- Bind con fallback a puertos aleatorios si 8081 está ocupado ---
    let base_ip        = "0.0.0.0";
    let default_port   = 8081u16;
    let min_rand_port  = 20000u16;
    let max_rand_port  = 65000u16;
    const MAX_BIND_ATTEMPTS: u8 = 10;

    let mut attempts = 0u8;
    let listener = loop {
        attempts += 1;
        if attempts > MAX_BIND_ATTEMPTS {
            return Err("Falló al enlazar a un puerto disponible tras 10 intentos.".into());
        }
        let current_port = if attempts == 1 {
            default_port
        } else {
            thread_rng().gen_range(min_rand_port..=max_rand_port)
        };
        let addr_str = format!("{}:{}", base_ip, current_port);

        match TcpListener::bind(&addr_str).await {
            Ok(l) => {
                info!("✅ Servidor WebSocket iniciado en: ws://{}", addr_str);
                break l;
            }
            Err(e) if e.kind() == io::ErrorKind::AddrInUse => {
                warn!("Puerto {} en uso, reintentando con puerto aleatorio...", current_port);
            }
            Err(e) => return Err(e.into()),
        }
    };

    info!("Esperando conexiones (máx. {} instancias IA simultáneas)...", MAX_GLOBAL_INSTANCES);

    while let Ok((stream, addr)) = listener.accept().await {
        info!("Nueva conexión desde: {}", addr);
        tokio::spawn(handle_connection(stream));
    }
    Ok(())
}

// --- MANEJO DE CONEXIÓN ---
async fn handle_connection(stream: tokio::net::TcpStream) {
    let client_id = Uuid::new_v4();

    // Modelo inicial = primer modelo disponible en Ollama
    let modelo_inicial = obtener_modelos_ollama().await
        .into_iter().next()
        .unwrap_or_else(|| DEFAULT_MODEL_FALLBACK.to_string());

    {
        let mut sessions = AI_SESSIONS.lock().await;
        sessions.insert(client_id, ClientSession::new(modelo_inicial.clone()));
    }

    info!("Cliente {} conectado. Modelo inicial: {}", client_id, modelo_inicial);

    if let Ok(ws_stream) = accept_async(stream).await {
        let (write, mut read) = ws_stream.split();
        let write_arc = Arc::new(Mutex::new(write));

        // Bienvenida como widget (el cliente lo renderiza en panel flotante)
        let bienvenida = widget_msg("welcome", 1, json!({
            "id":      &client_id.to_string()[..8],
            "model":   modelo_inicial,
            "message": "Escribe /help para ver los comandos disponibles."
        }));
        let _ = write_arc.lock().await.send(Message::Text(bienvenida)).await;

        while let Some(Ok(msg)) = read.next().await {
            if let Message::Text(text) = msg {
                let text_trimmed = text.trim().to_string();
                if text_trimmed.is_empty() { continue; }

                info!("[{}] << {}", &client_id.to_string()[..8], text_trimmed);

                // --- /stop: prioridad absoluta, siempre responde ---
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

                // --- Comandos libres: responden siempre, ignoran is_busy y semáforo ---
                if text_trimmed.starts_with('/') && es_comando_libre(&text_trimmed) {
                    let resp = handle_command(&text_trimmed, client_id).await;
                    let out = resp.unwrap_or_else(|e| format!("❌ {}", e));
                    let _ = write_arc.lock().await.send(Message::Text(out)).await;
                    continue;
                }

                // --- Rechazar si el cliente está ocupado generando ---
                let client_busy = {
                    let sessions = AI_SESSIONS.lock().await;
                    sessions.get(&client_id).map(|s| s.is_busy).unwrap_or(false)
                };
                if client_busy {
                    let _ = write_arc.lock().await.send(Message::Text(
                        "❌ RECHAZADO: Espera a que termine la respuesta actual. Usa /stop para cancelarla.\n".into()
                    )).await;
                    continue;
                }

                // --- Comandos no libres (clearcontext, model N...) ---
                if text_trimmed.starts_with('/') {
                    let resp = handle_command(&text_trimmed, client_id).await;
                    let out = resp.unwrap_or_else(|e| format!("Error: {}", e));
                    let _ = write_arc.lock().await.send(Message::Text(out)).await;
                    continue;
                }

                // --- Mensaje IA ---
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
                                error!("Error en flujo de IA [{}]: {}", client_id, e);
                                let _ = write_clone.lock().await.send(Message::Text(
                                    format!("\n⚠️ ERROR: {}. Prueba /clearcontext si persiste.", e)
                                )).await;
                            }

                            let mut sessions = AI_SESSIONS.lock().await;
                            if let Some(s) = sessions.get_mut(&client_id) {
                                s.is_busy = false;
                                s.abort_handle = None;
                            }
                        });

                        // FIX deadlock: abort_handle se obtiene antes de cualquier lock de sesiones
                        let abort_handle = task.abort_handle();
                        {
                            let mut sessions = AI_SESSIONS.lock().await;
                            if let Some(s) = sessions.get_mut(&client_id) {
                                s.abort_handle = Some(abort_handle);
                            }
                        }
                    }
                    Err(_) => {
                        let msg = format!(
                            "⚠️ SISTEMA SATURADO: Ya hay {} instancias activas. Espera a que alguien termine.\n",
                            MAX_GLOBAL_INSTANCES
                        );
                        let _ = write_arc.lock().await.send(Message::Text(msg)).await;
                    }
                }
            }
        }

        info!("Cliente {} desconectado.", client_id);
        AI_SESSIONS.lock().await.remove(&client_id);
    }
}

// --- MANEJO DE COMANDOS ---
async fn handle_command(command: &str, client_id: Uuid) -> Result<String, String> {
    let parts: Vec<&str> = command.split_whitespace().collect();

    match parts[0] {
        "/help" => Ok(r#"
📖 COMANDOS DISPONIBLES:
  /help           - Muestra esta ayuda.
  /stop           - Detiene la generación actual.
  /clearcontext   - Borra contexto e historial.
  /limit          - Estado de instancias IA.
  /models         - Lista modelos instalados en Ollama.
  /model N        - Cambia al modelo N (historial conservado).
  /info           - Métricas del servidor y tu sesión.
  /listtv         - Canales TV activos.
  /servers        - Servidores remotos.
  /way            - Info del sistema ODyN.
  /hello          - Test de conexión.
"#.into()),

        "/clearcontext" => {
            let mut sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get_mut(&client_id) {
                s.context.clear();
                s.history_text.clear();
                Ok("🧹 Contexto e historial borrados. Generando nueva sesión.".into())
            } else { Err("Sesión no encontrada.".into()) }
        }

        "/model" => {
            let idx: usize = parts.get(1).and_then(|s| s.parse().ok())
                .ok_or("Uso: /model [N] — usa /models para ver la lista.")?;
            if idx == 0 { return Err("Los modelos empiezan en 1. Usa /models.".into()); }

            let modelos = obtener_modelos_ollama().await;
            if modelos.is_empty() { return Err("Ollama no responde o no hay modelos instalados.".into()); }

            let nombre = modelos.get(idx - 1)
                .ok_or_else(|| format!("Índice inválido. Hay {} modelo(s). Usa /models.", modelos.len()))?
                .clone();

            // Aviso de RAM solo si el modelo no está ya cargado y no cabe cómodamente
            let (_, avail_mb, _) = leer_ram();
            let en_ram = obtener_modelos_en_ram().await.iter().any(|m| m == &nombre);
            let aviso_ram = if !en_ram && avail_mb < ram_necesaria_mb(&nombre) {
                format!("\n⚠️  RAM disponible: {}MB — este modelo puede requerir swap y tardar más.", avail_mb)
            } else { String::new() };

            let mut sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get_mut(&client_id) {
                let anterior = s.model.clone();
                s.model = nombre.clone();
                // Tokens incompatibles entre modelos → reset, pero historial de texto se conserva
                s.context.clear();
                Ok(format!(
                    "✅ IA cambiada: {} → {}\n💬 Historial conservado ({} turnos).{}",
                    anterior, nombre, s.history_text.len(), aviso_ram
                ))
            } else { Err("Sesión no encontrada.".into()) }
        }

        "/models" => {
            let modelos = obtener_modelos_ollama().await;
            if modelos.is_empty() {
                return Ok("⚠️ Ollama no responde o no hay modelos instalados.".into());
            }

            let sessions = AI_SESSIONS.lock().await;
            let modelo_actual = sessions.get(&client_id).map(|s| s.model.clone()).unwrap_or_default();
            drop(sessions);

            let en_ram      = obtener_modelos_en_ram().await;
            let (total_mb, avail_mb, _) = leer_ram();

            // Devolver como widget para que el cliente lo renderice como panel interactivo
            let items: Vec<serde_json::Value> = modelos.iter().enumerate().map(|(i, m)| json!({
                "index":    i + 1,
                "name":     m,
                "active":   *m == modelo_actual,
                "in_ram":   en_ram.iter().any(|c| c == m),
                "fits_ram": avail_mb >= ram_necesaria_mb(m)
            })).collect();

            Ok(widget_msg("models", 1, json!({
                "ram_total_mb":     total_mb,
                "ram_available_mb": avail_mb,
                "models":           items
            })))
        }

        "/limit" => {
            let activos = ACTIVE_AI_INSTANCES.load(Ordering::SeqCst);
            let total   = MAX_GLOBAL_INSTANCES;
            let clientes = AI_SESSIONS.lock().await.len();
            Ok(format!(
                "\n📊 ESTADO:\n  Instancias IA: {}/{}\n  Disponibles: {}\n  Clientes conectados: {}\n",
                activos, total, total.saturating_sub(activos), clientes
            ))
        }

        // /date es alias de /info para compatibilidad con el botón del drawer
        "/date" | "/info" => {
            let ahora = chrono::Local::now();
            let (total_mb, avail_mb, used_mb) = leer_ram();
            let uptime_os  = leer_uptime_os();
            let activos    = ACTIVE_AI_INSTANCES.load(Ordering::SeqCst);

            let sessions = AI_SESSIONS.lock().await;
            let clientes   = sessions.len();
            let mi         = sessions.get(&client_id);
            let mi_modelo  = mi.map(|s| s.model.clone()).unwrap_or_default();
            let mi_turnos  = mi.map(|s| s.history_text.len()).unwrap_or(0);
            let mi_msgs    = mi.map(|s| s.messages_sent).unwrap_or(0);
            let conectado  = mi.map(|s|
                formatear_duracion(ahora.signed_duration_since(s.connected_at).num_seconds().max(0) as u64)
            ).unwrap_or_default();
            let mi_id      = client_id.to_string()[..8].to_string();
            drop(sessions);

            let en_ram     = obtener_modelos_en_ram().await;
            let uptime_srv = formatear_duracion(
                ahora.signed_duration_since(*SERVER_START_TIME).num_seconds().max(0) as u64
            );
            let ram_pct    = if total_mb > 0 { (used_mb * 100) / total_mb } else { 0 };

            // Widget con todos los datos — el cliente los renderiza en panel bonito con barra de RAM, etc.
            Ok(widget_msg("info", 1, json!({
                "datetime": ahora.format("%d/%m/%Y %H:%M:%S").to_string(),
                "server": {
                    "uptime":    uptime_srv,
                    "uptime_os": formatear_duracion(uptime_os),
                    "clients":   clientes,
                    "ai_active": activos,
                    "ai_max":    MAX_GLOBAL_INSTANCES
                },
                "ram": {
                    "total_mb":     total_mb,
                    "used_mb":      used_mb,
                    "available_mb": avail_mb,
                    "used_pct":     ram_pct
                },
                "models_in_ram": en_ram,
                "session": {
                    "id":              mi_id,
                    "model":           mi_modelo,
                    "connected_since": conectado,
                    "messages":        mi_msgs,
                    "context_turns":   mi_turnos
                }
            })))
        }

        "/hello" => Ok("👋 GoyimAI en línea.".into()),
        "/way"   => Ok("Sistema ODyN - Goyim United Corp.".into()),
        "/listtv"  => list_tv_channels(),
        "/servers" => list_servers(),

        _ => Err(format!("Comando desconocido: '{}'. Escribe /help.", parts[0]))
    }
}

// --- INFERENCIA CON OLLAMA (STREAMING) ---
async fn preguntar_ollama_stream(
    prompt: &str,
    client_id: Uuid,
    write_sink: Arc<Mutex<futures_util::stream::SplitSink<
        tokio_tungstenite::WebSocketStream<tokio::net::TcpStream>, Message,
    >>>,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(OLLAMA_TIMEOUT_SECS))
        .build()?;

    let (ctx, model, history_text) = {
        let sessions = AI_SESSIONS.lock().await;
        let s = sessions.get(&client_id).ok_or("Sesión perdida")?;
        (s.context.clone(), s.model.clone(), s.history_as_text())
    };

    let ahora = chrono::Local::now().format("%d/%m/%Y %H:%M:%S").to_string();
    let instrucciones_extra = fs::read_to_string("instrucciones.txt")
        .unwrap_or_else(|_| "Instrucciones por defecto".to_string());

    let body = json!({
        "model":   model,
        "prompt":  prompt,
        "stream":  true,
        "context": if ctx.is_empty() { json!(null) } else { json!(ctx) },
        "system":  format!(
            "Eres una IA de GoyCorp. Fecha/Hora actual: {}.\nInstrucciones: {}\n{}",
            ahora, instrucciones_extra, history_text
        )
    });

    let mut res = client
        .post(format!("{}/api/generate", OLLAMA_URL))
        .json(&body)
        .send().await?;

    if !res.status().is_success() {
        let status    = res.status();
        let err_text  = format!("❌ Error API Ollama ({}). Revisa el modelo: {}", status, model);
        let _ = write_sink.lock().await.send(Message::Text(err_text.clone())).await;
        return Err(err_text.into());
    }

    let mut full_response  = String::new();
    let mut new_context: Vec<i64> = Vec::new();

    while let Some(chunk) = res.chunk().await? {
        let text = String::from_utf8_lossy(&chunk);
        for line in text.split('\n') {
            if line.is_empty() { continue; }
            if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(line) {

                if let Some(token) = json_val["response"].as_str() {
                    full_response.push_str(token);
                    let _ = write_sink.lock().await.send(Message::Text(token.to_string())).await;
                }

                if json_val["done"].as_bool().unwrap_or(false) {
                    if let Some(new_ctx) = json_val["context"].as_array() {
                        new_context = new_ctx.iter().filter_map(|v| v.as_i64()).collect();
                    }
                    let _ = write_sink.lock().await.send(Message::Text("\n".into())).await;
                }

                if let Some(err) = json_val["error"].as_str() {
                    return Err(format!("Ollama stream error: {}", err).into());
                }
            }
        }
    }

    // Guardar contexto e historial de texto
    let mut sessions = AI_SESSIONS.lock().await;
    if let Some(s) = sessions.get_mut(&client_id) {
        if !new_context.is_empty()    { s.context = new_context; }
        if !full_response.is_empty()  {
            s.add_history(prompt.to_string(), full_response.trim().to_string());
        }
    }

    Ok(())
}

// --- TV como widget ---
fn list_tv_channels() -> Result<String, String> {
    let data = fs::read_to_string("/var/osiris2/bin/com/datas/ffmpeg/activos.json")
        .map_err(|e| e.to_string())?;
    let channels: Vec<TVChannel> = serde_json::from_str(&data)
        .map_err(|e| e.to_string())?;

    if channels.is_empty() { return Ok("📺 No hay canales activos.".into()); }

    Ok(widget_msg("tv_channels", 1, json!({
        "channels": channels.iter().map(|ch| json!({ "canal": ch.canal, "url": ch.url })).collect::<Vec<_>>()
    })))
}

// --- SERVIDORES como widget ---
fn list_servers() -> Result<String, String> {
    let content = fs::read_to_string("/var/osiris2/bin/net/rserver.nrl")
        .map_err(|e| e.to_string())?;

    let servers: Vec<serde_json::Value> = content.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| json!({ "host": l.trim() }))
        .collect();

    Ok(widget_msg("servers", 1, json!({ "servers": servers })))
}
