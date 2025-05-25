#!/bin/bash

# Variables
VERSION="latest" # Puedes cambiar a una versión específica
ARCHITECTURE=$(dpkg --print-architecture)
PACKAGE_NAME="sublime-text"
DOWNLOAD_URL="https://download.sublimetext.com"
TEMP_DIR="/tmp"
PACKAGE_FILE="${TEMP_DIR}/sublime-text_${VERSION}_${ARCHITECTURE}.deb"

# Función para mostrar errores y salir
error_exit() {
  echo "❌ Error: $1" >&2
  exit 1
}

# Verificar si wget está instalado
if ! command -v wget &> /dev/null; then
  echo "ℹ️  wget no está instalado. Intentando instalar..."
  apt update && apt install -y wget
  if [ $? -ne 0 ]; then
    error_exit "wget no se pudo instalar.  Por favor, instálalo manualmente."
  fi
fi

# Descargar la llave GPG de Sublime Text
echo "🔑 Descargando llave GPG..."
wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | gpg --dearmor > sublimehq-pub.gpg
mv sublimehq-pub.gpg /etc/apt/trusted.gpg.d/
if [ $? -ne 0 ]; then
  error_exit "No se pudo importar la llave GPG. Verifica los permisos y la conexión a internet."
fi

# Añadir el repositorio de Sublime Text
echo "➕ Añadiendo repositorio de Sublime Text..."
echo "deb https://download.sublimetext.com/ apt/stable/" | tee /etc/apt/sources.list.d/sublime-text.list
if [ $? -ne 0 ]; then
  error_exit "No se pudo añadir el repositorio.  Verifica los permisos."
fi

# Actualizar la lista de paquetes
echo "🔄 Actualizando lista de paquetes..."
apt update
if [ $? -ne 0 ]; then
  error_exit "No se pudo actualizar la lista de paquetes."
fi

# Instalar Sublime Text
echo "📦 Instalando Sublime Text..."
apt install sublime-text
if [ $? -ne 0 ]; then
  error_exit "No se pudo instalar Sublime Text."
fi

echo "✅ Sublime Text instalado correctamente.  ¡Disfrútalo! 🎉"