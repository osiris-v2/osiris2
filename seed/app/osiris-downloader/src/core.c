/* core.c - opciones, registro, detección de yt-dlp y trabajadores de descarga. */
#define _GNU_SOURCE
#include "core.h"
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <spawn.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

extern char **environ;

const char *const FORMAT_NAMES[FORMAT_COUNT] = {
    "mejor (auto)", "mp4", "mkv", "webm",
    "mp3 (audio)", "m4a (audio)", "opus (audio)", "flac (audio)", "wav (audio)"};
static const char *const FORMAT_ARG[FORMAT_COUNT] = {
    NULL, "mp4", "mkv", "webm", "mp3", "m4a", "opus", "flac", "wav"};
const char *const BROWSER_NAMES[BROWSER_COUNT] = {
    "ninguno", "firefox", "chrome", "chromium", "brave", "edge", "opera", "vivaldi", "safari"};

/* ------------------------------------------------------------------ registro */
#define LOG_MAX 2000
#define LOG_LEN 512
static char g_log[LOG_MAX][LOG_LEN];
static int g_head, g_n;
static pthread_mutex_t g_logmu = PTHREAD_MUTEX_INITIALIZER;

void log_push(const char *fmt, ...) {
    char tmp[LOG_LEN - 32];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(tmp, sizeof tmp, fmt, ap);
    va_end(ap);
    time_t t = time(NULL);
    struct tm tv;
    localtime_r(&t, &tv);
    char ts[16];
    strftime(ts, sizeof ts, "%H:%M:%S", &tv);
    pthread_mutex_lock(&g_logmu);
    int idx = (g_head + g_n) % LOG_MAX;
    if (g_n == LOG_MAX) { idx = g_head; g_head = (g_head + 1) % LOG_MAX; } else g_n++;
    snprintf(g_log[idx], LOG_LEN, "[%s] %s", ts, tmp);
    pthread_mutex_unlock(&g_logmu);
}
int log_count(void) {
    pthread_mutex_lock(&g_logmu);
    int n = g_n;
    pthread_mutex_unlock(&g_logmu);
    return n;
}
bool log_get(int i, char *out, size_t cap) {
    bool ok = false;
    pthread_mutex_lock(&g_logmu);
    if (i >= 0 && i < g_n) { safe_strlcpy(out, g_log[(g_head + i) % LOG_MAX], cap); ok = true; }
    pthread_mutex_unlock(&g_logmu);
    return ok;
}
void log_clear(void) {
    pthread_mutex_lock(&g_logmu);
    g_head = g_n = 0;
    pthread_mutex_unlock(&g_logmu);
}

/* ------------------------------------------------------------------ opciones */
#define STR_FIELDS(X) X(ytdlp) X(outdir) X(rate) X(tmpl) X(proxy) X(ua) X(playlist) X(custom)
#define INT_FIELDS(X) X(format) X(browser) X(max_par)
#define BOOL_FIELDS(X) X(audio_only) X(thumb) X(meta)

void options_defaults(Options *o) {
    memset(o, 0, sizeof *o);
    const char *home = getenv("HOME");
    char dl[512];
    struct stat st;
    snprintf(dl, sizeof dl, "%s/Downloads", home ? home : ".");
    safe_strlcpy(o->outdir, (stat(dl, &st) == 0 && S_ISDIR(st.st_mode)) ? dl : ".", sizeof o->outdir);
    o->max_par = 2;
    o->meta = true;
}

void settings_path(char *out, size_t n) {
    const char *xdg = getenv("XDG_CONFIG_HOME"), *home = getenv("HOME");
    if (xdg && *xdg) snprintf(out, n, "%s/osiris-downloader/settings.ini", xdg);
    else snprintf(out, n, "%s/.config/osiris-downloader/settings.ini", home ? home : ".");
}

static void mkdir_parent(const char *file) {
    char tmp[512];
    safe_strlcpy(tmp, file, sizeof tmp);
    for (char *p = tmp + 1; *p; p++)
        if (*p == '/') { *p = 0; mkdir(tmp, 0755); *p = '/'; }
}

bool options_save(const Options *o, const char *path) {
    mkdir_parent(path);
    FILE *f = fopen(path, "w");
    if (!f) return false;
#define S(n) fprintf(f, #n "=%s\n", o->n);
    STR_FIELDS(S)
#undef S
#define I(n) fprintf(f, #n "=%d\n", (int)o->n);
    INT_FIELDS(I) BOOL_FIELDS(I)
#undef I
    return fclose(f) == 0;
}

