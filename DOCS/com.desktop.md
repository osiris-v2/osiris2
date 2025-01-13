
## Manual de Uso del Módulo "desktop"

Este manual de uso te ayudará a comprender cómo funciona el módulo "desktop" y cómo utilizarlo para ejecutar diferentes comandos y aplicaciones.

### Descripción General

El módulo "desktop" es un script en Python que proporciona una interfaz de línea de comandos para interactuar con diferentes aplicaciones y procesos, incluyendo la ejecución de comandos personalizados, la gestión de procesos en segundo plano (background) y la visualización de información del sistema. 

### Requisitos Previos

* **Python 3:** Asegúrate de tener Python 3 instalado en tu sistema.
* **Módulo "osiris2":** El módulo "desktop" depende del módulo "osiris2" para la gestión de procesos y la ejecución de comandos.  Asegúrate de que "osiris2" esté instalado y disponible en tu sistema.

### Cómo Ejecutar el Módulo

1. **Abre una terminal o línea de comandos.**
2. **Navega hasta la ubicación del archivo "desktop.py".**
3. **Ejecuta el módulo usando el comando:** `>>>destop> <comando> <argumentos>`
4. **Reemplaza `<comando>` y `<argumentos>` con los comandos y argumentos específicos que deseas utilizar.**

### Comandos Disponibles

**Comandos generales:**

* **`man`:** Muestra la documentación del módulo.
* **`---edit`:** Edita el script "desktop.py" usando el editor de texto `nano`.
* **`killall`:** Termina todos los procesos iniciados por el módulo "desktop".
* **`kill <PID>`:** Termina el proceso con el PID especificado.
* **`list_processes`:** Lista todos los procesos que están en ejecución en el sistema.
* **`show_handlers`:** Muestra el contenido del diccionario de procesos en "osiris2".

**Comandos para aplicaciones:**

* **`<nombre de la aplicación>` <argumentos>:** Ejecuta la aplicación especificada en segundo plano. Los nombres de las aplicaciones disponibles son:
    * `dsk1`, `dsk2`, `dsk3`, `dsk4`, `dsk5`, `dsk6`, `dsk7`
    * `ipinfo`, `localnet`

**Comando para comandos personalizados:**

* **`com <comando> <argumentos>`:** Ejecuta el comando personalizado especificado en segundo plano. 

**Ejemplo:**

```bash
# Ejecutar la aplicación "dsk2" con los argumentos "arg1" y "arg2"
>>>destop> dsk2 arg1 arg2

# Ejecutar el comando "ls -l" en segundo plano
>>>destop> com ls -l
```

### Argumentos de Línea de Comando

Los argumentos de línea de comando son valores que se proporcionan después del comando principal para especificar opciones o parámetros adicionales.

**Para la mayoría de los comandos:**

* **`<argumentos>`:** Los argumentos necesarios para ejecutar el comando o la aplicación especificada.

**Ejemplos:**

```bash
# Ejecutar el comando "kill" con el PID 1234
>>>destop> kill 1234

# Ejecutar la aplicación "dsk1" con los argumentos "archivo.txt"
>>>destop> dsk1 archivo.txt
```

### Opciones de Configuración

El módulo "desktop" no tiene archivos de configuración específicos.

### Ejemplos de Uso

```bash
# Mostrar la documentación del módulo
>>>destop> man

# Editar el script "desktop.py"
>>>destop> ---edit

# Terminar todos los procesos iniciados por el módulo "desktop"
>>>destop> killall

# Terminar el proceso con PID 1234
>>>destop> kill 1234

# Listar todos los procesos que están en ejecución en el sistema
>>>destop> list_processes

# Mostrar el contenido del diccionario de procesos en "osiris2"
>>>destop> show_handlers

# Ejecutar la aplicación "dsk2" con los argumentos "arg1" y "arg2"
>>>destop> dsk2 arg1 arg2

# Ejecutar el comando "ls -l" en segundo plano
>>>destop> com ls -l
```

### Solución de Problemas

* **Error al importar el módulo "osiris2":** Asegúrate de que el módulo "osiris2" esté instalado y disponible en tu sistema.
* **Error al ejecutar un comando o aplicación:** Verifica la sintaxis del comando o aplicación y asegúrate de que los argumentos sean correctos.
* **Error al matar un proceso:** Asegúrate de que el PID proporcionado sea válido y que tengas permisos para terminar el proceso. 

### Notas Adicionales

* El módulo "desktop" utiliza el módulo "osiris2" para la gestión de procesos. Es posible que se requieran permisos especiales para iniciar o terminar ciertos procesos.
* Para ejecutar la aplicación "ipinfo", es necesario tener una conexión a Internet.
* El módulo "desktop" está en desarrollo, por lo que es posible que se agreguen nuevas funciones o comandos en el futuro.










 Este código implementa el comando `desktop` de Osiris, que utiliza el módulo `osiris2` para gestionar la ejecución de otros comandos o scripts relacionados con el escritorio. Analicemos su funcionamiento:

**1. Importaciones:**

