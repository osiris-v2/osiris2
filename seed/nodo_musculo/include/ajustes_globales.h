#ifndef AJUSTES_GLOBALES_H
#define AJUSTES_GLOBALES_H

/* --- 1. CONFIGURACION DE MEMORIA SEGURA (URANIO) --- */
// Activa el modo paranoico: verifica limites en CADA lectura/escritura
#define URANIO_MODO_ESTRICTO  1
// Tamanio maximo de bloque seguro (evita allocs gigantes maliciosos)
#define URANIO_MAX_BLOQUE     (1024 * 1024 * 64) // 64 MB

/* --- 2. MODULOS DE HARDWARE --- */
// Comenta para desactivar si compilas para sistemas minimos
#define USAR_DRIVER_SDL2      1
#define USAR_DRIVER_X11       1
#define USAR_DRIVER_OPENGL    1
#define USAR_PROBE_RED        1

/* --- 3. PARAMETROS DE RED --- */
#define PUERTO_INGESTA        2000
#define PUERTO_CONTROL        2001
#define TIMEOUT_CONEXION_MS   5000

/* --- 4. COMPILADOR DE MACROS --- */
// Version del bytecode que este nodo entiende
#define VERSION_BYTECODE      0x01
// Tamanio del buffer de instrucciones entrantes
#define BUFFER_MACROS_SIZE    4096

#endif // AJUSTES_GLOBALES_H