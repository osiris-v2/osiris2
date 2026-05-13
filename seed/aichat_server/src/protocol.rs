// /var/osiris2/seed/aichat_server/src/protocol.rs
use serde_json::json;

// --- PROTOCOLO WIDGET ---
pub fn widget_msg(widget: &str, version: u32, data: serde_json::Value) -> String {
    json!({
        "type":    "widget",
        "widget":  widget,
        "version": version,
        "data":    data
    }).to_string()
}
