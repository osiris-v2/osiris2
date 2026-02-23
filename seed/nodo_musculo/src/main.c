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
#include "demo/fgn_monitor.c"
#include "fgn_ai_core.h"
#include "osiris_hmac.h"
#include "quickjs.h"
#include <SDL2/SDL.h>

extern void materializar_mirror_sdl(OsirisHardwareMap *map, uint16_t id_handler);
extern void probe_video_capacidades(OsirisHardwareMap *map);

#define PORT_DATA  2000
#define PORT_CTRL  2001
#define CEREBRO_IP "127.0.0.1"

OsirisHardwareMap mi_hardware;
OsirisVideoDriver driver_activo;

/* ── HEADER OSIRIS ───────────────────────────────────────────────────────── */
#pragma pack(push, 1)
typedef struct {
    uint8_t  version;
    uint8_t  seed_id;
    uint8_t  opcode;
    uint32_t signature;
    uint32_t payload_size;
    uint32_t frame_cnt;
    uint8_t  reservado;
} OsirisHeader;
#pragma pack(pop)
_Static_assert(sizeof(OsirisHeader) == 16, "OsirisHeader debe ser 16 bytes");

/* ── PAYLOADS ────────────────────────────────────────────────────────────── */
#pragma pack(push, 1)
typedef struct { uint16_t ancho; uint16_t alto; uint8_t titulo[64]; uint16_t flags; } WinCreateParams;
typedef struct { int16_t x; int16_t y; uint8_t color[4]; uint8_t size; uint8_t texto[128]; uint8_t pad; } OverlayParams;
typedef struct { uint8_t opcode_origen; uint8_t resultado; } AckPayload;
#pragma pack(pop)

#define ACK_OK      0
#define ACK_ERROR   1
#define ACK_PENDING 2

extern void inicializar_sistema_acero(void);
extern void inicializar_motor_osiris(void);
extern void cerrar_motor_osiris(void);
extern JSContext *obtener_contexto_osiris(void);
extern void manejar_comando_fgn_js(const char *script);

FILE    *display_pipe = NULL;
pid_t    ffplay_pid   = 0;
int      video_paused = 0;
int      sock_ctrl    = 0;
RB_SafePtr uranio_safe;
OsirisHMACCtx hmac_ctx = { .activo = 0 };
pthread_mutex_t pipe_mutex = PTHREAD_MUTEX_INITIALIZER;


/* ═══════════════════════════════════════════════════════════════════════════
 * COLA DE COMANDOS SDL  (MPSC — Multiple Producer, Single Consumer)
 *
 * El hilo TCP y el flush_thread escriben comandos SDL en esta cola.
 * El hilo SDL_THREAD es el UNICO consumidor y el UNICO que toca la API SDL.
 *
 * Esto elimina completamente la necesidad de SDL_PUMP_PAUSE/RESUME y
 * cualquier sincronizacion entre hilos para operaciones SDL. Escala a
 * cualquier numero de opcodes SDL sin cambios de arquitectura.
 *
 * Implementacion: ring buffer de SDL_CMD_QUEUE_SIZE posiciones.
 * - head: indice de escritura (productores)
 * - tail: indice de lectura  (consumidor SDL)
 * - Acceso protegido por sdl_queue_mutex para multiples productores.
 * - El consumidor no necesita mutex — es el unico lector.
 *
 * Cada comando lleva un RB_SafePtr ACERO para datos variables.
 * El SDL thread libera el bloque al ejecutar el comando.
 * ═══════════════════════════════════════════════════════════════════════════ */

#define SDL_CMD_QUEUE_SIZE 64   /* potencia de 2 — mascara con AND */
#define SDL_CMD_QUEUE_MASK (SDL_CMD_QUEUE_SIZE - 1)

