/* ================================================================
 * PROYECTO OSIRIS - osiris_windows.c
 * GESTION DE VENTANAS FGN — SDL_THREAD + FLUSH_THREAD
 *
 * RESPONSABILIDADES:
 *   - Ciclo de vida completo de fgn_wins[] (crear, mostrar, cerrar)
 *   - SDL_THREAD: unico consumidor de sdl_cmd_queue
 *   - FLUSH_THREAD: detecta cierres pendientes cada 50ms y limpia
 *   - HUD V-Ghost: slot 0 reservado, render via metricas volatiles
 *
 * INVARIANTES QUE NUNCA SE ROMPEN:
 *   1. SDL_CreateWindow / SDL_DestroyWindow SOLO ocurren en SDL_THREAD
 *   2. rb_liberar() se llama DESPUES de SDL_Destroy* — nunca antes
 *   3. Slot 0 tiene FGN_WIN_FLAG_SISTEMA — no puede cerrarse via ODS
 *   4. fgn_slots_libres se modifica SOLO con slot 0 del SDL_THREAD activo
 *
 * RELACION CON EL LENGUAJE FGN:
 *   Cada ventana es un bloque<DIAMANTE> con id = slot.
 *   fgn_win_crear() es el precursor de:
 *     bloque<DIAMANTE> v = crear_ventana(800, 600, "MONITOR");
 *   fgn_win_cerrar() es el precursor de:
 *     colapsar(v);  // zeroing garantizado
 *
 * DUREZA 256 - ASCII PURO
 * ================================================================ */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <pthread.h>
#include <time.h>

#include "../include/fgn_runtime.h"
#include "../include/rb_csp.h"
#include "../include/acero_interfaz.h"

/* ================================================================
 * DEFINICIONES GLOBALES (declaradas extern en fgn_runtime.h)
 * ================================================================ */

FgnWinEntry   fgn_wins[MAX_FGN_WINDOWS]  = {0};
uint32_t      fgn_slots_libres           = 0xFFFFFFFEu; /* slot 0 reservado */
SdlCmdQueue   sdl_cmd_queue              = {0};
OsirisHandler h_table[MAX_HANDLERS]      = {0};

/* Metricas HUD — escritas por hilo TCP, leidas por SDL_THREAD */
volatile uint64_t vg_bytes_total   = 0;
volatile uint64_t vg_bytes_ultimo  = 0;
volatile uint32_t vg_frames        = 0;
volatile uint8_t  vg_ultimo_opcode = 0;
volatile int      vg_conectado     = 0;

/* ================================================================
 * IMPLEMENTACIONES DE API DE SLOTS Y COLA
 * Definidas aqui (no inline en el header) para evitar reubicaciones
 * PIE: las funciones inline en headers que acceden a globals extern
 * producen DT_TEXTREL en binarios PIE con gcc -fcommon.
 * ================================================================ */

int fgn_slot_ultimo_activo(void) {
    for (int i = MAX_FGN_WINDOWS - 1; i >= 0; i--) {
        if (fgn_wins[i].activa) return i;
    }
    return -1;
}

int fgn_slot_reservar(void) {
    if (fgn_slots_libres == 0) return -1;
    int idx = __builtin_ctz(fgn_slots_libres);
    fgn_slots_libres &= ~(1u << idx);
    return idx;
}

void fgn_slot_liberar(int idx) {
    if ((uint32_t)idx < MAX_FGN_WINDOWS)
        fgn_slots_libres |= (1u << idx);
}

bool sdl_cmd_push(const SdlCmd *cmd) {
    unsigned head = __atomic_load_n(&sdl_cmd_queue.head, __ATOMIC_RELAXED);
    unsigned next = (head + 1) & FGN_CMD_QUEUE_MASK;
    if (next == __atomic_load_n(&sdl_cmd_queue.tail, __ATOMIC_ACQUIRE)) {
        printf("\x1b[33m[FGN] WARN: Cola SDL llena, cmd %d descartado.\x1b[0m\n",
               (int)cmd->tipo);
        return false;
    }
    sdl_cmd_queue.slots[head] = *cmd;
    __atomic_store_n(&sdl_cmd_queue.head, next, __ATOMIC_RELEASE);
    return true;
}

bool sdl_cmd_pop(SdlCmd *out) {
    unsigned tail = sdl_cmd_queue.tail;
    unsigned head = __atomic_load_n(&sdl_cmd_queue.head, __ATOMIC_ACQUIRE);
    if (tail == head) return false;
    *out = sdl_cmd_queue.slots[tail];
    __atomic_store_n(&sdl_cmd_queue.tail,
                     (tail + 1) & FGN_CMD_QUEUE_MASK,
                     __ATOMIC_RELEASE);
    return true;
}

/* ================================================================
 * ESTADO INTERNO DEL MODULO
 * ================================================================ */

