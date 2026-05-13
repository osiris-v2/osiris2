// src/social.rs
use uuid::Uuid;
use rand::{Rng, thread_rng};
use serde_json::json;
use tokio_tungstenite::tungstenite::Message;

use crate::config::{AI_SESSIONS, SHORT_ID_LEN, PRIVATE_ROOMS, ROOM_MAX_MEMBERS, PrivateRoom};

// ── SOCIAL: HELPERS ───────────────────────────────────────────────────────────

/// Genera un short_id hex único comprobando colisiones en AI_SESSIONS.
pub async fn generar_short_id_unico() -> String {
    for _ in 0..30 {
        let candidate: String = {
            let mut rng = thread_rng();
            (0..SHORT_ID_LEN).map(|_| format!("{:x}", rng.gen::<u8>() & 0xf)).collect()
        };
        let sessions = AI_SESSIONS.lock().await;
        if !sessions.values().any(|s| s.short_id == candidate) {
            return candidate;
        }
    }
    // Fallback extremo: UUID truncado
    uuid::Uuid::new_v4().to_string().replace('-', "")[..SHORT_ID_LEN].to_string()
}

/// Genera un room_id tipo "sala-XXXX" único.
pub async fn generar_room_id() -> String {
    for _ in 0..30 {
        let suffix: String = {
            let mut rng = thread_rng();
            (0..4).map(|_| format!("{:x}", rng.gen::<u8>() & 0xf)).collect()
        };
        let candidate = format!("sala-{}", suffix);
        let rooms = PRIVATE_ROOMS.lock().await;
        if !rooms.contains_key(&candidate) {
            return candidate;
        }
    }
    format!("sala-{}", Uuid::new_v4().to_string().replace('-', "")[..8].to_string())
}

/// Broadcast de presencia (join/leave) a todos los clientes conectados.
pub async fn broadcast_presence(event: &str, virtual_name: &str, total: usize) {
    let msg = json!({
        "type":    "presence",
        "event":   event,
        "id":      virtual_name,
        "clients": total
    }).to_string();
    broadcast_raw(msg, None).await;
}

/// Broadcast de un mensaje raw a todos los clientes.
/// exclude: UUID interno a omitir (None = enviar a todos).
pub async fn broadcast_raw(msg: String, exclude: Option<Uuid>) {
    let sessions = AI_SESSIONS.lock().await;
    for (uuid, session) in sessions.iter() {
        if let Some(ex) = exclude {
            if *uuid == ex { continue; }
        }
        let _ = session.chat_tx.send(Message::Text(msg.clone()));
    }
}

/// Enviar un mensaje privado a un cliente por su short_id.
pub async fn send_pm(from_vname: &str, to_short_id: &str, text: &str) -> Result<(), String> {
    let sessions = AI_SESSIONS.lock().await;
    match sessions.values().find(|s| s.short_id == to_short_id) {
        None => Err(format!("Usuario '{}@server' no encontrado o desconectado.", to_short_id)),
        Some(s) => {
            let pm = json!({
                "type": "pm",
                "from": from_vname,
                "to":   format!("{}@server", to_short_id),
                "text": text
            }).to_string();
            s.chat_tx.send(Message::Text(pm)).map_err(|_| "Error entregando PM.".to_string())
        }
    }
}

// ── SALAS PRIVADAS ────────────────────────────────────────────────────────────

/// Crea una nueva sala privada. El creador es automáticamente miembro.
/// Devuelve el room_id o un error.
pub async fn crear_sala(
    owner_uuid: Uuid,
    nombre: String,
) -> Result<String, String> {
    let room_id = generar_room_id().await;
    let mut rooms = PRIVATE_ROOMS.lock().await;
    let room = PrivateRoom::new(room_id.clone(), owner_uuid, nombre);
    rooms.insert(room_id.clone(), room);

    // Apuntar al owner en sus sesiones
    drop(rooms);
    let mut sessions = AI_SESSIONS.lock().await;
    if let Some(s) = sessions.get_mut(&owner_uuid) {
        if !s.rooms.contains(&room_id) {
            s.rooms.push(room_id.clone());
        }
    }

    Ok(room_id)
}

