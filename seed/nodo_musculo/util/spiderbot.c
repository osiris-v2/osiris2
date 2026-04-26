/*
 * SpiderBot v2.0 - Escáner masivo de IPs públicas aleatorias
 *
 * Compilar:
 *   gcc -o spiderbot spiderbot.c -lsqlite3 -lcurl -lpthread -O2 -Wall
 *
 * Uso:
 *   ./spiderbot [--help]
 *   ./spiderbot --ultrafast --ips 500 --run
 *   Desde el menú: múltiples parámetros por línea
 *   Ctrl+C durante el escaneo vuelve al menú
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <pthread.h>
#include <curl/curl.h>
#include <sqlite3.h>
#include <stdatomic.h>

/* ============================================================
 * CONSTANTES
 * ============================================================ */
#define VERSION          "2.0"
#define DB_PATH          "/tmp/spiderbot.db"
#define UA               "Mozilla/5.0 SpiderBot/" VERSION
#define MAX_PORTS        64
#define MAX_LINKS        512
#define MAX_THREADS      32
#define MAX_LINE         1024

/* Defaults normales */
#define DEF_MAX_IPS      10
#define DEF_TIMEOUT      5
#define DEF_SLEEP_MS     1000
#define DEF_THREADS      1
#define DEF_NUM_PORTS    4

/* Ultrafast: máxima velocidad, mínima info */
#define UF_TIMEOUT       1
#define UF_SLEEP_MS      0
#define UF_THREADS       8

/* ============================================================
 * COLORES ANSI
 * ============================================================ */
#define RST   "\033[0m"
#define GRN   "\033[32m"
#define YLW   "\033[33m"
#define RED   "\033[31m"
#define CYN   "\033[36m"
#define GRY   "\033[90m"
#define MAG   "\033[35m"
#define BLD   "\033[1m"
#define BGRN  "\033[1;32m"
#define BYLN  "\033[1;33m"
#define BRED  "\033[1;31m"

/* ============================================================
 * CONFIGURACIÓN
 * ============================================================ */
typedef struct {
    int  max_ips;
    int  scan_timeout;
    int  sleep_ms;
    int  threads;
    int  ports[MAX_PORTS];
    int  num_ports;
    int  verbose;
    int  ultrafast;
    int  no_dns;
    int  no_links;
    int  no_html;
} Config;

/* ============================================================
 * ESTADÍSTICAS ATÓMICAS (seguras entre threads)
 * ============================================================ */
typedef struct {
    atomic_int ips_scanned;
    atomic_int ips_with_open;
    atomic_int ports_open;
    atomic_int http_found;
    atomic_int links_found;
    time_t     start_time;
} Stats;

/* ============================================================
 * ESTADO GLOBAL
 * ============================================================ */
static Config          cfg;
static Stats           stats;
static volatile int    g_stop      = 0;
static sqlite3        *db          = NULL;
static pthread_mutex_t db_mutex    = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t print_mutex = PTHREAD_MUTEX_INITIALIZER;
static atomic_int      g_ip_counter = 0;

/* ============================================================
 * PRINT THREAD-SAFE
 * ============================================================ */
#define TPRINT(...) do { \
    pthread_mutex_lock(&print_mutex); \
    printf(__VA_ARGS__); \
    fflush(stdout); \
    pthread_mutex_unlock(&print_mutex); \
} while(0)

/* ============================================================
 * AYUDA
 * ============================================================ */
static void print_help(void) {
    printf(
        BGRN "SpiderBot v" VERSION RST " — Escáner masivo de IPs públicas aleatorias\n\n"
        BLD "COMPILAR:\n" RST
        "  gcc -o spiderbot spiderbot.c -lsqlite3 -lcurl -lpthread -O2\n\n"
        BLD "USO:\n" RST
        "  ./spiderbot [--help]\n"
        "  ./spiderbot --ultrafast --ips 1000 --run\n"
        "  ./spiderbot --ports-set 80,443,8080 --threads 4 --run\n\n"
        BLD "COMANDOS DEL MENÚ (combinables en una línea):\n" RST
        "  " GRN "--run" RST "                    Iniciar escaneo\n"
        "  " GRN "--ips N|unlimit" RST "          Máx IPs (0/unlimit = infinito)\n"
        "  " GRN "--timeout N" RST "              Timeout en segundos (1-120)\n"
        "  " GRN "--sleep N" RST "                Pausa entre IPs en ms (0-60000)\n"
        "  " GRN "--threads N" RST "              Threads paralelos (1-32)\n"
        "  " GRN "--ports-add 80,443,8080" RST "  Añadir puertos a la lista\n"
        "  " GRN "--ports-del 8080,8081" RST "    Eliminar puertos de la lista\n"
        "  " GRN "--ports-set 80,443" RST "       Reemplazar lista completa\n"
        "  " GRN "--ports-all" RST "              Añadir 70+ puertos web conocidos\n"
        "  " GRN "--ports-reset" RST "            Restaurar puertos por defecto\n"
        "  " GRN "--ultrafast" RST "              Modo máxima velocidad\n"
        "  " GRN "--no-dns" RST "                 Toggle resolución DNS\n"
        "  " GRN "--no-links" RST "               Toggle extracción de enlaces\n"
        "  " GRN "--no-html" RST "                Toggle fetch HTML (solo HEAD)\n"
        "  " GRN "--verbose" RST "                Toggle modo verbose\n"
        "  " GRN "--reset" RST "                  Restaurar todos los defaults\n"
        "  " GRN "--status" RST "                 Ver configuración actual\n"
        "  " GRN "--salir" RST "                  Salir\n\n"
        BLD "EJEMPLOS MULTI-COMANDO:\n" RST
        GRY "  spiderbot> --ips 200 --threads 6 --sleep 100 --run\n"
        "  spiderbot> --ports-set 80,443,8080,8443 --ultrafast --run\n"
        "  spiderbot> --ips unlimit --threads 16 --no-dns --no-links --run\n" RST "\n"
        BLD "ULTRAFAST aplica:\n" RST
        "  timeout=%ds, sleep=0, threads=%d, no-dns, no-links, no-html\n\n"
        BLD "DEFAULTS:\n" RST
        "  ips=%d  timeout=%ds  sleep=%dms  threads=%d  puertos=80,443,8080,8081\n"
        "  DB: " DB_PATH "\n\n"
        BLD "CTRL+C:" RST " durante escaneo → vuelve al menú sin cerrar\n\n",
        UF_TIMEOUT, UF_THREADS,
        DEF_MAX_IPS, DEF_TIMEOUT, DEF_SLEEP_MS, DEF_THREADS
    );
}

