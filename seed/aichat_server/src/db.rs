// src/db.rs
//
// ── CAPA DE BASE DE DATOS ─────────────────────────────────────────────────────
//
// SQLite embebido (rusqlite + bundled).
// Una sola conexión protegida por Mutex estándar — las operaciones son
// síncronas pero rápidas; se llaman desde tareas Tokio con spawn_blocking.
//
// ESQUEMA:
//   usuarios  — credenciales y metadatos de cuenta
//   perfiles  — datos de perfil y flags de visibilidad pública
//
// API pública (todas síncronas, llamar con spawn_blocking):
//   DB::open(path)           → Result<DB>
//   db.crear_usuario(...)    → Result<i64, DbError>
//   db.verificar_login(...)  → Result<UsuarioRow, DbError>
//   db.obtener_perfil(uid)   → Option<PerfilRow>
//   db.guardar_perfil(...)   → Result<()>
//   db.obtener_cuenta(uid)   → Option<CuentaRow>
//   db.username_existe(name) → bool
//   db.email_existe(email)   → bool
//   db.actualizar_ultimo_login(uid)

use rusqlite::{Connection, params, Result as SqlResult};
use std::sync::{Arc, Mutex};
use chrono::Local;
use log::{info, error};

// ── ERRORES ───────────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum DbError {
    UsernameTaken,
    EmailTaken,
    InvalidCredentials,
    NotFound,
    Sql(rusqlite::Error),
    Bcrypt(bcrypt::BcryptError),
}

impl std::fmt::Display for DbError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DbError::UsernameTaken      => write!(f, "El nombre de usuario ya existe."),
            DbError::EmailTaken         => write!(f, "El email ya está registrado."),
            DbError::InvalidCredentials => write!(f, "Usuario o contraseña incorrectos."),
            DbError::NotFound           => write!(f, "No encontrado."),
            DbError::Sql(e)             => write!(f, "Error SQL: {}", e),
            DbError::Bcrypt(e)          => write!(f, "Error de cifrado: {}", e),
        }
    }
}

impl From<rusqlite::Error> for DbError {
    fn from(e: rusqlite::Error) -> Self { DbError::Sql(e) }
}

impl From<bcrypt::BcryptError> for DbError {
    fn from(e: bcrypt::BcryptError) -> Self { DbError::Bcrypt(e) }
}

// ── FILAS DE RETORNO ──────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct UsuarioRow {
    pub id:         i64,
    pub username:   String,
    #[allow(dead_code)]
    pub email:      String,       // privado — usado en /cuenta
    #[allow(dead_code)]
    pub created_at: String,
    pub last_login: String,
}

#[derive(Debug, Clone)]
pub struct PerfilRow {
    pub user_id:     i64,
    pub tipo:        String,
    pub nombre:      String,
    pub descripcion: String,
    pub sector:      String,
    pub tono:        String,
    pub pub_nombre:  bool,
    pub pub_tipo:    bool,
    pub pub_desc:    bool,
}

impl PerfilRow {
    /// Lo que un tercero puede ver según los flags de visibilidad.
    /// Usado en /who y consultas de perfil público.
    #[allow(dead_code)]
    pub fn vista_publica(&self) -> serde_json::Value {
        use serde_json::json;
        json!({
            "nombre":      if self.pub_nombre { &self.nombre }      else { "" },
            "tipo":        if self.pub_tipo   { &self.tipo }         else { "" },
            "descripcion": if self.pub_desc   { &self.descripcion }  else { "" },
        })
    }
}

#[derive(Debug, Clone)]
pub struct CuentaRow {
    #[allow(dead_code)]
    pub id:         i64,
    pub username:   String,
    pub email:      String,
    pub created_at: String,
    pub last_login: String,
    pub perfil:     Option<PerfilRow>,
}

// ── HANDLE DE BASE DE DATOS ───────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct Db {
    conn: Arc<Mutex<Connection>>,
}

