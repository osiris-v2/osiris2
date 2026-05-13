// /var/osiris2/seed/aichat_server/src/commands/ai.rs
use uuid::Uuid;
use serde_json::json;

use crate::config::AI_SESSIONS;
use crate::ollama::{obtener_modelos_ollama, obtener_modelos_en_ram};
use crate::utils::{leer_ram, ram_necesaria_mb};
use crate::protocol::widget_msg;
use crate::logger::CONN_LOG;

pub async fn handle_ai_command(
    command: &str,
    client_id: Uuid,
) -> Result<String, String> {
    let parts: Vec<&str> = command.split_whitespace().collect();

    match parts[0] {
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
                format!("
⚠️  RAM disponible: {}MB — este modelo puede requerir swap.", avail_mb) // Corregido
            } else { String::new() };

            let mut sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get_mut(&client_id) {
                let anterior = s.model.clone();
                s.model = nombre.clone();
                s.context.clear();
                CONN_LOG.log_event(&s.short_id.clone(), "n/a", &format!("model_change from={} to={}", anterior, nombre));
                Ok(format!(
                    "✅ IA cambiada: {} → {}
💬 Historial conservado ({} turnos).{}", // Corregido
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
        _ => Err(format!("Comando desconocido de IA: '{}'.", parts[0]))
    }
}
