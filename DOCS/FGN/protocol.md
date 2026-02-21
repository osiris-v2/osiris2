# Protocolo de Red Osiris

## ¿Qué es esto?

Cuando el **Cerebro** (el servidor en Rust) envía video al **Nodo** (el cliente en C), no manda los datos a ciegas. Cada envío va precedido de un pequeño "sobre" de 16 bytes que explica qué contiene y qué debe hacer el Nodo con ello. A ese sobre lo llamamos **OsirisPacket** o **header**.

Es el mismo principio que una carta: el sobre tiene el remitente, el destinatario y el tipo de contenido antes de que abras nada.

---

## El sobre de 16 bytes

Cada mensaje entre Cerebro y Nodo empieza con exactamente **16 bytes** estructurados así:

```
Byte 0       → version       ¿Qué versión del protocolo usamos? (actualmente: 2)
Byte 1       → seed_id       ID interno para la firma de seguridad
Byte 2       → opcode        ¿Qué debe hacer el Nodo con esto?
Bytes 3-6    → signature     Firma de integridad del contenido (4 bytes)
Bytes 7-10   → payload_size  ¿Cuántos bytes vienen después del sobre? (4 bytes)
Bytes 11-15  → padding       Relleno para llegar a 16 bytes exactos
```

Después de estos 16 bytes viene el **payload**: los datos reales (el chunk de video, o un comando, etc.).

---

## El opcode: la orden del sobre

El **opcode** (byte 2) es el número que le dice al Nodo qué hacer. Es como el asunto de un email.

| Opcode | Nombre        | ¿Qué significa?                                         |
|--------|---------------|---------------------------------------------------------|
| `5`    | RESCALE       | "Agranda o achica tu buffer de memoria a N bytes"       |
| `7`    | VIDEO         | "Lo que viene después es un trozo de video, reprodúcelo"|
| `9`    | EXIT          | "Cierra la conexión de forma ordenada"                  |
| `10`   | PAUSE         | "Pausa o reanuda el video"                              |
| `15`   | SKIP          | "Salta a otro punto del video"                          |
| `22`   | IA_UPDATE     | "Lo que viene es un modelo de IA nuevo, cárgalo"        |

---

## La firma de integridad

Los bytes 3-6 contienen una **firma** calculada sobre el contenido del payload. Antes de procesar cualquier dato, el Nodo puede verificar que la firma coincide para asegurarse de que el mensaje no llegó corrupto.

El algoritmo es simple: se parte de una semilla fija (`0x1337BEEF`), se mezcla con el opcode y el tamaño, y se procesa cada byte del payload con rotaciones de bits. El resultado es un número de 4 bytes.

No es criptografía fuerte — es detección de corrupción accidental, similar a un CRC.

---

## Los dos canales

El sistema usa **dos conexiones TCP simultáneas**:

```
Puerto 2000 → Canal de DATOS   → chunks de video (flujo continuo, alto volumen)
Puerto 2001 → Canal de CONTROL → comandos (pausa, salto, modelos IA)
```

Separarlos garantiza que un comando de pausa nunca quede bloqueado detrás de un chunk de video de 16MB esperando transmitirse. Es el mismo principio que usa el protocolo FTP desde los años 70.

---

## Flujo completo de un frame de video

```
CEREBRO (Rust)                              NODO (C)
──────────────────────────────────────────────────────
1. FFmpeg decodifica un chunk de video
2. Calcula la firma del chunk
3. Construye OsirisPacket:
     version=2, opcode=7,
     signature=<calculada>,
     payload_size=<N bytes>
4. Envía: [16 bytes header] + [N bytes video]
                                    5. Lee 16 bytes → OsirisHeader
                                    6. Verifica version == 2
                                    7. Lee opcode=7 → op_stream
                                    8. Lee payload_size=N bytes de video
                                    9. Escribe en buffer Uranio
                                   10. Pasa a ffplay por pipe
```

---

## ¿Por qué 16 bytes exactos?

Porque es conveniente para la CPU. Los procesadores modernos leen memoria en bloques alineados de 8 o 16 bytes. Un header de 16 bytes se lee en un solo acceso de memoria, sin penalizaciones de alineación. El padding de 5 bytes al final no es desperdicio — es precisión de ingeniería.

---

## Archivos relevantes

| Archivo | Rol |
|---------|-----|
| `cerebro_semilla/src/network/protocol.rs` | Define `OsirisPacket` en Rust |
| `nodo_musculo/src/main.c` | Lee el header con `OsirisHeader` en C |
| `cerebro_semilla/src/security/signer.rs` | Calcula la firma de integridad |
| `nodo_musculo/include/fgn_protocol.h` | Diccionario de opcodes y formato `FGN_Opcode96` |




# Safe Pointers y Sistema de Tipos en Osiris

## El problema que resuelven

En C, un puntero normal es simplemente una dirección de memoria. No sabe cuántos bytes ocupa, no sabe si ya fue liberado, y no avisa si dos partes del código intentan liberarlo a la vez. Esto produce los errores más difíciles de depurar: crashes aleatorios, datos corruptos, o memory leaks silenciosos.

Osiris introduce los **Safe Pointers** (`RB_SafePtr`) para resolver exactamente eso.

---

## RB_SafePtr: el puntero que sabe lo que es

Un `RB_SafePtr` no es solo una dirección. Es una estructura que lleva consigo toda la información necesaria para manejarse de forma segura:

```c
typedef struct {
    void*      data;        // La dirección real de la memoria
    uint32_t   size;        // Cuántos bytes ocupa
    Hardness   hardness;    // Qué nivel de protección tiene
    uint32_t*  ref_count;   // Cuántas partes del código lo están usando
    FaseEstado estado;      // En qué fase del ciclo de vida está
    double     coherencia;  // Qué tan íntegro está [0.0 - 1.0]
} RB_SafePtr;
```

