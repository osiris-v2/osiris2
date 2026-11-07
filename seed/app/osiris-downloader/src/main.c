/* main.c - Osiris Downloader AI (C puro + SDL2): interfaz y cola de descargas. */
#define _GNU_SOURCE
#include <signal.h>
#include <stdarg.h>
#include "core.h"
#include "ui.h"


enum { TAB_DL, TAB_LOG, TAB_OPT };

typedef struct {
    UI ui;
    Options opt;
    Download **dl;
    int ndl, cap;
    char url_in[4096];
    char cfg[512];
    char toast[160];
    uint32_t toast_until;
    int tab, scroll_dl, scroll_log;
    bool queue_active, autoscroll, found;
} App;

static void toast(App *a, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(a->toast, sizeof a->toast, fmt, ap);
    va_end(ap);
    a->toast_until = SDL_GetTicks() + 3500;
}

/* ------------------------------------------------------------------- cola */
static int add_urls(App *a, const char *text) {
    int added = 0;
    safe_ptr(char) cp = safe_strdup(text);
    char *sv = NULL;
    for (char *t = strtok_r(cp, " \t\r\n", &sv); t; t = strtok_r(NULL, " \t\r\n", &sv)) {
        if (strncmp(t, "http://", 7) && strncmp(t, "https://", 8)) {
            log_push("Ignorado (no es una URL http/https): %s", t);
            continue;
        }
        if (a->ndl == a->cap) {
            a->cap = a->cap ? a->cap * 2 : 16;
            a->dl = (Download **)safe_realloc(a->dl, a->cap * sizeof *a->dl);
        }
        a->dl[a->ndl++] = dl_new(t);
        added++;
    }
    return added;
}

static DlState dl_state(Download *d) { DlSnap s; dl_snapshot(d, &s); return s.state; }

static void schedule(App *a) {
    if (!a->queue_active) return;
    int running = 0, queued = 0;
    for (int i = 0; i < a->ndl; i++) if (dl_state(a->dl[i]) == DL_RUNNING) running++;
    for (int i = 0; i < a->ndl; i++) {
        if (dl_state(a->dl[i]) != DL_QUEUED) continue;
        if (running < a->opt.max_par) { dl_start(a->dl[i], &a->opt); running++; }
        else queued++;
    }
    if (!running && !queued) { a->queue_active = false; log_push("Cola terminada."); }
}

static void remove_at(App *a, int i) {
    dl_free(a->dl[i]);
    memmove(&a->dl[i], &a->dl[i + 1], (size_t)(a->ndl - i - 1) * sizeof *a->dl);
    a->ndl--;
}

static void start_queue(App *a) {
    if (!a->found) a->found = ytdlp_detect(&a->opt);
    if (!a->found) { toast(a, "yt-dlp no encontrado: indica su ruta en Opciones"); return; }
    a->queue_active = true;
}

/* -------------------------------------------------------------- pantallas */
static SDL_Color state_color(UI *u, DlState s) {
    switch (s) {
        case DL_DONE: return u->th.ok;
        case DL_ERROR: return u->th.err;
        case DL_CANCELLED: return u->th.dim;
        default: return u->th.accent;
    }
}

