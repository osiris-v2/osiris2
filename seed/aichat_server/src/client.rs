// /var/osiris2/seed/aichat_server/src/client.rs
use tokio::io::{AsyncBufReadExt, BufReader, AsyncWriteExt};
use tokio_tungstenite::{connect_async, tungstenite::Message};
use futures_util::{StreamExt, SinkExt};
use std::error::Error;
use url::Url;
use async_trait::async_trait;
use log::{info, error};
use env_logger;
use serde_json::Value;

// Define un trait para los manejadores de mensajes, permitiendo procesar mensajes recibidos de forma flexible
#[async_trait]
trait MessageHandler {
    async fn handle_message(&mut self, msg: Message);
}

// Un manejador simple que imprime mensajes en la salida estándar, con formato avanzado
struct StdoutMessageHandler;

#[async_trait]
impl MessageHandler for StdoutMessageHandler {
    async fn handle_message(&mut self, msg: Message) {
        match msg {
            Message::Text(text) => {
                if let Ok(json_val) = serde_json::from_str::<Value>(&text) {
                    // Intento de analizar mensajes estructurados conocidos
                    match json_val["type"].as_str() {
                        Some("widget") => {
                            if let Some(widget_type) = json_val["widget"].as_str() {
                                match widget_type {
                                    "welcome" => {
                                        let id = json_val["data"]["id"].as_str().unwrap_or("?");
                                        let vname = json_val["data"]["vname"].as_str().unwrap_or("?");
                                        let model = json_val["data"]["model"].as_str().unwrap_or("?");
                                        let clients = json_val["data"]["clients"].as_u64().unwrap_or(0);
                                        let welcome_msg = json_val["data"]["message"].as_str().unwrap_or("");
                                        println!("
🤝 Conectado: {} (ID: {})", vname, id);
                                        println!("  Modelo IA: {}", model);
                                        println!("  Clientes online: {}", clients);
                                        if !welcome_msg.is_empty() { println!("  {}", welcome_msg); }
                                    },
                                    "models" => {
                                        println!("
--- Modelos Ollama disponibles ---");
                                        if let Some(models_arr) = json_val["data"]["models"].as_array() {
                                            for model_data in models_arr {
                                                let index = model_data["index"].as_u64().unwrap_or(0);
                                                let name = model_data["name"].as_str().unwrap_or("?");
                                                let active = model_data["active"].as_bool().unwrap_or(false);
                                                let in_ram = model_data["in_ram"].as_bool().unwrap_or(false);
                                                let fits_ram = model_data["fits_ram"].as_bool().unwrap_or(false);
                                                let mut status = Vec::new();
                                                if active { status.push("ACTIVO"); }
                                                if in_ram { status.push("EN_RAM"); }
                                                if !fits_ram && !in_ram { status.push("LOW_RAM_WARNING"); }
                                                println!("  {}. {} {}", index, name, if status.is_empty() { "".to_string() } else { format!("({})", status.join(", ")) });
                                            }
                                        }
                                        println!("  RAM Total: {}MB, Disponible: {}MB", 
                                            json_val["data"]["ram_total_mb"].as_u64().unwrap_or(0), 
                                            json_val["data"]["ram_available_mb"].as_u64().unwrap_or(0)
                                        );
                                        println!("--------------------------------");
                                    },
                                    "who" => {
                                        println!("
--- Clientes Conectados ---");
                                        if let Some(users_arr) = json_val["data"]["users"].as_array() {
                                            for user_data in users_arr {
                                                let vname = user_data["vname"].as_str().unwrap_or("?");
                                                let model = user_data["model"].as_str().unwrap_or("?");
                                                let since = user_data["since"].as_str().unwrap_or("?");
                                                let msgs = user_data["msgs"].as_u64().unwrap_or(0);
                                                let busy = user_data["busy"].as_bool().unwrap_or(false);
                                                println!("  {} ({}) - Modelo: {} - Conectado: {} - Mensajes: {}", 
                                                         vname, 
                                                         if busy { "BUSY" } else { "IDLE" },
                                                         model, since, msgs
                                                );
                                            }
                                        }
                                        println!("--------------------------");
                                    },
                                    "info" => {
                                        println!("
--- Info del Servidor y Sesión ---");
                                        if let Some(server) = json_val["data"]["server"].as_object() {
                                            println!("SERVER:");
                                            println!("  Uptime Server: {}", server["uptime"].as_str().unwrap_or("?"));
                                            println!("  Uptime OS:     {}", server["uptime_os"].as_str().unwrap_or("?"));
                                            println!("  Clientes:      {}", server["clients"].as_u64().unwrap_or(0));
                                            println!("  IA Activas:    {}/{}", server["ai_active"].as_u64().unwrap_or(0), server["ai_max"].as_u64().unwrap_or(0));
                                        }
                                        if let Some(ram) = json_val["data"]["ram"].as_object() {
                                            println!("RAM:");
                                            println!("  Total:       {}MB", ram["total_mb"].as_u64().unwrap_or(0));
                                            println!("  Usada:       {}MB ({}%)", ram["used_mb"].as_u64().unwrap_or(0), ram["used_pct"].as_u64().unwrap_or(0));
                                            println!("  Disponible:  {}MB", ram["available_mb"].as_u64().unwrap_or(0));
                                        }
                                        if let Some(session) = json_val["data"]["session"].as_object() {
                                            println!("TU SESIÓN:");
                                            println!("  ID:            {}", session["id"].as_str().unwrap_or("?"));
                                            println!("  Nombre Virtual:{}", session["vname"].as_str().unwrap_or("?"));
                                            println!("  Modelo:        {}", session["model"].as_str().unwrap_or("?"));
                                            println!("  Conectado desde:{}", session["connected_since"].as_str().unwrap_or("?"));
                                            println!("  Mensajes:      {}", session["messages"].as_u64().unwrap_or(0));
                                            println!("  Contexto:      {} turnos", session["context_turns"].as_u64().unwrap_or(0));
                                        }
                                        println!("----------------------------------");
                                    },
                                    "tv_channels" => {
                                        println!("
--- Canales de TV Activos ---");
                                        if let Some(channels_arr) = json_val["data"]["channels"].as_array() {
                                            for ch in channels_arr {
                                                println!("  - {}: {}", ch["canal"].as_str().unwrap_or("?"), ch["url"].as_str().unwrap_or("?"));
                                            }
                                        }
                                        println!("------------------------------");
                                    },
                                    "servers" => {
                                        println!("
--- Servidores Remotos ---");
                                        if let Some(servers_arr) = json_val["data"]["servers"].as_array() {
                                            for srv in servers_arr {
                                                println!("  - {}", srv["host"].as_str().unwrap_or("?"));
                                            }
                                        }
                                        println!("-------------------------");
                                    },
                                    _ => println!("SERVE_WIDGET: {}", text),
                                }
                            } else {
                                println!("SERVER: {}", text);
                            }
                        },
                        Some("presence") => {
                            let event = json_val["event"].as_str().unwrap_or("?");
                            let id = json_val["id"].as_str().unwrap_or("?");
                            let clients = json_val["clients"].as_u64().unwrap_or(0);
                            match event {
                                "join" => println!("👥 {} se ha conectado. Clientes: {}.", id, clients),
                                "leave" => println!("👋 {} se ha desconectado. Clientes: {}.", id, clients),
                                _ => println!("PRESENCE: {}", text),
                            }
                        },
                        Some("chat") => {
                            let from = json_val["from"].as_str().unwrap_or("?");
                            let chat_text = json_val["text"].as_str().unwrap_or("");
                            println!("[{}] {}", from, chat_text);
                        },
                        Some("post") => {
                            let from = json_val["from"].as_str().unwrap_or("?");
                            let post_text = json_val["text"].as_str().unwrap_or("");
                            println!("📢 [{}] POST: {}", from, post_text);
                        },
                        Some("pm") => {
                            let from = json_val["from"].as_str().unwrap_or("?");
                            let to = json_val["to"].as_str().unwrap_or("?");
                            let pm_text = json_val["text"].as_str().unwrap_or("");
                            let is_self = json_val["self"].as_bool().unwrap_or(false);
                            if is_self {
                                println!("[PM ➡️ {}] {}", to, pm_text);
                            } else {
                                println!("[PM ✉️ {}] {}", from, pm_text);
                            }
                        },
                        Some("chat_error") => {
                            let err_text = json_val["text"].as_str().unwrap_or("Error desconocido");
                            println!("❌ CHAT ERROR: {}", err_text);
                        },
                        _ => {
                            println!("{}", text);
                        }
                    }
                } else {
                    print!("{}", text);
                }
            },
            Message::Binary(bin) => println!("Received binary: {:?}", bin),
            Message::Ping(ping) => println!("Received ping: {:?}", ping),
            Message::Pong(pong) => println!("Received pong: {:?}", pong),
            Message::Close(close) => {
                println!("Connection closed: {:?}", close);
            },
            Message::Frame(_) => {},
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info")
    ).init();

    let connect_addr = std::env::args().nth(1).unwrap_or_else(|| {
        info!("Uso: client <ws_url>");
        info!("Usando dirección por defecto: ws://127.0.0.1:8081");
        "ws://127.0.0.1:8081".to_string()
    });

    let url = Url::parse(&connect_addr)?;

    println!("Intentando conectar a {}", url);
    let (ws_stream, _) = connect_async(url).await.expect("Fallo al conectar al servidor.");
    println!("✅ Conectado al servidor WebSocket.");

    let (mut write, mut read) = ws_stream.split();

    let stdin_tx = tokio::spawn(async move {
        let mut stdin = BufReader::new(tokio::io::stdin()).lines();
        loop {
            print!("> ");
            tokio::io::stdout().flush().await.expect("Failed to flush stdout");

            if let Some(line_result) = stdin.next_line().await.expect("Failed to read line") {
                let input = line_result.trim();
                if input.is_empty() { continue; }

                match input {
                    "/quit" | "/exit" => {
                        println!("Desconectando...");
                        break;
                    },
                    _ if input.starts_with('/') => {
                        write.send(Message::Text(input.to_string())).await.expect("Failed to send message");
                    },
                    _ => {
                        let chat_message = serde_json::json!({
                            "type": "chat",
                            "text": input
                        }).to_string();
                        write.send(Message::Text(chat_message)).await.expect("Failed to send message");
                    }
                }
            } else {
                break;
            }
        }
    });

    let mut message_handler = StdoutMessageHandler;
    let ws_rx = tokio::spawn(async move {
        while let Some(msg_result) = read.next().await {
            match msg_result {
                Ok(msg) => {
                    message_handler.handle_message(msg).await;
                    tokio::io::stdout().flush().await.expect("Failed to flush stdout");
                }
                Err(e) => {
                    error!("Error de lectura del WebSocket: {:?}", e);
                    break;
                }
            }
        }
    });

    tokio::select! {
        _ = stdin_tx => {
            info!("Tarea de entrada de usuario finalizada.");
        },
        _ = ws_rx => {
            info!("Tarea de recepción del WebSocket finalizada.");
        }
    }

    println!("Cliente desconectado.");
    Ok(())
}
