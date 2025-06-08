#!/bin/bash

# ========================================================================================================
# Interfaz de comunicación con Gemini AI de Google
# Interfaz Name: Osiris
# Version: gemini
# Idioma: Español
#
# Descripción:
# Este script es un instalador y gestor completo para Docker y Docker Compose en sistemas Linux.
# Detecta automáticamente si Docker está instalado y ofrece opciones para:
#   - Instalación guiada en distribuciones populares (Debian/Ubuntu, Fedora/CentOS/RHEL).
#   - Gestión exhaustiva del servicio Docker (iniciar, detener, reiniciar, habilitar/deshabilitar al inicio).
#   - Gestión avanzada de imágenes, contenedores, redes y volúmenes Docker.
#   - Herramientas de limpieza para liberar espacio en disco.
#   - Diagnóstico y visualización de logs del sistema Docker.
#   - Opciones para añadir el usuario al grupo 'docker' y desinstalar Docker por completo.
#   - Soporte para Docker Compose (plugin y standalone).
#
# Instrucciones:
# 1. Guarda este código en un archivo (ej: 'osiris_docker_super_manager.sh').
# 2. Dale permisos de ejecución: chmod +x osiris_docker_super_manager.sh
# 3. Ejecútalo con 'sudo': sudo ./osiris_docker_super_manager.sh
#
# ¡Bienvenido a Osiris! Usa emojis para dinamizar la conversación. ✨
# ========================================================================================================

# --- COLORES PARA LA SALIDA DE TERMINAL ---
VERDE='\033[0;32m'    # Éxito, confirmación
ROJO='\033[0;31m'     # Error, advertencia crítica
AZUL='\033[0;34m'     # Información, progreso
AMARILLO='\033[1;33m' # Advertencia, prompts
CYAN='\033[0;36m'     # Comandos, elementos importantes
MAGENTA='\033[0;35m'  # Títulos de menú
RESET='\033[0m'       # Restablecer color

# --- CONSTANTES Y CONFIGURACIÓN PREDETERMINADA ---
# URL oficial para el script de instalación de conveniencia de Docker.
# NO es el método recomendado para producción, pero es útil para demos o entornos de desarrollo.
DOCKER_INSTALL_URL="https://get.docker.com"

# Versión predeterminada de Docker Compose Standalone a instalar.
# Siempre verifica la última versión estable aquí: https://github.com/docker/compose/releases
DOCKER_COMPOSE_VERSION="v2.27.0"
# URL para descargar el binario de Docker Compose Standalone.
DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)"
# Destino común para el binario de Docker Compose Standalone.
DOCKER_COMPOSE_DEST="/usr/local/bin/docker-compose"
# Directorio para la configuración del daemon Docker.
DOCKER_DAEMON_CONFIG_DIR="/etc/docker"
# Archivo de configuración principal del daemon.
DOCKER_DAEMON_JSON_FILE="${DOCKER_DAEMON_CONFIG_DIR}/daemon.json"

# --- FUNCIONES DE UTILIDAD GENERAL ---

# Función para imprimir un encabezado de sección con estilo.
# Utiliza colores y una barra para mejorar la legibilidad del menú.
print_section_header() {
    echo
    echo -e "${CYAN}=====================================================${RESET}"
    echo -e "${CYAN}=== $1 ===${RESET}"
    echo -e "${CYAN}=====================================================${RESET}"
    echo
}

# Función para preguntar al usuario y confirmar una acción.
# Muestra un prompt en AMARILLO y espera una respuesta 's' o 'n'.
# Retorna 0 para 'sí' (S/s) y 1 para 'no' (cualquier otra cosa).
confirm_action() {
    local prompt="$1"
    read -p "$(echo -e "${AMARILLO}$prompt (s/n): ${RESET}")" -n 1 -r
    echo # Imprime una nueva línea para limpiar el terminal después de la entrada del usuario.
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        return 0 # True (sí)
    else
        echo -e "${ROJO}Operación cancelada por el usuario. 😟${RESET}"
        return 1 # False (no)
    fi
}

# Función para ejecutar un comando de forma segura.
# Muestra el comando que se va a ejecutar, lo ejecuta y luego reporta el éxito o fracaso.
# Redirige stderr a stdout y usa 'tee' para mostrar la salida en tiempo real.
# Retorna el código de salida del comando.
safe_execute() {
    local cmd="$@"
    echo -e "${AZUL}Ejecutando: ${CYAN}$cmd${RESET}"
    # 'eval' permite la expansión de variables y comandos dentro de la cadena 'cmd'.
    # 'tee /dev/tty' muestra la salida en la terminal mientras también la permite ser capturada por 'eval'.
    if eval "$cmd" > >(tee /dev/tty); then
        echo -e "${VERDE}Comando ejecutado con éxito. ✅${RESET}"
        return 0 # Éxito
    else
        echo -e "${ROJO}Error al ejecutar el comando. Por favor, revisa los mensajes anteriores para más detalles. ❌${RESET}"
        return 1 # Fallo
    fi
}

# Función para verificar si el script se está ejecutando con permisos de superusuario (root).
# Si no se ejecuta como root, imprime un mensaje de error y sale del script.
check_sudo() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${ROJO}Este script debe ejecutarse con 'sudo' para poder gestionar Docker y los archivos del sistema. 🚨${RESET}"
        echo -e "${ROJO}Por favor, inténtalo de nuevo: ${CYAN}sudo ./$(basename "$0")${RESET}"
        exit 1 # Salir con código de error
    fi
}

# Función para detectar la distribución del sistema operativo.
# Lee '/etc/os-release' para obtener el ID de la distribución.
# Intenta 'lsb_release' si '/etc/os-release' no está presente o no es útil.
# Retorna el ID de la distribución en minúsculas.
get_distribution() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release # Carga las variables de ese archivo en el entorno actual
        echo "$ID" | tr '[:upper:]' '[:lower:]' # Convertir a minúsculas
    elif type lsb_release >/dev/null 2>&1; then
        lsb_release -is | tr '[:upper:]' '[:lower:]'
    elif [ -f /etc/redhat-release ]; then
        # Para CentOS/RHEL/AlmaLinux/RockyLinux, /etc/redhat-release contiene la información.
        cat /etc/redhat-release | awk '{print $1}' | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown" # Si no se detecta la distribución
    fi
}

# Función para verificar si Docker Engine está instalado.
# Comprueba la existencia del comando 'docker' en el PATH.
# Retorna 0 si está instalado, 1 si no.
is_docker_installed() {
    if command -v docker &>/dev/null; then
        return 0 # Docker está instalado
    else
        return 1 # Docker NO está instalado
    fi
}

# Función para detectar qué tipo de Docker Compose está instalado.
# Docker Compose puede ser un plugin de la CLI de Docker (docker compose) o un binario standalone (docker-compose).
# Retorna "plugin", "standalone" o "none".
detect_docker_compose_type() {
    if docker compose version &>/dev/null; then
        echo "plugin" # docker compose (con espacio) es el plugin
    elif command -v docker-compose &>/dev/null; then
        echo "standalone" # docker-compose (con guion) es el binario standalone
    else
        echo "none" # Docker Compose no está instalado en ninguna forma
    fi
}

# Función para añadir el usuario actual al grupo 'docker'.
# Esto permite al usuario ejecutar comandos Docker sin necesidad de 'sudo'.
# Requiere que el usuario cierre y vuelva a iniciar sesión o reinicie para que los cambios surtan efecto.
add_user_to_docker_group() {
    print_section_header "Añadir Usuario al Grupo Docker 👥"
    local current_user=$(whoami) # Obtiene el nombre del usuario actual.
    echo "Para poder usar Docker sin 'sudo', tu usuario ('${CYAN}$current_user${RESET}') debe ser miembro del grupo 'docker'."
    
    # Comprueba si el usuario ya es miembro del grupo 'docker'.
    if groups $current_user | grep -q '\bdocker\b'; then
        echo -e "${VERDE}Tu usuario ('$current_user') ya es miembro del grupo 'docker'. ¡Todo listo! ✅${RESET}"
    else
        if confirm_action "¿Deseas añadir a tu usuario ('$current_user') al grupo 'docker' ahora?"; then
            # 'usermod -aG' añade el usuario al grupo especificado sin eliminarlo de otros grupos.
            safe_execute "usermod -aG docker $current_user"
            if [ $? -eq 0 ]; then
                echo -e "${VERDE}Usuario '$current_user' añadido al grupo 'docker' con éxito. ✅${RESET}"
                echo -e "${AMARILLO}¡ADVERTENCIA IMPORTANTE! Para que este cambio surta efecto, debes CERRAR COMPLETAMENTE tu sesión de terminal y volver a iniciarla, o REINICIAR tu sistema. 🚪🔄${RESET}"
                echo -e "${CYAN}Después de reiniciar la sesión, podrás ejecutar comandos 'docker' sin usar 'sudo'. ${RESET}"
            fi
        fi
    fi
}

# --- FUNCIONES DE INSTALACIÓN DE DOCKER ---

# Instala Docker CE en sistemas basados en Debian/Ubuntu.
# Sigue las instrucciones oficiales para añadir el repositorio de Docker.
install_docker_debian() {
    print_section_header "Instalación de Docker en Debian/Ubuntu 🐧"
    echo "Este proceso instalará Docker CE (Community Edition), containerd y el plugin Docker Compose CLI"
    echo "desde los repositorios oficiales de Docker, asegurando las últimas versiones estables."
    echo -e "${AMARILLO}Asegúrate de tener una conexión a internet estable. 📶${RESET}"
    echo
    if confirm_action "¿Proceder con la instalación de Docker en Debian/Ubuntu?"; then
        echo -e "${AZUL}Paso 1/7: Actualizando índices de paquetes APT...${RESET}"
        safe_execute "apt update" || { echo -e "${ROJO}Fallo al actualizar APT. Verifica tu conexión a internet o los repositorios.${RESET}"; return 1; }

        echo -e "${AZUL}Paso 2/7: Instalando paquetes de pre-requisitos para la configuración del repositorio...${RESET}"
        # 'ca-certificates' para asegurar conexiones SSL, 'curl' para descargar, 'gnupg' para claves, 'lsb-release' para detectar distribución.
        safe_execute "apt install -y ca-certificates curl gnupg lsb-release" || { echo -e "${ROJO}Fallo al instalar pre-requisitos.${RESET}"; return 1; }

        echo -e "${AZUL}Paso 3/7: Preparando el directorio para las claves GPG...${RESET}"
        # Crea el directorio '/etc/apt/keyrings' con permisos adecuados si no existe.
        safe_execute "install -m 0755 -d /etc/apt/keyrings" || { echo -e "${ROJO}Fallo al crear directorio de keyrings.${RESET}"; return 1; }
        
        echo -e "${AZUL}Paso 4/7: Descargando y añadiendo la clave GPG oficial de Docker para verificar la autenticidad de los paquetes...${RESET}"
        # Elimina cualquier clave antigua para evitar conflictos y añade la nueva.
        safe_execute "rm -f /etc/apt/keyrings/docker.gpg"
        safe_execute "curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg" || { echo -e "${ROJO}Fallo al descargar o procesar la clave GPG de Docker.${RESET}"; return 1; }
        safe_execute "chmod a+r /etc/apt/keyrings/docker.gpg" # Otorga permisos de lectura global a la clave.

        echo -e "${AZUL}Paso 5/7: Añadiendo el repositorio oficial de Docker a las fuentes de APT...${RESET}"
        local DISTRO_CODENAME=$(lsb_release -cs) # Obtiene el nombre en clave de la distribución (ej: 'bookworm' para Debian 12).
        # Agrega la línea del repositorio al archivo de configuración de APT.
        echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
            $DISTRO_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null || { echo -e "${ROJO}Fallo al añadir el repositorio de Docker.${RESET}"; return 1; }
        
        echo -e "${AZUL}Paso 6/7: Actualizando índices de paquetes nuevamente para incluir el nuevo repositorio de Docker...${RESET}"
        safe_execute "apt update" || { echo -e "${ROJO}Fallo al actualizar APT después de añadir el repositorio de Docker.${RESET}"; return 1; }

        echo -e "${AZUL}Paso 7/7: Instalando Docker Engine, containerd y Docker Compose (plugin CLI)...${RESET}"
        # Instala los paquetes principales de Docker.
        safe_execute "apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" || { echo -e "${ROJO}Fallo al instalar los componentes de Docker. Revisa dependencias o conflictos.${RESET}"; return 1; }

        echo -e "${VERDE}Docker se ha instalado correctamente y el servicio ha sido iniciado automáticamente. ✅🎉${RESET}"
        echo -e "${AZUL}Ahora, es crucial añadir tu usuario al grupo 'docker' para usar Docker sin 'sudo'.${RESET}"
        add_user_to_docker_group # Llama a la función para añadir el usuario al grupo Docker.
        echo -e "${AMARILLO}¡Recuerda que deberás cerrar y volver a abrir tu sesión de terminal para que los cambios surtan efecto! 🚪🔄${RESET}"
        echo -e "${CYAN}Puedes verificar la instalación ejecutando: ${VERDE}docker run hello-world${RESET}"
    else
        echo -e "${ROJO}Instalación de Docker cancelada. ¡Quizás en otra ocasión! 😟${RESET}"
    fi
}

