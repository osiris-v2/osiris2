// src/main.rs
use tokio::net::TcpListener;
use tokio_tungstenite::{
    tungstenite::Message,
    tungstenite::handshake::server::{Request, Response, ErrorResponse},
};
use futures_util::{StreamExt, SinkExt};
use std::error::Error;
use log::{info, warn, error};
use uuid::Uuid;
use rand::{Rng, thread_rng};
use std::io;
use std::sync::Arc;
use tokio::sync::{Mutex, OwnedSemaphorePermit};
use tokio::sync::mpsc;

mod config;
mod logger;
mod session;
mod db;
mod profile;
mod cro;
mod ollama;
mod commands;
mod utils;
mod social;
mod protocol;
mod types;

use crate::config::{
    MAX_GLOBAL_INSTANCES, OLLAMA_URL, DEFAULT_MODEL_FALLBACK,
    AI_LIMIT_SEM, AI_SESSIONS, SERVER_START_TIME, ACTIVE_AI_INSTANCES,
    PROFILES_DIR, TMP_BASE, DB_PATH, DATABASE,
};
use crate::logger::CONN_LOG;
use crate::session::ClientSession;
use crate::db::Db;
use crate::ollama::{obtener_modelos_ollama, preguntar_ollama_stream, ollama_disponible};
use crate::commands::{handle_command, es_comando_libre};
use crate::social::{
    generar_short_id_unico, broadcast_presence, broadcast_raw, send_pm,
    enviar_a_sala,
};
use crate::protocol::widget_msg;

// ── GUARD DE SEMÁFORO ────────────────────────────────────────────────────────
pub struct AiInstanceGuard { _permit: OwnedSemaphorePermit }

impl AiInstanceGuard {
    pub fn new(permit: OwnedSemaphorePermit) -> Self {
        ACTIVE_AI_INSTANCES.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        Self { _permit: permit }
    }
}
impl Drop for AiInstanceGuard {
    fn drop(&mut self) {
        ACTIVE_AI_INSTANCES.fetch_sub(1, std::sync::atomic::Ordering::SeqCst);
    }
}

// ── MAIN ──────────────────────────────────────────────────────────────────────
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info")
    ).init();

    let _ = *SERVER_START_TIME;

    // ── Inicializar DB ────────────────────────────────────────────────────
    let db_handle = Db::open(DB_PATH)
        .map_err(|e| format!("❌ No se pudo abrir la base de datos '{}': {}", DB_PATH, e))?;
    DATABASE.set(db_handle).expect("DATABASE ya inicializada");
    info!("💾 Base de datos lista: {}", DB_PATH);

    // ── Crear directorios necesarios ──────────────────────────────────────
    for (dir, desc) in &[
        (PROFILES_DIR, "perfiles temporales"),
        (TMP_BASE,     "carpetas tmp de sesión"),
    ] {
        let path = std::path::Path::new(dir);
        if !path.exists() {
            match std::fs::create_dir_all(path) {
                Ok(_)  => info!("📁 Directorio '{}' creado ({}).", dir, desc),
                Err(e) => warn!("⚠️  No se pudo crear '{}' ({}): {}", dir, desc, e),
            }
        }
    }

    // ── Limpiar carpetas tmp huérfanas de sesiones anteriores ─────────────
    if let Ok(entries) = std::fs::read_dir(TMP_BASE) {
        let mut limpiadas = 0usize;
        for entry in entries.flatten() {
            if entry.path().is_dir() {
                let _ = std::fs::remove_dir_all(entry.path());
                limpiadas += 1;
            }
        }
        if limpiadas > 0 {
            info!("🧹 {} carpeta(s) tmp huérfana(s) limpiada(s).", limpiadas);
        }
    }

    // ── Verificar Ollama ──────────────────────────────────────────────────
    if ollama_disponible().await {
        let modelos = obtener_modelos_ollama().await;
        info!("Ollama activo. {} modelo(s) disponible(s).", modelos.len());
        for m in &modelos { info!("  - {}", m); }
    } else {
        warn!("⚠️  Ollama no responde en {}. El servidor iniciará igualmente.", OLLAMA_URL);
    }

    // ── instrucciones.txt ─────────────────────────────────────────────────
    if let Some(ruta) = std::env::current_exe().ok()
        .and_then(|p| p.parent().map(|d| d.join("instrucciones.txt")))
    {
        match std::fs::read_to_string(&ruta) {
            Ok(c) if c.trim().is_empty() =>
                warn!("⚠️  instrucciones.txt existe pero está vacío."),
            Ok(c) =>
                info!("✅ instrucciones.txt cargado ({} bytes).", c.len()),
            Err(_) =>
                warn!("⚠️  instrucciones.txt no encontrado en {}.", ruta.display()),
        }
    }

    // ── Bind al puerto ────────────────────────────────────────────────────
    let base_ip      = "0.0.0.0";
    let default_port = 8081u16;
    const MAX_ATTEMPTS: u8 = 10;

    let mut attempts = 0u8;
    let listener = loop {
        attempts += 1;
        if attempts > MAX_ATTEMPTS {
            return Err("No se pudo enlazar a ningún puerto tras 10 intentos.".into());
        }
        let port = if attempts == 1 { default_port }
                   else { thread_rng().gen_range(20000u16..=65000u16) };
        let addr = format!("{}:{}", base_ip, port);
        match TcpListener::bind(&addr).await {
            Ok(l) => { info!("✅ WebSocket en: ws://{}", addr); break l; }
            Err(e) if e.kind() == io::ErrorKind::AddrInUse => {
                warn!("Puerto {} en uso, reintentando...", port);
            }
            Err(e) => return Err(e.into()),
        }
    };

    info!("Esperando conexiones (máx. {} instancias IA)...", MAX_GLOBAL_INSTANCES);

    while let Ok((stream, _addr)) = listener.accept().await {
        tokio::spawn(handle_connection(stream));
    }
    Ok(())
}

