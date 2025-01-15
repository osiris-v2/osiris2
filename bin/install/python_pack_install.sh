#!/bin/bash

# Script para instalar Python 3.11, venv, y las dependencias de pip
source /etc/environment
# Asegurarse de que las variables de entorno están definidas
if [ -z "$OSIRIS000_VENV_PATH" ] || [ -z "$OSIRIS000_VENV_NAME" ]; then
    echo "Las variables de entorno OSIRIS000_VENV_PATH y OSIRIS000_VENV_NAME deben estar definidas."
    exit 1
fi


# Variables
PYTHON_VERSION="3.11"
PIP_DEP_FILE="${OSIRIS000_BIN}/install/pip_dep"

# Crear el directorio para el entorno virtual si no existe
mkdir -p "$OSIRIS000_VENV_PATH"

# Actualizar la lista de paquetes e instalar dependencias iniciales
echo "Actualizando lista de paquetes..."
sudo apt-get update

# Instalar Python 3.11, venv, y pip
echo "Instalando Python ${PYTHON_VERSION}, venv, y pip..."
sudo apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip

# Verificar la instalación
echo "Verificando las versiones instaladas..."
python${PYTHON_VERSION} --version

# Crear el entorno virtual en la ruta y nombre especificados
VENV_DIR="${OSIRIS000_VENV_PATH}/${OSIRIS000_VENV_NAME}"
echo "Creando un entorno virtual en ${VENV_DIR}..."
python${PYTHON_VERSION} -m venv "$VENV_DIR"

# Activar el entorno virtual
echo "Activando el entorno virtual..."
source "${VENV_DIR}/bin/activate"

# Asegurarse de que pip está instalado en el entorno virtual
if [ ! -f "${VENV_DIR}/bin/pip" ]; then
    echo "pip no encontrado en el entorno virtual. Intentando instalar pip con apt-get..."
    
    # Intentar instalar pip usando apt-get
    sudo apt-get install -y python3-pip

    # Verificar si la instalación con apt-get funcionó
    if [ ! -f "${VENV_DIR}/bin/pip" ]; then
        echo "pip no se pudo instalar con apt-get. Intentando instalar pip manualmente..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python get-pip.py
        rm get-pip.py
    fi
else
    echo "pip ya está instalado."
fi

# Asegurarse de que pip está actualizado
echo "Actualizando pip en el entorno virtual..."
pip install --upgrade pip

# Instalar dependencias desde el archivo pip_dep
if [ -f "$PIP_DEP_FILE" ]; then
    echo "Instalando dependencias desde $PIP_DEP_FILE..."
    
    # Leer el archivo de dependencias y instalar cada línea, ignorando líneas en blanco y comentarios
    while IFS= read -r line; do
        if [[ ! -z "$line" && ! "$line" =~ ^# ]]; then
            pip install "$line"
        fi
    done < "$PIP_DEP_FILE"
else
    echo "Archivo de dependencias $PIP_DEP_FILE no encontrado."
fi

# Confirmar que las dependencias se instalaron
echo "Dependencias instaladas. Para usar el entorno virtual, ejecute 'source ${VENV_DIR}/bin/activate'."

# Finalizar
echo "Instalación completa."
