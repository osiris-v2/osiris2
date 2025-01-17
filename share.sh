#!/usr/bin/bash


# Leer el archivo de texto y crear el array
declare -A INSTALL_COMMANDS

while IFS= read -r line; do
  # Ignorar líneas vacías o que contengan solo espacios
  if [[ -n "${line// }" && "$line" != "#"* ]]; then
    app_name=$(echo "$line" | awk '{print $1}')
    command_to_install=$(echo "$line" | awk '{$1=""; print substr($0,2)}')
    INSTALL_COMMANDS["$app_name"]=$command_to_install
  fi
done < install.com

# Función apt_install_command con opción para saltar la instalación
apt_install_command() {
  app_name=$1
  command_to_install=${INSTALL_COMMANDS[$app_name]}

  if [ -n "$command_to_install" ]; then
    echo "Pruebe \"$command_to_install\" para instalar $app_name."
    read -p "¿Desea continuar? (y/s/n): " choice
    case "$choice" in
      y|Y )
        $command_to_install
        ;;
      s|S )
        echo "Instalación saltada."
        ;;
      * )
        echo "Instalación cancelada."
        ;;
    esac
  else
    echo "No se encontró el comando de instalación para $app_name."
    echo "Revise en el archivo install.com se encuentre su ruta correcta"
  fi
}


# Función para comprobar si un comando está instalado
check_command_installed() {
  command_path=$1
  version_option=$2

  # Si no se proporciona una opción de versión, utilizar --version
  if [ -z "$version_option" ]; then
    version_option="--version"
  fi

  # Verificar con la ruta del ejecutable
  if [ -x "$command_path" ]; then
    version_output="$($command_path $version_option </dev/null 2>&1)"
    command_name=$(basename "$command_path")
    echo "******************************************************************"
    printf "%-64s%s\n" " $command_name está instalado en la ruta especificada." "*"
    echo "------------------------------------------------------------------"
    echo "$version_output"
    echo "******************************************************************"
  else
    command_name=$(basename "$command_path")
    echo "------------------------------------------------------------------"
    printf "%-69s%s\n" " $command_name no está instalado en la ruta especificada."
    echo " Se está verificando con dpkg para obtener más información."
    echo "------------------------------------------------------------------"
    
    # Verificar con el sistema de gestión de paquetes
    dpkg_output=$(dpkg -l "$command_name" 2>&1)
    if [ $? -eq 0 ]; then
      echo "******************************************************************"
      printf "%-64s%s\n" " $command_name está instalado en el sistema (según dpkg)." "*"
      echo "------------------------------------------------------------------"
      echo "$dpkg_output" | tail -n +6
      echo "******************************************************************"



# Supongamos que las variables dpkg_output y command_name están definidas previamente

# Obtener la ruta de instalación del paquete
installation_path=$(echo "$dpkg_output" | awk -v pkg="$command_name" '$1 == "ii" && $2 == pkg {print $3}')

# Obtener el nombre completo del paquete (incluyendo versión y arquitectura)
full_package_name=$(echo "$dpkg_output" | awk -v pkg="$command_name" '$1 == "ii" && $2 == pkg {print $2}')

echo "Ruta de instalación: $installation_path"
echo "Nombre del paquete: $full_package_name"




      # Ofrecer opción para instalar el paquete
      read -p "¿Desea instalar $command_name? (y/n): " choice
      case "$choice" in
        y|Y )
          apt_install_command "$command_name"
          ;;
        * )
          echo "Instalación cancelada."
          ;;
      esac
    else
      echo "------------------------------------------------------------------"
      printf "%-69s%s\n" " $command_name no está instalado en el sistema (según dpkg) tampoco."
      echo  apt_install_command "$command_name"
      apt_install_command "$command_name"
      echo "------------------------------------------------------------------"
      read -p "¿Continuar o Salir? (c/s): " choice
      case "$choice" in
        s|S )
          echo "Instalación cancelada."
#          exit 0
          ;;
      esac
    fi
  fi
}