# Instala Docker CE en sistemas basados en Fedora/CentOS/RHEL.
# Sigue las instrucciones oficiales para añadir el repositorio de Docker y usar DNF.
install_docker_fedora() {
    print_section_header "Instalación de Docker en Fedora/CentOS/RHEL 🔶"
    echo "Este proceso instalará Docker CE (Community Edition), containerd y el plugin Docker Compose"
    echo "desde los repositorios oficiales de Docker utilizando el gestor de paquetes DNF/YUM."
    echo -e "${AMARILLO}Asegúrate de tener una conexión a internet estable. 📶${RESET}"
    echo
    if confirm_action "¿Proceder con la instalación de Docker en Fedora/CentOS/RHEL?"; then
        echo -e "${AZUL}Paso 1/4: Instalando 'dnf-plugins-core' y habilitando el repositorio de Docker...${RESET}"
        # Instala un plugin necesario para gestionar repositorios y añade el repo de Docker.
        safe_execute "dnf -y install dnf-plugins-core" || { echo -e "${ROJO}Fallo al instalar dnf-plugins-core.${RESET}"; return 1; }
        safe_execute "dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo" || { echo -e "${ROJO}Fallo al añadir el repositorio de Docker.${RESET}"; return 1; }

        echo -e "${AZUL}Paso 2/4: Instalando Docker Engine, containerd y Docker Compose (plugin CLI)...${RESET}"
        # Instala los paquetes principales de Docker.
        safe_execute "dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" || { echo -e "${ROJO}Fallo al instalar los componentes de Docker. Revisa dependencias.${RESET}"; return 1; }

        echo -e "${AZUL}Paso 3/4: Iniciando el servicio Docker...${RESET}"
        safe_execute "systemctl start docker" || { echo -e "${ROJO}Fallo al iniciar el servicio Docker. Verifica los logs con 'journalctl -u docker.service'.${RESET}"; return 1; }
        
        echo -e "${AZUL}Paso 4/4: Habilitando el servicio Docker para que se inicie automáticamente en cada arranque...${RESET}"
        safe_execute "systemctl enable docker" || { echo -e "${ROJO}Fallo al habilitar el servicio Docker para el inicio automático.${RESET}"; return 1; }

        echo -e "${VERDE}Docker se ha instalado correctamente y el servicio está corriendo. ✅🎉${RESET}"
        echo -e "${AZUL}Ahora, es crucial añadir tu usuario al grupo 'docker' para usar Docker sin 'sudo'.${RESET}"
        add_user_to_docker_group # Llama a la función para añadir el usuario al grupo Docker.
        echo -e "${AMARILLO}¡Recuerda que deberás cerrar y volver a abrir tu sesión de terminal para que los cambios surtan efecto! 🚪🔄${RESET}"
        echo -e "${CYAN}Puedes verificar la instalación ejecutando: ${VERDE}docker run hello-world${RESET}"
    else
        echo -e "${ROJO}Instalación de Docker cancelada. ¡Quizás en otra ocasión! 😟${RESET}"
    fi
}

# Instala Docker usando el script de conveniencia de get.docker.com.
# Este método es rápido pero NO recomendado para entornos de producción por razones de seguridad y control.
install_docker_generic() {
    print_section_header "Instalación Genérica de Docker (Script de Conveniencia) 🌐"
    echo "Esta opción utiliza el script de conveniencia de Docker (get.docker.com)."
    echo "${ROJO}¡ADVERTENCIA! Este método NO es el recomendado para entornos de producción y debe usarse con precaución, ya que salta pasos de verificación de paquetes y puede ser menos predecible.${RESET}"
    echo "Para la forma más segura y recomendada, visita la documentación oficial de Docker para tu distribución:"
    echo "  ${CYAN}https://docs.docker.com/engine/install/${RESET}"
    echo -e "${AMARILLO}Asegúrate de tener una conexión a internet estable. 📶${RESET}"
    echo
    if confirm_action "¿Deseas intentar ejecutar el script de instalación de conveniencia de Docker?"; then
        echo -e "${AZUL}Paso 1/2: Descargando el script de instalación desde ${DOCKER_INSTALL_URL}...${RESET}"
        # Descarga el script y lo guarda en 'get-docker.sh'.
        safe_execute "curl -fsSL ${DOCKER_INSTALL_URL} -o get-docker.sh" || { echo -e "${ROJO}Fallo al descargar el script. Verifica la URL y tu conexión. ${RESET}"; return 1; }
        
        echo -e "${AZUL}Paso 2/2: Ejecutando el script (esto puede tardar unos minutos y puede solicitar tu contraseña de sudo)...${RESET}"
        # Ejecuta el script descargado. Este script maneja la instalación y el inicio del servicio.
        # Luego, se elimina el script para limpiar.
        if safe_execute "sh get-docker.sh"; then
            safe_execute "rm get-docker.sh" # Limpiar el script descargado.
            echo -e "${VERDE}Docker se ha instalado (posiblemente). ✅${RESET}"
            add_user_to_docker_group # Llama a la función para añadir el usuario al grupo Docker.
            echo -e "${AMARILLO}¡Recuerda que deberás cerrar y volver a abrir tu sesión de terminal para que los cambios surtan efecto! 🚪🔄${RESET}"
            echo -e "${CYAN}Puedes verificar la instalación ejecutando: ${VERDE}docker run hello-world${RESET}"
        else
            echo -e "${ROJO}El script de instalación de Docker falló. Consulta los mensajes anteriores y los logs para más detalles. 😞${RESET}"
            safe_execute "rm -f get-docker.sh" # Asegurar limpieza incluso en caso de fallo.
        fi
    else
        echo -e "${ROJO}Instalación genérica de Docker cancelada. 😟${RESET}"
    fi
}

# --- FUNCIONES DE GESTIÓN DEL SERVICIO DOCKER (DAEMON) ---

# Comprueba el estado actual del servicio Docker.
check_docker_status() {
    print_section_header "Estado del Servicio Docker ℹ️"
    echo -e "${AZUL}Verificando el estado del daemon Docker con systemctl...${RESET}"
    if systemctl is-active --quiet docker; then
        echo -e "${VERDE}El servicio Docker está ${CYAN}ACTIVO y CORRIENDO${VERDE}. ✅${RESET}"
    else
        echo -e "${ROJO}El servicio Docker está ${AMARILLO}INACTIVO o DETENIDO${ROJO}. ❌${RESET}"
    fi
    echo -e "${AZUL}Información detallada del servicio (últimas líneas del estado):${RESET}"
    safe_execute "systemctl status docker --no-pager" # '--no-pager' evita que 'less' abra la salida.
}

# Inicia el servicio Docker.
start_docker() {
    print_section_header "Iniciar Servicio Docker ▶️"
    if systemctl is-active --quiet docker; then
        echo -e "${VERDE}El servicio Docker ya está corriendo. No es necesario iniciarlo nuevamente. ✅${RESET}"
    else
        if confirm_action "¿Deseas iniciar el servicio Docker ahora?"; then
            echo -e "${AZUL}Intentando iniciar el servicio Docker...${RESET}"
            safe_execute "systemctl start docker"
            if [ $? -eq 0 ]; then
                echo -e "${VERDE}Servicio Docker iniciado con éxito. ¡Listo para usar! ✅${RESET}"
            else
                echo -e "${ROJO}Fallo al iniciar el servicio Docker. Esto podría deberse a errores de configuración o recursos insuficientes. Consulta los logs para depurar con 'journalctl -u docker.service'. ❌${RESET}"
            fi
        fi
    fi
}

# Detiene el servicio Docker.
stop_docker() {
    print_section_header "Detener Servicio Docker ⏹️"
    if ! systemctl is-active --quiet docker; then
        echo -e "${VERDE}El servicio Docker ya está detenido. No hay nada que detener. ✅${RESET}"
    else
        if confirm_action "¿Deseas detener el servicio Docker? Esto detendrá ${ROJO}todos los contenedores en ejecución${RESET} controlados por Docker. Los contenedores no se eliminarán, pero dejarán de funcionar. 🚨"; then
            echo -e "${AZUL}Intentando detener el servicio Docker...${RESET}"
            safe_execute "systemctl stop docker"
            if [ $? -eq 0 ]; then
                echo -e "${VERDE}Servicio Docker detenido con éxito. ✅${RESET}"
            else
                echo -e "${ROJO}Fallo al detener el servicio Docker. Intenta forzar la detención si es necesario (con 'systemctl stop docker --force') o verifica los logs. ❌${RESET}"
            fi
        fi
    fi
}

# Reinicia el servicio Docker.
restart_docker() {
    print_section_header "Reiniciar Servicio Docker 🔄"
    if confirm_action "¿Deseas reiniciar el servicio Docker? Esto detendrá y luego reiniciará ${ROJO}todos los contenedores en ejecución${RESET}. Esto puede ser necesario después de cambios de configuración o para resolver problemas."; then
        echo -e "${AZUL}Intentando reiniciar el servicio Docker...${RESET}"
        safe_execute "systemctl restart docker"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Servicio Docker reiniciado con éxito. ✅${RESET}"
        else
            echo -e "${ROJO}Fallo al reiniciar el servicio Docker. Verifica los logs para encontrar la causa. ❌${RESET}"
        fi
    fi
}

# Habilita el servicio Docker para que se inicie automáticamente al arrancar el sistema.
enable_docker_on_boot() {
    print_section_header "Habilitar Docker al Inicio del Sistema ⚡"
    echo "Habilitar el servicio Docker significa que se iniciará automáticamente cada vez que el sistema se arranque."
    if systemctl is-enabled --quiet docker; then
        echo -e "${VERDE}El servicio Docker ya está habilitado para iniciar automáticamente en el arranque. ✅${RESET}"
    else
        if confirm_action "¿Deseas habilitar el servicio Docker para que se inicie automáticamente en el arranque del sistema?"; then
            echo -e "${AZUL}Habilitando el servicio Docker...${RESET}"
            safe_execute "systemctl enable docker"
            if [ $? -eq 0 ]; then
                echo -e "${VERDE}Servicio Docker habilitado para el inicio automático. ✅${RESET}"
            else
                echo -e "${ROJO}Fallo al habilitar el servicio Docker para el inicio. ❌${RESET}"
            fi
        fi
    fi
}

