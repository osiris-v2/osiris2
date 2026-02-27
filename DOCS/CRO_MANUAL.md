# Manual CRO — Command Request Object
### Osiris AI · Sistema de Comandos para Agentes Inteligentes
---

## Introducción

### ¿Qué es CRO?

CRO (*Command Request Object*) es el lenguaje intermedio que permite a un modelo de lenguaje grande (LLM) comunicarse con el sistema operativo y los servicios externos de forma estructurada, supervisada y segura.

En la arquitectura Osiris, la IA no ejecuta código directamente. En su lugar, **declara intenciones** usando bloques CRO embebidos en su respuesta de texto. Un módulo externo —el **CRO Parser**— lee esos bloques, los valida contra un esquema de definiciones, y el **CRO Translator** los convierte en comandos ejecutables reales, solicitando confirmación al operador humano cuando la acción lo requiere.

Este diseño resuelve uno de los problemas fundamentales de los agentes AI: cómo dar capacidad de acción real a un LLM sin perder el control humano sobre lo que ocurre en el sistema.

---

### ¿Por qué CRO y no llamadas directas a herramientas?

La mayoría de los frameworks de agentes exponen las herramientas directamente a la IA como funciones que el modelo invoca automáticamente. CRO adopta un enfoque diferente:

| Aspecto | Tool Calling directo | CRO |
|---|---|---|
| Confirmación humana | Opcional / ausente | Integrada en el flujo |
| Legibilidad | JSON interno | Texto estructurado visible |
| Auditoría | Difícil | Cada acción queda en el contexto |
| Control granular | Limitado | Por grupo, miembro y parámetro |
| Cancelación con contexto | No | El operador explica el motivo |

CRO es **deliberadamente visible**: el operador ve exactamente qué quiere hacer la IA antes de que ocurra, puede cancelarlo, y el motivo de la cancelación vuelve al contexto del modelo para que aprenda de ello en la misma sesión.

---

### El ciclo de vida de una acción CRO

```
┌──────────────┐    bloque ```CRO     ┌──────────────┐
│   Modelo AI  │ ──────────────────► │  CRO Parser  │
│  (Mistral)   │                     │  (valida)    │
└──────────────┘                     └──────┬───────┘
                                            │ acciones válidas
                                     ┌──────▼───────┐
                                     │CRO Translator│
                                     │ (convierte)  │
                                     └──────┬───────┘
                                            │ comando ejecutable
                                     ┌──────▼───────┐
                                     │  Operador    │
                                     │  Humano      │
                                     │  (confirma)  │
                                     └──────┬───────┘
                                            │ s/n + motivo
                                     ┌──────▼───────┐
                                     │   Sistema    │
                                     │  (ejecuta)   │
                                     └──────┬───────┘
                                            │ salida / error
                                     ┌──────▼───────┐
                                     │  Contexto AI │
                                     │  (MCX MGR)   │
                                     └──────────────┘
```

La salida del sistema —tanto si tuvo éxito como si falló— se inyecta de vuelta en el contexto del modelo como un fragmento `cro_system_output` o `cro_error`. En el siguiente turno, la IA tiene visibilidad completa de lo que ocurrió y puede continuar el razonamiento.

---

### Componentes del sistema

**`cro_definitions.py`** — El esquema de verdad. Define todos los grupos de comandos, sus miembros, y los parámetros aceptados por cada uno (tipo, si es requerido, si es dinámico, valores permitidos). El Parser y el Translator lo usan como fuente única.

**`cro_parser.py` → clase `CROParser`** — Lee la respuesta de texto del modelo, extrae los bloques ` ```CRO ``` `, los tokeniza línea a línea y valida cada parámetro contra `cro_definitions`. Soporta valores simples, comillas triples (`"""`) para contenido multilínea, y heredocs (`<<<DELIMITER`) para scripts complejos.

**`cro_parser.py` → clase `CROTranslator`** — Convierte cada acción validada en un comando ejecutable real (`bash -c`, `cat`, `ls`, llamada HTTP, etc.) y decide si necesita confirmación del operador (`needs_confirmation`).

**`mistral_context.py` → clase `MistralContextManager`** — Gestiona el historial de la conversación como fragmentos estructurados. Mantiene el orden cronológico estricto de los turnos user/assistant (crítico para la API de Mistral), ancla las instrucciones CRO al system prompt, y comprime el contexto automáticamente cuando se acerca al límite de tokens.

**`mistral2.py`** — El punto de entrada. Orquesta la conversación, activa/desactiva CROmode, ejecuta el ciclo Parser → Translator → confirmación → inyección de resultado en contexto.

---

## Referencia de Sintaxis

### Estructura básica

Todo bloque CRO debe estar envuelto en el delimitador de código con la etiqueta `CRO`:

````
```CRO
GRUPO_* MIEMBRO
PARAMETRO="valor"
```
````

**Reglas de formato:**
- La primera línea del bloque es siempre el **iniciador**: `GRUPO_* MIEMBRO`.
- Los parámetros van en líneas siguientes con formato `CLAVE="valor"`.
- Los valores **siempre** van entre comillas dobles.
- Múltiples miembros del mismo grupo se separan por coma: `GRUPO_* MIEMBRO1,MIEMBRO2`.
- Los nombres de grupo y miembro son siempre MAYÚSCULAS.

---

### Valores multilínea — Comillas triples

Para contenido que ocupa múltiples líneas o contiene caracteres especiales usa comillas triples `"""`. El contenido debe comenzar en la línea siguiente a la apertura y el cierre `"""` debe estar en su propia línea.

````
```CRO
LOCAL_FS_* WRITE_FILE
PATH="/ruta/archivo.py"
CONTENT="""
def saludo(nombre):
    print(f"Hola, {nombre}")

