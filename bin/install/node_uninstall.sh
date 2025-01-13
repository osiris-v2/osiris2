#!/bin/bash
echo "Uninstaller Node.js"

# Verificar si la variable OSIRIS000_VENV_PATH está definida y tiene valor
if [ -z "$OSIRIS000_VENV_PATH" ]; then
  echo "Error: La variable OSIRIS000_VENV_PATH no está definida o está vacía. Abortando."
  exit 1
else
  echo "Directorio base de la instalación de Node.js: $OSIRIS000_VENV_PATH"
fi

# Definir el directorio de instalación de Node.js
install_dir="$OSIRIS000_VENV_PATH/software/node"
bin_dir="$install_dir/bin"

# Verificar si Node.js está instalado en el sistema
if [ -f "$bin_dir/node" ]; then
  node_version=$("$bin_dir/node" -v 2>/dev/null | cut -d'v' -f2)
  echo "Node.js versión $node_version está instalado en $install_dir."
else
  echo "Node.js no está instalado en $install_dir."
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

# Preguntar si se desea desinstalar Node.js
if prompt_user "¿Desea desinstalar Node.js versión $node_version?"; then
  echo "Limpieza de cachés de npm..."
  npm cache clean --force

  echo "Desinstalando Node.js versión $node_version de $install_dir..."

  # Eliminar los binarios de Node.js
  rm -f "$bin_dir/node"
  rm -f "$bin_dir/npm"
  rm -f "$bin_dir/npx"

  # Eliminar los archivos de librerías de Node.js
  rm -rf "$install_dir/lib/node_modules"

  # Eliminar los archivos de Node.js instalados
  rm -rf "$install_dir/include/node"

  # Eliminar el archivo de registro de instalación, si existe
  rm -f "$install_dir/node.install"

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

  echo "Node.js versión $node_version ha sido desinstalado de $install_dir."
else
  echo "Desinstalación cancelada."
  exit 0
fi
