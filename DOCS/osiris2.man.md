
## Manual Definitivo de Osiris: Guía Integral

Este manual representa la culminación de nuestras conversaciones, integrando todos los manuales anteriores y el análisis de la última captura de pantalla en una guía integral de Osiris.

**1. Introducción a Osiris:**

*   Osiris es un entorno de desarrollo, pruebas, automatización y despliegue altamente personalizable que integra la inteligencia artificial y la interacción con servicios externos a través de una interfaz de línea de comandos (CLI).
*   Permite la creación de comandos personalizados, la gestión de entornos y la automatización de tareas complejas.

**2. Estructura del Sistema Osiris:**

*   `osiris/bin/auth.py`: Gestión de la autenticación mediante contraseñas hasheadas SHA512.
*   `osiris/bin/cnf.py`: Configuración del sistema, define rutas y variables.
*   `osiris/bin/com.py`: Núcleo de la CLI, gestiona comandos, módulos y la interacción con el usuario.
*  `osiris/bin/com/`: Contiene los archivos de los comandos en forma de módulos Python.
*   `osiris/bin/com/datas/`: Almacenamiento de datos persistentes: claves, historial, contextos y variables.
*   `osiris/lib/gemini/utils.py`: Funciones auxiliares para las interfaces graficas y el procesamiento de texto o imágenes.
*   `osiris/bin/lib/osiris/common.py`: Contiene funciones de ayuda y de uso común.
*  `osiris/bin/OPS/ops`: Shell externa `ods` para gestión de variables y ejecución de comandos.

**3. Inicio de Osiris:**

1.  Abrir una terminal y ejecutar `python3 osiris/bin/com.py`.
2.  Introducir la contraseña (si es necesario).
3.  Aparecerá el prompt de Osiris `>>>`.

**4. Comandos Básicos de Osiris:**

*   `use [comando]`: Establece el comando actual en uso.
*   `mount [comando]`: Carga un nuevo comando.
*   `reset`: Reinicia el prompt.
*   `--reload`: Recarga el entorno.
*   `--venv`: Muestra información sobre el entorno virtual.
*   `exit`: Sale de Osiris.
*   `Reset_Password`: Restablece la contraseña.
*  `[comando] --reset`: Desmonta un comando en memoria.
*   `[comando] --edit`: Abre el archivo del comando en el editor.
*   `[comando] --help`: Muestra la ayuda del comando.
*    `help`: Muestra la ayuda general de Osiris.

**5. Creación de Comandos Personalizados:**

1.  Utilizar `create [nombre_comando] --create`.
2.  Definir una función `main(args)` para el funcionamiento del comando, que tenga un único parámetro, que sea una lista.
3.  Utilizar las funciones de `lib.gemini.utils.py` o importar otros módulos utilizando la ruta relativa: `import lib.osiris.common as common`,  `import com.micomando as micomando`.
4.  Guardar el archivo en la carpeta `osiris/bin/com/`.
5. Para concatenar comandos, utiliza la funcion `main` de cada módulo.

**6. Comando `gemini` (Interacción con la API de Google Gemini):**

*   **Uso:** `gemini [pregunta] [opciones]`
*   **Funcionalidades:**
    *   Interacción con la API de Gemini para procesamiento de texto y lenguaje natural.
    *   Gestión del contexto de conversaciones.
    *   Carga de imágenes para su análisis por parte de la IA.
    *  Traducción de videos y generación de subtítulos con el comando `tvideol`.
    *   Las respuestas pueden ser utilizadas como contexto para futuras preguntas.
    *  Exportación e importación de contextos de conversación.
*  **Opciones:**
    *   `--load [ruta_archivo]` (`-l`): Carga contexto de archivo.
    *   `--addload [texto]` (`-al`): Añade texto a la consulta con el contexto.
    *  `--loadimage [ruta_imagen]` (`-li`): Carga una imagen a Gemini, con la posibilidad de utilizar el dialogo de selección de archivos con `--fd`.
    *  `--showwin` (`-sw`): Muestra el contexto en una ventana.
    *   `--showlastanswer` (`-sla`): Muestra la última respuesta de Gemini en una ventana.
    *  `--loadanswer` (`-la`): Carga la ultima respuesta de Gemini como contexto.
    *   `--saveload [nombre_archivo]` (`-sav`): Guarda el contexto.
    *   `--saverequest [texto]` (`-sr`): Guarda la última solicitud.
    *  `--saveanswer [nombre_archivo]` (`-sa`): Guarda la última respuesta de Gemini en un fichero.
    *   `--savecontext` (`-sc`): Guarda el contexto actual de la conversación.
    *   `--autosave` (`-as`): Activa/desactiva el autosave.
    *   `--newquestions [pregunta]` (`-nq`): Genera nuevas preguntas relacionadas al tema.
    *    `--send [texto]` (`-s`): Envia un texto sin el contexto anterior.
     *  `--search [termino]` (`-s`):  Busca un término en el contexto. Utilizar `--search [termino] --load` para cargar las lineas encontradas como contexto.
    *   `--export [nombre_archivo]` (`-exp`): Exporta el contexto.
    *   `--import [nombre_archivo]` (`-imp`): Importa el contexto.
     *   `--reset`: Resetea el comando `gemini`.
     *   `--screenshot` (`-ss`): Realiza captura de pantalla y la manda a Gemini para su análisis.
     *   `--tvideol [ruta_o_url_video] [prompt]` (`-tvl`): Procesa un vídeo y genera subtítulos y un vídeo con ellos.