static void draw_downloads(App *a, int W, int H, int y0) {
    UI *u = &a->ui;
    int fh = u->lh + 10, x = 12, y = y0, bw = 96;
    SDL_Rect in = {x, y, W - 2 * x - 2 * bw - 16, fh};
    bool enter = ui_input(u, in, a->url_in, sizeof a->url_in);
    SDL_Rect b1 = {in.x + in.w + 8, y, bw, fh}, b2 = {b1.x + bw + 8, y, bw, fh};
    if (ui_button(u, b1, "Añadir", 0) || enter) {
        if (a->url_in[0]) { int n = add_urls(a, a->url_in); a->url_in[0] = 0; toast(a, "%d URL(s) añadida(s)", n); }
    }
    if (ui_button(u, b2, "Pegar", 0)) {
        char *c = SDL_GetClipboardText();
        if (c && *c) toast(a, "%d URL(s) añadida(s)", add_urls(a, c));
        SDL_free(c);
    }
    y += fh + 8;
    int cx = x;
    if (ui_button(u, (SDL_Rect){cx, y, 110, fh}, "Iniciar", a->queue_active ? UI_ACTIVE : 0)) start_queue(a);
    cx += 118;
    if (ui_button(u, (SDL_Rect){cx, y, 130, fh}, "Detener todas", 0)) {
        a->queue_active = false;
        for (int i = 0; i < a->ndl; i++) if (dl_state(a->dl[i]) <= DL_RUNNING) dl_cancel(a->dl[i]);
        toast(a, "Descargas detenidas");
    }
    cx += 138;
    if (ui_button(u, (SDL_Rect){cx, y, 160, fh}, "Limpiar terminadas", 0)) {
        for (int i = a->ndl - 1; i >= 0; i--) if (dl_state(a->dl[i]) >= DL_DONE) remove_at(a, i);
    }
    cx += 168;
    if (ui_button(u, (SDL_Rect){cx, y, 140, fh}, "Abrir carpeta", 0)) open_path(a->opt.outdir);
    y += fh + 8;
    char st[640];
    if (a->found) snprintf(st, sizeof st, "yt-dlp: %s   |   salida: %s", a->opt.ytdlp, a->opt.outdir);
    else snprintf(st, sizeof st, "yt-dlp NO encontrado: instálalo o indica la ruta en Opciones");
    ui_text(u, x, y, st, a->found ? u->th.dim : u->th.err);
    y += u->lh + 10;

    /* tabla */
    int cw[7] = {32, 0, 150, 230, 95, 70, 170}, fixed = 0;
    for (int k = 0; k < 7; k++) fixed += cw[k];
    cw[1] = W - 2 * x - fixed;
    if (cw[1] < 120) cw[1] = 120;
    int px[7];
    px[0] = x;
    for (int k = 1; k < 7; k++) px[k] = px[k - 1] + cw[k - 1];
    const char *hd[7] = {"#", "URL", "Progreso", "Estado", "Velocidad", "ETA", "Acciones"};
    int rh = u->lh + 14, hh = u->lh + 8;
    ui_rect(u, (SDL_Rect){x, y, W - 2 * x, hh}, u->th.panel);
    for (int k = 0; k < 7; k++) ui_text(u, px[k] + 4, y + 4, hd[k], u->th.dim);
    SDL_Rect reg = {x, y + hh, W - 2 * x, H - (y + hh) - 30};
    ui_rect(u, reg, u->th.field);
    if (ui_hover(u, reg)) a->scroll_dl -= u->wheel * 40;
    int total = a->ndl * rh, maxs = total > reg.h ? total - reg.h : 0;
    if (a->scroll_dl > maxs) a->scroll_dl = maxs;
    if (a->scroll_dl < 0) a->scroll_dl = 0;
    if (!a->ndl) ui_text(u, reg.x + 12, reg.y + 12, "Sin descargas. Pega una o varias URLs arriba y pulsa Añadir.", u->th.dim);

    int rem = -1;
    ui_clip(u, &reg);
    for (int i = 0; i < a->ndl; i++) {
        int ry = reg.y + i * rh - a->scroll_dl;
        if (ry + rh < reg.y || ry > reg.y + reg.h) continue;
        DlSnap s;
        dl_snapshot(a->dl[i], &s);
        if (i & 1) ui_rect(u, (SDL_Rect){reg.x, ry, reg.w, rh}, u->th.bg);
        char n[16];
        snprintf(n, sizeof n, "%d", i + 1);
        ui_text(u, px[0] + 4, ry + (rh - u->lh) / 2, n, u->th.dim);
        ui_text_clip(u, (SDL_Rect){px[1], ry, cw[1] - 6, rh}, a->dl[i]->url, u->th.text);
        ui_progress(u, (SDL_Rect){px[2] + 2, ry + 5, cw[2] - 10, rh - 10}, s.pct, state_color(u, s.state));
        ui_text_clip(u, (SDL_Rect){px[3], ry, cw[3] - 6, rh}, s.status, state_color(u, s.state));
        ui_text_clip(u, (SDL_Rect){px[4], ry, cw[4] - 4, rh}, s.speed, u->th.text);
        ui_text_clip(u, (SDL_Rect){px[5], ry, cw[5] - 4, rh}, s.eta, u->th.text);
        SDL_Rect ba = {px[6] + 2, ry + 3, 80, rh - 6}, bq = {px[6] + 88, ry + 3, 76, rh - 6};
        if (s.state == DL_RUNNING) { if (ui_button(u, ba, "Parar", 0)) dl_cancel(a->dl[i]); }
        else if (s.state != DL_QUEUED) { if (ui_button(u, ba, "Reintentar", 0)) { dl_requeue(a->dl[i]); start_queue(a); } }
        if (ui_button(u, bq, "Quitar", 0)) rem = i;
    }
    ui_clip(u, NULL);
    ui_border(u, reg, u->th.border);
    if (rem >= 0) remove_at(a, rem);
}