# Deshabilita el servicio Docker para que NO se inicie automáticamente al arrancar el sistema.
disable_docker_on_boot() {
    print_section_header "Deshabilitar Docker al Inicio del Sistema 🛑"
    echo "Deshabilitar el servicio Docker significa que NO se iniciará automáticamente con el sistema. Tendrás que iniciarlo manualmente cada vez que lo necesites."
    if ! systemctl is-enabled --quiet docker; then
        echo -e "${VERDE}El servicio Docker ya está deshabilitado para iniciar automáticamente en el arranque. ✅${RESET}"
    else
        if confirm_action "¿Deseas deshabilitar el servicio Docker para que NO se inicie automáticamente en el arranque del sistema?"; then
            echo -e "${AZUL}Deshabilitando el servicio Docker...${RESET}"
            safe_execute "systemctl disable docker"
            if [ $? -eq 0 ]; then
                echo -e "${VERDE}Servicio Docker deshabilitado para el inicio automático. ✅${RESET}"
            else
                echo -e "${ROJO}Fallo al deshabilitar el servicio Docker para el inicio. ❌${RESET}"
            fi
        fi
    fi
}

# --- FUNCIONES DE GESTIÓN DE IMÁGENES DOCKER ---
list_images() {
    print_section_header "Listar Imágenes Docker 🖼️"
    echo "Mostrando todas las imágenes Docker disponibles en tu sistema. Esto incluye las imágenes descargadas y las que has construido."
    echo -e "${AZUL}Leyenda:${RESET}"
    echo -e "${CYAN}REPOSITORY:${RESET} Nombre de la imagen."
    echo -e "${CYAN}TAG:${RESET} Etiqueta de la versión de la imagen."
    echo -e "${CYAN}IMAGE ID:${RESET} Identificador único de la imagen."
    echo -e "${CYAN}CREATED:${RESET} Cuándo fue creada la imagen."
    echo -e "${CYAN}SIZE:${RESET} Tamaño de la imagen."
    safe_execute "docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}'"
    echo -e "${CYAN}Consejo: Las imágenes con '<none>' en REPOSITORY o TAG son 'dangling images' (imágenes colgantes) y pueden limpiarse para liberar espacio.${RESET}"
    echo -e "${CYAN}Usa la opción de limpieza de recursos para gestionarlas.${RESET}"
}

pull_image() {
    print_section_header "Descargar Imagen Docker ⬇️"
    echo "Descarga una imagen de Docker Hub (por defecto) o de un registro privado. El formato es 'nombre[:tag]'."
    echo "Ejemplos: 'ubuntu:latest', 'nginx', 'myregistry.com/myimage:v1.0'"
    read -p "$(echo -e "${AMARILLO}Introduce el nombre de la imagen a descargar: ${RESET}")" image_name
    if [ -z "$image_name" ]; then
        echo -e "${ROJO}El nombre de la imagen no puede estar vacío. Por favor, introduce un valor válido. ❌${RESET}"
        return
    fi
    if confirm_action "¿Deseas descargar la imagen '${image_name}'? Esto puede tardar dependiendo del tamaño y tu conexión."; then
        echo -e "${AZUL}Iniciando descarga de la imagen '${image_name}'...${RESET}"
        safe_execute "docker pull $image_name"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Imagen '${image_name}' descargada con éxito. ✅${RESET}"
            list_images
        else
            echo -e "${ROJO}Fallo al descargar la imagen '${image_name}'. Verifica el nombre, la etiqueta y tu conexión. ❌${RESET}"
        fi
    fi
}

remove_image() {
    print_section_header "Eliminar Imagen Docker 🗑️"
    echo "Elimina una imagen de Docker de tu sistema. ¡Una vez eliminada, no se puede recuperar fácilmente!"
    echo -e "${AMARILLO}ADVERTENCIA: Si la imagen está siendo utilizada por contenedores en ejecución, Docker te impedirá eliminarla. Debes detener y eliminar los contenedores primero. Si está en uso por contenedores detenidos, se te preguntará si quieres forzar la eliminación.${RESET}"
    list_images
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o el nombre completo de la imagen a eliminar (ej. 'abc123def456' o 'myimage:latest'): ${RESET}")" image_id
    if [ -z "$image_id" ]; then
        echo -e "${ROJO}El ID/Nombre de la imagen no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Estás seguro de que quieres eliminar la imagen '${image_id}'? Esto no se puede deshacer y puede afectar contenedores que la usen. 🚨💥"; then
        echo -e "${AZUL}Intentando eliminar la imagen '${image_id}'...${RESET}"
        # Utiliza 'docker rmi -f' para forzar la eliminación si la imagen no está en uso por contenedores en ejecución.
        # Sin '-f', Docker arrojará un error si hay contenedores detenidos que la usan.
        if safe_execute "docker rmi $image_id"; then
            echo -e "${VERDE}Imagen '${image_id}' eliminada con éxito. ✅${RESET}"
            list_images
        else
            echo -e "${ROJO}Fallo al eliminar la imagen '${image_id}'. Asegúrate de que no está en uso o intenta la limpieza de recursos. ❌${RESET}"
            echo -e "${CYAN}Si la imagen está en uso por un contenedor, deberás detener y eliminar el contenedor primero.${RESET}"
        fi
    fi
}

inspect_image() {
    print_section_header "Inspeccionar Imagen Docker 🔍"
    echo "Muestra información detallada de bajo nivel (formato JSON) sobre una imagen Docker. Esto incluye su historial, capas, configuración de red, volúmenes, etc."
    list_images
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre de la imagen a inspeccionar: ${RESET}")" image_id
    if [ -z "$image_id" ]; then
        echo -e "${ROJO}El ID/Nombre de la imagen no puede estar vacío. ❌${RESET}"
        return
    fi
    echo -e "${AZUL}Inspeccionando imagen '${image_id}'...${RESET}"
    safe_execute "docker inspect $image_id"
}

build_image() {
    print_section_header "Construir Imagen Docker (Básico) 🏗️"
    echo "Construye una imagen Docker a partir de un Dockerfile en un directorio (contexto) dado."
    echo -e "${AMARILLO}Asegúrate de que tu Dockerfile se encuentre en el directorio que especifiques como contexto.${RESET}"
    echo "Ejemplo de contexto: './mi_app_docker/' (el punto indica el directorio actual)"
    echo "Ejemplo de nombre de imagen: 'mi-app:latest' o 'mi-backend'"
    read -p "$(echo -e "${AMARILLO}Introduce la ruta al contexto del build (ej. './mi_app_docker/'): ${RESET}")" build_context
    if [ -z "$build_context" ]; then
        echo -e "${ROJO}La ruta del contexto no puede estar vacía. ❌${RESET}"
        return
    fi
    # Normalizar la ruta del contexto para que termine en '/' si es un directorio.
    if [ -d "$build_context" ] && [[ "$build_context" != */ ]]; then
        build_context="${build_context}/"
    fi

    read -p "$(echo -e "${AMARILLO}Introduce el nombre para la nueva imagen (ej. 'mi-app:latest'): ${RESET}")" image_tag
    if [ -z "$image_tag" ]; then
        echo -e "${ROJO}El nombre de la imagen no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Deseas construir la imagen '${image_tag}' desde el contexto '${build_context}'?"; then
        echo -e "${AZUL}Iniciando la construcción de la imagen '${image_tag}'...${RESET}"
        safe_execute "docker build -t $image_tag $build_context"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Imagen '${image_tag}' construida con éxito. ✅${RESET}"
            list_images
        else
            echo -e "${ROJO}Fallo al construir la imagen. Revisa la salida del comando para errores en tu Dockerfile o en el contexto de la construcción. ❌${RESET}"
        fi
    fi
}

# --- FUNCIONES DE GESTIÓN DE CONTENEDORES DOCKER ---
list_containers() {
    print_section_header "Listar Contenedores Docker 📦"
    echo -e "${AMARILLO}Contenedores Activos (en ejecución):${RESET}"
    echo -e "${AZUL}Comando: ${CYAN}docker ps${RESET}"
    safe_execute "docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'"
    echo
    echo -e "${AMARILLO}Todos los Contenedores (incluyendo detenidos, con el tamaño en disco):${RESET}"
    echo -e "${AZUL}Comando: ${CYAN}docker ps -a -s${RESET}"
    safe_execute "docker ps -a -s --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Size}}\t{{.Ports}}'"
    echo -e "${CYAN}Consejo: La columna 'SIZE' muestra el tamaño virtual y el tamaño en disco del contenedor. Los contenedores detenidos aún ocupan espacio.${RESET}"
}

start_container() {
    print_section_header "Iniciar Contenedor Docker ▶️"
    echo "Inicia uno o más contenedores previamente detenidos."
    list_containers # Muestra los contenedores para que el usuario pueda elegir.
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre del contenedor a iniciar: ${RESET}")" container_id
    if [ -z "$container_id" ]; then
        echo -e "${ROJO}El ID/Nombre de contenedor no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Deseas iniciar el contenedor '${container_id}'?"; then
        echo -e "${AZUL}Iniciando contenedor '${container_id}'...${RESET}"
        safe_execute "docker start $container_id"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Contenedor '${container_id}' iniciado con éxito. ✅${RESET}"
            list_containers
        else
            echo -e "${ROJO}Fallo al iniciar el contenedor '${container_id}'. Verifica si existe o su estado. ❌${RESET}"
        fi
    fi
}

stop_container() {
    print_section_header "Detener Contenedor Docker ⏹️"
    echo "Detiene uno o más contenedores en ejecución suavemente. Docker intentará detenerlos en 10 segundos por defecto."
    echo -e "${AMARILLO}Si un contenedor no se detiene después de un tiempo, puedes intentar forzar la detención con 'docker kill <ID>' o 'docker stop <ID> --time 1' si el problema persiste.${RESET}"
    list_containers
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre del contenedor a detener: ${RESET}")" container_id
    if [ -z "$container_id" ]; then
        echo -e "${ROJO}El ID/Nombre de contenedor no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Deseas detener el contenedor '${container_id}'?"; then
        echo -e "${AZUL}Deteniendo contenedor '${container_id}'...${RESET}"
        safe_execute "docker stop $container_id"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Contenedor '${container_id}' detenido con éxito. ✅${RESET}"
            list_containers
        else
            echo -e "${ROJO}Fallo al detener el contenedor '${container_id}'. Asegúrate de que está corriendo. ❌${RESET}"
        fi
    fi
}

remove_container() {
    print_section_header "Eliminar Contenedor Docker 🗑️"
    echo "Elimina un contenedor Docker. Un contenedor debe estar detenido para ser eliminado (a menos que uses '-f')."
    echo -e "${ROJO}¡ADVERTENCIA! Eliminar un contenedor no elimina automáticamente los volúmenes de datos asociados a él. Esos datos persistirán hasta que elimines el volumen explícitamente.${RESET}"
    list_containers
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre del contenedor a eliminar: ${RESET}")" container_id
    if [ -z "$container_id" ]; then
        echo -e "${ROJO}El ID/Nombre de contenedor no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Estás seguro de que quieres eliminar el contenedor '${container_id}'? Esto no se puede deshacer. 🚨💥"; then
        echo -e "${AZUL}Eliminando contenedor '${container_id}'...${RESET}"
        safe_execute "docker rm $container_id"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Contenedor '${container_id}' eliminado con éxito. ✅${RESET}"
            list_containers
        else
            echo -e "${ROJO}Fallo al eliminar el contenedor '${container_id}'. Asegúrate de que esté detenido o usa 'docker rm -f ${container_id}' para forzar la eliminación. ❌${RESET}"
            echo -e "${CYAN}Si el contenedor no se elimina, asegúrate de que esté detenido o usa 'docker rm -f ${container_id}' para forzar (¡esto también detendrá si está en ejecución!).${RESET}"
        fi
    fi
}