impl Db {
    /// Abre (o crea) la base de datos en `path` y aplica el esquema.
    pub fn open(path: &str) -> Result<Self, DbError> {
        // Crear el directorio padre si no existe
        if let Some(parent) = std::path::Path::new(path).parent() {
            if !parent.exists() {
                std::fs::create_dir_all(parent).ok();
            }
        }

        let conn = Connection::open(path)?;

        // WAL mode: mejor rendimiento con lecturas concurrentes
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;

        // Esquema
        conn.execute_batch(r#"
            CREATE TABLE IF NOT EXISTS usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                created_at    TEXT    NOT NULL,
                last_login    TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS perfiles (
                user_id      INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
                tipo         TEXT    NOT NULL DEFAULT '',
                nombre       TEXT    NOT NULL DEFAULT '',
                descripcion  TEXT    NOT NULL DEFAULT '',
                sector       TEXT    NOT NULL DEFAULT '',
                tono         TEXT    NOT NULL DEFAULT '',
                pub_nombre   INTEGER NOT NULL DEFAULT 1,
                pub_tipo     INTEGER NOT NULL DEFAULT 1,
                pub_desc     INTEGER NOT NULL DEFAULT 0
            );
        "#)?;

        info!("💾 Base de datos abierta: {}", path);
        Ok(Self { conn: Arc::new(Mutex::new(conn)) })
    }

    // ── USUARIOS ──────────────────────────────────────────────────────────────

    /// Registra un nuevo usuario. Devuelve su id.
    /// Errores: UsernameTaken, EmailTaken.
    pub fn crear_usuario(
        &self,
        username: &str,
        email: &str,
        password: &str,
    ) -> Result<i64, DbError> {
        // Validaciones previas (más informativas que el UNIQUE de SQLite)
        if self.username_existe(username) { return Err(DbError::UsernameTaken); }
        if self.email_existe(email)       { return Err(DbError::EmailTaken); }

        let hash = bcrypt::hash(password, bcrypt::DEFAULT_COST)?;
        let ahora = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO usuarios (username, password_hash, email, created_at, last_login)
             VALUES (?1, ?2, ?3, ?4, '')",
            params![username.trim(), hash, email.trim().to_lowercase(), ahora],
        )?;
        let id = conn.last_insert_rowid();
        info!("👤 Nuevo usuario registrado: @{} (id={})", username, id);
        Ok(id)
    }

    /// Verifica credenciales. Devuelve UsuarioRow si son correctas.
    pub fn verificar_login(
        &self,
        username: &str,
        password: &str,
    ) -> Result<UsuarioRow, DbError> {
        let conn = self.conn.lock().unwrap();
        let result: SqlResult<(i64, String, String, String, String)> = conn.query_row(
            "SELECT id, password_hash, email, created_at, last_login
             FROM usuarios WHERE username = ?1 COLLATE NOCASE",
            params![username.trim()],
            |row| Ok((
                row.get(0)?,
                row.get(1)?,
                row.get(2)?,
                row.get(3)?,
                row.get(4)?,
            )),
        );

        match result {
            Err(rusqlite::Error::QueryReturnedNoRows) => Err(DbError::InvalidCredentials),
            Err(e) => Err(DbError::Sql(e)),
            Ok((id, hash, email, created_at, last_login)) => {
                let ok = bcrypt::verify(password, &hash)
                    .map_err(DbError::Bcrypt)?;
                if !ok { return Err(DbError::InvalidCredentials); }
                Ok(UsuarioRow {
                    id,
                    username: username.trim().to_string(),
                    email,
                    created_at,
                    last_login,
                })
            }
        }
    }

    /// Actualiza la fecha de último login.
    pub fn actualizar_ultimo_login(&self, user_id: i64) {
        let ahora = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
        let conn = self.conn.lock().unwrap();
        if let Err(e) = conn.execute(
            "UPDATE usuarios SET last_login = ?1 WHERE id = ?2",
            params![ahora, user_id],
        ) {
            error!("Error actualizando last_login: {}", e);
        }
    }