static void draw_log(App *a, int W, int H, int y0) {
    UI *u = &a->ui;
    int fh = u->lh + 10, x = 12, y = y0;
    if (ui_button(u, (SDL_Rect){x, y, 150, fh}, "Limpiar registro", 0)) log_clear();
    ui_checkbox(u, x + 170, y + (fh - 18) / 2, "Scroll automático", &a->autoscroll);
    y += fh + 8;
    SDL_Rect reg = {x, y, W - 2 * x, H - y - 30};
    ui_rect(u, reg, u->th.field);
    int n = log_count(), lines = reg.h / u->lh;
    if (ui_hover(u, reg) && u->wheel) { a->scroll_log -= u->wheel * 3; if (u->wheel > 0) a->autoscroll = false; }
    int maxs = n > lines ? n - lines : 0;
    if (a->autoscroll) a->scroll_log = maxs;
    if (a->scroll_log > maxs) a->scroll_log = maxs;
    if (a->scroll_log < 0) a->scroll_log = 0;
    ui_clip(u, &reg);
    for (int i = 0; i < lines && a->scroll_log + i < n; i++) {
        char ln[512];
        if (!log_get(a->scroll_log + i, ln, sizeof ln)) break;
        SDL_Color c = strstr(ln, "ERROR") || strstr(ln, "Falló") || strstr(ln, "No se pudo") ? u->th.err
                    : strstr(ln, "WARNING") ? u->th.warn : strstr(ln, "Completado") ? u->th.ok : u->th.text;
        ui_text(u, reg.x + 6, reg.y + 2 + i * u->lh, ln, c);
    }
    ui_clip(u, NULL);
    ui_border(u, reg, u->th.border);
}

#define LBLW 240
static SDL_Rect orow(App *a, int *y, int W, const char *label, int rw) {
    UI *u = &a->ui;
    int fh = u->lh + 10;
    ui_text(u, 12, *y + 5, label, u->th.dim);
    SDL_Rect r = {12 + LBLW, *y, rw > 0 ? rw : W - 24 - LBLW, fh};
    *y += fh + 8;
    return r;
}

