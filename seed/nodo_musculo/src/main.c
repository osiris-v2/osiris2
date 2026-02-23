#include <stdio.h>
#include <math.h>
#include "rb_csp.h"
#include "fgn_math.h"
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <signal.h>
#include <pthread.h>
#include "acero_interfaz.h"
#include "osiris_hw.h"
#include "demo/fgn_monitor.c"
#include "fgn_ai_core.h"  // <--- ESTE ES EL QUE FALTA
#include "osiris_hmac.h"    // Fase 2B: verificacion HMAC-SHA256



#define PORT_DATA 2000
#define PORT_CTRL 2001
#define CEREBRO_IP "127.0.0.1"

OsirisHardwareMap mi_hardware;
OsirisVideoDriver driver_activo;

// Declaraciones de los puntos de entrada del Bridge



/* --- ESTRUCTURA ESPEJO DE OsirisPacket (Rust) ---
 * Debe mantenerse sincronizada con protocol.rs
 * Total: 16 bytes exactos (verificar con static_assert)
 */
#pragma pack(push, 1)
typedef struct {
    uint8_t  version;       /* Byte 0  : Version del protocolo (esperamos 2) */
    uint8_t  seed_id;       /* Byte 1  : ID de semilla del signer             */
    uint8_t  opcode;        /* Byte 2  : Operacion a ejecutar                 */
    uint32_t signature;     /* Bytes 3-6  : Hash de integridad del payload    */
    uint32_t payload_size;  /* Bytes 7-10 : Tamanio del payload en bytes      */
    uint32_t frame_cnt;   /* Fase 2B: contador XOR */
    uint8_t  reservado;    /* Bytes 11-15: Relleno hasta 16 bytes            */
} OsirisHeader;
#pragma pack(pop)

/* Verificacion en tiempo de compilacion: si esto falla, hay desalineacion */
_Static_assert(sizeof(OsirisHeader) == 16, "OsirisHeader debe ser exactamente 16 bytes");

extern void inicializar_sistema_acero(void); 
extern void inicializar_motor_osiris(void);
extern void cerrar_motor_osiris(void);

FILE *display_pipe = NULL;
pid_t ffplay_pid = 0;
int video_paused = 0;
int sock_ctrl = 0;
RB_SafePtr uranio_safe;
OsirisHMACCtx hmac_ctx = { .activo = 0 }; /* Fase 2B: contexto HMAC de sesion */
pthread_mutex_t pipe_mutex = PTHREAD_MUTEX_INITIALIZER;

void update_ffplay_pid() {
    FILE *p = popen("pidof ffplay", "r");
    if (p) {
        if (fscanf(p, "%d", &ffplay_pid) != 1) ffplay_pid = 0;
        pclose(p);
    }
}

void close_display() {
    pthread_mutex_lock(&pipe_mutex);
    if (display_pipe) {
        printf("\x1b[31m[SISTEMA] Cerrando visor (Flush/Salto)...\n\x1b[0m");
        pclose(display_pipe);
        display_pipe = NULL;
        ffplay_pid = 0;
        video_paused = 0;
    }
    pthread_mutex_unlock(&pipe_mutex);
}

void* control_logic(void* arg) {
    (void)arg;

    /* ── FASE 2B: Handshake HMAC ────────────────────────────────────────
     * El Cerebro envia 36 bytes por canal CONTROL antes de empezar video:
     * [0..4)  = magic 0x4F534B59 ("OSKY")
     * [4..36) = session_key (32 bytes, CSPRNG del kernel)
     * Sin esta clave no es posible forjar signatures validos.
     * ─────────────────────────────────────────────────────────────────── */
    uint8_t hs_buf[OSIRIS_HANDSHAKE_SIZE];
    int hs_tr = 0;
    while (hs_tr < OSIRIS_HANDSHAKE_SIZE) {
        int n = read(sock_ctrl, hs_buf + hs_tr, OSIRIS_HANDSHAKE_SIZE - hs_tr);
        if (n <= 0) {
            printf("[HMAC] Error leyendo handshake — conexion perdida.\n");
            return NULL;
        }
        hs_tr += n;
    }
    osiris_hmac_recibir_handshake(hs_buf, &hmac_ctx);

    /* ── Bucle normal de comandos de control ─────────────────────────── */
    uint8_t cmd_header[16]; /* OsirisHeader completo de 16 bytes */
    while (read(sock_ctrl, cmd_header, 16) > 0) {
        uint8_t opcode = cmd_header[2]; /* Byte 2 = opcode en OsirisHeader */
        if (opcode == 10) { /* PAUSA */
            printf("\x1b[35m[CTRL] >>> RECIBIENDO FLUJO (PLAY/PAUSE)\n\x1b[0m");
            update_ffplay_pid();
            if (ffplay_pid > 0) {
                if (!video_paused) {
                    kill(ffplay_pid, SIGSTOP); video_paused = 1;
                    printf("\x1b[35m[CTRL] >>> SET IN PAUSE\n\x1b[0m");
                } else {
                    kill(ffplay_pid, SIGCONT); video_paused = 0;
                    printf("\x1b[35m[CTRL] >>> SET IN PLAY\n\x1b[0m");
                }
            }
        } else if (opcode == 15) { /* SKIP */
            printf("\x1b[35m[CTRL] >>> REINICIANDO FLUJO (SALTO)\n\x1b[0m");
        }
    }
    return NULL;
}