bool options_load(Options *o, const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) return false;
    char line[1024];
    while (fgets(line, sizeof line, f)) {
        line[strcspn(line, "\r\n")] = 0;
        char *eq = strchr(line, '=');
        if (!eq) continue;
        *eq = 0;
        const char *k = line, *v = eq + 1;
#define S(n) if (!strcmp(k, #n)) safe_strlcpy(o->n, v, sizeof o->n); else
#define I(n) if (!strcmp(k, #n)) o->n = atoi(v); else
#define B(n) if (!strcmp(k, #n)) o->n = atoi(v) != 0; else
        STR_FIELDS(S) INT_FIELDS(I) BOOL_FIELDS(B) { }
#undef S
#undef I
#undef B
    }
    fclose(f);
    if (o->format < 0 || o->format >= FORMAT_COUNT) o->format = 0;
    if (o->browser < 0 || o->browser >= BROWSER_COUNT) o->browser = 0;
    if (o->max_par < 1) o->max_par = 1;
    if (o->max_par > 8) o->max_par = 8;
    return true;
}

static bool is_exec(const char *p) {
    struct stat st;
    return stat(p, &st) == 0 && S_ISREG(st.st_mode) && access(p, X_OK) == 0;
}

/* Prioridad: ruta del usuario > PATH > ubicaciones habituales (pip, venv, brew). */
bool ytdlp_detect(Options *o) {
    if (o->ytdlp[0] && is_exec(o->ytdlp)) return true;
    char c[1024];
    const char *path = getenv("PATH");
    if (path) {
        safe_ptr(char) cp = safe_strdup(path);
        char *sv = NULL;
        for (char *d = strtok_r(cp, ":", &sv); d; d = strtok_r(NULL, ":", &sv)) {
            snprintf(c, sizeof c, "%s/yt-dlp", d);
            if (is_exec(c)) { safe_strlcpy(o->ytdlp, c, sizeof o->ytdlp); return true; }
        }
    }
    const char *home = getenv("HOME");
    const char *rel[] = {".local/bin/yt-dlp", ".venv/bin/yt-dlp", "venv/bin/yt-dlp", NULL};
    for (int i = 0; rel[i]; i++) {
        snprintf(c, sizeof c, "%s/%s", home ? home : ".", rel[i]);
        if (is_exec(c)) { safe_strlcpy(o->ytdlp, c, sizeof o->ytdlp); return true; }
        snprintf(c, sizeof c, "./%s", rel[i]);
        if (is_exec(c)) { safe_strlcpy(o->ytdlp, c, sizeof o->ytdlp); return true; }
    }
    const char *abs[] = {"/usr/local/bin/yt-dlp", "/opt/homebrew/bin/yt-dlp", "/usr/bin/yt-dlp", NULL};
    for (int i = 0; abs[i]; i++)
        if (is_exec(abs[i])) { safe_strlcpy(o->ytdlp, abs[i], sizeof o->ytdlp); return true; }
    o->ytdlp[0] = 0;
    return false;
}

/* --------------------------------------------------------------- argumentos */
typedef struct { char **v; int n, cap; } Args;
static void a_add(Args *a, const char *s) {
    if (a->n + 2 > a->cap) { a->cap = a->cap ? a->cap * 2 : 24; a->v = (char **)safe_realloc(a->v, a->cap * sizeof *a->v); }
    a->v[a->n++] = safe_strdup(s);
    a->v[a->n] = NULL;
}
static void a_free(Args *a) {
    for (int i = 0; i < a->n; i++) free(a->v[i]);
    free(a->v);
    a->v = NULL; a->n = a->cap = 0;
}
/* Divide por espacios respetando comillas simples/dobles. */
static void a_split(Args *a, const char *s) {
    SBuf b = {0};
    char q = 0;
    bool has = false;
    for (;; s++) {
        char c = *s;
        if (q) { if (!c) break; if (c == q) q = 0; else sb_push(&b, c); continue; }
        if (c == '"' || c == '\'') { q = c; has = true; continue; }
        if (!c || isspace((unsigned char)c)) {
            if (has) { a_add(a, b.d ? b.d : ""); sb_clear(&b); has = false; }
            if (!c) break;
            continue;
        }
        sb_push(&b, c); has = true;
    }
    sb_free(&b);
}

