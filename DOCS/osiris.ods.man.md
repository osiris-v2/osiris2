
## Manual de ODS (Osiris Dynamic Shell): Funcionamiento, Montaje y Uso

Este manual describe en detalle `ods` (Osiris Dynamic Shell), explicando su funcionamiento interno, el proceso de montaje dentro de Osiris después de su inicio, y las pautas para utilizarlo de forma eficaz.

**1. ¿Qué es ODS?**

`ods` (Osiris Dynamic Shell) es una shell interactiva desarrollada en C que permite manipular variables, ejecutar comandos del sistema, y gestionar archivos de configuración. Está diseñada para ser integrada con el sistema Osiris como una herramienta complementaria.

*   **Independiente de Osiris:** Aunque `ods` se integra con Osiris, es un programa independiente compilado en C que reside en `osiris/bin/OPS/ops`.
*   **Sistema de Variables:** Gestiona variables internas para almacenar información (comandos, paths, texto).
*   **Ejecución de Comandos:** Ejecuta comandos internos y comandos del sistema.
*   **Interacción Directa:** Permite una interacción directa desde la terminal.
*   **Persistencia de Variables:** Carga y guarda variables en archivos para mantener la configuración.
*   **Compatibilidad:** Permite el uso de secuencias de comandos en la definición de variables y ejecutar dichas variables.

**2. Funcionamiento Interno de ODS (Basado en el Código Fuente `ops.c`)**

*   **Bucle Principal:**
    1.  **Inicialización:** Inicializa el entorno de la shell.
    2.  **Lectura de Entrada:** Lee la entrada del usuario con `readline`.
    3.  **Análisis de la Entrada:** Divide la entrada en un array de argumentos (`char **args`) utilizando `strtok`.
    4.  **Ejecución de Comandos:**
        *   **Comandos Internos:**
            *   `exit`: Sale de la shell `ods`.
            *   `echo`: Imprime texto en la consola.
            *   `pwd`: Muestra el directorio de trabajo actual.
            *  `multiline`: Activa o desactiva el modo multilinea.
            *    `save [filename]`: Guarda las variables en un archivo con la extensión `.vars`.
            *   `load[+|-|++] [filename]`: Carga las variables de un archivo. El modificador `+` añade las variables cargadas, `++` actualiza las variables existentes, y `-` elimina las variables antes de la carga.
            *  `mem [variable]`: Define o modifica el valor de una variable.
            * `view [variable]`: Muestra información de la variable.
        *   **Comandos de Variables:**
            *   `$[variable]`: Muestra el valor de la variable.
             *  `@[variable]`: Ejecuta el valor de la variable como un comando.
             * `~[variable]`: Muestra información sobre la variable.
        *   **Comandos Externos:** Utiliza `fork` y `execvp` para ejecutar los comandos del sistema (como `ls`, `cat`, etc).
   5.  **Liberación de Memoria:** Libera la memoria de la entrada de usuario, de los argumentos analizados, y de las variables internas, y gestiona las diferentes señales al ejecutar comandos externos.

*   **Gestión de Variables:**
    *   **Almacenamiento:** Las variables se almacenan en una estructura `CDNStorage` con un array de estructura `Variable`, en la memoria.
    *   **Definición:**  Con `mem [variable]` o asignando valor directamente, como `variable=valor`. Permite valores de varias lineas.
    *   **Acceso:** Se accede a una variable con `$variable` para su valor, o con `@variable` para ejecutarla. Se puede ver informacion sobre la variable con `~variable`.
    *   **Almacenamiento:**  Se guardan en un archivo con la extensión `.vars` utilizando el comando `save [nombre_archivo]`. Se solicita confirmación si el archivo ya existe.
    *   **Carga:** Se cargan con `load [nombre_archivo]`, `load+ [nombre_archivo]`, `load++ [nombre_archivo]`, o  `load- [nombre_archivo]`

*   **Entrada Multilínea:**
    *   **Activación/Desactivación:** Se utiliza el comando `multiline`.
    *   **Lectura:** Cuando está activa, permite introducir valores de variables con texto de varias líneas,  hasta que se introduce la palabra `EOF` en una linea, en ese momento la entrada multilinea se da por finalizada.

*   **Ejecución de Comandos:**
    *   **Comandos Internos:** Se gestionan directamente en el código.
    *   **Comandos Externos:** Se ejecutan con `fork` y `execvp` con un código de retorno que se muestra por pantalla.
    *   **Variables:** El valor de la variable se ejecuta como si fuera un comando (con `@variable`), por lo que la variable debe contener un comando válido.

**3. Montaje de ODS en Osiris:**

