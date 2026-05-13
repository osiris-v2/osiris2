// src/commands/mod.rs
use uuid::Uuid;
use tokio_tungstenite::tungstenite::Message;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::net::TcpStream;
use futures_util::stream::SplitSink;

mod system;
mod chat;
mod ai;
mod external;
pub mod auth;

use system::handle_system_command;
use chat::handle_chat_command;
use ai::handle_ai_command;
use auth::handle_auth_command;
use external::{list_tv_channels, list_servers};

/// Comandos que responden siempre, aunque la IA esté ocupada.
pub fn es_comando_libre(cmd: &str) -> bool {
    let base = cmd.split_whitespace().next().unwrap_or("");
    matches!(base,
        "/listtv"   | "/info"    | "/date"   | "/servers"
        | "/models" | "/who"    | "/perfil"  | "/help"
        | "/sala"   | "/login"  | "/logout"  | "/registro"
        | "/cuenta"
    )
}

pub async fn handle_command(
    command: &str,
    client_id: Uuid,
    _write_sink: Arc<Mutex<SplitSink<tokio_tungstenite::WebSocketStream<TcpStream>, Message>>>,
) -> Result<String, String> {
    let base = command.split_whitespace().next().unwrap_or("");

    match base {

        "/help" => Ok(r#"
📖 COMANDOS DISPONIBLES
══════════════════════════════════════════════════

🔐 IDENTIDAD (sistema base)
  /registro @usuario email contraseña  → Crear cuenta única permanente.
  /login    @usuario contraseña        → Iniciar sesión.
  /logout                              → Cerrar sesión (vuelves a anónimo).
  /cuenta                              → Ver tus datos privados de cuenta.

👤 PERFIL (visible / privado)
  /perfil ver
  /perfil personal nombre="X" desc="Y" tono=Z
  /perfil empresa  nombre="X" sector=S desc="Y" tono=Z
  /perfil publico  nombre|tipo|desc on|off   → Controlar visibilidad.
  /perfil guardar | cargar <reg> | lista | borrar

🤖 IA
  /models           Lista modelos Ollama.
  /model N          Cambia de modelo.
  /clearcontext     Borra contexto e historial.
  /limit            Instancias IA activas.
  /stop             Detiene la generación actual.

ℹ️  SISTEMA
  /info | /date     Métricas del servidor y sesión.
  /hello            Test de conexión.
  /way              Info del sistema ODyN.

💬 CHAT GLOBAL
  /who              Clientes conectados.
  /pm <id> <msg>    Mensaje privado.

🏠 SALAS PRIVADAS
  /sala crear [nombre]
  /sala invitar <sala> <usuario>
  /sala aceptar <sala>
  /sala msg <sala> <texto>
  /sala salir <sala>
  /sala lista

📺 OTROS
  /listtv           Canales TV activos.
  /servers          Servidores remotos.

══════════════════════════════════════════════════
"#.into()),

        "/registro" | "/login" | "/logout" | "/cuenta" => {
            handle_auth_command(command, client_id).await
        }

        "/clearcontext" | "/model" | "/models" => {
            handle_ai_command(command, client_id).await
        }

        "/limit" | "/info" | "/date" | "/hello" | "/way" => {
            handle_system_command(command, client_id).await
        }

        "/who" | "/perfil" | "/sala" => {
            handle_chat_command(command, client_id).await
        }

        "/listtv"  => list_tv_channels().await,
        "/servers" => list_servers().await,

        _ => Err(format!("Comando desconocido: '{}'. Escribe /help.", base))
    }
}
