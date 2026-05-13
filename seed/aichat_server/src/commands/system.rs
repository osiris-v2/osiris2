// /var/osiris2/seed/aichat_server/src/commands/system.rs
use uuid::Uuid;
use serde_json::json;
use std::sync::atomic::Ordering;
use chrono::Local;

use crate::config::{AI_SESSIONS, ACTIVE_AI_INSTANCES, MAX_GLOBAL_INSTANCES, SERVER_START_TIME};
use crate::utils::{leer_ram, leer_uptime_os, formatear_duracion};
use crate::protocol::widget_msg;

pub async fn handle_system_command(
    command: &str,
    client_id: Uuid,
) -> Result<String, String> {
    let parts: Vec<&str> = command.split_whitespace().collect();

    match parts[0] {
        "/limit" => {
            let activos  = ACTIVE_AI_INSTANCES.load(Ordering::SeqCst);
            let total    = MAX_GLOBAL_INSTANCES;
            let clientes = AI_SESSIONS.lock().await.len();
            Ok(format!(
                "
📊 ESTADO:
  Instancias IA: {}/{}
  Disponibles: {}
  Clientes conectados: {}
", // Corregido
                activos, total, total.saturating_sub(activos), clientes
            ))
        }

        "/date" | "/info" => {
            let ahora = Local::now();
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
                formatear_duracion(Local::now().signed_duration_since(s.connected_at).num_seconds().max(0) as u64)
            ).unwrap_or_default();
            drop(sessions);

            let en_ram    = crate::ollama::obtener_modelos_en_ram().await;
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
        "/way"     => Ok("Sistema ODyN - Goyim Corp.".into()),

        _ => Err(format!("Comando desconocido de sistema: '{}'.", parts[0]))
    }
}
