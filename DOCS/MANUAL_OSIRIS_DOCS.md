# 📖 Manual de Usuario: Osiris Documentador ✨

¡Bienvenido al Manual de Usuario de Osiris Documentador! Esta aplicación te permite crear, organizar y visualizar tu propia documentación de forma eficiente, utilizando Markdown y el potente motor de plantillas Jinja2 para contenido dinámico.

## Tabla de Contenidos

1.  [🚀 Introducción](#1-introduccin)
    *   [¿Qué es Osiris Documentador?](#qu-es-osiris-documentador)
    *   [Características Principales](#caractersticas-principales)
2.  [🛠️ Primeros Pasos: Instalación y Ejecución](#2-primeros-pasos-instalacin-y-ejecucin)
    *   [Requisitos del Sistema](#requisitos-del-sistema)
    *   [Instalación de Dependencias](#instalacin-de-dependencias)
    *   [Preparación Inicial del Entorno](#preparacin-inicial-del-entorno)
    *   [Ejecución de la Aplicación](#ejecucin-de-la-aplicacin)
3.  [💻 Interfaz de Usuario (UI)](#3-interfaz-de-usuario-ui)
    *   [Visión General](#visin-general)
    *   [Barra Superior](#barra-superior)
    *   [Panel Izquierdo: Tabla de Contenidos (TOC)](#panel-izquierdo-tabla-de-contenidos-toc)
    *   [Panel Derecho: Visor de Documentos](#panel-derecho-visor-de-documentos)
    *   [Barra de Estado](#barra-de-estado)
4.  [📝 Uso Básico: Generar y Visualizar Documentación](#4-uso-bsico-generar-y-visualizar-documentacin)
    *   [Generación Automática al Inicio](#generacin-automtica-al-inicio)
    *   [Botón "Generar Documentación"](#botn-generar-documentacin)
5.  [📊 Uso Avanzado: Gestión de la Documentación](#5-uso-avanzado-gestin-de-la-documentacin)
    *   [Acceder al Gestor de Capítulos](#acceder-al-gestor-de-captulos)
    *   [Configuración Global del Documento](#configuracin-global-del-documento)
    *   [Añadir un Nuevo Capítulo](#aadadir-un-nuevo-captulo)
    *   [Editar un Capítulo Existente](#editar-un-captulo-existente)
    *   [Eliminar un Capítulo](#eliminar-un-captulo)
    *   [Reordenar Capítulos](#reordenar-captulos)
    *   [Abrir y Editar Plantillas (Markdown + Jinja2)](#abrir-y-editar-plantillas-markdown--jinja2)
        *   [Sintaxis Markdown](#sintaxis-markdown)
        *   [Sintaxis Jinja2](#sintaxis-jinja2)
6.  [🔍 Búsqueda de Contenido](#6-bsqueda-de-contenido)
    *   [Cómo Realizar una Búsqueda](#cmo-realizar-una-bsqueda)
    *   [Navegación entre Coincidencias](#navegacin-entre-coincidencias)
7.  [⚙️ Configuración del Editor Externo](#7-configuracin-del-editor-externo)
8.  [📂 Estructura de Archivos](#8-estructura-de-archivos)
9.  [ troubleshoot Solución de Problemas](#9--solucin-de-problemas)
    *   [Errores al Cargar/Guardar `doc_config.json`](#errores-al-cargarguardar-doc_configjson)
    *   [Editor Externo no se Abre (`FileNotFoundError`)](#editor-externo-no-se-abre-filenotfounderror)
    *   [Errores al Renderizar Plantillas (Jinja2/Markdown)](#errores-al-renderizar-plantillas-jinja2markdown)
    *   [IDs de Capítulo Duplicados o Inválidos](#ids-de-captulo-duplicados-o-invlidos)
    *   [Plantillas no Encontradas](#plantillas-no-encontradas)
10. [💡 Consejos y Buenas Prácticas](#10-consejos-y-buenas-prcticas)
11. [👋 Despedida](#11-despedida)

---

## 1. 🚀 Introducción

### ¿Qué es Osiris Documentador?

Osiris Documentador es una aplicación de escritorio basada en PyQt5 que te ayuda a organizar y visualizar la documentación de tus proyectos. Utiliza archivos de texto plano escritos en formato Markdown para el contenido, y Jinja2 para la templating, lo que permite la inyección de datos dinámicos y la reutilización de contenido. La documentación se genera en HTML y se muestra directamente en la aplicación.

### Características Principales

*   Generación de documentación HTML a partir de plantillas Markdown.
*   Gestión de la estructura de capítulos (añadir, editar, eliminar, reordenar).
*   Visualización interactiva de la documentación con Tabla de Contenidos.
*   Funcionalidad de búsqueda de texto con navegación entre coincidencias.
*   Integración con un editor externo para la edición de plantillas.
*   Persistencia de la configuración de la documentación (capítulos, título, autor).

---

## 2. 🛠️ Primeros Pasos: Instalación y Ejecución

### Requisitos del Sistema

*   Python 3.x
*   Sistema operativo compatible con PyQt5 (Windows, macOS, Linux).

### Instalación de Dependencias

Antes de ejecutar la aplicación, necesitas instalar las librerías necesarias. Abre tu terminal o línea de comandos y ejecuta:

```bash
pip install PyQt5 Jinja2 markdown
```

### Preparación Inicial del Entorno

Cuando ejecutes el script por primera vez, Osiris Documentador creará automáticamente la siguiente estructura de directorios y archivos si no existen:

```
tu_directorio_proyecto/
├── osiris_doc_gen.py          # Tu script principal
├── doc_config.json            # Archivo de configuración de la documentación
└── documentation/             # Directorio base para la documentación
    ├── osiris_documentation.html  # Salida HTML generada
    └── templates/             # Directorio para tus archivos de plantilla Markdown
        ├── bienvenida.md
        ├── primeros_pasos.md
        └── uso_avanzado.md
```

Se te notificará mediante un `QMessageBox` y la barra de estado cuando estos archivos y directorios sean creados. `doc_config.json` se inicializará con una configuración de ejemplo para que puedas empezar inmediatamente.

### Ejecución de la Aplicación

Para iniciar Osiris Documentador, navega hasta el directorio donde guardaste el script `osiris_doc_gen.py` en tu terminal y ejecuta:

```bash
python3 osiris_doc_gen.py
```

La aplicación se abrirá y generará automáticamente la documentación con la configuración actual, mostrándola en el visor.

---

## 3. 💻 Interfaz de Usuario (UI)

### Visión General

La ventana principal de Osiris Documentador se divide en varias secciones clave para facilitar la interacción:

*   **Barra Superior:** Contiene botones de acción para generar, gestionar y buscar en la documentación.
*   **Panel Izquierdo (Tabla de Contenidos):** Un árbol de navegación que muestra la estructura de tus capítulos.
*   **Panel Derecho (Visor de Documentos):** Un navegador HTML interno que muestra la documentación generada.
*   **Barra de Estado:** Muestra mensajes informativos sobre las operaciones de la aplicación.

### Barra Superior

*   **"Generar Documentación 📖"**:
    *   Actualiza y regenera la documentación HTML utilizando la configuración actual de `doc_config.json` y las plantillas en `documentation/templates`.
    *   Es útil después de realizar cambios manuales en las plantillas o en el archivo de configuración.
*   **"Gestionar Documentación 📊"**:
    *   Abre un diálogo avanzado para gestionar la estructura de tu documentación: añadir, editar, eliminar y reordenar capítulos. Es tu centro de control para la configuración del documento.
*   **Campo de Búsqueda:**
    *   `QLineEdit` donde introduces el texto que deseas buscar en la documentación actual.
*   **"Buscar 🔍"**:
    *   Inicia una nueva búsqueda del texto introducido en el campo de búsqueda, comenzando desde el principio del documento.
*   **"Siguiente ▶️"**:
    *   Navega a la siguiente coincidencia del texto de búsqueda en el documento.
*   **"Anterior ◀️"**:
    *   Navega a la coincidencia anterior del texto de búsqueda en el documento.

### Panel Izquierdo: Tabla de Contenidos (TOC)

Este panel muestra un árbol con los títulos de tus capítulos, tal como están definidos en `doc_config.json`.
*   Al hacer clic en un título de capítulo, el visor de documentos se desplazará automáticamente a la sección correspondiente en el HTML.

### Panel Derecho: Visor de Documentos

Este es el área principal donde se muestra tu documentación generada. Es un visor HTML que:
*   Muestra el contenido de tus plantillas Markdown convertidas a HTML.
*   Renderiza el CSS por defecto para una lectura agradable.
*   Permite hacer clic en enlaces externos (se abrirán en tu navegador web por defecto).
*   Permite navegar entre secciones internas del documento usando los enlaces de la Tabla de Contenidos o las anclas definidas en tus plantillas.

### Barra de Estado

Ubicada en la parte inferior de la ventana, esta barra muestra mensajes en tiempo real sobre las acciones que se están realizando, errores, o información relevante para el usuario.

---

## 4. 📝 Uso Básico: Generar y Visualizar Documentación

### Generación Automática al Inicio

Cada vez que abres Osiris Documentador, el programa:
1.  Carga la configuración desde `doc_config.json`.
2.  Verifica y crea las plantillas de ejemplo si no existen.
3.  Genera el archivo `osiris_documentation.html` basado en esta configuración.
4.  Muestra el contenido HTML en el visor.

Esto asegura que siempre tengas la última versión de tu documentación disponible al iniciar la aplicación.

### Botón "Generar Documentación"

Si realizas cambios manuales en el archivo `doc_config.json` o editas directamente alguno de los archivos `.md` de plantilla fuera de la aplicación (aunque se recomienda usar el gestor interno), debes hacer clic en el botón **"Generar Documentación 📖"** en la barra superior.

Esto recargará la configuración, procesará todas las plantillas y actualizará el visor, mostrando los cambios.

---

## 5. 📊 Uso Avanzado: Gestión de la Documentación

El botón **"Gestionar Documentación 📊"** abre el `ChapterManagerDialog`, un potente diálogo para controlar la estructura y los metadatos de tu documentación.

### Acceder al Gestor de Capítulos

Haz clic en el botón **"Gestionar Documentación 📊"** en la barra superior. Se abrirá una nueva ventana de diálogo.

### Configuración Global del Documento

En la parte superior del diálogo, encontrarás campos para configurar el título general del documento y el autor:

*   **"Título del Documento"**: El título principal que aparecerá en la parte superior del documento HTML generado y en la pestaña del navegador.
*   **"Autor del Documento"**: El nombre del autor o la entidad responsable del documento.

Estos valores se guardarán en `doc_config.json` cuando aceptes los cambios.

### Añadir un Nuevo Capítulo

1.  En el diálogo "Gestionar Capítulos de Documentación", haz clic en el botón **"➕ Añadir"**.
2.  Se abrirá un diálogo más pequeño: "Editar Capítulo de Documentación".
3.  Rellena los siguientes campos:
    *   **"Título del Capítulo"**: El título que aparecerá en la Tabla de Contenidos y como encabezado en el documento HTML.
    *   **"ID (para anclas HTML)"**: Un identificador único para este capítulo. **¡Importante!** Este ID debe ser una cadena simple sin espacios, sin caracteres especiales (solo letras, números, guiones `-` y guiones bajos `_`). Se utiliza para los enlaces internos (anclas HTML) en la Tabla de Contenidos. Si no lo introduces, el programa generará uno.
    *   **"Ruta de Plantilla (.md)"**: La ruta al archivo Markdown (`.md`) que contendrá el contenido de este capítulo. Puedes usar rutas relativas al directorio raíz del script (ej: `documentation/templates/mi_nuevo_capitulo.md`) o rutas absolutas. Se recomienda mantenerlos dentro del subdirectorio `documentation/templates/`.
    *   **"Datos Extra (JSON)"**: Un objeto JSON (diccionario) con datos adicionales que quieras inyectar en tu plantilla Jinja2. Por ejemplo: `{"version": "1.0", "fecha_revision": "2023-10-27"}`. Puedes dejarlo vacío si no lo necesitas.
4.  Haz clic en **"OK"** para añadir el capítulo. Si el ID no es único o hay un error en el JSON de datos extra, se te notificará.

### Editar un Capítulo Existente

1.  En el diálogo "Gestionar Capítulos de Documentación", selecciona un capítulo de la lista.
2.  Haz clic en el botón **"✏️ Editar"**.
3.  Se abrirá el diálogo "Editar Capítulo de Documentación" con los datos del capítulo seleccionado precargados.
4.  Modifica los campos que desees y haz clic en **"OK"** para guardar los cambios.

### Eliminar un Capítulo

1.  En el diálogo "Gestionar Capítulos de Documentación", selecciona el capítulo que deseas eliminar de la lista.
2.  Haz clic en el botón **"🗑️ Eliminar"**.
3.  Se te pedirá confirmación. Haz clic en **"Yes"** para eliminarlo.
    *   **Nota:** Esto solo elimina el capítulo de la *estructura de la documentación* (de `doc_config.json`); **no elimina el archivo `.md` de la plantilla asociada** de tu disco.

### Reordenar Capítulos

Puedes cambiar el orden en que aparecen los capítulos en el documento y en la Tabla de Contenidos:

1.  Selecciona un capítulo de la lista.
2.  Haz clic en **"🔼 Subir"** para moverlo una posición hacia arriba.
3.  Haz clic en **"🔽 Bajar"** para moverlo una posición hacia abajo.

### Abrir y Editar Plantillas (Markdown + Jinja2)

Para editar el contenido real de un capítulo:

1.  En el diálogo "Gestionar Capítulos de Documentación", selecciona el capítulo cuya plantilla quieres editar.
2.  Haz clic en el botón **"📂 Abrir Plantilla"**.
3.  **Si el archivo de plantilla no existe**, la aplicación te preguntará si deseas crearlo con un contenido básico de ejemplo.
4.  El archivo se abrirá en el **editor externo** configurado en la variable `EDITOR_COMMAND` (por defecto `gedit`).
5.  Realiza tus cambios en el archivo Markdown y **guárdalo** en tu editor.
6.  **Cierra el editor externo**. La aplicación detectará que se ha cerrado.
7.  Se te preguntará si deseas **regenerar la documentación** ahora para ver los cambios. Haz clic en **"Yes"**.
    *   **Importante:** Asegúrate de que tu `EDITOR_COMMAND` esté configurado para **esperar** a que el editor se cierre (ej: `code --wait` para VS Code). Si no espera, la aplicación no sabrá cuándo has terminado de editar.

#### Sintaxis Markdown

Tus plantillas Markdown admiten la sintaxis extendida de Markdown, incluyendo:

*   Encabezados (`#`, `##`, `###`, etc.)
*   Párrafos
*   Negrita (`**texto**`), cursiva (`*texto*`)
*   Listas (ordenadas y desordenadas)
*   Enlaces (`[Texto del enlace](url)`)
*   Imágenes (`![Alt text](ruta/a/imagen.jpg)`)
*   Bloques de código (` ```lenguaje\n código \n ``` `)
*   Tablas
*   Citas (`> `)

#### Sintaxis Jinja2

Las plantillas Markdown se procesan con Jinja2 antes de ser convertidas a HTML. Esto te permite inyectar datos dinámicos y reutilizar contenido.

Tienes acceso a dos variables principales dentro de tus plantillas:

*   **`chapter`**: Un diccionario que contiene los metadatos del capítulo actual (definidos en `doc_config.json`).
    *   Puedes acceder a `{{ chapter.id }}` para el ID del capítulo.
    *   Puedes acceder a `{{ chapter.titulo }}` para el título del capítulo.
    *   Puedes acceder a `{{ chapter.plantilla }}` para la ruta de la plantilla.
*   **`datos_extra`**: Un diccionario que contiene los datos que especificaste en el campo "Datos Extra (JSON)" al crear/editar el capítulo.
    *   Si en "Datos Extra" pusiste `{"version": "1.0", "creado_por": "Osiris"}`, puedes usar `{{ datos_extra.version }}` o `{{ datos_extra.creado_por }}`.

**Ejemplo de plantilla Markdown con Jinja2:**

```markdown
# {{ chapter.titulo }}

Bienvenido al capítulo de {{ chapter.id }}.

Este capítulo fue creado el {{ datos_extra.creado_el | default("fecha desconocida") }}.

Aquí puedes encontrar información importante sobre el uso de Osiris Documentador.

```python
# Un ejemplo de código Python
def hola_osiris():
    print("¡Hola desde Osiris Documentador!")

hola_osiris()
```

Para más detalles sobre Jinja2, consulta su documentación oficial.

---

## 6. 🔍 Búsqueda de Contenido

Osiris Documentador te permite buscar texto dentro del documento HTML cargado en el visor.

### Cómo Realizar una Búsqueda

1.  Introduce el texto que deseas buscar en el **campo de búsqueda** en la barra superior.
2.  Presiona `Enter` o haz clic en el botón **"Buscar 🔍"**. La primera coincidencia se resaltará.

### Navegación entre Coincidencias

*   Haz clic en **"Siguiente ▶️"** para saltar a la siguiente coincidencia.
*   Haz clic en **"Anterior ◀️"** para saltar a la coincidencia anterior.

Si no se encuentran más coincidencias en una dirección, la búsqueda "envolverá" el documento y continuará desde el principio o el final, según la dirección de la búsqueda.

---

## 7. ⚙️ Configuración del Editor Externo

Puedes cambiar el comando utilizado para abrir las plantillas Markdown. Busca la línea:

```python
EDITOR_COMMAND = "gedit" # Por defecto a VS Code (con espera), ajusta para tu OS/editor
```

en el archivo `osiris_doc_gen.py` y modifícala según tu editor preferido.

**Ejemplos de `EDITOR_COMMAND`:**

*   **Visual Studio Code (con espera):** `"code --wait"`
*   **Sublime Text (con espera):** `"subl -w"`
*   **Gedit (Linux):** `"gedit"`
*   **Nano (Linux CLI - abre nueva terminal):** `"gnome-terminal -- bash -c 'nano %f; exec bash'"` (puede variar según tu emulador de terminal)
*   **Notepad (Windows):** `"notepad.exe"` (no espera por defecto)

**Es crucial que el comando haga que el editor *espere* a ser cerrado** para que la aplicación pueda detectar cuándo has terminado de editar y preguntarte si quieres regenerar la documentación.

---

## 8. 📂 Estructura de Archivos

Aquí se detalla la estructura de archivos que Osiris Documentador espera y genera en el directorio donde se ejecuta `osiris_doc_gen.py`:

```
.
├── osiris_doc_gen.py        # El script principal de la aplicación.
├── doc_config.json          # Archivo JSON que define la estructura del documento:
│                            # - Título global, Autor.
│                            # - Lista de capítulos: título, ID, ruta de plantilla y datos extra.
│                            #   Este archivo es gestionado por la aplicación.
└── documentation/           # Directorio principal para el output y las plantillas.
    ├── osiris_documentation.html # El archivo HTML final generado, que se visualiza en la aplicación.
    │                             # Siempre se sobrescribe al generar.
    └── templates/           # Subdirectorio donde DEBEN residir tus archivos de plantilla Markdown (.md).
        ├── bienvenida.md      # Ejemplo de plantilla Markdown con Jinja2.
        ├── primeros_pasos.md  # Otro ejemplo de plantilla.
        └── uso_avanzado.md    # Otro ejemplo de plantilla.
        └── ...                # Aquí guardarías todas tus plantillas de capítulos.
```

---

## 9.  troubleshoot Solución de Problemas

### Errores al Cargar/Guardar `doc_config.json`

*   **Problema:** "Error de JSON", "Error de Lectura", "Error de Guardado".
*   **Causa:** El archivo `doc_config.json` está dañado, contiene sintaxis JSON inválida o hay problemas de permisos.
*   **Solución:**
    *   Asegúrate de que `doc_config.json` sea un JSON válido. Puedes usar un validador JSON en línea.
    *   Verifica los permisos de escritura/lectura en el directorio de la aplicación.
    *   Si el error persiste y no tienes cambios importantes, puedes eliminar `doc_config.json` y la aplicación creará uno de ejemplo al reiniciar.

### Editor Externo no se Abre (`FileNotFoundError`)

*   **Problema:** "Editor no encontrado", "Error al abrir el editor".
*   **Causa:** El comando especificado en `EDITOR_COMMAND` no está en la ruta del sistema o no es el comando correcto para tu editor.
*   **Solución:**
    *   Verifica que el nombre del comando sea correcto para tu sistema operativo y editor (ej: `code` para VS Code, `gedit` para Gedit).
    *   Asegúrate de que el editor esté instalado y que su ejecutable sea accesible desde la línea de comandos (esté en tu PATH).
    *   Considera usar la ruta completa al ejecutable de tu editor si no está en el PATH (ej: `C:\\Program Files\\VS Code\\bin\\code.cmd --wait`).

### Errores al Renderizar Plantillas (Jinja2/Markdown)

*   **Problema:** Mensajes de error como "Error al cargar o renderizar la plantilla", "SyntaxError", "UndefinedError".
*   **Causa:**
    *   Errores de sintaxis en tus archivos `.md` de plantilla (especialmente en la parte de Jinja2).
    *   La plantilla especificada en `doc_config.json` no existe o la ruta es incorrecta.
    *   Intentas acceder a variables Jinja2 que no están definidas (ej: `{{ datos_extra.algo_que_no_existe }}`).
*   **Solución:**
    *   Revisa cuidadosamente el archivo de plantilla mencionado en el error.
    *   Asegúrate de que la ruta de la plantilla en `doc_config.json` (y en el diálogo de edición de capítulo) sea correcta y apunte a un archivo existente.
    *   Si usas Jinja2, verifica que las variables `chapter` y `datos_extra` se usen correctamente. Para variables opcionales, usa filtros `default` (ej: `{{ datos_extra.mi_variable | default('Valor por defecto') }}`).

### IDs de Capítulo Duplicados o Inválidos

*   **Problema:** Mensaje "ID Duplicado" o "El ID del capítulo solo puede contener...".
*   **Causa:** Has introducido un ID de capítulo que ya está siendo utilizado por otro capítulo, o contiene caracteres no permitidos para un ID HTML.
*   **Solución:**
    *   Asegúrate de que cada capítulo tenga un ID único en `doc_config.json`.
    *   Usa solo letras, números, guiones (`-`) y guiones bajos (`_`) para los IDs.

### Plantillas no Encontradas

*   **Problema:** Al generar la documentación, un capítulo aparece con el mensaje "(Sin contenido de plantilla especificado)" o "Error al cargar o renderizar la plantilla" mencionando un archivo no encontrado.
*   **Causa:** La ruta especificada para la plantilla de ese capítulo en `doc_config.json` es incorrecta o el archivo de plantilla no existe en esa ubicación.
*   **Solución:**
    *   Ve a "Gestionar Documentación", selecciona el capítulo problemático, haz clic en "Editar" y verifica la "Ruta de Plantilla (.md)".
    *   Asegúrate de que la ruta sea correcta y que el archivo exista en el sistema de archivos. Si no existe, puedes crearlo desde el botón "Abrir Plantilla" dentro del gestor de capítulos.

---

## 10. 💡 Consejos y Buenas Prácticas

*   **Mantén tus IDs de Capítulo Significativos:** Usar IDs claros y concisos como `intro_proyecto` o `instalacion_dependencias` te ayudará a navegar y referenciar capítulos más fácilmente.
*   **Organiza tus Plantillas:** Aunque todas las plantillas pueden estar en `documentation/templates/`, para proyectos muy grandes, podrías crear subdirectorios dentro de `templates/` (ej: `templates/conceptos/`, `templates/tutoriales/`) y referenciarlos en `doc_config.json` (ej: `plantilla: "documentation/templates/conceptos/basicos.md"`).
*   **Copia de Seguridad de `doc_config.json`:** Este archivo es el corazón de la estructura de tu documentación. Haz copias de seguridad regularmente.
*   **Utiliza Jinja2 para la Reutilización:** Si tienes información que se repite (versión del proyecto, fecha de la última actualización, nombres de colaboradores), defínela en `datos_extra` de un capítulo o incluso crea un capítulo "general" con datos extra que puedas referenciar en otras plantillas (aunque necesitarías Jinja2 `{% include %}` para eso, que no está expuesto directamente en el modelo actual pero es una posibilidad avanzada).
*   **Aprovecha Markdown:** Aprende las características avanzadas de Markdown (tablas, bloques de código, resaltado de sintaxis, enlaces internos) para crear documentos claros y bien formateados.
*   **Guarda Frecuentemente:** Después de hacer cambios importantes en la estructura o el contenido de las plantillas, guarda y regenera la documentación para ver los cambios reflejados.

---

## 11. 👋 Despedida

¡Esperamos que Osiris Documentador te sea una herramienta muy útil para gestionar tus proyectos! Si tienes alguna duda o sugerencia, no dudes en explorar el código o contactar al creador.

¡Feliz documentación! ✨