static pthread_t  sdl_thread_id;
static pthread_t  flush_thread_id;
static volatile int sdl_thread_activo  = 0;
static volatile int flush_thread_activo = 0;

/* Senyal de shutdown para SDL_THREAD */
static volatile int sdl_shutdown_pedido = 0;

/* ================================================================
 * FUENTE BITMAP 5x7 — solo para el HUD (sin SDL_ttf)
 * Identica a la de acero_gl_legacy.c para coherencia visual.
 * Se declara aqui para que osiris_windows.c sea autocontenido.
 * ================================================================ */

static const uint8_t font5x7[][5] = {
    {0x00,0x00,0x00,0x00,0x00}, {0x00,0x00,0x5F,0x00,0x00},
    {0x00,0x07,0x00,0x07,0x00}, {0x14,0x7F,0x14,0x7F,0x14},
    {0x24,0x2A,0x7F,0x2A,0x12}, {0x23,0x13,0x08,0x64,0x62},
    {0x36,0x49,0x55,0x22,0x50}, {0x00,0x05,0x03,0x00,0x00},
    {0x00,0x1C,0x22,0x41,0x00}, {0x00,0x41,0x22,0x1C,0x00},
    {0x08,0x2A,0x1C,0x2A,0x08}, {0x08,0x08,0x3E,0x08,0x08},
    {0x00,0x50,0x30,0x00,0x00}, {0x08,0x08,0x08,0x08,0x08},
    {0x00,0x60,0x60,0x00,0x00}, {0x20,0x10,0x08,0x04,0x02},
    /* 0-9 */
    {0x3E,0x51,0x49,0x45,0x3E}, {0x00,0x42,0x7F,0x40,0x00},
    {0x42,0x61,0x51,0x49,0x46}, {0x21,0x41,0x45,0x4B,0x31},
    {0x18,0x14,0x12,0x7F,0x10}, {0x27,0x45,0x45,0x45,0x39},
    {0x3C,0x4A,0x49,0x49,0x30}, {0x01,0x71,0x09,0x05,0x03},
    {0x36,0x49,0x49,0x49,0x36}, {0x06,0x49,0x49,0x29,0x1E},
    /* :;<=>?@ */
    {0x00,0x36,0x36,0x00,0x00}, {0x00,0x56,0x36,0x00,0x00},
    {0x00,0x08,0x14,0x22,0x41}, {0x14,0x14,0x14,0x14,0x14},
    {0x41,0x22,0x14,0x08,0x00}, {0x02,0x01,0x51,0x09,0x06},
    {0x32,0x49,0x79,0x41,0x3E},
    /* A-Z */
    {0x7E,0x11,0x11,0x11,0x7E}, {0x7F,0x49,0x49,0x49,0x36},
    {0x3E,0x41,0x41,0x41,0x22}, {0x7F,0x41,0x41,0x22,0x1C},
    {0x7F,0x49,0x49,0x49,0x41}, {0x7F,0x09,0x09,0x09,0x01},
    {0x3E,0x41,0x41,0x51,0x32}, {0x7F,0x08,0x08,0x08,0x7F},
    {0x00,0x41,0x7F,0x41,0x00}, {0x20,0x40,0x41,0x3F,0x01},
    {0x7F,0x08,0x14,0x22,0x41}, {0x7F,0x40,0x40,0x40,0x40},
    {0x7F,0x02,0x04,0x02,0x7F}, {0x7F,0x04,0x08,0x10,0x7F},
    {0x3E,0x41,0x41,0x41,0x3E}, {0x7F,0x09,0x09,0x09,0x06},
    {0x3E,0x41,0x51,0x21,0x5E}, {0x7F,0x09,0x19,0x29,0x46},
    {0x46,0x49,0x49,0x49,0x31}, {0x01,0x01,0x7F,0x01,0x01},
    {0x3F,0x40,0x40,0x40,0x3F}, {0x1F,0x20,0x40,0x20,0x1F},
    {0x3F,0x40,0x38,0x40,0x3F}, {0x63,0x14,0x08,0x14,0x63},
    {0x07,0x08,0x70,0x08,0x07}, {0x61,0x51,0x49,0x45,0x43},
    /* [\]^_` */
    {0x00,0x7F,0x41,0x41,0x00}, {0x02,0x04,0x08,0x10,0x20},
    {0x00,0x41,0x41,0x7F,0x00}, {0x04,0x02,0x01,0x02,0x04},
    {0x40,0x40,0x40,0x40,0x40}, {0x00,0x01,0x02,0x04,0x00},
    /* a-z */
    {0x20,0x54,0x54,0x54,0x78}, {0x7F,0x48,0x44,0x44,0x38},
    {0x38,0x44,0x44,0x44,0x20}, {0x38,0x44,0x44,0x48,0x7F},
    {0x38,0x54,0x54,0x54,0x18}, {0x08,0x7E,0x09,0x01,0x02},
    {0x08,0x54,0x54,0x54,0x3C}, {0x7F,0x08,0x04,0x04,0x78},
    {0x00,0x44,0x7D,0x40,0x00}, {0x20,0x40,0x44,0x3D,0x00},
    {0x7F,0x10,0x28,0x44,0x00}, {0x00,0x41,0x7F,0x40,0x00},
    {0x7C,0x04,0x18,0x04,0x78}, {0x7C,0x08,0x04,0x04,0x78},
    {0x38,0x44,0x44,0x44,0x38}, {0x7C,0x14,0x14,0x14,0x08},
    {0x08,0x14,0x14,0x18,0x7C}, {0x7C,0x08,0x04,0x04,0x08},
    {0x48,0x54,0x54,0x54,0x20}, {0x04,0x3F,0x44,0x40,0x20},
    {0x3C,0x40,0x40,0x40,0x7C}, {0x1C,0x20,0x40,0x20,0x1C},
    {0x3C,0x40,0x30,0x40,0x3C}, {0x44,0x28,0x10,0x28,0x44},
    {0x0C,0x50,0x50,0x50,0x3C}, {0x44,0x64,0x54,0x4C,0x44},
    {0x00,0x08,0x36,0x41,0x00}, {0x00,0x00,0x7F,0x00,0x00},
    {0x00,0x41,0x36,0x08,0x00}, {0x08,0x04,0x08,0x10,0x08},
};