static void build_args(Args *a, const Options *o, const char *url) {
    a_add(a, o->ytdlp[0] ? o->ytdlp : "yt-dlp");
    a_add(a, "--newline");
    if (o->outdir[0]) { a_add(a, "-P"); a_add(a, o->outdir); }
    if (o->tmpl[0]) { a_add(a, "-o"); a_add(a, o->tmpl); }
    int f = o->format;
    if (f >= 4 || o->audio_only) {
        a_add(a, "-x"); a_add(a, "--audio-format"); a_add(a, f >= 4 ? FORMAT_ARG[f] : "best");
    } else if (f >= 1) {
        a_add(a, "--merge-output-format"); a_add(a, FORMAT_ARG[f]);
    }
    if (o->thumb) a_add(a, "--embed-thumbnail");
    if (o->meta) a_add(a, "--embed-metadata");
    if (o->rate[0]) { a_add(a, "--limit-rate"); a_add(a, o->rate); }
    if (o->proxy[0]) { a_add(a, "--proxy"); a_add(a, o->proxy); }
    if (o->browser > 0) { a_add(a, "--cookies-from-browser"); a_add(a, BROWSER_NAMES[o->browser]); }
    if (o->ua[0]) { a_add(a, "--user-agent"); a_add(a, o->ua); }
    if (o->playlist[0]) { a_add(a, "--playlist-items"); a_add(a, o->playlist); }
    if (o->custom[0]) a_split(a, o->custom);
    a_add(a, "--");           /* la URL nunca se interpreta como opción */
    a_add(a, url);
}

/* ---------------------------------------------------------------- descargas */
static atomic_int g_next_id = 1;
static pthread_mutex_t g_spawn_mu = PTHREAD_MUTEX_INITIALIZER;

static void dl_set(Download *d, DlState s, const char *m) {
    pthread_mutex_lock(&d->mu);
    d->state = s;
    safe_strlcpy(d->status, m, sizeof d->status);
    pthread_mutex_unlock(&d->mu);
}
static void tok(char *out, size_t n, const char *s) {
    size_t i = 0;
    while (*s && !isspace((unsigned char)*s) && i + 1 < n) out[i++] = *s++;
    out[i] = 0;
}

enum { K_OTHER, K_PROG, K_DEST, K_ALREADY, K_MERGE, K_AUDIO, K_META, K_ITEM, K_INFO, K_ERR, K_WARN };

static int classify(const char *l) {
    if (!strncmp(l, "[download]", 10)) {
        if (strchr(l, '%') && strstr(l, " of ")) return K_PROG;
        if (strstr(l, "Destination:")) return K_DEST;
        if (strstr(l, "has already been downloaded")) return K_ALREADY;
        if (strstr(l, "Downloading item")) return K_ITEM;
        return K_OTHER;
    }
    if (!strncmp(l, "[Merger]", 8)) return K_MERGE;
    if (!strncmp(l, "[ExtractAudio]", 14) || !strncmp(l, "[VideoConvertor]", 16)) return K_AUDIO;
    if (!strncmp(l, "[Metadata]", 10) || !strncmp(l, "[EmbedThumbnail]", 16) ||
        !strncmp(l, "[Thumbnails", 11) || !strncmp(l, "[ThumbnailsConvertor]", 21)) return K_META;
    if (!strncmp(l, "ERROR:", 6)) return K_ERR;
    if (!strncmp(l, "WARNING:", 8)) return K_WARN;
    if (l[0] == '[' && (strstr(l, "Extracting") || strstr(l, "Downloading webpage"))) return K_INFO;
    return K_OTHER;
}