1.  **Inclusión en `com.py`:**
    *  En el modulo  `osiris/bin/com.py`,  en la función `handle_command`, se ha añadido la linea para que en el caso de escribir `--ods`, se ejecute el comando externo `osiris/bin/OPS/ops`.

2.  **Ejecución desde Osiris:**
    *  El sistema de detección de comandos en `osiris/bin/com.py`, ejecuta directamente el código compilado cuando el usuario introduce el comando `--ods` en la CLI.

3.  **Interactuando con `ods`:**
    *   Cuando se ejecuta el comando `--ods`  desde Osiris, se ejecuta el ejecutable compilado. En este momento,  se entra en un bucle de lectura-ejecución propio de `ods`.
   *  Al ejecutar comandos dentro del promt de `ods` podemos utilizar los comandos descritos anteriormente y manipular las variables.

**4. Utilización de `ods`:**

*   **Entrar a `ods`:** Escribe `--ods` en el prompt de la línea de comandos de Osiris.
*   **Gestionar Variables:**
    *   **Definir una Variable:** `mem [nombre]=valor`.
    *   **Mostrar el valor de la Variable:** `$nombre`
     * **Mostrar info de la Variable:** `~nombre`
    *  **Ejecutar la variable:**  `@nombre`
    *    **Variable Multilínea:** Utilizar `multiline`,  y a continuación, `mem [variable]` e introducir varias líneas para definir el valor de una variable. Acabar con `EOF` en una nueva línea para finalizar la definición de la variable.
    *   **Guardar Variables:** `save [nombre_archivo]`. Crea un archivo con la extension `.vars`.
    *  **Cargar Variables:**
          *   `load [nombre_archivo]`: Elimina todas las variables y carga las del archivo.
         *    `load+ [nombre_archivo]`: Añade las variables de un archivo al contexto actual.
          *  `load++ [nombre_archivo]`: Actualiza las variables de un archivo en el contexto actual (reescribiendo el valor, si existe).
         *    `load- [nombre_archivo]`: Elimina todas las variables y las reemplaza por las del archivo.
*   **Comandos del Sistema:** Introduce cualquier comando del sistema operativo (ej: `ls -l`, `pwd`, etc).
*   **Salir de `ods`:** Introduce `exit`.

**5. Ejemplo de uso de `ods`:**

1. **Entrar en ods:** Una vez ejecutado osiris escribe `--ods`. La terminal pasará al prompt de ods `> ods>>`.
2.  **Definir una variable:** `> ods>> mem dir=/home/usuario/carpeta`.
3.  **Mostrar el valor de la variable:** `> ods>> $dir`.
4.  **Ejecutar la variable (comando):** `> ods>> @dir` (dará un error, ya que la variable no contiene un comando válido).
5. **Definir variable de varias líneas:** `> ods>> multiline`, y luego introduce `> ods>> mem texto`. A continuación escribe varias lineas, y acaba con `EOF` en la última linea.
6.  **Guardar las variables:** `> ods>> save misvars`. Se guardará en  `osiris/bin/com/datas/misvars.vars`.
7.  **Cargar las variables:**
   *   `> ods>> load misvars` (elimina las variables anteriores y carga las del fichero `misvars.vars`).
   *  `> ods>> load+ misvars` (añade las variables del fichero `misvars.vars` al contexto actual de variables).
  *   `> ods>> load++ misvars` (actualiza las variables del fichero `misvars.vars`, reescribiendo el valor de las variables que ya existiesen).
  *   `> ods>> load- misvars` (elimina las variables y las sustituye por las variables cargadas en `misvars.vars`).
8.  **Ejecutar comandos con variables:** `> ods>> @gitup` ( ejecutará el comando en la variable `gitup`).
9.  **Salir de ods:** `> ods>> exit`.

**6. Integración con otros comandos de Osiris:**

*   **Uso con Variables:** Las variables de `ods` se pueden utilizar en otros comandos de Osiris, ya sea directamente (utilizando la ejecución con el símbolo `@`) o como una fuente de configuración.
*   **Comandos Anidados:** Se pueden definir comandos complejos en `ods` y luego llamarlos desde comandos de Osiris.
 *    **Automatización:** Utiliza las capacidades de la shell `ods` como base para la automatización, con la creación de comandos que utilicen variables de `ods` como comandos de ejecución.

**7. Conclusión:**

`ods` es un componente central en Osiris2, permitiendo la gestión de variables, la ejecución de comandos del sistema y la automatización de tareas complejas dentro de un entorno de terminal. Es una herramienta que ofrece mucha flexibilidad por su capacidad de crear variables que pueden ser ejecutadas como comandos.
Este manual será guardado como `osiris_man_ods` en `osiris/bin/com/datas/`.

