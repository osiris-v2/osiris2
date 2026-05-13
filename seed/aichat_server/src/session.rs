// src/session.rs
use tokio::sync::mpsc;
use tokio::task::AbortHandle;
use tokio_tungstenite::tungstenite::Message;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use log::warn;

use crate::config::MAX_HISTORY_MESSAGES;

pub type ChatTx = mpsc::UnboundedSender<Message>;

// ── NIVEL DE IDENTIDAD ────────────────────────────────────────────────────────

#[derive(Clone, Debug, Default, PartialEq)]
pub enum NivelIdentidad {
    #[default]
    Anonimo,
    Registrado {
        user_id:  i64,
        username: String,
    },
}

impl NivelIdentidad {
    pub fn es_registrado(&self) -> bool {
        matches!(self, NivelIdentidad::Registrado { .. })
    }

    pub fn nombre_visible(&self, short_id: &str) -> String {
        match self {
            NivelIdentidad::Anonimo => format!("{}@server", short_id),
            NivelIdentidad::Registrado { username, .. } => format!("@{}", username),
        }
    }

    pub fn username(&self) -> Option<&str> {
        match self {
            NivelIdentidad::Registrado { username, .. } => Some(username.as_str()),
            _ => None,
        }
    }

    pub fn user_id(&self) -> Option<i64> {
        match self {
            NivelIdentidad::Registrado { user_id, .. } => Some(*user_id),
            _ => None,
        }
    }
}

// ── TIPO DE PERFIL ────────────────────────────────────────────────────────────

#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq)]
pub enum TipoPerfil {
    #[default]
    Ninguno,
    Personal,
    Empresa,
}

// ── PERFIL EN RAM ─────────────────────────────────────────────────────────────

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct PerfilUsuario {
    pub tipo:            TipoPerfil,
    pub nombre:          String,
    pub descripcion:     String,
    pub sector:          String,
    pub tono:            String,
    /// Solo usado para perfiles anónimos (nivel 0) guardados en /tmp
    pub nombre_registro: String,
}

impl PerfilUsuario {
    pub fn calcular_registro(nombre: &str) -> String {
        let ascii = nombre.to_lowercase().chars().map(|c| match c {
            'á'|'à'|'ä'|'â' => 'a',
            'é'|'è'|'ë'|'ê' => 'e',
            'í'|'ì'|'ï'|'î' => 'i',
            'ó'|'ò'|'ö'|'ô' => 'o',
            'ú'|'ù'|'ü'|'û' => 'u',
            'ñ' => 'n', 'ç' => 'c',
            'a'..='z'|'0'..='9' => c,
            _ => '_',
        }).collect::<String>();
        let mut last = '_';
        let collapsed: String = ascii.chars().filter(|&c| {
            if c == '_' && last == '_' { return false; }
            last = c; true
        }).collect();
        collapsed.trim_matches('_').to_string()
    }

    pub fn para_prompt(&self) -> String {
        match self.tipo {
            TipoPerfil::Ninguno => String::new(),

            TipoPerfil::Personal => format!(
                "── PERFIL DEL USUARIO ────────────────────────────────────────────────\n\
                Tipo:        Personal\n\
                Nombre:      {nombre}\n\
                Descripción: {descripcion}\n\
                Tono:        {tono}\n\
                Adapta tus respuestas a este perfil.\n",
                nombre      = ifne(&self.nombre,      "no especificado"),
                descripcion = ifne(&self.descripcion, "no especificada"),
                tono        = ifne(&self.tono,        "neutro"),
            ),

            TipoPerfil::Empresa => format!(
                "── PERFIL DE EMPRESA ─────────────────────────────────────────────────\n\
                Tipo:        Empresa\n\
                Nombre:      {nombre}\n\
                Sector:      {sector}\n\
                Descripción: {descripcion}\n\
                Tono:        {tono}\n\
                Prioriza contexto corporativo.\n",
                nombre      = ifne(&self.nombre,      "no especificado"),
                sector      = ifne(&self.sector,      "no especificado"),
                descripcion = ifne(&self.descripcion, "no especificada"),
                tono        = ifne(&self.tono,        "profesional"),
            ),
        }
    }