saludo("Osiris")
"""
OVERWRITE="True"
```
````

> **Importante:** si el contenido en sí incluye tres comillas dobles literales, escápalas como `\"\"\"`. El Translator las restaura antes de ejecutar.

---

### Valores multilínea — Heredocs

Para scripts o comandos que pueden contener cualquier carácter sin necesidad de escapar nada, usa heredocs con un delimitador en MAYÚSCULAS:

````
```CRO
EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
COMMAND=<<<FIN_CMD
echo "directorios:"
ls -la /home
df -h
FIN_CMD
```
````

El contenido entre el delimitador de apertura y el de cierre se toma **literalmente**, incluyendo comillas, saltos de línea y caracteres especiales.

---

## Grupos y Miembros

### `SEARCH_IN` — Búsquedas web

Realiza búsquedas en motores externos.

| Miembro | Descripción |
|---|---|
| `GOOGLE` | Búsqueda via Google Custom Search API |
| `BING` | Búsqueda via Bing |
| `OSIRIS_INTERNAL` | Búsqueda en la base de conocimiento interna |

**Parámetros comunes:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `QUERY` | string | ✅ | Términos de búsqueda |
| `TYPE` | enum | — | `text`, `image`, `video`, `pdf` (permite múltiples separados por coma) |
| `TAGS` | string | — | Solo para `OSIRIS_INTERNAL`. Etiquetas de filtrado |

**Ejemplo — búsqueda en Google:**
````
```CRO
SEARCH_IN_* GOOGLE
QUERY="vulnerabilidades log4j 2025"
TYPE="text,pdf"
```
````

**Ejemplo — múltiples motores simultáneos:**
````
```CRO
SEARCH_IN_* GOOGLE,BING
QUERY="python asyncio best practices"
TYPE="text"
```
````

> La API key y el CX code de Google los gestiona el Translator internamente, no deben incluirse en el bloque CRO.

---

### `EXECUTE_SYSTEM_ACTION` — Comandos de sistema

Ejecuta acciones sobre el sistema operativo. **Siempre requieren confirmación del operador.**

| Miembro | Descripción |
|---|---|
| `RUN_COMMAND` | Ejecuta un comando bash arbitrario |
| `REBOOT` | Reinicia el sistema |
| `SHUTDOWN` | Apaga el sistema |

**Parámetros de `RUN_COMMAND`:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `COMMAND` | string | ✅ | Comando bash a ejecutar |
| `INTERACTIVE` | boolean | — | Si `True`, no captura la salida (modo interactivo) |

**Ejemplo — comando simple:**
````
```CRO
EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
COMMAND="df -h && free -m"
```
````

**Ejemplo — script multilínea con heredoc:**
````
```CRO
EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
COMMAND=<<<FIN
#!/bin/bash
for dir in /var/log /tmp /home; do
    echo "=== $dir ==="
    ls -lh "$dir" | head -5
done
FIN
```
````

**Ejemplo — búsqueda en web específica con curl:**
````
```CRO
EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
COMMAND="curl -s 'https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=apache' | html2text -utf8 | head -80"
```
````

---

### `LOCAL_FS` — Sistema de archivos local

Operaciones de lectura y escritura sobre el sistema de archivos. **Siempre requieren confirmación del operador.**

| Miembro | Descripción |
|---|---|
| `LIST_DIRECTORY` | Lista el contenido de un directorio |
| `READ_FILE` | Lee el contenido de un archivo |
| `WRITE_FILE` | Escribe o crea un archivo |

**Parámetros de `LIST_DIRECTORY`:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `PATH` | string | ✅ | Ruta del directorio a listar |

**Parámetros de `READ_FILE`:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `PATH` | string | ✅ | Ruta del archivo a leer |
| `ENCODING` | enum | — | `utf-8` (default) o `latin-1` |
| `FLAGS` | enum | — | `WRITE_CONTEXT` — escribe el contenido en el contexto |

**Parámetros de `WRITE_FILE`:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `PATH` | string | ✅ | Ruta destino |
| `CONTENT` | string | ✅ | Contenido a escribir (soporta `"""` y heredoc) |
| `OVERWRITE` | boolean | — | `True` sobreescribe, `False` (default) añade al final |
| `ENCODING` | enum | — | `utf-8` (default) o `latin-1` |

**Ejemplo — listar directorio:**
````
```CRO
LOCAL_FS_* LIST_DIRECTORY
PATH="/var/www/html"
```
````

**Ejemplo — leer archivo:**
````
```CRO
LOCAL_FS_* READ_FILE
PATH="/etc/nginx/nginx.conf"
ENCODING="utf-8"
```
````

**Ejemplo — escribir archivo de configuración:**
````
```CRO
LOCAL_FS_* WRITE_FILE
PATH="/etc/osiris/config.json"
CONTENT="""
{
  "modo": "produccion",
  "log_level": "INFO",
  "max_tokens": 32000
}
"""
OVERWRITE="True"
ENCODING="utf-8"
```
````

---

### `LOG_OSIRIS` — Registro de sistema

Escribe entradas en el log del sistema Osiris. No requieren confirmación.

| Miembro | Descripción |
|---|---|
| `INFO` | Mensaje informativo |
| `WARN` | Advertencia |
| `ERROR` | Error crítico |

**Parámetros:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `MESSAGE` | string | ✅ | Texto del mensaje a registrar |

**Ejemplo:**
````
```CRO
LOG_OSIRIS_* INFO
MESSAGE="Operacion de backup completada. Archivos procesados: 142."
```
````

````
```CRO
LOG_OSIRIS_* WARN
MESSAGE="El operador cancelo la escritura en /etc/hosts. Motivo: riesgo de bloqueo."
```
````

---

### `DEFINE_VAR` — Variables de contexto

Persiste información en el contexto de la sesión. Útil para que la IA mantenga estado entre turnos. No requieren confirmación.

| Miembro | Descripción |
|---|---|
| `USER_QUERY_SUMMARY` | Resumen de la consulta actual (contexto permanente de sesión) |
| `TEMP_DATA` | Datos temporales clave-valor para la sesión |

**Parámetros de `USER_QUERY_SUMMARY`:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `VALUE` | string | ✅ | Texto del resumen |

**Parámetros de `TEMP_DATA`:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `KEY` | string | ✅ | Nombre de la variable |
| `VALUE` | string | ✅ | Valor a almacenar |

**Ejemplo:**
````
```CRO
DEFINE_VAR_* USER_QUERY_SUMMARY
VALUE="El operador solicitó auditoría de seguridad del servidor web en 192.168.1.10."
```
````

````
```CRO
DEFINE_VAR_* TEMP_DATA
KEY="target_ip"
VALUE="192.168.1.10"
```
````

---

### `REMOTE_FS` — Sistema de archivos remoto (SFTP)

Operaciones sobre sistemas remotos via SFTP. Requiere conexión previa con `--sshc`.

| Miembro | Descripción |
|---|---|
| `SFTP_LS` | Lista un directorio en el servidor remoto |

**Parámetros:**

| Parámetro | Tipo | Req. | Descripción |
|---|---|---|---|
| `PATH` | string | ✅ | Ruta en el servidor remoto (default: `.`) |

**Ejemplo:**
````
```CRO
REMOTE_FS_* SFTP_LS
PATH="/var/www/html/uploads"
```
````

---

### `WEB_MODE` — JavaScript en navegador

Solo disponible cuando el sistema opera en modo `WEB`. Ejecuta código JavaScript en el contexto del navegador.

| Miembro | Descripción |
|---|---|
| `JS` | Ejecuta una función JavaScript |

**Parámetros:**

| Parámetro | Tipo | Req. | Valores | Descripción |
|---|---|---|---|---|
| `FUNCTION` | enum | ✅ | `alert`, `console.log`, `redirect`, `set_element_text`, `custom_script` | Función a ejecutar |
| `MESSAGE` | string | — | — | Para `alert` y `console.log` |
| `URL` | string | — | — | Para `redirect` |
| `ELEMENT_ID` | string | — | — | Para `set_element_text` |
| `TEXT` | string | — | — | Para `set_element_text` |
| `SCRIPT` | string | — | — | Para `custom_script` (requiere confirmación) |

**Ejemplos:**
````
```CRO
WEB_MODE_* JS
FUNCTION="alert"
MESSAGE="Conexion establecida con el servidor."
```
````

````
```CRO
WEB_MODE_* JS
FUNCTION="set_element_text"
ELEMENT_ID="status-badge"
TEXT="Activo"
```
````

---

## Flujo de confirmación

### Acciones que siempre requieren confirmación

| Grupo | Miembro | Motivo |
|---|---|---|
| `EXECUTE_SYSTEM_ACTION` | `RUN_COMMAND` | Ejecución arbitraria en shell |
| `EXECUTE_SYSTEM_ACTION` | `REBOOT` / `SHUTDOWN` | Impacto en disponibilidad del sistema |
| `LOCAL_FS` | `WRITE_FILE` | Modificación de archivos |
| `LOCAL_FS` | `READ_FILE` | Acceso a datos del sistema |
| `LOCAL_FS` | `LIST_DIRECTORY` | Revelación de estructura de archivos |
| `REMOTE_FS` | `SFTP_LS` | Acceso a sistema remoto |

### Flujo de confirmación paso a paso

```
  [Osiris propone]
  💬 Comando propuesto:
     >>> ls -la '/home/usuario'

  ¿Deseas ejecutar este comando? (s/n): _
