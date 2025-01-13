#!/bin/bash
echo "Instalador de tmux"

# Verificar si la variable OSIRIS000_VENV_PATH está definida y tiene valor
if [ -z "$OSIRIS000_VENV_PATH" ]; then
  echo "Error: La variable OSIRIS000_VENV_PATH no está definida o está vacía. Abortando."
  exit 1
else
  echo "Directorio base para la instalación de tmux: $OSIRIS000_VENV_PATH"
fi

# Definir el directorio base para la instalación
install_dir="$OSIRIS000_VENV_PATH/software/tmux"
bin_dir="$install_dir/bin"

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

# Verificar si tmux ya está instalado
if [ -f "$bin_dir/tmux" ]; then
  current_version=$("$bin_dir/tmux" -V | grep -oP '\d+(\.\d+)+')
  echo "tmux ya está instalado en el sistema (versión actual: $current_version)."
  if prompt_user "¿Desea reinstalar tmux para asegurarse de tener la última versión?"; then
    echo "Reinstalando tmux..."
    sudo apt-get install --reinstall -y tmux

    # Crear el directorio de instalación si no existe
    mkdir -p "$install_dir"

    # Copiar el binario de tmux al directorio especificado
    cp $(which tmux) "$bin_dir/tmux"

    # Crear archivo de registro de instalación
    echo "tmux instalado en $install_dir." > "$install_dir/tmux.install"
    add_to_path
  else
    echo "Reinstalación cancelada."
    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
      return 0
    else
      exit 0
    fi
  fi
else
  echo "tmux no está instalado en este sistema."
  if prompt_user "¿Desea instalar la última versión de tmux?"; then
    echo "Instalando tmux..."
    sudo apt-get install -y tmux

    # Crear el directorio de instalación si no existe
    mkdir -p "$bin_dir"

    # Copiar el binario de tmux al directorio especificado
    cp $(which tmux) "$bin_dir/tmux"

    # Crear archivo de registro de instalación
    echo "tmux instalado en $install_dir." > "$install_dir/tmux.install"
    add_to_path
  else
    echo "Instalación cancelada."
    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
      return 0
    else
      exit 0
    fi
  fi
fi
