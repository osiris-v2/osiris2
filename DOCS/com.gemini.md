

## Manual de Uso del Módulo "gemini"

Este manual te ayudará a comprender cómo funciona el módulo "gemini" para interactuar con la API de Google Gemini y generar contenido a partir de texto e imágenes.

### Descripción General

El módulo "gemini" es un script Python que ofrece una interfaz de línea de comandos para utilizar el modelo generativo Gemini de Google. Permite generar texto, cargar y procesar imágenes, guardar y cargar conversaciones, así como configurar varios parámetros del modelo. Para usar el módulo "gemini", debes montarlo en tu programa principal usando la función `mount gemini`.

### Requisitos Previos

* **Python 3:** Asegúrate de tener Python 3 instalado en tu sistema.
* **Google Gemini API:** Debes tener una cuenta de Google Cloud y una API Key válida para la API de Gemini.
* **Librerías:** 
    * `google-generativeai`
    * `PIL` (Pillow)
    * `tkinter`
    * `json`
    * `os`

### Configuración

1. **Obtener API Key:**
    * Visita la consola de Google Cloud: [https://console.cloud.google.com/](https://console.cloud.google.com/)
    * Crea un nuevo proyecto o utiliza uno existente.
    * Habilita la API de Gemini y crea una API Key.

2. **Configurar el módulo:**
    * **Opción 1: Variable de entorno:**
        * Define la variable de entorno `GOOGLE_API_KEY` con tu API Key antes de ejecutar el script.
    * **Opción 2: Código:**
        * Sustituye el valor de la variable `API_KEY` en el script con tu API Key real.

3. **Instalar dependencias:**
    * Ejecuta el siguiente comando en tu terminal:
    ```bash
    pip install google-generativeai pillow tkinter
    ```

### Cómo Ejecutar el Módulo

1. **Abre una terminal o línea de comandos.**
2. **Navega hasta la ubicación del archivo "gemini.py".**
3. **Ejecuta el módulo usando la función `mount gemini` en tu programa principal.**
4. **Ejecuta comandos usando la siguiente sintaxis:** `>>>gemini> <comando> <argumentos>`
5. **Reemplaza `<comando>` y `<argumentos>` con los comandos y argumentos específicos que deseas utilizar.**

### Comandos Disponibles

**Comandos de Generación:**

* **`<texto>`:** Genera una respuesta basada en el texto ingresado.
    * Ejemplo: `>>>gemini> "¿Cómo funciona la API de Gemini?"`
* **`--li <ruta_de_la_imagen>`:** Genera texto a partir de una imagen.
    * Ejemplo: `>>>gemini> --li "imagen.jpg"`

**Comandos de Carga y Guardado:**

* **`--load <ruta_del_archivo>`:** Carga un archivo de texto y lo almacena en la variable `load`.
    * Ejemplo: `>>>gemini> --load "archivo.txt"`
* **`--addload <texto>`:** Añade el contenido del archivo cargado (`load`) al texto ingresado y lo envía al modelo para generar una respuesta.
    * Ejemplo: `>>>gemini> --addload "Esto es una prueba"`
* **`--showload`:** Muestra el contenido de la variable `load`.
* **`--saveload <nombre_de_archivo>`:** Guarda el contexto actual de la conversación en un archivo.
    * Ejemplo: `>>>gemini> --saveload "mi_conversacion"`
* **`--saverequest <texto>`:** Guarda una solicitud de usuario en un archivo.
* **`--saveanswer`:** Guarda la última respuesta del modelo en un archivo.
* **`--savecontext`:** Guarda el contexto completo de la conversación en un archivo.

**Comandos de Manejo de Contexto:**

* **`--showwin`:** Muestra el contexto actual de la conversación en una ventana de tkinter.
* **`--clearcontext`:** Borra el contexto actual de la conversación.
* **`--loadselect <ruta_del_archivo>`:** Carga un contexto de conversación específico desde un archivo y lo agrega al contexto actual.
* **`--loadmultiple <ruta_archivo1> <ruta_archivo2> ...`:** Carga múltiples contextos de conversación desde archivos y los agrega al contexto actual.
* **`--export <nombre_de_archivo>`:** Exporta el contexto de la conversación actual a un archivo JSON.
* **`--import <nombre_de_archivo>`:** Importa un contexto de conversación desde un archivo JSON.
* **`--search <término>`:** Busca un término en el contexto de la conversación actual.

**Comandos de Configuración:**

* **`--autosave`:** Guarda automáticamente la última respuesta y el contexto de la conversación.
* **`--newquestions <pregunta_base>`:** Genera preguntas relacionadas a partir de una pregunta base.
* **`--send <texto>`:** Envía un mensaje al modelo sin agregar al contexto actual.
* **`--listfiles`:** Muestra una lista de los archivos en el directorio "com/datas".
* **`--info`:** Muestra información del modelo, incluyendo el contexto actual.
* **`--settopic <tema>`:** Establece un tema para la conversación.
* **`--reset`:** Resetea todos los valores y el contexto de la conversación.
* **`--loadconfig <ruta_del_archivo>`:** Carga las configuraciones desde un archivo JSON.
    * Ejemplo: `>>>gemini> --loadconfig "configuracion.json"`
* **`--log <texto> <respuesta>`:** Guarda una interacción de usuario y respuesta en un archivo de log.
    * Ejemplo: `>>>gemini> --log "Hola" "Hola a ti también!"`
* **`--setparams <parametro1=valor1> <parametro2=valor2> ...`:** Configura parámetros del modelo, como `temperature` y `max_tokens`.
    * Ejemplo: `>>>gemini> --setparams temperature=0.5 max_tokens=150`
* **`--toggleautosave <on/off>`:** Activa o desactiva la función de autosave.
    * Ejemplo: `>>>gemini> --toggleautosave on`

### Argumentos de Línea de Comando

Los argumentos de línea de comando son valores que se proporcionan después del comando principal para especificar opciones o parámetros adicionales.

* **`<texto>`:** El texto que se utilizará para generar contenido.
* **`<ruta_de_la_imagen>`:** La ruta al archivo de imagen que se utilizará para generar texto.
* **`<ruta_del_archivo>`:** La ruta al archivo que se va a cargar o guardar.
* **`<nombre_de_archivo>`:** El nombre del archivo que se va a crear o usar.
* **`<término>`:** El término que se va a buscar en el contexto de la conversación.
* **`<tema>`:** El tema que se va a establecer para la conversación.
* **`<parametro1=valor1> <parametro2=valor2> ...`:** Parámetros que se van a configurar para el modelo.

### Opciones de Configuración

* **`api_key`:** La API Key para la API de Google Gemini. Se puede definir como una variable de entorno (`GOOGLE_API_KEY`) o en el código.

### Ejemplos de Uso

```bash
# Generar texto a partir de una pregunta
>>>gemini> "¿Cómo funciona la API de Gemini?"

# Generar texto a partir de una imagen
>>>gemini> --li "imagen.jpg"

# Cargar un archivo de texto
>>>gemini> --load "archivo.txt"

# Añadir contenido cargado al texto ingresado
>>>gemini> --addload "Esto es una prueba"

# Mostrar el contenido del archivo cargado
>>>gemini> --showload

# Guardar el contexto actual de la conversación
>>>gemini> --saveload "mi_conversacion"

# Guardar una solicitud de usuario en un archivo
>>>gemini> --saverequest "Quiero saber más sobre los gatos."

# Guardar la última respuesta del modelo en un archivo
>>>gemini> --saveanswer

# Guardar el contexto completo de la conversación en un archivo
>>>gemini> --savecontext

# Mostrar el contexto actual de la conversación en una ventana de tkinter
>>>gemini> --showwin

# Borrar el contexto actual de la conversación
>>>gemini> --clearcontext

# Cargar un contexto de conversación específico desde un archivo
>>>gemini> --loadselect "contexto_1.json"

# Cargar múltiples contextos de conversación desde archivos
>>>gemini> --loadmultiple "contexto_1.json" "contexto_2.json"

# Exportar el contexto de la conversación actual a un archivo JSON
>>>gemini> --export "mi_conversacion.json"

# Importar un contexto de conversación desde un archivo JSON
>>>gemini> --import "mi_conversacion.json"

# Buscar un término en el contexto de la conversación actual
>>>gemini> --search "gatos"

# Activar el autosave
>>>gemini> --autosave

# Generar preguntas relacionadas a partir de una pregunta base
>>>gemini> --newquestions "¿Cómo funciona la API de Gemini?"

# Enviar un mensaje al modelo sin agregar al contexto actual
>>>gemini> --send "Hola, ¿qué tal?"

# Mostrar una lista de los archivos en el directorio "com/datas"
>>>gemini> --listfiles

# Mostrar información del modelo, incluyendo el contexto actual
>>>gemini> --info

# Establecer un tema para la conversación
>>>gemini> --settopic "Programación"

# Resetea todos los valores y el contexto de la conversación
>>>gemini> --reset

# Cargar las configuraciones desde un archivo JSON
>>>gemini> --loadconfig "configuracion.json"

# Guardar una interacción de usuario y respuesta en un archivo de log
>>>gemini> --log "Hola" "Hola a ti también!"

# Configurar parámetros del modelo
>>>gemini> --setparams temperature=0.5 max_tokens=150

# Activar/desactivar la función de autosave
>>>gemini> --toggleautosave on
```

### Solución de Problemas

* **Error de API Key:** Verifica que tu API Key sea válida y esté configurada correctamente en el script o en las variables de entorno.
* **Error de conexión:** Asegúrate de tener una conexión a Internet activa.
* **Error de dependencias:** Asegúrate de que las librerías necesarias estén instaladas correctamente.
* **Error de permisos:** Es posible que necesites permisos especiales para acceder a archivos o guardar información.

### Notas Adicionales

* El módulo "gemini" se encuentra en desarrollo y puede tener nuevas funciones y comandos en el futuro.
* Es importante tener en cuenta que la API de Google Gemini tiene sus propias políticas de uso y límites de uso. Consulta la documentación oficial para obtener más información.

Si tienes alguna duda o necesitas más información, por favor, no dudes en consultar la documentación oficial de la API de Google Gemini o contactar con el desarrollador.

### Tabla de Comandos con Sinónimos Cortos

| Comando Completo | Sinónimo Corto | Descripción |
|---|---|---|
| `--load <ruta_del_archivo>` | `--l` | Carga un archivo de texto y lo almacena en la variable `load`. |
| `--addload <texto>` | `--al` | Añade el contenido del archivo cargado (`load`) al texto ingresado y lo envía al modelo para generar una respuesta. |
| `--showload` | `--sl` | Muestra el contenido de la variable `load`. |
| `--loadimage <ruta_de_la_imagen>` | `--li` | Genera texto a partir de una imagen. |
| `--showwin` | `--sw` | Muestra el contexto actual de la conversación en una ventana de tkinter. |
| `--saveload <nombre_de_archivo>` | `--sav` | Guarda el contexto actual de la conversación en un archivo. |
| `--saverequest <texto>` | `--sr` | Guarda una solicitud de usuario en un archivo. |
| `--saveanswer` | `--sa` | Guarda la última respuesta del modelo en un archivo. |
| `--savecontext` | `--sc` | Guarda el contexto completo de la conversación en un archivo. |
| `--autosave` | `--as` | Guarda automáticamente la última respuesta y el contexto de la conversación. |
| `--newquestions <pregunta_base>` | `--nq` | Genera preguntas relacionadas a partir de una pregunta base. |
| `--send <texto>` | `--s` | Envía un mensaje al modelo sin agregar al contexto actual. |
| `--listfiles` | `--ls` | Muestra una lista de los archivos en el directorio "com/datas". |
| `--clearcontext` | `--cc` | Borra el contexto actual de la conversación. |
| `--loadselect <ruta_del_archivo>` | `--lsel` | Carga un contexto de conversación específico desde un archivo y lo agrega al contexto actual. |
| `--loadmultiple <ruta_archivo1> <ruta_archivo2> ...` | `--lm` | Carga múltiples contextos de conversación desde archivos y los agrega al contexto actual. |
| `--info` | `--i` | Muestra información del modelo, incluyendo el contexto actual. |
| `--export <nombre_de_archivo>` | `--exp` | Exporta el contexto de la conversación actual a un archivo JSON. |
| `--import <nombre_de_archivo>` | `--imp` | Importa un contexto de conversación desde un archivo JSON. |
| `--search <término>` | `--s` | Busca un término en el contexto de la conversación actual. |
| `--settopic <tema>` | `--st` | Establece un tema para la conversación. |
| `--reset` | `--r` | Resetea todos los valores y el contexto de la conversación. |
| `--loadconfig <ruta_del_archivo>` | `--lc` | Carga las configuraciones desde un archivo JSON. |
| `--log <texto> <respuesta>` | `--log` | Guarda una interacción de usuario y respuesta en un archivo de log. |
| `--setparams <parametro1=valor1> <parametro2=valor2> ...` | `--sp` | Configura parámetros del modelo, como `temperature` y `max_tokens`. |
| `--toggleautosave <on/off>` | `--ta` | Activa o desactiva la función de autosave. |
```

**Recuerda:**

* El módulo "gemini" requiere que se monte en el programa principal para funcionar. Debes llamar a la función `mount gemini` en el programa principal para iniciar el módulo.
* Los comandos se ejecutan con la sintaxis `>>>gemini> <comando> <argumentos>`. 



