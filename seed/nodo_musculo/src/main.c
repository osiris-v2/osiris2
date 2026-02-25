#include <stdio.h>
#include <math.h>
#include "rb_csp.h"
#include "fgn_math.h"
#include <stdlib.h>
#include <string.h>
#include <stdatomic.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <signal.h>
#include <pthread.h>
#include <time.h>
#include "acero_interfaz.h"
#include "osiris_hw.h"
#include "fgn_runtime.h"      /* Fase 3B: ventanas FGN, cola MPSC, h_table */
#include "demo/fgn_monitor.c"
#include "fgn_ai_core.h"
#include "osiris_hmac.h"      /* Fase 2B: HMAC-SHA256 + XOR               */
#include "quickjs.h"          /* Fase 3A: motor QuickJS embebido           */
#include <SDL2/SDL.h>         /* Fase 3A: ventanas nativas                 */

/* sdl_core.c: solo probe_video — el mirror ya no se usa en el path principal */
extern void probe_video_capacidades(OsirisHardwareMap *map);

#define PORT_DATA  2000
#define PORT_CTRL  2001
#define CEREBRO_IP "127.0.0.1"

OsirisHardwareMap mi_hardware;
OsirisVideoDriver driver_activo;

/* ── HEADER OSIRIS 16 bytes (sincronizado con protocol.rs Fase 2B) ───────── */
#pragma pack(push, 1)
typedef struct {
    uint8_t  version;
    uint8_t  seed_id;
    uint8_t  opcode;
    uint32_t signature;
    uint32_t payload_size;
    uint32_t frame_cnt;   /* Fase 2B: nonce XOR keystream */
    uint8_t  reservado;
} OsirisHeader;
#pragma pack(pop)
_Static_assert(sizeof(OsirisHeader) == 16, "OsirisHeader debe ser exactamente 16 bytes");

/* ── STRUCTS DE PAYLOAD FASE 3A ──────────────────────────────────────────── */
#pragma pack(push, 1)

/* OP_WIN_CREATE (30) — 70 bytes */
typedef struct {
    uint16_t ancho;
    uint16_t alto;
    uint8_t  titulo[64];
    uint16_t flags;       /* 0=normal, 1=fullscreen, 2=borderless */
} WinCreateParams;

/* OP_OVERLAY_TEXT (35) — 136 bytes */
typedef struct {
    int16_t  x;
    int16_t  y;
    uint8_t  color[4];
    uint8_t  size;
    uint8_t  texto[128];
    uint8_t  pad;
} OverlayParams;

/* OP_ACK (50) — 2 bytes, Nodo→Cerebro */
typedef struct {
    uint8_t opcode_origen;
    uint8_t resultado;    /* 0=OK  1=ERROR  2=PENDIENTE */
} AckPayload;

#pragma pack(pop)

#define ACK_OK      0
#define ACK_ERROR   1
#define ACK_PENDING 2

extern void inicializar_sistema_acero(void);
extern void inicializar_motor_osiris(void);
extern void cerrar_motor_osiris(void);
extern JSContext *obtener_contexto_osiris(void);
extern void manejar_comando_fgn_js(const char *script);

/* ── V-GHOST HUD: metricas declaradas en fgn_runtime.h, definidas en osiris_windows.c */
/* vg_bytes_total, vg_frames, vg_ultimo_opcode, vg_conectado ya visibles via fgn_runtime.h */

/* Solicita refresco del HUD al SDL_THREAD via la cola MPSC.
 * Seguro llamar desde cualquier hilo — no toca SDL directamente. */
static inline void vg_hud_request_refresh(void) {
    fgn_hud_render();
}

FILE    *display_pipe = NULL;
pid_t    ffplay_pid   = 0;
int      video_paused = 0;
int      sock_ctrl    = 0;
RB_SafePtr uranio_safe;
OsirisHMACCtx hmac_ctx = { .activo = 0 };
pthread_mutex_t pipe_mutex = PTHREAD_MUTEX_INITIALIZER;