restart_container() {
    print_section_header "Reiniciar Contenedor Docker 🔄"
    echo "Detiene y luego inicia un contenedor Docker. Esto es útil para aplicar cambios de configuración o para refrescar el estado de una aplicación."
    list_containers
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre del contenedor a reiniciar: ${RESET}")" container_id
    if [ -z "$container_id" ]; then
        echo -e "${ROJO}El ID/Nombre de contenedor no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Deseas reiniciar el contenedor '${container_id}'?"; then
        echo -e "${AZUL}Reiniciando contenedor '${container_id}'...${RESET}"
        safe_execute "docker restart $container_id"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Contenedor '${container_id}' reiniciado con éxito. ✅${RESET}"
            list_containers
        else
            echo -e "${ROJO}Fallo al reiniciar el contenedor '${container_id}'. Verifica si está corriendo o su estado. ❌${RESET}"
        fi
    fi
}

exec_container() {
    print_section_header "Ejecutar Comando en Contenedor 🚀"
    echo "Ejecuta un comando directamente dentro de un contenedor en ejecución. Esto es extremadamente útil para depuración, instalación de paquetes temporales o inspección de archivos."
    echo -e "${AMARILLO}Para una sesión interactiva (como una shell), usa comandos como 'bash' o 'sh'.${RESET}"
    list_containers
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre del contenedor donde quieres ejecutar el comando: ${RESET}")" container_id
    if [ -z "$container_id" ]; then
        echo -e "${ROJO}El ID/Nombre de contenedor no puede estar vacío. ❌${RESET}"
        return
    fi
    read -p "$(echo -e "${AMARILLO}Introduce el comando a ejecutar dentro del contenedor (ej. bash, sh, ls -l /app, python3 --version): ${RESET}")" command_to_exec
    if [ -z "$command_to_exec" ]; then
        echo -e "${ROJO}El comando no puede estar vacío. ❌${RESET}"
        return
    fi
    echo -e "${AZUL}Ejecutando comando en el contenedor '${container_id}'...${RESET}"
    echo -e "${AMARILLO}Se usará '-it' para una sesión interactiva si el comando lo permite (ej. shell).${RESET}"
    safe_execute "docker exec -it $container_id $command_to_exec"
    echo -e "${CYAN}Si el comando no funciona, el contenedor podría no tener el comando instalado o la ruta es incorrecta.${RESET}"
}

view_container_logs() {
    print_section_header "Ver Logs de Contenedor 📜"
    echo "Muestra los logs de salida estándar (stdout) y de error (stderr) de un contenedor."
    echo "Útil para depurar aplicaciones dentro de los contenedores."
    list_containers
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre del contenedor para ver sus logs: ${RESET}")" container_id
    if [ -z "$container_id" ]; then
        echo -e "${ROJO}El ID/Nombre de contenedor no puede estar vacío. ❌${RESET}"
        return
    fi
    echo -e "${AZUL}Mostrando logs para el contenedor '${container_id}' (últimas 50 líneas por defecto).${RESET}"
    echo -e "${CYAN}Puedes ver los logs en tiempo real con '-f' (follow) o ajustar el número de líneas con '--tail N'.${RESET}"
    safe_execute "docker logs --tail 50 $container_id"
    if [ $? -ne 0 ]; then
        echo -e "${ROJO}Fallo al obtener los logs. Asegúrate de que el contenedor existe. ❌${RESET}"
    fi
    echo -e "${AMARILLO}Para seguir los logs en tiempo real, puedes usar: ${CYAN}docker logs -f $container_id${RESET}"
    echo -e "${AMARILLO}Para ver todos los logs, omite '--tail': ${CYAN}docker logs $container_id${RESET}"
}

inspect_container() {
    print_section_header "Inspeccionar Contenedor Docker 🔍"
    echo "Muestra información detallada de bajo nivel (formato JSON) sobre un contenedor Docker específico."
    echo "Esto incluye su configuración, estado de red, volúmenes montados, procesos, etc."
    list_containers
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre del contenedor a inspeccionar: ${RESET}")" container_id
    if [ -z "$container_id" ]; then
        echo -e "${ROJO}El ID/Nombre de contenedor no puede estar vacío. ❌${RESET}"
        return
    fi
    echo -e "${AZUL}Inspeccionando contenedor '${container_id}'...${RESET}"
    safe_execute "docker inspect $container_id"
    if [ $? -ne 0 ]; then
        echo -e "${ROJO}Fallo al inspeccionar el contenedor. Asegúrate de que el contenedor existe. ❌${RESET}"
    fi
}

# --- FUNCIONES DE GESTIÓN DE REDES DOCKER ---
list_networks() {
    print_section_header "Listar Redes Docker 🌐"
    echo "Muestra todas las redes Docker en tu sistema. Estas redes permiten la comunicación entre contenedores y con el host."
    echo -e "${AZUL}Columnas:${RESET}"
    echo -e "${CYAN}NETWORK ID:${RESET} Identificador único de la red."
    echo -e "${CYAN}NAME:${RESET} Nombre de la red."
    echo -e "${CYAN}DRIVER:${RESET} Driver de la red (bridge, overlay, macvlan, etc.)."
    echo -e "${CYAN}SCOPE:${RESET} Ámbito de la red (local o swarm)."
    safe_execute "docker network ls --format 'table {{.ID}}\t{{.Name}}\t{{.Driver}}\t{{.Scope}}'"
    echo -e "${CYAN}Las redes 'bridge', 'host', 'none' son redes predeterminadas de Docker. Las redes personalizadas ofrecen un mejor aislamiento.${RESET}"
}

create_network() {
    print_section_header "Crear Red Docker ➕"
    echo "Crea una nueva red personalizada para tus contenedores. Esto mejora el aislamiento y la organización de tus servicios Docker."
    echo "Drivers comunes: 'bridge' (por defecto, para un solo host), 'overlay' (para Docker Swarm en múltiples hosts), 'macvlan'."
    read -p "$(echo -e "${AMARILLO}Introduce el nombre de la nueva red: ${RESET}")" network_name
    if [ -z "$network_name" ]; then
        echo -e "${ROJO}El nombre de la red no puede estar vacío. ❌${RESET}"
        return
    fi
    read -p "$(echo -e "${AMARILLO}Introduce el driver de la red (ej. bridge, overlay, macvlan - por defecto 'bridge'): ${RESET}")" network_driver
    network_driver=${network_driver:-bridge} # Asigna 'bridge' si la entrada está vacía.

    local options=""
    if [[ "$network_driver" == "bridge" ]]; then
        if confirm_action "¿Deseas especificar un rango de subred y gateway para la red bridge (avanzado)?"; then
            read -p "$(echo -e "${AMARILLO}Introduce la subred en formato CIDR (ej. 172.20.0.0/16): ${RESET}")" subnet
            read -p "$(echo -e "${AMARILLO}Introduce el gateway (ej. 172.20.0.1): ${RESET}")" gateway
            if [ -n "$subnet" ] && [ -n "$gateway" ]; then
                options="--subnet $subnet --gateway $gateway"
                echo -e "${CYAN}La red se creará con IPAM personalizado.${RESET}"
            else
                echo -e "${AMARILLO}Subred o gateway vacíos, se usará la asignación automática.${RESET}"
            fi
        fi
    fi

    if confirm_action "¿Deseas crear la red '${network_name}' con el driver '${network_driver}' y opciones '${options}'?"; then
        echo -e "${AZUL}Creando red '${network_name}'...${RESET}"
        safe_execute "docker network create --driver $network_driver $options $network_name"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Red '${network_name}' creada con éxito. ✅${RESET}"
            list_networks
        else
            echo -e "${ROJO}Fallo al crear la red '${network_name}'. Verifica el nombre, driver o las opciones. ❌${RESET}"
        fi
    fi
}

remove_network() {
    print_section_header "Eliminar Red Docker 🗑️"
    echo "Elimina una red Docker. Asegúrate de que ningún contenedor esté conectado a ella antes de eliminarla."
    echo -e "${ROJO}ADVERTENCIA: Eliminar una red en uso puede causar que los contenedores conectados pierdan conectividad y fallen. 🚨${RESET}"
    list_networks
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre de la red a eliminar: ${RESET}")" network_id
    if [ -z "$network_id" ]; then
        echo -e "${ROJO}El ID/Nombre de la red no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Estás seguro de que quieres eliminar la red '${network_id}'? Los contenedores conectados a ella podrían perder conectividad. 🚨💥"; then
        echo -e "${AZUL}Eliminando red '${network_id}'...${RESET}"
        safe_execute "docker network rm $network_id"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Red '${network_id}' eliminada con éxito. ✅${RESET}"
            list_networks
        else
            echo -e "${ROJO}Fallo al eliminar la red '${network_id}'. Si la red está en uso, Docker te lo informará. Debes desconectar los contenedores primero. ❌${RESET}"
        fi
    fi
}

inspect_network() {
    print_section_header "Inspeccionar Red Docker 🔍"
    echo "Muestra información detallada de bajo nivel (formato JSON) sobre una red Docker específica."
    echo "Esto incluye su driver, subred, gateway, contenedores conectados y opciones configuradas."
    list_networks
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el ID o nombre de la red a inspeccionar: ${RESET}")" network_id
    if [ -z "$network_id" ]; then
        echo -e "${ROJO}El ID/Nombre de la red no puede estar vacío. ❌${RESET}"
        return
    fi
    echo -e "${AZUL}Inspeccionando red '${network_id}'...${RESET}"
    safe_execute "docker inspect $network_id"
    if [ $? -ne 0 ]; then
        echo -e "${ROJO}Fallo al inspeccionar la red. Asegúrate de que la red existe. ❌${RESET}"
    fi
}

# --- FUNCIONES DE GESTIÓN DE VOLÚMENES DOCKER ---
list_volumes() {
    print_section_header "Listar Volúmenes Docker 💾"
    echo "Muestra todos los volúmenes Docker. Los volúmenes se utilizan para persistir datos generados por los contenedores, desacoplándolos del ciclo de vida del contenedor."
    echo -e "${AZUL}Columnas:${RESET}"
    echo -e "${CYAN}DRIVER:${RESET} Driver del volumen (generalmente 'local')."
    echo -e "${CYAN}VOLUME NAME:${RESET} Nombre del volumen."
    safe_execute "docker volume ls --format 'table {{.Driver}}\t{{.Name}}'"
    echo -e "${CYAN}Consejo: Los volúmenes son ideales para datos importantes que no deben perderse al eliminar un contenedor.${RESET}"
}

create_volume() {
    print_section_header "Crear Volumen Docker ➕"
    echo "Crea un nuevo volumen de datos. Este volumen puede ser montado en uno o varios contenedores para almacenar datos persistentes."
    echo -e "${AMARILLO}Los volúmenes son la forma preferida de gestionar datos persistentes en Docker.${RESET}"
    read -p "$(echo -e "${AMARILLO}Introduce el nombre del nuevo volumen: ${RESET}")" volume_name
    if [ -z "$volume_name" ]; then
        echo -e "${ROJO}El nombre del volumen no puede estar vacío. ❌${RESET}"
        return
    fi
    local driver_options=""
    if confirm_action "¿Deseas especificar un driver de volumen diferente (ej. 'local' con opciones) o configuraciones avanzadas?"; then
        read -p "$(echo -e "${AMARILLO}Introduce el driver del volumen (ej. 'local' o un driver de plugin): ${RESET}")" custom_driver
        if [ -n "$custom_driver" ]; then
            driver_options="--driver $custom_driver"
            read -p "$(echo -e "${AMARILLO}Introduce opciones para el driver (ej. 'o=bind,type=nfs,device=:/path' para NFS): ${RESET}")" volume_options
            if [ -n "$volume_options" ]; then
                driver_options+=" -o $volume_options"
            fi
        fi
    fi
    
    if confirm_action "¿Deseas crear el volumen '${volume_name}' con opciones '${driver_options}'?"; then
        echo -e "${AZUL}Creando volumen '${volume_name}'...${RESET}"
        safe_execute "docker volume create $driver_options $volume_name"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Volumen '${volume_name}' creado con éxito. ✅${RESET}"
            list_volumes
        else
            echo -e "${ROJO}Fallo al crear el volumen '${volume_name}'. Verifica el nombre, driver u opciones. ❌${RESET}"
        fi
    fi
}