*   **Ejemplos:**
    *    `gemini "¿Cuál es la capital de España?"`
     *   `gemini --load contexto.gemini --al "información adicional" "pregunta"`
     *   `gemini --li imagen.png "Describe esta imagen"`
      *  `gemini --ss`
     *  `gemini --tvideol video.mp4 "Traduce al español"`

**7. Comando `tvideol` (Procesamiento de Vídeo con Subtítulos):**

*   **Uso:** `gemini --tvideol [ruta_video] [prompt_adicional]`
*   **Objetivo:** Traduce vídeos y genera subtítulos en formato SRT, generando el video resultante.
*  **Flujo:**
     1.   Descarga el vídeo (si es una URL).
    2.    Sube el video a la API de Gemini.
    3.     Genera el archivo SRT utilizando el modelo `gemini-video`.
    4.    Aplica estilos en el archivo SRT.
     5.   Utiliza `ffmpeg` para generar el video con los subtítulos.
     6.   Utiliza `osiris2.multiprocess` para ejecutar un reproductor de video.
     7.   Envia la información a `gemini-text` para procesar dicha información y ejecutar otros comandos adicionales.
*   **Parámetros:**
    *   `ruta_video`: Ruta o URL del video.
    *   `prompt_adicional` (opcional): Instrucciones para la traducción y el estilo.

**8. Comando `ods` (Osiris Dynamic Shell):**

*   **Uso:** `--ods`
*   **Objetivo:**  Proporciona una shell para la gestión de variables, la ejecución de comandos del sistema y la manipulación de ficheros.
*   **Funcionalidades:**
    *   Gestión de variables con `mem [variable]=[valor]`.
    *   Acceso al valor de una variable con `$[variable]`.
    *   Ejecución del valor de una variable como comando con `@[variable]`.
    *    Muestra información de una variable con `~[variable]`.
    *    Guardado y carga de variables con `save`, `load`, `load+`, `load++` y  `load-`.
     *  Permite entradas multilínea con `multiline`, terminadas con `EOF` en una nueva línea.
      *   Ejecución de comandos externos.
*   **Ejemplo de uso:**
     1. `ods`: Entrar en la shell `ods`.
     2. `mem variable=valor` o `mem variable` (si la entrada es multilinea).
     3. `save fichero_vars`, o `load fichero_vars`.
     4. `$variable`
     5. `@variable`

**9. Flujo de Funcionamiento General de Osiris:**

1.  **Inicio:** `python3 osiris/bin/com.py`.
2.  **Autenticación:**  `osiris/bin/auth.py` verifica la contraseña.
3.  **CLI:** Se muestra el prompt de Osiris.
4.  **Interpretación:** `osiris/bin/com.py` analiza e interpreta la entrada del usuario.
5.  **Ejecución:** Se ejecuta el comando o modulo correspondiente.
   *   Los comandos que no son módulos, se ejecutan mediante la librería `pty` como comandos del sistema.
  *    La ejecución del comando `--ods`, ejecuta el programa compilado en c `osiris/bin/OPS/ops`.
  *  Los comandos de IA se ejecutan mediante la API de Gemini.
6.  **Datos Persistentes:**  Se gestiona el contexto y los ficheros con las diferentes opciones de los comandos.
7.  **Finalización:** Se utiliza el comando `exit` para cerrar el programa.

**10. Manejo de Errores:**

*   `try...except` para la gestión de excepciones.
*  `messagebox.showerror()` para mensajes de error en interfaz gráfica.
* Gestión de errores al llamar a funciones del sistema con `perror`.
* Gestión de los códigos de retorno de los comandos del sistema.

**11. Almacenamiento:**

*   Clave API de Gemini:  `osiris/bin/com/datas/gemini_key.enc` (cifrada).
*   Contraseña de usuario: `osiris/bin/com/datas/auth_pwd` (hash SHA512).
*    Historial de comandos:  `osiris/bin/com/datas/command_history.pkl`.
*   Contexto de las conversaciones: `osiris/bin/com/datas/*.gemini`.
*   Variables de ods:  `osiris/bin/com/datas/*.vars`.

