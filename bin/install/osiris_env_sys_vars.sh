#!/usr/bin/bash
echo "Este script establece las variables del entorno global"
echo "  Virtual environment G-Osiris"
VENV_NAME="osiris_env"

VERSION="osiris2"

# Variables de entorno (usa comillas dobles en todos los valores)
export OSIRIS000_VENV_PYTHONPATH="/var/${VERSION}/bin/com/osiris_env/lib/python3.11/site-packages"
export OSIRIS000_BIN="/var/${VERSION}/bin"
export OSIRIS000_BASEPATH="/var/${VERSION}"
export OSIRIS000_VENV_NAME="${VENV_NAME}"
export OSIRIS000_VENV_PATH="/var/${VERSION}/bin/com/osiris_env"
export VENV_ACTIVATE_PATH="/var/${VERSION}/bin/com/osiris_env/bin/activate"
export AME_VENV="${VENV_NAME}"
export OSIRIS_PUBLIC_WWW_DIR="/var/${VERSION}/html/app/freedirectory/osiris"

#echo $AME_VENV


# Asegúrate de que las variables estén correctamente definidas antes de ejecutar
if ! grep -q "OSIRIS000_VENV_PYTHONPATH" /etc/environment; then
    echo "OSIRIS000_VENV_PYTHONPATH=\"${OSIRIS000_VENV_PYTHONPATH}\"" | sudo tee -a /etc/environment > /dev/null
fi

if ! grep -q "OSIRIS000_BIN" /etc/environment; then
    echo "OSIRIS000_BIN=\"${OSIRIS000_BIN}\"" | sudo tee -a /etc/environment > /dev/null
fi

if ! grep -q "OSIRIS000_BASEPATH" /etc/environment; then
    echo "OSIRIS000_BASEPATH=\"${OSIRIS000_BASEPATH}\"" | sudo tee -a /etc/environment > /dev/null
fi

if ! grep -q "OSIRIS000_VENV_NAME" /etc/environment; then
    echo "OSIRIS000_VENV_NAME=\"${OSIRIS000_VENV_NAME}\"" | sudo tee -a /etc/environment > /dev/null
fi

if ! grep -q "OSIRIS000_VENV_PATH" /etc/environment; then
    echo "OSIRIS000_VENV_PATH=\"${OSIRIS000_VENV_PATH}\"" | sudo tee -a /etc/environment > /dev/null
fi

if ! grep -q "VENV_ACTIVATE_PATH" /etc/environment; then
    echo "VENV_ACTIVATE_PATH=\"${VENV_ACTIVATE_PATH}\"" | sudo tee -a /etc/environment > /dev/null
fi

if ! grep -q "AME_VENV" /etc/environment; then
    echo "AME_VENV=\"${AME_VENV}\"" | sudo tee -a /etc/environment > /dev/null
fi

if ! grep -q "OSIRIS_PUBLIC_WWW_DIR" /etc/environment; then
    echo "OSIRIS_PUBLIC_WWW_DIR=\"${OSIRIS_PUBLIC_WWW_DIR}\"" | sudo tee -a /etc/environment > /dev/null
fi

echo "Variables de entorno configuradas."

cat /etc/environment

# Recargar variables de entorno (opcional, ya que se exportan arriba)
source /etc/environment


