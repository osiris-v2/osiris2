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



# Modelo de Privacidad y Seguridad — Sistema Osiris

## Filosofía de diseño

Osiris no es un sistema que "añade seguridad encima". Es un sistema donde la
privacidad es una propiedad estructural desde el primer byte. Cada decisión
de arquitectura — memoria gestionada, zero persistence, canal dual, bytecode
propio — tiene una consecuencia directa en el modelo de privacidad.

La pregunta que guía el diseño no es "¿cómo ciframos esto?" sino
"¿cómo hacemos que no exista nada que capturar?".

---

## Modelo de amenaza

### ¿Qué protege Osiris?

- El **contenido del stream de video** frente a interceptación en tránsito
- Los **mensajes de texto** del usuario frente a volcados de memoria y forenses
- El **historial de sesión** frente a análisis post-mortem
- Los **modelos de IA** frente a extracción por terceros

### ¿Contra quién?

| Adversario | Capacidad | Nivel de protección Osiris |
|------------|-----------|---------------------------|
| Snifer de red pasivo | Captura paquetes TCP | Alto (con XOR/TLS activo) |
| Análisis forense de disco | Lee archivos del sistema | Total — nada toca disco |
| Volcado de memoria RAM | Lee el heap del proceso | Alto — zeroing garantizado en liberación |
| Proceso externo / debugger | ptrace, /proc/mem | Medio — detectable, mitigable |
| Auditoría del SO (EDR/Sysmon) | Eventos de proceso | Medio — mejora con renderer propio |
| Atacante con acceso físico | Hardware | Fuera del modelo de amenaza actual |

---

## Capas de protección

### Capa 1 — Zero Persistence (YA IMPLEMENTADA)

Nada del sistema escribe contenido sensible en disco durante operación normal.

- El stream de video vive y muere en el buffer Uranio (RAM)
- Los mensajes de texto del usuario nunca se escriben en `/tmp`, logs, ni bases de datos locales
- Al liberar cualquier bloque URANIO, `rb_liberar()` ejecuta `memset(data, 0, size)` antes del `free()`
- Al desconectar un cliente, la sesión completa se destruye atómicamente

**Garantía real:** Un análisis forense de disco posterior a una sesión no
encuentra rastro del contenido transmitido ni de los mensajes intercambiados.

```
Ciclo de vida de un mensaje de texto:
  
  Usuario escribe → RAM (buffer de entrada)
                  → Cifrado XOR en Cerebro
                  → TCP (bytes sin sentido)
                  → Buffer Uranio en Nodo
                  → Renderizado como píxeles (renderer propio)
                  → VRAM (desaparece al siguiente frame)
                  → memset + free al desconectar
  
  En ningún paso existe como texto en disco.
```

---

### Capa 2 — Cifrado de Contenido en Tránsito (IMPLEMENTACIÓN PENDIENTE)

#### 2a. XOR dinámico por frame (prioridad alta)

El Cerebro genera una clave de sesión única en cada conexión. Esa clave
nunca sale del proceso Rust — reside únicamente en memoria volátil.

Cada chunk de video o mensaje se ofusca con XOR usando una clave derivada de:
- La clave de sesión negociada en el handshake
- El timestamp del frame (rotación por frame)
- La firma FGN del chunk (entropía del contenido propio)

```rust
// Cerebro — antes de enviar el chunk:
fn xor_frame(data: &mut [u8], session_key: &[u8], frame_id: u64) {
    let key_material = derive_frame_key(session_key, frame_id);
    for (byte, key_byte) in data.iter_mut().zip(key_material.iter().cycle()) {
        *byte ^= key_byte;
    }
}

// Nodo C — después de leer del buffer Uranio:
// Misma operación, misma clave derivada → recupera el contenido original
// La contra-operación ocurre justo antes del renderizado, no antes.
```

**Efecto forense:** Un snifer que capture el tráfico TCP ve bytes sin
estructura reconocible. Sin la clave de sesión (que solo existe en RAM del
Cerebro durante la sesión), los bytes son matemáticamente inútiles.

#### 2b. TLS en el canal TCP (prioridad media)

XOR protege el contenido. TLS protege el canal completo incluyendo
los headers del protocolo Osiris, los opcodes, y los tamaños de payload.

Con ambas capas activas un atacante de red no puede determinar ni qué tipo
de operación se está ejecutando ni cuánto datos contiene.

---

### Capa 3 — Protección de Mensajes de Texto de Usuario

Esta capa es específica para el flujo de texto (comandos ODS, mensajes al
servidor IA, interacción con Ollama).

#### El problema del texto en memoria

Con una aplicación normal, un mensaje de texto existe en varias copias:
- El string original en el heap
- La copia en el buffer de red
- La copia en el log del servidor
- La respuesta almacenada en el historial

Cualquier volcado de memoria puede extraer conversaciones completas
buscando cadenas de texto legibles.

#### La solución Osiris: texto que nunca es texto en el Nodo

```
CEREBRO (Rust)                          NODO (C)
──────────────────────────────────────────────────────
Recibe mensaje de texto del usuario
         │
         ▼
Renderiza el texto como imagen pequeña
(píxeles, no caracteres)
         │
         ▼
Empaqueta como chunk de video           Recibe bytes de video
con opcode 7 (stream normal)     ──→    (no sabe que es texto)
                                                │
                                                ▼
                                        Vuelca en buffer URANIO
                                                │
                                                ▼
                                        Renderer SDL2/OpenGL
                                        pinta píxeles en pantalla
                                                │
                                                ▼
                                        Buffer URANIO → memset → free
```

**Garantía:** Un volcado de RAM del proceso del Nodo buscando la cadena
"contraseña" o cualquier texto del usuario no encontrará nada.
Solo existe como datos de píxel comprimidos en MPEG-TS.