/* ============================================================
 * BASE DE DATOS SQLite
 * ============================================================ */
static int db_init(void) {
    if (db) return 0; /* Ya abierta */

    int rc = sqlite3_open(DB_PATH, &db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, BRED "Error DB: %s\n" RST, sqlite3_errmsg(db));
        return -1;
    }

    /* WAL mode: escrituras concurrentes desde múltiples threads */
    sqlite3_exec(db, "PRAGMA journal_mode=WAL;",    NULL, NULL, NULL);
    sqlite3_exec(db, "PRAGMA synchronous=NORMAL;",  NULL, NULL, NULL);
    sqlite3_exec(db, "PRAGMA cache_size=10000;",    NULL, NULL, NULL);
    sqlite3_exec(db, "PRAGMA temp_store=MEMORY;",   NULL, NULL, NULL);

    const char *sql =
        "CREATE TABLE IF NOT EXISTS scans ("
        "  id        INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  ip        TEXT NOT NULL,"
        "  domain    TEXT,"
        "  thread_id INTEGER DEFAULT 0,"
        "  scan_time DATETIME DEFAULT CURRENT_TIMESTAMP"
        ");"
        "CREATE TABLE IF NOT EXISTS ports ("
        "  id       INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  scan_id  INTEGER,"
        "  port     INTEGER,"
        "  protocol TEXT,"
        "  service  TEXT,"
        "  is_http  INTEGER DEFAULT 0,"
        "  html_content TEXT,"
        "  FOREIGN KEY(scan_id) REFERENCES scans(id)"
        ");"
        "CREATE TABLE IF NOT EXISTS links ("
        "  id        INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  scan_id   INTEGER,"
        "  port_id   INTEGER,"
        "  url       TEXT,"
        "  link_type TEXT,"
        "  FOREIGN KEY(scan_id) REFERENCES scans(id)"
        ");"
        "CREATE INDEX IF NOT EXISTS idx_scans_ip   ON scans(ip);"
        "CREATE INDEX IF NOT EXISTS idx_links_scan ON links(scan_id);";

    char *err = NULL;
    rc = sqlite3_exec(db, sql, NULL, NULL, &err);
    if (rc != SQLITE_OK) {
        fprintf(stderr, BRED "Error tablas: %s\n" RST, err);
        sqlite3_free(err);
        return -1;
    }
    printf(GRY "  DB: " DB_PATH "\n" RST);
    return 0;
}

static long long db_insert_scan(const char *ip, const char *domain, int tid) {
    pthread_mutex_lock(&db_mutex);
    sqlite3_stmt *stmt;
    sqlite3_prepare_v2(db,
        "INSERT INTO scans(ip,domain,thread_id) VALUES(?,?,?)", -1, &stmt, NULL);
    sqlite3_bind_text(stmt, 1, ip,                        -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 2, domain ? domain : "",      -1, SQLITE_STATIC);
    sqlite3_bind_int (stmt, 3, tid);
    sqlite3_step(stmt);
    long long id = sqlite3_last_insert_rowid(db);
    sqlite3_finalize(stmt);
    pthread_mutex_unlock(&db_mutex);
    return id;
}

// Firma: añadir const char *html_content
static long long db_insert_port(long long scan_id, int port,
                                  const char *service, int is_http,
                                  const char *html_content) {
    pthread_mutex_lock(&db_mutex);
    sqlite3_stmt *stmt;
    sqlite3_prepare_v2(db,
        "INSERT INTO ports(scan_id,port,protocol,service,is_http,html_content)"
        " VALUES(?,?,?,?,?,?)",
        -1, &stmt, NULL);
    sqlite3_bind_int64(stmt, 1, scan_id);
    sqlite3_bind_int  (stmt, 2, port);
    sqlite3_bind_text (stmt, 3, "tcp",                         -1, SQLITE_STATIC);
    sqlite3_bind_text (stmt, 4, service ? service : "unknown", -1, SQLITE_STATIC);
    sqlite3_bind_int  (stmt, 5, is_http);
    // html puede ser NULL (no HTTP, o no_html activo)
    if (html_content)
        sqlite3_bind_text(stmt, 6, html_content, -1, SQLITE_STATIC);
    else
        sqlite3_bind_null(stmt, 6);
    sqlite3_step(stmt);
    long long id = sqlite3_last_insert_rowid(db);
    sqlite3_finalize(stmt);
    pthread_mutex_unlock(&db_mutex);
    return id;
}

