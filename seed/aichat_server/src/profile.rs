// src/profile.rs
//
// Persistencia de perfiles de usuario en disco.
// Cada perfil se guarda como <nombre_registro>.json en PROFILES_DIR.
// El directorio se crea automáticamente si no existe.
//
// API pública:
//   guardar_perfil(&PerfilUsuario) -> Result<(), String>
//   cargar_perfil(nombre_registro: &str) -> Option<PerfilUsuario>
//   listar_perfiles() -> Vec<String>        // nombres_registro disponibles
//   borrar_perfil(nombre_registro: &str) -> Result<(), String>

use std::fs;
use std::path::PathBuf;
use log::{info, warn};

use crate::config::PROFILES_DIR;
use crate::session::PerfilUsuario;

// ── Helpers internos ──────────────────────────────────────────────────────────

fn profiles_dir() -> PathBuf {
    PathBuf::from(PROFILES_DIR)
}

/// Asegura que el directorio de perfiles existe. Crea recursivamente si hace falta.
fn ensure_dir() -> Result<(), String> {
    let dir = profiles_dir();
    if !dir.exists() {
        fs::create_dir_all(&dir)
            .map_err(|e| format!("No se pudo crear el directorio de perfiles '{}': {}", dir.display(), e))?;
        info!("📁 Directorio de perfiles creado: {}", dir.display());
    }
    Ok(())
}

fn perfil_path(nombre_registro: &str) -> PathBuf {
    profiles_dir().join(format!("{}.json", nombre_registro))
}

// ── API pública ───────────────────────────────────────────────────────────────

/// Guarda el perfil en disco. Sobreescribe si ya existe.
/// Devuelve Err si no se puede escribir.
pub fn guardar_perfil(perfil: &PerfilUsuario) -> Result<(), String> {
    if perfil.nombre_registro.is_empty() {
        return Err("El perfil no tiene nombre_registro; no se puede guardar.".into());
    }
    ensure_dir()?;
    let json = serde_json::to_string_pretty(perfil)
        .map_err(|e| format!("Error serializando perfil: {}", e))?;
    let path = perfil_path(&perfil.nombre_registro);
    fs::write(&path, &json)
        .map_err(|e| format!("Error guardando perfil en '{}': {}", path.display(), e))?;
    info!("💾 Perfil guardado: {}", path.display());
    Ok(())
}

/// Carga un perfil desde disco por su nombre_registro.
/// Devuelve None si el fichero no existe o hay error de parseo.
pub fn cargar_perfil(nombre_registro: &str) -> Option<PerfilUsuario> {
    let path = perfil_path(nombre_registro);
    match fs::read_to_string(&path) {
        Err(_) => None,
        Ok(json) => {
            match serde_json::from_str::<PerfilUsuario>(&json) {
                Ok(p) => {
                    info!("📂 Perfil cargado: {}", path.display());
                    Some(p)
                }
                Err(e) => {
                    warn!("⚠️  Error parseando perfil '{}': {}", path.display(), e);
                    None
                }
            }
        }
    }
}

/// Devuelve la lista de nombres_registro disponibles en disco.
pub fn listar_perfiles() -> Vec<String> {
    let dir = profiles_dir();
    if !dir.exists() { return vec![]; }
    fs::read_dir(&dir)
        .ok()
        .map(|entries| {
            entries
                .filter_map(|e| e.ok())
                .filter_map(|e| {
                    let p = e.path();
                    if p.extension().and_then(|x| x.to_str()) == Some("json") {
                        p.file_stem().and_then(|s| s.to_str()).map(|s| s.to_string())
                    } else {
                        None
                    }
                })
                .collect()
        })
        .unwrap_or_default()
}

/// Borra el fichero de un perfil. Devuelve Err si no existe o no se puede borrar.
pub fn borrar_perfil(nombre_registro: &str) -> Result<(), String> {
    let path = perfil_path(nombre_registro);
    if !path.exists() {
        return Err(format!("No existe el perfil '{}'.", nombre_registro));
    }
    fs::remove_file(&path)
        .map_err(|e| format!("Error borrando perfil '{}': {}", path.display(), e))?;
    info!("🗑️  Perfil borrado: {}", path.display());
    Ok(())
}