    pub fn tiene_perfil(&self) -> bool {
        !matches!(self.tipo, TipoPerfil::Ninguno)
    }

    pub fn resumen_corto(&self) -> &str {
        match self.tipo {
            TipoPerfil::Ninguno  => "ninguno",
            TipoPerfil::Personal => "personal",
            TipoPerfil::Empresa  => "empresa",
        }
    }
}

fn ifne<'a>(s: &'a str, default: &'a str) -> &'a str {
    if s.is_empty() { default } else { s }
}

// ── SESIÓN DE CLIENTE ─────────────────────────────────────────────────────────

pub struct ClientSession {
    pub context:       Vec<i64>,
    pub history_text:  Vec<(String, String)>,
    pub model:         String,
    pub is_busy:       bool,
    pub abort_handle:  Option<AbortHandle>,
    pub connected_at:  chrono::DateTime<chrono::Local>,
    pub messages_sent: usize,
    /// ID efímero de 8 hex. Siempre presente independientemente del nivel.
    pub short_id:      String,
    /// Canal mpsc hacia el WS del cliente.
    pub chat_tx:       ChatTx,
    /// Perfil en RAM (inyectado en el system prompt de Ollama).
    pub perfil:        PerfilUsuario,
    /// Salas privadas activas.
    pub rooms:         Vec<String>,
    /// Nivel de identidad: Anonimo | Registrado { user_id, username }
    pub identidad:     NivelIdentidad,
    /// Carpeta temporal aislada: /tmp/aichat/<short_id>/
    /// Creada al conectar, eliminada al desconectar.
    pub tmp_dir:       PathBuf,
}

impl ClientSession {
    pub fn new(model: String, short_id: String, chat_tx: ChatTx) -> Self {
        let tmp_dir = PathBuf::from(format!("/tmp/aichat/{}", short_id));
        if let Err(e) = std::fs::create_dir_all(&tmp_dir) {
            warn!("No se pudo crear {}: {}", tmp_dir.display(), e);
        }
        Self {
            context:       Vec::new(),
            history_text:  Vec::new(),
            model,
            is_busy:       false,
            abort_handle:  None,
            connected_at:  chrono::Local::now(),
            messages_sent: 0,
            short_id,
            chat_tx,
            perfil:        PerfilUsuario::default(),
            rooms:         Vec::new(),
            identidad:     NivelIdentidad::Anonimo,
            tmp_dir,
        }
    }

    pub fn add_history(&mut self, user: String, assistant: String) {
        self.history_text.push((user, assistant));
        if self.history_text.len() > MAX_HISTORY_MESSAGES {
            self.history_text.remove(0);
        }
        self.messages_sent += 1;
    }

    pub fn history_as_text(&self) -> String {
        if self.history_text.is_empty() { return String::new(); }
        let mut out = String::from(
            "\n── Conversación previa ───────────────────────────────────────────────\n"
        );
        for (u, a) in &self.history_text {
            out.push_str(&format!("Usuario:    {}\nAsistente: {}\n", u, a));
        }
        out.push_str(
            "──────────────────────────────────────────────────────────────────────\n"
        );
        out
    }

    /// Nombre visible en el chat y en logs.
    pub fn virtual_name(&self) -> String {
        self.identidad.nombre_visible(&self.short_id)
    }

    /// Limpia la carpeta /tmp al desconectar.
    pub fn limpiar_tmp(&self) {
        if self.tmp_dir.exists() {
            if let Err(e) = std::fs::remove_dir_all(&self.tmp_dir) {
                warn!("Error limpiando {}: {}", self.tmp_dir.display(), e);
            }
        }
    }

    /// Escribe un fichero en la carpeta tmp de esta sesión.
    #[allow(dead_code)]
    pub fn tmp_write(&self, nombre: &str, contenido: &str) {
        let path = self.tmp_dir.join(nombre);
        if let Err(e) = std::fs::write(&path, contenido) {
            warn!("tmp_write {}: {}", path.display(), e);
        }
    }

    /// Lee un fichero de la carpeta tmp de esta sesión.
    #[allow(dead_code)]
    pub fn tmp_read(&self, nombre: &str) -> Option<String> {
        std::fs::read_to_string(self.tmp_dir.join(nombre)).ok()
    }
}
