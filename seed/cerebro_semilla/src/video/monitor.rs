use std::sync::Arc;
use tokio::sync::Mutex;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;
use crate::VideoState; // Importamos la estructura del main

// Control de activación por tecla 'f' (Global para el proyecto)
pub static MONITOR_F_ACTIVO: AtomicBool = AtomicBool::new(false);

pub struct MonitorConfig {
    pub input_actual: String,
    pub requiere_reinicio: bool,
}

impl MonitorConfig {
    pub fn new(default_url: String) -> Self {
        Self {
            input_actual: default_url,
            requiere_reinicio: false,
        }
    }
}

/// Función principal del vigilante que corre en su propio hilo
pub fn spawn_vigilante(config: Arc<Mutex<MonitorConfig>>, state: Arc<Mutex<VideoState>>) {
    let path_var = "/tmp/osiris_input";
    
    tokio::spawn(async move {
        loop {
            // Solo procesamos si el usuario pulsó 'f' en el teclado
            if MONITOR_F_ACTIVO.load(Ordering::Relaxed) {
                
                if let Ok(contenido) = std::fs::read_to_string(path_var) {
                    let nueva_url = contenido.trim().to_string();
                    
                    if !nueva_url.is_empty() {
                        let mut cfg = config.lock().await;
                        
                        // Si la URL del archivo es distinta a la que estamos reproduciendo
                        if cfg.input_actual != nueva_url {
                            cfg.input_actual = nueva_url;
                            cfg.requiere_reinicio = true; // Señal para que el Hilo 5 rompa el loop
                            
                            // ACCIÓN CRÍTICA: Accedemos al estado de video
                            let mut st = state.lock().await;
                            st.reset_time_pending = true; // El Hilo 5 verá esto y pondrá el tiempo a 0
                            st.gestor.filtros_activos.clear(); // Limpiamos filtros para el nuevo input
                            
                            println!("\n\x1b[32m[MONITOR] Nueva fuente detectada. Reiniciando a 0s...\x1b[0m");
                        }
                    }
                }
            }
            
            // Frecuencia de escaneo: 1 segundo es ideal para no saturar el disco
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    });
}