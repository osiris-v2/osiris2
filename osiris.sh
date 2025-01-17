#!/bin/bash


script_dir=$(dirname "$(readlink -f "$0")")

cd $script_dir

if [ "$(id -u)" -eq 0 ]; then
    echo "El usuario es root. Continuando con el script."
else
    echo "Este script debe ejecutarse como root para continuar."

    # Obtener la ruta del directorio actual
    current_directory=$(pwd)

    # Intentar cambiar al usuario root con el comando "su"
    su -c "cd $current_directory; exec bash ./osiris.sh"

    # Comprobar si se pudo cambiar a root exitosamente
    if [ "$(id -u)" -eq 0 ]; then
        echo "Ahora eres root. Continuando con el script."
    else
        ./osiris.sh
        exit 1
    fi
fi


# Continuar con el resto del script aquí...

source share.sh
source install.sh
#continue
echo "SDP: ${script_dir}"
python_osiris_index_file="osiris.py"
cd bin
python3 "$python_osiris_index_file"