remove_volume() {
    print_section_header "Eliminar Volumen Docker 🗑️"
    echo "Elimina un volumen de datos. ¡Esto es una operación destructiva! Los datos almacenados en el volumen se perderán PARA SIEMPRE."
    echo -e "${ROJO}¡ADVERTENCIA CRÍTICA! ASEGÚRATE de que el volumen no contiene datos importantes que necesites. Esta acción es IRREVERSIBLE. 🚨💥${RESET}"
    list_volumes
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el nombre del volumen a eliminar: ${RESET}")" volume_name
    if [ -z "$volume_name" ]; then
        echo -e "${ROJO}El nombre del volumen no puede estar vacío. ❌${RESET}"
        return
    fi
    if confirm_action "¿Estás ABSOLUTAMENTE seguro de que quieres eliminar el volumen '${volume_name}'? ¡Los datos se perderán PERMANENTEMENTE! (escribe 's' para confirmar) 🚨💥"; then
        echo -e "${AZUL}Eliminando volumen '${volume_name}'...${RESET}"
        safe_execute "docker volume rm $volume_name"
        if [ $? -eq 0 ]; then
            echo -e "${VERDE}Volumen '${volume_name}' eliminado con éxito. ✅${RESET}"
            list_volumes
        else
            echo -e "${ROJO}Fallo al eliminar el volumen '${volume_name}'. Si el volumen está en uso por un contenedor, Docker te avisará. Debes detener y eliminar el contenedor primero. ❌${RESET}"
        fi
    fi
}

inspect_volume() {
    print_section_header "Inspeccionar Volumen Docker 🔍"
    echo "Muestra información detallada de bajo nivel (formato JSON) sobre un volumen Docker específico."
    echo "Esto incluye su driver, ruta de montaje en el host, etiquetas y opciones."
    list_volumes
    echo
    read -p "$(echo -e "${AMARILLO}Introduce el nombre del volumen a inspeccionar: ${RESET}")" volume_name
    if [ -z "$volume_name" ]; then
        echo -e "${ROJO}El nombre del volumen no puede estar vacío. ❌${RESET}"
        return
    fi
    echo -e "${AZUL}Inspeccionando volumen '${volume_name}'...${RESET}"
    safe_execute "docker inspect $volume_name"
    if [ $? -ne 0 ]; then
        echo -e "${ROJO}Fallo al inspeccionar el volumen. Asegúrate de que el volumen existe. ❌${RESET}"
    fi
}

# --- Limpieza de Recursos Docker ---
prune_docker() {
    print_section_header "Limpieza de Recursos Docker 🧹"
    echo "Esta sección te ayuda a liberar espacio en disco eliminando recursos Docker no utilizados."
    echo -e "${AMARILLO}¡CUIDADO! Algunas operaciones de limpieza son irreversibles y pueden eliminar datos.${RESET}"
    echo
    echo "1.  Limpiar TODOS los recursos no utilizados (contenedores detenidos, imágenes sin etiqueta o no referenciadas, redes no usadas, volúmenes no usados y caché de build). 🚨 (docker system prune -a --volumes)"
    echo "2.  Limpiar solo contenedores detenidos. (docker container prune)"
    echo "3.  Limpiar solo imágenes no utilizadas (pendientes y sin referencia). (docker image prune -a)"
    echo "4.  Limpiar solo volúmenes no utilizados (¡MUCHO CUIDADO! Esto puede eliminar datos de forma permanente). (docker volume prune)"
    echo "5.  Limpiar solo redes no utilizadas. (docker network prune)"
    echo "0.  Volver al menú anterior."

    read -p "$(echo -e "${AMARILLO}Selecciona una opción de limpieza: ${RESET}")" prune_choice
    echo

    case $prune_choice in
        1)
            if confirm_action "¿Estás ABSOLUTAMENTE seguro de que quieres limpiar TODOS los recursos Docker no utilizados, incluyendo volúmenes (docker system prune -a --volumes)? Esto es irreversible y eliminará muchos datos no usados. 🚨💥"; then
                echo -e "${AZUL}Ejecutando limpieza total...${RESET}"
                safe_execute "docker system prune -a --volumes"
                echo -e "${VERDE}Limpieza total de Docker completada. ✅${RESET}"
            fi
            ;;
        2)
            if confirm_action "¿Deseas limpiar solo contenedores detenidos? (docker container prune) (No se eliminarán los datos asociados a los volúmenes)"; then
                echo -e "${AZUL}Limpiando contenedores detenidos...${RESET}"
                safe_execute "docker container prune"
                echo -e "${VERDE}Contenedores detenidos limpiados. ✅${RESET}"
            fi
            ;;
        3)
            if confirm_action "¿Deseas limpiar solo imágenes no utilizadas? (docker image prune -a) (Imágenes sin etiquetas y sin referencia por contenedores)"; then
                echo -e "${AZUL}Limpiando imágenes no utilizadas...${RESET}"
                safe_execute "docker image prune -a" # '-a' para todas las imágenes no usadas (incluye dangling y no referenciadas)
                echo -e "${VERDE}Imágenes no utilizadas limpiadas. ✅${RESET}"
            fi
            ;;
        4)
            if confirm_action "¿Deseas limpiar solo volúmenes no utilizados? ${ROJO}¡ADVERTENCIA: Esto puede eliminar datos IMPORTANTES y es IRREVERSIBLE! (docker volume prune) ${RESET}"; then
                echo -e "${AZUL}Limpiando volúmenes no utilizados...${RESET}"
                safe_execute "docker volume prune"
                echo -e "${VERDE}Volúmenes no utilizados limpiados. ✅${RESET}"
            fi
            ;;
        5)
            if confirm_action "¿Deseas limpiar solo redes no utilizadas? (docker network prune)"; then
                echo -e "${AZUL}Limpiando redes no utilizadas...${RESET}"
                safe_execute "docker network prune"
                echo -e "${VERDE}Redes no utilizadas limpiadas. ✅${RESET}"
            fi
            ;;
        0)
            echo -e "${AZUL}Volviendo al menú de gestión principal. ✅${RESET}"
            ;;
        *)
            echo -e "${ROJO}Opción inválida. Por favor, selecciona un número del menú. 😕${RESET}"
            ;;
    esac
}

# --- Información y Diagnóstico del Sistema Docker ---
docker_version() {
    print_section_header "Versión de Docker 🏷️"
    echo "Muestra información de la versión del cliente (CLI) y del servidor (Daemon) Docker."
    echo -e "${CYAN}Cliente: Versión de la interfaz de línea de comandos de Docker.${RESET}"
    echo -e "${CYAN}Servidor: Versión del motor Docker que gestiona los contenedores.${RESET}"
    safe_execute "docker version"
}

docker_info() {
    print_section_header "Información del Sistema Docker Detallada 🔬"
    echo "Muestra información detallada sobre la instalación de Docker, almacenamiento, redes, contenedores en ejecución, estadísticas del host, etc."
    echo -e "${CYAN}Útil para el diagnóstico de problemas a nivel de sistema Docker y para entender la configuración actual.${RESET}"
    safe_execute "docker info"
}

view_docker_logs() {
    print_section_header "Ver Logs del Daemon Docker 📜"
    echo "Muestra los logs del servicio Docker (el daemon que gestiona contenedores, imágenes, etc.)."
    echo "Estos logs son cruciales para depurar problemas de inicio del servicio, errores de red o fallos inesperados."
    echo -e "${AZUL}Mostrando las últimas 100 líneas de los logs del daemon Docker (usando systemd journal, si está disponible):${RESET}"
    # '--since' muestra logs desde un período de tiempo. '--no-pager' evita el paginador.
    # 'tail -n 100' asegura que solo se muestren las últimas 100 líneas.
    safe_execute "journalctl -u docker.service --since '1 hour ago' --no-pager | tail -n 100"
    if [ $? -ne 0 ]; then
        echo -e "${ROJO}No se pudieron obtener los logs del servicio Docker. Asegúrate de que systemd está en uso y que tienes permisos. ❌${RESET}"
    fi
    echo -e "${AMARILLO}Para seguir los logs en tiempo real, usa: ${CYAN}journalctl -u docker.service -f${RESET}"
    echo -e "${AMARILLO}Para ver logs desde el inicio del sistema: ${CYAN}journalctl -u docker.service --boot${RESET}"
}

view_docker_events() {
    print_section_header "Ver Eventos de Docker en Tiempo Real 📡"
    echo "Muestra un flujo continuo de eventos del daemon Docker en tiempo real (creación/inicio/detención de contenedores, descarga de imágenes, etc.)."
    echo -e "${AMARILLO}Presiona ${ROJO}Ctrl+C${AMARILLO} para detener la visualización de eventos.${RESET}"
    echo -e "${AZUL}Iniciando el monitoreo de eventos de Docker...${RESET}"
    safe_execute "docker events"
    if [ $? -ne 0 ]; then
        echo -e "${ROJO}Fallo al iniciar el monitoreo de eventos. Asegúrate de que el servicio Docker está corriendo. ❌${RESET}"
    fi
}

docker_system_df() {
    print_section_header "Espacio en Disco Usado por Docker 📊"
    echo "Muestra el uso de espacio en disco de las imágenes, contenedores, volúmenes y caché de buildkit de Docker."
    echo -e "${CYAN}Esto es útil para identificar dónde se está consumiendo más espacio en tu sistema Docker.${RESET}"
    safe_execute "docker system df"
}

