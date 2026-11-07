/* ui.c - mini GUI de modo inmediato en C sobre SDL2 + SDL2_ttf. */
#include "ui.h"
#include "safe.h"
#include <stdlib.h>
#include <string.h>

static void setc(UI *u, SDL_Color c) { SDL_SetRenderDrawColor(u->r, c.r, c.g, c.b, c.a); }

static const char *find_font(void) {
    static const char *cand[] = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "./font.ttf", NULL};
    const char *env = getenv("OSIRIS_FONT");
    if (env && *env) { FILE *f = fopen(env, "rb"); if (f) { fclose(f); return env; } }
    for (int i = 0; cand[i]; i++) { FILE *f = fopen(cand[i], "rb"); if (f) { fclose(f); return cand[i]; } }
    return NULL;
}

bool ui_init(UI *u, SDL_Renderer *r, int px) {
    memset(u, 0, sizeof *u);
    u->r = r;
    const char *fp = find_font();
    if (!fp) {
        fputs("No se encontró ninguna fuente TTF. Define OSIRIS_FONT=/ruta/fuente.ttf "
              "o copia una fuente como ./font.ttf\n", stderr);
        return false;
    }
    u->font = TTF_OpenFont(fp, px);
    if (!u->font) { fprintf(stderr, "TTF_OpenFont: %s\n", TTF_GetError()); return false; }
    u->lh = TTF_FontHeight(u->font);
    u->th = (Theme){
        {24, 26, 32, 255}, {34, 37, 46, 255}, {17, 19, 25, 255}, {230, 232, 238, 255},
        {150, 155, 168, 255}, {86, 156, 255, 255}, {90, 200, 120, 255}, {235, 95, 95, 255},
        {235, 190, 80, 255}, {70, 75, 90, 255}, {52, 57, 72, 255}, {70, 78, 100, 255}};
    return true;
}
void ui_shutdown(UI *u) { if (u->font) TTF_CloseFont(u->font); u->font = NULL; }

void ui_end(UI *u) {
    if (u->released) u->active = 0;
    u->pressed = u->released = false;
    u->wheel = 0;
    u->textin[0] = 0;
    u->bs = u->del = u->left = u->right = u->home = u->end = u->enter = u->paste = 0;
}

void ui_clip(UI *u, const SDL_Rect *r) {
    if (r) { u->clip = *r; u->hasclip = true; SDL_RenderSetClipRect(u->r, r); }
    else { u->hasclip = false; SDL_RenderSetClipRect(u->r, NULL); }
}
/* recorte anidado: intersecta con el actual */
static void clip_push(UI *u, SDL_Rect r, SDL_Rect *save, bool *had) {
    *save = u->clip; *had = u->hasclip;
    if (u->hasclip) {
        SDL_Rect o;
        if (!SDL_IntersectRect(&u->clip, &r, &o)) o = (SDL_Rect){0, 0, 0, 0};
        r = o;
    }
    SDL_RenderSetClipRect(u->r, &r);
}
static void clip_pop(UI *u, SDL_Rect save, bool had) { SDL_RenderSetClipRect(u->r, had ? &save : NULL); }

bool ui_hover(UI *u, SDL_Rect r) {
    SDL_Point p = {u->mx, u->my};
    if (u->hasclip && !SDL_PointInRect(&p, &u->clip)) return false;
    return SDL_PointInRect(&p, &r);
}
void ui_rect(UI *u, SDL_Rect r, SDL_Color c) { setc(u, c); SDL_RenderFillRect(u->r, &r); }
void ui_border(UI *u, SDL_Rect r, SDL_Color c) { setc(u, c); SDL_RenderDrawRect(u->r, &r); }

int ui_text_w(UI *u, const char *s) {
    int w = 0, h = 0;
    if (s && *s) TTF_SizeUTF8(u->font, s, &w, &h);
    return w;
}
void ui_text(UI *u, int x, int y, const char *s, SDL_Color c) {
    if (!s || !*s) return;
    SDL_Surface *sf = TTF_RenderUTF8_Blended(u->font, s, c);
    if (!sf) return;
    SDL_Texture *t = SDL_CreateTextureFromSurface(u->r, sf);
    if (t) { SDL_Rect d = {x, y, sf->w, sf->h}; SDL_RenderCopy(u->r, t, NULL, &d); SDL_DestroyTexture(t); }
    SDL_FreeSurface(sf);
}
void ui_text_clip(UI *u, SDL_Rect r, const char *s, SDL_Color c) {
    SDL_Rect sv; bool had;
    clip_push(u, r, &sv, &had);
    ui_text(u, r.x + 4, r.y + (r.h - u->lh) / 2, s, c);
    clip_pop(u, sv, had);
}

static uint32_t hash_str(const char *s) { uint32_t h = 2166136261u; while (*s) h = (h ^ (uint8_t)*s++) * 16777619u; return h; }

