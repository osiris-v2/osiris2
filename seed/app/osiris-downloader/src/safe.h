/* safe.h - memoria segura para Osiris Downloader (GCC/Clang).
 *  - safe_malloc/calloc/realloc: nunca devuelven NULL (abortan con mensaje).
 *  - safe_ptr(T): puntero que se libera solo al salir de su ámbito (cleanup).
 *  - safe_free(&p): libera y deja p = NULL (evita double-free / use-after-free).
 *  - SAFE_MOVE(p): transfiere la propiedad y anula el original.
 *  - SBuf: cadena dinámica con crecimiento controlado.
 */
#ifndef OSIRIS_SAFE_H
#define OSIRIS_SAFE_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stddef.h>

#ifndef __GNUC__
#error "Se requiere GCC o Clang (computed goto y __attribute__((cleanup)))"
#endif

static inline void *safe_malloc(size_t n) {
    void *p = malloc(n ? n : 1);
    if (!p) { fputs("osiris: sin memoria\n", stderr); abort(); }
    return p;
}
static inline void *safe_calloc(size_t n, size_t s) {
    void *p = calloc(n ? n : 1, s ? s : 1);
    if (!p) { fputs("osiris: sin memoria\n", stderr); abort(); }
    return p;
}
static inline void *safe_realloc(void *old, size_t n) {
    void *p = realloc(old, n ? n : 1);
    if (!p) { fputs("osiris: sin memoria\n", stderr); abort(); }
    return p;
}
static inline char *safe_strdup(const char *s) {
    size_t n = strlen(s) + 1;
    return (char *)memcpy(safe_malloc(n), s, n);
}
/* Copia acotada; siempre termina en '\0'. Devuelve la longitud de src. */
static inline size_t safe_strlcpy(char *d, const char *s, size_t n) {
    size_t l = strlen(s);
    if (n) { size_t c = l >= n ? n - 1 : l; memcpy(d, s, c); d[c] = 0; }
    return l;
}

static inline void safe_autofree(void *pp) {
    void **p = (void **)pp;
    if (*p) { free(*p); *p = NULL; }
}
#define safe_ptr(T) T *__attribute__((cleanup(safe_autofree)))
#define safe_free(pp) do { __typeof__(pp) _pp = (pp); if (_pp && *_pp) { free(*_pp); *_pp = NULL; } } while (0)
#define SAFE_MOVE(p) ({ __typeof__(p) _t = (p); (p) = NULL; _t; })

/* Cadena dinámica */
typedef struct { char *d; size_t len, cap; } SBuf;
static inline void sb_push(SBuf *b, char c) {
    if (b->len + 2 > b->cap) { b->cap = b->cap ? b->cap * 2 : 128; b->d = (char *)safe_realloc(b->d, b->cap); }
    b->d[b->len++] = c; b->d[b->len] = 0;
}
static inline void sb_str(SBuf *b, const char *s) { while (*s) sb_push(b, *s++); }
static inline void sb_clear(SBuf *b) { b->len = 0; if (b->d) b->d[0] = 0; }
static inline void sb_free(SBuf *b) { safe_free(&b->d); b->len = b->cap = 0; }
#endif