#define HUD_ESCALA      2
#define HUD_CHAR_W      (5 * HUD_ESCALA + HUD_ESCALA)
#define HUD_CHAR_H      (7 * HUD_ESCALA + 2)
#define HUD_W           320
#define HUD_H           110
#define HUD_MARGIN_R    8
#define HUD_MARGIN_T    8

static void hud_draw_char(SDL_Renderer *r, int x, int y, char c,
                          uint8_t cr, uint8_t cg, uint8_t cb) {
    if (c < 32 || c > 126) c = '?';
    const uint8_t *glyph = font5x7[(uint8_t)(c - 32)];
    SDL_SetRenderDrawColor(r, cr, cg, cb, 255);
    for (int col = 0; col < 5; col++) {
        uint8_t bits = glyph[col];
        for (int row = 0; row < 7; row++) {
            if (bits & (1 << row)) {
                SDL_Rect px = { x + col * HUD_ESCALA,
                                y + row * HUD_ESCALA,
                                HUD_ESCALA, HUD_ESCALA };
                SDL_RenderFillRect(r, &px);
            }
        }
    }
}

static void hud_draw_string(SDL_Renderer *r, int x, int y, const char *s,
                             uint8_t cr, uint8_t cg, uint8_t cb) {
    while (*s) {
        hud_draw_char(r, x, y, *s, cr, cg, cb);
        x += HUD_CHAR_W;
        s++;
    }
}

/* ================================================================
 * RENDER DEL HUD (ejecutado SOLO desde SDL_THREAD)
 * Lee las metricas volatiles y las pinta sobre el slot 0.
 * ================================================================ */
