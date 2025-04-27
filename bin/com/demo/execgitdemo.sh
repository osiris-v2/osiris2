#!/bin/bash

# Script para descargar, verificar dependencias e ejecutar un script Python desde una URL.

# --- Configuración ---
# URL del script Python en GitHub
PYTHON_SCRIPT_URL="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/demo/walletav.py"

BIO_DIR="$HOME/osiris2/bio"

mkdir -p $BIO_DIR/tmp
chmod 0777 $BIO_DIR
echo " VHOST VENV "
pip3 install virtualenv
python3 -m venv $BIO_DIR/venv
source $BIO_DIR/venv/bin/activate


# Archivo temporal para guardar el script descargado
# mktemp crea un nombre de archivo temporal único y seguro
TEMP_SCRIPT=$(mktemp $BIO_DIR/tmp/beta-tmp-file-init.01.py)
# Lista de paquetes Python necesarios (usar los nombres que usa pip)
REQUIRED_PACKAGES=("cryptography" "PyQt5" "qrcode" "pillow")
# Comando Python a usar (se recomienda python3 para compatibilidad con las libs)
PYTHON_CMD="python3"
# Comando pip a usar (asociado a python3)
PIP_CMD="pip3"

# --- Funciones de Utilidad ---

# Función para limpiar el archivo temporal al salir
cleanup() {
    echo "--- Limpiando archivo temporal: $TEMP_SCRIPT ---"
    # -f: ignora si el archivo no existe
    rm -f "$TEMP_SCRIPT"
    echo "--- Limpieza completada ---"
}

# Registrar la función cleanup para que se ejecute al salir del script (normal o por error/señal)
trap cleanup EXIT

# --- Flujo Principal ---

echo "===================================================="
echo "  Inicio: Descarga y Ejecución de Script Python    "
echo "===================================================="

# 1. Descargar el script Python
echo "--- Descargando script de: $PYTHON_SCRIPT_URL ---"
# curl opciones:
# -f: Fail fast, no output on HTTP errors like 404
# -s: Silent mode (no progress meter)
# -S: Show error when -s is used
# -L: Follow redirects
# -o: Output to specified file
if ! curl -fsSL "$PYTHON_SCRIPT_URL" -o "$TEMP_SCRIPT"; then
    echo "Error: No se pudo descargar el script Python desde la URL especificada." >&2 # Imprime a stderr
    echo "Por favor, verifica la URL y tu conexión a internet."
    exit 1 # Sale del script con un código de error
fi

echo "--- Script descargado exitosamente a $TEMP_SCRIPT ---"

# 2. Verificar e instalar dependencias
echo "--- Verificando dependencias Python: ${REQUIRED_PACKAGES[@]} ---"
MISSING_PACKAGES=()
for package in "${REQUIRED_PACKAGES[@]}"; do
    # Intentar importar el paquete usando el comando Python
    # Redirige la salida estándar (stdout) y de error (stderr) a /dev/null
    # para que no se vea la salida del import o posibles errores internos del módulo si está mal instalado
    if ! "$PYTHON_CMD" -c "import $package" &>/dev/null; then
        echo "Paquete necesario no encontrado: $package"
        MISSING_PACKAGES+=("$package") # Añade a la lista de paquetes faltantes
    else
        echo "Paquete encontrado: $package"
    fi
done

# Si hay paquetes faltantes, intentar instalarlos
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "--- Intentando instalar paquetes faltantes... ---"
    # Añadir el flag --user para intentar instalar en el directorio del usuario si no hay permisos globales
    # O puedes usar sudo si estás seguro de que es necesario y permitido: sudo "$PIP_CMD" install "${MISSING_PACKAGES[@]}"
    if "$PIP_CMD" install  "${MISSING_PACKAGES[@]}"; then
        echo "--- Paquetes instalados exitosamente (posiblemente en el directorio del usuario) ---"
        # Opcional: Re-verificar después de instalar (útil si --user instaló correctamente)
        # for package in "${MISSING_PACKAGES[@]}"; do
        #     if ! "$PYTHON_CMD" -c "import $package" &>/dev/null; then
        #         echo "Advertencia: El paquete '$package' aún no se puede importar después de la instalación." >&2
        #     fi
        # done
    else
        echo "Error: No se pudieron instalar uno o más paquetes necesarios." >&2
        echo "Por favor, intenta instalar manualmente con: $PIP_CMD install ${MISSING_PACKAGES[@]} "
        echo "O contacta a un administrador si necesitas instalar globalmente."
        exit 1 # Sale del script si la instalación falla
    fi
else
    echo "--- Todas las dependencias ya están instaladas. ---"
fi

# 3. Ejecutar el script Python descargado
echo "--- Ejecutando el script Python descargado ---"
echo "===================================================="

# Ejecuta el script temporal, pasando todos los argumentos recibidos por este script bash ("$@")
# "$@" asegura que los argumentos con espacios se pasen correctamente
if ! "$PYTHON_CMD" "$TEMP_SCRIPT" "$@"; then
    echo "===================================================="
    echo "Error: La ejecución del script Python falló." >&2
    exit 1 # Sale del script si la ejecución falla
fi

echo "===================================================="
echo "--- Ejecución del script Python completada ---"

# El 'trap cleanup EXIT' se encargará de la limpieza al salir.

echo "===================================================="
echo " Fin: Proceso completado.                          "
echo "===================================================="