El código importa varias bibliotecas, incluyendo `osiris2`, `datetime`, `subprocess`, `os`, `sys`, `importlib`, `time`, y `signal`. Estas bibliotecas proporcionan funcionalidades para la gestión de procesos, manejo de fechas y horas, ejecución de comandos, interacción con el sistema operativo, importación dinámica de módulos, manejo de tiempo y señales.

**2. Variables Globales:**

* `usuario`: Almacena el nombre de usuario actual.
* `r_def_mode`: Almacena el modo de ejecución predeterminado (`bg` para segundo plano).
* `def_exec_mode`: Almacena el modo de ejecución actual.
* `apps`: Una lista de comandos o aplicaciones que se pueden ejecutar a través de `desktop`.
* `fixed_process_pid`: Variable global para almacenar el PID del proceso en ejecución en modo "fixed".

**3. Función `recargar_modulo()`:**

Esta función recarga un módulo, lo que resulta útil si se hacen cambios en el código fuente del módulo sin necesidad de reiniciar la aplicación.  Elimina el módulo de `sys.modules` y luego lo importa de nuevo.

**4. Función `kill_fixed_process()`:**

Manejador de señales (`SIGINT`, Ctrl+C) que termina el proceso si se ejecuta en modo "fixed". Se encarga de matar el proceso de manera ordenada si es necesario.

**5. Función `iniciar_multiprocess()`:**

Esta función inicia un proceso usando el módulo `osiris2`.  El modo de ejecución se toma de la variable global `def_exec_mode`. Se guarda el PID del proceso si se ejecuta en modo "fixed".  Gestiona las excepciones `ValueError`.

**6. Funciones de Ayuda:**

* `mostrar_man()`: Imprime la documentación de `osiris2`.
* `editar_script()`: Abre el script actual en el editor `nano`.

**7. Función `listar_procesos()`:**

Esta función lista todos los procesos en ejecución, mostrando su nombre, PID, estado y metadatos. Usa `osiris2.process_manager.get_all_handlers()` para obtener información de todos los procesos activos.

**8. Función `kill()`:**

Permite matar un proceso, ya sea por su PID o por su nombre.  Intenta primero con `SIGTERM` y luego con `SIGKILL` si es necesario.  Gestiona las excepciones `ProcessLookupError` y `PermissionError`.  Se ha modificado para aceptar tanto PIDs como nombres de procesos.

**9. Función `kill_all()`:**

Mata todos los procesos en ejecución, solicitando primero su confirmación.  Se ha mejorado para usar `osiris2.process_manager.list_processes()` y gestionar las excepciones.

**10. Función `get_mode_from_args()`:**

Esta función extrae el modo de ejecución (`fixed` o `bg`) de los argumentos proporcionados. Devuelve el modo y la lista de argumentos restantes.


**11. Función `main()`:**

Esta función es el punto de entrada del script.  Procesar los argumentos proporcionados:

*   `man`: Imprime el manual de `osiris2`.
*   `---edit`: Abre el script actual en nano.
*   `killall`: Mata todos los procesos.
*   `kill [PID|nombre]`: Mata un proceso especifico.
*   `output [nombre_proceso]`: Monitorea la salida de un proceso en modo "fixed".
*   Si el primer argumento está en `apps`, ejecuta el comando correspondiente usando `osiris2`.
*   `com`: Ejecuta un comando arbitrario.
*   `list_processes`: Lista todos los procesos en ejecución.
*   `show_handlers`: Muestra el diccionario `process_handlers`.

Se gestionan los errores con un bloque `try...except`.


**Cómo `desktop` utiliza `osiris2`:**

El comando `desktop` utiliza `osiris2` para iniciar y gestionar aplicaciones o comandos de escritorio.  La función `main` en `desktop.py` crea un diccionario `obj` que contiene la configuración para `osiris2.multiprocess()`.  Este diccionario incluye:

*   `mode`:  El modo de ejecución ("fixed" o "bg").  Se puede especificar usando `--mode fixed` o `--mode bg`. El modo predeterminado es "bg".
*   `com`: El comando a ejecutar.  Es una lista que contiene el comando `python3` seguido de la ruta al archivo Python del comando y sus argumentos.
*   `metadata`: Metadatos adicionales como el nombre de usuario y el tiempo de inicio.

La función `iniciar_multiprocess()` pasa este diccionario a `osiris2.multiprocess()`, que se encarga de ejecutar el comando según la configuración especificada.  La función `kill_fixed_process` gestiona la interrupción con Ctrl+C.


**En resumen:** `desktop.py` actúa como una interfaz para ejecutar otros comandos o aplicaciones de escritorio, utilizando `osiris2` para gestionar la ejecución en primer plano o en segundo plano y para monitorear la salida de esos procesos.  Su principal función es facilitar la ejecución de aplicaciones de escritorio dentro del entorno de Osiris.  La modularidad y la gestión de errores están bien implementadas.  El uso de la variable global `fixed_process_pid` permite gestionar las interrupciones con `Ctrl+C` de forma eficiente.  La capacidad de controlar el modo de ejecución ("fixed" o "bg") usando `--mode` es una característica útil.