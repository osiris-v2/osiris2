#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <signal.h>
#include <pthread.h>
#include "mem/rb_csp.h"
#include "../include/osiris_hw.h"

#define PORT_DATA 2000
#define PORT_CTRL 2001
#define CEREBRO_IP "127.0.0.1"

OsirisHardwareMap mi_hardware;

FILE *display_pipe = NULL;
pid_t ffplay_pid = 0;
int video_paused = 0;
int sock_ctrl = 0;
RB_SafePtr uranio_safe;
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
    uint8_t cmd_header[12];
    while(read(sock_ctrl, cmd_header, 12) > 0) {
        uint8_t opcode = cmd_header[0];
        if (opcode == 10) { // PAUSA
            update_ffplay_pid();
            if (ffplay_pid > 0) {
                if (!video_paused) { kill(ffplay_pid, SIGSTOP); video_paused = 1; }
                else { kill(ffplay_pid, SIGCONT); video_paused = 0; }
            }
        } 
        else if (opcode == 15) { // SALTO SIN CERRAR
            printf("\x1b[35m[CTRL] >>> REINICIANDO FLUJO (SALTO)\n\x1b[0m");
            // No cerramos el pipe, solo esperamos el nuevo flujo
            // El truco está en que Rust matará su FFmpeg y mandará datos nuevos
        }
    }
    return NULL;
}


// Funcion auxiliar para mostrar el reporte de arranque
void imprimir_reporte_hw() {
    printf("\n\x1b[1;36m=== REPORTE DE SISTEMA (FGN) ===\x1b[0m\n");
    printf("CPU Nucleos:    %u\n", mi_hardware.cpu_nucleos);
    printf("RAM Total:      %llu MB\n", mi_hardware.ram_total_mb);
    printf("Pantalla:       %ux%u\n", mi_hardware.pantalla_ancho, mi_hardware.pantalla_alto);
    printf("Driver SDL2:    %s\n", mi_hardware.soporte_sdl2 ? "ACTIVO" : "NO DETECTADO");
    printf("Aceleracion 3D: %s\n", mi_hardware.soporte_opengl ? "DISPONIBLE" : "SOFTWARE");
    printf("Latencia Red:   %.2f ms\n", mi_hardware.latencia_ms);
    printf("\x1b[1;36m================================\x1b[0m\n\n");
}


int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    signal(SIGPIPE, SIG_IGN);

    int sock_data = 0;
    struct sockaddr_in addr_data, addr_ctrl;
    pthread_t thread_ctrl;


// Si tengo mas de 4GB, uso buffer de 64MB, si no, de 1MB
uint32_t tam_inicio = (mi_hardware.ram_total_mb > 4096) ? 67108864 : 1048576;
uranio_safe = crear_bloque(tam_inicio, URANIO);


//    uranio_safe = crear_bloque(1048576, URANIO);

printf("RAM Total: %lu MB\n", (unsigned long)mi_hardware.ram_total_mb);

// --- FASE 1: PROBE (AUTODIAGNOSTICO) ---
    printf("\x1b[1m[INIT] Iniciando secuencia de sondas...\x1b[0m\n");
    
    // Llenamos la estructura con ceros por seguridad
    memset(&mi_hardware, 0, sizeof(OsirisHardwareMap));

    // Ejecutamos los drivers de deteccion
    probe_sistema_base(&mi_hardware);    // CPU y RAM
    probe_video_capacidades(&mi_hardware); // SDL2 y OpenGL
    probe_red_estado(&mi_hardware);      // Latencia

    // Mostramos que tenemos potencia para arrancar
    imprimir_reporte_hw();




    static void* dispatch_table[256] = { [0 ... 255] = &&unknown_op };
    dispatch_table[5] = &&op_rescale;
    dispatch_table[7] = &&op_stream;
    dispatch_table[9] = &&op_exit;
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
        uint8_t header[12];
        if (read(sock_data, header, 12) <= 0) goto connection_lost;
        goto *dispatch_table[header[0]];

    op_rescale:
        {
            uint32_t ns;
            if (read(sock_data, &ns, 4) <= 0) goto connection_lost;
            rb_rescale(&uranio_safe, ns);
            uint8_t dummy; read(sock_data, &dummy, 1);
        }
        goto next_op;

    op_stream:
        {
            uint32_t chunk_size;
            if (read(sock_data, &chunk_size, 4) <= 0) goto connection_lost;
            
            if (chunk_size > uranio_safe.size) {
                rb_rescale(&uranio_safe, chunk_size);
            }

            int tr = 0;
            while(tr < (int)chunk_size) {
                int n = read(sock_data, (uint8_t*)uranio_safe.data + tr, chunk_size - tr);
                if (n <= 0) goto connection_lost;
                tr += n;
            }

            pthread_mutex_lock(&pipe_mutex);
            // APERTURA DINÁMICA: Si no hay visor, se abre con los nuevos datos
            if (!display_pipe && !video_paused && tr > 0) {
                printf("\x1b[34m[STREAM] Iniciando ffplay...\n\x1b[0m");
                display_pipe = popen("ffplay -i pipe:0 -fflags nobuffer -flags low_delay -probesize 32 -loglevel quiet", "w");
                update_ffplay_pid();
            }

          
          if (display_pipe && !video_paused) {
        // Escribimos directamente. Si FFmpeg ha cambiado el stream, 
        // ffplay intentará resincronizar solo.
        if (fwrite(uranio_safe.data, 1, tr, display_pipe) < (size_t)tr) {
            // Solo si falla de verdad cerramos
            pclose(display_pipe); display_pipe = NULL;
        } else {
            fflush(display_pipe);
        }
      }
            pthread_mutex_unlock(&pipe_mutex);
        }
        goto next_op;

    unknown_op: goto next_op;
    op_exit: goto connection_lost;

    connection_lost:
        printf("\x1b[31m[!] Conexion perdida o reset. Limpiando...\n\x1b[0m");
        close_display();
        close(sock_data); close(sock_ctrl);
        pthread_cancel(thread_ctrl);
        sleep(1);
    }
    return 0;
}