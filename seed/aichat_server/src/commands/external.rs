// /var/osiris2/seed/aichat_server/src/commands/external.rs
use serde_json::json;
use tokio::fs;

use crate::types::TVChannel;
use crate::protocol::widget_msg;

// --- TV como widget ---
pub async fn list_tv_channels() -> Result<String, String> {
    let data = fs::read_to_string("/var/osiris2/bin/com/datas/ffmpeg/activos.json")
        .await
        .map_err(|e| format!("Error leyendo canales TV: {}", e))?;
    let channels: Vec<TVChannel> = serde_json::from_str(&data)
        .map_err(|e| format!("Error parseando canales TV: {}", e))?;
    if channels.is_empty() { return Ok("📺 No hay canales activos.".into()); }
    Ok(widget_msg("tv_channels", 1, json!({
        "channels": channels.iter().map(|ch| json!({ "canal": ch.canal, "url": ch.url })).collect::<Vec<_>>()
    })))
}

// --- SERVIDORES como widget ---
pub async fn list_servers() -> Result<String, String> {
    let content = fs::read_to_string("/var/osiris2/bin/net/rserver.nrl")
        .await
        .map_err(|e| format!("Error leyendo servidores: {}", e))?;
    let servers: Vec<serde_json::Value> = content.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| json!({ "host": l.trim() }))
        .collect();
    Ok(widget_msg("servers", 1, json!({ "servers": servers })))
}
