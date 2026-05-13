// src/config.rs
use lazy_static::lazy_static;
use tokio::sync::Mutex;
use std::collections::HashMap;
use uuid::Uuid;
use std::sync::atomic::AtomicUsize;
use std::sync::Arc;

use crate::session::ClientSession;
use crate::db::Db;

// ── SERVIDOR ──────────────────────────────────────────────────────────────────
pub const MAX_GLOBAL_INSTANCES:   usize = 2;
pub const MAX_HISTORY_MESSAGES:   usize = 20;
pub const DEFAULT_MODEL_FALLBACK: &str  = "llama3.2:latest";
pub const OLLAMA_URL:             &str  = "http://localhost:11434";
pub const OLLAMA_TIMEOUT_SECS:    u64   = 500;

// ── LOGS ──────────────────────────────────────────────────────────────────────
pub const CONN_LOG_PATH:      &str = "/var/log/goyimai_connections.log";
pub const CONN_LOG_MAX_BYTES: u64  = 256 * 1024;

// ── DATOS EN DISCO ────────────────────────────────────────────────────────────
/// Base de datos SQLite. Cambia esta constante para mover la DB.
pub const DB_PATH:      &str = "/var/osiris2/data/goyim.db";
/// Perfiles temporales de usuarios anónimos.
pub const PROFILES_DIR: &str = "/var/osiris2/data/profiles";
/// Base de carpetas tmp aisladas por sesión.
pub const TMP_BASE:     &str = "/tmp/aichat";

// ── SESIONES / SALAS ──────────────────────────────────────────────────────────
pub const SHORT_ID_LEN:    usize = 8;
pub const ROOM_MAX_MEMBERS: usize = 20;

// ── CONTADORES ────────────────────────────────────────────────────────────────
pub static ACTIVE_AI_INSTANCES: AtomicUsize = AtomicUsize::new(0);

// ── HANDLE GLOBAL DE LA DB ───────────────────────────────────────────────────
/// Inicializado una sola vez en main(). Usar config::db() para acceder.
pub static DATABASE: std::sync::OnceLock<Db> = std::sync::OnceLock::new();

/// Devuelve el handle de la DB. Panic si main() no llamó a DATABASE.set().
pub fn db() -> &'static Db {
    DATABASE.get().expect("DATABASE no inicializada")
}

// ── LAZY STATICS ─────────────────────────────────────────────────────────────
lazy_static! {
    pub static ref AI_LIMIT_SEM: Arc<tokio::sync::Semaphore> =
        Arc::new(tokio::sync::Semaphore::new(MAX_GLOBAL_INSTANCES));

    pub static ref AI_SESSIONS: Mutex<HashMap<Uuid, ClientSession>> =
        Mutex::new(HashMap::new());

    pub static ref SERVER_START_TIME: chrono::DateTime<chrono::Local> =
        chrono::Local::now();

    pub static ref PRIVATE_ROOMS: Mutex<HashMap<String, PrivateRoom>> =
        Mutex::new(HashMap::new());
}

// ── SALA PRIVADA ──────────────────────────────────────────────────────────────
#[derive(Debug, Clone)]
pub struct PrivateRoom {
    pub id:      String,
    pub owner:   Uuid,
    pub members: Vec<Uuid>,
    pub pending: Vec<Uuid>,
    pub name:    String,
}

impl PrivateRoom {
    pub fn new(id: String, owner: Uuid, name: String) -> Self {
        Self { id, owner, members: vec![owner], pending: vec![], name }
    }
    pub fn is_member(&self, uuid: &Uuid) -> bool {
        self.members.contains(uuid)
    }
}
