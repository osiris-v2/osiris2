#ifndef OSIRIS_UI_H
#define OSIRIS_UI_H
#include <SDL.h>
#include <SDL_ttf.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct { SDL_Color bg, panel, field, text, dim, accent, ok, err, warn, border, btn, btnhov; } Theme;

enum { UI_DISABLED = 1, UI_ACTIVE = 2 };

typedef struct {
    SDL_Renderer *r;
    TTF_Font *font;
    int lh;
    Theme th;
    /* entrada (la rellena el bucle de eventos) */
    int mx, my, wheel;
    bool pressed, released, down;
    char textin[128];
    int bs, del, left, right, home, end, enter, paste;
    /* estado interno */
    uint32_t active, focus, ticks;
    int cursor;
    SDL_Rect clip;
    bool hasclip;
} UI;

bool ui_init(UI *u, SDL_Renderer *r, int px);
void ui_shutdown(UI *u);
void ui_end(UI *u);                 /* limpia los eventos de un fotograma */
bool ui_hover(UI *u, SDL_Rect r);
void ui_rect(UI *u, SDL_Rect r, SDL_Color c);
void ui_border(UI *u, SDL_Rect r, SDL_Color c);
int  ui_text_w(UI *u, const char *s);
void ui_text(UI *u, int x, int y, const char *s, SDL_Color c);
void ui_text_clip(UI *u, SDL_Rect r, const char *s, SDL_Color c);
void ui_clip(UI *u, const SDL_Rect *r);   /* NULL = sin recorte */
bool ui_button(UI *u, SDL_Rect r, const char *label, int flags);
bool ui_checkbox(UI *u, int x, int y, const char *label, bool *v);
bool ui_input(UI *u, SDL_Rect r, char *buf, size_t cap);  /* true si se pulsó Enter */
bool ui_cycle(UI *u, SDL_Rect r, const char *const *items, int n, int *sel);
void ui_progress(UI *u, SDL_Rect r, float pct, SDL_Color c);
#endif