static void _hud_render_interno(void) {
    FgnWinEntry *hud = &fgn_wins[FGN_SLOT_HUD];
    if (!hud->activa || !hud->ren || !hud->visible) return;

    SDL_Renderer *r = hud->ren;

    /* Fondo */
    SDL_SetRenderDrawColor(r, 10, 10, 20, 220);
    SDL_RenderClear(r);

    /* Borde cyan doble */
    SDL_SetRenderDrawColor(r, 0, 180, 216, 255);
    SDL_Rect b0 = {0, 0, HUD_W, HUD_H};
    SDL_Rect b1 = {1, 1, HUD_W-2, HUD_H-2};
    SDL_RenderDrawRect(r, &b0);
    SDL_RenderDrawRect(r, &b1);

    /* Titulo */
    hud_draw_string(r, 6, 5, "V-GHOST ODS", 0, 180, 216);

    /* Linea separadora */
    SDL_SetRenderDrawColor(r, 40, 80, 100, 255);
    SDL_RenderDrawLine(r, 3, 20, HUD_W-4, 20);

    /* Calcular KB/s — basado en delta de bytes desde ultima llamada */
    static uint64_t bytes_prev   = 0;
    static time_t   t_prev       = 0;
    static double   kbps_cached  = 0.0;
    time_t ahora = time(NULL);
    double dt = difftime(ahora, t_prev);
    if (dt >= 1.0) {
        uint64_t total = vg_bytes_total;
        kbps_cached = ((double)(total - bytes_prev) / 1024.0) / dt;
        bytes_prev  = total;
        t_prev      = ahora;
    }

    char buf[64];
    int y = 24;
    const int col_lbl = 6;
    const int col_val = 100;

    /* RX Total */
    hud_draw_string(r, col_lbl, y, "RX TOTAL", 120, 180, 120);
    if (vg_bytes_total < 1024*1024)
        snprintf(buf, sizeof(buf), "%5llu KB",
                 (unsigned long long)(vg_bytes_total / 1024));
    else
        snprintf(buf, sizeof(buf), "%5.1f MB",
                 (double)vg_bytes_total / (1024.0*1024.0));
    hud_draw_string(r, col_val, y, buf, 180, 255, 180);
    y += HUD_CHAR_H;

    /* Velocidad */
    hud_draw_string(r, col_lbl, y, "VELOCIDAD", 120, 180, 120);
    if (kbps_cached >= 1024.0)
        snprintf(buf, sizeof(buf), "%5.1f MB/s", kbps_cached / 1024.0);
    else
        snprintf(buf, sizeof(buf), "%5.1f KB/s", kbps_cached);
    uint8_t vr = (kbps_cached < 50.0) ? 255 : 180;
    uint8_t vg = (kbps_cached < 50.0) ? 200 :  255;
    uint8_t vb = (kbps_cached < 50.0) ?   0 :  180;
    hud_draw_string(r, col_val, y, buf, vr, vg, vb);
    y += HUD_CHAR_H;

    /* Frames */
    hud_draw_string(r, col_lbl, y, "FRAMES", 120, 180, 120);
    snprintf(buf, sizeof(buf), "%8lu", (unsigned long)vg_frames);
    hud_draw_string(r, col_val, y, buf, 180, 255, 180);
    y += HUD_CHAR_H;

    /* Ultimo opcode */
    hud_draw_string(r, col_lbl, y, "OP", 120, 180, 120);
    snprintf(buf, sizeof(buf), "0x%02X  (%3u)",
             vg_ultimo_opcode, vg_ultimo_opcode);
    hud_draw_string(r, col_val, y, buf, 200, 200, 255);
    y += HUD_CHAR_H;

    /* Tiempo conectado */
    hud_draw_string(r, col_lbl, y, "T.CONN", 120, 180, 120);
    if (vg_conectado) {
        static time_t t_conexion = 0;
        if (t_conexion == 0) t_conexion = time(NULL);
        long seg = (long)difftime(ahora, t_conexion);
        snprintf(buf, sizeof(buf), "%02ld:%02ld:%02ld",
                 seg/3600, (seg%3600)/60, seg%60);
        hud_draw_string(r, col_val, y, buf, 180, 255, 180);
    } else {
        hud_draw_string(r, col_val, y, "OFFLINE", 255, 80, 80);
    }

    SDL_RenderPresent(r);
}

/* ================================================================
 * EJECUCION DE COMANDOS SDL
 * Toda esta funcion corre EXCLUSIVAMENTE en SDL_THREAD.
 * ================================================================ */