static void draw_options(App *a, int W, int H, int y0) {
    (void)H;
    UI *u = &a->ui;
    Options *o = &a->opt;
    int y = y0, fh = u->lh + 10;
    SDL_Rect r;

    r = orow(a, &y, W, "Ruta de yt-dlp", W - 24 - LBLW - 120);
    ui_input(u, r, o->ytdlp, sizeof o->ytdlp);
    if (ui_button(u, (SDL_Rect){r.x + r.w + 8, r.y, 112, fh}, "Detectar", 0)) {
        o->ytdlp[0] = 0;
        a->found = ytdlp_detect(o);
        toast(a, a->found ? "yt-dlp: %s" : "yt-dlp no encontrado", o->ytdlp);
    }
    r = orow(a, &y, W, "Directorio de salida", W - 24 - LBLW - 120);
    ui_input(u, r, o->outdir, sizeof o->outdir);
    if (ui_button(u, (SDL_Rect){r.x + r.w + 8, r.y, 112, fh}, "Abrir", 0)) open_path(o->outdir);

    r = orow(a, &y, W, "Formato de salida", 240);
    ui_cycle(u, r, FORMAT_NAMES, FORMAT_COUNT, &o->format);
    ui_text(u, 12, y + 2, "Solo audio", u->th.dim);
    ui_checkbox(u, 12 + LBLW, y + 2, "Extraer solo la pista de audio", &o->audio_only);
    y += fh + 8;

    r = orow(a, &y, W, "Descargas en paralelo", 34);
    if (ui_button(u, r, "-", 0) && o->max_par > 1) o->max_par--;
    char nb[8];
    snprintf(nb, sizeof nb, "%d", o->max_par);
    ui_text(u, r.x + 46, r.y + 5, nb, u->th.text);
    if (ui_button(u, (SDL_Rect){r.x + 76, r.y, 34, fh}, "+", 0) && o->max_par < 8) o->max_par++;

    r = orow(a, &y, W, "Límite velocidad (1M, 500K)", 160);
    ui_input(u, r, o->rate, sizeof o->rate);
    r = orow(a, &y, W, "Plantilla de nombre (-o)", 0);
    ui_input(u, r, o->tmpl, sizeof o->tmpl);

    ui_text(u, 12, y + 2, "Incrustar", u->th.dim);
    ui_checkbox(u, 12 + LBLW, y + 2, "Miniatura", &o->thumb);
    ui_checkbox(u, 12 + LBLW + 140, y + 2, "Metadatos", &o->meta);
    y += fh + 8;

    r = orow(a, &y, W, "Proxy (http://host:puerto)", 0);
    ui_input(u, r, o->proxy, sizeof o->proxy);
    r = orow(a, &y, W, "Cookies del navegador", 240);
    ui_cycle(u, r, BROWSER_NAMES, BROWSER_COUNT, &o->browser);
    r = orow(a, &y, W, "User-Agent", 0);
    ui_input(u, r, o->ua, sizeof o->ua);
    r = orow(a, &y, W, "Rango de playlist (1:5)", 160);
    ui_input(u, r, o->playlist, sizeof o->playlist);
    r = orow(a, &y, W, "Argumentos extra", 0);
    ui_input(u, r, o->custom, sizeof o->custom);

    if (ui_button(u, (SDL_Rect){12 + LBLW, y + 4, 180, fh}, "Guardar opciones", 0))
        toast(a, options_save(o, a->cfg) ? "Guardado en %s" : "No se pudo guardar %s", a->cfg);
}

/* --------------------------------------------------------------- eventos */
/* Despacho de eventos SDL mediante tabla de etiquetas (computed goto). */
static bool handle_event(App *a, SDL_Event *e) {
    static const void *const T[] = {&&ev_other, &&ev_quit, &&ev_motion, &&ev_down, &&ev_up, &&ev_wheel, &&ev_text, &&ev_key};
    UI *u = &a->ui;
    int k = 0;
    switch (e->type) {
        case SDL_QUIT: k = 1; break;
        case SDL_MOUSEMOTION: k = 2; break;
        case SDL_MOUSEBUTTONDOWN: k = 3; break;
        case SDL_MOUSEBUTTONUP: k = 4; break;
        case SDL_MOUSEWHEEL: k = 5; break;
        case SDL_TEXTINPUT: k = 6; break;
        case SDL_KEYDOWN: k = 7; break;
        default: break;
    }
    goto *T[k];
ev_quit:   return false;
ev_motion: u->mx = e->motion.x; u->my = e->motion.y; return true;
ev_down:
    if (e->button.button == SDL_BUTTON_LEFT) { u->mx = e->button.x; u->my = e->button.y; u->pressed = u->down = true; }
    return true;
ev_up:
    if (e->button.button == SDL_BUTTON_LEFT) { u->mx = e->button.x; u->my = e->button.y; u->released = true; u->down = false; }
    return true;
ev_wheel:  u->wheel += e->wheel.y; return true;
ev_text:   strncat(u->textin, e->text.text, sizeof u->textin - strlen(u->textin) - 1); return true;
ev_key: {
    SDL_Keycode s = e->key.keysym.sym;
    bool ctl = (e->key.keysym.mod & (KMOD_CTRL | KMOD_GUI)) != 0;
    if (ctl && s == SDLK_v) u->paste = 1;
    else if (s == SDLK_BACKSPACE) u->bs++;
    else if (s == SDLK_DELETE) u->del++;
    else if (s == SDLK_LEFT) u->left++;
    else if (s == SDLK_RIGHT) u->right++;
    else if (s == SDLK_HOME) u->home++;
    else if (s == SDLK_END) u->end++;
    else if (s == SDLK_RETURN || s == SDLK_KP_ENTER) u->enter++;
    return true;
}
ev_other:  return true;
}