static void db_insert_link(long long scan_id, long long port_id,
                            const char *url, const char *type) {
    pthread_mutex_lock(&db_mutex);
    sqlite3_stmt *stmt;
    sqlite3_prepare_v2(db,
        "INSERT INTO links(scan_id,port_id,url,link_type) VALUES(?,?,?,?)",
        -1, &stmt, NULL);
    sqlite3_bind_int64(stmt, 1, scan_id);
    sqlite3_bind_int64(stmt, 2, port_id);
    sqlite3_bind_text (stmt, 3, url,  -1, SQLITE_STATIC);
    sqlite3_bind_text (stmt, 4, type, -1, SQLITE_STATIC);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    pthread_mutex_unlock(&db_mutex);
}

/* ============================================================
 * GENERACIÓN DE IPs (thread-safe con rand_r)
 * ============================================================ */
static int is_private_ip(unsigned int ip) {
    unsigned int a = (ip >> 24) & 0xFF;
    unsigned int b = (ip >> 16) & 0xFF;
    unsigned int c = (ip >>  8) & 0xFF;
    if (a == 0 || a == 127)                         return 1;
    if (a == 10)                                    return 1;
    if (a >= 224)                                   return 1;
    if (a == 172 && b >= 16 && b <= 31)             return 1;
    if (a == 192 && b == 168)                       return 1;
    if (a == 169 && b == 254)                       return 1;
    if (a == 100 && b >= 64 && b <= 127)            return 1;
    if (a == 198 && (b == 18 || b == 19))           return 1;
    if (a == 203 && b == 0 && c == 113)             return 1;
    if (a == 192 && b == 0 && c == 2)               return 1;
    if (a == 192 && b == 88 && c == 99)             return 1;
    return 0;
}

static void generate_random_ip(char *buf, size_t len, unsigned int *seed) {
    while (1) {
        unsigned int ip = rand_r(seed);
        if (!is_private_ip(ip)) {
            snprintf(buf, len, "%u.%u.%u.%u",
                (ip>>24)&0xFF, (ip>>16)&0xFF, (ip>>8)&0xFF, ip&0xFF);
            return;
        }
    }
}

/* ============================================================
 * RED
 * ============================================================ */
static int resolve_domain(const char *ip, char *out, size_t len) {
    struct sockaddr_in sa;
    memset(&sa, 0, sizeof(sa));
    sa.sin_family = AF_INET;
    inet_pton(AF_INET, ip, &sa.sin_addr);
    return getnameinfo((struct sockaddr *)&sa, sizeof(sa),
                       out, len, NULL, 0, NI_NAMEREQD) == 0;
}

static int check_port(const char *ip, int port) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return 0;

    struct timeval tv = { .tv_sec = cfg.scan_timeout, .tv_usec = 0 };
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port   = htons((uint16_t)port);
    inet_pton(AF_INET, ip, &addr.sin_addr);

    int r = connect(sock, (struct sockaddr *)&addr, sizeof(addr));
    close(sock);
    return r == 0;
}

/* ---- CURL ---- */
typedef struct { char *data; size_t size; } CurlBuf;

static size_t curl_write_cb(void *ptr, size_t size, size_t nmemb, void *ud) {
    size_t total = size * nmemb;
    CurlBuf *buf = (CurlBuf *)ud;
    if (buf->size + total > 512*1024) total = 512*1024 - buf->size;
    if (total == 0) return size * nmemb;
    char *tmp = realloc(buf->data, buf->size + total + 1);
    if (!tmp) return 0;
    buf->data = tmp;
    memcpy(buf->data + buf->size, ptr, total);
    buf->size += total;
    buf->data[buf->size] = '\0';
    return size * nmemb;
}

/* Devuelve 1 si responde HTTP. Si no no_html, pone html en *html_out */
static int fetch_http(const char *ip, int port, char **html_out) {
    CURL *curl = curl_easy_init();
    if (!curl) return 0;

    const char *scheme = (port == 443) ? "https" : "http";
    char url[256];
    snprintf(url, sizeof(url), "%s://%s:%d/", scheme, ip, port);

    CurlBuf buf = { NULL, 0 };

    curl_easy_setopt(curl, CURLOPT_URL,            url);
    curl_easy_setopt(curl, CURLOPT_USERAGENT,      UA);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT,        (long)cfg.scan_timeout);
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, (long)cfg.scan_timeout);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_MAXREDIRS,      3L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL,       1L); /* imprescindible con threads */

    if (cfg.no_html) {
        curl_easy_setopt(curl, CURLOPT_NOBODY, 1L);
    } else {
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curl_write_cb);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA,     &buf);
    }

    CURLcode res = curl_easy_perform(curl);
    int is_http  = 0;

    if (res == CURLE_OK) {
        long http_code = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
        if (http_code >= 100 && http_code < 600) {
            is_http = 1;
            if (html_out && buf.data) { *html_out = buf.data; buf.data = NULL; }
        }
    }

    curl_easy_cleanup(curl);
    if (buf.data) free(buf.data);
    return is_http;
}

