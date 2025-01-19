#!/bin/bash

script_dir=$(dirname "$(readlink -f "$0")")
cd $script_dir
#nos situamos en raiz
cd ../..


# Variables
TARGET_DIR="html/app/mitv/channels/main"
LIVE_DIR="$TARGET_DIR/live-ts"
HTACCESS_FILE="$TARGET_DIR/.htaccess"
HTACCESS_CONTENT='
# Directivas para servir archivos HLS (m3u8)
AddType application/x-mpegURL .m3u8
AddType video/MP2T .ts
'

# Función para preguntar al usuario
ask_question() {
  read -r -p "$1" answer
  echo "$answer" | tr '[:upper:]' '[:lower:]'
}

# Verificar si el directorio existe
if [ ! -d "$TARGET_DIR" ]; then
  read -r -p "El directorio $TARGET_DIR no existe. ¿Desea crearlo? (s/n): " create_dir
  create_dir=$(echo "$create_dir" | tr '[:upper:]' '[:lower:]')
  if [ "$create_dir" != "s" ]; then
    echo "Operación cancelada."
    exit 1
  fi
  mkdir -p "$TARGET_DIR"
  echo "Directorio $TARGET_DIR creado."
fi

# se crea live dir si no existe

mkdir -p  $LIVE_DIR 
chmod 0777 $LIVE_DIR

# Verificar si el archivo .htaccess existe
if [ -f "$HTACCESS_FILE" ]; then
  read -r -p "El archivo $HTACCESS_FILE ya existe. ¿Desea sobreescribirlo? (s/n): " overwrite_file
  overwrite_file=$(echo "$overwrite_file" | tr '[:upper:]' '[:lower:]')
  if [ "$overwrite_file" != "s" ]; then
    echo "Operación cancelada."
    exit 1
  fi
  echo "$HTACCESS_CONTENT" > "$HTACCESS_FILE"
  echo "Archivo $HTACCESS_FILE sobreescrito con las directivas HLS."
else
  echo "$HTACCESS_CONTENT" > "$HTACCESS_FILE"
  echo "Archivo $HTACCESS_FILE creado con las directivas HLS."
fi

echo "Proceso completado."
