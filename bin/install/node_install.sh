#!/bin/bash
echo "Node.js Installer"

# Verificar si la variable OSIRIS000_VENV_PATH está definida y tiene valor
if [ -z "$OSIRIS000_VENV_PATH" ]; then
  echo "Error: La variable OSIRIS000_VENV_PATH no está definida o está vacía. Aborting."
  exit 1
else
  echo "Directorio base para la instalación de NODE: $OSIRIS000_VENV_PATH"
fi

# Definir el directorio base para la instalación
install_dir="$OSIRIS000_VENV_PATH/software/node"
bin_dir="$install_dir/bin"

# Función para detectar el sistema operativo y la arquitectura
function detect_system_architecture() {
  uname_out="$(uname -s)"
  case "${uname_out}" in
      Linux*)     os=linux;;
      Darwin*)    os=darwin;;
      CYGWIN*|MINGW*) os=win;;
      *)          os="UNKNOWN:${uname_out}"
  esac

  architecture=$(uname -m)
  case "${architecture}" in
      x86_64)    arch=x64;;
      aarch64)   arch=arm64;;
      armv7l)    arch=armv7l;;
      *)         arch="UNKNOWN:${architecture}"
  esac

  echo "$os-$arch"
}

# Función para preguntar al usuario
function prompt_user() {
  while true; do
    read -p "$1 [y/n]: " yn
    case $yn in
        [Yy]* ) return 0;;
        [Nn]* ) return 1;;
        * ) echo "Por favor responda 'y' para sí o 'n' para no.";;
    esac
  done
}

# Función para agregar binarios al PATH si no están ya incluidos
function add_to_path() {
  profile_file="$HOME/.bashrc"  # Cambia esto según tu shell (por ejemplo, .zshrc para Zsh)

  if ! grep -q "$bin_dir" "$profile_file"; then
    echo "Agregando $bin_dir a PATH en $profile_file"
    echo "export PATH=\$PATH:$bin_dir" >> "$profile_file"
    export PATH="$PATH:$bin_dir"
    echo "Recargando el perfil del shell..."
    source "$profile_file"
    echo "El PATH ha sido actualizado."
  else
    echo "$bin_dir ya está en el PATH."
  fi
}

# Función para instalar o actualizar Node.js
function nodejs_install_or_update() {
  # Obtener la última versión disponible
  latest_version=$(curl -s https://nodejs.org/dist/latest/ | grep -oP '(?<=v)\d+(\.\d+)+' | head -n 1)

  # Verificar la versión instalada en el directorio específico
  if [ -f "$bin_dir/node" ]; then
    current_version=$("$bin_dir/node" -v 2>/dev/null | cut -d'v' -f2)
  else
    current_version=""
  fi

  # Detectar sistema operativo y arquitectura
  system_architecture=$(detect_system_architecture)

  if [[ $system_architecture == "UNKNOWN"* ]]; then
    echo "Sistema operativo o arquitectura no soportados: $system_architecture"
    exit 1
  fi

  # Nombre del archivo a descargar
  node_filename="node-v$latest_version-$system_architecture.tar.gz"
  node_url="https://nodejs.org/dist/latest/$node_filename"

  # Si Node.js no está instalado o está desactualizado
  if [ -z "$current_version" ] || [ "$current_version" != "$latest_version" ]; then
    if [ -z "$current_version" ]; then
      echo "Node.js no está instalado en $install_dir."
      if prompt_user "¿Desea instalar la última versión ($latest_version) en $install_dir?"; then
        echo "Instalando Node.js versión $latest_version en $install_dir..."
      else
        echo "Instalación cancelada."
        exit 0
      fi
    else
      echo "Node.js está desactualizado en $install_dir (versión actual: $current_version)."
      if prompt_user "¿Desea actualizar a la versión $latest_version en $install_dir?"; then
        echo "Actualizando Node.js a la versión $latest_version en $install_dir..."
      else
        echo "Actualización cancelada."
        exit 0
      fi
    fi

    # Crear el directorio de instalación si no existe
    mkdir -p "$install_dir"

    # Descargar y descomprimir Node.js
    curl -O $node_url
    tar -xzf $node_filename

    # Instalar Node.js en el directorio especificado
    cp -r node-v$latest_version-$system_architecture/* "$install_dir/"

    # Crear archivo de registro de instalación
    echo "Node.js versión $latest_version instalado en $install_dir." > "$install_dir/node.install"

    # Limpiar
    rm -rf node-v$latest_version-$system_architecture
    rm $node_filename

    echo "Node.js ha sido instalado/actualizado a la versión $latest_version en $install_dir."

    # Agregar el directorio de binarios al PATH y recargar el shell
    add_to_path
  else
    echo "Node.js ya está actualizado a la última versión ($current_version) en $install_dir."
    # Asegurarse de que el directorio de binarios esté en el PATH
    add_to_path
  fi
}

# Ejecutar la función
nodejs_install_or_update
