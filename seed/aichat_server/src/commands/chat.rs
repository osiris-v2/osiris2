// src/commands/chat.rs
use uuid::Uuid;
use serde_json::json;
use chrono::Local;
use tokio::task::spawn_blocking;

use crate::config::{AI_SESSIONS, db};
use crate::utils::formatear_duracion;
use crate::protocol::widget_msg;
use crate::session::{PerfilUsuario, TipoPerfil};
use crate::profile::{guardar_perfil, cargar_perfil, listar_perfiles, borrar_perfil};
use crate::social::{
    crear_sala, invitar_a_sala, aceptar_invitacion,
    enviar_a_sala, salir_de_sala, mis_salas,
};
use crate::commands::auth::perfil_ram_a_db;
use crate::db::PerfilRow;

// ── PARSER DE ARGUMENTOS CON ESPACIOS ────────────────────────────────────────
// Soporta: clave=valor  clave="valor con espacios"  clave='valor con espacios'
fn parse_kv(args: &str, key: &str) -> String {
    let needle = format!("{}=", key);
    let Some(pos) = args.find(&needle) else { return String::new(); };
    let after = &args[pos + needle.len()..];

    if after.starts_with('"') {
        let inner = &after[1..];
        return inner.find('"')
            .map(|e| inner[..e].trim().to_string())
            .unwrap_or_else(|| inner.trim().to_string());
    }
    if after.starts_with('\'') {
        let inner = &after[1..];
        return inner.find('\'')
            .map(|e| inner[..e].trim().to_string())
            .unwrap_or_else(|| inner.trim().to_string());
    }
    // Sin comillas: hasta la próxima clave conocida o fin
    let known = ["nombre=","desc=","tono=","sector=","registro=","publico="];
    let mut end = after.len();
    for k in &known {
        if let Some(p) = after.find(k) {
            if p > 0 && p < end { end = p; }
        }
    }
    after[..end].trim().to_string()
}

// ── HANDLER PRINCIPAL ─────────────────────────────────────────────────────────

