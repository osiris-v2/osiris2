
**Manual de Instalación de Osiris Scale**
**Versión: General**
**Fecha: 2026-02-27**

**1. Visión General del Sistema**

Osiris V2 es un ecosistema modular, adaptable y auto-evolutivo diseñado para la inteligencia artificial y sistemas extendidos. Proporciona una arquitectura robusta y personalizable que permite a los operadores configurar y expandir sus capacidades. El sistema integra inteligencia artificial con componentes modulares, facilitando el mantenimiento y la adaptación a diversos casos de uso.

**2. Características Clave**

*   **Independencia del Modelo de IA:** Osiris soporta la integración de múltiples paradigmas de IA, incluyendo Google Gemini, modelos de Hugging Face y soluciones propietarias. Esto ofrece flexibilidad para la elección y adaptación de modelos.
*   **Arquitectura Modular y Transparente:** El sistema se organiza en componentes intercambiables que simplifican el mantenimiento y la expansión. Cada elemento puede ser activado, desactivado o reemplazado según las necesidades operativas.
*   **Gestión Multimedia Avanzada:** La plataforma está equipada para procesar, transmitir y presentar contenido multimedia en tiempo real, utilizando herramientas como FFmpeg y protocolos como HLS.
*   **Ingeniería Cliente/Servidor en Rust:** Los módulos críticos de cliente y servidor se desarrollan en Rust, lo que contribuye a un alto rendimiento, concurrencia robusta y estabilidad.
*   **Exploración de Integración Blockchain:** Osiris investiga la fusión con tecnologías blockchain para futuras funcionalidades en la gestión segura de datos, identidades digitales y transacciones.
*   **Interfaz de Consola:** El sistema incluye una interfaz de consola con herramientas avanzadas y soporte contextual para una interacción eficiente y la configuración de módulos.

**3. Componentes Estructurales**

La estructura principal del sistema se organiza en los siguientes directorios:
*   `bin/`: Contiene los ejecutables y scripts centrales para la operación del sistema.
*   `DEBIAN/`: Alberga los paquetes de instalación, incluyendo los archivos de control.
*   `DOCS/`: Almacena la documentación técnica del proyecto.
*   `html/`: Proporciona el directorio para la interfaz web.

**4. Interacción con la IA (CRO)**

La inteligencia artificial de Osiris opera mediante el lenguaje CRO (Command Request Object), un pseudocódigo estructurado que permite la interacción directa con el núcleo del sistema para orquestar acciones.
*   **Modo Desarrollador (DevMode):** En este modo, cada acción propuesta por la IA se presenta como un comando CRO explícito al operador humano para su revisión y confirmación.
*   **Modo Producción:** En entornos operativos, la ejecución de comandos CRO se realiza de manera automática, y la comunicación de la IA se enfoca en la información y las acciones completadas.

**5. Instalación del Sistema**

**Importante:** El sistema se encuentra en fase de desarrollo. Se recomienda contactar al autor para soporte técnico o participación en el proyecto.

*   **Método Principal de Instalación:**
    Osiris se instala utilizando un paquete `.deb`. Actualmente, el instalador es `osiris2release.deb`, ubicado en el directorio `/DEBIAN/` del repositorio.

*   **Pasos para la Instalación:**
    1.  Descargue el archivo `osiris2release.deb`.
    2.  Ejecute el siguiente comando desde el directorio donde se descargó:
        `sudo dpkg -i osiris2release.deb`

*   **Configuración del Directorio Base:**
    El instalador instala los archivos en el directorio `/var/`. Durante la instalación, se solicitará un nombre base (por defecto, `osiris2`). Es posible especificar un nombre diferente para crear nuevas bases o actualizar existentes. Esto permite mantener múltiples versiones de Osiris (ej., `/var/osiris2`, `/var/osiris21`).

*   **Instalador Interno:**
    Tras la descarga inicial de archivos, la instalación se completa utilizando el "instalador interno". Puede acceder a él manualmente desde el directorio `**/var/VERSION**` (donde `VERSION` es el nombre base que haya elegido) ejecutando `./osiris` o directamente `./install.sh`.

*   **Modos de Instalación (Desarrollo vs. Release):**
    *   **Versión de Desarrollo:** Menos estricta, puede contener archivos en distintas fases de implementación y no está enfocada a la seguridad absoluta.
    *   **Versión Release:** Más estable y estricta, utiliza los archivos listados en `bin/gitup-release.txt`, que han sido probados y validados para producción. Se recomienda para sistemas en producción.

*   **Instalador BIO:**
    El instalador `bio.deb` corresponde a la versión de escritorio de Osiris. Se encuentra en fase de desarrollo e implementación.

**6. Herramientas y Componentes Integrados**

Osiris integra y utiliza diversas herramientas y componentes para su funcionamiento y gestión:

*   **GIT:** Se utiliza para la descarga, instalación y actualización del programa. Osiris también incluye herramientas para la gestión de versiones personalizadas del proyecto.
*   **DOCKER:** Permite la ejecución de aplicaciones en contenedores aislados, lo que contribuye a la estabilidad y el rendimiento del sistema, y es un eje central en el desarrollo de Osiris V2.
*   **FFMPEG:** Proporciona herramientas para descargar, compilar y gestionar diferentes versiones de FFmpeg de forma independiente para cada instalación de Osiris.
*   **APACHE2:** Realiza una instalación global del servidor Apache, permitiendo que las distintas versiones de Osiris configuren sus propios hosts virtuales.
*   **PHP-FPM:** Implementa FastCGI Process Manager para PHP, mejorando la seguridad y el rendimiento al separar las aplicaciones PHP en distintos "pools".
*   **NGINX:** Se utiliza para gestionar flujos de streaming HLS y otras funciones HTTP, complementando a Apache. Puede operar en contenedores Docker junto con FFmpeg para transmisiones.
*   **CERTBOT:** Facilita la creación automatizada de certificados SSL (HTTPS) para dominios web y hosts virtuales mediante Let's Encrypt.
*   **MARIADB:** Incluye el gestor de bases de datos Maria-DB, un derivado de MySQL, conocido por su potencia, flexibilidad y rendimiento.
*   **TMUX:** Osiris proporciona herramientas para descargar y actualizar tmux, un multiplexor de terminal. Permite composiciones personalizadas de la terminal.
*   **TERMINATOR:** Un emulador de terminal avanzado que mejora las funcionalidades de la terminal clásica y facilita tareas, especialmente en combinación con tmux.
*   **PYTHON:** Utilizado principalmente para aplicaciones de consola y gráficas no críticas en rendimiento, aprovechando su amplia biblioteca de módulos. Cada proyecto Osiris dispone de su propio entorno virtual Python.
*   **RUST:** Osiris incluye herramientas para descargar e instalar la última versión del lenguaje Rust, su compilador (`rustc`) y el asistente de proyectos (`cargo`), para desarrollar componentes de alto rendimiento como servidores y clientes.
*   **NODEJS:** Se pueden integrar proyectos basados en Node.js; Osiris ofrece herramientas para su instalación y uso.

**7. Contacto**

osiris.osscom@gmail.com

**Nota Final:** Este manual es un reflejo de la evolución de Osiris y será actualizado por la IA para mantener la información más reciente sobre su visión y capacidades.