/* ============================================================
 * EXTRACCIÓN DE ENLACES
 * ============================================================ */
typedef struct { char url[512]; char type[32]; } Link;

static void resolve_url(const char *base, const char *href,
                         char *out, size_t len) {
    if (strncmp(href,"http://",7)==0 || strncmp(href,"https://",8)==0) {
        strncpy(out, href, len-1); out[len-1] = '\0'; return;
    }
    if (href[0] == '/') {
        char scheme[8]="http", host[256]="";
        sscanf(base, "%7[^:]://%255[^/]", scheme, host);
        snprintf(out, len, "%s://%s%s", scheme, host, href);
        return;
    }
    snprintf(out, len, "%.*s/%.*s", (int)(len/2 - 1), base, (int)(len/2 - 1), href);
}

static int extract_links(const char *base_url, const char *html,
                          Link *links, int max) {
    if (!html) return 0;
    int count = 0;

    const char *tags[]  = {"<a ","<link ","<script ","<img ","<iframe ","<source "};
    const char *akeys[] = {"href","href","src","src","src","src"};
    const char *types[] = {"html_link","html_link","asset","asset","asset","asset"};

    for (int t = 0; t < 6 && count < max; t++) {
        const char *p = html;
        while (count < max) {
            const char *tag = strcasestr(p, tags[t]);
            if (!tag) break;
            const char *end_tag = strchr(tag, '>');
            if (!end_tag) { p = tag + 1; continue; }

            /* Copiar el tag para buscar el atributo */
            size_t tlen = (size_t)(end_tag - tag);
            if (tlen > 2048) { p = end_tag; continue; }
            char tmp[2049];
            strncpy(tmp, tag, tlen); tmp[tlen] = '\0';

            const char *ak = strcasestr(tmp, akeys[t]);
            if (!ak) { p = end_tag; continue; }

            const char *eq = strchr(ak, '=');
            if (!eq) { p = end_tag; continue; }
            eq++;
            while (*eq == ' ') eq++;
            char delim = (*eq=='"'||*eq=='\'') ? *eq++ : ' ';
            const char *ve = strchr(eq, delim);
            if (!ve) ve = eq + strlen(eq);

            size_t vlen = (size_t)(ve - eq);
            if (vlen > 0 && vlen < 500) {
                char val[512] = {0};
                strncpy(val, eq, vlen);
                if (strncmp(val,"javascript:",11)!=0 &&
                    strncmp(val,"data:",5)!=0 && strlen(val) > 1) {
                    resolve_url(base_url, val,
                                links[count].url, sizeof(links[count].url));
                    strncpy(links[count].type, types[t],
                            sizeof(links[count].type)-1);
                    count++;
                }
            }
            p = end_tag;
        }
    }
    return count;
}

/* ============================================================
 * SEÑAL SIGINT
 * ============================================================ */
static void sigint_handler(int sig) {
    (void)sig;
    g_stop = 1;
    write(STDOUT_FILENO,
        "\n" BYLN "  [!] Ctrl+C — parando threads, espera...\n" RST, 55);
}

/* ============================================================
 * ESTADÍSTICAS EN TIEMPO REAL
 * ============================================================ */
static void print_realtime_stats(int tid) {
    int sc = atomic_load(&stats.ips_scanned);
    int po = atomic_load(&stats.ports_open);
    int ht = atomic_load(&stats.http_found);
    int lk = atomic_load(&stats.links_found);
    time_t el = time(NULL) - stats.start_time;
    float ips_sec = el > 0 ? (float)sc / el : 0.0f;

    TPRINT(GRY "  [T%02d] ips=%-6d puertos=%-5d http=%-4d links=%-5d  "
               "%.1f ip/s\n" RST,
           tid, sc, po, ht, lk, ips_sec);
}

/* ============================================================
 * WORKER DE ESCANEO
 * ============================================================ */
typedef struct { int thread_id; Config cfg_snap; } ThreadArg;

