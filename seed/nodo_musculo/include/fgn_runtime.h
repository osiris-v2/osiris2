/* ================================================================
 * PROYECTO OSIRIS - fgn_runtime.h
 * NUCLEO DE VENTANAS FGN Y COLA MPSC SDL
 *
 * FILOSOFIA:
 *   Toda ventana es un bloque DIAMANTE en fgn_wins[].
 *   Ningun modulo crea ventanas SDL directamente — toda creacion,
 *   destruccion y render pasa por este contrato.
 *   El SDL_THREAD es el UNICO consumidor de SDL_CMD_*.
 *   El FLUSH_THREAD detecta cierres y encola limpiezas cada 50ms.
 *
 * ESCALADO FGN:
 *   - Slots: actualmente 32 (bitmap uint32_t).
 *     Para 64 slots: cambiar a uint64_t sin tocar el resto.
 *   - Cola MPSC: 64 slots de ring buffer sin locks en path caliente.
 *     Para mayor throughput: aumentar FGN_CMD_QUEUE_SIZE a potencia de 2.
 *   - FgnWinEntry lleva RB_SafePtr DIAMANTE — ciclo de vida auditado.
 *
 * SEGURIDAD:
 *   - slot_id siempre validado con FGN_SLOT_VALIDO() antes de acceder.
 *   - El HUD (slot 0) es reservado — solo fgn_hud_render() lo escribe.
 *   - FGN_WIN_FLAG_PERSISTENTE: intercepta SDL_QUIT, no cierra.
 *   - SDL_CMD_WIN_CERRAR se genera SOLO por el FLUSH_THREAD tras
 *     detectar sdl_cierre_pendiente — nunca desde un hilo TCP.
 *
 * MODULOS QUE INCLUYEN ESTE HEADER:
 *   main.c, sdl_core.c, acero_gl_legacy.c, osiris_windows.c
 *
 * DUREZA 256 - ASCII PURO
 * ================================================================ */

#ifndef FGN_RUNTIME_H
#define FGN_RUNTIME_H

#include <stdint.h>
#include <stdbool.h>
#include <SDL2/SDL.h>
#include "rb_csp.h"

/* ================================================================
 * LIMITES DEL SISTEMA
 * ================================================================ */

/* Numero maximo de ventanas SDL simultaneas.
 * Cambiar a uint64_t + 64 para doblar capacidad sin mas cambios. */
#define MAX_FGN_WINDOWS     32

/* Slots reservados por el sistema (no accesibles via ODS): */
#define FGN_SLOT_HUD        0   /* V-Ghost HUD — siempre activo */

/* Capacidad de la cola MPSC. DEBE ser potencia de 2. */
#define FGN_CMD_QUEUE_SIZE  64
#define FGN_CMD_QUEUE_MASK  (FGN_CMD_QUEUE_SIZE - 1)

/* Intervalo del FLUSH_THREAD en milisegundos. */
#define FGN_FLUSH_INTERVAL_MS  50

/* Tamaño maximo del titulo de una ventana FGN. */
#define FGN_TITULO_MAX      64

/* Longitud maxima de texto en un comando overlay. */
#define FGN_OVERLAY_TEXT_MAX 128

/* ================================================================
 * FLAGS DE VENTANA
 * ================================================================ */

/* La ventana intercepta SDL_QUIT en lugar de cerrar (persistencia). */
#define FGN_WIN_FLAG_PERSISTENTE    (1u << 0)

/* La ventana tiene siempre el foco sobre otras (SDL_WINDOW_ALWAYS_ON_TOP). */
#define FGN_WIN_FLAG_TOPMOST        (1u << 1)

/* La ventana no tiene bordes (SDL_WINDOW_BORDERLESS). */
#define FGN_WIN_FLAG_BORDERLESS     (1u << 2)

/* La ventana arranca en fullscreen (SDL_WINDOW_FULLSCREEN_DESKTOP). */
#define FGN_WIN_FLAG_FULLSCREEN     (1u << 3)

/* Slot reservado para uso del sistema — el ODS no puede cerrarlo. */
#define FGN_WIN_FLAG_SISTEMA        (1u << 4)

/* ================================================================
 * ENTRADA DE VENTANA (FgnWinEntry)
 *
 * Una entrada ocupa exactamente un slot en fgn_wins[].
 * El bloque DIAMANTE garantiza zeroing al liberar — los punteros
 * SDL (win, ren, tex) se almacenan aparte; el bloque es el
 * contenedor de datos de usuario (frame RGBA, overlay, etc.)
 * ================================================================ */