/* Despacho por computed goto: una tabla de etiquetas indexada por la clase de línea. */
static void parse_line(Download *d, const char *l) {
    static const void *const T[] = {&&o_other, &&o_prog, &&o_dest, &&o_already, &&o_merge,
                                    &&o_audio, &&o_meta, &&o_item, &&o_info, &&o_err, &&o_warn};
    const char *msg = NULL;
    goto *T[classify(l)];

o_prog: {
    const char *p = l + 10;
    while (*p == ' ') p++;
    float pct = strtof(p, NULL);
    char sp[32] = "", eta[32] = "";
    const char *s = strstr(p, " at ");
    if (s) { s += 4; while (*s == ' ') s++; tok(sp, sizeof sp, s); }
    const char *e = strstr(p, "ETA ");
    if (e) tok(eta, sizeof eta, e + 4);
    pthread_mutex_lock(&d->mu);
    d->pct = pct;
    safe_strlcpy(d->speed, sp, sizeof d->speed);
    safe_strlcpy(d->eta, eta, sizeof d->eta);
    safe_strlcpy(d->status, "Descargando", sizeof d->status);
    pthread_mutex_unlock(&d->mu);
    return;
}
o_dest:    log_push("#%d %s", d->id, l); msg = "Descargando"; goto set;
o_already: log_push("#%d %s", d->id, l);
    pthread_mutex_lock(&d->mu); d->pct = 100; pthread_mutex_unlock(&d->mu);
    msg = "Ya descargado"; goto set;
o_merge:   log_push("#%d %s", d->id, l); msg = "Uniendo audio y vídeo"; goto set;
o_audio:   log_push("#%d %s", d->id, l); msg = "Convirtiendo"; goto set;
o_meta:    log_push("#%d %s", d->id, l); msg = "Metadatos / miniatura"; goto set;
o_item:    log_push("#%d %s", d->id, l); msg = "Lista de reproducción"; goto set;
o_info:    log_push("#%d %s", d->id, l); msg = "Extrayendo información"; goto set;
o_warn:    log_push("#%d %s", d->id, l); return;
o_err:
    log_push("#%d %s", d->id, l);
    pthread_mutex_lock(&d->mu);
    safe_strlcpy(d->last_err, l + 6 + (l[6] == ' '), sizeof d->last_err);
    pthread_mutex_unlock(&d->mu);
    return;
o_other:   log_push("#%d %s", d->id, l); return;
set:
    pthread_mutex_lock(&d->mu);
    safe_strlcpy(d->status, msg, sizeof d->status);
    pthread_mutex_unlock(&d->mu);
}

static void *worker(void *arg) {
    Download *d = (Download *)arg;
    Args a = {0};
    SBuf ln = {0};
    char buf[4096];
    int fd[2] = {-1, -1};
    pid_t pid = 0;
    int st = 0, rc;

    build_args(&a, &d->opt, d->url);
    {
        SBuf cmd = {0};
        for (int i = 0; i < a.n; i++) { if (i) sb_push(&cmd, ' '); sb_str(&cmd, a.v[i]); }
        log_push("#%d Ejecutando: %s", d->id, cmd.d);
        sb_free(&cmd);
    }

    /* pipe + spawn bajo mutex: ningún otro hijo hereda nuestro extremo de escritura */
    pthread_mutex_lock(&g_spawn_mu);
    if (pipe(fd) != 0) {
        pthread_mutex_unlock(&g_spawn_mu);
        dl_set(d, DL_ERROR, "Error interno: pipe()");
        goto out;
    }
    posix_spawn_file_actions_t fa;
    posix_spawnattr_t at;
    posix_spawn_file_actions_init(&fa);
    posix_spawnattr_init(&at);
    posix_spawn_file_actions_adddup2(&fa, fd[1], 1);
    posix_spawn_file_actions_adddup2(&fa, fd[1], 2);
    posix_spawn_file_actions_addclose(&fa, fd[0]);
    posix_spawn_file_actions_addclose(&fa, fd[1]);
    posix_spawnattr_setpgroup(&at, 0);                 /* grupo propio: se puede matar con yt-dlp+ffmpeg */
    posix_spawnattr_setflags(&at, POSIX_SPAWN_SETPGROUP);
    rc = posix_spawnp(&pid, a.v[0], &fa, &at, a.v, environ);
    posix_spawn_file_actions_destroy(&fa);
    posix_spawnattr_destroy(&at);
    close(fd[1]); fd[1] = -1;
    pthread_mutex_unlock(&g_spawn_mu);
    if (rc != 0) {
        log_push("#%d No se pudo ejecutar '%s': %s", d->id, a.v[0], strerror(rc));
        dl_set(d, DL_ERROR, "No se pudo ejecutar yt-dlp");
        goto out;
    }

    pthread_mutex_lock(&d->mu);
    d->pid = pid;
    pthread_mutex_unlock(&d->mu);
    if (atomic_load(&d->cancel)) kill(-pid, SIGTERM);   /* cancelado durante el arranque */
    dl_set(d, DL_RUNNING, "Iniciando");

    for (;;) {
        ssize_t n = read(fd[0], buf, sizeof buf);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) break;
        for (ssize_t i = 0; i < n; i++) {
            char c = buf[i];
            if (c == '\n' || c == '\r') {
                if (ln.len) { parse_line(d, ln.d); sb_clear(&ln); }
            } else if (ln.len < 2000) sb_push(&ln, c);
        }
    }
    if (ln.len) parse_line(d, ln.d);
    while (waitpid(pid, &st, 0) < 0 && errno == EINTR) {}
    pthread_mutex_lock(&d->mu);
    d->pid = 0;
    pthread_mutex_unlock(&d->mu);

    if (atomic_load(&d->cancel)) {
        dl_set(d, DL_CANCELLED, "Cancelado");
    } else if (WIFEXITED(st) && WEXITSTATUS(st) == 0) {
        pthread_mutex_lock(&d->mu);
        d->pct = 100; d->eta[0] = 0; d->state = DL_DONE;
        safe_strlcpy(d->status, "Completado", sizeof d->status);
        pthread_mutex_unlock(&d->mu);
        log_push("#%d Completado: %s", d->id, d->url);
    } else {
        char m[128];
        pthread_mutex_lock(&d->mu);
        if (d->last_err[0]) safe_strlcpy(m, d->last_err, sizeof m);
        else snprintf(m, sizeof m, "yt-dlp terminó con código %d", WIFEXITED(st) ? WEXITSTATUS(st) : -1);
        pthread_mutex_unlock(&d->mu);
        log_push("#%d Falló: %s", d->id, m);
        dl_set(d, DL_ERROR, m);
    }