static void *scan_worker(void *varg) {
    ThreadArg *ta = (ThreadArg *)varg;
    int    tid = ta->thread_id;
    Config *c  = &ta->cfg_snap;

    /* Seed única por thread: mezcla tiempo + tid */
    unsigned int seed = (unsigned int)(time(NULL)) ^ ((unsigned int)tid * 0x9e3779b9u);

    int local_n = 0;

    while (!g_stop) {
        /* Distribuir trabajo entre threads con contador atómico */
        if (c->max_ips > 0) {
            int idx = atomic_fetch_add(&g_ip_counter, 1);
            if (idx >= c->max_ips) break;
        }

        char ip[20];
        generate_random_ip(ip, sizeof(ip), &seed);
        local_n++;
        atomic_fetch_add(&stats.ips_scanned, 1);

        /* DNS */
        char domain[256] = "";
        if (!c->no_dns) {
            if (!resolve_domain(ip, domain, sizeof(domain)))
                strcpy(domain, "n/a");
        }

        if (c->verbose) {
            TPRINT(CYN "[T%02d] " RST "%s " GRY "%s%s%s\n" RST,
                   tid, ip,
                   domain[0]?"(":"", domain, domain[0]?")":"");
        }

        long long scan_id = db_insert_scan(ip, domain, tid);
        int had_open = 0;

        /* Puertos */
        for (int pi = 0; pi < c->num_ports && !g_stop; pi++) {
            int port = c->ports[pi];
            if (!check_port(ip, port)) {
                if (c->verbose)
                    TPRINT(GRY "  [T%02d] :%d cerrado\n" RST, tid, port);
                continue;
            }

            had_open = 1;
            atomic_fetch_add(&stats.ports_open, 1);

            /* HTTP */
            char *html   = NULL;
            int  is_http = fetch_http(ip, port, (c->no_links || c->no_html) ? NULL : &html);

            if (is_http) {
                atomic_fetch_add(&stats.http_found, 1);
                const char *scheme = (port==443) ? "https" : "http";

                TPRINT(GRN "  [T%02d] %s:%-5d" RST " [%s]",
                       tid, ip, port, port==443 ? "HTTPS":"HTTP");

                long long port_id = db_insert_port(scan_id, port, port==443?"HTTPS":"HTTP", 1, html);

                if (html) {
                    char base[256];
                    snprintf(base, sizeof(base), "%s://%s:%d", scheme, ip, port);
                    Link links_buf[MAX_LINKS];
                    int nl = extract_links(base, html, links_buf, MAX_LINKS);
                    for (int li = 0; li < nl; li++)
                        db_insert_link(scan_id, port_id,
                                       links_buf[li].url, links_buf[li].type);
                    if (nl > 0) {
                        atomic_fetch_add(&stats.links_found, nl);
                        TPRINT(MAG " %d links" RST, nl);
                    }
                    free(html);
                }
                TPRINT("\n");

            } else {
                if (c->verbose)
                    TPRINT(YLW "  [T%02d] %s:%-5d no-HTTP\n" RST, tid, ip, port);
                db_insert_port(scan_id, port, "tcp", 0, NULL);
            }
        }

        if (had_open) atomic_fetch_add(&stats.ips_with_open, 1);

        /* Stats en tiempo real cada 50 IPs por thread */
        if (local_n % 50 == 0) print_realtime_stats(tid);

        /* Sleep */
        if (!g_stop && c->sleep_ms > 0) {
            struct timespec ts = {
                .tv_sec  =  c->sleep_ms / 1000,
                .tv_nsec = (c->sleep_ms % 1000) * 1000000L
            };
            nanosleep(&ts, NULL);
        }
    }

    free(ta);
    return NULL;
}

/* ============================================================
 * LANZAR ESCANEO
 * ============================================================ */
static void run_scan(void) {
    g_stop = 0;
    atomic_store(&g_ip_counter, 0);
    atomic_store(&stats.ips_scanned,   0);
    atomic_store(&stats.ips_with_open, 0);
    atomic_store(&stats.ports_open,    0);
    atomic_store(&stats.http_found,    0);
    atomic_store(&stats.links_found,   0);
    stats.start_time = time(NULL);

    signal(SIGINT, sigint_handler);

    /* Banner */
    printf(BGRN "\n[SpiderBot v" VERSION "] Iniciando\n" RST);
    printf(GRY
        "  IPs      : %s\n"
        "  Threads  : %d\n"
        "  Timeout  : %ds   Sleep: %dms\n"
        "  Modo     : %s\n"
        "  DNS      : %-4s  Links: %s  HTML: %s\n"
        "  Puertos  : ",
        cfg.max_ips == 0 ? "ILIMITADO" : ({ static char _b[24]; snprintf(_b,24,"%d",cfg.max_ips); _b; }),
        cfg.threads,
        cfg.scan_timeout, cfg.sleep_ms,
        cfg.ultrafast ? BYLN "ULTRAFAST" RST : "normal",
        cfg.no_dns    ? RED "off" RST : GRN "on" RST,
        cfg.no_links  ? RED "off" RST : GRN "on" RST,
        cfg.no_html   ? RED "off" RST : GRN "on" RST
    );
    for (int i = 0; i < cfg.num_ports; i++)
        printf("%d%s", cfg.ports[i], i < cfg.num_ports-1 ? "," : "");
    printf(GRY "\n  Ctrl+C para volver al menú\n\n" RST);

    /* Lanzar threads */
    pthread_t tids[MAX_THREADS];
    for (int t = 0; t < cfg.threads; t++) {
        ThreadArg *ta  = malloc(sizeof(ThreadArg));
        ta->thread_id  = t + 1;
        ta->cfg_snap   = cfg;  /* snapshot en el momento del lanzamiento */
        pthread_create(&tids[t], NULL, scan_worker, ta);
    }

    /* Esperar a que terminen */
    for (int t = 0; t < cfg.threads; t++)
        pthread_join(tids[t], NULL);

    signal(SIGINT, SIG_DFL);

    /* Resumen */
    time_t elapsed = time(NULL) - stats.start_time;
    float  ips_sec = elapsed > 0
        ? (float)atomic_load(&stats.ips_scanned) / elapsed : 0.0f;

    printf(BYLN "\n  ══════════════════════════════════════\n" RST);
    printf(BLD  "  Escaneo completado\n" RST);
    printf("  IPs escaneadas    : " BLD "%d\n" RST, atomic_load(&stats.ips_scanned));
    printf("  Con puertos abiertos: %d\n",           atomic_load(&stats.ips_with_open));
    printf("  Puertos abiertos  : %d\n",             atomic_load(&stats.ports_open));
    printf("  HTTP/S encontrados: %d\n",             atomic_load(&stats.http_found));
    printf("  Links guardados   : %d\n",             atomic_load(&stats.links_found));
    printf("  Tiempo total      : %lds  (%.1f ip/s)\n", elapsed, ips_sec);
    printf("  DB                : " DB_PATH "\n");
    printf(BYLN "  ══════════════════════════════════════\n\n" RST);
}

