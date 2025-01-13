#!/usr/bin/bash
source /etc/environment
echo "Este script activa el directorio virtual"

# Asegurarse de que las variables de entorno están definidas
if [ -z "$OSIRIS000_VENV_PATH" ] || [ -z "$OSIRIS000_VENV_NAME" ]; then
    echo "Las variables de entorno OSIRIS000_VENV_PATH y OSIRIS000_VENV_NAME deben estar definidas."
    echo "Se va a Ejecutar osiris_env_sys_vars.sh para establecer las variables de entorno "
    . ./bin/install/osiris_env_sys_vars.sh
    exit 1
fi

# Comprobar si el entorno virtual ya está creado
if [ ! -d "$OSIRIS000_VENV_PATH" ]; then
    echo "Creando entorno virtual en $OSIRIS000_VENV_PATH"
    python3 -m venv $OSIRIS000_VENV_PATH
fi

echo "Activando directorio virtual en: ${OSIRIS000_VENV_PATH}"

# Verificar que VENV_ACTIVATE_PATH esté definida correctamente
if [ -z "$VENV_ACTIVATE_PATH" ]; then
    echo "VENV_ACTIVATE_PATH no está definida."
    exit 1
fi

# Comprobar si el archivo de activación existe
if [ ! -f "$VENV_ACTIVATE_PATH" ]; then
    echo "El archivo de activación no existe: $VENV_ACTIVATE_PATH"
    exit 1
fi

# Activar el entorno virtual
echo "Activando entorno virtual en: $VENV_ACTIVATE_PATH"
source $VENV_ACTIVATE_PATH

# La ruta que deseas agregar
NUEVA_RUTA=$OSIRIS000_VENV_PYTHONPATH

# Verificar si la ruta ya está en PYTHONPATH, si no, agregarla
if [[ ":$PYTHONPATH:" != *":$NUEVA_RUTA:"* ]]; then
    export PYTHONPATH="$PYTHONPATH:$NUEVA_RUTA"
fi

# Mostrar la variable VIRTUAL_ENV y PYTHONPATH
echo "Entorno virtual activado: $VIRTUAL_ENV"
echo "PYTHONPATH: $PYTHONPATH"