typedef struct {
    /* Identificadores SDL — acceso SOLO desde SDL_THREAD */
    SDL_Window   *win;
    SDL_Renderer *ren;
    SDL_Texture  *tex;          /* Textura de streaming ARGB8888 */

    /* Metadatos del slot */
    char          titulo[FGN_TITULO_MAX];
    uint16_t      ancho;
    uint16_t      alto;
    uint32_t      flags;        /* OR de FGN_WIN_FLAG_* */

    /* Estado de ciclo de vida */
    bool          activa;       /* true = slot ocupado */
    bool          visible;      /* false = oculta (persistencia silenciosa) */
    volatile bool sdl_cierre_pendiente; /* SDL_QUIT capturado, esperando FLUSH */

    /* Bloque DIAMANTE — datos del frame / overlay asociados al slot.
     * zeroing garantizado al llamar rb_liberar(). */
    RB_SafePtr    bloque;

} FgnWinEntry;

/* ================================================================
 * TABLA DE VENTANAS Y BITMAP DE SLOTS LIBRES
 *
 * fgn_wins[]        — array global de slots.
 * fgn_slots_libres  — bitmap: bit i = 1 si slot i esta libre.
 *                     Slot 0 (HUD) siempre ocupado tras init.
 *
 * ACCESO:
 *   Escritura: solo SDL_THREAD o seccion critica protegida.
 *   Lectura de 'activa': cualquier hilo (volatile bool basta aqui).
 * ================================================================ */
extern FgnWinEntry fgn_wins[MAX_FGN_WINDOWS];
extern uint32_t    fgn_slots_libres;   /* bitmap: 1 = libre */

/* Macro de validacion — usar ANTES de cualquier acceso a fgn_wins[i] */
#define FGN_SLOT_VALIDO(i) \
    ((uint32_t)(i) < MAX_FGN_WINDOWS && fgn_wins[(i)].activa)

/* Las siguientes funciones se implementan en osiris_windows.c
 * para evitar reubicaciones PIE desde .text al acceder a los
 * globals fgn_wins[] y fgn_slots_libres desde funciones inline. */

/* Encontrar el slot activo mas reciente. Devuelve -1 si ninguno. */
int  fgn_slot_ultimo_activo(void);

/* Reservar el siguiente slot libre en el bitmap.
 * Devuelve el indice, o -1 si todos ocupados. */
int  fgn_slot_reservar(void);

/* Liberar un slot en el bitmap. */
void fgn_slot_liberar(int idx);

/* ================================================================
 * COLA MPSC SDL (Multiple Producers, Single Consumer)
 *
 * Productores: hilo TCP, hilo ODS, FLUSH_THREAD (para cierres).
 * Consumidor unico: SDL_THREAD.
 *
 * Implementacion: ring buffer de 64 slots con atomic head/tail.
 * Sin mutex en el path caliente — solo atomic_uint.
 *
 * Si la cola se llena, el comando se descarta con log de warning.
 * Para mayor capacidad: aumentar FGN_CMD_QUEUE_SIZE.
 * ================================================================ */

/* Tipos de comando SDL */
typedef enum {
    SDL_CMD_NOP         = 0,  /* Sin operacion — slot vacio */
    SDL_CMD_WIN_CREAR   = 1,  /* Crear ventana en slot */
    SDL_CMD_WIN_CERRAR  = 2,  /* Destruir ventana de slot */
    SDL_CMD_WIN_MOSTRAR = 3,  /* SDL_ShowWindow */
    SDL_CMD_WIN_OCULTAR = 4,  /* SDL_HideWindow */
    SDL_CMD_RENDER_HUD  = 5,  /* Re-render del HUD (slot 0) */
    SDL_CMD_RENDER_FRAME= 6,  /* Frame RGBA directo a textura */
    SDL_CMD_OVERLAY_TXT = 7,  /* Texto sobre ventana via JS bridge */
    SDL_CMD_SHUTDOWN    = 8,  /* Apagado ordenado del SDL_THREAD */
} SdlCmdTipo;

/* Payload del comando — union para mantener el struct pequeno (cache-friendly).
 * Todos los campos que el SDL_THREAD necesita para ejecutar sin releer memoria. */