/* ============================================================
 * GESTIÓN DE PUERTOS
 * ============================================================ */

/* 70+ puertos web conocidos */
static const int KNOWN_PORTS[] = {
    80,81,88,443,591,593,832,981,1010,1311,2082,2087,2095,2096,
    2480,3000,3128,3333,4243,4567,4711,4712,4993,5000,5104,5108,
    5800,6543,7000,7396,7474,8000,8001,8008,8014,8042,8069,8080,
    8081,8088,8090,8091,8118,8123,8172,8222,8243,8280,8281,8333,
    8443,8500,8834,8880,8888,8983,9000,9043,9060,9080,9090,9091,
    9200,9443,9800,9981,10000,10443,11371,12443,16080,18091,18092,
    20720,28017
};
#define N_KNOWN (int)(sizeof(KNOWN_PORTS)/sizeof(KNOWN_PORTS[0]))

static int port_exists(int p) {
    for (int i = 0; i < cfg.num_ports; i++) if (cfg.ports[i]==p) return 1;
    return 0;
}

static void ports_add(const char *csv) {
    char buf[512]; strncpy(buf,csv,511); buf[511]='\0';
    int added=0;
    char *tok=strtok(buf,",");
    while(tok){
        int p=atoi(tok);
        if(p>0&&p<=65535&&!port_exists(p)&&cfg.num_ports<MAX_PORTS){
            cfg.ports[cfg.num_ports++]=p; added++;
        }
        tok=strtok(NULL,",");
    }
    printf(GRN "  +%d puerto(s). Total: %d\n" RST, added, cfg.num_ports);
}

static void ports_del(const char *csv) {
    char buf[512]; strncpy(buf,csv,511); buf[511]='\0';
    int removed=0;
    char *tok=strtok(buf,",");
    while(tok){
        int p=atoi(tok);
        for(int i=0;i<cfg.num_ports;i++){
            if(cfg.ports[i]==p){
                for(int j=i;j<cfg.num_ports-1;j++) cfg.ports[j]=cfg.ports[j+1];
                cfg.num_ports--; removed++; break;
            }
        }
        tok=strtok(NULL,",");
    }
    printf(GRN "  -%d puerto(s). Total: %d\n" RST, removed, cfg.num_ports);
}

static void ports_set(const char *csv) {
    cfg.num_ports=0;
    ports_add(csv);
}

static void ports_reset(void) {
    int p[]={80,443,8080,8081};
    cfg.num_ports=4;
    memcpy(cfg.ports,p,sizeof(p));
    printf(GRN "  Puertos → 80,443,8080,8081\n" RST);
}

static void ports_all(void) {
    int added=0;
    for(int i=0;i<N_KNOWN;i++)
        if(!port_exists(KNOWN_PORTS[i])&&cfg.num_ports<MAX_PORTS){
            cfg.ports[cfg.num_ports++]=KNOWN_PORTS[i]; added++;
        }
    printf(GRN "  +%d puertos conocidos. Total: %d\n" RST, added, cfg.num_ports);
}

/* ============================================================
 * STATUS
 * ============================================================ */
static void print_status(void) {
    printf(BLD
        "\n  ┌─ Configuración ─────────────────────────┐\n" RST);
    printf("  │  %-18s ", "Max IPs:");
    if (cfg.max_ips==0) printf(YLW "ILIMITADO" RST "\n");
    else                printf("%d\n", cfg.max_ips);
    printf("  │  %-18s %ds\n",  "Timeout:",    cfg.scan_timeout);
    printf("  │  %-18s %dms\n", "Sleep:",      cfg.sleep_ms);
    printf("  │  %-18s %d\n",   "Threads:",    cfg.threads);
    printf("  │  %-18s %s\n",   "Modo:",       cfg.ultrafast ? BYLN"ULTRAFAST"RST : "normal");
    printf("  │  %-18s %s\n",   "Verbose:",    cfg.verbose  ? GRN"on"RST : "off");
    printf("  │  %-18s %s\n",   "DNS:",        cfg.no_dns   ? RED"off"RST : GRN"on"RST);
    printf("  │  %-18s %s\n",   "Links:",      cfg.no_links ? RED"off"RST : GRN"on"RST);
    printf("  │  %-18s %s\n",   "HTML fetch:", cfg.no_html  ? RED"off"RST : GRN"on"RST);
    printf("  │  %-18s ", "Puertos:");
    for(int i=0;i<cfg.num_ports;i++)
        printf("%d%s", cfg.ports[i], i<cfg.num_ports-1?",":"");
    printf(" " GRY "(%d)" RST "\n", cfg.num_ports);
    printf(BLD "  └──────────────────────────────────────────┘\n" RST);

    int sc = atomic_load(&stats.ips_scanned);
    if (sc > 0) {
        printf(GRY "\n  Última sesión: %d IPs | %d HTTP | %d links\n" RST,
               sc, atomic_load(&stats.http_found), atomic_load(&stats.links_found));
    }
    printf("\n");
}

