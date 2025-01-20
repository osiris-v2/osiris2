## Manual de Osiris: Interfaz de Línea de Comandos para la Gestión de Módulos y Gemini AI

Osiris es una interfaz de línea de comandos (CLI) que facilita la interacción con diferentes módulos y la API de Gemini de Google.  Su arquitectura modular permite la carga y ejecución dinámica de comandos, la gestión eficiente de recursos y una experiencia de usuario simplificada.

**I. Requisitos Previos:**

* Python 3.x instalado con las siguientes dependencias: `google-generativeai`, `Pillow`, `tkinter`, `requests`, `cryptography`, `yt-dlp`, `ffmpeg`, `pickle`, `readline`.  Puedes instalarlas con `pip install -r requirements.txt` (asumiendo que existe un archivo `requirements.txt` con las dependencias).
* Una clave API válida para Google Gemini AI.  El script te guiará para configurarla de forma segura.
* Los módulos de comandos deben estar ubicados en la carpeta `osiris/bin/com`. Cada módulo debe contener una función `main` que recibe una lista de argumentos como parámetro único.
* (Opcional) El programa `dsk/dskv` para la previsualización de vídeos (si se utiliza la opción `--tvl`).


**II. Ejecución e Inicialización:**

Para ejecutar Osiris, ejecuta `python3 osiris/bin/com/com.py` desde la línea de comandos. La aplicación iniciará un proceso de autenticación.


**III. Autenticación:**

Osiris utiliza un sistema de autenticación simple basado en contraseña.

* **Primer Inicio:** Si no existe un archivo de autenticación (`osiris/bin/data/auth_pwd`), se te solicitará crear una contraseña.
* **Inicio de Sesión:**  Se te pedirá introducir la contraseña.  La contraseña se almacena de forma segura como un hash SHA512.
* **Restablecimiento de Contraseña:** Si introduces `"Reset Password Key " + <hash_almacenado> + ".SECRET_RECOVER"`, se te permitirá restablecer la contraseña.  `<hash_almacenado>` es el hash de la contraseña que puedes ver en el archivo `osiris/bin/data/auth_pwd`  **Por razones de seguridad, no debes tener la clave secreta ("SECRET_RECOVER") almacenada directamente en el código.**  Considera la posibilidad de usar una variable de entorno.

**IV. Comandos Principales:**

Osiris ofrece comandos para interactuar con la API de Gemini y ejecutar comandos del sistema.


**A. Comandos para la Gestión de Módulos:**

* **`use [comando]`:** Selecciona un comando para facilitar el uso subsecuente. Luego, solo necesitas escribir los argumentos para el comando. El comando actual se muestra en el prompt (ej: `gemini3> `).  Para cancelar la selección de un comando, simplemente escribe `use`.

* **`mount [comando]`:**  Añade un nuevo comando a la lista de comandos disponibles. El archivo del comando (ej: `mi_comando.py`) debe existir en la carpeta `osiris/bin/com` y contener una función `main` que reciba una lista como parámetro.

* **`[comando] --reset`:** Elimina un comando de la memoria.  Libera los recursos asociados con el comando previamente montado.

* **`[comando] --edit`:** Abre el archivo del comando especificado en el editor de texto configurado (por defecto, `subl`).

* **`reset`:**  Reinicia el prompt. Utilízalo si el cursor se comporta de forma inesperada.

* **`--reload`:** Recarga el entorno de comandos.  Utilízalo después de instalar o actualizar un módulo.


**B. Comandos para Gemini AI:**

* **`--nmodel`:** Permite seleccionar un modelo Gemini.  Tras ejecutar este comando, la interfaz te pedirá que selecciones un modelo de una lista predefinida.

* **`--load [ruta_archivo]` (-l):** Carga el contenido de un archivo de texto para usarlo como contexto en las interacciones con Gemini.

* **`--addload [texto]` (-al):** Agrega el contenido de un archivo cargado con `--load` a la entrada del usuario.

* **`--showload` (-sl):** Muestra el contenido del archivo cargado con `--load`.

* **`--loadimage [ruta_imagen]` (-li):** Envía una imagen al modelo de Gemini para generar una respuesta. Puedes usar `--li --fd` para abrir un diálogo de selección de archivos.

* **`--showwin` (-sw):** Muestra el contexto de la conversación en una ventana.

* **`--saveload [nombre_archivo]` (-sav):** Guarda el contexto de la conversación en un archivo.

