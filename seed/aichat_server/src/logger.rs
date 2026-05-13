// /var/osiris2/seed/aichat_server/src/logger.rs
use std::fs;
use std::fs::OpenOptions;
use std::io::Write;
use std::sync::Mutex as StdMutex;
use chrono;

use crate::config::{CONN_LOG_PATH, CONN_LOG_MAX_BYTES};

/// Logger de conexiones con rotación por tamaño máximo.
pub struct ConnLogger {
    path: &'static str,
    max_bytes: u64,
    lock: StdMutex<()>, // Mutex estándar, ya que `write` es síncrono
}

impl ConnLogger {
    pub const fn new(path: &'static str, max_bytes: u64) -> Self {
        Self { path, max_bytes, lock: StdMutex::new(()) }
    }

    pub fn write(&self, line: &str) {
        let _guard = self.lock.lock().unwrap_or_else(|e| e.into_inner());
        if let Ok(meta) = fs::metadata(self.path) {
            if meta.len() >= self.max_bytes {
                if let Ok(content) = fs::read_to_string(self.path) {
                    let keep_from = content.len() / 2;
                    let cut = content[keep_from..].find(' ')
                        .map(|p| keep_from + p + 1)
                        .unwrap_or(keep_from);
                    let kept = format!("# --- rotación automática ---{}", &content[cut..]);
                    let _ = fs::write(self.path, kept);
                }
            }
        }
        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(self.path) {
            let _ = writeln!(f, "{}", line);
        }
    }

    pub fn log_connect(&self, short_id: &str, ip: &str, model: &str, total_clients: usize) {
        let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
        self.write(&format!(
            "{} | CONNECT   | {} | ip={} | model={} | total_clients={}",
            ts, short_id, ip, model, total_clients
        ));
    }

    pub fn log_disconnect(&self, short_id: &str, ip: &str, duration_secs: u64, messages: usize, total_clients: usize) {
        let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
        self.write(&format!(
            "{} | DISCONNECT | {} | ip={} | session_secs={} | messages={} | total_clients={}",
            ts, short_id, ip, duration_secs, messages, total_clients
        ));
    }

    pub fn log_event(&self, short_id: &str, ip: &str, event: &str) {
        let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
        self.write(&format!(
            "{} | EVENT      | {} | ip={} | {}",
            ts, short_id, ip, event
        ));
    }
}

lazy_static::lazy_static! {
    pub static ref CONN_LOG: ConnLogger = ConnLogger::new(CONN_LOG_PATH, CONN_LOG_MAX_BYTES);
}
