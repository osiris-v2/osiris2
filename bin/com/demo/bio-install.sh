#!/bin/bash

contains_element () {
    local e match="$1"
    shift
    for e; do [[ "$e" == "$match" ]] && return 0; done
    return 1
}

script_dir=$(dirname "$(readlink -f "$0")")
cd $script_dir
# Script para descargar, verificar dependencias e ejecutar un script Python desde una URL.
# --- Configuración ---
# URL del script Python en GitHub
verified_dev_requeriments="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/osiris_env/osiris.pip.requeriments" 
verified_dev_requeriments="/var/osiris2/bin/com/osiris_env/bio.pip.requeriments" # entorno virtual de desarrollo base por defecto /var/osiris2/...
BIO_DIR=$script_dir
cd $BIO_DIR
echo " --- VHOST VENV --- "
sudo python3 -m venv $BIO_DIR/venv
sudo chmod -R 0777 $BIO_DIR/venv
source $BIO_DIR/venv/bin/activate
#VRF=A5wqwAaXdcsdr454rt576Y7ua
#inspect VRF
# Archivo temporal para guardar el script descargado
# mktemp crea un nombre de archivo temporal único y seguro
TEMP_SCRIPT="$BIO_DIR/tmp/beta-tmp-file-init.01.py"
# Lista de paquetes Python necesarios (usar los nombres que usa pip)
REQUIRED_PACKAGES=("")


while IFS= read -r LINEA;
 do

if ! printf "%s\n" "${REQUIRED_PACKAGES=[@]}" | grep -q -x -F -- "$LINEA"; then 
REQUIRED_PACKAGES+=("$LINEA"); echo "Añadido '$LINEA'."; 
else echo "'$LINEA' ya existe."; 
fi

 done < $verified_dev_requeriments



# Comando Python a usar (se recomienda python3 para compatibilidad con las libs)

PYTHON_CMD="python3"
# Comando pip a usar (asociado a python3)
PIP_CMD="pip"

# --- Funciones de Utilidad ---

# Función para limpiar el archivo temporal al salir
cleanup() {
    echo "--- Limpiando archivo temporal: $TEMP_SCRIPT ---"
    # -f: ignora si el archivo no existe
    rm -f "$TEMP_SCRIPT"
    echo "--- Limpieza completada ---"
}

# Registrar la función cleanup para que se ejecute al salir del script (normal o por error/señal)
#trap cleanup EXIT

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

dl() {
if ! curl -fsSL "$1" -o "$2"; then
    echo "Error: No se pudo descargar el script Python desde la URL especificada." >&2 # Imprime a stderr
    echo "Por favor, verifica la URL y tu conexión a internet."
    exit 1 # Sale del script con un código de error
fi
echo "--- Script descargado exitosamente a $2 ---"
}

dl1="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/demo/walletav.py"
dl1a="$BIO_DIR/o3wallet"

dl $dl1 $dl1a
sudo chmod +x $dl1a

dl2="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/dsk/dskl"
dl2a="$BIO_DIR/o2launcher"

dl $dl2  $dl2a
sudo chmod +x $dl2a

dl3="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/dsk/dskcfg"
dl3a="$BIO_DIR/o3config"

dl $dl3  $dl3a
sudo chmod +x $dl3a

dl4="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/dsk/dskv"
dl4a="$BIO_DIR/o3video"

dl $dl4  $dl4a
sudo chmod +x $dl4a


dl5="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/demo/aplicaciones.json"
dl5a="$BIO_DIR/aplicaciones.json"

dl $dl5  $dl5a
#sudo chmod +x $dl5a


dl6="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/OPS/win"
dl6a="$BIO_DIR/o3window"

dl $dl6  $dl6a
sudo chmod +x $dl6a


dl7="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/demo/o2doc.py"
dl7a="$BIO_DIR/o3documentation.py"

dl $dl7  $dl7a
sudo chmod +x $dl7a


dl8="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/dsk/dskvu"
dl8a="$BIO_DIR/dskvu"

dl $dl8  $dl8a
sudo chmod +x $dl8a


dl9="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/dsk/dskvc"
dl9a="$BIO_DIR/o3transcoder"

dl $dl9  $dl9a
sudo chmod +x $dl9a


dl10="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/dsk/dskvdl"
dl10a="$BIO_DIR/o3downloader"

dl $dl10  $dl10a
sudo chmod +x $dl10a


dl11="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/audio.py"
dl11a="$BIO_DIR/o3audio"

dl $dl11  $dl11a
sudo chmod +x $dl11a



dl12W="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/o2config.py"
dl12aW="$BIO_DIR/o3config"

dl $dl12W  $dl12aW
sudo chmod +x $dl12aW




dl12="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/processbck2.py"
dl12a="$BIO_DIR/o3blockchain"

dl $dl12  $dl12a
sudo chmod +x $dl12a


dl13="https://raw.githubusercontent.com/osiris-v2/osiris2/refs/heads/master/bin/com/o2ws2.py"
dl13a="$BIO_DIR/o3servers"

dl $dl13  $dl13a
sudo chmod +x $dl13a



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
ef() {
if "$1" "$@" & then
  # Script launched in the background successfully.  No further action needed here.
  :  # Null command (does nothing).  Keeps the "if" block syntactically valid.
else
  echo "===================================="
  echo "Error: Failed to launch script." >&2
  exit 1
fi
}
#exec file
#ef $dl3a
ef $dl2a

echo "===================================================="
echo "--- Ejecución del script Python completada ---"

# El 'trap cleanup EXIT' se encargará de la limpieza al salir.

echo "===================================================="
echo " Fin: Proceso completado.                          "
echo "===================================================="





