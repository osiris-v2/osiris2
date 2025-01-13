#!/bin/bash
echo "Terminator Installer"

# Verificar si la variable OSIRIS000_VENV_PATH está definida y tiene valor
if [ -z "$OSIRIS000_VENV_PATH" ]; then
  echo "Error: La variable OSIRIS000_VENV_PATH no está definida o está vacía. Aborting."
  exit 
else
  echo "Directorio base para la instalación de Terminator: $OSIRIS000_VENV_PATH"
fi

# Definir el directorio base para la instalación
install_dir="$OSIRIS000_VENV_PATH/software/terminator"
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

# Función para instalar o actualizar Terminator
function terminator_install_or_update() {
  # Comprobar si Terminator está instalado
  if command -v terminator &> /dev/null; then
    current_version=$(terminator --version | grep -oP '\d+\.\d+(\.\d+)?')
  else
    current_version=""
  fi

  # Detectar sistema operativo y arquitectura
  system_architecture=$(detect_system_architecture)

  if [[ $system_architecture == "UNKNOWN"* ]]; then
    echo "Sistema operativo o arquitectura no soportados: $system_architecture"
    exit 
  fi

  # Descargar e instalar solo Terminator
  if [ -z "$current_version" ]; then
    echo "Terminator no está instalado en este sistema."
    if prompt_user "¿Desea instalar la última versión de Terminator?"; then
      echo "Instalando Terminator..."
      sudo apt-get install -y terminator
    else
      echo "Instalación cancelada."
      return 0
      exit 
    fi
  else
    echo "Terminator ya está instalado en el sistema (versión actual: $current_version)."
    if prompt_user "¿Desea reinstalar Terminator para asegurarse de tener la última versión?"; then
      echo "Reinstalando Terminator..."
      sudo apt-get install --reinstall -y terminator
    else
      echo "Reinstalación cancelada."
      return 0
      exit 
    fi
  fi

  # Crear el directorio de instalación si no existe
  mkdir -p "$bin_dir"

  # Copiar el binario de Terminator al directorio especificado
  cp $(which terminator) "$bin_dir/terminator"

  # Crear archivo de registro de instalación
  echo "Terminator instalado en $install_dir." > "$install_dir/terminator.install"

  echo "Terminator ha sido instalado/actualizado en $install_dir."

  # Agregar el directorio de binarios al PATH y recargar el shell
  add_to_path
}

# Ejecutar la función
terminator_install_or_update
