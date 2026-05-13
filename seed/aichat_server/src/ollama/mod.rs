// src/ollama/mod.rs
use std::fs;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio_tungstenite::tungstenite::Message;
use futures_util::SinkExt;
use log::warn;
use serde_json::json;
use uuid::Uuid;
use chrono::Local;

use crate::config::{OLLAMA_URL, OLLAMA_TIMEOUT_SECS, AI_SESSIONS};
use crate::cro::{CroParser, CroConfig};

// ── OLLAMA HELPERS ─────────────────────────────────────────────────────────────

pub async fn obtener_modelos_ollama() -> Vec<String> {
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

pub async fn obtener_modelos_en_ram() -> Vec<String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build().unwrap_or_default();
    match client.get(format!("{}/api/ps", OLLAMA_URL)).send().await {
        Ok(res) => res.json::<serde_json::Value>().await.ok()
            .and_then(|j| j["models"].as_array().map(|a|
                a.iter().filter_map(|m| m["name"].as_str().map(|s| s.to_string())).collect()
            )).unwrap_or_default(),
        Err(e) => { warn!("No se pudo contactar Ollama (ps): {}", e); vec![] }
    }
}

pub async fn ollama_disponible() -> bool {
    reqwest::Client::builder().timeout(std::time::Duration::from_secs(3))
        .build().unwrap_or_default()
        .get(format!("{}/api/tags", OLLAMA_URL)).send().await.is_ok()
}

// ── INFERENCIA CON OLLAMA (STREAMING) ─────────────────────────────────────────

pub async fn preguntar_ollama_stream(
    prompt: &str,
    client_id: Uuid,
    write_sink: Arc<Mutex<futures_util::stream::SplitSink<
        tokio_tungstenite::WebSocketStream<tokio::net::TcpStream>, Message,
    >>>,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(OLLAMA_TIMEOUT_SECS))
        .build()?;

    // Leer todo lo necesario de la sesión en un único lock
    let (ctx, model, history_text, short_id, virtual_name, bloque_perfil) = {
        let sessions = AI_SESSIONS.lock().await;
        let s = sessions.get(&client_id).ok_or("Sesión perdida")?;
        (
            s.context.clone(),
            s.model.clone(),
            s.history_as_text(),
            s.short_id.clone(),
            s.virtual_name(),
            s.perfil.para_prompt(),
        )
    };

    let ahora = Local::now().format("%d/%m/%Y %H:%M:%S").to_string();

    // Cargar instrucciones.txt desde el directorio del binario
    let instrucciones_extra = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|d| d.join("instrucciones.txt")))
        .and_then(|p| fs::read_to_string(p).ok())
        .unwrap_or_default();

    // ── Bloque identidad del usuario ──────────────────────────────────────
    let bloque_identidad = if bloque_perfil.is_empty() {
        format!(
            "── IDENTIDAD DEL USUARIO ─────────────────────────────────────────────\n\
            ID de sesión: {short_id}  ({virtual_name})\n\
            Perfil:       no configurado — usa /perfil para personalizarme.\n",
        )
    } else {
        format!(
            "── IDENTIDAD DEL USUARIO ─────────────────────────────────────────────\n\
            ID de sesión: {short_id}  ({virtual_name})\n\
            {perfil}",
            perfil = bloque_perfil,
        )
    };

    // ── Bloque instrucciones CRO del operador (instrucciones.txt) ─────────
    //
    // Este fichero contiene las instrucciones personalizadas del operador:
    //   • Reglas de comportamiento y restricciones de respuesta.
    //   • Instrucciones CRO: cómo estructurar la respuesta para maximizar
    //     la conversión o la acción deseada del usuario (llamadas a la acción,
    //     tono persuasivo, formato de oferta, etc.).
    //   • Contexto de producto/empresa: nombre comercial, propuesta de valor,
    //     límites de soporte, idioma preferido.
    //
    // Si el fichero está vacío o no existe, este bloque no aparece en el prompt.
    // El CRO Parser (src/cro.rs) puede post-procesar adicionalmente la salida
    // en tiempo real sin modificar el prompt.
    let bloque_instrucciones = if instrucciones_extra.trim().is_empty() {
        String::new()
    } else {
        format!(
            "── INSTRUCCIONES DEL OPERADOR ────────────────────────────────────────\n\
            {instrucciones}\n\
            ── FIN INSTRUCCIONES ─────────────────────────────────────────────────\n",
            instrucciones = instrucciones_extra.trim()
        )
    };

    // ── System prompt final ───────────────────────────────────────────────
    let system_prompt = format!(
        "Eres GoyimAI, asistente de GoyCorp. Fecha y hora: {ahora}.\n\
        Responde siempre en el idioma del usuario. Sé directo y conciso.\n\
        \n\
        {bloque_identidad}\
        {bloque_instrucciones}\
        {history_text}",
        ahora                = ahora,
        bloque_identidad     = bloque_identidad,
        bloque_instrucciones = bloque_instrucciones,
        history_text         = history_text,
    );

    let body = json!({
        "model":   model,
        "prompt":  prompt,
        "stream":  true,
        "context": if ctx.is_empty() { json!(null) } else { json!(ctx) },
        "system":  system_prompt
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

    // ── CRO Parser: instanciar con config por defecto (passthrough) ───────
    // Para activar transformaciones, cambia CroConfig::default() por una
    // CroConfig con `activo: true` y las reglas que necesites.
    // En el futuro se cargará desde fichero de configuración.
    let mut cro = CroParser::new(CroConfig::default());

    while let Some(chunk) = res.chunk().await? {
        let text = String::from_utf8_lossy(&chunk);
        for line in text.split('\n') {
            if line.is_empty() { continue; }
            if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(line) {

                if let Some(token) = json_val["response"].as_str() {
                    full_response.push_str(token);

                    // Pasar el token por el CRO Parser antes de enviarlo al cliente
                    let salida = cro.procesar_token(token);
                    if !salida.is_empty() {
                        let _ = write_sink.lock().await.send(Message::Text(salida)).await;
                    }
                }

                if json_val["done"].as_bool().unwrap_or(false) {
                    if let Some(new_ctx) = json_val["context"].as_array() {
                        new_context = new_ctx.iter().filter_map(|v| v.as_i64()).collect();
                    }
                    // Vaciar el buffer del CRO Parser al terminar
                    let cola = cro.flush();
                    if !cola.is_empty() {
                        let _ = write_sink.lock().await.send(Message::Text(cola)).await;
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