    /// Comprueba si un username ya existe (case-insensitive).
    pub fn username_existe(&self, username: &str) -> bool {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT COUNT(*) FROM usuarios WHERE username = ?1 COLLATE NOCASE",
            params![username.trim()],
            |row| row.get::<_, i64>(0),
        ).unwrap_or(0) > 0
    }

    /// Comprueba si un email ya existe.
    pub fn email_existe(&self, email: &str) -> bool {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT COUNT(*) FROM usuarios WHERE email = ?1 COLLATE NOCASE",
            params![email.trim().to_lowercase().as_str()],
            |row| row.get::<_, i64>(0),
        ).unwrap_or(0) > 0
    }

    // ── PERFILES ──────────────────────────────────────────────────────────────

    /// Obtiene el perfil de un usuario por su user_id.
    pub fn obtener_perfil(&self, user_id: i64) -> Option<PerfilRow> {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT user_id, tipo, nombre, descripcion, sector, tono,
                    pub_nombre, pub_tipo, pub_desc
             FROM perfiles WHERE user_id = ?1",
            params![user_id],
            |row| Ok(PerfilRow {
                user_id:     row.get(0)?,
                tipo:        row.get(1)?,
                nombre:      row.get(2)?,
                descripcion: row.get(3)?,
                sector:      row.get(4)?,
                tono:        row.get(5)?,
                pub_nombre:  row.get::<_, i32>(6)? != 0,
                pub_tipo:    row.get::<_, i32>(7)? != 0,
                pub_desc:    row.get::<_, i32>(8)? != 0,
            }),
        ).ok()
    }

    /// Guarda o actualiza el perfil de un usuario (UPSERT).
    pub fn guardar_perfil(&self, p: &PerfilRow) -> Result<(), DbError> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO perfiles
                (user_id, tipo, nombre, descripcion, sector, tono, pub_nombre, pub_tipo, pub_desc)
             VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9)
             ON CONFLICT(user_id) DO UPDATE SET
                tipo        = excluded.tipo,
                nombre      = excluded.nombre,
                descripcion = excluded.descripcion,
                sector      = excluded.sector,
                tono        = excluded.tono,
                pub_nombre  = excluded.pub_nombre,
                pub_tipo    = excluded.pub_tipo,
                pub_desc    = excluded.pub_desc",
            params![
                p.user_id,
                p.tipo, p.nombre, p.descripcion, p.sector, p.tono,
                p.pub_nombre as i32,
                p.pub_tipo   as i32,
                p.pub_desc   as i32,
            ],
        )?;
        Ok(())
    }

    /// Actualiza un flag de visibilidad pública.
    pub fn set_visibilidad(
        &self,
        user_id: i64,
        campo: &str,   // "nombre" | "tipo" | "desc"
        valor: bool,
    ) -> Result<(), DbError> {
        let col = match campo {
            "nombre" => "pub_nombre",
            "tipo"   => "pub_tipo",
            "desc"   => "pub_desc",
            _        => return Err(DbError::NotFound),
        };
        // Construimos la query de forma segura (col viene de match, no del usuario)
        let sql = format!("UPDATE perfiles SET {} = ?1 WHERE user_id = ?2", col);
        let conn = self.conn.lock().unwrap();
        conn.execute(&sql, params![valor as i32, user_id])?;
        Ok(())
    }

    // ── CUENTA ────────────────────────────────────────────────────────────────

    /// Datos completos de la cuenta (uso privado del propietario).
    pub fn obtener_cuenta(&self, user_id: i64) -> Option<CuentaRow> {
        let conn = self.conn.lock().unwrap();
        let row: SqlResult<(String, String, String, String)> = conn.query_row(
            "SELECT username, email, created_at, last_login FROM usuarios WHERE id = ?1",
            params![user_id],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?)),
        );
        match row {
            Err(_) => None,
            Ok((username, email, created_at, last_login)) => {
                drop(conn); // liberar el lock antes de la segunda consulta
                let perfil = self.obtener_perfil(user_id);
                Some(CuentaRow { id: user_id, username, email, created_at, last_login, perfil })
            }
        }
    }

    /// Busca un usuario por username y devuelve su PerfilRow público.
    /// Para que otros usuarios puedan ver el perfil público de alguien.
    #[allow(dead_code)]
    pub fn perfil_publico_por_username(&self, username: &str) -> Option<PerfilRow> {
        let conn = self.conn.lock().unwrap();
        let uid: SqlResult<i64> = conn.query_row(
            "SELECT id FROM usuarios WHERE username = ?1 COLLATE NOCASE",
            params![username.trim()],
            |r| r.get(0),
        );
        drop(conn);
        uid.ok().and_then(|id| self.obtener_perfil(id))
    }
}
