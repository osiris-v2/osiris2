/* cerebro/src/ai/trainer.rs */
use std::fs::File;
use std::io::Write;
use std::error::Error;
use std::time::{SystemTime, UNIX_EPOCH}; // Añadimos tiempo para romper el bucle

pub struct AnalisisIA {
    pub esfericidad: f32,
    pub disonancia: f32,
    pub requiere_colapso: bool,
}

pub struct FgnTrainer {
    pub dureza: u32,
}

impl FgnTrainer {
    pub fn new(dureza: u32) -> Self {
        Self { dureza }
    }

    pub async fn procesar_resonancia_osiris(&self, data: &[u8]) -> AnalisisIA {
        if data.is_empty() { 
            return AnalisisIA { esfericidad: 0.0, disonancia: 0.0, requiere_colapso: true }; 
        }

        // 1. SEMILLA DE ENTROPÍA (Para que dejen de ser iguales los resultados)
        // Usamos los nanosegundos actuales para que el offset cambie SIEMPRE
        let nano = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
        let semilla_caos = (nano % data.len() as u128) as usize;
        
        // 2. SALTO DE FASE DINÁMICO
        let offset = (semilla_caos + self.dureza as usize).min(data.len() - 1);
        
        // 3. MUESTREO DE ALTA VARIANZA
        // Usamos un step_by que dependa de la dureza para captar diferentes texturas
        let n_id: u64 = data.iter()
            .skip(offset / 4) // Empezamos en un punto variable
            .step_by(7) 
            .take(512)
            .map(|&b| b as u64)
            .sum();
        
        // 4. FACTORIZACIÓN (Sincronizada con fgn_math.c)
        let mut t_cantidad = 0;
        let mut temp = n_id;
        let mut divisor = 2;
        while temp > 1 && t_cantidad < 32 && divisor < 500 {
            if temp % divisor == 0 {
                while temp % divisor == 0 { temp /= divisor; }
                t_cantidad += 1;
            }
            divisor += 1;
        }

        // 5. RESULTADOS DINÁMICOS
        let esfericidad = if t_cantidad > 5 { 0.95 } else { t_cantidad as f32 * 0.15 };
        let curvatura = (n_id as f64).sin() as f32;
        let fase_esperada = (n_id as f64).cos() as f32;
        let disonancia = (curvatura - fase_esperada).abs();

        // Relajamos el colapso para que no sature el log si no es necesario
        let requiere_colapso = esfericidad < 0.10 && disonancia > 1.7;



        if requiere_colapso {
            let _ = self.forjar_modelo(data, "/tmp/disonancia.fgn");
        }

        AnalisisIA { esfericidad, disonancia, requiere_colapso }
    }

    pub fn forjar_modelo(&self, muestra: &[u8], nombre_salida: &str) -> Result<(), Box<dyn Error>> {
        let mut archivo = File::create(nombre_salida)?;
        let len = (self.dureza as usize).min(muestra.len());
        archivo.write_all(&muestra[..len])?;
        Ok(())
    }
}

pub async fn ejecutar_entrenamiento_temporal(data: &[u8]) -> AnalisisIA {
    let trainer = FgnTrainer::new(256);
    trainer.procesar_resonancia_osiris(data).await
}