* **`--saverequest [texto]` (-sr):** Guarda la solicitud actual en un archivo.

* **`--saveanswer [nombre_archivo]` (-sa):** Guarda la última respuesta generada en un archivo.

* **`--savecontext` (-sc):** Guarda el contexto actual de la conversación.

* **`--autosave` (-as):** Activa o desactiva el guardado automático del contexto y las respuestas.

* **`--newquestions [pregunta]` (-nq):** Genera preguntas relacionadas con una pregunta base.

* **`--send [texto]` (-s):** Envía una solicitud de texto a Gemini.

* **`--listfiles` (-ls):** Lista los archivos en el directorio `osiris/bin/data`.

* **`--clearcontext` (-cc):** Limpia el contexto actual de la conversación.

* **`--loadselect [ruta_archivo]` (-lsel):** Carga un contexto seleccionado desde un archivo.

* **`--loadmultiple [archivo1] [archivo2] ...` (-lm):** Carga múltiples contextos desde archivos.

* **`--info` (-i):** Muestra información sobre el modelo Gemini y el contexto actual.

* **`--export [nombre_archivo]` (-exp):** Exporta el contexto actual o genera un manual de uso.  Ej: `--exp man` genera un manual de usuario.

* **`--import [nombre_archivo]` (-imp):** Importa un contexto de un archivo.

* **`--search [término]` (-s):** Busca un término en el contexto actual. Usa `--search --load [término]` para cargar el contexto encontrado.

* **`--settopic [tema]` (-st):** Establece un tema para la conversación.

* **`--resetkey`:**  Reinicia la clave API de Gemini.

* **`--loadconfig [ruta_archivo]` (-lc):** Carga la configuración desde un archivo JSON.

* **`--log [texto]`:** Registra interacciones en un archivo de log.

* **`--setparams [param1=valor1] [param2=valor2] ...` (-sp):** Configura parámetros del modelo Gemini (ej: `--setparams temperature=0.5 max_tokens=150`).

* **`--toggleautosave [on/off]` (-ta):** Activa o desactiva el guardado automático.


**C. Comandos para Procesamiento de Medios:**

* **`--screenshot` (-ss):** Captura una captura de pantalla y la envía a Gemini para su interpretación.

* **`--showlastanswer` (-sla):** Muestra la última respuesta generada por Gemini.

* **`--loadanswer` (-la):** Carga la última respuesta generada por Gemini en el contexto actual.

* **`--tvideol [ruta_o_url_video] [prompt]` (-tvl):** Procesa un vídeo, generando subtítulos SRT y un vídeo con subtítulos.


**D. Comandos de Diagnóstico:**

* **`--diagnostic [server/system/memory]` (-d):** Ejecuta comandos de diagnostico del sistema.


**E. Comandos de Salida:**

* **`exit`:** Sale del programa.  Se pedirá confirmación antes de salir.

**V. Manejo de Comandos Externos:**

Osiris puede ejecutar comandos externos del sistema operativo.  Para esto, simplemente escribe el comando como lo harías en tu terminal.  El comando se ejecutará en un pseudoterminal (`pty`), lo que permite la interacción interactiva.

**VI.  Manejo de Errores:**

Osiris incluye un sistema básico para detectar y mostrar errores.  Los mensajes de error se mostrarán en la consola.

**VII.  Generación de Manual ( `--exp man` ):**

El comando `--exp man` genera un archivo de texto llamado `man.txt` (o el nombre que especifiques) que contiene un manual de usuario actualizado dinámicamente.  Este manual se genera analizando el código fuente de los módulos, la configuración y la documentación.  Asegúrate de tener permisos de escritura en la carpeta donde se genera el archivo.


**VIII.  Consideraciones:**

* La funcionalidad de Osiris depende de la existencia y correcta configuración de los módulos en la carpeta `osiris/bin/com`.
* Se recomienda revisar y asegurar la seguridad de la configuración del sistema de autenticación.


Este manual proporciona una visión general de la interfaz Osiris. Para más detalles y ejemplos de uso, consulta el código fuente.  Puedes obtener ayuda sobre comandos individuales usando el argumento `--help` (ej: `gemini3 --help`).


<img src="https://www.gifss.com/economia/bitcoin/images/bitcoin-05.gif"  width=40 height=40><b></b>  

<b>AMM 2024</b> [LICENCIA](LICENSE.md)  