out:
    if (fd[0] >= 0) close(fd[0]);
    sb_free(&ln);
    a_free(&a);
    return NULL;
}

Download *dl_new(const char *url) {
    Download *d = (Download *)safe_calloc(1, sizeof *d);
    d->id = atomic_fetch_add(&g_next_id, 1);
    d->url = safe_strdup(url);
    pthread_mutex_init(&d->mu, NULL);
    atomic_init(&d->cancel, false);
    dl_requeue(d);
    return d;
}
void dl_join(Download *d) {
    if (d->started) { pthread_join(d->th, NULL); d->started = false; }
}
void dl_requeue(Download *d) {
    dl_join(d);
    pthread_mutex_lock(&d->mu);
    d->state = DL_QUEUED; d->pct = 0; d->speed[0] = d->eta[0] = d->last_err[0] = 0;
    safe_strlcpy(d->status, "En cola", sizeof d->status);
    pthread_mutex_unlock(&d->mu);
}
bool dl_start(Download *d, const Options *o) {
    dl_join(d);
    pthread_mutex_lock(&d->mu);
    d->opt = *o; d->state = DL_RUNNING; d->pct = 0; d->pid = 0;
    d->speed[0] = d->eta[0] = d->last_err[0] = 0;
    safe_strlcpy(d->status, "Iniciando", sizeof d->status);
    pthread_mutex_unlock(&d->mu);
    atomic_store(&d->cancel, false);
    if (pthread_create(&d->th, NULL, worker, d) != 0) { dl_set(d, DL_ERROR, "No se pudo crear el hilo"); return false; }
    d->started = true;
    return true;
}
void dl_cancel(Download *d) {
    atomic_store(&d->cancel, true);
    pthread_mutex_lock(&d->mu);
    pid_t p = d->pid;
    if (d->state == DL_QUEUED) { d->state = DL_CANCELLED; safe_strlcpy(d->status, "Cancelado", sizeof d->status); }
    pthread_mutex_unlock(&d->mu);
    if (p > 0) kill(-p, SIGTERM);
}
void dl_free(Download *d) {
    if (!d) return;
    dl_cancel(d);
    dl_join(d);
    pthread_mutex_destroy(&d->mu);
    safe_free(&d->url);
    free(d);
}
void dl_snapshot(Download *d, DlSnap *s) {
    pthread_mutex_lock(&d->mu);
    s->state = d->state; s->pct = d->pct;
    safe_strlcpy(s->speed, d->speed, sizeof s->speed);
    safe_strlcpy(s->eta, d->eta, sizeof s->eta);
    safe_strlcpy(s->status, d->status, sizeof s->status);
    pthread_mutex_unlock(&d->mu);
}

/* ------------------------------------------------------------- abrir carpeta */
static void *reap(void *a) { waitpid((pid_t)(intptr_t)a, NULL, 0); return NULL; }
void open_path(const char *path) {
#ifdef __APPLE__
    const char *cmd = "open";
#else
    const char *cmd = "xdg-open";
#endif
    char *argv[] = {(char *)cmd, (char *)path, NULL};
    pid_t pid;
    if (posix_spawnp(&pid, cmd, NULL, NULL, argv, environ) == 0) {
        pthread_t t;
        if (pthread_create(&t, NULL, reap, (void *)(intptr_t)pid) == 0) pthread_detach(t);
    } else log_push("No se pudo abrir '%s' con %s", path, cmd);
}