typedef enum {
    SDL_CMD_NOP         = 0,
    SDL_CMD_WIN_CREATE  = 1,   /* datos: WinCreateParams en bloque ACERO   */
    SDL_CMD_WIN_CLOSE   = 2,   /* datos: uint32_t slot_id en bloque ACERO  */
    SDL_CMD_WIN_DESTROY = 3,   /* datos: ninguno — destruye ultima ventana */
    SDL_CMD_WIN_SHOW    = 4,   /* datos: uint32_t slot_id                  */
    SDL_CMD_WIN_HIDE    = 5,   /* datos: uint32_t slot_id                  */
    SDL_CMD_WIN_LIST    = 6,   /* datos: ninguno — imprime slots activos   */
    SDL_CMD_RENDER_FRAME= 7,   /* datos: frame en bloque ACERO             */
    /* Espacio reservado para Fase 4: SDL_CMD_RENDER_TEXTURE, _SHADER, etc. */
} SdlCmdTipo;

typedef struct {
    SdlCmdTipo  tipo;
    RB_SafePtr  datos;    /* ACERO — liberado por SDL thread al ejecutar  */
    uint8_t     ack_op;   /* opcode origen para ACK al Cerebro (0=no ack) */
} SdlCmd;

static SdlCmd          sdl_queue[SDL_CMD_QUEUE_SIZE] = {0};
static volatile uint32_t sdl_queue_head = 0;   /* escritura — productores */
static volatile uint32_t sdl_queue_tail = 0;   /* lectura  — SDL thread   */
static pthread_mutex_t sdl_queue_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Empuja un comando a la cola. Devuelve 0 si OK, -1 si cola llena. */
static int sdl_cmd_push(SdlCmdTipo tipo, RB_SafePtr datos, uint8_t ack_op) {
    pthread_mutex_lock(&sdl_queue_mutex);
    uint32_t next = (sdl_queue_head + 1) & SDL_CMD_QUEUE_MASK;
    if (next == sdl_queue_tail) {
        /* Cola llena — en produccion podriamos expandirla dinamicamente */
        pthread_mutex_unlock(&sdl_queue_mutex);
        printf("\x1b[31m[SDL_Q] Cola llena — comando descartado.\x1b[0m\n");
        return -1;
    }
    sdl_queue[sdl_queue_head].tipo   = tipo;
    sdl_queue[sdl_queue_head].datos  = datos;
    sdl_queue[sdl_queue_head].ack_op = ack_op;
    sdl_queue_head = next;
    pthread_mutex_unlock(&sdl_queue_mutex);
    return 0;
}

