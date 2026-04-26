#include "acero_interfaz.h"
#include <stdio.h>

// Variable global que usaran el MAIN y el JS_BRIDGE
OsirisVideoDriver driver_activo = {0}; 

extern OsirisVideoDriver cargar_driver_gl_legacy();

// ESTA ES LA FUNCION QUE EL MAIN BUSCA
void inicializar_sistema_acero(void) {
    printf("[ACERO] Detectando Hardware...\n");
    
    // 1. Cargamos la estructura de funciones
    driver_activo = cargar_driver_gl_legacy();
    
    // 2. Ejecutamos la inicializacion real
    // Las dimensiones ya no se usan — el HUD calcula su propia posicion
    if (driver_activo.iniciar(0, 0)) {
        printf("[ACERO] Driver activo: %s\n", driver_activo.nombre_driver);
    } else {
        printf("[ERROR] Fallo critico al iniciar hardware.\n");
    }
}