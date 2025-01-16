<h3> Crear comandos para la consola Osiris </h3>

Entendido. Aquí tienes un manual detallado sobre cómo crear comandos para Osiris, incluyendo los requisitos, la estructura del código y ejemplos. Este manual se centrará en la creación de comandos utilizando `create.py`, y abordará aspectos prácticos para el desarrollo de comandos funcionales dentro del sistema Osiris.

## Manual para la Creación de Comandos en Osiris

Este manual describe el proceso para crear comandos personalizados para Osiris. Se detallarán los requisitos, la estructura básica, los aspectos a considerar, y ejemplos para el desarrollo de comandos eficientes.

**Requisitos:**

1.  **Conocimientos básicos de Python:** Debes tener conocimientos sobre sintaxis, funciones y manejo de variables en Python.
2.  **Entorno de desarrollo Osiris:** Debes tener acceso al sistema de archivos de Osiris (directorio `osiris/`).
3.  **Uso de `create`:** Es necesario saber cómo utilizar el comando `create` de Osiris.

**Estructura Básica de un Comando:**

Cada comando es un archivo Python `.py` que debe tener una estructura específica. Los archivos de los comandos deben estar en el directorio  `osiris/bin/com/`. La estructura básica es la siguiente:

```python
import sys
import os
import inspect

def main(args):
    """
    Función principal del comando [nombre_comando].
    Recibe una lista de argumentos del usuario.
    """
    # Aquí va la lógica del comando
    print(f"Comando [nombre_comando] ejecutado con argumentos: {args}")


if __name__ == "__main__":
    """
    Código para ejecución directa del script en la terminal
    """
    main(sys.argv[1:])
```

*   **`import sys`:** Importa el módulo `sys` para acceder a los argumentos de la línea de comandos (`sys.argv`).
*   **`import os`:** Importa el módulo `os` para operar con el sistema de archivos.
*   **`import inspect`:** Importa el módulo `inspect` para analizar funciones.
*   **`main(args)`:** La función principal del comando:
    *   Debe llamarse `main`.
    *   Debe recibir un solo argumento llamado `args`. Este argumento es una lista de strings con los argumentos de línea de comandos proporcionados por el usuario.
    *   Contiene la lógica del comando: operaciones, procesamiento de argumentos, etc.
    *   Puede usar otras funciones definidas dentro del mismo archivo.
    *   Puede imprimir salidas por pantalla usando `print()`.
*   **`if __name__ == "__main__":`:** Este bloque asegura que la función `main` se ejecute cuando el archivo es ejecutado directamente desde la terminal, lo que permite depurar el comando. Se pasa una lista con los argumentos del script (sin el nombre del script).

**Creación de un Comando:**

1.  **Usa `create`:** En la línea de comandos de Osiris, escribe `create [nombre_comando] --create`, donde `[nombre_comando]` es el nombre deseado para el nuevo comando (ej: `create test_command --create`).
2.  **Confirmación:** Osiris informará si el archivo ha sido creado con éxito. El archivo creado estará en  `osiris/bin/com/[nombre_comando].py`.
3.  **Edita el Archivo:** Edita el archivo creado en `osiris/bin/com/[nombre_comando].py`, implementando la lógica del comando.

**Ejemplo de Comando Simple:**

Este comando imprimirá los argumentos recibidos:

```python
import sys
import os
import inspect


def main(args):
    """
    Comando para mostrar los argumentos introducidos.
    """
    print(f"Comando mycommand ejecutado con los siguientes argumentos:")
    for arg in args:
        print(f"- {arg}")

if __name__ == "__main__":
    main(sys.argv[1:])
```

Para usarlo:

1.  Crea el archivo con `create mycommand --create`.
2.  Edita el archivo con el contenido del código de arriba.
3.  Ejecuta `use mycommand` para establecerlo como comando en uso.
4.  Escribe  `arg1 arg2 arg3` y se imprimirá la salida del comando.

**Aspectos a Considerar:**