**12. Osiris2tmux:**

*   `tmux` como multiplexor de terminales para gestionar múltiples paneles y sesiones en la terminal.
*  Permite la gestión de entornos de desarrollo, la organización de procesos y la persistencia de las sesiones.

**13. Perspectivas de Osiris:**

*   **Desde Fuera:** Una CLI para tareas de automatización y la interacción con la IA.
*    **Desde Dentro:** Un sistema modular con funciones para la gestión de comandos, la comunicación con la IA, la gestión de ficheros, la automatización y la gestión de la seguridad, todos integrados para conseguir una herramienta de desarrollo y puesta en marcha de software de forma eficiente.

**14. Descripción de la Captura de Pantalla de la Actualización de Osiris2:**

*   La imagen muestra el proceso de desarrollo de `osiris2`, con la compilación de código fuente en `c` y `python`, la creación de paquetes `.deb` y la comunicación con un servidor central mediante WebSockets.
*   Se destaca el uso de `tmux` para la gestion de múltiples ventanas.
*   Hay una interacción con la API de Gemini (uso del comando `gemini` e interacciones con la IA).
*   Se utiliza `git` para la gestión del código.
*  Muestra que Osiris2 gestiona sus propios logs de información.
*   Se ve la ejecución de un programa que gestiona procesos como `Pilot TV`.
*  Muestra una secuencia de comandos ejecutados en `ods` con uso de variables.

**15. Conclusión:**

Osiris es una herramienta versátil y potente para automatizar tareas, interactuar con la IA y desarrollar software, con una alta capacidad de adaptación a diversos entornos de trabajo gracias a su arquitectura modular. El sistema combina un potente sistema de ejecución de comandos, un sistema de gestión de la información, con gestión de ficheros y la capacidad de poder concatenar todos los comandos, a través de la potencia de Python, y la gestión de variables de la shell `ods` que esta escrita en `c`.

Este manual será guardado como `osiris_man_ultimate` en la ruta `osiris/bin/com/datas/`.

User: Perfecto. Ahora que has realizado un gran trabajo y has generado una gran cantidad de información, haz un resumen final de todo el contenido.
AI: Entendido. Aquí tienes un resumen final y conciso que abarca todo el contenido que hemos generado y analizado durante nuestras interacciones sobre Osiris. Este resumen será guardado como `osiris_summary_final` utilizando la opción `--exp`.

## Resumen Final de Osiris: Una Visión General

Este documento proporciona un resumen final de todas las características, funcionalidades y componentes de Osiris, según la información generada y analizada en nuestras conversaciones.

**1. Osiris en Pocas Palabras:**

*   **Herramienta Integral:** Osiris es una interfaz de línea de comandos (CLI) personalizable y modular diseñada para el desarrollo de software, la automatización de tareas, la gestión de sistemas, la interacción con la inteligencia artificial y la gestión de flujos de trabajo.
*   **Versatilidad:** Se integra con diversas tecnologías y proporciona un entorno flexible y potente.

**2. Arquitectura de Osiris:**

*   **Módulos Python:** La mayoría de las funcionalidades de Osiris se implementan mediante módulos Python (como `com.py`, `gemini.py`, `create.py`) que se encuentran en el directorio `osiris/bin/com/`.
*   **Shell Externa:** El sistema de gestión de variables es realizado por el programa compilado en C  `ods` (ubicado en `osiris/bin/OPS/ops`).
*   **Autenticación:** Se gestiona mediante el modulo `osiris/bin/auth.py` utilizando contraseñas con hash SHA512.
*   **Datos Persistentes:** La configuración y los datos del sistema se guardan en ficheros que están en la carpeta `osiris/bin/com/datas/`.
*   **Libreria `utils`:** La libreria `osiris/lib/gemini/utils.py` centraliza funcionalidades de interfaz gráfica y otras funciones de ayuda para los diferentes comandos.
*   **Gestión de comandos:** Se lleva a cabo mediante el fichero `osiris/bin/com.py`, que tiene un bucle que gestiona comandos internos, comandos del sistema, módulos, e interacción con la API de Gemini, y el proceso externo `ods`.

**3. Flujo de Funcionamiento:**

1.  **Inicio:** Ejecución de `python3 osiris/bin/com.py` en la terminal y solicitud de la contraseña.
2.  **CLI:** Se presenta el prompt para ingresar comandos `>>>`.
3.  **Interpretación:** El modulo principal `com.py` analiza la entrada del usuario.
4. **Redirección:** En función del tipo de entrada se redirige al modulo, al programa externo o a la API de gemini.
5.  **Ejecución:** Se realiza la acción especificada por el comando.
6.  **Persistencia:** Se gestionan los datos de forma persistente, y se guarda el historial de comandos.