static void _ejecutar_cmd_crear(const SdlCmd *cmd) {
    uint8_t slot = cmd->slot;
    if (slot >= MAX_FGN_WINDOWS) return;

    FgnWinEntry *w = &fgn_wins[slot];

    /* Calcular posicion: slot 0 (HUD) va a esquina superior derecha */
    int pos_x = SDL_WINDOWPOS_CENTERED;
    int pos_y = SDL_WINDOWPOS_CENTERED;

    if (slot == FGN_SLOT_HUD) {
        SDL_DisplayMode dm;
        int screen_w = 1920; /* fallback */
        if (SDL_GetCurrentDisplayMode(0, &dm) == 0)
            screen_w = dm.w;
        pos_x = screen_w - HUD_W - HUD_MARGIN_R;
        pos_y = HUD_MARGIN_T;
    }

    /* Flags SDL segun flags FGN */
    uint32_t sdl_flags = SDL_WINDOW_SHOWN;
    if (cmd->crear.flags & FGN_WIN_FLAG_TOPMOST)    sdl_flags |= SDL_WINDOW_ALWAYS_ON_TOP;
    if (cmd->crear.flags & FGN_WIN_FLAG_BORDERLESS)  sdl_flags |= SDL_WINDOW_BORDERLESS;
    if (cmd->crear.flags & FGN_WIN_FLAG_FULLSCREEN)  sdl_flags |= SDL_WINDOW_FULLSCREEN_DESKTOP;

    w->win = SDL_CreateWindow(
        cmd->crear.titulo,
        pos_x, pos_y,
        cmd->crear.ancho, cmd->crear.alto,
        sdl_flags
    );
    if (!w->win) {
        printf("\x1b[31m[FGN] Error creando ventana slot %u: %s\x1b[0m\n",
               slot, SDL_GetError());
        fgn_slot_liberar(slot);
        return;
    }

    /* Renderer: acelerado con vsync; fallback a software */
    w->ren = SDL_CreateRenderer(w->win, -1,
                 SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!w->ren)
        w->ren = SDL_CreateRenderer(w->win, -1, SDL_RENDERER_SOFTWARE);

    if (!w->ren) {
        printf("\x1b[31m[FGN] Error creando renderer slot %u\x1b[0m\n", slot);
        SDL_DestroyWindow(w->win);
        w->win = NULL;
        fgn_slot_liberar(slot);
        return;
    }

    SDL_SetRenderDrawBlendMode(w->ren, SDL_BLENDMODE_BLEND);

    /* Textura de streaming para frames RGBA (solo si no es HUD) */
    if (slot != FGN_SLOT_HUD && cmd->crear.ancho > 0 && cmd->crear.alto > 0) {
        w->tex = SDL_CreateTexture(
            w->ren,
            SDL_PIXELFORMAT_ARGB8888,
            SDL_TEXTUREACCESS_STREAMING,
            cmd->crear.ancho,
            cmd->crear.alto
        );
    }

    /* Bloque DIAMANTE — payload de usuario para este slot.
     * Tamano inicial: 4 bytes por pixel (ARGB8888). */
    uint32_t tam_bloque = (uint32_t)cmd->crear.ancho * cmd->crear.alto * 4;
    if (tam_bloque == 0) tam_bloque = 4096; /* minimo para slots sin textura */
    w->bloque = crear_bloque(tam_bloque, DIAMANTE);

    if (!w->bloque.data) {
        printf("\x1b[31m[FGN] Error alocando bloque DIAMANTE slot %u\x1b[0m\n",
               slot);
        if (w->tex) { SDL_DestroyTexture(w->tex); w->tex = NULL; }
        SDL_DestroyRenderer(w->ren); w->ren = NULL;
        SDL_DestroyWindow(w->win);   w->win = NULL;
        fgn_slot_liberar(slot);
        return;
    }

    /* Fondo inicial oscuro */
    SDL_SetRenderDrawColor(w->ren, 0, 20, 40, 255);
    SDL_RenderClear(w->ren);
    SDL_RenderPresent(w->ren);

    /* Metadatos */
    /* memcpy + null explícito evita el warning -Wstringop-truncation
     * de strncpy cuando src y dst tienen el mismo tamaño máximo.
     * El campo cmd->crear.titulo ya viene terminado en null por fgn_win_crear(). */
    memcpy(w->titulo, cmd->crear.titulo, FGN_TITULO_MAX - 1);
    w->titulo[FGN_TITULO_MAX - 1] = '\0';
    w->ancho   = cmd->crear.ancho;
    w->alto    = cmd->crear.alto;
    w->flags   = cmd->crear.flags;
    w->activa  = true;
    w->visible = true;
    w->sdl_cierre_pendiente = false;

    printf("\x1b[32m[FGN] Ventana slot %u creada: '%s' (%ux%u)\x1b[0m\n",
           slot, w->titulo, w->ancho, w->alto);
}

static void _ejecutar_cmd_cerrar(uint8_t slot) {
    if (slot >= MAX_FGN_WINDOWS) return;

    FgnWinEntry *w = &fgn_wins[slot];
    if (!w->activa) return;

    /* Guardia: slot de sistema (HUD) no se puede destruir */
    if (w->flags & FGN_WIN_FLAG_SISTEMA) {
        printf("\x1b[33m[FGN] Slot %u es de sistema — cierre ignorado.\x1b[0m\n",
               slot);
        return;
    }

    /* ORDEN CRITICO (del manual OSIRIS):
     * a) Copiar punteros SDL al stack
     * b) Marcar inactivo y liberar slot del bitmap
     * c) rb_liberar() — zeroing DIAMANTE
     * d) SDL_Destroy* con punteros del stack */
    SDL_Texture  *tex = w->tex;
    SDL_Renderer *ren = w->ren;
    SDL_Window   *win = w->win;

    w->activa  = false;
    w->visible = false;
    w->sdl_cierre_pendiente = false;
    w->tex = NULL; w->ren = NULL; w->win = NULL;
    fgn_slot_liberar(slot);

    /* zeroing DIAMANTE garantizado */
    rb_liberar(&w->bloque);

    /* Destruir recursos SDL — orden inverso a la creacion */
    if (tex) SDL_DestroyTexture(tex);
    if (ren) SDL_DestroyRenderer(ren);
    if (win) SDL_DestroyWindow(win);

    printf("\x1b[33m[FGN] Slot %u cerrado y liberado.\x1b[0m\n", slot);
}

static void _ejecutar_cmd_overlay(const SdlCmd *cmd) {
    uint8_t slot = cmd->slot;
    if (!FGN_SLOT_VALIDO(slot)) return;

    FgnWinEntry *w = &fgn_wins[slot];
    if (!w->ren || !w->visible) return;

    /* Para el HUD usamos la fuente bitmap interna.
     * Para otros slots, el JS bridge puede registrar su propia funcion. */
    if (slot == FGN_SLOT_HUD) {
        hud_draw_string(w->ren,
                        cmd->overlay.x, cmd->overlay.y,
                        cmd->overlay.texto,
                        cmd->overlay.color[0],
                        cmd->overlay.color[1],
                        cmd->overlay.color[2]);
        SDL_RenderPresent(w->ren);
    } else {
        /* Llamada al driver activo para ventanas no-HUD */
        if (driver_activo.dibujar_overlay) {
            driver_activo.dibujar_overlay(
                cmd->overlay.texto,
                cmd->overlay.x,
                cmd->overlay.y
            );
        }
    }
}

