#!/bin/bash
echo "Desinstalador de tmux"

# Verificar si la variable OSIRIS000_VENV_PATH está definida y tiene valor
if [ -z "$OSIRIS000_VENV_PATH" ]; then
  echo "Error: La variable OSIRIS000_VENV_PATH no está definida o está vacía. Abortando."
  exit 1
else
  echo "Directorio base de la instalación de tmux: $OSIRIS000_VENV_PATH"
fi

# Definir el directorio de instalación de tmux
install_dir="$OSIRIS000_VENV_PATH/software/tmux"
bin_dir="$install_dir/bin"

# Verificar si tmux está instalado en el sistema
if [ -f "$bin_dir/tmux" ]; then
  echo "tmux está instalado en $install_dir."
else
  echo "tmux no está instalado en $install_dir."
  exit 1
fi

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

# Preguntar si se desea desinstalar tmux
if prompt_user "¿Desea desinstalar tmux?"; then
  echo "Desinstalando tmux de $install_dir..."

  # Eliminar el binario de tmux
  rm -f "$bin_dir/tmux"

  # Eliminar el archivo de registro de instalación, si existe
  rm -f "$install_dir/tmux.install"

  # Opcional: Eliminar el directorio de instalación si está vacío
  if [ -d "$install_dir" ] && [ -z "$(ls -A $install_dir)" ]; then
    rmdir "$install_dir"
  fi

  # Eliminar el bin_dir del PATH en ~/.bashrc si existe
  profile_file="$HOME/.bashrc"
  if grep -q "$bin_dir" "$profile_file"; then
    echo "Eliminando $bin_dir del PATH en $profile_file"
    sed -i "\|$bin_dir|d" "$profile_file"
    echo "Recargando el perfil del shell..."
    source "$profile_file"
    echo "El PATH ha sido actualizado."
  fi

  # Opcional: Desinstalar tmux usando el gestor de paquetes
  if prompt_user "¿Desea eliminar tmux del sistema utilizando el gestor de paquetes?"; then
    sudo apt-get remove --purge -y tmux
  fi

  echo "tmux ha sido desinstalado de $install_dir."
else
  echo "Desinstalación cancelada."
  if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return 0
  else
    exit 0
  fi
fi
