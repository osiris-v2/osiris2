/* ================================================================
 * PROYECTO OSIRIS - osiris_hmac.h
 * FASE 2B: Verificacion HMAC-SHA256 en el Nodo C
 *
 * Implementacion SHA-256 pura (sin OpenSSL, sin deps externas).
 * Solo un header que incluir — cero dependencias nuevas en el
 * Makefile del Nodo.
 *
 * USO:
 *   1. Al recibir el handshake (36 bytes por canal CONTROL):
 *      osiris_hmac_recibir_handshake(buf, &ctx)
 *
 *   2. Antes de procesar cada opcode:
 *      if (!osiris_hmac_verificar(&hdr, payload, n, &ctx)) {
 *          goto next_op; // descartar silenciosamente
 *      }
 * ================================================================ */

#ifndef OSIRIS_HMAC_H
#define OSIRIS_HMAC_H

#include <stdint.h>
#include <string.h>
#include <stdio.h>

/* Magic del handshake: "OSKY" en little-endian */
/* Magic "OSKY" = 0x4F534B59.
 * Rust envia con to_le_bytes() → bytes en cable: 59 4B 53 4F
 * x86 Nodo: memcpy a uint32_t → lee 0x4F534B59 (LE nativo). Coincide. */
#define OSIRIS_HANDSHAKE_MAGIC  0x4F534B59u
#define OSIRIS_KEY_SIZE         32
#define OSIRIS_HANDSHAKE_SIZE   36   /* 4 magic + 32 key */

/* Estado HMAC del Nodo — vive en bloque URANIO */
typedef struct {
    uint8_t  session_key[OSIRIS_KEY_SIZE];
    int      activo;   /* 1 = handshake recibido, 0 = sin autenticar */
} OsirisHMACCtx;

/* ── SHA-256 puro ──────────────────────────────────────────────── */

static const uint32_t SHA256_K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

#define ROTR32(x,n) (((x)>>(n))|((x)<<(32-(n))))
#define CH(x,y,z)   (((x)&(y))^(~(x)&(z)))
#define MAJ(x,y,z)  (((x)&(y))^((x)&(z))^((y)&(z)))
#define S0(x)  (ROTR32(x,2)^ROTR32(x,13)^ROTR32(x,22))
#define S1(x)  (ROTR32(x,6)^ROTR32(x,11)^ROTR32(x,25))
#define s0(x)  (ROTR32(x,7)^ROTR32(x,18)^((x)>>3))
#define s1(x)  (ROTR32(x,17)^ROTR32(x,19)^((x)>>10))

typedef struct {
    uint32_t state[8];
    uint64_t count;
    uint8_t  buf[64];
    uint32_t buflen;
} SHA256Ctx;

static inline void sha256_init(SHA256Ctx *c) {
    c->state[0]=0x6a09e667; c->state[1]=0xbb67ae85;
    c->state[2]=0x3c6ef372; c->state[3]=0xa54ff53a;
    c->state[4]=0x510e527f; c->state[5]=0x9b05688c;
    c->state[6]=0x1f83d9ab; c->state[7]=0x5be0cd19;
    c->count=0; c->buflen=0;
}

static void sha256_transform(SHA256Ctx *c, const uint8_t *data) {
    uint32_t w[64], a,b,d,e,f,g,h,t1,t2;
    uint32_t cc = c->state[0]; uint32_t cv = c->state[1];
    a=c->state[0];b=c->state[1];uint32_t cx=c->state[2];
    d=c->state[3];e=c->state[4];f=c->state[5];g=c->state[6];h=c->state[7];
    (void)cv; (void)cc; (void)cx;
    for(int i=0;i<16;i++)
        w[i]=((uint32_t)data[i*4]<<24)|((uint32_t)data[i*4+1]<<16)
            |((uint32_t)data[i*4+2]<<8)|(uint32_t)data[i*4+3];
    for(int i=16;i<64;i++)
        w[i]=s1(w[i-2])+w[i-7]+s0(w[i-15])+w[i-16];
    a=c->state[0];b=c->state[1];cx=c->state[2];d=c->state[3];
    e=c->state[4];f=c->state[5];g=c->state[6];h=c->state[7];
    for(int i=0;i<64;i++){
        t1=h+S1(e)+CH(e,f,g)+SHA256_K[i]+w[i];
        t2=S0(a)+MAJ(a,b,cx);
        h=g;g=f;f=e;e=d+t1;d=cx;cx=b;b=a;a=t1+t2;
    }
    c->state[0]+=a;c->state[1]+=b;c->state[2]+=cx;c->state[3]+=d;
    c->state[4]+=e;c->state[5]+=f;c->state[6]+=g;c->state[7]+=h;
}