/// Invita a un usuario (por short_id) a una sala.
/// Solo el owner puede invitar.
pub async fn invitar_a_sala(
    room_id: &str,
    invitador_uuid: Uuid,
    invitado_short_id: &str,
) -> Result<(), String> {
    // Resolver UUID del invitado
    let (invitado_uuid, invitado_vname, invitador_vname) = {
        let sessions = AI_SESSIONS.lock().await;
        let invitado = sessions.values()
            .find(|s| s.short_id == invitado_short_id)
            .ok_or_else(|| format!("Usuario '{}@server' no encontrado.", invitado_short_id))?;
        let invitador = sessions.get(&invitador_uuid)
            .ok_or("Tu sesión no se encontró.")?;
        // Verificar que no es el mismo
        if invitado.short_id == invitador.short_id {
            return Err("No puedes invitarte a ti mismo.".into());
        }
        (
            // Necesitamos el UUID del invitado — buscarlo por short_id
            sessions.iter()
                .find(|(_, s)| s.short_id == invitado_short_id)
                .map(|(u, _)| *u)
                .ok_or("Error interno resolviendo UUID.")?,
            invitado.virtual_name(),
            invitador.virtual_name(),
        )
    };

    let mut rooms = PRIVATE_ROOMS.lock().await;
    let room = rooms.get_mut(room_id)
        .ok_or_else(|| format!("Sala '{}' no existe.", room_id))?;

    if room.members.len() >= ROOM_MAX_MEMBERS {
        return Err(format!("La sala '{}' está llena ({} miembros máx.).", room_id, ROOM_MAX_MEMBERS));
    }
    if room.members.contains(&invitado_uuid) {
        return Err(format!("'{}' ya es miembro de la sala.", invitado_short_id));
    }
    if room.pending.contains(&invitado_uuid) {
        return Err(format!("'{}' ya tiene una invitación pendiente.", invitado_short_id));
    }

    room.pending.push(invitado_uuid);
    let room_nombre = room.name.clone();
    drop(rooms);

    // Notificar al invitado
    let sessions = AI_SESSIONS.lock().await;
    if let Some(s) = sessions.get(&invitado_uuid) {
        let notif = json!({
            "type":    "room_invite",
            "room_id": room_id,
            "room_name": room_nombre,
            "from":    invitador_vname,
            "to":      invitado_vname,
            "text":    format!("📨 Invitación a sala '{}' ({}). Escribe /sala aceptar {} para entrar.", room_id, room_nombre, room_id)
        }).to_string();
        let _ = s.chat_tx.send(Message::Text(notif));
    }

    Ok(())
}

/// El invitado acepta la invitación y entra en la sala.
pub async fn aceptar_invitacion(
    room_id: &str,
    invitado_uuid: Uuid,
) -> Result<String, String> {
    let invitado_vname = {
        let sessions = AI_SESSIONS.lock().await;
        sessions.get(&invitado_uuid)
            .map(|s| s.virtual_name())
            .ok_or("Tu sesión no se encontró.")?
    };

    let mut rooms = PRIVATE_ROOMS.lock().await;
    let room = rooms.get_mut(room_id)
        .ok_or_else(|| format!("Sala '{}' no existe.", room_id))?;

    if !room.pending.contains(&invitado_uuid) {
        return Err(format!("No tienes invitación pendiente para la sala '{}'.", room_id));
    }
    if room.members.contains(&invitado_uuid) {
        return Err(format!("Ya eres miembro de la sala '{}'.", room_id));
    }

    room.pending.retain(|u| u != &invitado_uuid);
    room.members.push(invitado_uuid);
    let room_nombre = room.name.clone();
    let members = room.members.clone();
    drop(rooms);

    // Registrar en la sesión del usuario
    {
        let mut sessions = AI_SESSIONS.lock().await;
        if let Some(s) = sessions.get_mut(&invitado_uuid) {
            if !s.rooms.contains(&room_id.to_string()) {
                s.rooms.push(room_id.to_string());
            }
        }
    }

    // Notificar a todos los miembros de la sala
    notificar_sala(
        room_id,
        &members,
        &json!({
            "type":    "room_msg",
            "room_id": room_id,
            "from":    "sistema",
            "text":    format!("🚪 {} se ha unido a la sala '{}'.", invitado_vname, room_nombre)
        }).to_string(),
        None,
    ).await;

    Ok(format!("✅ Entraste en la sala '{}' ({}).", room_id, room_nombre))
}

