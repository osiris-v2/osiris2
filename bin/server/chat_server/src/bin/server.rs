use tokio::net::TcpListener;
use tokio_tungstenite::{tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::fs;
use std::fs::OpenOptions;
use std::error::Error;
use log::{info, error, warn};
use uuid::Uuid;
use rand::{Rng, thread_rng};
use std::io;
use std::io::Write;
use serde::Deserialize;
use serde_json::json;
use std::sync::Arc;
use tokio::sync::{Semaphore, Mutex, OwnedSemaphorePermit};
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use tokio::task::AbortHandle;
use std::sync::Mutex as StdMutex;
use tokio::sync::mpsc;

// --- CONFIGURACIÓN GLOBAL ---
const MAX_GLOBAL_INSTANCES: usize = 2;
const MAX_HISTORY_MESSAGES: usize = 20;
const DEFAULT_MODEL_FALLBACK: &str = "llama3.2:latest";
const OLLAMA_URL: &str = "http://localhost:11434";
const OLLAMA_TIMEOUT_SECS: u64 = 500;

// --- LOG DE CONEXIONES ---
const CONN_LOG_PATH: &str = "/var/log/goyimai_connections.log";
const CONN_LOG_MAX_BYTES: u64 = 256 * 1024; // 256 KB

// Longitud del short-id visible (chars hex aleatorios)
const SHORT_ID_LEN: usize = 8;

static ACTIVE_AI_INSTANCES: AtomicUsize = AtomicUsize::new(0);

/// Logger de conexiones con rotación por tamaño máximo.
struct ConnLogger {
    path: &'static str,
    max_bytes: u64,
    lock: StdMutex<()>,
}

impl ConnLogger {
    const fn new(path: &'static str, max_bytes: u64) -> Self {
        Self { path, max_bytes, lock: StdMutex::new(()) }
    }

    fn write(&self, line: &str) {
        let _guard = self.lock.lock().unwrap_or_else(|e| e.into_inner());
        if let Ok(meta) = fs::metadata(self.path) {
            if meta.len() >= self.max_bytes {
                if let Ok(content) = fs::read_to_string(self.path) {
                    let keep_from = content.len() / 2;
                    let cut = content[keep_from..].find('\n')
                        .map(|p| keep_from + p + 1)
                        .unwrap_or(keep_from);
                    let kept = format!("# --- rotación automática ---\n{}", &content[cut..]);
                    let _ = fs::write(self.path, kept);
                }
            }
        }
        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(self.path) {
            let _ = writeln!(f, "{}", line);
        }
    }

    fn log_connect(&self, short_id: &str, ip: &str, model: &str, total_clients: usize) {
        let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
        self.write(&format!(
            "{} | CONNECT   | {} | ip={} | model={} | total_clients={}",
            ts, short_id, ip, model, total_clients
        ));
    }

    fn log_disconnect(&self, short_id: &str, ip: &str, duration_secs: u64, messages: usize, total_clients: usize) {
        let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
        self.write(&format!(
            "{} | DISCONNECT | {} | ip={} | session_secs={} | messages={} | total_clients={}",
            ts, short_id, ip, duration_secs, messages, total_clients
        ));
    }

    fn log_event(&self, short_id: &str, ip: &str, event: &str) {
        let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
        self.write(&format!(
            "{} | EVENT      | {} | ip={} | {}",
            ts, short_id, ip, event
        ));
    }
}

lazy_static::lazy_static! {
    static ref CONN_LOG: ConnLogger = ConnLogger::new(CONN_LOG_PATH, CONN_LOG_MAX_BYTES);
}

// Comandos libres: responden siempre aunque la IA esté ocupada (is_busy).
fn es_comando_libre(cmd: &str) -> bool {
    let base = cmd.split_whitespace().next().unwrap_or("");
    matches!(base,
        "/listtv" | "/info" | "/date" | "/servers" | "/models" | "/who"
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

// Tipo del sender por cliente para el canal de chat interno
type ChatTx = mpsc::UnboundedSender<Message>;

// --- SESIÓN DE CLIENTE ---
struct ClientSession {
    context: Vec<i64>,
    history_text: Vec<(String, String)>,
    model: String,
    is_busy: bool,
    abort_handle: Option<AbortHandle>,
    connected_at: chrono::DateTime<chrono::Local>,
    messages_sent: usize,
    /// ID corto único garantizado. Formato: 8 chars hex. Nombre virtual: id@server
    short_id: String,
    /// Sender del canal mpsc para enviar mensajes al WS de este cliente sin bloquear
    chat_tx: ChatTx,
}

impl ClientSession {
    fn new(model: String, short_id: String, chat_tx: ChatTx) -> Self {
        Self {
            context: Vec::new(),
            history_text: Vec::new(),
            model,
            is_busy: false,
            abort_handle: None,
            connected_at: chrono::Local::now(),
            messages_sent: 0,
            short_id,
            chat_tx,
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

    fn virtual_name(&self) -> String {
        format!("{}@server", self.short_id)
    }
}

// --- ESTRUCTURAS ---
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
fn widget_msg(widget: &str, version: u32, data: serde_json::Value) -> String {
    json!({
        "type":    "widget",
        "widget":  widget,
        "version": version,
        "data":    data
    }).to_string()
}

// --- SOCIAL: HELPERS ---

/// Genera un short_id hex único comprobando colisiones en AI_SESSIONS.
async fn generar_short_id_unico() -> String {
    for _ in 0..30 {
        let candidate: String = {
            let mut rng = thread_rng();
            (0..SHORT_ID_LEN).map(|_| format!("{:x}", rng.gen::<u8>() & 0xf)).collect()
        };
        let sessions = AI_SESSIONS.lock().await;
        if !sessions.values().any(|s| s.short_id == candidate) {
            return candidate;
        }
    }
    // Fallback extremo: usar UUID sin guiones truncado
    Uuid::new_v4().to_string().replace('-', "")[..SHORT_ID_LEN].to_string()
}

/// Broadcast de presencia (join/leave) a todos los clientes conectados.
async fn broadcast_presence(event: &str, virtual_name: &str, total: usize) {
    let msg = json!({
        "type":    "presence",
        "event":   event,
        "id":      virtual_name,
        "clients": total
    }).to_string();
    broadcast_raw(msg, None).await;
}

/// Broadcast de un mensaje raw a todos los clientes.
/// exclude: UUID interno a omitir (None = enviar a todos).
/// No bloquea — usa los canales mpsc de cada cliente.
async fn broadcast_raw(msg: String, exclude: Option<Uuid>) {
    let sessions = AI_SESSIONS.lock().await;
    for (uuid, session) in sessions.iter() {
        if let Some(ex) = exclude {
            if *uuid == ex { continue; }
        }
        // Error ignorado: el cliente puede haberse desconectado justo ahora
        let _ = session.chat_tx.send(Message::Text(msg.clone()));
    }
}

/// Enviar un mensaje privado a un cliente por su short_id.
async fn send_pm(from_vname: &str, to_short_id: &str, text: &str) -> Result<(), String> {
    let sessions = AI_SESSIONS.lock().await;
    match sessions.values().find(|s| s.short_id == to_short_id) {
        None => Err(format!("Usuario '{}@server' no encontrado o desconectado.", to_short_id)),
        Some(s) => {
            let pm = json!({
                "type": "pm",
                "from": from_vname,
                "to":   format!("{}@server", to_short_id),
                "text": text
            }).to_string();
            s.chat_tx.send(Message::Text(pm)).map_err(|_| "Error entregando PM.".to_string())
        }
    }
}

// --- HELPERS DE SISTEMA ---

fn leer_ram() -> (u64, u64, u64) {
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

    let _ = *SERVER_START_TIME;

    if ollama_disponible().await {
        let modelos = obtener_modelos_ollama().await;
        info!("Ollama activo. {} modelo(s) disponible(s).", modelos.len());
        for m in &modelos { info!("  - {}", m); }
    } else {
        warn!("⚠️  Ollama no responde en {}. El servidor iniciará igualmente.", OLLAMA_URL);
    }

    let base_ip       = "0.0.0.0";
    let default_port  = 8081u16;
    let min_rand_port = 20000u16;
    let max_rand_port = 65000u16;
    const MAX_BIND_ATTEMPTS: u8 = 10;

    let mut attempts = 0u8;
    let listener = loop {
        attempts += 1;
        if attempts > MAX_BIND_ATTEMPTS {
            return Err("Falló al enlazar a un puerto disponible tras 10 intentos.".into());
        }
        let current_port = if attempts == 1 { default_port } else { thread_rng().gen_range(min_rand_port..=max_rand_port) };
        let addr_str = format!("{}:{}", base_ip, current_port);

        match TcpListener::bind(&addr_str).await {
            Ok(l) => { info!("✅ Servidor WebSocket iniciado en: ws://{}", addr_str); break l; }
            Err(e) if e.kind() == io::ErrorKind::AddrInUse => {
                warn!("Puerto {} en uso, reintentando...", current_port);
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

    let tcp_ip = stream.peer_addr()
        .map(|a| a.to_string())
        .unwrap_or_else(|_| "unknown".to_string());

    let modelo_inicial = obtener_modelos_ollama().await
        .into_iter().next()
        .unwrap_or_else(|| DEFAULT_MODEL_FALLBACK.to_string());

    let real_ip: Arc<std::sync::Mutex<Option<String>>> = Arc::new(std::sync::Mutex::new(None));
    let real_ip_cb = Arc::clone(&real_ip);

    let callback = move |req: &tokio_tungstenite::tungstenite::handshake::server::Request,
                         res:  tokio_tungstenite::tungstenite::handshake::server::Response|
        -> Result<tokio_tungstenite::tungstenite::handshake::server::Response,
                  tokio_tungstenite::tungstenite::handshake::server::ErrorResponse>
    {
        let ip = req.headers()
            .get("x-forwarded-for")
            .and_then(|v| v.to_str().ok())
            .and_then(|s| s.split(',').next())
            .map(|s| s.trim().to_string())
            .or_else(|| req.headers().get("x-real-ip").and_then(|v| v.to_str().ok()).map(|s| s.trim().to_string()));
        if let Ok(mut guard) = real_ip_cb.lock() { *guard = ip; }
        Ok(res)
    };

    let ws_result = tokio_tungstenite::accept_hdr_async(stream, callback).await;

    let peer_ip = real_ip.lock().ok().and_then(|g| g.clone()).unwrap_or(tcp_ip);

    if let Ok(ws_stream) = ws_result {
        // Generar ID único antes de registrar la sesión
        let short_id = generar_short_id_unico().await;
        let virtual_name = format!("{}@server", short_id);

        // Canal mpsc para mensajes de chat/presencia/pm dirigidos a este cliente
        let (chat_tx, mut chat_rx) = mpsc::unbounded_channel::<Message>();

        {
            let mut sessions = AI_SESSIONS.lock().await;
            sessions.insert(client_id, ClientSession::new(modelo_inicial.clone(), short_id.clone(), chat_tx));
        }

        let total_clients = AI_SESSIONS.lock().await.len();
        CONN_LOG.log_connect(&short_id, &peer_ip, &modelo_inicial, total_clients);
        info!("Cliente {} ({}) desde {}. Modelo: {}", client_id, virtual_name, peer_ip, modelo_inicial);

        let (write, mut read) = ws_stream.split();
        let write_arc = Arc::new(Mutex::new(write));

        // Widget de bienvenida con el virtual_name asignado
        let bienvenida = widget_msg("welcome", 1, json!({
            "id":      &short_id,
            "vname":   &virtual_name,
            "model":   modelo_inicial,
            "message": "Escribe /help para ver los comandos disponibles."
        }));
        let _ = write_arc.lock().await.send(Message::Text(bienvenida)).await;

        // Notificar a todos la llegada (incluido el propio cliente)
        broadcast_presence("join", &virtual_name, total_clients).await;

        // Task auxiliar: reenvía mensajes del canal mpsc al WebSocket del cliente.
        // Completamente independiente del loop de lectura → NO bloqueante.
        let write_chat = Arc::clone(&write_arc);
        let chat_fwd = tokio::spawn(async move {
            while let Some(msg) = chat_rx.recv().await {
                if write_chat.lock().await.send(msg).await.is_err() { break; }
            }
        });

        // --- Loop principal de lectura ---
        while let Some(Ok(msg)) = read.next().await {
            if let Message::Text(text) = msg {
                let text_trimmed = text.trim().to_string();
                if text_trimmed.is_empty() { continue; }

                info!("[{}] << {}", &short_id, &text_trimmed[..text_trimmed.len().min(120)]);

                // ── CHAT COMÚN / PM ──────────────────────────────────────────────
                // El cliente envía {"type":"chat","text":"..."} para el canal social.
                // No toca is_busy ni el semáforo de IA en ningún caso.
                if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(&text_trimmed) {
                    if parsed["type"].as_str() == Some("chat") {
                        let chat_text = parsed["text"].as_str().unwrap_or("").trim().to_string();
                        if !chat_text.is_empty() {
                            let from_vname = {
                                let sessions = AI_SESSIONS.lock().await;
                                sessions.get(&client_id).map(|s| s.virtual_name()).unwrap_or_default()
                            };

                            if chat_text.starts_with("/pm ") {
                                // Mensaje privado: /pm <short_id> <texto>
                                let parts: Vec<&str> = chat_text.splitn(3, ' ').collect();
                                if parts.len() == 3 {
                                    let to_id   = parts[1];
                                    let pm_text = parts[2];
                                    match send_pm(&from_vname, to_id, pm_text).await {
                                        Ok(_) => {
                                            // Eco al remitente para confirmación visual
                                            let confirm = json!({
                                                "type": "pm",
                                                "from": &from_vname,
                                                "to":   format!("{}@server", to_id),
                                                "text": pm_text,
                                                "self": true
                                            }).to_string();
                                            let _ = write_arc.lock().await.send(Message::Text(confirm)).await;
                                        }
                                        Err(e) => {
                                            let err = json!({"type":"chat_error","text": e}).to_string();
                                            let _ = write_arc.lock().await.send(Message::Text(err)).await;
                                        }
                                    }
                                } else {
                                    let err = json!({"type":"chat_error","text":"Uso: /pm <id> <mensaje>  (id sin @server)"}).to_string();
                                    let _ = write_arc.lock().await.send(Message::Text(err)).await;
                                }
                            } else {
                                // Broadcast al canal común (todos lo reciben, incluido el remitente)
                                let broadcast = json!({
                                    "type": "chat",
                                    "from": &from_vname,
                                    "text": &chat_text
                                }).to_string();
                                broadcast_raw(broadcast, None).await;
                            }
                        }
                        continue; // chat NUNCA llega al pipeline IA
                    }
                }

                // ── /stop: máxima prioridad ───────────────────────────────────────
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

                // ── Comandos libres (ignoran is_busy) ────────────────────────────
                if text_trimmed.starts_with('/') && es_comando_libre(&text_trimmed) {
                    let resp = handle_command(&text_trimmed, client_id).await;
                    let out = resp.unwrap_or_else(|e| format!("❌ {}", e));
                    let _ = write_arc.lock().await.send(Message::Text(out)).await;
                    continue;
                }

                // ── Rechazar si el cliente está ocupado generando ─────────────────
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

                // ── Comandos normales (bloqueados si busy) ────────────────────────
                if text_trimmed.starts_with('/') {
                    let resp = handle_command(&text_trimmed, client_id).await;
                    let out = resp.unwrap_or_else(|e| format!("Error: {}", e));
                    let _ = write_arc.lock().await.send(Message::Text(out)).await;
                    continue;
                }

                // ── Mensaje IA ────────────────────────────────────────────────────
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

                        let abort_handle = task.abort_handle();
                        {
                            let mut sessions = AI_SESSIONS.lock().await;
                            if let Some(s) = sessions.get_mut(&client_id) {
                                s.abort_handle = Some(abort_handle);
                            }
                        }
                    }
                    Err(_) => {
                        let _ = write_arc.lock().await.send(Message::Text(format!(
                            "⚠️ SISTEMA SATURADO: Ya hay {} instancias activas. Espera a que alguien termine.\n",
                            MAX_GLOBAL_INSTANCES
                        ))).await;
                    }
                }
            }
        }

        // Limpiar task auxiliar
        chat_fwd.abort();

        // Métricas de sesión
        let (duration_secs, messages_sent) = {
            let sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get(&client_id) {
                let dur = chrono::Local::now().signed_duration_since(s.connected_at).num_seconds().max(0) as u64;
                (dur, s.messages_sent)
            } else { (0, 0) }
        };

        AI_SESSIONS.lock().await.remove(&client_id);
        let total_clients = AI_SESSIONS.lock().await.len();

        info!("Cliente {} ({}) desconectado. {}s, {} msgs.", client_id, virtual_name, duration_secs, messages_sent);
        CONN_LOG.log_disconnect(&short_id, &peer_ip, duration_secs, messages_sent, total_clients);

        // Notificar salida a todos los que quedan
        broadcast_presence("leave", &virtual_name, total_clients).await;

    } else {
        warn!("Handshake WS fallido para {} desde {}.", client_id, peer_ip);
        CONN_LOG.log_event(&client_id.to_string()[..8], &peer_ip, "handshake_failed");
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
  /clearcontext   - Borra contexto e historial IA.
  /limit          - Estado de instancias IA.
  /models         - Lista modelos Ollama instalados.
  /model N        - Cambia al modelo N (historial conservado).
  /info           - Métricas del servidor y tu sesión.
  /who            - Clientes conectados ahora mismo.
  /listtv         - Canales TV activos.
  /servers        - Servidores remotos.
  /way            - Info del sistema ODyN.
  /hello          - Test de conexión.

💬 CHAT COMÚN (botón 👥 Chat):
  Escribe en el input del chat para hablar con todos.
  /pm <id> <msg>  - Mensaje privado (id sin @server).
"#.into()),

        "/clearcontext" => {
            let mut sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get_mut(&client_id) {
                s.context.clear();
                s.history_text.clear();
                Ok("🧹 Contexto e historial borrados.".into())
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

            let (_, avail_mb, _) = leer_ram();
            let en_ram = obtener_modelos_en_ram().await.iter().any(|m| m == &nombre);
            let aviso_ram = if !en_ram && avail_mb < ram_necesaria_mb(&nombre) {
                format!("\n⚠️  RAM disponible: {}MB — este modelo puede requerir swap.", avail_mb)
            } else { String::new() };

            let mut sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get_mut(&client_id) {
                let anterior = s.model.clone();
                s.model = nombre.clone();
                s.context.clear();
                CONN_LOG.log_event(&s.short_id.clone(), "n/a", &format!("model_change from={} to={}", anterior, nombre));
                Ok(format!(
                    "✅ IA cambiada: {} → {}\n💬 Historial conservado ({} turnos).{}",
                    anterior, nombre, s.history_text.len(), aviso_ram
                ))
            } else { Err("Sesión no encontrada.".into()) }
        }

        "/models" => {
            let modelos = obtener_modelos_ollama().await;
            if modelos.is_empty() { return Ok("⚠️ Ollama no responde o no hay modelos instalados.".into()); }

            let sessions = AI_SESSIONS.lock().await;
            let modelo_actual = sessions.get(&client_id).map(|s| s.model.clone()).unwrap_or_default();
            drop(sessions);

            let en_ram = obtener_modelos_en_ram().await;
            let (total_mb, avail_mb, _) = leer_ram();

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
            let activos  = ACTIVE_AI_INSTANCES.load(Ordering::SeqCst);
            let total    = MAX_GLOBAL_INSTANCES;
            let clientes = AI_SESSIONS.lock().await.len();
            Ok(format!(
                "\n📊 ESTADO:\n  Instancias IA: {}/{}\n  Disponibles: {}\n  Clientes conectados: {}\n",
                activos, total, total.saturating_sub(activos), clientes
            ))
        }

        "/who" => {
            let sessions = AI_SESSIONS.lock().await;
            let ahora = chrono::Local::now();
            let users: Vec<serde_json::Value> = sessions.values().map(|s| {
                let dur = ahora.signed_duration_since(s.connected_at).num_seconds().max(0) as u64;
                json!({
                    "id":    s.short_id,
                    "vname": s.virtual_name(),
                    "model": s.model,
                    "since": formatear_duracion(dur),
                    "msgs":  s.messages_sent,
                    "busy":  s.is_busy
                })
            }).collect();
            Ok(widget_msg("who", 1, json!({ "users": users })))
        }

        "/date" | "/info" => {
            let ahora = chrono::Local::now();
            let (total_mb, avail_mb, used_mb) = leer_ram();
            let uptime_os = leer_uptime_os();
            let activos   = ACTIVE_AI_INSTANCES.load(Ordering::SeqCst);

            let sessions  = AI_SESSIONS.lock().await;
            let clientes  = sessions.len();
            let mi        = sessions.get(&client_id);
            let mi_modelo = mi.map(|s| s.model.clone()).unwrap_or_default();
            let mi_turnos = mi.map(|s| s.history_text.len()).unwrap_or(0);
            let mi_msgs   = mi.map(|s| s.messages_sent).unwrap_or(0);
            let mi_id     = mi.map(|s| s.short_id.clone()).unwrap_or_default();
            let mi_vname  = mi.map(|s| s.virtual_name()).unwrap_or_default();
            let conectado = mi.map(|s|
                formatear_duracion(chrono::Local::now().signed_duration_since(s.connected_at).num_seconds().max(0) as u64)
            ).unwrap_or_default();
            drop(sessions);

            let en_ram    = obtener_modelos_en_ram().await;
            let uptime_srv = formatear_duracion(
                ahora.signed_duration_since(*SERVER_START_TIME).num_seconds().max(0) as u64
            );
            let ram_pct   = if total_mb > 0 { (used_mb * 100) / total_mb } else { 0 };

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
                    "vname":           mi_vname,
                    "model":           mi_modelo,
                    "connected_since": conectado,
                    "messages":        mi_msgs,
                    "context_turns":   mi_turnos
                }
            })))
        }

        "/hello"   => Ok("👋 GoyimAI en línea.".into()),
        "/way"     => Ok("Sistema ODyN - Goyim United Corp.".into()),
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
        let status   = res.status();
        let err_text = format!("❌ Error API Ollama ({}). Revisa el modelo: {}", status, model);
        let _ = write_sink.lock().await.send(Message::Text(err_text.clone())).await;
        return Err(err_text.into());
    }

    let mut full_response = String::new();
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

    let mut sessions = AI_SESSIONS.lock().await;
    if let Some(s) = sessions.get_mut(&client_id) {
        if !new_context.is_empty()   { s.context = new_context; }
        if !full_response.is_empty() { s.add_history(prompt.to_string(), full_response.trim().to_string()); }
    }

    Ok(())
}

// --- TV como widget ---
fn list_tv_channels() -> Result<String, String> {
    let data = fs::read_to_string("/var/osiris2/bin/com/datas/ffmpeg/activos.json")
        .map_err(|e| e.to_string())?;
    let channels: Vec<TVChannel> = serde_json::from_str(&data).map_err(|e| e.to_string())?;
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