// ── MANEJO DE CONEXIÓN ────────────────────────────────────────────────────────
async fn handle_connection(stream: tokio::net::TcpStream) {
    let client_id = Uuid::new_v4();

    let tcp_ip = stream.peer_addr()
        .map(|a| a.to_string())
        .unwrap_or_else(|_| "unknown".to_string());

    let modelo_inicial = obtener_modelos_ollama().await
        .into_iter().next()
        .unwrap_or_else(|| DEFAULT_MODEL_FALLBACK.to_string());

    // Extraer IP real desde headers de proxy
    let real_ip: Arc<std::sync::Mutex<Option<String>>> =
        Arc::new(std::sync::Mutex::new(None));
    let real_ip_cb = Arc::clone(&real_ip);

    let callback = move |req: &Request, res: Response|
        -> Result<Response, ErrorResponse>
    {
        let ip = req.headers()
            .get("x-forwarded-for")
            .and_then(|v| v.to_str().ok())
            .and_then(|s| s.split(',').next())
            .map(|s| s.trim().to_string())
            .or_else(|| req.headers()
                .get("x-real-ip")
                .and_then(|v| v.to_str().ok())
                .map(|s| s.trim().to_string()));
        if let Ok(mut g) = real_ip_cb.lock() { *g = ip; }
        Ok(res)
    };

    let ws_result = tokio_tungstenite::accept_hdr_async(stream, callback).await;
    let peer_ip = real_ip.lock().ok()
        .and_then(|g| g.clone())
        .unwrap_or(tcp_ip);

    if let Ok(ws_stream) = ws_result {
        let short_id     = generar_short_id_unico().await;
        let virtual_name = format!("{}@server", short_id);

        let (chat_tx, mut chat_rx) = mpsc::unbounded_channel::<Message>();

        // Crear sesión (también crea /tmp/aichat/<short_id>/)
        {
            let mut sessions = AI_SESSIONS.lock().await;
            sessions.insert(
                client_id,
                ClientSession::new(modelo_inicial.clone(), short_id.clone(), chat_tx.clone()),
            );
        }

        let total_clients = AI_SESSIONS.lock().await.len();
        CONN_LOG.log_connect(&short_id, &peer_ip, &modelo_inicial, total_clients);
        info!("+ {} ({}) desde {}. Modelo: {}", client_id, virtual_name, peer_ip, modelo_inicial);

        let (write, mut read) = ws_stream.split();
        let write_arc = Arc::new(Mutex::new(write));

        // Bienvenida
        let bienvenida = widget_msg("welcome", 2, serde_json::json!({
            "id":      &short_id,
            "vname":   &virtual_name,
            "model":   modelo_inicial,
            "clients": total_clients,
            "message": "Escribe /help para comandos. Usa /registro para cuenta permanente."
        }));
        let _ = write_arc.lock().await.send(Message::Text(bienvenida)).await;

        // Broadcast de presencia
        let join_msg = serde_json::json!({
            "type": "presence", "event": "join",
            "id": &virtual_name, "clients": total_clients
        }).to_string();
        broadcast_raw(join_msg, Some(client_id)).await;

        // Tarea de reenvío mpsc → WS
        let write_fwd = Arc::clone(&write_arc);
        let chat_fwd = tokio::spawn(async move {
            while let Some(msg) = chat_rx.recv().await {
                if write_fwd.lock().await.send(msg).await.is_err() { break; }
            }
        });

        // ── BUCLE PRINCIPAL ───────────────────────────────────────────────
        while let Some(Ok(msg)) = read.next().await {
            if let Message::Text(text) = msg {
                let text = text.trim().to_string();
                if text.is_empty() { continue; }

                info!("[{}] << {}", &short_id, &text[..text.len().min(120)]);

                // ── JSON estructurado ──────────────────────────────────────
                if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(&text) {
                    if let Some(tipo) = parsed["type"].as_str() {
                        match tipo {
                            "post" => {
                                let t = parsed["text"].as_str().unwrap_or("").trim().to_string();
                                if !t.is_empty() && t.len() <= 500 {
                                    let from = {
                                        let s = AI_SESSIONS.lock().await;
                                        s.get(&client_id).map(|s| s.virtual_name()).unwrap_or_default()
                                    };
                                    let b = serde_json::json!({
                                        "type":"post","from":from,"text":t
                                    }).to_string();
                                    broadcast_raw(b, None).await;
                                }
                                continue;
                            }
                            "chat" => {
                                let t = parsed["text"].as_str().unwrap_or("").trim().to_string();
                                if !t.is_empty() {
                                    let from = {
                                        let s = AI_SESSIONS.lock().await;
                                        s.get(&client_id).map(|s| s.virtual_name()).unwrap_or_default()
                                    };
                                    if t.starts_with("/pm ") {
                                        let parts: Vec<&str> = t.splitn(3, ' ').collect();
                                        if parts.len() == 3 {
                                            let to_id = parts[1].trim_end_matches("@server");
                                            match send_pm(&from, to_id, parts[2]).await {
                                                Ok(_) => {
                                                    let c = serde_json::json!({
                                                        "type":"pm","from":&from,
                                                        "to":format!("{}@server",to_id),
                                                        "text":parts[2],"self":true
                                                    }).to_string();
                                                    let _ = write_arc.lock().await.send(Message::Text(c)).await;
                                                }
                                                Err(e) => {
                                                    let e = serde_json::json!({
                                                        "type":"chat_error","text":e
                                                    }).to_string();
                                                    let _ = write_arc.lock().await.send(Message::Text(e)).await;
                                                }
                                            }
                                        }
                                    } else {
                                        let b = serde_json::json!({
                                            "type":"chat","from":&from,"text":&t
                                        }).to_string();
                                        broadcast_raw(b, None).await;
                                    }
                                }
                                continue;
                            }
                            "room_msg" => {
                                let room_id = parsed["room_id"].as_str().unwrap_or("").trim().to_string();
                                let texto   = parsed["text"].as_str().unwrap_or("").trim().to_string();
                                if !room_id.is_empty() && !texto.is_empty() {
                                    if let Err(e) = enviar_a_sala(&room_id, client_id, &texto).await {
                                        let err = serde_json::json!({
                                            "type":"chat_error","text":e
                                        }).to_string();
                                        let _ = write_arc.lock().await.send(Message::Text(err)).await;
                                    }
                                }
                                continue;
                            }
                            _ => {}
                        }
                    }
                }

                // ── /stop ──────────────────────────────────────────────────
                if text == "/stop" {
                    let mut sessions = AI_SESSIONS.lock().await;
                    if let Some(s) = sessions.get_mut(&client_id) {
                        if let Some(h) = s.abort_handle.take() {
                            h.abort();
                            s.is_busy = false;
                            let _ = write_arc.lock().await
                                .send(Message::Text("🛑 Generación abortada.".into())).await;
                        } else {
                            let _ = write_arc.lock().await
                                .send(Message::Text("⚠️ No hay proceso activo.".into())).await;
                        }
                    }
                    continue;
                }

                // ── Comandos libres ────────────────────────────────────────
                if text.starts_with('/') && es_comando_libre(&text) {
                    let out = handle_command(&text, client_id, write_arc.clone()).await
                        .unwrap_or_else(|e| format!("❌ {}", e));
                    if !out.is_empty() {
                        let _ = write_arc.lock().await.send(Message::Text(out)).await;
                    }
                    continue;
                }

                // ── Rechazar si IA ocupada ─────────────────────────────────
                let busy = {
                    let s = AI_SESSIONS.lock().await;
                    s.get(&client_id).map(|s| s.is_busy).unwrap_or(false)
                };
                if busy {
                    let _ = write_arc.lock().await.send(Message::Text(
                        "❌ Espera a que termine la respuesta actual (/stop para cancelar).\n".into()
                    )).await;
                    continue;
                }

                // ── Comandos normales ──────────────────────────────────────
                if text.starts_with('/') {
                    let out = handle_command(&text, client_id, write_arc.clone()).await
                        .unwrap_or_else(|e| format!("❌ {}", e));
                    if !out.is_empty() {
                        let _ = write_arc.lock().await.send(Message::Text(out)).await;
                    }
                    continue;
                }

                // ── Inferencia IA ──────────────────────────────────────────
                match AI_LIMIT_SEM.clone().try_acquire_owned() {
                    Ok(permit) => {
                        {
                            let mut s = AI_SESSIONS.lock().await;
                            if let Some(s) = s.get_mut(&client_id) { s.is_busy = true; }
                        }
                        let write_clone = Arc::clone(&write_arc);
                        let text_clone  = text.clone();
                        let task = tokio::spawn(async move {
                            let _guard = AiInstanceGuard::new(permit);
                            if let Err(e) = preguntar_ollama_stream(
                                &text_clone, client_id, write_clone.clone()
                            ).await {
                                error!("Error IA [{}]: {}", client_id, e);
                                let _ = write_clone.lock().await.send(Message::Text(
                                    format!("\n⚠️ ERROR: {}. Prueba /clearcontext.", e)
                                )).await;
                            }
                            let mut s = AI_SESSIONS.lock().await;
                            if let Some(s) = s.get_mut(&client_id) {
                                s.is_busy = false;
                                s.abort_handle = None;
                            }
                        });
                        let abort = task.abort_handle();
                        let mut s = AI_SESSIONS.lock().await;
                        if let Some(s) = s.get_mut(&client_id) {
                            s.abort_handle = Some(abort);
                        }
                    }
                    Err(_) => {
                        let _ = write_arc.lock().await.send(Message::Text(format!(
                            "⚠️ Sistema saturado ({} instancias activas). Espera.\n",
                            MAX_GLOBAL_INSTANCES
                        ))).await;
                    }
                }
            }
        }

        // ── DESCONEXIÓN ────────────────────────────────────────────────────
        chat_fwd.abort();

        let (dur, msgs) = {
            let s = AI_SESSIONS.lock().await;
            s.get(&client_id).map(|s| {
                let d = chrono::Local::now()
                    .signed_duration_since(s.connected_at)
                    .num_seconds().max(0) as u64;
                (d, s.messages_sent)
            }).unwrap_or((0, 0))
        };

        // Limpiar /tmp/aichat/<short_id>/
        {
            let s = AI_SESSIONS.lock().await;
            if let Some(s) = s.get(&client_id) {
                s.limpiar_tmp();
            }
        }

        let total = {
            let mut s = AI_SESSIONS.lock().await;
            s.remove(&client_id);
            s.len()
        };

        info!("- {} ({}) desconectado. {}s {} msgs.", client_id, virtual_name, dur, msgs);
        CONN_LOG.log_disconnect(&short_id, &peer_ip, dur, msgs, total);
        broadcast_presence("leave", &virtual_name, total).await;

    } else {
        warn!("Handshake WS fallido para {} desde {}.", client_id, peer_ip);
        CONN_LOG.log_event(&client_id.to_string()[..8], &peer_ip, "handshake_failed");
    }
}