static void _ejecutar_cmd_render_frame(const SdlCmd *cmd) {
    uint8_t slot = cmd->slot;
    if (!FGN_SLOT_VALIDO(slot)) return;

    FgnWinEntry *w = &fgn_wins[slot];
    if (!w->tex || !w->ren || !w->visible || !w->bloque.data) return;

    void *pixels;
    int   pitch;
    if (SDL_LockTexture(w->tex, NULL, &pixels, &pitch) == 0) {
        uint32_t bytes = cmd->frame.n_bytes;
        if (bytes > w->bloque.size) bytes = w->bloque.size;
        memcpy(pixels, w->bloque.data, bytes);
        SDL_UnlockTexture(w->tex);
        SDL_RenderCopy(w->ren, w->tex, NULL, NULL);
        SDL_RenderPresent(w->ren);
    }
}

/* ================================================================
 * PROCESADO DE EVENTOS SDL
 * Corre dentro del SDL_THREAD — unico punto donde SDL_PollEvent
 * es seguro segun la documentacion de SDL2.
 * ================================================================ */
static void _procesar_eventos_sdl(void) {
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) {
            /* Intentamos identificar que ventana genero el QUIT */
            uint32_t win_id = 0;
            if (e.type == SDL_WINDOWEVENT)
                win_id = e.window.windowID;

            /* Marcar todos los slots con ventana como pendientes
             * si tienen flag PERSISTENTE, o como cerrar si no */
            for (int i = 0; i < MAX_FGN_WINDOWS; i++) {
                if (!fgn_wins[i].activa || !fgn_wins[i].win) continue;
                if (win_id && SDL_GetWindowID(fgn_wins[i].win) != win_id)
                    continue;

                if (fgn_wins[i].flags & FGN_WIN_FLAG_PERSISTENTE) {
                    SDL_HideWindow(fgn_wins[i].win);
                    fgn_wins[i].visible = false;
                    printf("\x1b[33m[FGN] Slot %d: persistencia silenciosa.\x1b[0m\n", i);
                } else if (!(fgn_wins[i].flags & FGN_WIN_FLAG_SISTEMA)) {
                    fgn_wins[i].sdl_cierre_pendiente = true;
                }
            }
        }

        if (e.type == SDL_WINDOWEVENT &&
            e.window.event == SDL_WINDOWEVENT_CLOSE) {
            /* Buscar el slot por SDL_Window ID */
            uint32_t wid = e.window.windowID;
            for (int i = 0; i < MAX_FGN_WINDOWS; i++) {
                if (!fgn_wins[i].activa || !fgn_wins[i].win) continue;
                if (SDL_GetWindowID(fgn_wins[i].win) != wid) continue;

                if (fgn_wins[i].flags & FGN_WIN_FLAG_SISTEMA) {
                    /* HUD: nunca cerrar — solo ocultar */
                    SDL_HideWindow(fgn_wins[i].win);
                    fgn_wins[i].visible = false;
                    printf("\x1b[33m[FGN] HUD oculto. Persistencia activa.\x1b[0m\n");
                } else if (fgn_wins[i].flags & FGN_WIN_FLAG_PERSISTENTE) {
                    SDL_HideWindow(fgn_wins[i].win);
                    fgn_wins[i].visible = false;
                } else {
                    fgn_wins[i].sdl_cierre_pendiente = true;
                }
                break;
            }
        }
    }
}

/* ================================================================
 * SDL_THREAD — unico consumidor de sdl_cmd_queue
 * ================================================================ */