/* ============================================================
 * APPLY ULTRAFAST
 * ============================================================ */
static void apply_ultrafast(void) {
    cfg.ultrafast    = 1;
    cfg.scan_timeout = UF_TIMEOUT;
    cfg.sleep_ms     = UF_SLEEP_MS;
    cfg.threads      = UF_THREADS;
    cfg.no_dns       = 1;
    cfg.no_links     = 1;
    cfg.no_html      = 1;
    printf(BYLN "  ⚡ ULTRAFAST:" RST GRY
           " timeout=%ds  sleep=0  threads=%d  dns=off  links=off  html=off\n" RST,
           UF_TIMEOUT, UF_THREADS);
}

/* ============================================================
 * DEFAULTS
 * ============================================================ */
static void config_defaults(void) {
    cfg.max_ips      = DEF_MAX_IPS;
    cfg.scan_timeout = DEF_TIMEOUT;
    cfg.sleep_ms     = DEF_SLEEP_MS;
    cfg.threads      = DEF_THREADS;
    cfg.verbose      = 0;
    cfg.ultrafast    = 0;
    cfg.no_dns       = 0;
    cfg.no_links     = 0;
    cfg.no_html      = 0;
    cfg.num_ports    = DEF_NUM_PORTS;
    int p[]          = {80,443,8080,8081};
    memcpy(cfg.ports, p, sizeof(p));
}

/* ============================================================
 * TOKENIZADOR PROPIO: parse_line
 * Permite múltiples comandos+args en una sola línea
 * Retorna: 1=run  2=salir  0=normal
 * ============================================================ */
static int parse_and_exec(const char *input) {
    char buf[MAX_LINE];
    strncpy(buf, input, MAX_LINE-1); buf[MAX_LINE-1]='\0';

    int do_run  = 0;
    int do_exit = 0;
    int pos     = 0;
    int len     = (int)strlen(buf);

    while (pos < len && !do_exit) {
        /* Saltar espacios */
        while (pos < len && (buf[pos]==' '||buf[pos]=='\t')) pos++;
        if (pos >= len) break;

        /* Extraer comando (hasta espacio) */
        int cs = pos;
        while (pos < len && buf[pos]!=' ' && buf[pos]!='\t') pos++;
        buf[pos] = '\0';
        char *cmd = buf + cs;
        pos++;

        /* Comandos que necesitan argumento */
        int needs_arg = (
            strcmp(cmd,"--ips")==0       ||
            strcmp(cmd,"--timeout")==0   ||
            strcmp(cmd,"--sleep")==0     ||
            strcmp(cmd,"--threads")==0   ||
            strcmp(cmd,"--ports-add")==0 ||
            strcmp(cmd,"--ports-del")==0 ||
            strcmp(cmd,"--ports-set")==0
        );

        char *arg = NULL;
        if (needs_arg) {
            while (pos < len && (buf[pos]==' '||buf[pos]=='\t')) pos++;
            if (pos < len) {
                int as = pos;
                while (pos < len && buf[pos]!=' ' && buf[pos]!='\t') pos++;
                buf[pos] = '\0';
                arg = buf + as;
                pos++;
            }
        }

        /* Ejecutar comando */
        if (strcmp(cmd,"--run")==0) {
            do_run = 1;
        } else if (strcmp(cmd,"--salir")==0 ||
                   strcmp(cmd,"exit")==0    ||
                   strcmp(cmd,"quit")==0) {
            do_exit = 1;

        } else if (strcmp(cmd,"--ips")==0) {
            if (!arg) { printf(RED "  --ips requiere argumento\n" RST); }
            else if (strcmp(arg,"unlimit")==0||strcmp(arg,"0")==0) {
                cfg.max_ips=0; printf(GRN "  Max IPs → ILIMITADO\n" RST);
            } else {
                int v=atoi(arg);
                if (v<=0) printf(RED "  Valor inválido\n" RST);
                else { cfg.max_ips=v; printf(GRN "  Max IPs → %d\n" RST,v); }
            }

        } else if (strcmp(cmd,"--timeout")==0) {
            if (!arg) { printf(RED "  --timeout requiere argumento\n" RST); }
            else {
                int v=atoi(arg);
                if (v<=0||v>120) printf(RED "  Rango: 1-120\n" RST);
                else { cfg.scan_timeout=v; printf(GRN "  Timeout → %ds\n" RST,v); }
            }

        } else if (strcmp(cmd,"--sleep")==0) {
            if (!arg) { printf(RED "  --sleep requiere argumento\n" RST); }
            else {
                int v=atoi(arg);
                if (v<0||v>60000) printf(RED "  Rango: 0-60000ms\n" RST);
                else { cfg.sleep_ms=v; printf(GRN "  Sleep → %dms\n" RST,v); }
            }

        } else if (strcmp(cmd,"--threads")==0) {
            if (!arg) { printf(RED "  --threads requiere argumento\n" RST); }
            else {
                int v=atoi(arg);
                if (v<1||v>MAX_THREADS) printf(RED "  Rango: 1-%d\n" RST,MAX_THREADS);
                else { cfg.threads=v; printf(GRN "  Threads → %d\n" RST,v); }
            }

        } else if (strcmp(cmd,"--ports-add")==0) {
            if (!arg) printf(RED "  --ports-add requiere lista\n" RST);
            else ports_add(arg);

        } else if (strcmp(cmd,"--ports-del")==0) {
            if (!arg) printf(RED "  --ports-del requiere lista\n" RST);
            else ports_del(arg);

        } else if (strcmp(cmd,"--ports-set")==0) {
            if (!arg) printf(RED "  --ports-set requiere lista\n" RST);
            else ports_set(arg);

        } else if (strcmp(cmd,"--ports-all")==0)   { ports_all();
        } else if (strcmp(cmd,"--ports-reset")==0)  { ports_reset();
        } else if (strcmp(cmd,"--ultrafast")==0)    { apply_ultrafast();
        } else if (strcmp(cmd,"--no-dns")==0) {
            cfg.no_dns=!cfg.no_dns;
            printf(GRN "  DNS → %s\n" RST, cfg.no_dns?"off":"on");
        } else if (strcmp(cmd,"--no-links")==0) {
            cfg.no_links=!cfg.no_links;
            printf(GRN "  Links → %s\n" RST, cfg.no_links?"off":"on");
        } else if (strcmp(cmd,"--no-html")==0) {
            cfg.no_html=!cfg.no_html;
            printf(GRN "  HTML fetch → %s\n" RST, cfg.no_html?"off":"on");
        } else if (strcmp(cmd,"--verbose")==0) {
            cfg.verbose=!cfg.verbose;
            printf(GRN "  Verbose → %s\n" RST, cfg.verbose?"on":"off");
        } else if (strcmp(cmd,"--reset")==0) {
            config_defaults();
            printf(GRN "  Config restaurada a defaults\n" RST);
        } else if (strcmp(cmd,"--status")==0) {
            print_status();
        } else if (strcmp(cmd,"--help")==0||strcmp(cmd,"help")==0) {
            print_help();
        } else {
            printf(RED "  Desconocido: '%s'  (--help para ayuda)\n" RST, cmd);
        }
    }

    if (do_exit) return 2;
    if (do_run)  return 1;
    return 0;
}