/// Enviar un mensaje a una sala privada (solo miembros).
pub async fn enviar_a_sala(
    room_id: &str,
    remitente_uuid: Uuid,
    texto: &str,
) -> Result<(), String> {
    let (members, from_vname) = {
        let rooms = PRIVATE_ROOMS.lock().await;
        let room = rooms.get(room_id)
            .ok_or_else(|| format!("Sala '{}' no existe.", room_id))?;
        if !room.is_member(&remitente_uuid) {
            return Err(format!("No eres miembro de la sala '{}'.", room_id));
        }
        let sessions = AI_SESSIONS.lock().await;
        let vname = sessions.get(&remitente_uuid)
            .map(|s| s.virtual_name())
            .unwrap_or_default();
        (room.members.clone(), vname)
    };

    let msg = json!({
        "type":    "room_msg",
        "room_id": room_id,
        "from":    from_vname,
        "text":    texto
    }).to_string();

    notificar_sala(room_id, &members, &msg, None).await;
    Ok(())
}

/// Salir de una sala.
pub async fn salir_de_sala(
    room_id: &str,
    uuid: Uuid,
) -> Result<String, String> {
    let vname = {
        let sessions = AI_SESSIONS.lock().await;
        sessions.get(&uuid).map(|s| s.virtual_name()).unwrap_or_default()
    };

    let mut rooms = PRIVATE_ROOMS.lock().await;
    let room = rooms.get_mut(room_id)
        .ok_or_else(|| format!("Sala '{}' no existe.", room_id))?;

    if !room.is_member(&uuid) {
        return Err(format!("No eres miembro de la sala '{}'.", room_id));
    }

    room.members.retain(|u| u != &uuid);
    let members = room.members.clone();
    let room_nombre = room.name.clone();

    // Si queda vacía, eliminar la sala
    let sala_eliminada = members.is_empty();
    if sala_eliminada {
        rooms.remove(room_id);
    }
    drop(rooms);

    // Actualizar sesión
    {
        let mut sessions = AI_SESSIONS.lock().await;
        if let Some(s) = sessions.get_mut(&uuid) {
            s.rooms.retain(|r| r != room_id);
        }
    }

    if !sala_eliminada {
        notificar_sala(
            room_id,
            &members,
            &json!({
                "type":    "room_msg",
                "room_id": room_id,
                "from":    "sistema",
                "text":    format!("👋 {} ha salido de la sala '{}'.", vname, room_nombre)
            }).to_string(),
            None,
        ).await;
    }

    Ok(if sala_eliminada {
        format!("Saliste de '{}'. La sala fue eliminada (sin miembros).", room_id)
    } else {
        format!("Saliste de la sala '{}' ({}).", room_id, room_nombre)
    })
}

/// Helper: enviar un mensaje raw a todos los miembros de una sala.
pub async fn notificar_sala(
    _room_id: &str,
    members: &[Uuid],
    msg: &str,
    exclude: Option<Uuid>,
) {
    let sessions = AI_SESSIONS.lock().await;
    for uuid in members {
        if let Some(ex) = exclude {
            if *uuid == ex { continue; }
        }
        if let Some(s) = sessions.get(uuid) {
            let _ = s.chat_tx.send(Message::Text(msg.to_string()));
        }
    }
}

/// Devuelve info de las salas a las que pertenece un usuario.
pub async fn mis_salas(uuid: Uuid) -> Vec<serde_json::Value> {
    let rooms = PRIVATE_ROOMS.lock().await;
    let sessions = AI_SESSIONS.lock().await;
    rooms.values()
        .filter(|r| r.is_member(&uuid))
        .map(|r| {
            let miembros: Vec<String> = r.members.iter()
                .filter_map(|u| sessions.get(u).map(|s| s.virtual_name()))
                .collect();
            json!({
                "id":      r.id,
                "name":    r.name,
                "owner":   sessions.get(&r.owner).map(|s| s.virtual_name()).unwrap_or_default(),
                "members": miembros,
                "pending": r.pending.len()
            })
        })
        .collect()
}