```

**Si el operador responde `s`:**

Se ejecuta el comando. La salida aparece en consola y el operador elige cómo incorporarla al contexto:

```
  ┌──────────────────────────────────────────────┐
  │   Opciones: Añadir Salida al Contexto        │
  │                                              │
  │  1) Añadir salida al contexto y continuar   │
  │  2) (1 + añadir mensaje tuyo a la IA)       │
  │  3) No añadir salida y continuar            │
  │  4) (3 + añadir mensaje tuyo a la IA)       │
  └──────────────────────────────────────────────┘
```

Opciones 2 y 4 permiten al operador adjuntar una instrucción o comentario que se envía junto con (o en lugar de) la salida del comando. Esto es útil para corregir el rumbo de la IA: *"La salida es correcta, pero céntrate solo en los archivos .log"*.

**Si el operador responde `n`:**

Se pide el motivo. El motivo se registra en el contexto como error con código 666 (cancelación humana), para que la IA sepa que la acción fue rechazada y por qué.

---

## Gestión del Contexto

### Fragmentos y tipos

El `MistralContextManager` mantiene el historial como una lista ordenada de fragmentos. Cada fragmento tiene tipo, contenido, timestamp, relevancia y banderas.

| Tipo | Cuándo se crea | Relevancia por defecto |
|---|---|---|
| `user_turn` | Cada mensaje del operador | 1.0 |
| `ai_response` | Cada respuesta del modelo | 1.0 (con CRO) / 0.85 |
| `cro_instruction` | Al activar CROmode | 1.0 |
| `cro_system_output` | Resultado de acción CRO | 0.9 |
| `cro_error` | Error de acción CRO | 0.7 |
| `system_instruction` | Instrucciones del sistema | 1.0 |
| `compressed_summary` | Resultado de compresión | 0.9 |

### Banderas

| Bandera | Efecto |
|---|---|
| `ESSENTIAL_CORE` | Nunca se purga ni comprime |
| `CRO_ACTIVE_INSTRUCTION` | Se ancla al system prompt |
| `HIGH_RELEVANCE` | Alta prioridad en compresión |
| `TEMPORARY_PIN` | Anclado temporalmente |
| `CRO_RESULT` | Marcado como salida de sistema |
| `CRO_IRRELEVANT` | Candidato a purga en compresión |
| `OBSOLETE` | Excluido del contexto enviado a la API |

### Orden de fragmentos en la API

Los fragmentos llegan a Mistral en este orden:

```
[system]     → instrucciones base + instrucciones CRO ancladas
[user]       → turno 1 del operador
[assistant]  → respuesta 1 de la IA
[user]       → salida CRO + turno 2 del operador (fusionados si son consecutivos)
[assistant]  → respuesta 2 de la IA
...
```

El orden cronológico se preserva **estrictamente**. Los fragmentos de alta relevancia NO se reordenan — solo los `cro_instruction` y `system_instruction` se extraen al bloque system.

### Compresión automática

Cuando el uso de tokens supera el 75% del límite configurado (por defecto 32.000), se dispara la compresión en pasos:

1. Purga de fragmentos `IRRELEVANT` / `OBSOLETE`
2. Inferencia Mistral para resumir los fragmentos de menor relevancia
3. Purga de salidas CRO no esenciales
4. Resumen agresivo (mayor número de fragmentos)
5. Purga forzosa conservando solo los últimos 4 turnos + esenciales

---

## Comandos del operador

### Gestión de CROmode

| Comando | Descripción |
|---|---|
| `--cm` / `--cromode` | Activa CROmode (carga `develop.info` y notifica al modelo) |
| `--cmc` / `--cromode-commute` | Alterna CROmode sin recargar instrucciones |
| `--exit` *(dentro del wCRO loop)* | Sale de la consola CRO y notifica al modelo |

### Gestión de contexto

| Comando | Descripción |
|---|---|
| `--ctx` | Estado del gestor (tokens, fragmentos, compresiones) |
| `--ctx-list` | Lista todos los fragmentos activos |
| `--ctx-compress` | Fuerza compresión manual |
| `--ctx-export [path]` | Exporta el contexto a JSON |
| `--ctx-import <path>` | Importa fragmentos desde JSON |
| `--ctx-reset` | Resetea el gestor (opcional: conserva esenciales) |
| `--cc` / `--clearcontext` | Limpia todo el contexto |

### Carga de archivos

| Comando | Descripción |
|---|---|
| `--l <archivo>` | Carga archivo en el buffer `load` |
| `--al <texto>` | Envía `load + texto` al modelo y limpia `load` |
| `--la` | Carga la última respuesta de la IA en `load` |
| `--lm <arc1> <arc2>` | Carga múltiples archivos al contexto |

---

## Buenas prácticas

**Usa CRO solo cuando sea necesario.** El hecho de que CROmode esté activo no significa que debas usarlo en cada respuesta. Para preguntas informativas, responde en lenguaje natural.

**Después de cada búsqueda, guarda un resumen.** Usar `DEFINE_VAR USER_QUERY_SUMMARY` inmediatamente después de una búsqueda importante evita que esa información se pierda en una compresión futura.

**Para auditorías de red, lanza comandos en cadena.** En una misma respuesta puedes incluir múltiples bloques CRO que el sistema ejecutará secuencialmente:

````
```CRO
EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
COMMAND="nmap -sV -p 22,80,443,8080 192.168.1.10"
```

```CRO
EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
COMMAND="whois 192.168.1.10"
```

```CRO
LOG_OSIRIS_* INFO
MESSAGE="Iniciando auditoria de red en 192.168.1.10"
```
````

**No inventes grupos o miembros.** Si necesitas una capacidad que no existe en `cro_definitions.py`, propónsela al desarrollador. El parser rechazará cualquier grupo o miembro no definido.

**Para contenido con caracteres especiales, prefiere heredoc sobre comillas triples.** El heredoc es más robusto porque no requiere ningún tipo de escape.

**Explica las acciones al operador antes de proponerlas.** Una breve frase antes del bloque CRO ayuda al operador a tomar una decisión informada al ver el prompt de confirmación.

---

## Referencia rápida

```
SEARCH_IN_* GOOGLE | BING | OSIRIS_INTERNAL
  QUERY="..."  TYPE="text|image|video|pdf"

EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
  COMMAND="..."  INTERACTIVE="True|False"

EXECUTE_SYSTEM_ACTION_* REBOOT | SHUTDOWN

LOCAL_FS_* LIST_DIRECTORY
  PATH="..."

LOCAL_FS_* READ_FILE
  PATH="..."  ENCODING="utf-8|latin-1"

LOCAL_FS_* WRITE_FILE
  PATH="..."  CONTENT="..."  OVERWRITE="True|False"

LOG_OSIRIS_* INFO | WARN | ERROR
  MESSAGE="..."

DEFINE_VAR_* USER_QUERY_SUMMARY
  VALUE="..."

DEFINE_VAR_* TEMP_DATA
  KEY="..."  VALUE="..."

REMOTE_FS_* SFTP_LS
  PATH="..."

WEB_MODE_* JS
  FUNCTION="alert|console.log|redirect|set_element_text|custom_script"
  MESSAGE="..."  URL="..."  ELEMENT_ID="..."  TEXT="..."  SCRIPT="..."
```

---

*Osiris AI · CRO Manual v4.0 · 2026*
