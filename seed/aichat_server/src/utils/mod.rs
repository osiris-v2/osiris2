// /var/osiris2/seed/aichat_server/src/utils/mod.rs
use std::fs; // Temporalmente std::fs. Para evitar bloqueos en Tokio, estas funciones deberían usar tokio::task::spawn_blocking.

// --- HELPERS DE SISTEMA ---

// Idealmente, estas funciones deberían leer de /proc de forma asíncrona si es posible,
// o ser movidas a un módulo síncrono que se ejecute en un tokio::task::spawn_blocking.
// Por ahora, se mantienen como están para no introducir cambios profundos en el manejo de /proc
// y para minimizar el alcance de la corrección actual.
pub fn leer_ram() -> (u64, u64, u64) {
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

pub fn leer_uptime_os() -> u64 {
    fs::read_to_string("/proc/uptime").ok()
        .and_then(|s| s.split_whitespace().next().and_then(|v| v.parse::<f64>().ok()))
        .map(|f| f as u64).unwrap_or(0)
}

pub fn formatear_duracion(secs: u64) -> String {
    let d = secs / 86400;
    let h = (secs % 86400) / 3600;
    let m = (secs % 3600) / 60;
    if d > 0 { format!("{}d {}h {}m", d, h, m) }
    else if h > 0 { format!("{}h {}m", h, m) }
    else { format!("{}m", m) }
}

pub fn ram_necesaria_mb(modelo: &str) -> u64 {
    if modelo.contains("phi4") || modelo.contains("phi-4")            { 3500 }
    else if modelo.contains("7b") || modelo.contains("8b")            { 5000 }
    else if modelo.contains("3b") || modelo.contains("4b")            { 3000 }
    else if modelo.contains("1.5b") || modelo.contains("1.7b") || modelo.contains("1b") { 1200 }
    else if modelo.contains("360m") || modelo.contains("0.5b") || modelo.contains("0.6b") { 600 }
    else if modelo.contains("135m") || modelo.contains("270m")        { 400 }
    else                                                               { 2000 }
}
