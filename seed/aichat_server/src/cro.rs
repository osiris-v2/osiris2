// src/cro.rs
//
// ── CRO PARSER ────────────────────────────────────────────────────────────────
//
// Módulo de post-procesado del stream de tokens de Ollama en tiempo real.
// "CRO" (Conversion Rate Optimization) aquí significa: aplicar reglas de
// transformación al texto generado por la IA antes de enviarlo al cliente.
//
// ESTADO: stub funcional — todas las transformaciones están desactivadas por
// defecto (modo passthrough). Añade tus reglas en `aplicar_reglas`.
//
// ARQUITECTURA:
//   CroParser::new(config)          → crea instancia con su configuración
//   parser.procesar_token(token)    → transforma un token individual
//   parser.flush()                  → devuelve tokens en buffer pendientes
//
// INTEGRACIÓN en ollama/mod.rs:
//   let mut cro = CroParser::new(CroConfig::default());
//   // … en el bucle de chunks:
//   let salida = cro.procesar_token(token);
//   if !salida.is_empty() { enviar_al_cliente(salida); }
//   // … al terminar:
//   let cola = cro.flush();
//   if !cola.is_empty() { enviar_al_cliente(cola); }
//
// ─────────────────────────────────────────────────────────────────────────────

/// Configuración del CRO Parser.
/// Se puede construir desde un fichero JSON o desde config.rs en el futuro.
#[derive(Debug, Clone)]
pub struct CroConfig {
    /// Activar/desactivar el parser por completo
    pub activo: bool,

    /// Reemplazos de texto plano: (patrón_exacto, sustitución)
    pub reemplazos: Vec<(String, String)>,

    /// Palabras a censurar/ocultar (reemplazadas por ***)
    pub palabras_prohibidas: Vec<String>,

    /// Si true, convierte URLs en formato Markdown: [url](url)
    pub linkify: bool,

    /// Prefijo que se añade al inicio de cada respuesta completa
    pub prefijo_respuesta: String,

    /// Sufijo que se añade al final de cada respuesta completa
    pub sufijo_respuesta: String,
}

impl Default for CroConfig {
    fn default() -> Self {
        Self {
            activo:              false,   // Passthrough por defecto
            reemplazos:          vec![],
            palabras_prohibidas: vec![],
            linkify:             false,
            prefijo_respuesta:   String::new(),
            sufijo_respuesta:    String::new(),
        }
    }
}

/// Parser CRO con buffer interno para tokens que cruzan límites de chunk.
pub struct CroParser {
    config:  CroConfig,
    /// Buffer para acumular contexto entre tokens (útil para reemplazos multi-token)
    buffer:  String,
    /// Indica si ya se emitió el prefijo de respuesta
    iniciado: bool,
}

impl CroParser {
    pub fn new(config: CroConfig) -> Self {
        Self {
            config,
            buffer:   String::new(),
            iniciado: false,
        }
    }

    /// Procesa un token del stream y devuelve el texto a enviar al cliente.
    /// Puede devolver cadena vacía si el token queda en buffer.
    pub fn procesar_token(&mut self, token: &str) -> String {
        if !self.config.activo {
            return token.to_string(); // Passthrough
        }

        let mut salida = String::new();

        // Emitir prefijo en el primer token real
        if !self.iniciado && !token.is_empty() {
            self.iniciado = true;
            if !self.config.prefijo_respuesta.is_empty() {
                salida.push_str(&self.config.prefijo_respuesta);
            }
        }

        self.buffer.push_str(token);

        // Aplicar transformaciones al buffer
        let procesado = self.aplicar_reglas(&self.buffer.clone());

        // Política de vaciado: emitir si el buffer es suficientemente largo
        // o si el token termina en puntuación (límite natural).
        let debe_emitir = token.ends_with(['.', '!', '?', '\n', ',', ';'])
            || self.buffer.len() > 512;

        if debe_emitir {
            salida.push_str(&procesado);
            self.buffer.clear();
        }

        salida
    }

    /// Vacía el buffer al final del stream. Siempre llamar al terminar.
    pub fn flush(&mut self) -> String {
        if !self.config.activo {
            return String::new();
        }
        let mut salida = String::new();
        if !self.buffer.is_empty() {
            salida.push_str(&self.aplicar_reglas(&self.buffer.clone()));
            self.buffer.clear();
        }
        if !self.config.sufijo_respuesta.is_empty() {
            salida.push_str(&self.config.sufijo_respuesta);
        }
        self.iniciado = false;
        salida
    }

    /// Aplica todas las reglas de transformación activas a un fragmento de texto.
    /// El orden de aplicación es: palabras_prohibidas → reemplazos → linkify.
    fn aplicar_reglas(&self, texto: &str) -> String {
        let mut resultado = texto.to_string();

        // 1. Censurar palabras prohibidas
        for palabra in &self.config.palabras_prohibidas {
            if !palabra.is_empty() {
                let asteriscos = "*".repeat(palabra.len());
                resultado = resultado.replace(palabra.as_str(), &asteriscos);
            }
        }

        // 2. Reemplazos exactos
        for (patron, sustitucion) in &self.config.reemplazos {
            if !patron.is_empty() {
                resultado = resultado.replace(patron.as_str(), sustitucion.as_str());
            }
        }

        // 3. Linkify (stub — activa para futuro uso)
        if self.config.linkify {
            resultado = linkify(&resultado);
        }

        resultado
    }
}

/// Convierte URLs planas en links Markdown.
/// Ejemplo: "visita https://ejemplo.com hoy" → "visita [https://ejemplo.com](https://ejemplo.com) hoy"
fn linkify(texto: &str) -> String {
    // Implementación mínima: detecta tokens que empiezan por http:// o https://
    texto.split_whitespace()
        .map(|word| {
            if word.starts_with("http://") || word.starts_with("https://") {
                format!("[{}]({})", word, word)
            } else {
                word.to_string()
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

// ── Tests unitarios ───────────────────────────────────────────────────────────
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn passthrough_cuando_desactivado() {
        let mut p = CroParser::new(CroConfig::default());
        assert_eq!(p.procesar_token("hola"), "hola");
        assert_eq!(p.flush(), "");
    }

    #[test]
    fn reemplaza_texto_simple() {
        let cfg = CroConfig {
            activo: true,
            reemplazos: vec![("GoyimAI".to_string(), "Asistente".to_string())],
            ..Default::default()
        };
        let mut p = CroParser::new(cfg);
        // Forzar vaciado con puntuación
        let out = p.procesar_token("Soy GoyimAI.");
        assert!(out.contains("Asistente"), "debería reemplazar 'GoyimAI'");
    }

    #[test]
    fn censura_palabras_prohibidas() {
        let cfg = CroConfig {
            activo: true,
            palabras_prohibidas: vec!["secreto".to_string()],
            ..Default::default()
        };
        let mut p = CroParser::new(cfg);
        let out = p.procesar_token("esto es secreto.");
        assert!(!out.contains("secreto"), "debería censurar la palabra");
    }

    #[test]
    fn linkify_urls() {
        assert_eq!(
            linkify("visita https://ejemplo.com hoy"),
            "visita [https://ejemplo.com](https://ejemplo.com) hoy"
        );
    }
}