/* Lee el siguiente comando de la cola. Devuelve 0 si habia algo, -1 si vacia. */
static int sdl_cmd_pop(SdlCmd *out) {
    if (sdl_queue_tail == sdl_queue_head) return -1;  /* vacia */
    *out = sdl_queue[sdl_queue_tail];
    sdl_queue_tail = (sdl_queue_tail + 1) & SDL_CMD_QUEUE_MASK;
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * REGISTRO DE VENTANAS FGN
 *
 * Solo el SDL_THREAD accede a fgn_wins para crear/destruir.
 * El flush_thread y el TCP solo leen fgn_slots_libres bajo fgn_wins_mutex
 * para saber si hay pendientes. Sin races posibles.
 *
 * Ciclo de vida de un slot:
 *   TCP push(SDL_CMD_WIN_CREATE) → SDL_THREAD crea → registra en fgn_wins
 *   Pump marca pendiente_destruir → flush_thread push(SDL_CMD_WIN_CLOSE)
 *   SDL_THREAD ejecuta cierre → rb_liberar → slot libre
 * ═══════════════════════════════════════════════════════════════════════════ */

#define MAX_FGN_WINDOWS    32
#define FGN_WIN_BLOCK_SIZE (sizeof(SDL_Window*) + sizeof(SDL_Renderer*) + sizeof(uint32_t))

typedef struct {
    RB_SafePtr bloque;             /* DIAMANTE: [SDL_Window*][SDL_Renderer*][win_id] */
    bool       activa;
    bool       pendiente_destruir; /* pump marca — flush_thread encola cierre        */
} FgnWinEntry;

static FgnWinEntry     fgn_wins[MAX_FGN_WINDOWS] = {0};
static uint32_t        fgn_slots_libres          = 0xFFFFFFFFu;
static pthread_mutex_t fgn_wins_mutex            = PTHREAD_MUTEX_INITIALIZER;

/* Accesores tipados al bloque DIAMANTE */
static inline SDL_Window**   _win  (FgnWinEntry *e) { return (SDL_Window**)  e->bloque.data; }
static inline SDL_Renderer** _ren  (FgnWinEntry *e) { return (SDL_Renderer**)((uint8_t*)e->bloque.data + sizeof(SDL_Window*)); }
static inline uint32_t*      _winid(FgnWinEntry *e) { return (uint32_t*)     ((uint8_t*)e->bloque.data + sizeof(SDL_Window*) + sizeof(SDL_Renderer*)); }

/* Registra ventana — LLAMAR SOLO DESDE SDL_THREAD */
static int fgn_wins_registrar(SDL_Window *w, SDL_Renderer *r) {
    pthread_mutex_lock(&fgn_wins_mutex);
    if (!fgn_slots_libres) { pthread_mutex_unlock(&fgn_wins_mutex); return -1; }

    int i = __builtin_ctz(fgn_slots_libres);
    fgn_slots_libres &= ~(1u << i);

    memset(&fgn_wins[i], 0, sizeof(FgnWinEntry));
    fgn_wins[i].bloque = crear_bloque(FGN_WIN_BLOCK_SIZE, DIAMANTE);
    if (!fgn_wins[i].bloque.data) {
        fgn_slots_libres |= (1u << i);
        pthread_mutex_unlock(&fgn_wins_mutex);
        return -1;
    }
    *_win  (&fgn_wins[i]) = w;
    *_ren  (&fgn_wins[i]) = r;
    *_winid(&fgn_wins[i]) = SDL_GetWindowID(w);
    fgn_wins[i].activa             = true;
    fgn_wins[i].pendiente_destruir = false;
    pthread_mutex_unlock(&fgn_wins_mutex);
    return i;
}

/* Cierra ventana por slot — LLAMAR SOLO DESDE SDL_THREAD, FUERA de PollEvent */
static void fgn_wins_cerrar_slot(int i) {
    pthread_mutex_lock(&fgn_wins_mutex);
    if (i < 0 || i >= MAX_FGN_WINDOWS || !fgn_wins[i].activa ||
        !fgn_wins[i].bloque.data || fgn_wins[i].bloque.estado == ESTADO_VOID) {
        pthread_mutex_unlock(&fgn_wins_mutex);
        return;
    }
    SDL_Renderer *ren = *_ren(&fgn_wins[i]);
    SDL_Window   *win = *_win(&fgn_wins[i]);
    fgn_wins[i].activa = false;
    fgn_slots_libres  |= (1u << i);
    rb_liberar(&fgn_wins[i].bloque);
    pthread_mutex_unlock(&fgn_wins_mutex);
    if (ren) SDL_DestroyRenderer(ren);
    if (win) SDL_DestroyWindow(win);
    printf("\x1b[33m[SDL] Slot %d cerrado.\x1b[0m\n", i);
}

/* Cierra la ventana mas reciente — LLAMAR SOLO DESDE SDL_THREAD */
static void fgn_wins_cerrar_ultima(void) {
    pthread_mutex_lock(&fgn_wins_mutex);
    uint32_t ocupados = ~fgn_slots_libres;
    if (!ocupados) { pthread_mutex_unlock(&fgn_wins_mutex); return; }
    int i = 31 - __builtin_clz(ocupados);
    pthread_mutex_unlock(&fgn_wins_mutex);
    fgn_wins_cerrar_slot(i);
}


/* ── HELPERS GENERALES ───────────────────────────────────────────────────── */
void update_ffplay_pid() {
    FILE *p = popen("pidof ffplay", "r");
    if (p) { if (fscanf(p, "%d", &ffplay_pid) != 1) ffplay_pid = 0; pclose(p); }
}

void close_display() {
    pthread_mutex_lock(&pipe_mutex);
    if (display_pipe) {
        printf("\x1b[31m[SISTEMA] Cerrando visor...\n\x1b[0m");
        if (ffplay_pid > 0) { kill(ffplay_pid, SIGTERM); ffplay_pid = 0; }
        fclose(display_pipe); display_pipe = NULL; video_paused = 0;
    }
    pthread_mutex_unlock(&pipe_mutex);
}

static inline void nodo_send_ack(uint8_t opcode_origen, uint8_t resultado) {
    if (sock_ctrl <= 0) return;
    uint8_t pkt[18] = {0};
    pkt[0]=2; pkt[1]=1; pkt[2]=50; pkt[7]=2;
    pkt[16]=opcode_origen; pkt[17]=resultado;
    write(sock_ctrl, pkt, 18);
}


/* ── HILO DE CONTROL ─────────────────────────────────────────────────────── */
void* control_logic(void* arg) {
    (void)arg;
    uint8_t hs_buf[OSIRIS_HANDSHAKE_SIZE];
    int hs_tr = 0;
    while (hs_tr < OSIRIS_HANDSHAKE_SIZE) {
        int n = read(sock_ctrl, hs_buf + hs_tr, OSIRIS_HANDSHAKE_SIZE - hs_tr);
        if (n <= 0) { printf("[HMAC] Error en handshake.\n"); return NULL; }
        hs_tr += n;
    }
    osiris_hmac_recibir_handshake(hs_buf, &hmac_ctx);

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


/* ═══════════════════════════════════════════════════════════════════════════
 * FLUSH THREAD
 *
 * Despierta cada 50ms. Comprueba si hay ventanas marcadas pendiente_destruir
 * por el pump. Si las hay, empuja SDL_CMD_WIN_CLOSE a la cola.
 * El SDL_THREAD ejecuta el cierre limpiamente fuera de SDL_PollEvent.
 *
 * Esto hace que el cierre con la X sea casi instantaneo para el usuario
 * sin necesidad de ningun comando manual.
 * ═══════════════════════════════════════════════════════════════════════════ */
static volatile int flush_thread_activo = 1;

void* flush_thread(void* arg) {
    (void)arg;
    struct timespec sleep_t = {0, 50000000};  /* 50ms */
    while (flush_thread_activo) {
        nanosleep(&sleep_t, NULL);

        pthread_mutex_lock(&fgn_wins_mutex);
        uint32_t tmp = ~fgn_slots_libres;
        while (tmp) {
            int i = __builtin_ctz(tmp); tmp &= tmp - 1;
            if (!fgn_wins[i].pendiente_destruir) continue;
            /* Marcar como ya encolado para no encolar dos veces */
            fgn_wins[i].pendiente_destruir = false;
            pthread_mutex_unlock(&fgn_wins_mutex);

            /* Encolar SDL_CMD_WIN_CLOSE con el slot_id */
            RB_SafePtr slot_bloque = crear_bloque(sizeof(uint32_t), ACERO);
            if (slot_bloque.data) {
                *(uint32_t*)slot_bloque.data = (uint32_t)i;
                sdl_cmd_push(SDL_CMD_WIN_CLOSE, slot_bloque, 0);
            }
            pthread_mutex_lock(&fgn_wins_mutex);
            tmp = ~fgn_slots_libres;  /* recalcular */
        }
        pthread_mutex_unlock(&fgn_wins_mutex);
    }
    return NULL;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SDL THREAD
 *
 * Unico hilo que toca la API SDL. Dos responsabilidades:
 *   1. SDL_PollEvent — mantiene el WM respondiendo
 *   2. Consumir sdl_cmd_queue — ejecutar Create/Close/Show/Hide/Render
 *
 * Al ejecutar un comando, libera el bloque ACERO de datos con rb_liberar.
 * Si el comando tiene ack_op != 0, envia ACK al Cerebro.
 *
 * REGLA: SDL_Destroy* NUNCA dentro de SDL_PollEvent. Los comandos de cierre
 * se ejecutan DESPUES del vaciado de eventos en cada ciclo.
 * ═══════════════════════════════════════════════════════════════════════════ */
static volatile int sdl_thread_activo = 1;

void* sdl_thread_fn(void* arg) {
    (void)arg;
    SDL_Event e;

    while (sdl_thread_activo) {

        /* ── FASE 1: Procesar eventos SDL ──────────────────────────────── */
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                printf("\x1b[33m[SDL] QUIT interceptado.\x1b[0m\n");
            }
            if (e.type == SDL_WINDOWEVENT &&
                e.window.event == SDL_WINDOWEVENT_CLOSE) {
                /* Buscar slot por win_id y marcar pendiente */
                pthread_mutex_lock(&fgn_wins_mutex);
                uint32_t tmp = ~fgn_slots_libres;
                while (tmp) {
                    int i = __builtin_ctz(tmp); tmp &= tmp - 1;
                    if (fgn_wins[i].activa &&
                        fgn_wins[i].bloque.data &&
                        fgn_wins[i].bloque.estado != ESTADO_VOID &&
                        *_winid(&fgn_wins[i]) == e.window.windowID) {
                        fgn_wins[i].pendiente_destruir = true;
                        printf("\x1b[33m[SDL] Ventana %d: cierre pendiente.\x1b[0m\n", i);
                        break;
                    }
                }
                pthread_mutex_unlock(&fgn_wins_mutex);
            }
        }

        /* ── FASE 2: Consumir cola de comandos SDL ─────────────────────
         * Separado del PollEvent — los Destroy ocurren aqui, fuera del
         * bucle de eventos. Esto es lo que evita el segfault de X11.    */
        SdlCmd cmd;
        while (sdl_cmd_pop(&cmd) == 0) {
            switch (cmd.tipo) {

            case SDL_CMD_WIN_CREATE: {
                if (!cmd.datos.data) break;
                WinCreateParams *p = (WinCreateParams*)cmd.datos.data;
                p->titulo[63] = 0;
                for (int ti = 0; ti < 63; ti++)
                    if (p->titulo[ti] && (p->titulo[ti] < 32 || p->titulo[ti] > 126))
                        p->titulo[ti] = '_';
                uint16_t w = (p->ancho > 0 && p->ancho < 7680) ? p->ancho : 640;
                uint16_t h = (p->alto  > 0 && p->alto  < 4320) ? p->alto  : 480;
                char titulo[64]; memcpy(titulo, p->titulo, 64); titulo[63]=0;
                uint16_t flags = p->flags;

                if (SDL_WasInit(SDL_INIT_VIDEO) == 0) SDL_Init(SDL_INIT_VIDEO);
                SDL_Window *win = SDL_CreateWindow(titulo,
                    SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, w, h,
                    SDL_WINDOW_SHOWN | (flags==1 ? SDL_WINDOW_FULLSCREEN_DESKTOP :
                                        flags==2 ? SDL_WINDOW_BORDERLESS : 0));
                SDL_Renderer *ren = NULL;
                if (win) {
                    ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
                    if (ren) {
                        SDL_SetRenderDrawColor(ren, 0, 20, 40, 255);
                        SDL_RenderClear(ren);
                        SDL_SetRenderDrawColor(ren, 0, 180, 220, 255);
                        SDL_Rect rect = {w/2-60, h/2-10, 120, 20};
                        SDL_RenderFillRect(ren, &rect);
                        SDL_RenderPresent(ren);
                    }
                    int slot = fgn_wins_registrar(win, ren);
                    if (slot >= 0) {
                        printf("\x1b[32m[SDL] Ventana '%s' en slot %d.\x1b[0m\n", titulo, slot);
                        mi_hardware.pantalla_ancho = w;
                        mi_hardware.pantalla_alto  = h;
                        mi_hardware.soporte_sdl2   = true;
                        if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_OK);
                    } else {
                        SDL_DestroyRenderer(ren); SDL_DestroyWindow(win);
                        printf("\x1b[31m[SDL] Sin slots disponibles.\x1b[0m\n");
                        if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_ERROR);
                    }
                } else {
                    printf("\x1b[31m[SDL] Error create: %s\x1b[0m\n", SDL_GetError());
                    if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_ERROR);
                }
                rb_liberar(&cmd.datos);
                break;
            }

            case SDL_CMD_WIN_CLOSE: {
                int slot = cmd.datos.data ? (int)*(uint32_t*)cmd.datos.data : -1;
                if (slot >= 0) fgn_wins_cerrar_slot(slot);
                if (cmd.datos.data) rb_liberar(&cmd.datos);
                if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_OK);
                break;
            }

            case SDL_CMD_WIN_DESTROY: {
                fgn_wins_cerrar_ultima();
                if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_OK);
                break;
            }

            case SDL_CMD_WIN_SHOW: {
                int slot = cmd.datos.data ? (int)*(uint32_t*)cmd.datos.data : -1;
                pthread_mutex_lock(&fgn_wins_mutex);
                if (slot >= 0 && slot < MAX_FGN_WINDOWS && fgn_wins[slot].activa &&
                    fgn_wins[slot].bloque.data)
                    SDL_ShowWindow(*_win(&fgn_wins[slot]));
                pthread_mutex_unlock(&fgn_wins_mutex);
                if (cmd.datos.data) rb_liberar(&cmd.datos);
                if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_OK);
                break;
            }

            case SDL_CMD_WIN_HIDE: {
                int slot = cmd.datos.data ? (int)*(uint32_t*)cmd.datos.data : -1;
                pthread_mutex_lock(&fgn_wins_mutex);
                if (slot >= 0 && slot < MAX_FGN_WINDOWS && fgn_wins[slot].activa &&
                    fgn_wins[slot].bloque.data)
                    SDL_HideWindow(*_win(&fgn_wins[slot]));
                pthread_mutex_unlock(&fgn_wins_mutex);
                if (cmd.datos.data) rb_liberar(&cmd.datos);
                if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_OK);
                break;
            }

            case SDL_CMD_WIN_LIST: {
                printf("\x1b[36m[SDL] Slots activos: ");
                pthread_mutex_lock(&fgn_wins_mutex);
                uint32_t tmp = ~fgn_slots_libres;
                if (!tmp) printf("(ninguno)");
                while (tmp) {
                    int i = __builtin_ctz(tmp); tmp &= tmp - 1;
                    if (fgn_wins[i].activa && fgn_wins[i].bloque.data) {
                        char *t = (char*)SDL_GetWindowTitle(*_win(&fgn_wins[i]));
                        printf("[%d:'%s'] ", i, t ? t : "?");
                    }
                }
                pthread_mutex_unlock(&fgn_wins_mutex);
                printf("\x1b[0m\n");
                if (cmd.ack_op) nodo_send_ack(cmd.ack_op, ACK_OK);
                break;
            }

            case SDL_CMD_RENDER_FRAME:
                /* Fase 4: renderizado de frames via textura SDL */
                if (cmd.datos.data) rb_liberar(&cmd.datos);
                break;

            default:
                if (cmd.datos.data) rb_liberar(&cmd.datos);
                break;
            }
        }

        SDL_Delay(16);
    }
    return NULL;
}


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

    /* Lanzar hilos de infraestructura */
    pthread_t thread_sdl, thread_flush;
    pthread_create(&thread_sdl,   NULL, sdl_thread_fn, NULL);
    pthread_create(&thread_flush, NULL, flush_thread,  NULL);
    pthread_detach(thread_sdl);
    pthread_detach(thread_flush);

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
    dispatch_table[36] = &&op_win_close;    /* nuevo: cierra por slot */
    dispatch_table[37] = &&op_win_list;     /* nuevo: lista slots     */
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
        pthread_create(&thread_ctrl, NULL, control_logic, NULL);