/* ═══════════════════════════════════════════════════════════════════════════
 * COLA SDL, REGISTRO DE VENTANAS FGN y H_TABLE
 *
 * Movidos a osiris_windows.c + fgn_runtime.h (Fase 3B).
 * main.c consume la API publica:
 *   fgn_windows_iniciar()  — arranca SDL_THREAD, FLUSH_THREAD, crea HUD
 *   fgn_win_crear()        — encola SDL_CMD_WIN_CREAR
 *   fgn_win_cerrar()       — encola SDL_CMD_WIN_CERRAR
 *   fgn_win_overlay()      — encola SDL_CMD_OVERLAY_TXT
 *   fgn_hud_render()       — encola SDL_CMD_RENDER_HUD
 *   sdl_cmd_push()         — acceso directo a la cola para handlers complejos
 * ═══════════════════════════════════════════════════════════════════════════ */


/* ── HELPERS GENERALES ───────────────────────────────────────────────────── */
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
        printf("\x1b[31m[SISTEMA] Cerrando visor...\n\x1b[0m");
        /* SIGTERM al proceso ffplay antes de cerrar la pipe.
         * Si usamos pclose() sin matar el proceso primero, espera
         * a que ffplay termine — deadlock. fclose() cierra el fd
         * inmediatamente sin esperar al proceso hijo. */
        if (ffplay_pid > 0) { kill(ffplay_pid, SIGTERM); ffplay_pid = 0; }
        fclose(display_pipe);
        display_pipe = NULL;
        video_paused = 0;
    }
    pthread_mutex_unlock(&pipe_mutex);
}

/* ── HELPER: ACK al Cerebro por canal CONTROL ────────────────────────────── */
static inline void nodo_send_ack(uint8_t opcode_origen, uint8_t resultado) {
    if (sock_ctrl <= 0) return;
    uint8_t pkt[18] = {0};
    pkt[0] = 2;   /* version */
    pkt[1] = 1;   /* seed_id */
    pkt[2] = 50;  /* OP_ACK  */
    pkt[7] = 2;   /* payload_size = 2 (LE) */
    pkt[16] = opcode_origen;
    pkt[17] = resultado;
    write(sock_ctrl, pkt, 18);
}


/* ── HILO DE CONTROL (handshake HMAC + pause/skip) ───────────────────────── */
void* control_logic(void* arg) {
    (void)arg;

    /* Handshake: 4 bytes magic OSKY + 32 bytes session_key */
    uint8_t hs_buf[OSIRIS_HANDSHAKE_SIZE];
    int hs_tr = 0;
    while (hs_tr < OSIRIS_HANDSHAKE_SIZE) {
        int n = read(sock_ctrl, hs_buf + hs_tr, OSIRIS_HANDSHAKE_SIZE - hs_tr);
        if (n <= 0) { printf("[HMAC] Error en handshake.\n"); return NULL; }
        hs_tr += n;
    }
    osiris_hmac_recibir_handshake(hs_buf, &hmac_ctx);

    /* Dispatch table para control — computed goto */
    static void* ctrl_table[256] = { [0 ... 255] = &&ctrl_unknown };
    ctrl_table[10] = &&ctrl_pause;
    ctrl_table[15] = &&ctrl_skip;
    uint8_t cmd_header[16];

ctrl_next: ;
    { int n = read(sock_ctrl, cmd_header, 16); if (n <= 0) return NULL; }
    goto *ctrl_table[cmd_header[2]];
ctrl_pause:
    video_paused = !video_paused;
    if (ffplay_pid > 0) kill(ffplay_pid, video_paused ? SIGSTOP : SIGCONT);
    goto ctrl_next;
ctrl_skip:
    printf("\x1b[36m[NODO/CTRL] OP_SKIP. Reproduccion continua.\x1b[0m\n");
    goto ctrl_next;
ctrl_unknown:
    goto ctrl_next;
}