// Funcion auxiliar para mostrar el reporte de arranque
void imprimir_reporte_hw() {
    printf("\n\x1b[1;36m=== REPORTE DE SISTEMA (FGN) ===\x1b[0m\n");
    printf("CPU Nucleos:    %u\n", mi_hardware.cpu_nucleos);
    printf("RAM Total:      %lu MB\n", mi_hardware.ram_total_mb);
    printf("Pantalla:       %ux%u\n", mi_hardware.pantalla_ancho, mi_hardware.pantalla_alto);
    printf("Driver SDL2:    %s\n", mi_hardware.soporte_sdl2 ? "ACTIVO" : "NO DETECTADO");
    printf("Aceleracion 3D: %s\n", mi_hardware.soporte_opengl ? "DISPONIBLE" : "SOFTWARE");
    printf("Latencia Red:   %.2f ms\n", mi_hardware.latencia_ms);
    printf("\x1b[1;36m================================\x1b[0m\n\n");
}


int main() {
    // 1. Hardware y Video
    inicializar_sistema_acero(); 
    #include "demo/fgn_math.c"
    // 2. JS Engine (Mínima huella)
    inicializar_motor_osiris(); 

    setvbuf(stdout, NULL, _IONBF, 0);
    signal(SIGPIPE, SIG_IGN);

int sock_data = 0;
    struct sockaddr_in addr_data, addr_ctrl;
    pthread_t thread_ctrl;
    
    // DECLARACION AQUI (Para que op_stream y op_ia_update lo vean)
    FGN_AI_Context* core_ia = NULL;


// Si tengo mas de 4GB, uso buffer de 64MB, si no, de 1MB
uint32_t tam_inicio = (mi_hardware.ram_total_mb > 4096) ? 67108864 : 1048576;
uranio_safe = crear_bloque(tam_inicio, URANIO);


//    uranio_safe = crear_bloque(1048576, URANIO);

printf("RAM Total: %llu MB\n", (unsigned int long long)mi_hardware.ram_total_mb);

    // Llenamos la estructura con ceros por seguridad
    memset(&mi_hardware, 0, sizeof(OsirisHardwareMap));

// --- FASE 1: PROBE (AUTODIAGNOSTICO) ---
    printf("\x1b[1m[INIT] Iniciando secuencia de sondas...\x1b[0m\n");
    


// Correccion de formato de bits
//printf("RAM Total:      %lu MB\n", (unsigned long)mi_hardware.ram_total_mb);

    // Ejecutamos los drivers de deteccion
    probe_sistema_base(&mi_hardware);    // CPU y RAM
    probe_video_capacidades(&mi_hardware); // SDL2 y OpenGL
    probe_red_estado(&mi_hardware);      // Latencia

    // Mostramos que tenemos potencia para arrancar
    imprimir_reporte_hw();

/* --- INYECCION DE MASA (FGN) --- */
// Usamos 'resultado' que ya viene del include de fgn_math.c
FirmaGeo f_alfa, f_beta; 
// Reutilizamos la variable global 'resultado'
FirmaGeo base = FGN_Forjar(20260120, URANIO); 
FGN_SepararOnda(&base, &f_alfa, &f_beta); 
FGN_Colapsar(&f_alfa, &f_beta, &resultado); // <--- Aqui se llena la global

/* --- TEST DE EMERGENCIA --- */
printf("\n[DEBUG] Intentando ejecutar Monitor de Fase...\n");
fflush(stdout);

if (resultado.bloques.data != NULL) {
    FGN_Vigilar_GPU(&resultado);
    fflush(stdout);
} else {
    printf("[ERROR] La particula sigue vacia tras el colapso.\n");
    fflush(stdout);
}
/* -------------------------- */


    static void* dispatch_table[256] = { [0 ... 255] = &&unknown_op };
    dispatch_table[5] = &&op_rescale;
    dispatch_table[7] = &&op_stream;
    dispatch_table[9] = &&op_exit;
    dispatch_table[22] = &&op_ia_update; // <--- Opcode para recibir ADN
// dispatch_table[1] = &&op_handshake; // <--- FUTURO: Enviaremos mi_hardware aqui

    printf("\x1b[1m--- NODO OSIRIS ACTIVO ---\x1b[0m\n");

    while (1) {
        sock_data = socket(AF_INET, SOCK_STREAM, 0);
        sock_ctrl = socket(AF_INET, SOCK_STREAM, 0);
        
        addr_data.sin_family = addr_ctrl.sin_family = AF_INET;
        addr_data.sin_port = htons(PORT_DATA);
        addr_ctrl.sin_port = htons(PORT_CTRL);
        inet_pton(AF_INET, CEREBRO_IP, &addr_data.sin_addr);
        inet_pton(AF_INET, CEREBRO_IP, &addr_ctrl.sin_addr);

        if (connect(sock_data, (struct sockaddr *)&addr_data, sizeof(addr_data)) < 0 ||
            connect(sock_ctrl, (struct sockaddr *)&addr_ctrl, sizeof(addr_ctrl)) < 0) {
            close(sock_data); close(sock_ctrl);
            sleep(1); continue;
        }

        printf("\x1b[32m[OK] Doble vinculo con Cerebro.\n\x1b[0m");
        pthread_create(&thread_ctrl, NULL, control_logic, NULL);

   

next_op: ;

    OsirisHeader hdr;
    int tr = 0;

    /* Lectura robusta: reintentar hasta tener los 16 bytes completos */
    while (tr < (int)sizeof(OsirisHeader)) {
        int n = read(sock_data, (uint8_t*)&hdr + tr, sizeof(OsirisHeader) - tr);
        if (n <= 0) goto connection_lost;
        tr += n;
    }

    /* Validacion de version (en lugar del magic de 12 bytes identicos) */
    if (hdr.version != 2) {
        printf("[SYNC] Version desconocida (%u), descartando header.\n", hdr.version);
        goto next_op;
    }

    /* Ahora opcode y payload_size son correctos */
    uint8_t  opcode     = hdr.opcode;
    uint32_t chunk_size = hdr.payload_size;

    /* ── FASE 2B: Verificacion HMAC ─────────────────────────────────────
     * Opcodes con payload (VIDEO=7, IA_UPDATE=22): leer el payload primero,
     * verificar HMAC sobre header+payload, luego hacer dispatch.
     * Opcodes de control sin payload: verificar con payload vacio.
     * Si la verificacion falla: descartar silenciosamente (goto next_op).
     * ─────────────────────────────────────────────────────────────────── */
    if (chunk_size > 0) {
        /* Seguridad: rechazar payloads absurdamente grandes antes de alocar */
        if (chunk_size > 67108864u) { /* 64 MB maximo */
            printf("[SEC] payload_size=%u excede limite, descartando.\n", chunk_size);
            goto next_op;
        }
        /* Asegurar buffer Uranio suficiente */
        if (chunk_size > uranio_safe.size) {
            rb_rescale(&uranio_safe, chunk_size);
        }
        /* Leer payload completo en buffer Uranio */
        int tr_pre = 0;
        while (tr_pre < (int)chunk_size) {
            int n = read(sock_data,
                         (uint8_t*)uranio_safe.data + tr_pre,
                         chunk_size - tr_pre);
            if (n <= 0) goto connection_lost;
            tr_pre += n;
        }
        /* Verificar HMAC: header parcial + payload */
        if (!osiris_hmac_verificar((OsirisHeaderForHMAC*)&hdr,
                                   (uint8_t*)uranio_safe.data,
                                   chunk_size, &hmac_ctx)) {
            goto next_op; /* Firma invalida — paquete descartado */
        }
        /* HMAC verificado — descifrar payload con XOR */
        osiris_xor_payload(
            (uint8_t*)uranio_safe.data,
            chunk_size,
            hmac_ctx.session_key,
            hdr.frame_cnt
        );
    } else {
        /* Paquetes de control sin payload */
        if (!osiris_hmac_verificar((OsirisHeaderForHMAC*)&hdr,
                                   NULL, 0, &hmac_ctx)) {
            goto next_op;
        }
    }

    /* Dispatch a la tabla de operaciones */
    goto *dispatch_table[opcode];



//        uint8_t header[16]; // Aumentado a 16 bytes
//        if (read(sock_data, header, 16) <= 0) goto connection_lost;


    op_stream:
        {
            // El payload ya fue leido y verificado (HMAC-SHA256) antes del dispatch.
            // chunk_size viene de hdr.payload_size. 
            // uranio_safe.data contiene los bytes listos para renderizar.
            int tr = (int)chunk_size;

            // --- FASE IA: VALIDACION DE RESONANCIA ---
            // Solo si el Core IA ha sido inyectado con ADN desde Rust
            // Nota: El core_ia deberia inicializarse en el main o en op_ia_update
            
            if (core_ia && core_ia->modelo_data) {

// Pasamos la direccion de uranio_safe ya que es RB_SafePtr*
                float resonancia = fgn_ai_analizar(core_ia, &uranio_safe);
                if (resonancia < 0.25f) {
                    printf("\x1b[1;31m[!] ALERTA: RESONANCIA DE FASE BAJA (%.2f)\x1b[0m\n", resonancia);
                }
            }

            // 4. Renderizado via FFPLAY (Seccion Critica)
            pthread_mutex_lock(&pipe_mutex);
            
            if (!display_pipe && !video_paused && tr > 0) {
                printf("\x1b[34m[STREAM] Iniciando ffplay (Protocolo Osiris)...\n\x1b[0m");
                // Flags optimizados para minima latencia
                display_pipe = popen("ffplay -i pipe:0  -flags low_delay -probesize 32 -loglevel quiet -window_title ' FGN STREAM ' ", "w");
                update_ffplay_pid();
            }

            if (display_pipe && !video_paused) {
                if (fwrite(uranio_safe.data, 1, tr, display_pipe) < (size_t)tr) {
                    printf("\x1b[31m[!] Error de escritura en pipe. Reiniciando visor...\n\x1b[0m");
                    pclose(display_pipe); 
                    display_pipe = NULL;
                } else {
                    fflush(display_pipe);
                }
            }
            
            pthread_mutex_unlock(&pipe_mutex);
        }
        goto next_op;

    op_rescale:
        {
            uint32_t ns;
            if (read(sock_data, &ns, 4) <= 0) goto connection_lost;
            rb_rescale(&uranio_safe, ns);
            uint8_t dummy; read(sock_data, &dummy, 1);
        }
        goto next_op;

op_ia_update:
        {
            printf("\x1b[35m[IA] RECIBIENDO ADN (BLOQUE URANIO)...\n\x1b[0m");
            
            // 1. Creamos el contenedor con tu funcion real
            RB_SafePtr adn_safe = crear_bloque(1024, URANIO);
            
            // 2. Leemos directamente al data del SafePtr
            int tr = 0;
            while(tr < 1024) {
                int n = read(sock_data, (uint8_t*)adn_safe.data + tr, 1024 - tr);
                if (n <= 0) {
                    rb_liberar(&adn_safe); // Limpieza si falla
                    goto connection_lost;
                }
                tr += n;
            }

            if(!core_ia) core_ia = fgn_ai_init();

            // 3. Sincronizamos (fgn_ai_core.h debe aceptar RB_SafePtr*)
            fgn_ai_actualizar_modelo(core_ia, &adn_safe);
            
            printf("\x1b[32m[IA] RESONANCIA SINCRONIZADA (ID: %u)\n\x1b[0m", core_ia->id_modelo);
        }        
        goto next_op;


    unknown_op: goto next_op;
    op_exit: goto connection_lost;

connection_lost:
        printf("\x1b[31m[!] Conexion perdida o reset. Limpiando...\n\x1b[0m");
        
        // --- LIMPIEZA DE IA (Dureza 256) ---
        if (core_ia) {
            fgn_ai_destruir(core_ia);
            core_ia = NULL; // Reset de puntero para el proximo reintento
        }

        close_display();
        close(sock_data); close(sock_ctrl);
        pthread_cancel(thread_ctrl);
        sleep(1);
    } // Fin del while(1)
 
    cerrar_motor_osiris();
    return 0;
}