int main(void) {
    signal(SIGPIPE, SIG_IGN);
    App *a = (App *)safe_calloc(1, sizeof *a);
    a->autoscroll = true;
    options_defaults(&a->opt);
    settings_path(a->cfg, sizeof a->cfg);
    options_load(&a->opt, a->cfg);
    a->found = ytdlp_detect(&a->opt);

    if (SDL_Init(SDL_INIT_VIDEO) != 0) { fprintf(stderr, "SDL_Init: %s\n", SDL_GetError()); return 1; }
    if (TTF_Init() != 0) { fprintf(stderr, "TTF_Init: %s\n", TTF_GetError()); return 1; }
    SDL_Window *win = SDL_CreateWindow("Osiris Downloader AI (C / SDL2)", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                       1100, 720, SDL_WINDOW_RESIZABLE);
    if (!win) { fprintf(stderr, "SDL_CreateWindow: %s\n", SDL_GetError()); return 1; }
    SDL_Renderer *ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!ren) ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_SOFTWARE);
    if (!ren) { fprintf(stderr, "SDL_CreateRenderer: %s\n", SDL_GetError()); return 1; }
    if (!ui_init(&a->ui, ren, 15)) return 1;
    SDL_StartTextInput();

    log_push("Osiris Downloader iniciado. Configuración: %s", a->cfg);
    if (!a->found) log_push("ERROR: yt-dlp no encontrado. Instálalo o indica la ruta en Opciones.");
    else log_push("yt-dlp detectado: %s", a->opt.ytdlp);

    bool run = true;
    while (run) {
        SDL_Event e;
        if (SDL_WaitEventTimeout(&e, 33)) {
            do { if (!handle_event(a, &e)) run = false; } while (SDL_PollEvent(&e));
        }
        UI *u = &a->ui;
        u->ticks = SDL_GetTicks();
        schedule(a);

        SDL_SetRenderDrawColor(ren, u->th.bg.r, u->th.bg.g, u->th.bg.b, 255);
        SDL_RenderClear(ren);
        int W, H;
        SDL_GetRendererOutputSize(ren, &W, &H);
        int fh = u->lh + 10;
        ui_text(u, 12, 8 + (fh - u->lh) / 2, "Osiris Downloader AI", u->th.accent);
        const char *names[3] = {"Descargas", "Registro", "Opciones"};
        for (int t = 0; t < 3; t++)
            if (ui_button(u, (SDL_Rect){250 + t * 118, 8, 110, fh}, names[t], a->tab == t ? UI_ACTIVE : 0)) a->tab = t;
        int y0 = 8 + fh + 14;
        switch (a->tab) {
            case TAB_DL:  draw_downloads(a, W, H, y0); break;
            case TAB_LOG: draw_log(a, W, H, y0); break;
            default:      draw_options(a, W, H, y0); break;
        }
        int q = 0, r = 0, d = 0, er = 0;
        for (int i = 0; i < a->ndl; i++) {
            switch (dl_state(a->dl[i])) {
                case DL_QUEUED: q++; break; case DL_RUNNING: r++; break;
                case DL_DONE: d++; break; case DL_ERROR: er++; break; default: break;
            }
        }
        char sb[200];
        snprintf(sb, sizeof sb, "En cola: %d   Activas: %d   Completadas: %d   Errores: %d", q, r, d, er);
        ui_text(u, 12, H - u->lh - 6, sb, u->th.dim);
        if (SDL_GetTicks() < a->toast_until) {
            int tw = ui_text_w(u, a->toast);
            ui_rect(u, (SDL_Rect){W - tw - 36, H - u->lh - 14, tw + 24, u->lh + 10}, u->th.btnhov);
            ui_text(u, W - tw - 24, H - u->lh - 9, a->toast, u->th.text);
        }
        SDL_RenderPresent(ren);
        ui_end(u);
    }

    for (int i = 0; i < a->ndl; i++) dl_cancel(a->dl[i]);
    for (int i = 0; i < a->ndl; i++) dl_free(a->dl[i]);
    options_save(&a->opt, a->cfg);
    safe_free(&a->dl);
    ui_shutdown(&a->ui);
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    TTF_Quit();
    SDL_Quit();
    safe_free(&a);
    return 0;
}