pub async fn handle_chat_command(command: &str, client_id: Uuid) -> Result<String, String> {
    let (cmd, rest) = {
        let mut it = command.splitn(2, ' ');
        let c = it.next().unwrap_or("");
        let r = it.next().unwrap_or("");
        (c, r)
    };

    match cmd {

        // ── /who ──────────────────────────────────────────────────────────
        "/who" => {
            let sessions = AI_SESSIONS.lock().await;
            let ahora = Local::now();
            let users: Vec<serde_json::Value> = sessions.values().map(|s| {
                let dur = ahora.signed_duration_since(s.connected_at).num_seconds().max(0) as u64;
                json!({
                    "id":         s.short_id,
                    "vname":      s.virtual_name(),
                    "registrado": s.identidad.es_registrado(),
                    "model":      s.model,
                    "since":      formatear_duracion(dur),
                    "msgs":       s.messages_sent,
                    "busy":       s.is_busy,
                    "perfil":     s.perfil.resumen_corto(),
                    "salas":      s.rooms.len()
                })
            }).collect();
            Ok(widget_msg("who", 3, json!({ "users": users })))
        }

        // ── /perfil ───────────────────────────────────────────────────────
        "/perfil" => {
            let (sub, args) = {
                let mut it = rest.splitn(2, ' ');
                let s = it.next().unwrap_or("ver");
                let a = it.next().unwrap_or("");
                (s, a)
            };

            match sub {

                "ver" => {
                    let sessions = AI_SESSIONS.lock().await;
                    let s = sessions.get(&client_id).ok_or("Sesión no encontrada.")?;
                    if !s.perfil.tiene_perfil() {
                        return Ok(format!(
                            "👤 Sin perfil activo. Eres {}\n\
                            Comandos:\n\
                            • /perfil personal nombre=\"X\" desc=\"Y\" tono=Z\n\
                            • /perfil empresa  nombre=\"X\" sector=S desc=\"Y\" tono=Z\n\
                            {}",
                            s.virtual_name(),
                            if s.identidad.es_registrado() {
                                "• /perfil publico nombre on|off"
                            } else {
                                "• /registro para cuenta permanente"
                            }
                        ));
                    }
                    let extra = if s.identidad.es_registrado() {
                        "\n💾 Perfil guardado en cuenta registrada."
                    } else {
                        "\n⚠️  Sesión anónima — el perfil se perderá al desconectar. Usa /registro."
                    };
                    Ok(format!("👤 Perfil activo:\n{}{}", s.perfil.para_prompt(), extra))
                }

                // /perfil publico <campo> on|off  (solo registrados)
                "publico" => {
                    let mut it = args.split_whitespace();
                    let campo = it.next().unwrap_or("");
                    let valor_str = it.next().unwrap_or("");

                    if campo.is_empty() || valor_str.is_empty() {
                        return Err(
                            "Uso: /perfil publico <nombre|tipo|desc> <on|off>".into()
                        );
                    }
                    let valor = match valor_str {
                        "on"  | "1" | "si" | "yes" => true,
                        "off" | "0" | "no"         => false,
                        _ => return Err("Usa 'on' u 'off'.".into()),
                    };
                    let campo_ok = matches!(campo, "nombre"|"tipo"|"desc");
                    if !campo_ok {
                        return Err("Campos disponibles: nombre, tipo, desc.".into());
                    }

                    let user_id = {
                        let sessions = AI_SESSIONS.lock().await;
                        sessions.get(&client_id)
                            .and_then(|s| s.identidad.user_id())
                            .ok_or("Debes estar autenticado. Usa /login o /registro.")?
                    };

                    let campo2 = campo.to_string();
                    let res = spawn_blocking(move || {
                        db().set_visibilidad(user_id, &campo2, valor)
                    }).await.map_err(|e| format!("Error interno: {}", e))?;

                    res.map_err(|e| format!("❌ {}", e))?;
                    Ok(format!(
                        "✅ Campo '{}' ahora es {}.",
                        campo,
                        if valor { "público 👁️" } else { "privado 🔒" }
                    ))
                }

                "guardar" => {
                    let (user_id, perfil) = {
                        let sessions = AI_SESSIONS.lock().await;
                        let s = sessions.get(&client_id).ok_or("Sesión no encontrada.")?;
                        (s.identidad.user_id(), s.perfil.clone())
                    };

                    match user_id {
                        // Registrado → guardar en DB
                        Some(uid) => {
                            if !perfil.tiene_perfil() {
                                return Err("No hay perfil activo que guardar.".into());
                            }
                            // Obtener flags actuales de visibilidad
                            let uid2 = uid;
                            let fila_actual = spawn_blocking(move || {
                                db().obtener_perfil(uid2)
                            }).await.ok().flatten();

                            let (pn, pt, pd) = fila_actual
                                .map(|f| (f.pub_nombre, f.pub_tipo, f.pub_desc))
                                .unwrap_or((true, true, false));

                            let fila = perfil_ram_a_db(uid, &perfil, pn, pt, pd);
                            let res = spawn_blocking(move || {
                                db().guardar_perfil(&fila)
                            }).await.map_err(|e| format!("Error interno: {}", e))?;
                            res.map_err(|e| format!("❌ {}", e))?;
                            Ok("💾 Perfil guardado en tu cuenta.".into())
                        }
                        // Anónimo → guardar en disco /var/osiris2/data/profiles/
                        None => {
                            if !perfil.tiene_perfil() {
                                return Err("No hay perfil activo que guardar.".into());
                            }
                            guardar_perfil(&perfil).map_err(|e| format!("❌ {}", e))?;
                            Ok(format!(
                                "💾 Perfil guardado en disco ('{}.json').\n\
                                ⚠️  Sesión anónima: usa /registro para persistencia real.",
                                perfil.nombre_registro
                            ))
                        }
                    }
                }

                "cargar" => {
                    // Solo anónimos — los registrados cargan al hacer /login
                    let es_registrado = {
                        let sessions = AI_SESSIONS.lock().await;
                        sessions.get(&client_id)
                            .map(|s| s.identidad.es_registrado())
                            .unwrap_or(false)
                    };
                    if es_registrado {
                        return Err(
                            "Eres usuario registrado. Tu perfil se carga automáticamente al hacer /login.".into()
                        );
                    }
                    let nombre_reg = args.trim();
                    if nombre_reg.is_empty() {
                        return Err("Uso: /perfil cargar <nombre_registro>".into());
                    }
                    match cargar_perfil(nombre_reg) {
                        None => Err(format!(
                            "❌ Perfil '{}' no encontrado. Usa /perfil lista.", nombre_reg
                        )),
                        Some(p) => {
                            let resumen = p.para_prompt();
                            let mut sessions = AI_SESSIONS.lock().await;
                            let s = sessions.get_mut(&client_id).ok_or("Sesión no encontrada.")?;
                            s.perfil = p;
                            Ok(format!("✅ Perfil temporal cargado:\n{}", resumen))
                        }
                    }
                }

                "lista" => {
                    let perfiles = listar_perfiles();
                    if perfiles.is_empty() {
                        return Ok("📂 No hay perfiles temporales en disco.".into());
                    }
                    Ok(format!("📂 Perfiles temporales: {}", perfiles.join(", ")))
                }

                "borrar" => {
                    let (user_id, reg) = {
                        let mut sessions = AI_SESSIONS.lock().await;
                        let s = sessions.get_mut(&client_id).ok_or("Sesión no encontrada.")?;
                        let uid = s.identidad.user_id();
                        let reg = s.perfil.nombre_registro.clone();
                        s.perfil = PerfilUsuario::default();
                        (uid, reg)
                    };

                    match user_id {
                        Some(uid) => {
                            // Para registrados, borramos perfil de DB
                            let fila = PerfilRow {
                                user_id: uid,
                                tipo: String::new(), nombre: String::new(),
                                descripcion: String::new(), sector: String::new(),
                                tono: String::new(),
                                pub_nombre: true, pub_tipo: true, pub_desc: false,
                            };
                            let _ = spawn_blocking(move || db().guardar_perfil(&fila)).await;
                            Ok("🗑️ Perfil eliminado de RAM y cuenta.".into())
                        }
                        None => {
                            if !reg.is_empty() {
                                match borrar_perfil(&reg) {
                                    Ok(_)  => Ok(format!("🗑️ Perfil '{}' eliminado de RAM y disco.", reg)),
                                    Err(e) => Ok(format!("🗑️ Perfil eliminado de RAM. Disco: {}", e)),
                                }
                            } else {
                                Ok("🗑️ Perfil eliminado de RAM.".into())
                            }
                        }
                    }
                }

                tipo @ ("personal" | "empresa") => {
                    let nombre      = parse_kv(args, "nombre");
                    let descripcion = parse_kv(args, "desc");
                    let sector      = parse_kv(args, "sector");
                    let tono        = parse_kv(args, "tono");
                    let reg_raw     = parse_kv(args, "registro");

                    let nombre_registro = if !reg_raw.is_empty() {
                        PerfilUsuario::calcular_registro(&reg_raw)
                    } else if !nombre.is_empty() {
                        PerfilUsuario::calcular_registro(&nombre)
                    } else {
                        String::new()
                    };

                    let perfil = PerfilUsuario {
                        tipo: if tipo == "empresa" { TipoPerfil::Empresa } else { TipoPerfil::Personal },
                        nombre, descripcion, sector, tono,
                        nombre_registro: nombre_registro.clone(),
                    };
                    let resumen = perfil.para_prompt();

                    let (user_id, vname) = {
                        let mut sessions = AI_SESSIONS.lock().await;
                        let s = sessions.get_mut(&client_id).ok_or("Sesión no encontrada.")?;
                        let uid = s.identidad.user_id();
                        let vn  = s.virtual_name();
                        s.perfil = perfil.clone();
                        (uid, vn)
                    };

                    // Guardar automáticamente según nivel de identidad
                    let disco_msg = match user_id {
                        Some(uid) => {
                            // Registrado → DB
                            let fila = perfil_ram_a_db(uid, &perfil, true, true, false);
                            match spawn_blocking(move || db().guardar_perfil(&fila)).await {
                                Ok(Ok(_))  => "\n💾 Guardado en tu cuenta de forma permanente.".to_string(),
                                Ok(Err(e)) => format!("\n⚠️  Error guardando en DB: {}", e),
                                Err(e)     => format!("\n⚠️  Error interno: {}", e),
                            }
                        }
                        None => {
                            // Anónimo → disco temporal
                            if !nombre_registro.is_empty() {
                                match guardar_perfil(&perfil) {
                                    Ok(_)  => format!("\n💾 Guardado en disco como '{}.json'.\n⚠️  Usa /registro para cuenta permanente.", nombre_registro),
                                    Err(e) => format!("\n⚠️  No se pudo guardar en disco: {}", e),
                                }
                            } else {
                                "\n⚠️  Sin nombre — no persistido. Añade nombre=\"X\" para guardar.".to_string()
                            }
                        }
                    };

                    Ok(format!("✅ Perfil configurado para {}:\n{}{}", vname, resumen, disco_msg))
                }

                _ => Err(
                    "Uso: /perfil [ver|personal|empresa|guardar|cargar|borrar|lista|publico]\n\
                    Ejemplos:\n\
                    • /perfil personal nombre=\"Ana López\" desc=\"Diseñadora\" tono=informal\n\
                    • /perfil publico nombre on\n\
                    • /perfil empresa  nombre=\"MiCorp\" sector=tech tono=formal".into()
                )
            }
        }

        // ── /sala ─────────────────────────────────────────────────────────
        "/sala" => {
            let (sub, args) = {
                let mut it = rest.splitn(2, ' ');
                let s = it.next().unwrap_or("");
                let a = it.next().unwrap_or("");
                (s, a)
            };

            match sub {
                "crear" => {
                    let nombre = if args.trim().is_empty() {
                        "sala privada".to_string()
                    } else {
                        args.trim().to_string()
                    };
                    match crear_sala(client_id, nombre.clone()).await {
                        Ok(room_id) => Ok(format!(
                            "🏠 Sala '{}' creada: {}\n\
                            Invita con: /sala invitar {} <usuario>",
                            nombre, room_id, room_id
                        )),
                        Err(e) => Err(e),
                    }
                }
                "invitar" => {
                    let mut it = args.splitn(2, ' ');
                    let room_id  = it.next().unwrap_or("").trim();
                    let short_id = it.next().unwrap_or("").trim().trim_end_matches("@server");
                    if room_id.is_empty() || short_id.is_empty() {
                        return Err("Uso: /sala invitar <room_id> <usuario>".into());
                    }
                    match invitar_a_sala(room_id, client_id, short_id).await {
                        Ok(_)  => Ok(format!("📨 Invitación enviada a '{}' para '{}'.", short_id, room_id)),
                        Err(e) => Err(e),
                    }
                }
                "aceptar" => {
                    let room_id = args.trim();
                    if room_id.is_empty() { return Err("Uso: /sala aceptar <room_id>".into()); }
                    aceptar_invitacion(room_id, client_id).await
                }
                "msg" => {
                    let mut it = args.splitn(2, ' ');
                    let room_id = it.next().unwrap_or("").trim();
                    let texto   = it.next().unwrap_or("").trim();
                    if room_id.is_empty() || texto.is_empty() {
                        return Err("Uso: /sala msg <room_id> <texto>".into());
                    }
                    match enviar_a_sala(room_id, client_id, texto).await {
                        Ok(_)  => Ok(String::new()),
                        Err(e) => Err(e),
                    }
                }
                "salir" => {
                    let room_id = args.trim();
                    if room_id.is_empty() { return Err("Uso: /sala salir <room_id>".into()); }
                    salir_de_sala(room_id, client_id).await
                }
                "lista" | "" => {
                    let salas = mis_salas(client_id).await;
                    if salas.is_empty() {
                        return Ok("🏠 No perteneces a ninguna sala. Crea una con: /sala crear <nombre>".into());
                    }
                    Ok(widget_msg("salas", 1, json!({ "salas": salas })))
                }
                _ => Err(
                    "Uso: /sala [crear|invitar|aceptar|msg|salir|lista]".into()
                )
            }
        }

        _ => Err(format!("Comando de chat desconocido: '{}'.", cmd))
    }
}