static void* _sdl_thread(void *arg) {
    (void)arg;
    SdlCmd cmd;

    printf("\x1b[36m[FGN] SDL_THREAD arrancado.\x1b[0m\n");

    while (!sdl_shutdown_pedido) {
        /* 1. Procesar eventos de ventana */
        _procesar_eventos_sdl();

        /* 2. Drenar la cola de comandos */
        while (sdl_cmd_pop(&cmd)) {
            switch (cmd.tipo) {
                case SDL_CMD_WIN_CREAR:
                    _ejecutar_cmd_crear(&cmd);
                    break;
                case SDL_CMD_WIN_CERRAR:
                    _ejecutar_cmd_cerrar(cmd.slot);
                    break;
                case SDL_CMD_WIN_MOSTRAR:
                    if (FGN_SLOT_VALIDO(cmd.slot) && fgn_wins[cmd.slot].win) {
                        SDL_ShowWindow(fgn_wins[cmd.slot].win);
                        fgn_wins[cmd.slot].visible = true;
                    }
                    break;
                case SDL_CMD_WIN_OCULTAR:
                    if (FGN_SLOT_VALIDO(cmd.slot) && fgn_wins[cmd.slot].win) {
                        SDL_HideWindow(fgn_wins[cmd.slot].win);
                        fgn_wins[cmd.slot].visible = false;
                    }
                    break;
                case SDL_CMD_RENDER_HUD:
                    _hud_render_interno();
                    break;
                case SDL_CMD_RENDER_FRAME:
                    _ejecutar_cmd_render_frame(&cmd);
                    break;
                case SDL_CMD_OVERLAY_TXT:
                    _ejecutar_cmd_overlay(&cmd);
                    break;
                case SDL_CMD_SHUTDOWN:
                    sdl_shutdown_pedido = 1;
                    break;
                default:
                    break;
            }
        }

        /* 3. Re-render del HUD a ~60fps si esta activo y visible */
        if (fgn_wins[FGN_SLOT_HUD].activa &&
            fgn_wins[FGN_SLOT_HUD].visible) {
            _hud_render_interno();
        }

        SDL_Delay(16); /* ~60fps */
    }

    /* Cierre ordenado: destruir todos los slots activos */
    for (int i = MAX_FGN_WINDOWS - 1; i >= 0; i--) {
        if (fgn_wins[i].activa) {
            /* Forzar cierre incluso de slots de sistema al shutdown */
            fgn_wins[i].flags &= ~FGN_WIN_FLAG_SISTEMA;
            _ejecutar_cmd_cerrar((uint8_t)i);
        }
    }

    SDL_Quit();
    printf("\x1b[33m[FGN] SDL_THREAD terminado.\x1b[0m\n");
    return NULL;
}

/* ================================================================
 * FLUSH_THREAD — detecta cierres pendientes cada 50ms
 * Separa la deteccion del evento SDL_QUIT del cierre real,
 * evitando el segfault clasico de X11 al destruir ventanas
 * dentro de SDL_PollEvent.
 * ================================================================ */
static void* _flush_thread(void *arg) {
    (void)arg;
    struct timespec ts = { .tv_sec = 0, .tv_nsec = FGN_FLUSH_INTERVAL_MS * 1000000L };

    printf("\x1b[36m[FGN] FLUSH_THREAD arrancado (intervalo %dms).\x1b[0m\n",
           FGN_FLUSH_INTERVAL_MS);

    while (sdl_thread_activo) {
        nanosleep(&ts, NULL);

        for (int i = 0; i < MAX_FGN_WINDOWS; i++) {
            if (fgn_wins[i].activa && fgn_wins[i].sdl_cierre_pendiente) {
                /* Encolar el cierre real — lo ejecuta SDL_THREAD */
                SdlCmd cmd = { .tipo = SDL_CMD_WIN_CERRAR, .slot = (uint8_t)i };
                if (!sdl_cmd_push(&cmd)) {
                    /* Cola llena — limpiar el flag para reintentar en el siguiente tick */
                    printf("\x1b[33m[FGN] FLUSH: cola llena, reintento slot %d\x1b[0m\n",
                           i);
                }
                /* El flag se limpia en _ejecutar_cmd_cerrar */
            }
        }
    }

    printf("\x1b[33m[FGN] FLUSH_THREAD terminado.\x1b[0m\n");
    return NULL;
}

/* ================================================================
 * API PUBLICA
 * ================================================================ */

int fgn_windows_iniciar(void) {
    /* Inicializar SDL una sola vez */
    if (SDL_WasInit(SDL_INIT_VIDEO) == 0) {
        if (SDL_Init(SDL_INIT_VIDEO) < 0) {
            printf("\x1b[31m[FGN] Error iniciando SDL: %s\x1b[0m\n",
                   SDL_GetError());
            return -1;
        }
    }

    /* Bitmap inicial: todos los slots libres excepto slot 0 (HUD) */
    fgn_slots_libres = 0xFFFFFFFEu;
    memset(fgn_wins, 0, sizeof(fgn_wins));
    memset(&sdl_cmd_queue, 0, sizeof(sdl_cmd_queue));

    /* Arrancar SDL_THREAD primero — necesita estar activo antes del HUD */
    sdl_thread_activo   = 1;
    sdl_shutdown_pedido = 0;
    if (pthread_create(&sdl_thread_id, NULL, _sdl_thread, NULL) != 0) {
        printf("\x1b[31m[FGN] Error creando SDL_THREAD\x1b[0m\n");
        return -1;
    }

    /* Arrancar FLUSH_THREAD */
    flush_thread_activo = 1;
    if (pthread_create(&flush_thread_id, NULL, _flush_thread, NULL) != 0) {
        printf("\x1b[31m[FGN] Error creando FLUSH_THREAD\x1b[0m\n");
        sdl_thread_activo = 0;
        return -1;
    }

    /* Crear el HUD en slot 0 — reservado, sistema, siempre visible,
     * siempre encima, sin borde. */
    int slot = fgn_win_crear(
        FGN_SLOT_HUD,
        HUD_W, HUD_H,
        "V-GHOST ODS",
        FGN_WIN_FLAG_SISTEMA   |
        FGN_WIN_FLAG_TOPMOST   |
        FGN_WIN_FLAG_BORDERLESS
    );

    if (slot != FGN_SLOT_HUD) {
        printf("\x1b[31m[FGN] Error: HUD no pudo crearse en slot 0\x1b[0m\n");
        return -1;
    }

    printf("\x1b[32m[FGN] Sistema de ventanas FGN inicializado. "
           "HUD en slot 0. Slots disponibles: %u\x1b[0m\n",
           MAX_FGN_WINDOWS - 1);
    return 0;
}