# --- Configuración del Daemon Docker (daemon.json) ---
manage_daemon_config() {
    print_section_header "Gestionar Configuración del Daemon Docker (daemon.json) ⚙️"
    echo "Este menú te permite ver y modificar el archivo de configuración clave del daemon Docker, daemon.json."
    echo -e "${ROJO}¡ADVERTENCIA! Cambios incorrectos en daemon.json pueden impedir que Docker se inicie. Siempre haz una copia de seguridad.${RESET}"
    echo "El archivo se encuentra en: ${CYAN}${DOCKER_DAEMON_JSON_FILE}${RESET}"
    echo

    if [ ! -d "$DOCKER_DAEMON_CONFIG_DIR" ]; then
        echo -e "${AMARILLO}El directorio de configuración del daemon '${DOCKER_DAEMON_CONFIG_DIR}' no existe. Creándolo...${RESET}"
        safe_execute "mkdir -p $DOCKER_DAEMON_CONFIG_DIR" || { echo -e "${ROJO}No se pudo crear el directorio de configuración. Permisos? ❌${RESET}"; return; }
    fi

    local current_config=""
    if [ -f "$DOCKER_DAEMON_JSON_FILE" ]; then
        current_config=$(cat "$DOCKER_DAEMON_JSON_FILE")
        echo -e "${AZUL}Contenido actual de ${DOCKER_DAEMON_JSON_FILE}: ${RESET}"
        echo -e "${CYAN}${current_config}${RESET}"
    else
        echo -e "${AMARILLO}El archivo ${DOCKER_DAEMON_JSON_FILE} no existe. Se creará si eliges editarlo o añadir configuraciones.${RESET}"
    fi
    echo

    echo "1.  Ver contenido actual de daemon.json."
    echo "2.  Editar daemon.json manualmente (abrirá un editor de texto). 📝"
    echo "3.  Añadir/Modificar una configuración específica (ej. 'data-root', 'log-driver')."
    echo "4.  Eliminar una configuración específica."
    echo "5.  Reiniciar Docker para aplicar cambios."
    echo "0.  Volver al menú principal."

    read -p "$(echo -e "${AMARILLO}Selecciona una opción de configuración del daemon: ${RESET}")" daemon_choice
    echo

    case $daemon_choice in
        1)
            if [ -f "$DOCKER_DAEMON_JSON_FILE" ]; then
                echo -e "${AZUL}Contenido de ${DOCKER_DAEMON_JSON_FILE}: ${RESET}"
                safe_execute "cat $DOCKER_DAEMON_JSON_FILE"
            else
                echo -e "${AMARILLO}El archivo ${DOCKER_DAEMON_JSON_FILE} no existe. ${RESET}"
            fi
            ;;
        2)
            if confirm_action "¿Deseas editar daemon.json? Se abrirá nano. ¡Guarda y cierra para aplicar!"; then
                # Crear copia de seguridad antes de editar.
                local BACKUP_FILE="${DOCKER_DAEMON_JSON_FILE}.bak.$(date +%Y%m%d%H%M%S)"
                if [ -f "$DOCKER_DAEMON_JSON_FILE" ]; then
                    safe_execute "cp $DOCKER_DAEMON_JSON_FILE $BACKUP_FILE"
                    if [ $? -eq 0 ]; then
                        echo -e "${VERDE}Copia de seguridad creada: ${BACKUP_FILE} ✅${RESET}"
                    else
                        echo -e "${ROJO}No se pudo crear la copia de seguridad. Procediendo con la edición sin copia. ❌${RESET}"
                    fi
                else
                    echo -e "${AMARILLO}El archivo no existe, se creará. No se requiere copia de seguridad.${RESET}"
                fi

                # Abrir el editor. 'nano' es común y fácil de usar.
                safe_execute "nano $DOCKER_DAEMON_JSON_FILE"
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Edición de daemon.json completada. ✅${RESET}"
                    echo -e "${AMARILLO}¡Recuerda reiniciar el servicio Docker para aplicar los cambios!${RESET}"
                else
                    echo -e "${ROJO}El editor terminó con un error. Revisa el archivo manualmente. ❌${RESET}"
                fi
            fi
            ;;
        3)
            echo "Puedes añadir o modificar una clave-valor en el JSON."
            echo "Ejemplos: 'data-root' '/mnt/docker-data', 'log-driver' 'json-file', 'registry-mirrors' '[\"https://my.mirror.com\"]'"
            read -p "$(echo -e "${AMARILLO}Introduce la clave (ej. 'data-root'): ${RESET}")" json_key
            read -p "$(echo -e "${AMARILLO}Introduce el valor (ej. '/var/lib/docker-new' o '[\"https://my.mirror.com\"]'): ${RESET}")" json_value
            if [ -z "$json_key" ] || [ -z "$json_value" ]; then
                echo -e "${ROJO}Clave o valor no pueden estar vacíos. ❌${RESET}"
                return
            fi
            if confirm_action "¿Deseas añadir/modificar '${json_key}' con valor '${json_value}' en daemon.json?"; then
                local BACKUP_FILE="${DOCKER_DAEMON_JSON_FILE}.bak.$(date +%Y%m%d%H%M%S)"
                if [ -f "$DOCKER_DAEMON_JSON_FILE" ]; then
                    safe_execute "cp $DOCKER_DAEMON_JSON_FILE $BACKUP_FILE"
                    echo -e "${VERDE}Copia de seguridad creada: ${BACKUP_FILE} ✅${RESET}"
                fi
                
                # Usar jq para modificar/añadir la clave. Instalar jq si no está.
                if ! command -v jq &>/dev/null; then
                    echo -e "${AMARILLO}La herramienta 'jq' no está instalada. Es necesaria para modificar JSON automáticamente. Instalándola...${RESET}"
                    local distro=$(get_distribution)
                    if [[ "$distro" == "debian" || "$distro" == "ubuntu" ]]; then
                        safe_execute "apt install -y jq"
                    elif [[ "$distro" == "fedora" || "$distro" == "centos" || "$distro" == "rhel" ]]; then
                        safe_execute "dnf install -y jq"
                    else
                        echo -e "${ROJO}No se puede instalar 'jq' automáticamente para esta distribución. Por favor, instálalo manualmente. ❌${RESET}"
                        return
                    fi
                fi

                if [ ! -f "$DOCKER_DAEMON_JSON_FILE" ]; then
                    # Si el archivo no existe, crearlo con un JSON vacío.
                    echo "{}" | safe_execute "tee $DOCKER_DAEMON_JSON_FILE" >/dev/null
                fi

                # Intentar añadir/modificar usando jq.
                # Si el valor es un array JSON (empieza con '['), jq lo tratará como tal.
                # Si no, lo tratará como string.
                if [[ "$json_value" == \[*\] ]]; then
                    safe_execute "jq --arg key \"$json_key\" --argjson value \"$json_value\" '.[$key] = $value' $DOCKER_DAEMON_JSON_FILE > temp_daemon.json && mv temp_daemon.json $DOCKER_DAEMON_JSON_FILE"
                else
                    safe_execute "jq --arg key \"$json_key\" --arg value \"$json_value\" '.[$key] = $value' $DOCKER_DAEMON_JSON_FILE > temp_daemon.json && mv temp_daemon.json $DOCKER_DAEMON_JSON_FILE"
                fi

                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Configuración de daemon.json actualizada. ✅${RESET}"
                    echo -e "${AMARILLO}¡Reinicia el servicio Docker para que los cambios surtan efecto!${RESET}"
                else
                    echo -e "${ROJO}Fallo al actualizar daemon.json. Revisa el formato de la clave/valor y el archivo. ❌${RESET}"
                    # Revertir desde la copia de seguridad si hubo fallo y se hizo copia.
                    if [ -f "$BACKUP_FILE" ]; then
                        echo -e "${AMARILLO}Intentando restaurar la copia de seguridad...${RESET}"
                        safe_execute "mv $BACKUP_FILE $DOCKER_DAEMON_JSON_FILE"
                        echo -e "${VERDE}Copia de seguridad restaurada. ✅${RESET}"
                    fi
                fi
            fi
            ;;
        4)
            echo "Puedes eliminar una clave específica de daemon.json."
            read -p "$(echo -e "${AMARILLO}Introduce la clave a eliminar (ej. 'data-root'): ${RESET}")" json_key_to_delete
            if [ -z "$json_key_to_delete" ]; then
                echo -e "${ROJO}La clave no puede estar vacía. ❌${RESET}"
                return
            fi
            if confirm_action "¿Deseas eliminar la clave '${json_key_to_delete}' de daemon.json?"; then
                local BACKUP_FILE="${DOCKER_DAEMON_JSON_FILE}.bak.$(date +%Y%m%d%H%M%S)"
                if [ -f "$DOCKER_DAEMON_JSON_FILE" ]; then
                    safe_execute "cp $DOCKER_DAEMON_JSON_FILE $BACKUP_FILE"
                    echo -e "${VERDE}Copia de seguridad creada: ${BACKUP_FILE} ✅${RESET}"
                else
                    echo -e "${AMARILLO}El archivo daemon.json no existe. Nada que eliminar.${RESET}"
                    return
                fi
                
                if ! command -v jq &>/dev/null; then
                    echo -e "${ROJO}La herramienta 'jq' no está instalada y es necesaria. Por favor, instálala manualmente. ❌${RESET}"
                    return
                fi

                safe_execute "jq 'del(.\"$json_key_to_delete\")' $DOCKER_DAEMON_JSON_FILE > temp_daemon.json && mv temp_daemon.json $DOCKER_DAEMON_JSON_FILE"
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Clave '${json_key_to_delete}' eliminada de daemon.json. ✅${RESET}"
                    echo -e "${AMARILLO}¡Reinicia el servicio Docker para que los cambios surtan efecto!${RESET}"
                else
                    echo -e "${ROJO}Fallo al eliminar la clave de daemon.json. Revisa si la clave existe. ❌${RESET}"
                    if [ -f "$BACKUP_FILE" ]; then
                        echo -e "${AMARILLO}Intentando restaurar la copia de seguridad...${RESET}"
                        safe_execute "mv $BACKUP_FILE $DOCKER_DAEMON_JSON_FILE"
                        echo -e "${VERDE}Copia de seguridad restaurada. ✅${RESET}"
                    fi
                fi
            fi
            ;;
        5)
            restart_docker # Llama a la función de reinicio del servicio Docker.
            ;;
        0)
            echo -e "${AZUL}Volviendo al menú de gestión principal. ✅${RESET}"
            ;;
        *)
            echo -e "${ROJO}Opción inválida. Por favor, selecciona un número del menú. 😕${RESET}"
            ;;
    esac
}

# --- Actualización y Desinstalación de Docker ---
update_docker() {
    print_section_header "Actualizar Docker ⬆️"
    echo "Actualizar Docker generalmente implica usar el gestor de paquetes de tu sistema para obtener las últimas versiones de los componentes de Docker CE."
    echo -e "${AMARILLO}Se recomienda reiniciar el servicio Docker después de una actualización para asegurar que los nuevos binarios se carguen. 🔄${RESET}"
    local distro=$(get_distribution)
    case "$distro" in
        "debian" | "ubuntu")
            echo -e "${AZUL}Se actualizará Docker utilizando APT.${RESET}"
            if confirm_action "¿Deseas actualizar Docker CE (Engine, CLI, containerd, plugins) ahora?"; then
                echo -e "${AZUL}Ejecutando 'apt update && apt upgrade'...${RESET}"
                safe_execute "apt update && apt upgrade -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Docker se ha actualizado (posiblemente). ✅${RESET}"
                    if confirm_action "¿Deseas reiniciar el servicio Docker ahora para aplicar los cambios?"; then
                        restart_docker # Llama a la función de reinicio.
                    fi
                else
                    echo -e "${ROJO}Fallo al actualizar Docker. Revisa los mensajes de error. ❌${RESET}"
                fi
            fi
            ;;
        "fedora" | "centos" | "rhel" | "almalinux" | "rocky")
            echo -e "${AZUL}Se actualizará Docker utilizando DNF.${RESET}"
            if confirm_action "¿Deseas actualizar Docker CE (Engine, CLI, containerd, plugins) ahora?"; then
                echo -e "${AZUL}Ejecutando 'dnf update'...${RESET}"
                safe_execute "dnf update -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Docker se ha actualizado (posiblemente). ✅${RESET}"
                    if confirm_action "¿Deseas reiniciar el servicio Docker ahora para aplicar los cambios?"; then
                        restart_docker # Llama a la función de reinicio.
                    fi
                else
                    echo -e "${ROJO}Fallo al actualizar Docker. Revisa los mensajes de error. ❌${RESET}"
                fi
            fi
            ;;
        *)
            echo -e "${ROJO}Tu distribución ('$distro') no es compatible con la actualización automatizada a través de este script. 😞${RESET}"
            echo -e "${AMARILLO}Consulta la documentación oficial de Docker para tu distribución para los pasos de actualización manual.${RESET}"
            ;;
    esac
}