Piénsalo como una caja con etiqueta. La caja tiene el contenido (`data`), pero también dice cuánto cabe (`size`), cuántas personas la tienen abierta (`ref_count`), y si ya se usó y se cerró (`estado`).

---

## Los niveles de dureza (Hardness)

Cada bloque de memoria tiene un nivel de dureza que define su política de gestión:

### ACERO
Memoria temporal y de corta vida. Se usa para buffers intermedios que se crean y destruyen rápidamente. Sin protecciones especiales más allá de las básicas.

```c
RB_SafePtr buf = crear_bloque(1024, ACERO);
// Úsalo, libéralo. Ciclo de vida corto.
```

### DIAMANTE
Memoria de larga vida. Para estructuras del compilador, tablas de handlers, datos que persisten durante toda la sesión. Más cuidado en su gestión.

```c
RB_SafePtr tabla = crear_bloque(sizeof(OsirisHandler) * 1024, DIAMANTE);
// Vive mientras viva el sistema.
```

### URANIO
Memoria crítica. Antes de liberarse, **todos sus bytes se ponen a cero** (`memset` garantizado). Esto asegura que datos sensibles — modelos de IA, claves, buffers de red — no queden flotando en memoria después de usarse.

```c
RB_SafePtr modelo = crear_bloque(65536, URANIO);
// Al liberar: los bytes se borran primero, luego se libera.
```

---

## El ref_count: compartir sin miedo

El mayor peligro de la memoria compartida es que dos partes del código intenten liberarla. `RB_SafePtr` lo evita con un contador de referencias:

```
Crear bloque     → ref_count = 1
rb_adquirir()    → ref_count = 2  (otra parte del código lo quiere usar)
rb_liberar()     → ref_count = 1  (esa parte termina)
rb_liberar()     → ref_count = 0  → SE LIBERA LA MEMORIA
```

Mientras `ref_count > 0`, la memoria no se toca. Solo cuando nadie la necesita se destruye. Es el mismo mecanismo que usa `Arc` en Rust o los smart pointers de C++.

---

## Los estados de fase

Un bloque puede estar en tres estados:

**ESTADO_PARTICULA** — estado normal. Un propietario, coherencia 1.0. Es como un objeto sólido: definido, localizado, manejable.

**ESTADO_BIFURCADO** — el bloque fue bifurcado. Dos partes del código apuntan al mismo bloque físico. Cada una ve coherencia 0.5. Ninguna modifica hasta que se colapsa. Útil para pasar el mismo frame de video al renderer y al analizador FGN simultáneamente sin copiar.

**ESTADO_VOID** — memoria liberada. No acceder. El puntero `data` es NULL.

---

## Bifurcar y colapsar: cero copias

Una de las operaciones más potentes del sistema es la bifurcación:

```c
RB_SafePtr original = crear_bloque(1920*1080*3, URANIO); // Frame de video
RB_SafePtr alfa, beta;

rb_bifurcar_onda(&original, &alfa, &beta);
// alfa y beta apuntan al MISMO bloque físico
// ref_count = 2, coherencia de cada uno = 0.5
// No se copió ni un byte

// Ahora:
// - alfa va al renderer OpenGL
// - beta va al analizador FGN
// Ambos leen el mismo frame en paralelo

rb_colapsar_observacion(&alfa, &beta, &resultado);
// Volvemos a un propietario
// ref_count = 1, coherencia = 1.0
```

Sin bifurcación habría que copiar el frame dos veces. Con bifurcación, cero copias.

---

## ODS_SafeRef: el descriptor de auditoría

El **ODS Engine** (la shell del sistema) tiene su propio descriptor más ligero llamado `ODS_SafeRef`. Es importante no confundirlo con `RB_SafePtr`:

| | `RB_SafePtr` | `ODS_SafeRef` |
|---|---|---|
| **Rol** | Gestiona memoria real | Solo audita variables ODS |
| **Hace malloc/free** | Sí | No |
| **Tiene ref_count** | Sí | No |
| **Para qué sirve** | Runtime, buffers, modelos | Inspección con `~` y `#` |

`ODS_SafeRef` guarda la dirección, el límite y un hash del valor de cada variable ODS. Cuando usas el operador `~variable` en la shell, lo que ves es el contenido de su `ODS_SafeRef`.

---

## Flujo de vida de un bloque Uranio típico

```
crear_bloque(N, URANIO)
    → malloc(N)
    → ref_count = 1
    → estado = ESTADO_PARTICULA
    → coherencia = 1.0
         │
         ▼
    [escribir datos]
         │
         ▼ (si se comparte)
    rb_adquirir()
    → ref_count = 2
         │
         ▼
    rb_liberar() x2
    → ref_count = 0
    → memset(data, 0, size)   ← zeroing garantizado (URANIO)
    → free(data)
    → estado = ESTADO_VOID
```

---

## Archivos relevantes

| Archivo | Rol |
|---------|-----|
| `nodo_musculo/include/rb_csp.h` | Definición maestra de `RB_SafePtr` y `Hardness` |
| `nodo_musculo/src/mem/rb_csp.c` | Implementación de `crear_bloque`, `rb_liberar`, bifurcación |
| `nodo_musculo/include/ods_definiciones.h` | Definición de `ODS_SafeRef` y `VariableODS` |
| `nodo_musculo/src/core/ods_memoria.c` | Gestión del almacén de variables ODS |

---

## Regla de oro

> Si incluyes `rb_csp.h`, **no** incluyas `uranio.h` ni `ods_definiciones.h` en la misma unidad de compilación. `rb_csp.h` es la única fuente de verdad para `RB_SafePtr`.