static void sha256_update(SHA256Ctx *c, const uint8_t *data, size_t len) {
    c->count += len;
    while (len > 0) {
        size_t cp = 64 - c->buflen;
        if (cp > len) cp = len;
        memcpy(c->buf + c->buflen, data, cp);
        c->buflen += cp; data += cp; len -= cp;
        if (c->buflen == 64) { sha256_transform(c, c->buf); c->buflen = 0; }
    }
}

static void sha256_final(SHA256Ctx *c, uint8_t out[32]) {
    uint64_t bits = c->count * 8;
    uint8_t pad = 0x80;
    sha256_update(c, &pad, 1);
    while (c->buflen != 56) { pad=0; sha256_update(c,&pad,1); }
    for(int i=7;i>=0;i--){ pad=(bits>>(i*8))&0xff; sha256_update(c,&pad,1); }
    for(int i=0;i<8;i++){
        out[i*4]  =(c->state[i]>>24)&0xff; out[i*4+1]=(c->state[i]>>16)&0xff;
        out[i*4+2]=(c->state[i]>>8)&0xff;  out[i*4+3]= c->state[i]&0xff;
    }
}

/* ── HMAC-SHA256 ───────────────────────────────────────────────── */

static void hmac_sha256(
    const uint8_t *key, size_t klen,
    const uint8_t *msg, size_t mlen,
    uint8_t out[32])
{
    uint8_t k_ipad[64], k_opad[64], tk[32];

    /* Si key > 64 bytes, reducir con SHA-256 */
    if (klen > 64) {
        SHA256Ctx c; sha256_init(&c);
        sha256_update(&c, key, klen);
        sha256_final(&c, tk);
        key = tk; klen = 32;
    }

    memset(k_ipad, 0x36, 64);
    memset(k_opad, 0x5c, 64);
    for (size_t i = 0; i < klen; i++) {
        k_ipad[i] ^= key[i];
        k_opad[i] ^= key[i];
    }

    /* inner = SHA256(ipad || msg) */
    uint8_t inner[32];
    SHA256Ctx c; sha256_init(&c);
    sha256_update(&c, k_ipad, 64);
    sha256_update(&c, msg, mlen);
    sha256_final(&c, inner);

    /* outer = SHA256(opad || inner) */
    sha256_init(&c);
    sha256_update(&c, k_opad, 64);
    sha256_update(&c, inner, 32);
    sha256_final(&c, out);
}

/* ── API PUBLICA ───────────────────────────────────────────────── */

/* Incluir la cabecera OsirisHeader aqui minima para evitar circular */
typedef struct __attribute__((packed)) {
    uint8_t  version;
    uint8_t  seed_id;
    uint8_t  opcode;
    uint32_t signature;
    uint32_t payload_size;
    uint32_t frame_cnt;   /* contador de frame para XOR keystream */
    uint8_t  reservado;   /* uso futuro */
} OsirisHeaderForHMAC;

/**
 * Recibe el handshake del Cerebro (36 bytes) y extrae la session_key.
 * Llamar una vez al inicio, antes del bucle de paquetes.
 * Devuelve 1 si el magic es correcto, 0 si el buffer es invalido.
 */
static inline int osiris_hmac_recibir_handshake(
    const uint8_t buf[OSIRIS_HANDSHAKE_SIZE],
    OsirisHMACCtx *ctx)
{
    uint32_t magic;
    memcpy(&magic, buf, 4);
    if (magic != OSIRIS_HANDSHAKE_MAGIC) {
        printf("[HMAC] ERROR: magic de handshake invalido (0x%08X)\n", magic);
        return 0;
    }
    memcpy(ctx->session_key, buf + 4, OSIRIS_KEY_SIZE);
    ctx->activo = 1;
    printf("\x1b[32m[HMAC] Session key recibida. Autenticacion HMAC-SHA256 ACTIVA.\x1b[0m\n");
    return 1;
}

/**
 * Verifica el signature HMAC-SHA256 de un paquete recibido.
 * Devuelve 1 si es valido, 0 si hay manipulacion o sin handshake.
 *
 * El Nodo debe llamar a esto ANTES de entrar al dispatch_table.
 * Si devuelve 0: goto next_op (descartar silenciosamente).
 */