uninstall_docker() {
    print_section_header "Desinstalar Docker Completamente 🗑️"
    echo -e "${ROJO}¡ADVERTENCIA CRÍTICA! Esta operación es DESTRUCTIVA e IRREVERSIBLE.${RESET}"
    echo "Eliminará Docker Engine, CLI, containerd, y ${ROJO}todos tus contenedores, imágenes, volúmenes y redes Docker por defecto${RESET}."
    echo "Asegúrate de haber hecho copias de seguridad de cualquier dato importante en tus volúmenes antes de proceder."
    echo
    if confirm_action "¿Estás ABSOLUTAMENTE SEGURO de que quieres DESINSTALAR Docker y eliminar todos sus datos (incluyendo contenedores, imágenes y volúmenes)? (escribe 's' para confirmar) 🚨💥"; then
        echo -e "${AMARILLO}Paso previo opcional: Limpiando todos los recursos Docker antes de desinstalar para una limpieza más completa.${RESET}"
        if confirm_action "¿Deseas ejecutar 'docker system prune -a --volumes' (limpieza total) ahora como precaución antes de desinstalar?"; then
            prune_docker # Invoca la función de limpieza que ofrece opciones
            echo -e "${AZUL}Continuando con la desinstalación de Docker...${RESET}"
        else
            echo -e "${AMARILLO}Saltando la limpieza de recursos previa. Ten en cuenta que podrían quedar más remanentes.${RESET}"
        fi

        local distro=$(get_distribution)
        case "$distro" in
            "debian" | "ubuntu")
                echo -e "${AZUL}Deteniendo el servicio Docker...${RESET}"
                safe_execute "systemctl stop docker"
                echo -e "${AZUL}Desinstalando paquetes principales de Docker (docker-ce, docker-ce-cli, containerd.io, plugins)...${RESET}"
                safe_execute "apt purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
                echo -e "${AZUL}Eliminando directorios de datos y configuración residuales (/var/lib/docker, /etc/docker, /var/lib/containerd)...${RESET}"
                safe_execute "rm -rf /var/lib/docker"
                safe_execute "rm -rf /etc/docker"
                safe_execute "rm -rf /var/lib/containerd"
                echo -e "${AZUL}Eliminando archivos de repositorio y claves GPG de Docker...${RESET}"
                safe_execute "rm -f /etc/apt/sources.list.d/docker.list"
                safe_execute "rm -f /etc/apt/keyrings/docker.gpg"
                echo -e "${AZUL}Limpiando paquetes residuales y dependencias no usadas...${RESET}"
                safe_execute "apt autoremove -y"
                safe_execute "apt clean"
                ;;
            "fedora" | "centos" | "rhel" | "almalinux" | "rocky")
                echo -e "${AZUL}Deteniendo el servicio Docker...${RESET}"
                safe_execute "systemctl stop docker"
                echo -e "${AZUL}Desinstalando paquetes principales de Docker...${RESET}"
                safe_execute "dnf remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
                echo -e "${AZUL}Eliminando directorios de datos y configuración residuales (/var/lib/docker, /etc/docker, /var/lib/containerd)...${RESET}"
                safe_execute "rm -rf /var/lib/docker"
                safe_execute "rm -rf /etc/docker"
                safe_execute "rm -rf /var/lib/containerd"
                echo -e "${AZUL}Eliminando archivos de repositorio de Docker...${RESET}"
                safe_execute "rm -f /etc/yum.repos.d/docker-ce.repo"
                ;;
            *)
                echo -e "${ROJO}Tu distribución ('$distro') no es compatible con la desinstalación automatizada a través de este script. 😞${RESET}"
                echo -e "${AMARILLO}Consulta la documentación oficial de Docker para tu distribución para los pasos de desinstalación manual.${RESET}"
                ;;
        esac
        echo -e "${VERDE}Desinstalación de Docker completada (o al menos sus componentes principales). ✅${RESET}"
        echo -e "${AMARILLO}Se recomienda ${ROJO}reiniciar tu sistema${AMARILLO} para una limpieza completa de cualquier componente en memoria o archivos bloqueados y para remover cualquier dependencia residual de Docker. 🔄${RESET}"
    fi
}

# --- Gestión de Docker Compose (Standalone, no plugin) ---
install_docker_compose_standalone() {
    print_section_header "Instalar Docker Compose (Standalone) 📦"
    echo "Docker Compose ahora viene como un plugin CLI con la mayoría de las instalaciones modernas de Docker CE (se usa el comando 'docker compose' con espacio)."
    echo "Esta opción es para instalar la versión binaria standalone (generalmente escrita en Python) de Docker Compose ('docker-compose' con guion)."
    echo "Versión de Docker Compose Standalone a instalar: ${CYAN}${DOCKER_COMPOSE_VERSION}${RESET}"
    echo -e "${AMARILLO}Considera usar el plugin 'docker compose' si ya está disponible en tu instalación de Docker CE.${RESET}"

    local compose_type=$(detect_docker_compose_type)
    if [ "$compose_type" = "plugin" ]; then
        echo -e "${VERDE}Ya tienes 'docker compose' (plugin) disponible. Es la forma recomendada de usar Compose. ✅${RESET}"
        if ! confirm_action "¿Aún así quieres instalar la versión standalone (${DOCKER_COMPOSE_VERSION})? Esto podría crear un comando 'docker-compose' adicional.${RESET}"; then
            return # El usuario ha cancelado la instalación.
        fi
    elif [ "$compose_type" = "standalone" ]; then
        local installed_version=$("$DOCKER_COMPOSE_DEST" version --short 2>/dev/null)
        echo -e "${VERDE}Docker Compose (standalone) ya está instalado. Versión actual: ${CYAN}${installed_version}${VERDE}. ✅${RESET}"
        if [ "$installed_version" == "${DOCKER_COMPOSE_VERSION}" ]; then
            echo -e "${VERDE}Ya tienes la versión ${DOCKER_COMPOSE_VERSION} instalada. No es necesario reinstalar. ${RESET}"
            return # Salir, no hay nada que hacer.
        elif ! confirm_action "¿Quieres actualizar/reinstalar Docker Compose a la versión ${DOCKER_COMPOSE_VERSION}?"; then
            return # El usuario ha cancelado la actualización.
        fi
    fi

    if confirm_action "¿Proceder con la descarga e instalación de Docker Compose Standalone (${DOCKER_COMPOSE_VERSION})?"; then
        echo -e "${AZUL}Descargando Docker Compose desde GitHub...${RESET}"
        safe_execute "curl -L ${DOCKER_COMPOSE_URL} -o ${DOCKER_COMPOSE_DEST}" || { echo -e "${ROJO}Fallo al descargar Docker Compose. Verifica la URL y tu conexión. ${RESET}"; return 1; }
        
        echo -e "${AZUL}Dando permisos de ejecución al binario...${RESET}"
        safe_execute "chmod +x ${DOCKER_COMPOSE_DEST}" || { echo -e "${ROJO}Fallo al establecer permisos de ejecución.${RESET}"; return 1; }

        echo -e "${VERDE}Docker Compose (standalone) instalado correctamente en '${DOCKER_COMPOSE_DEST}'. ✅${RESET}"
        echo -e "${CYAN}Puedes verificar la instalación con: ${VERDE}docker-compose --version${RESET}"
        echo -e "${AMARILLO}Recuerda que para Docker Compose moderno, la mayoría de los comandos se ejecutan con 'docker compose' (con espacio).${RESET}"
    fi
}

manage_docker_compose_project() {
    print_section_header "Gestión Básica de Proyectos Docker Compose 🏗️"
    local compose_cmd # Variable para almacenar el comando correcto de Docker Compose.
    local compose_type=$(detect_docker_compose_type)

    if [ "$compose_type" = "plugin" ]; then
        compose_cmd="docker compose" # Usa el plugin.
        echo -e "${VERDE}Usando el plugin Docker Compose (comando: '${CYAN}docker compose${VERDE}'). ✅${RESET}"
    elif [ "$compose_type" = "standalone" ]; then
        compose_cmd="docker-compose" # Usa la versión standalone.
        echo -e "${VERDE}Usando la versión standalone de Docker Compose (comando: '${CYAN}docker-compose${VERDE}'). ✅${RESET}"
    else
        echo -e "${ROJO}Docker Compose no está instalado. Por favor, instálalo primero desde la opción anterior. ❌${RESET}"
        return # Sale de la función si Compose no está disponible.
    fi

    echo "Este submenú te permite realizar acciones básicas en tus proyectos de Docker Compose."
    echo -e "${AMARILLO}¡IMPORTANTE! Debes ejecutar estas acciones ${ROJO}desde el directorio donde se encuentra tu archivo ${CYAN}docker-compose.yml${AMARILLO} (o .yaml).${RESET}"
    echo "Si no estás en el directorio correcto, los comandos pueden fallar o no encontrar tus servicios."
    echo "Tu directorio actual es: ${CYAN}$(pwd)${RESET}"
    echo
    echo "1.  Levantar servicios (construir, crear, iniciar - en segundo plano: ${CYAN}$compose_cmd up -d${RESET})"
    echo "2.  Detener y eliminar servicios (contenedores, redes - ${CYAN}$compose_cmd down${RESET})"
    echo "3.  Listar servicios de un proyecto (estado de contenedores: ${CYAN}$compose_cmd ps${RESET})"
    echo "4.  Ver logs de todos los servicios de un proyecto (${CYAN}$compose_cmd logs${RESET})"
    echo "5.  Construir/Reconstruir imágenes (sin levantar servicios: ${CYAN}$compose_cmd build${RESET})"
    echo "6.  Ejecutar un comando en un servicio (ej. ${CYAN}$compose_cmd exec web bash${RESET})"
    echo "0.  Volver al menú anterior"

    read -p "$(echo -e "${AMARILLO}Selecciona una opción de Docker Compose: ${RESET}")" dc_choice
    echo

    case $dc_choice in
        1)
            if confirm_action "¿Deseas levantar los servicios definidos en docker-compose.yml (en modo detached -d)?"; then
                echo -e "${AZUL}Levantando servicios Docker Compose...${RESET}"
                safe_execute "$compose_cmd up -d"
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Servicios levantados con éxito. ✅${RESET}"
                else
                    echo -e "${ROJO}Fallo al levantar los servicios. Revisa la salida para depurar tu archivo docker-compose.yml. ❌${RESET}"
                fi
            fi
            ;;
        2)
            if confirm_action "¿Deseas detener y eliminar los servicios, redes, etc. definidos en docker-compose.yml? ${ROJO}Esto detendrá y removerá tus contenedores.${RESET}"; then
                echo -e "${AZUL}Deteniendo y eliminando servicios Docker Compose...${RESET}"
                safe_execute "$compose_cmd down"
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Servicios detenidos y eliminados con éxito. ✅${RESET}"
                else
                    echo -e "${ROJO}Fallo al detener los servicios. ❌${RESET}"
                fi
            fi
            ;;
        3)
            echo -e "${AZUL}Listando servicios del proyecto Docker Compose...${RESET}"
            safe_execute "$compose_cmd ps"
            ;;
        4)
            echo -e "${AZUL}Mostrando logs de todos los servicios del proyecto Docker Compose...${RESET}"
            safe_execute "$compose_cmd logs"
            echo -e "${AMARILLO}Para seguir los logs en tiempo real, usa: ${CYAN}$compose_cmd logs -f${RESET}"
            ;;
        5)
            if confirm_action "¿Deseas construir/reconstruir las imágenes definidas en docker-compose.yml?"; then
                echo -e "${AZUL}Construyendo imágenes Docker Compose...${RESET}"
                safe_execute "$compose_cmd build"
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}Imágenes construidas con éxito. ✅${RESET}"
                else
                    echo -e "${ROJO}Fallo al construir las imágenes. Revisa tu Dockerfile o docker-compose.yml. ❌${RESET}"
                fi
            fi
            ;;
        6)
            echo "Ejecuta un comando dentro de un servicio específico de tu proyecto Docker Compose."
            read -p "$(echo -e "${AMARILLO}Introduce el nombre del servicio (ej. 'web', 'db'): ${RESET}")" service_name
            read -p "$(echo -e "${AMARILLO}Introduce el comando a ejecutar (ej. 'bash', 'ls -l /app', 'python3 manage.py shell'): ${RESET}")" command_in_service
            if [ -z "$service_name" ] || [ -z "$command_in_service" ]; then
                echo -e "${ROJO}El nombre del servicio o el comando no pueden estar vacíos. ❌${RESET}"
                return
            fi
            echo -e "${AZUL}Ejecutando comando en el servicio '${service_name}'...${RESET}"
            safe_execute "$compose_cmd exec $service_name $command_in_service"
            ;;
        0)
            echo -e "${AZUL}Volviendo al menú de gestión principal. ✅${RESET}"
            ;;
        *)
            echo -e "${ROJO}Opción inválida. Por favor, selecciona un número del menú. 😕${RESET}"
            ;;
    esac
}

