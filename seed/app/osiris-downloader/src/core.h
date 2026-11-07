#ifndef OSIRIS_CORE_H
#define OSIRIS_CORE_H
#include <pthread.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <sys/types.h>
#include "safe.h"

#define FORMAT_COUNT 9
#define BROWSER_COUNT 9
extern const char *const FORMAT_NAMES[FORMAT_COUNT];
extern const char *const BROWSER_NAMES[BROWSER_COUNT];

typedef struct {
    char ytdlp[512], outdir[512], rate[32], tmpl[256], proxy[256], ua[256], playlist[48], custom[512];
    int format, browser, max_par;
    bool audio_only, thumb, meta;
} Options;

typedef enum { DL_QUEUED, DL_RUNNING, DL_DONE, DL_ERROR, DL_CANCELLED } DlState;
typedef struct { DlState state; float pct; char speed[32], eta[32], status[128]; } DlSnap;

typedef struct Download {
    int id;
    char *url;
    pthread_mutex_t mu;           /* protege los campos de progreso */
    DlState state;
    float pct;
    char speed[32], eta[32], status[128], last_err[128];
    pid_t pid;
    pthread_t th;
    bool started;
    atomic_bool cancel;
    Options opt;                  /* copia de las opciones al iniciar */
} Download;

/* Opciones y persistencia */
void options_defaults(Options *o);
void settings_path(char *out, size_t n);
bool options_load(Options *o, const char *path);
bool options_save(const Options *o, const char *path);
bool ytdlp_detect(Options *o);

/* Descargas */
Download *dl_new(const char *url);
bool dl_start(Download *d, const Options *o);
void dl_cancel(Download *d);
void dl_join(Download *d);
void dl_requeue(Download *d);
void dl_free(Download *d);
void dl_snapshot(Download *d, DlSnap *s);

/* Registro global thread-safe */
void log_push(const char *fmt, ...);
int  log_count(void);
bool log_get(int i, char *out, size_t cap);
void log_clear(void);

void open_path(const char *path);
#endif