#### Destrucción atómica del historial

En `server.rs` (servidor IA), el historial de conversación vive en
`ClientSession.history_text` — un `Vec` en heap de Rust.

Al desconectar, la sesión se elimina con `AI_SESSIONS.remove(&client_id)`.
Para garantía completa, antes del drop se sobreescribe:

```rust
// Al desconectar — destrucción segura del historial:
if let Some(mut session) = sessions.remove(&client_id) {
    // Sobreescribir cada mensaje antes de soltar la memoria
    for (user_msg, assistant_msg) in session.history_text.iter_mut() {
        // Sobreescribir con ceros lógicos
        user_msg.as_bytes_mut().fill(0);       
        assistant_msg.as_bytes_mut().fill(0);
    }
    // El drop libera la memoria ya limpia
}
```

---

### Capa 4 — Opacidad ante el Sistema Operativo

#### Estado actual (con ffplay)

El SO ve: `osiris_node` + `ffplay` como procesos separados.
Un EDR ve una conexión TCP en puerto 2000 con tráfico continuo.

#### Estado objetivo (con renderer propio SDL2/X11)

El SO ve: un único proceso `osiris_node` dibujando en pantalla.
No hay proceso multimedia externo. No hay pipe entre procesos.
El tráfico TCP sigue visible (inevitable) pero el contenido es opaco.

**Lo que el SO registra con renderer propio:**
```
"El proceso osiris_node está actualizando su buffer de video"
```

**Lo que el SO NO puede ver:**
- Qué instrucciones FGN se están ejecutando
- Qué contenido tiene el stream
- Si el stream es video, texto, o comandos de VM

#### Aislamiento de memoria

`RB_SafePtr` garantiza que no haya desbordamientos de buffer.
Los desbordamientos son una de las señales que los EDR modernos usan para
detectar actividad anómala. Un proceso que nunca desborda es invisible
para esa categoría de detección.

---

### Capa 5 — Integridad del Canal (Autenticación)

#### Estado actual

La firma en `OsirisPacket` es un hash de 32 bits con semilla fija.
Sirve para detectar corrupción accidental, no para autenticar el origen.

#### Objetivo: HMAC-SHA256 por sesión

```rust
// En signer.rs — versión hardened:
use hmac::{Hmac, Mac};
use sha2::Sha256;

pub fn generate_signature(
    packet: &OsirisPacket, 
    payload: &[u8],
    session_key: &[u8]      // Clave única por sesión, nunca fija
) -> [u8; 32] {
    let mut mac = Hmac::<Sha256>::new_from_slice(session_key)
        .expect("HMAC acepta cualquier longitud de clave");
    mac.update(&[packet.opcode]);
    mac.update(&packet.payload_size.to_le_bytes());
    mac.update(payload);
    mac.finalize().into_bytes().into()
}
```

Con HMAC-SHA256 un atacante que inyecte paquetes manipulados en el canal
no puede forjar una firma válida sin conocer la clave de sesión.

---

## Hoja de ruta de implementación

### Fase 1 — Fundación (trabajo actual)
- [x] Zero persistence con URANIO zeroing
- [x] Canal dual datos/control
- [x] Buffer Uranio con límites validados
- [ ] Validar `payload_size` contra `URANIO_MAX_BLOQUE` antes de rescale
- [ ] Unificación de tipos `RB_SafePtr`
- [ ] Fix del protocolo header C/Rust

### Fase 2 — Privacidad del canal
- [ ] XOR dinámico por frame (clave de sesión en RAM volátil)
- [ ] Handshake de intercambio de clave de sesión
- [ ] HMAC-SHA256 en signer.rs
- [ ] TLS sobre el canal TCP

### Fase 3 — Privacidad del contenido
- [ ] Renderer propio SDL2/OpenGL (eliminar ffplay)
- [ ] Renderizado de texto como píxeles en Cerebro
- [ ] Destrucción segura del historial en server.rs
- [ ] Volcado directo a VRAM sin copia intermedia

### Fase 4 — Hardening del proceso
- [ ] Detección de ptrace / anti-debug en el Nodo C
- [ ] Bloqueo de core dumps (`prctl(PR_SET_DUMPABLE, 0)`)
- [ ] Memoria bloqueada en RAM (`mlock`) para buffers URANIO críticos

---

## Propiedades verificables hoy

Estas afirmaciones están respaldadas directamente por código existente
y son auditables:

> "Ningún byte de contenido sensible sobrevive a la desconexión en disco"
> → `rb_liberar()` en `rb_csp.c`, línea del `memset`

> "El buffer de recepción nunca excede su capacidad declarada"  
> → validación en `op_stream` de `main.c` con `rb_rescale`

> "Los comandos de control no bloquean el flujo de datos"
> → arquitectura de canal dual, puertos 2000 y 2001 independientes

> "Cada sesión de IA es completamente independiente de las anteriores"
> → `ClientSession` en `server.rs`, destruida al desconectar

---

## Lo que Osiris NO garantiza (honestidad del modelo)

- **No protege contra el sistema operativo comprometido.** Si el kernel
  está bajo control de un atacante, ninguna medida en espacio de usuario
  es suficiente.

- **No oculta la existencia de la conexión TCP.** Un firewall o IDS puede
  ver que hay tráfico entre dos IPs en los puertos configurados.

- **El XOR no es cifrado criptográfico fuerte.** Proporciona opacidad del
  contenido pero no autenticación. TLS + HMAC son necesarios para
  garantías criptográficas reales.

- **Mientras se use ffplay**, los frames pasan por un proceso externo sin
  las protecciones de memoria de Osiris.