# --- MENÚS PRINCIPALES Y LÓGICA DE FLUJO ---

# Muestra el menú de opciones de instalación de Docker.
show_docker_install_menu() {
    print_section_header "Menú de Instalación de Docker ⚙️"
    local distro=$(get_distribution)
    echo "Tu sistema operativo detectado es: ${CYAN}$distro${RESET}"
    echo -e "${AMARILLO}Selecciona la opción de instalación que mejor se adapte a tu distribución.${RESET}"
    echo
    echo "1.  Instalar Docker en ${CYAN}Debian/Ubuntu${RESET} (Recomendado para tu sistema Osiris si es Debian) 🐧"
    echo "2.  Instalar Docker en ${CYAN}Fedora/CentOS/RHEL/AlmaLinux/RockyLinux${RESET} (Para otros sistemas basados en Red Hat) 🔶"
    echo "3.  Instalación Genérica de Docker (Script de conveniencia - ${ROJO}usar con precaución${RESET}) 🌐"
    echo "0.  Volver al menú principal / Salir del asistente"
    echo
    read -p "$(echo -e "${AMARILLO}Selecciona una opción de instalación (0-3): ${RESET}")" choice
    echo

    case $choice in
        1) install_docker_debian ;;
        2) install_docker_fedora ;;
        3) install_docker_generic ;;
        0)
            echo -e "${AZUL}¡Adiós! 👋 Esperamos que vuelvas cuando estés listo para Docker. ${RESET}"
            exit 0
            ;;
        *)
            echo -e "${ROJO}Opción inválida. Por favor, selecciona un número válido del menú. 😕${RESET}"
            ;;
    esac
}

# Muestra el menú principal de gestión de Docker.
show_docker_management_menu() {
    print_section_header "Menú de Gestión de Docker 🐳"
    echo -e "${CYAN}Aquí puedes gestionar todos los aspectos de tu entorno Docker. ¡Explora con confianza!${RESET}"
    echo
    echo "1.  Gestionar ${MAGENTA}Servicio Docker${RESET} (Iniciar/Detener/Reiniciar/Estado/Configuración de Inicio) 🛠️"
    echo "2.  Gestionar ${MAGENTA}Imágenes Docker${RESET} (Listar/Descargar/Eliminar/Inspeccionar/Construir) 🖼️"
    echo "3.  Gestionar ${MAGENTA}Contenedores Docker${RESET} (Listar/Iniciar/Detener/Eliminar/Logs/Comando/Inspeccionar) 📦"
    echo "4.  Gestionar ${MAGENTA}Redes Docker${RESET} (Listar/Crear/Eliminar/Inspeccionar) 🌐"
    echo "5.  Gestionar ${MAGENTA}Volúmenes Docker${RESET} (Listar/Crear/Eliminar/Inspeccionar) 💾"
    echo "6.  ${MAGENTA}Limpiar Recursos Docker${RESET} (Contenedores/Imágenes/Volúmenes/Redes no usados) 🧹"
    echo "7.  ${MAGENTA}Información y Diagnóstico${RESET} del Sistema Docker (Versión/Info/Logs del Daemon/Eventos/Uso Disco) ℹ️"
    echo "8.  ${MAGENTA}Configuración Avanzada del Daemon Docker${RESET} (Editar daemon.json) ⚙️"
    echo "9.  ${MAGENTA}Añadir usuario actual al grupo 'docker'${RESET} 👥"
    echo "10. ${MAGENTA}Actualizar Docker${RESET} ⬆️"
    echo "11. ${MAGENTA}Desinstalar Docker${RESET} completamente 🗑️"
    echo "12. Gestionar ${MAGENTA}Docker Compose${RESET} (Instalar Standalone / Acciones Básicas de Proyecto) 🏗️"
    echo "0.  ${ROJO}Salir del asistente${RESET}"
    echo
    read -p "$(echo -e "${AMARILLO}Selecciona una opción de gestión (0-12): ${RESET}")" choice
    echo

    case $choice in
        1)
            print_section_header "Submenú: Gestión de Servicio Docker 🛠️"
            echo "1.  Ver estado del servicio"
            echo "2.  Iniciar servicio"
            echo "3.  Detener servicio"
            echo "4.  Reiniciar servicio"
            echo "5.  Habilitar inicio al arrancar el sistema"
            echo "6.  Deshabilitar inicio al arrancar el sistema"
            echo "0.  Volver al menú principal"
            read -p "$(echo -e "${AMARILLO}Selecciona una opción de servicio (0-6): ${RESET}")" service_choice
            echo
            case $service_choice in
                1) check_docker_status ;;
                2) start_docker ;;
                3) stop_docker ;;
                4) restart_docker ;;
                5) enable_docker_on_boot ;;
                6) disable_docker_on_boot ;;
                0) ;; # Regresa al menú principal
                *) echo -e "${ROJO}Opción inválida. 😕${RESET}" ;;
            esac
            ;;
        2)
            print_section_header "Submenú: Gestión de Imágenes Docker 🖼️"
            echo "1.  Listar imágenes disponibles"
            echo "2.  Descargar una imagen (pull)"
            echo "3.  Eliminar una imagen"
            echo "4.  Inspeccionar una imagen (ver detalles)"
            echo "5.  Construir una imagen desde un Dockerfile"
            echo "0.  Volver al menú principal"
            read -p "$(echo -e "${AMARILLO}Selecciona una opción de imagen (0-5): ${RESET}")" image_choice
            echo
            case $image_choice in
                1) list_images ;;
                2) pull_image ;;
                3) remove_image ;;
                4) inspect_image ;;
                5) build_image ;;
                0) ;;
                *) echo -e "${ROJO}Opción inválida. 😕${RESET}" ;;
            esac
            ;;
        3)
            print_section_header "Submenú: Gestión de Contenedores Docker 📦"
            echo "1.  Listar contenedores (activos y todos)"
            echo "2.  Iniciar un contenedor detenido"
            echo "3.  Detener un contenedor en ejecución"
            echo "4.  Reiniciar un contenedor"
            echo "5.  Eliminar un contenedor"
            echo "6.  Ver logs de un contenedor"
            echo "7.  Ejecutar un comando dentro de un contenedor"
            echo "8.  Inspeccionar un contenedor (ver detalles)"
            echo "0.  Volver al menú principal"
            read -p "$(echo -e "${AMARILLO}Selecciona una opción de contenedor (0-8): ${RESET}")" container_choice
            echo
            case $container_choice in
                1) list_containers ;;
                2) start_container ;;
                3) stop_container ;;
                4) restart_container ;;
                5) remove_container ;;
                6) view_container_logs ;;
                7) exec_container ;;
                8) inspect_container ;;
                0) ;;
                *) echo -e "${ROJO}Opción inválida. 😕${RESET}" ;;
            esac
            ;;
        4)
            print_section_header "Submenú: Gestión de Redes Docker 🌐"
            echo "1.  Listar redes existentes"
            echo "2.  Crear una nueva red"
            echo "3.  Eliminar una red"
            echo "4.  Inspeccionar una red (ver detalles)"
            echo "0.  Volver al menú principal"
            read -p "$(echo -e "${AMARILLO}Selecciona una opción de red (0-4): ${RESET}")" network_choice
            echo
            case $network_choice in
                1) list_networks ;;
                2) create_network ;;
                3) remove_network ;;
                4) inspect_network ;;
                0) ;;
                *) echo -e "${ROJO}Opción inválida. 😕${RESET}" ;;
            esac
            ;;
        5)
            print_section_header "Submenú: Gestión de Volúmenes Docker 💾"
            echo "1.  Listar volúmenes existentes"
            echo "2.  Crear un nuevo volumen"
            echo "3.  Eliminar un volumen (¡CUIDADO con la pérdida de datos!)"
            echo "4.  Inspeccionar un volumen (ver detalles)"
            echo "0.  Volver al menú principal"
            read -p "$(echo -e "${AMARILLO}Selecciona una opción de volumen (0-4): ${RESET}")" volume_choice
            echo
            case $volume_choice in
                1) list_volumes ;;
                2) create_volume ;;
                3) remove_volume ;;
                4) inspect_volume ;;
                0) ;;
                *) echo -e "${ROJO}Opción inválida. 😕${RESET}" ;;
            esac
            ;;
        6) prune_docker ;;
        7)
            print_section_header "Submenú: Información y Diagnóstico de Docker ℹ️"
            echo "1.  Ver versión de Docker (cliente y servidor)"
            echo "2.  Ver información detallada del sistema Docker (docker info)"
            echo "3.  Ver logs del daemon Docker (para depuración)"
            echo "4.  Ver eventos de Docker en tiempo real"
            echo "5.  Ver uso de espacio en disco por Docker (docker system df)"
            echo "0.  Volver al menú principal"
            read -p "$(echo -e "${AMARILLO}Selecciona una opción de información (0-5): ${RESET}")" info_choice
            echo
            case $info_choice in
                1) docker_version ;;
                2) docker_info ;;
                3) view_docker_logs ;;
                4) view_docker_events ;;
                5) docker_system_df ;;
                0) ;;
                *) echo -e "${ROJO}Opción inválida. 😕${RESET}" ;;
            esac
            ;;
        8) manage_daemon_config ;;
        9) add_user_to_docker_group ;;
        10) update_docker ;;
        11) uninstall_docker ;;
        12)
            print_section_header "Submenú: Gestión de Docker Compose 🏗️"
            echo "1.  Instalar Docker Compose (versión standalone si no es plugin)"
            echo "2.  Gestión básica de proyectos Docker Compose (up, down, ps, logs, build, exec)"
            echo "0.  Volver al menú principal"
            read -p "$(echo -e "${AMARILLO}Selecciona una opción de Docker Compose (0-2): ${RESET}")" compose_choice
            echo
            case $compose_choice in
                1) install_docker_compose_standalone ;;
                2) manage_docker_compose_project ;;
                0) ;;
                *) echo -e "${ROJO}Opción inválida. 😕${RESET}" ;;
            esac
            ;;
        0)
            echo -e "${AZUL}¡Adiós! 👋 Espero que este asistente de Osiris haya sido de gran ayuda. ¡Hasta la próxima! ${RESET}"
            exit 0
            ;;
        *)
            echo -e "${ROJO}Opción inválida. Por favor, selecciona un número válido del menú. 😕${RESET}"
            ;;
    esac
}

# --- LÓGICA PRINCIPAL DEL SCRIPT ---
main_logic() {
    check_sudo # Asegura que el script se ejecuta con sudo al principio.
    echo -e "${AZUL}¡Bienvenido al gestor inteligente de Docker de Osiris! 🐳✨${RESET}"
    echo -e "${AZUL}Este asistente te guiará para instalar o gestionar Docker en tu sistema.${RESET}"
    echo -e "${AZUL}Idioma: Español${RESET}"
    echo

    # Bucle principal del programa. Continúa hasta que el usuario elija salir.
    while true; do
        if ! is_docker_installed; then
            # Si Docker NO está instalado, muestra el menú de instalación.
            echo -e "${AMARILLO}--- Docker NO está instalado en este sistema. Ofreciendo opciones de instalación. --- 😔${RESET}"
            show_docker_install_menu
        else
            # Si Docker YA está instalado, muestra el menú de gestión.
            echo -e "${VERDE}--- Docker YA está instalado y funcionando. ¡Excelente! Ofreciendo opciones de gestión. --- 🎉${RESET}"
            show_docker_management_menu
        fi
        echo
        echo -e "${CYAN}Presiona Enter para volver al menú principal...${RESET}"
        read -s # Espera por cualquier tecla sin mostrarla para continuar.
        echo
    done
}

# Iniciar la lógica principal del script cuando se ejecuta.
main_logic