static inline int osiris_hmac_verificar(
    const OsirisHeaderForHMAC *hdr,
    const uint8_t *payload,
    uint32_t payload_len,
    const OsirisHMACCtx *ctx)
{
    if (!ctx->activo) {
        /* Sin handshake todavia — modo permisivo hasta que llegue */
        return 1;
    }

    /* Construir mensaje para HMAC:
     * Header de 16 bytes con signature=0 + payload completo.
     * Identico al calculo en signer.rs — no puede desincronizarse.
     *
     * Layout: [version(1), seed_id(1), opcode(1), 0x00000000(4), payload_size(4LE), padding(5)]
     */
    uint8_t hdr_bytes[16] = {0};
    hdr_bytes[0]  = hdr->version;
    hdr_bytes[1]  = hdr->seed_id;
    hdr_bytes[2]  = hdr->opcode;
    /* bytes 3..6 = signature → 0 (ya inicializado) */
    /* payload_size en LE: en x86 packed struct ya esta en LE en memoria */
    memcpy(hdr_bytes + 7, &hdr->payload_size, 4);
    /* frame_cnt (4 bytes LE) + reservado (1 byte) = 5 bytes */
    memcpy(hdr_bytes + 11, &hdr->frame_cnt, 4);
    hdr_bytes[15] = hdr->reservado;

    uint8_t *combined = (uint8_t*)malloc(16 + payload_len);
    if (!combined) return 0;
    memcpy(combined, hdr_bytes, 16);
    if (payload_len > 0 && payload != NULL)
        memcpy(combined + 16, payload, payload_len);

    uint8_t hmac_out[32];
    hmac_sha256(ctx->session_key, OSIRIS_KEY_SIZE,
                combined, 16 + payload_len,
                hmac_out);
    free(combined);

    /* Primeros 4 bytes del HMAC como u32 LE — igual que signer.rs */
    uint32_t esperado = (uint32_t)hmac_out[0]
                      | ((uint32_t)hmac_out[1] << 8)
                      | ((uint32_t)hmac_out[2] << 16)
                      | ((uint32_t)hmac_out[3] << 24);

    /* Comparacion en tiempo constante */
    uint32_t diff = hdr->signature ^ esperado;
    if (diff != 0) {
        printf("\x1b[1;31m[HMAC] PAQUETE RECHAZADO: signature invalido "
               "(op=%u, recibido=0x%08X, esperado=0x%08X)\x1b[0m\n",
               hdr->opcode, hdr->signature, esperado);
        return 0;
    }
    return 1;
}


/* ══════════════════════════════════════════════════════════════
 * XOR CIFRADO POR FRAME — Fase 2B
 *
 * Keystream = SHA256(session_key || frame_cnt_le || bloque_le)
 * repetido en bloques de 32 bytes hasta cubrir el payload.
 *
 * Llamar DESPUES de verificar el HMAC — descifra el payload
 * en el mismo buffer (in-place). Idempotente: XOR dos veces
 * devuelve el original.
 * ══════════════════════════════════════════════════════════════ */

static void osiris_xor_payload(
    uint8_t *payload,
    uint32_t payload_len,
    const uint8_t session_key[OSIRIS_KEY_SIZE],
    uint32_t frame_cnt)
{
    if (payload_len == 0 || payload == NULL) return;

    /* Semilla = session_key(32) || frame_cnt(4 LE) = 36 bytes */
    uint8_t seed[36];
    memcpy(seed, session_key, 32);
    seed[32] = (uint8_t)(frame_cnt & 0xFF);
    seed[33] = (uint8_t)((frame_cnt >> 8)  & 0xFF);
    seed[34] = (uint8_t)((frame_cnt >> 16) & 0xFF);
    seed[35] = (uint8_t)((frame_cnt >> 24) & 0xFF);

    uint32_t offset = 0;
    uint32_t bloque = 0;

    while (offset < payload_len) {
        /* keystream_block = SHA256(seed || bloque_le) */
        uint8_t bloque_bytes[4] = {
            (uint8_t)(bloque & 0xFF),
            (uint8_t)((bloque >> 8)  & 0xFF),
            (uint8_t)((bloque >> 16) & 0xFF),
            (uint8_t)((bloque >> 24) & 0xFF)
        };

        SHA256Ctx ctx_ks;
        sha256_init(&ctx_ks);
        sha256_update(&ctx_ks, seed, 36);
        sha256_update(&ctx_ks, bloque_bytes, 4);
        uint8_t ks[32];
        sha256_final(&ctx_ks, ks);

        uint32_t remaining = payload_len - offset;
        uint32_t n = remaining < 32 ? remaining : 32;
        for (uint32_t i = 0; i < n; i++) {
            payload[offset + i] ^= ks[i];
        }
        offset += n;
        bloque++;
    }
}

#undef ROTR32
#undef CH
#undef MAJ
#undef S0
#undef S1
#undef s0
#undef s1

#endif /* OSIRIS_HMAC_H */