*   **Nombre de Comando:** El nombre del comando será el nombre del archivo Python (sin la extensión `.py`).
*   **Argumentos:** La función `main` recibe los argumentos como una lista de strings. Debes validar y procesar los argumentos que recibe el comando.
*   **Salida del Comando:** Usa `print()` para enviar la salida del comando a la consola. Si el comando requiere mostrar salidas complejas, es necesario crear una funcion específica y reutilizarla en el código de ese comando.
*   **Librerías:** Usa las librerías importadas (`os`, `sys`, `inspect`, etc.) y otras que necesites dentro del código de tu comando.
*   **`lib/gemini/utils.py`:** Utiliza las funciones útiles disponibles en `lib/gemini/utils.py`, para crear ventanas, procesar imágenes, exportar/importar información.
*    **Importar módulos de otros comandos:** Para importar otros módulos es necesario conocer que las rutas son relativas al punto de entrada `osiris/bin/com.py`, por lo que por ejemplo para importar un módulo localizado en  `osiris/lib/osiris/common.py` desde un comando localizado en `osiris/bin/com/micomando.py`, se realiza importando  `import lib.osiris.common as common`
*   **`cnf.py`:** Puedes acceder a la configuración del sistema a través del módulo `cnf` de Osiris.

**Ejemplo de un Comando Más Complejo:**

Este comando utiliza la función `dialog_window` para que el usuario introduzca texto y luego lo imprime en pantalla:

```python
import sys
import os
import inspect
import lib.gemini.utils as win


def main(args):
    """
    Comando para pedir al usuario que escriba texto y mostrarlo.
    """
    text = win.dialog_window("Escribe aquí tu texto")
    if text:
        print(f"Texto introducido:\n{text}")
    else:
      print("No se introdujo texto")
if __name__ == "__main__":
    main(sys.argv[1:])
```

Para usarlo:

1.  Crea el archivo con `create dialog_test --create`.
2.  Edita el archivo con el contenido del código de arriba.
3.  Ejecuta `use dialog_test`.
4.  Escribe lo que sea y se mostrará por pantalla en la terminal.

**Recomendaciones:**

*   **Modularidad:** Divide los comandos complejos en funciones para facilitar la lectura y el mantenimiento del código.
*   **Comentarios:** Añade comentarios explicativos para que el código sea comprensible.
*   **Errores:** Gestiona los errores adecuadamente, utilizando bloques `try...except`.
*   **Validaciones:** Valida los argumentos proporcionados por el usuario.
*   **Documentación:** Añade un comentario `help` al inicio del código para documentar el funcionamiento del comando y su uso.

Con esta información, ya estás preparado para crear tus propios comandos para Osiris.

Para crear más comandos que se puedan ejecutar en conjunto, y no de forma aislada como ahora, se ha de seguir la siguiente nomenclatura:

Para poder ejecutar comandos en serie, es necesario que los comandos que se usan llamen a la función `main` de cada módulo.
 Por ejemplo:

Si quieres crear un comando `cadena.py`, donde se ejecutarán los comandos `comando_a`, `comando_b` y `comando_c` y que este comando `cadena` sea ejecutado desde el prompt de osiris.

En el comando cadena.py se haria lo siguiente:
```python
import sys
import os
import inspect
import com.comando_a as cmd_a
import com.comando_b as cmd_b
import com.comando_c as cmd_c


def main(args):
    """
    Comando para encadenar otros comandos.
    """
    print(f"Ejecutando comando cadena.")
    # Ejecutar comando_a
    print(f"Ejecutando comando_a.")
    cmd_a.main(args)

    # Ejecutar comando_b
    print(f"Ejecutando comando_b.")
    cmd_b.main(args)

    # Ejecutar comando_c
    print(f"Ejecutando comando_c.")
    cmd_c.main(args)


if __name__ == "__main__":
    main(sys.argv[1:])
```

De esta forma se pueden concatenar comandos dentro de un comando.

Con este manual, tienes una guía para crear, entender, e implementar comandos dentro del sistema Osiris.