FGN_AI_Context *core_ia = NULL;


/* ════════════════════════════════════════════════════════════════════════════
 * MAIN
 * ════════════════════════════════════════════════════════════════════════════ */
int main(void) {
    int sock_data;
    struct sockaddr_in addr_data, addr_ctrl;
    pthread_t thread_ctrl;

    inicializar_sistema_acero();
    inicializar_motor_osiris();

    signal(SIGPIPE, SIG_IGN);

    /* Arrancar sistema de ventanas FGN:
     * - SDL_Init, HUD slot 0, SDL_THREAD, FLUSH_THREAD
     * - driver_activo vinculado a slot 0 tras esta llamada */
    if (fgn_windows_iniciar() != 0) {
        printf("\x1b[31m[ERROR] No se pudo iniciar sistema de ventanas FGN.\x1b[0m\n");
        return 1;
    }
    driver_activo = cargar_driver_gl_legacy();
    driver_activo.iniciar(0, 0);

    uranio_safe = crear_bloque(65536, URANIO);
    if (!uranio_safe.data) { printf("[ERROR] Fallo bloque Uranio.\n"); return 1; }

    /* ── DISPATCH TABLE ──────────────────────────────────────────────────── */
    static void* dispatch_table[256] = { [0 ... 255] = &&unknown_op };
    dispatch_table[1]  = &&op_hwprobe;
    dispatch_table[5]  = &&op_rescale;
    dispatch_table[7]  = &&op_stream;
    dispatch_table[9]  = &&op_exit;
    dispatch_table[10] = &&op_pause;
    dispatch_table[15] = &&op_skip;
    dispatch_table[22] = &&op_ia_update;
    dispatch_table[30] = &&op_win_create;
    dispatch_table[31] = &&op_win_destroy;
    dispatch_table[32] = &&op_win_show;
    dispatch_table[33] = &&op_win_hide;
    dispatch_table[34] = &&op_render_frame;
    dispatch_table[35] = &&op_overlay_text;
    dispatch_table[36] = &&op_win_close;
    dispatch_table[37] = &&op_win_list;
    dispatch_table[40] = &&op_js_eval;
    dispatch_table[41] = &&op_js_load;
    dispatch_table[42] = &&op_js_reset;

    printf("\x1b[1m--- NODO OSIRIS ACTIVO ---\x1b[0m\n");

    while (1) {
        sock_data = socket(AF_INET, SOCK_STREAM, 0);
        sock_ctrl = socket(AF_INET, SOCK_STREAM, 0);
        addr_data.sin_family = addr_ctrl.sin_family = AF_INET;
        addr_data.sin_port   = htons(PORT_DATA);
        addr_ctrl.sin_port   = htons(PORT_CTRL);
        inet_pton(AF_INET, CEREBRO_IP, &addr_data.sin_addr);
        inet_pton(AF_INET, CEREBRO_IP, &addr_ctrl.sin_addr);

        if (connect(sock_data, (struct sockaddr*)&addr_data, sizeof(addr_data)) < 0 ||
            connect(sock_ctrl, (struct sockaddr*)&addr_ctrl, sizeof(addr_ctrl)) < 0) {
            close(sock_data); close(sock_ctrl); sleep(1); continue;
        }
        printf("\x1b[32m[OK] Doble vinculo con Cerebro.\n\x1b[0m");

        /* Inicializar métricas V-Ghost para esta sesión */
        vg_conectado   = 1;
        vg_bytes_total = 0;
        vg_frames      = 0;
        vg_hud_request_refresh();

        pthread_create(&thread_ctrl, NULL, control_logic, NULL);

next_op: ;
    OsirisHeader hdr;
    int tr = 0;
    while (tr < (int)sizeof(OsirisHeader)) {
        int n = read(sock_data, (uint8_t*)&hdr + tr, sizeof(OsirisHeader) - tr);
        if (n <= 0) goto connection_lost;
        tr += n;
    }

    if (hdr.version != 2) {
        printf("[SYNC] Version desconocida (%u), descartando.\n", hdr.version);
        goto next_op;
    }

    uint8_t  opcode     = hdr.opcode;
    uint32_t chunk_size = hdr.payload_size;

    /* ── Actualizar métricas V-Ghost ─────────────────────────────────────── */
    vg_bytes_total   += sizeof(OsirisHeader) + chunk_size;
    vg_ultimo_opcode  = opcode;

    /* ── HMAC + XOR (Fase 2B) ────────────────────────────────────────────── */
    if (chunk_size > 0) {
        if (chunk_size > 67108864u) {
            printf("[SEC] payload_size=%u excede limite.\n", chunk_size);
            goto next_op;
        }
        if (chunk_size > uranio_safe.size)
            rb_rescale(&uranio_safe, chunk_size);
        int tr2 = 0;
        while (tr2 < (int)chunk_size) {
            int n = read(sock_data, (uint8_t*)uranio_safe.data + tr2, chunk_size - tr2);
            if (n <= 0) goto connection_lost;
            tr2 += n;
        }
        if (!osiris_hmac_verificar((OsirisHeaderForHMAC*)&hdr,
                                   (uint8_t*)uranio_safe.data, chunk_size, &hmac_ctx))
            goto next_op;
        osiris_xor_payload((uint8_t*)uranio_safe.data, chunk_size,
                           hmac_ctx.session_key, hdr.frame_cnt);
    } else {
        if (!osiris_hmac_verificar((OsirisHeaderForHMAC*)&hdr, NULL, 0, &hmac_ctx))
            goto next_op;
    }

    goto *dispatch_table[opcode];

    /* ════════════════════════════════════════════════════════════════════════
     * HANDLERS — El TCP solo prepara datos y empuja a la cola MPSC.
     * No toca SDL directamente. ACK se envía desde SDL_THREAD al ejecutar.
     * ════════════════════════════════════════════════════════════════════════ */

    /* ── OP_STREAM (7) ───────────────────────────────────────────────────── */
    op_stream:
    {
        if (core_ia && core_ia->modelo_data) {
            float r = fgn_ai_analizar(core_ia, &uranio_safe);
            if (r < 0.25f)
                printf("\x1b[1;31m[!] RESONANCIA BAJA (%.2f)\x1b[0m\n", r);
        }
        pthread_mutex_lock(&pipe_mutex);
        if (!display_pipe && !video_paused && chunk_size > 0) {
            printf("\x1b[34m[STREAM] Iniciando RAW mpegts+...\n\x1b[0m");
            display_pipe = popen("ffplay -i pipe:0 -flags low_delay "
                                 "-probesize 32 -loglevel quiet "
                                 "-window_title 'FGN Secure RAW STREAM'", "w");
            update_ffplay_pid();
        }
        if (display_pipe && !video_paused) {
            if (fwrite(uranio_safe.data, 1, chunk_size, display_pipe) < chunk_size) {
                printf("\x1b[31m[!] Error pipe. Reiniciando...\n\x1b[0m");
                if (ffplay_pid > 0) { kill(ffplay_pid, SIGTERM); ffplay_pid = 0; }
                fclose(display_pipe); display_pipe = NULL;
            } else {
                fflush(display_pipe);
                vg_frames++;            /* frame entregado a ffplay */
            }
        }
        pthread_mutex_unlock(&pipe_mutex);
        vg_hud_request_refresh();       /* pedir refresco HUD al SDL_THREAD */
    }
    goto next_op;

    /* ── OP_RESCALE (5) ──────────────────────────────────────────────────── */
    op_rescale:
        rb_rescale(&uranio_safe, chunk_size);
        goto next_op;

    /* ── OP_PAUSE (10) ───────────────────────────────────────────────────── */
    op_pause:
        video_paused = !video_paused;
        if (ffplay_pid > 0)
            kill(ffplay_pid, video_paused ? SIGSTOP : SIGCONT);
        goto next_op;

    /* ── OP_SKIP (15) ────────────────────────────────────────────────────── */
    op_skip:
        printf("\x1b[36m[NODO] OP_SKIP. Reproduccion continua.\x1b[0m\n");
        goto next_op;

    /* ── OP_IA_UPDATE (22) ───────────────────────────────────────────────── */
    op_ia_update:
    {
        printf("\x1b[35m[IA] RECIBIENDO ADN...\n\x1b[0m");
        RB_SafePtr adn_safe = crear_bloque(1024, URANIO);
        int tr3 = 0;
        while (tr3 < 1024) {
            int n = read(sock_data, (uint8_t*)adn_safe.data + tr3, 1024 - tr3);
            if (n <= 0) { rb_liberar(&adn_safe); goto connection_lost; }
            tr3 += n;
        }
        if (!core_ia) core_ia = fgn_ai_init();
        fgn_ai_actualizar_modelo(core_ia, &adn_safe);
        printf("\x1b[32m[IA] ADN sincronizado (ID: %u)\n\x1b[0m", core_ia->id_modelo);
    }
    goto next_op;

    /* ── OP_HWPROBE (1) ──────────────────────────────────────────────────── */
    op_hwprobe:
    {
        printf("\x1b[36m[HW] Probe solicitado por Cerebro.\x1b[0m\n");
        probe_sistema_base(&mi_hardware);
        probe_video_capacidades(&mi_hardware);
        probe_red_estado(&mi_hardware);
        uint32_t hw_sz = (uint32_t)sizeof(OsirisHardwareMap);
        uint8_t resp_hdr[16] = {0};
        resp_hdr[0] = 2; resp_hdr[1] = 1; resp_hdr[2] = 51;
        resp_hdr[7]  = (uint8_t)(hw_sz & 0xFF);
        resp_hdr[8]  = (uint8_t)((hw_sz >>  8) & 0xFF);
        resp_hdr[9]  = (uint8_t)((hw_sz >> 16) & 0xFF);
        resp_hdr[10] = (uint8_t)((hw_sz >> 24) & 0xFF);
        write(sock_ctrl, resp_hdr, 16);
        write(sock_ctrl, &mi_hardware, hw_sz);
        printf("\x1b[32m[HW] Mapa enviado (%u bytes).\x1b[0m\n", hw_sz);
    }
    goto next_op;

    /* ── OP_WIN_CREATE (30) ──────────────────────────────────────────────── */
    op_win_create:
    {
        if (chunk_size < sizeof(WinCreateParams)) {
            nodo_send_ack(30, ACK_ERROR); goto next_op;
        }
        WinCreateParams *p = (WinCreateParams*)uranio_safe.data;
        p->titulo[63] = 0;

        /* Traducir flags de protocolo a FGN_WIN_FLAG_* */
        uint32_t fgn_flags = 0;
        if (p->flags == 1) fgn_flags |= FGN_WIN_FLAG_FULLSCREEN;
        if (p->flags == 2) fgn_flags |= FGN_WIN_FLAG_BORDERLESS;

        uint16_t w = (p->ancho > 0 && p->ancho < 7680) ? p->ancho : 640;
        uint16_t h = (p->alto  > 0 && p->alto  < 4320) ? p->alto  : 480;

        int slot = fgn_win_crear(-1, w, h, (const char*)p->titulo, fgn_flags);
        if (slot >= 0) {
            mi_hardware.pantalla_ancho = w;
            mi_hardware.pantalla_alto  = h;
            mi_hardware.soporte_sdl2   = true;
            nodo_send_ack(30, ACK_OK);
        } else {
            nodo_send_ack(30, ACK_ERROR);
        }
    }
    goto next_op;

    /* ── OP_WIN_DESTROY (31) — cierra el slot activo mas reciente ───────── */
    op_win_destroy:
    {
        int ultimo = fgn_slot_ultimo_activo();
        if (ultimo > 0) {   /* > 0: nunca destruir slot 0 (HUD) por este opcode */
            fgn_win_cerrar(ultimo);
            nodo_send_ack(31, ACK_OK);
        } else {
            nodo_send_ack(31, ACK_ERROR);
        }
    }
    goto next_op;

    /* ── OP_WIN_SHOW (32) ────────────────────────────────────────────────── */
    op_win_show:
    {
        int slot = (chunk_size >= 4) ?
            (int)*(uint32_t*)uranio_safe.data :
            fgn_slot_ultimo_activo();
        if (FGN_SLOT_VALIDO(slot)) {
            SdlCmd cmd = { .tipo = SDL_CMD_WIN_MOSTRAR, .slot = (uint8_t)slot };
            sdl_cmd_push(&cmd);
            nodo_send_ack(32, ACK_OK);
        } else {
            nodo_send_ack(32, ACK_ERROR);
        }
    }
    goto next_op;

    /* ── OP_WIN_HIDE (33) ────────────────────────────────────────────────── */
    op_win_hide:
    {
        int slot = (chunk_size >= 4) ?
            (int)*(uint32_t*)uranio_safe.data :
            fgn_slot_ultimo_activo();
        if (FGN_SLOT_VALIDO(slot)) {
            SdlCmd cmd = { .tipo = SDL_CMD_WIN_OCULTAR, .slot = (uint8_t)slot };
            sdl_cmd_push(&cmd);
            nodo_send_ack(33, ACK_OK);
        } else {
            nodo_send_ack(33, ACK_ERROR);
        }
    }
    goto next_op;

    /* ── OP_RENDER_FRAME (34) ────────────────────────────────────────────── */
    op_render_frame:
    {
        int slot = -1;
        for (int i = 1; i < MAX_FGN_WINDOWS; i++) {
            if (FGN_SLOT_VALIDO(i) && fgn_wins[i].tex) { slot = i; break; }
        }
        if (slot >= 0 && chunk_size > 0 &&
            chunk_size <= fgn_wins[slot].bloque.size) {
            memcpy(fgn_wins[slot].bloque.data, uranio_safe.data, chunk_size);
            SdlCmd cmd = {
                .tipo  = SDL_CMD_RENDER_FRAME,
                .slot  = (uint8_t)slot,
                .frame = { .n_bytes = chunk_size }
            };
            sdl_cmd_push(&cmd);
            printf("\x1b[34m[SDL] Frame %u bytes -> slot %d\x1b[0m\n",
                   chunk_size, slot);
        }
    }
    goto next_op;

    /* ── OP_OVERLAY_TEXT (35) ────────────────────────────────────────────── */
    op_overlay_text:
    {
        if (chunk_size < sizeof(OverlayParams)) {
            nodo_send_ack(35, ACK_ERROR); goto next_op;
        }
        OverlayParams *op = (OverlayParams*)uranio_safe.data;
        op->texto[127] = 0;

        /* Intentar via JS bridge si el contexto esta disponible */
        JSContext *js_ctx = obtener_contexto_osiris();
        if (js_ctx) {
            char script[256];
            snprintf(script, sizeof(script),
                "osiris_dibujar_texto('%s', %d, %d);",
                (char*)op->texto, (int)op->x, (int)op->y);
            manejar_comando_fgn_js(script);
        }

        /* Siempre encolar tambien via cola FGN — el JS bridge puede fallar */
        fgn_win_overlay(-1,
                        (int16_t)op->x, (int16_t)op->y,
                        (const char*)op->texto,
                        (uint8_t*)op->color);
        nodo_send_ack(35, ACK_OK);
    }
    goto next_op;

    /* ── OP_WIN_CLOSE (36) — cierra ventana por slot ID ─────────────────── */
    op_win_close:
    {
        if (chunk_size < sizeof(uint32_t)) {
            nodo_send_ack(36, ACK_ERROR); goto next_op;
        }
        int slot = (int)*(uint32_t*)uranio_safe.data;
        fgn_win_cerrar(slot);
        nodo_send_ack(36, ACK_OK);
    }
    goto next_op;

    /* ── OP_WIN_LIST (37) — lista slots activos ──────────────────────────── */
    op_win_list:
    {
        printf("\x1b[36m[SDL] Slots activos: ");
        bool alguno = false;
        for (int i = 0; i < MAX_FGN_WINDOWS; i++) {
            if (fgn_wins[i].activa) {
                printf("[%d:'%s'] ", i, fgn_wins[i].titulo);
                alguno = true;
            }
        }
        if (!alguno) printf("(ninguno)");
        printf("\x1b[0m\n");
        nodo_send_ack(37, ACK_OK);
    }
    goto next_op;

    /* ── OP_JS_EVAL (40) ─────────────────────────────────────────────────── */
    op_js_eval:
    {
        if (chunk_size == 0 || chunk_size > 65535) {
            nodo_send_ack(40, ACK_ERROR); goto next_op;
        }
        if (chunk_size >= uranio_safe.size)
            rb_rescale(&uranio_safe, chunk_size + 1);
        ((uint8_t*)uranio_safe.data)[chunk_size] = 0;
        printf("\x1b[35m[JS] Eval (%u bytes)\x1b[0m\n", chunk_size);
        manejar_comando_fgn_js((const char*)uranio_safe.data);
        nodo_send_ack(40, ACK_OK);
    }
    goto next_op;

    /* ── OP_JS_LOAD (41) ─────────────────────────────────────────────────── */
    op_js_load:
    {
        if (chunk_size == 0) { nodo_send_ack(41, ACK_ERROR); goto next_op; }
        printf("\x1b[35m[JS] Cargando bytecode (%u bytes)\x1b[0m\n", chunk_size);
        JSContext *js_ctx = obtener_contexto_osiris();
        if (!js_ctx) { inicializar_motor_osiris(); js_ctx = obtener_contexto_osiris(); }
        if (js_ctx) {
            JSValue obj = JS_ReadObject(js_ctx,
                                        (const uint8_t*)uranio_safe.data,
                                        chunk_size, JS_READ_OBJ_BYTECODE);
            if (JS_IsException(obj)) {
                printf("\x1b[31m[JS] Error bytecode\x1b[0m\n");
                nodo_send_ack(41, ACK_ERROR);
            } else {
                JS_FreeValue(js_ctx, JS_EvalFunction(js_ctx, obj));
                nodo_send_ack(41, ACK_OK);
            }
        } else nodo_send_ack(41, ACK_ERROR);
    }
    goto next_op;

    /* ── OP_JS_RESET (42) ────────────────────────────────────────────────── */
    op_js_reset:
        printf("\x1b[33m[JS] Reset motor QuickJS.\x1b[0m\n");
        cerrar_motor_osiris();
        inicializar_motor_osiris();
        nodo_send_ack(42, ACK_OK);
        goto next_op;

    unknown_op:
        goto next_op;

    op_exit:
        goto connection_lost;

connection_lost:
        printf("\x1b[31m[!] Conexion perdida. Limpiando...\n\x1b[0m");
        vg_conectado = 0;
        vg_hud_request_refresh();   /* HUD muestra estado desconectado */
        if (core_ia) { fgn_ai_destruir(core_ia); core_ia = NULL; }
        close_display();
        close(sock_data); close(sock_ctrl);
        pthread_cancel(thread_ctrl);
        sleep(1);
    } /* fin while(1) */

    cerrar_motor_osiris();
    fgn_windows_cerrar();
    return 0;
}