typedef struct {
    SdlCmdTipo tipo;
    uint8_t    slot;           /* Slot destino [0..MAX_FGN_WINDOWS-1] */
    union {
        /* SDL_CMD_WIN_CREAR */
        struct {
            uint16_t ancho;
            uint16_t alto;
            uint32_t flags;    /* OR de FGN_WIN_FLAG_* */
            char     titulo[FGN_TITULO_MAX];
        } crear;

        /* SDL_CMD_RENDER_FRAME */
        struct {
            uint32_t n_bytes;  /* Bytes validos en el bloque del slot */
        } frame;

        /* SDL_CMD_OVERLAY_TXT */
        struct {
            int16_t  x;
            int16_t  y;
            uint8_t  color[4]; /* RGBA */
            char     texto[FGN_OVERLAY_TEXT_MAX];
        } overlay;
    };
} SdlCmd;

/* Ring buffer de la cola */
typedef struct {
    SdlCmd   slots[FGN_CMD_QUEUE_SIZE];
    unsigned head;   /* escribe el productor (atomic) */
    unsigned tail;   /* lee el SDL_THREAD (no necesita atomic — unico consumidor) */
} SdlCmdQueue;

extern SdlCmdQueue sdl_cmd_queue;

/* Encolar un comando (thread-safe para multiples productores).
 * Devuelve true si se encolo, false si la cola estaba llena.
 * Implementada en osiris_windows.c — no inline para evitar
 * reubicaciones PIE al referenciar sdl_cmd_queue desde .text. */
bool sdl_cmd_push(const SdlCmd *cmd);

/* Leer el siguiente comando. Solo llamar desde SDL_THREAD.
 * Devuelve true si habia un comando, false si la cola estaba vacia.
 * Implementada en osiris_windows.c. */
bool sdl_cmd_pop(SdlCmd *out);

/* ================================================================
 * API PUBLICA DE VENTANAS
 * (implementada en osiris_windows.c)
 * ================================================================ */

/* Inicializa SDL, crea el HUD en slot 0 y arranca SDL_THREAD y FLUSH_THREAD.
 * Llamar UNA vez desde main() antes del bucle TCP.
 * Devuelve 0 en exito, -1 en error critico. */
int  fgn_windows_iniciar(void);

/* Cierre ordenado: encola SDL_CMD_SHUTDOWN y espera a que el SDL_THREAD termine.
 * Llamar desde main() en la ruta de salida. */
void fgn_windows_cerrar(void);

/* Encola SDL_CMD_WIN_CREAR para el slot indicado.
 * Si slot == -1, reserva el siguiente libre automaticamente.
 * Devuelve el slot asignado, o -1 si no hay slots disponibles. */
int  fgn_win_crear(int slot, uint16_t ancho, uint16_t alto,
                   const char *titulo, uint32_t flags);

/* Encola SDL_CMD_WIN_CERRAR para el slot indicado.
 * Si el slot tiene FGN_WIN_FLAG_SISTEMA, la llamada es ignorada. */
void fgn_win_cerrar(int slot);

/* Encola un overlay de texto para el slot activo (o slot explicito). */
void fgn_win_overlay(int slot, int16_t x, int16_t y,
                     const char *texto, uint8_t color[4]);

/* Renderiza el HUD V-Ghost (slot 0) con las metricas actuales.
 * Encola SDL_CMD_RENDER_HUD — no bloquea. */
void fgn_hud_render(void);

/* ================================================================
 * TABLA DE HANDLERS (h_table) — base del namespace FGN
 *
 * Cada handler es un bloque de memoria gestionado con RB_SafePtr.
 * La h_table es el precursor del sistema de modulos del lenguaje.
 * MAX_HANDLERS = 1024 por compatibilidad con sdl_core.c existente.
 * ================================================================ */

#define MAX_HANDLERS    1024

typedef struct {
    RB_SafePtr  bloque;         /* Memoria del handler */
    void       *base_fisica;    /* Acceso directo para DMA / memcpy */
    uint32_t    tamano_total;   /* Bytes del bloque */
    bool        activo;
} OsirisHandler;

extern OsirisHandler h_table[MAX_HANDLERS];

/* ================================================================
 * METRICAS V-GHOST HUD
 *
 * Escritas desde el hilo TCP (volatile), leidas desde SDL_THREAD.
 * No necesitan mutex — son contadores acumulativos; una lectura
 * ligeramente desincronizada no afecta a la correccion del HUD.
 * ================================================================ */
extern volatile uint64_t vg_bytes_total;    /* Bytes RX acumulados */
extern volatile uint64_t vg_bytes_ultimo;   /* Bytes en ventana actual */
extern volatile uint32_t vg_frames;         /* Frames OP_STREAM procesados */
extern volatile uint8_t  vg_ultimo_opcode;  /* Ultimo opcode recibido */
extern volatile int      vg_conectado;      /* 1 = enlace activo */

#endif /* FGN_RUNTIME_H */