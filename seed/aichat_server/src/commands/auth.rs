// src/commands/auth.rs
//
// ── COMANDOS DE IDENTIDAD ─────────────────────────────────────────────────────
//
//   /registro <@usuario> <email> <contraseña>
//   /login    <@usuario> <contraseña>
//   /logout
//   /cuenta                         → datos privados de la cuenta
//   /perfil publico <campo> on|off  → manejado en chat.rs pero usa db aquí
//
// Todas las operaciones de DB son síncronas (rusqlite); se lanzan con
// tokio::task::spawn_blocking para no bloquear el runtime async.

use uuid::Uuid;
use tokio::task::spawn_blocking;

use crate::config::{AI_SESSIONS, db};
use crate::session::NivelIdentidad;
use crate::db::PerfilRow;

// ── VALIDACIONES ──────────────────────────────────────────────────────────────

/// Valida formato de username: solo letras, números, guión bajo. 3–24 chars.
fn validar_username(u: &str) -> Result<(), String> {
    let u = u.trim_start_matches('@');
    if u.len() < 3  { return Err("El usuario debe tener al menos 3 caracteres.".into()); }
    if u.len() > 24 { return Err("El usuario no puede superar 24 caracteres.".into()); }
    if !u.chars().all(|c| c.is_ascii_alphanumeric() || c == '_') {
        return Err("Solo se permiten letras, números y '_' en el nombre de usuario.".into());
    }
    Ok(())
}

fn validar_email(e: &str) -> Result<(), String> {
    if e.contains('@') && e.contains('.') { Ok(()) }
    else { Err("El email no tiene un formato válido.".into()) }
}

fn validar_password(p: &str) -> Result<(), String> {
    if p.len() < 8 { Err("La contraseña debe tener al menos 8 caracteres.".into()) }
    else { Ok(()) }
}

// ── HANDLERS ─────────────────────────────────────────────────────────────────

pub async fn handle_auth_command(
    command: &str,
    client_id: Uuid,
) -> Result<String, String> {
    let parts: Vec<&str> = command.splitn(5, ' ').collect();
    let cmd = parts[0];

    match cmd {

        // ── /registro @usuario email contraseña ───────────────────────────
        "/registro" => {
            if parts.len() < 4 {
                return Err(
                    "Uso: /registro <@usuario> <email> <contraseña>\n\
                    Ejemplo: /registro @juan juan@ejemplo.com MiPass123".into()
                );
            }

            // ¿Ya está autenticado?
            {
                let sessions = AI_SESSIONS.lock().await;
                if let Some(s) = sessions.get(&client_id) {
                    if s.identidad.es_registrado() {
                        return Err(format!(
                            "Ya estás registrado como {}. Haz /logout primero.",
                            s.virtual_name()
                        ));
                    }
                }
            }

            let username = parts[1].trim_start_matches('@').trim().to_string();
            let email    = parts[2].trim().to_string();
            let password = parts[3].trim().to_string();

            validar_username(&username)?;
            validar_email(&email)?;
            validar_password(&password)?;

            // Operación bloqueante en hilo aparte
            let user2 = username.clone();
            let email2 = email.clone();
            let pass2  = password.clone();

            let resultado = spawn_blocking(move || {
                db().crear_usuario(&user2, &email2, &pass2)
            }).await.map_err(|e| format!("Error interno: {}", e))?;

            match resultado {
                Err(e) => Err(format!("❌ {}", e)),
                Ok(user_id) => {
                    // Login automático tras registro exitoso
                    aplicar_login(client_id, user_id, username.clone()).await;
                    Ok(format!(
                        "✅ Cuenta creada y sesión iniciada como @{}.\n\
                        Tu identidad en este servidor es única y persistente.\n\
                        Configura tu perfil con: /perfil personal nombre=\"X\" desc=\"Y\"\n\
                        Controla tu privacidad con: /perfil publico nombre on|off",
                        username
                    ))
                }
            }
        }

        // ── /login @usuario contraseña ────────────────────────────────────
        "/login" => {
            if parts.len() < 3 {
                return Err("Uso: /login <@usuario> <contraseña>".into());
            }

            // ¿Ya autenticado?
            {
                let sessions = AI_SESSIONS.lock().await;
                if let Some(s) = sessions.get(&client_id) {
                    if s.identidad.es_registrado() {
                        return Err(format!(
                            "Ya tienes sesión como {}. Usa /logout primero.",
                            s.virtual_name()
                        ));
                    }
                }
            }

            let username = parts[1].trim_start_matches('@').trim().to_string();
            let password = parts[2].trim().to_string();

            // Verificar que no hay otra sesión activa con este username
            {
                let sessions = AI_SESSIONS.lock().await;
                let ya_conectado = sessions.values().any(|s| {
                    s.identidad.username()
                        .map(|u| u.eq_ignore_ascii_case(&username))
                        .unwrap_or(false)
                });
                if ya_conectado {
                    return Err(format!(
                        "❌ @{} ya tiene una sesión activa en este servidor.\n\
                        Solo puede haber una sesión por usuario.",
                        username
                    ));
                }
            }

            let user2 = username.clone();
            let pass2 = password.clone();

            let resultado = spawn_blocking(move || {
                db().verificar_login(&user2, &pass2)
            }).await.map_err(|e| format!("Error interno: {}", e))?;

            match resultado {
                Err(e) => Err(format!("❌ {}", e)),
                Ok(row) => {
                    let user_id  = row.id;
                    let username = row.username.clone();

                    // Actualizar last_login en hilo aparte (sin esperar)
                    tokio::task::spawn_blocking(move || {
                        db().actualizar_ultimo_login(user_id);
                    });

                    // Cargar perfil de DB a RAM
                    let uid2 = user_id;
                    let perfil_db = spawn_blocking(move || {
                        db().obtener_perfil(uid2)
                    }).await.ok().flatten();

                    aplicar_login(client_id, user_id, username.clone()).await;

                    // Volcar perfil de DB a sesión en RAM
                    if let Some(p) = perfil_db {
                        cargar_perfil_db_a_ram(client_id, &p).await;
                    }

                    Ok(format!(
                        "✅ Sesión iniciada como @{}.\n\
                        Último acceso: {}.\n\
                        Escribe /cuenta para ver tus datos.",
                        username, row.last_login
                    ))
                }
            }
        }

        // ── /logout ───────────────────────────────────────────────────────
        "/logout" => {
            let mut sessions = AI_SESSIONS.lock().await;
            if let Some(s) = sessions.get_mut(&client_id) {
                if !s.identidad.es_registrado() {
                    return Err("No tienes sesión registrada activa.".into());
                }
                let nombre = s.virtual_name();
                s.identidad = NivelIdentidad::Anonimo;
                s.perfil    = crate::session::PerfilUsuario::default();
                Ok(format!("👋 Sesión de {} cerrada. Ahora eres anónimo ({}).",
                    nombre, s.short_id))
            } else {
                Err("Sesión no encontrada.".into())
            }
        }

        // ── /cuenta ───────────────────────────────────────────────────────
        "/cuenta" => {
            let user_id = {
                let sessions = AI_SESSIONS.lock().await;
                sessions.get(&client_id)
                    .and_then(|s| s.identidad.user_id())
                    .ok_or("Debes estar autenticado para ver tu cuenta. Usa /login.")?
            };

            let cuenta = spawn_blocking(move || {
                db().obtener_cuenta(user_id)
            }).await.map_err(|e| format!("Error interno: {}", e))?
              .ok_or("No se encontraron datos de cuenta.")?;

            let perfil_str = match &cuenta.perfil {
                None    => "  (sin perfil configurado)".to_string(),
                Some(p) => format!(
                    "  Tipo:        {}\n  Nombre:      {}\n  Sector:      {}\n\
                     Descripción: {}\n  Tono:        {}\n\
                     Público:     nombre={} tipo={} desc={}",
                    p.tipo, p.nombre, p.sector, p.descripcion, p.tono,
                    if p.pub_nombre {"on"} else {"off"},
                    if p.pub_tipo   {"on"} else {"off"},
                    if p.pub_desc   {"on"} else {"off"},
                ),
            };

            Ok(format!(
                "👤 TU CUENTA (solo visible para ti)\n\
                ══════════════════════════════════\n\
                Usuario:    @{}\n\
                Email:      {}\n\
                Registrado: {}\n\
                Último acc: {}\n\
                ──────────────────────────────────\n\
                PERFIL:\n{}\n\
                ══════════════════════════════════\n\
                /perfil publico nombre on|off  → controlar visibilidad",
                cuenta.username,
                cuenta.email,
                cuenta.created_at,
                if cuenta.last_login.is_empty() { "primera vez" } else { &cuenta.last_login },
                perfil_str
            ))
        }

        _ => Err(format!("Comando de auth desconocido: '{}'.", cmd))
    }
}