void fgn_windows_cerrar(void) {
    /* Detener FLUSH_THREAD primero — ya no generara mas cierres */
    flush_thread_activo = 0;
    pthread_join(flush_thread_id, NULL);

    /* Encolar shutdown al SDL_THREAD y esperar */
    SdlCmd cmd_shutdown = { .tipo = SDL_CMD_SHUTDOWN };
    sdl_cmd_push(&cmd_shutdown);
    sdl_thread_activo = 0;
    pthread_join(sdl_thread_id, NULL);

    printf("\x1b[33m[FGN] Sistema de ventanas cerrado.\x1b[0m\n");
}

int fgn_win_crear(int slot, uint16_t ancho, uint16_t alto,
                  const char *titulo, uint32_t flags) {
    /* Si slot == -1, reservar el siguiente libre */
    if (slot < 0) {
        slot = fgn_slot_reservar();
        if (slot < 0) {
            printf("\x1b[31m[FGN] Sin slots disponibles "
                   "(MAX_FGN_WINDOWS=%d)\x1b[0m\n", MAX_FGN_WINDOWS);
            return -1;
        }
    } else if ((uint32_t)slot >= MAX_FGN_WINDOWS) {
        return -1;
    } else {
        /* Slot explicito: marcarlo como ocupado en el bitmap */
        fgn_slots_libres &= ~(1u << slot);
    }

    SdlCmd cmd = {
        .tipo = SDL_CMD_WIN_CREAR,
        .slot = (uint8_t)slot,
    };
    cmd.crear.ancho = ancho;
    cmd.crear.alto  = alto;
    cmd.crear.flags = flags;
    strncpy(cmd.crear.titulo, titulo ? titulo : "FGN",
            FGN_TITULO_MAX - 1);
    cmd.crear.titulo[FGN_TITULO_MAX - 1] = '\0';

    if (!sdl_cmd_push(&cmd)) {
        fgn_slot_liberar(slot);
        return -1;
    }
    return slot;
}

void fgn_win_cerrar(int slot) {
    if (!FGN_SLOT_VALIDO(slot)) return;

    /* Slots de sistema no se pueden cerrar desde el API publica */
    if (fgn_wins[slot].flags & FGN_WIN_FLAG_SISTEMA) {
        printf("\x1b[33m[FGN] fgn_win_cerrar: slot %d es de sistema.\x1b[0m\n",
               slot);
        return;
    }

    SdlCmd cmd = { .tipo = SDL_CMD_WIN_CERRAR, .slot = (uint8_t)slot };
    sdl_cmd_push(&cmd);
}

void fgn_win_overlay(int slot, int16_t x, int16_t y,
                     const char *texto, uint8_t color[4]) {
    if (slot < 0) slot = fgn_slot_ultimo_activo();
    if (!FGN_SLOT_VALIDO(slot)) return;

    SdlCmd cmd = {
        .tipo = SDL_CMD_OVERLAY_TXT,
        .slot = (uint8_t)slot,
    };
    cmd.overlay.x = x;
    cmd.overlay.y = y;
    if (color) {
        cmd.overlay.color[0] = color[0];
        cmd.overlay.color[1] = color[1];
        cmd.overlay.color[2] = color[2];
        cmd.overlay.color[3] = color[3];
    } else {
        /* Default: verde FGN */
        cmd.overlay.color[0] = 0;
        cmd.overlay.color[1] = 255;
        cmd.overlay.color[2] = 180;
        cmd.overlay.color[3] = 255;
    }
    strncpy(cmd.overlay.texto, texto ? texto : "",
            FGN_OVERLAY_TEXT_MAX - 1);
    cmd.overlay.texto[FGN_OVERLAY_TEXT_MAX - 1] = '\0';

    sdl_cmd_push(&cmd);
}

void fgn_hud_render(void) {
    SdlCmd cmd = { .tipo = SDL_CMD_RENDER_HUD, .slot = FGN_SLOT_HUD };
    sdl_cmd_push(&cmd);
}