bool ui_button(UI *u, SDL_Rect r, const char *label, int fl) {
    uint32_t id = hash_str(label) ^ ((uint32_t)r.x * 73856093u) ^ ((uint32_t)r.y * 19349663u);
    bool dis = fl & UI_DISABLED, hov = !dis && ui_hover(u, r), click = false;
    if (hov && u->pressed) u->active = id;
    if (u->released && u->active == id && hov) click = true;
    SDL_Color bg = (fl & UI_ACTIVE) ? u->th.accent : (hov ? u->th.btnhov : u->th.btn);
    if (hov && u->active == id && u->down) bg = u->th.border;
    ui_rect(u, r, bg);
    ui_border(u, r, u->th.border);
    int tw = ui_text_w(u, label);
    SDL_Rect sv; bool had;
    clip_push(u, r, &sv, &had);
    ui_text(u, r.x + (r.w - tw) / 2, r.y + (r.h - u->lh) / 2, label,
            dis ? u->th.dim : ((fl & UI_ACTIVE) ? (SDL_Color){10, 14, 24, 255} : u->th.text));
    clip_pop(u, sv, had);
    return click;
}

bool ui_checkbox(UI *u, int x, int y, const char *label, bool *v) {
    SDL_Rect box = {x, y, 18, 18}, all = {x, y, 18 + 8 + ui_text_w(u, label), 18};
    bool hov = ui_hover(u, all), ch = false;
    if (hov && u->pressed) { *v = !*v; ch = true; }
    ui_rect(u, box, u->th.field);
    ui_border(u, box, hov ? u->th.accent : u->th.border);
    if (*v) ui_rect(u, (SDL_Rect){x + 4, y + 4, 10, 10}, u->th.accent);
    ui_text(u, x + 26, y + (18 - u->lh) / 2, label, u->th.text);
    return ch;
}

static int u8prev(const char *s, int i) { if (i <= 0) return 0; i--; while (i > 0 && (s[i] & 0xC0) == 0x80) i--; return i; }
static int u8next(const char *s, int i) { int n = (int)strlen(s); if (i >= n) return n; i++; while (i < n && (s[i] & 0xC0) == 0x80) i++; return i; }
static void ins(char *buf, int cap, int *cur, const char *s, int n) {
    int len = (int)strlen(buf);
    if (len + n >= cap) n = cap - 1 - len;
    if (n <= 0) return;
    memmove(buf + *cur + n, buf + *cur, len - *cur + 1);
    memcpy(buf + *cur, s, n);
    *cur += n;
}

bool ui_input(UI *u, SDL_Rect r, char *buf, size_t capz) {
    int cap = (int)capz;
    uint32_t id = (uint32_t)(uintptr_t)buf;
    bool hov = ui_hover(u, r), enter = false;
    if (u->pressed) {
        if (hov) { u->focus = id; u->cursor = (int)strlen(buf); }
        else if (u->focus == id) u->focus = 0;
    }
    bool f = (u->focus == id);
    int len = (int)strlen(buf), cur = f ? u->cursor : len;
    if (f) {
        if (cur > len) cur = len;
        int tl = (int)strlen(u->textin);
        if (tl) ins(buf, cap, &cur, u->textin, tl);
        if (u->paste) {
            char *c = SDL_GetClipboardText();
            if (c) {
                char t[4096];
                size_t k = 0;
                for (const char *p = c; *p && k < sizeof t - 1; p++) t[k++] = ((unsigned char)*p < 32) ? ' ' : *p;
                t[k] = 0;
                ins(buf, cap, &cur, t, (int)k);
                SDL_free(c);
            }
        }
        len = (int)strlen(buf);
        if (u->bs && cur > 0) { int p = u8prev(buf, cur); memmove(buf + p, buf + cur, len - cur + 1); cur = p; }
        len = (int)strlen(buf);
        if (u->del && cur < len) { int n = u8next(buf, cur); memmove(buf + cur, buf + n, len - n + 1); }
        if (u->left) cur = u8prev(buf, cur);
        if (u->right) cur = u8next(buf, cur);
        if (u->home) cur = 0;
        if (u->end) cur = (int)strlen(buf);
        if (u->enter) enter = true;
        u->cursor = cur;
    }
    ui_rect(u, r, u->th.field);
    ui_border(u, r, f ? u->th.accent : u->th.border);
    int vw = r.w - 10;
    char sv = buf[cur]; buf[cur] = 0;
    int cw = ui_text_w(u, buf);
    buf[cur] = sv;
    int sx = cw > vw ? cw - vw : 0;
    SDL_Rect sc; bool had;
    clip_push(u, (SDL_Rect){r.x + 3, r.y, r.w - 6, r.h}, &sc, &had);
    ui_text(u, r.x + 5 - sx, r.y + (r.h - u->lh) / 2, buf, u->th.text);
    if (f && ((u->ticks / 500) & 1) == 0) ui_rect(u, (SDL_Rect){r.x + 5 - sx + cw, r.y + 5, 1, r.h - 10}, u->th.text);
    clip_pop(u, sc, had);
    return enter;
}

bool ui_cycle(UI *u, SDL_Rect r, const char *const *items, int n, int *sel) {
    char lbl[96];
    snprintf(lbl, sizeof lbl, "%s   >", items[*sel]);
    bool c = ui_button(u, r, lbl, 0);
    if (c) *sel = (*sel + 1) % n;
    return c;
}

void ui_progress(UI *u, SDL_Rect r, float pct, SDL_Color c) {
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    ui_rect(u, r, u->th.field);
    ui_rect(u, (SDL_Rect){r.x, r.y, (int)(r.w * pct / 100.0f), r.h}, c);
    ui_border(u, r, u->th.border);
    char t[16];
    snprintf(t, sizeof t, "%.1f%%", pct);
    int tw = ui_text_w(u, t);
    ui_text(u, r.x + (r.w - tw) / 2, r.y + (r.h - u->lh) / 2, t, u->th.text);
}