next_op: ;
    OsirisHeader hdr;
    int tr = 0;
    while (tr < (int)sizeof(OsirisHeader)) {
        int n = read(sock_data, (uint8_t*)&hdr + tr, sizeof(OsirisHeader) - tr);
        if (n <= 0) goto connection_lost;
        tr += n;
    }
    if (hdr.version != 2) goto next_op;

    uint8_t  opcode     = hdr.opcode;
    uint32_t chunk_size = hdr.payload_size;

    if (chunk_size > 0) {
        if (chunk_size > 67108864u) goto next_op;
        if (chunk_size > uranio_safe.size) rb_rescale(&uranio_safe, chunk_size);
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
     * HANDLERS — El TCP solo prepara datos y empuja a la cola.
     * No toca SDL directamente. ACK se envia desde SDL_THREAD al ejecutar.
     * ════════════════════════════════════════════════════════════════════════ */

    op_stream:
    {
        if (core_ia && core_ia->modelo_data) {
            float r = fgn_ai_analizar(core_ia, &uranio_safe);
            if (r < 0.25f) printf("\x1b[1;31m[!] RESONANCIA BAJA (%.2f)\x1b[0m\n", r);
        }
        pthread_mutex_lock(&pipe_mutex);
        if (!display_pipe && !video_paused && chunk_size > 0) {
            printf("\x1b[34m[STREAM] Iniciando ffplay...\n\x1b[0m");
            display_pipe = popen("ffplay -i pipe:0 -flags low_delay "
                                 "-probesize 32 -loglevel quiet "
                                 "-window_title 'FGN STREAM'", "w");
            update_ffplay_pid();
        }
        if (display_pipe && !video_paused) {
            if (fwrite(uranio_safe.data, 1, chunk_size, display_pipe) < chunk_size) {
                printf("\x1b[31m[!] Error pipe.\n\x1b[0m");
                if (ffplay_pid > 0) { kill(ffplay_pid, SIGTERM); ffplay_pid = 0; }
                fclose(display_pipe); display_pipe = NULL;
            } else fflush(display_pipe);
        }
        pthread_mutex_unlock(&pipe_mutex);
    }
    goto next_op;

    op_rescale:
        rb_rescale(&uranio_safe, chunk_size);
        goto next_op;

    op_pause:
        video_paused = !video_paused;
        if (ffplay_pid > 0) kill(ffplay_pid, video_paused ? SIGSTOP : SIGCONT);
        goto next_op;

    op_skip:
        printf("\x1b[36m[NODO] OP_SKIP. Reproduccion continua.\x1b[0m\n");
        goto next_op;

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

    op_hwprobe:
    {
        printf("\x1b[36m[HW] Probe solicitado.\x1b[0m\n");
        probe_sistema_base(&mi_hardware);
        probe_video_capacidades(&mi_hardware);
        probe_red_estado(&mi_hardware);
        uint32_t hw_sz = (uint32_t)sizeof(OsirisHardwareMap);
        uint8_t resp_hdr[16] = {0};
        resp_hdr[0]=2; resp_hdr[1]=1; resp_hdr[2]=51;
        resp_hdr[7]=(uint8_t)(hw_sz&0xFF); resp_hdr[8]=(uint8_t)((hw_sz>>8)&0xFF);
        resp_hdr[9]=(uint8_t)((hw_sz>>16)&0xFF); resp_hdr[10]=(uint8_t)((hw_sz>>24)&0xFF);
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
        /* Copiar params a bloque ACERO — uranio_safe puede reubicarse */
        RB_SafePtr params = crear_bloque(sizeof(WinCreateParams), ACERO);
        if (!params.data) { nodo_send_ack(30, ACK_ERROR); goto next_op; }
        memcpy(params.data, uranio_safe.data, sizeof(WinCreateParams));
        /* ACK se envia desde SDL_THREAD al crear — ack_op=30 */
        if (sdl_cmd_push(SDL_CMD_WIN_CREATE, params, 30) < 0) {
            rb_liberar(&params);
            nodo_send_ack(30, ACK_ERROR);
        }
        /* No llamamos nodo_send_ack aqui — lo hace el SDL_THREAD */
    }
    goto next_op;

    /* ── OP_WIN_DESTROY (31) ─────────────────────────────────────────────── */
    op_win_destroy:
    {
        RB_SafePtr vacio = {0};
        if (sdl_cmd_push(SDL_CMD_WIN_DESTROY, vacio, 31) < 0)
            nodo_send_ack(31, ACK_ERROR);
    }
    goto next_op;

    /* ── OP_WIN_SHOW (32) ────────────────────────────────────────────────── */
    op_win_show:
    {
        RB_SafePtr slot_b = crear_bloque(sizeof(uint32_t), ACERO);
        if (slot_b.data) {
            /* Si hay payload usa el slot_id del payload, si no usa el ultimo */
            *(uint32_t*)slot_b.data = (chunk_size >= 4) ?
                *(uint32_t*)uranio_safe.data :
                (uint32_t)(31 - __builtin_clz(~fgn_slots_libres));
            sdl_cmd_push(SDL_CMD_WIN_SHOW, slot_b, 32);
        } else nodo_send_ack(32, ACK_ERROR);
    }
    goto next_op;

    /* ── OP_WIN_HIDE (33) ────────────────────────────────────────────────── */
    op_win_hide:
    {
        RB_SafePtr slot_b = crear_bloque(sizeof(uint32_t), ACERO);
        if (slot_b.data) {
            *(uint32_t*)slot_b.data = (chunk_size >= 4) ?
                *(uint32_t*)uranio_safe.data :
                (uint32_t)(31 - __builtin_clz(~fgn_slots_libres));
            sdl_cmd_push(SDL_CMD_WIN_HIDE, slot_b, 33);
        } else nodo_send_ack(33, ACK_ERROR);
    }
    goto next_op;

    op_render_frame:
        /* Fase 4: encolar frame para renderizado SDL */
        if (chunk_size > 0) printf("\x1b[34m[SDL] Frame %u bytes\x1b[0m\n", chunk_size);
        goto next_op;

    op_overlay_text:
    {
        if (chunk_size < sizeof(OverlayParams)) { nodo_send_ack(35, ACK_ERROR); goto next_op; }
        OverlayParams *op = (OverlayParams*)uranio_safe.data;
        op->texto[127] = 0;
        JSContext *js_ctx = obtener_contexto_osiris();
        if (js_ctx) {
            char script[256];
            snprintf(script, sizeof(script), "osiris_dibujar_texto('%s',%d,%d);",
                     (char*)op->texto, (int)op->x, (int)op->y);
            manejar_comando_fgn_js(script);
        } else {
            printf("\x1b[36m[SDL] Overlay: '%s' @(%d,%d)\x1b[0m\n",
                   op->texto, op->x, op->y);
        }
        nodo_send_ack(35, ACK_OK);
    }
    goto next_op;

    /* ── OP_WIN_CLOSE (36) — cierra ventana por slot ID ─────────────────── */
    op_win_close:
    {
        if (chunk_size < sizeof(uint32_t)) { nodo_send_ack(36, ACK_ERROR); goto next_op; }
        RB_SafePtr slot_b = crear_bloque(sizeof(uint32_t), ACERO);
        if (!slot_b.data) { nodo_send_ack(36, ACK_ERROR); goto next_op; }
        *(uint32_t*)slot_b.data = *(uint32_t*)uranio_safe.data;
        if (sdl_cmd_push(SDL_CMD_WIN_CLOSE, slot_b, 36) < 0) {
            rb_liberar(&slot_b);
            nodo_send_ack(36, ACK_ERROR);
        }
    }
    goto next_op;

    /* ── OP_WIN_LIST (37) — lista slots activos ──────────────────────────── */
    op_win_list:
    {
        RB_SafePtr vacio = {0};
        if (sdl_cmd_push(SDL_CMD_WIN_LIST, vacio, 37) < 0)
            nodo_send_ack(37, ACK_ERROR);
    }
    goto next_op;

    op_js_eval:
    {
        if (chunk_size == 0 || chunk_size > 65535) { nodo_send_ack(40, ACK_ERROR); goto next_op; }
        if (chunk_size >= uranio_safe.size) rb_rescale(&uranio_safe, chunk_size + 1);
        ((uint8_t*)uranio_safe.data)[chunk_size] = 0;
        printf("\x1b[35m[JS] Eval (%u bytes)\x1b[0m\n", chunk_size);
        manejar_comando_fgn_js((const char*)uranio_safe.data);
        nodo_send_ack(40, ACK_OK);
    }
    goto next_op;

    op_js_load:
    {
        if (chunk_size == 0) { nodo_send_ack(41, ACK_ERROR); goto next_op; }
        JSContext *js_ctx = obtener_contexto_osiris();
        if (!js_ctx) { inicializar_motor_osiris(); js_ctx = obtener_contexto_osiris(); }
        if (js_ctx) {
            JSValue obj = JS_ReadObject(js_ctx, (const uint8_t*)uranio_safe.data,
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

    op_js_reset:
        printf("\x1b[33m[JS] Reset QuickJS.\x1b[0m\n");
        cerrar_motor_osiris(); inicializar_motor_osiris();
        nodo_send_ack(42, ACK_OK);
        goto next_op;

    unknown_op:
        goto next_op;

    op_exit:
        goto connection_lost;

connection_lost:
        printf("\x1b[31m[!] Conexion perdida.\n\x1b[0m");
        if (core_ia) { fgn_ai_destruir(core_ia); core_ia = NULL; }
        close_display();
        close(sock_data); close(sock_ctrl);
        pthread_cancel(thread_ctrl);
        sleep(1);
    } /* fin while(1) */

    cerrar_motor_osiris();
    return 0;
}