// ── HELPERS INTERNOS ──────────────────────────────────────────────────────────

/// Aplica el login en la sesión en RAM.
async fn aplicar_login(client_id: Uuid, user_id: i64, username: String) {
    let mut sessions = AI_SESSIONS.lock().await;
    if let Some(s) = sessions.get_mut(&client_id) {
        s.identidad = NivelIdentidad::Registrado { user_id, username };
    }
}

/// Vuelca un PerfilRow de la DB al PerfilUsuario en RAM de la sesión.
async fn cargar_perfil_db_a_ram(client_id: Uuid, p: &PerfilRow) {
    use crate::session::{PerfilUsuario, TipoPerfil};
    let tipo = match p.tipo.as_str() {
        "personal" => TipoPerfil::Personal,
        "empresa"  => TipoPerfil::Empresa,
        _          => TipoPerfil::Ninguno,
    };
    let perfil = PerfilUsuario {
        tipo,
        nombre:          p.nombre.clone(),
        descripcion:     p.descripcion.clone(),
        sector:          p.sector.clone(),
        tono:            p.tono.clone(),
        nombre_registro: String::new(), // no aplica para registrados
    };
    let mut sessions = AI_SESSIONS.lock().await;
    if let Some(s) = sessions.get_mut(&client_id) {
        s.perfil = perfil;
    }
}

/// Convierte el PerfilUsuario en RAM a PerfilRow para guardarlo en DB.
/// Solo para usuarios autenticados.
pub fn perfil_ram_a_db(
    user_id: i64,
    p: &crate::session::PerfilUsuario,
    pub_nombre: bool,
    pub_tipo: bool,
    pub_desc: bool,
) -> PerfilRow {
    use crate::session::TipoPerfil;
    PerfilRow {
        user_id,
        tipo:        match p.tipo {
            TipoPerfil::Personal => "personal".to_string(),
            TipoPerfil::Empresa  => "empresa".to_string(),
            TipoPerfil::Ninguno  => String::new(),
        },
        nombre:      p.nombre.clone(),
        descripcion: p.descripcion.clone(),
        sector:      p.sector.clone(),
        tono:        p.tono.clone(),
        pub_nombre,
        pub_tipo,
        pub_desc,
    }
}