/* ============================================================
 * MENÚ INTERACTIVO
 * ============================================================ */
static void run_menu(void) {
    char line[MAX_LINE];

    printf(BGRN
        "\n ╔══════════════════════════════════════════╗\n"
        " ║   SpiderBot v" VERSION "  —  Menú interactivo    ║\n"
        " ║    GSE - Gooyim Search Engine            ║\n"
        " ╚══════════════════════════════════════════╝\n" RST
        GRY
        "  --help para ver todos los comandos\n"
        "  Combina comandos: --ips 100 --threads 4 --run\n\n" RST);

    while (1) {
        printf(BYLN "spiderbot> " RST);
        fflush(stdout);

        if (!fgets(line, sizeof(line), stdin)) break;
        line[strcspn(line,"\n")] = '\0';

        char *p = line;
        while (*p==' '||*p=='\t') p++;
        if (*p == '\0') continue;

        int ret = parse_and_exec(p);

        if (ret == 2) {
            printf(GRY "  Saliendo...\n" RST);
            break;
        }
        if (ret == 1) {
            if (db_init() != 0) {
                printf(RED "  Error inicializando DB\n" RST);
                continue;
            }
            run_scan();
        }
    }
}

/* ============================================================
 * MAIN
 * ============================================================ */
int main(int argc, char *argv[]) {
    srand((unsigned int)time(NULL));
    curl_global_init(CURL_GLOBAL_DEFAULT);
    config_defaults();

    if (argc > 1) {
        /* --help */
        if (strcmp(argv[1],"--help")==0 || strcmp(argv[1],"-h")==0) {
            print_help();
            curl_global_cleanup();
            return 0;
        }

        /* Construir línea de comandos desde args */
        char combined[MAX_LINE] = "";
        for (int i = 1; i < argc; i++) {
            if (strlen(combined) + strlen(argv[i]) + 2 < MAX_LINE) {
                strcat(combined, argv[i]);
                strcat(combined, " ");
            }
        }

        int ret = parse_and_exec(combined);
        if (ret == 1) {
            if (db_init()==0) run_scan();
        }
        if (ret == 2) {
            curl_global_cleanup();
            return 0;
        }
        /* Si no había --run ni --salir, entrar al menú */
        if (ret == 0) run_menu();

    } else {
        run_menu();
    }

    if (db) sqlite3_close(db);
    curl_global_cleanup();
    return 0;
}
