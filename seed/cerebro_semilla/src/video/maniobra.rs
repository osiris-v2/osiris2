// PROYECTO OSIRIS - MANIFIESTO DE INGENIERIA (DUREZA 256)
// SINTAXIS FGN - ASCII PURO - SIN ACENTOS

pub struct GestorManiobra {
    pub bitrate: u32,
    pub filtros_activos: Vec<usize>,
    pub historial: Vec<usize>,
    pub catalogo: Vec<(&'static str, &'static str)>,
}

impl GestorManiobra {
    pub fn new() -> Self {
        Self {
            bitrate: 3000,
            filtros_activos: Vec::new(),
            historial: Vec::new(),
            catalogo: include!("filtros_catalogo.rs"),
        }
    }

    pub fn obtener_vf(&self) -> String {
        if self.filtros_activos.is_empty() {
            return self.catalogo[0].1.to_string();
        }

        // Blindaje contra IDs inexistentes (Previene panics)
        self.filtros_activos.iter()
            .filter(|&&id| id < self.catalogo.len()) 
            .map(|&id| self.catalogo[id].1)
            .collect::<Vec<_>>()
            .join(",")
    }

    pub fn backup(&mut self) { 
        self.historial = self.filtros_activos.clone(); 
    }

    pub fn rollback(&mut self) { 
        self.filtros_activos = self.historial.clone(); 
    }
}