**4. Comandos de Osiris:**

*   **`use`**: Establecer el comando actual de uso.
*   **`mount`**:  Añadir un nuevo comando al sistema.
*   **`create`**:  Crea un nuevo comando en el directorio `osiris/bin/com/`.
*   **`gemini`**:  Utiliza la API de Gemini para procesamiento de texto, imágenes, y vídeo (con la opción `tvideol`). Permite la gestión del contexto de las conversaciones y la ejecución de acciones.
*    **`--ods`**:  Ejecuta la shell `ods` para gestionar variables y ejecutar comandos del sistema.
*   **Otros Comandos:**  Se utilizan para diversas acciones (gestión de variables, información del sistema, etc).
*   **Opciones de Comandos:**  Gestiona los diferentes modificadores de los comandos (ej: `--load`, `--save`, `--help`, etc)
*  **Comandos Externos:** Utiliza la librería `pty` para la correcta ejecución de comandos del sistema.

**5. Componentes Clave:**

*  **Interfaz de Línea de Comandos (CLI):** El núcleo de la interacción con Osiris.
*   **API de Gemini:** Permite la interacción con modelos de inteligencia artificial.
*   **Shell `ods`:** Proporciona un entorno para la gestión de variables y comandos externos.
*   **`tmux`:** Permite multiplexación de la terminal para gestionar múltiples vistas y persistencia de sesiones.
*   **Git:**  Gestión del código fuente y la automatización de las actualizaciones.
*  **Libreria `utils`:** Contiene funcionalidades de interfaz gráfica y otras funciones de ayuda para el procesamiento de ficheros, texto e imagenes.
* **Ficheros de Configuración:** Gestión de las configuraciones en diferentes ficheros.
*   **Variables:** Permiten la gestión de información dinámica mediante la shell `ods`, así como la automatización de la ejecución de comandos.
*   **Contexto:** Se gestiona el contexto de la conversación en `gemini.py` y el contexto de variables en la shell `ods`.

**6. Flujos de Trabajo:**

*  **Desarrollo de Comandos:**  Crea archivos con la estructura del modulo de Osiris, y escribe lógica python.
*   **Automatización de Tareas:**  Gestiona la ejecución de comandos del sistema, y la comunicación con la API de Gemini mediante la combinación de las opciones, y los diferentes módulos, así como la potencia de las variables de `ods`.
*  **Interacción con IA:** Se realiza mediante el comando `gemini` y todas sus opciones para la interacción con el modelo de lenguaje de google.
*   **Análisis de Imágenes:** Se utilizan capturas de pantalla y el comando `gemini` para interpretar información de las imágenes.
*    **Procesamiento de Vídeo:** Se gestiona con la opción `--tvideol` del comando `gemini`.
*    **Persistencia de Sesiones:** Permite la gestión del terminal con `tmux`, manteniendo la continuidad del trabajo aunque el sistema se reinicie o se cierre la terminal.
* **Integración con Git:** Permite el uso de Git mediante comandos de la shell `ods` y la propia gestión de la paquetería.
* **Seguridad:** Protege el sistema con una contraseña y la clave API de Google con encriptado.

**7. Gestión de Errores:**

*   Bloques `try...except` para gestionar las excepciones.
*  Funciones específicas para avisar de los errores.
* Se gestiona los códigos de retorno de los comandos del sistema.

**8. Funcionalidades Principales:**

*  **Gestión de comandos, carga de modulos y ejecución de comandos.**
*   **Interacción con la API de Gemini para procesar textos, imágenes y videos.**
*   **Proporciona una shell para la manipulación de variables y la ejecución de comandos de sistema (`ods`).**
*   **Permite la gestión y ejecución de procesos en segundo plano.**
*  **Posibilidad de la creación de nuevos comandos personalizados.**
*   **Permite la gestión de contextos de conversación, del estado de las variables, la gestión de la configuración, o el historial de comandos.**
*   **El uso de la herramienta `tmux` para la gestión de terminales y la persistencia de sesiones.**

**9. Perspectivas:**

*   **Desde Fuera (Usuario):** Osiris es una herramienta para automatizar, interactuar con la IA,  gestionar ficheros y ejecutar comandos de manera rápida y eficiente.
*   **Desde Dentro (Código):** Osiris es una arquitectura modular que combina código Python y C que se ejecuta en un bucle de ejecución, gestiona el sistema de archivos, el estado de las variables, la comunicación con otros sistemas, y la seguridad.

**10. Conclusión:**

Osiris es una herramienta compleja y potente que integra una variedad de funciones y tecnologías. Es un proyecto en desarrollo, diseñado para ser altamente personalizable y adaptable a diferentes entornos de trabajo.

Este manual será guardado como `osiris_summary_final` en `osiris/bin/com/datas/`.

