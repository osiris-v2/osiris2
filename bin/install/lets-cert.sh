#!/bin/bash

script_dir=$(dirname "$(readlink -f "$0")")
cd $script_dir
#nos situamos en bin
cd ..

echo "SD:".$PWD

# Variables por defecto
BASE_DIR="/etc/letsencrypt/live"
DEFAULT_KEY_SIZE=2048
DEFAULT_CERT_FILE="$BASE_DIR/cert.pem"
TEMP_KEY_FILE="$BASE_DIR/temp_key.pem"
CERT_EXTENSION="pem"

# Variables por defecto
DEFAULT_CERT_DIR="$BASE_DIR" # Directirio base de certbot
DEFAULT_LOG_FILE="$BASE_DIR/certbot_manager.log"
DEFAULT_WEBROOT_PATH="/var/www/html" #Directorio webroot por defecto
DEFAULT_APACHE_SITES_DIR="/etc/apache2/sites-available"
DEFAULT_APACHE_ENABLED_DIR="/etc/apache2/sites-enabled"

# Función para mostrar un mensaje de error y salir
error_exit() {
  echo "Error: $1" >&2
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Error: $1" >> "$DEFAULT_LOG_FILE"
  exit 1
}

# Función para comprobar la existencia y permisos de escritura de un archivo
check_file_writable() {
  local file="$1"
  if [[ -e "$file" ]]; then
    if [[ ! -w "$file" ]]; then
      error_exit "El archivo '$file' existe pero no tiene permisos de escritura."
    fi
  fi
}

# Función para comprobar que certbot esté instalado
check_certbot() {
  if ! command -v certbot &> /dev/null; then
    error_exit "Certbot no está instalado. Instálalo para poder gestionar los certificados de Let's Encrypt."
  fi
}


# Función para verificar y actualizar certbot
check_and_update_certbot() {
  echo "DEBUG: Verificando la versión de certbot..."
  certbot --version >> "$DEFAULT_LOG_FILE"
  certbot_version=$($certbot --version 2>&1 | awk '{print $3}')

  if [[ -z "$certbot_version" ]]; then
      error_exit "No se pudo obtener la versión de certbot. Por favor, verifica la instalación de certbot y su configuración."
  fi

  if [[ "$certbot_version" == *"unknown"* ]] || [[ "$certbot_version" == "" ]]; then
      error_exit "La versión de certbot es desconocida. Por favor, verifica la instalación de certbot y su configuración."
  fi


  echo "DEBUG: Versión de certbot instalada: $certbot_version"
  # Define a valid version, for example 2.9.0
  valid_version="2.0.0"
  if version_lt "$certbot_version" "$valid_version"; then
       echo "DEBUG: La versión de certbot es inferior a $valid_version. Intentando actualizar certbot..."
       if ! sudo apt-get update; then
          error_exit "No se pudo actualizar la lista de paquetes."
       fi
        if ! sudo apt-get install --only-upgrade certbot -y; then
          error_exit "No se pudo actualizar certbot a la última versión."
        else
          echo "DEBUG: certbot actualizado a la última versión. Por favor, vuelve a ejecutar este script."
        exit 0
       fi
  else
       echo "DEBUG: La versión de certbot es $certbot_version y es igual o superior a la versión $valid_version, por lo tanto no es necesario actualizarlo"
  fi
}

# Función para verificar si una versión es inferior a otra
version_lt() {
    if [[ "$1" == "$2" ]]; then
        return 1 # Versions are equal
    fi
    local IFS=.
    local v1_arr=($1)
    local v2_arr=($2)

    local i=0
    while [[ $i -lt ${#v1_arr[@]} || $i -lt ${#v2_arr[@]} ]]; do
        local v1_part=${v1_arr[$i]:-0}
        local v2_part=${v2_arr[$i]:-0}

        if [[ $v1_part -lt $v2_part ]]; then
            return 0  # Version 1 is lower
        elif [[ $v1_part -gt $v2_part ]]; then
            return 1  # Version 1 is higher
        fi
        i=$((i+1))
    done

   return 1 # Versions are equal
}


# Función para verificar las librerias de python
check_python_libs() {
  echo "DEBUG: Verificando las librerías de python..."
  if ! pip3 list | grep -E 'cryptography|cffi|pyOpenSSL' >> "$DEFAULT_LOG_FILE"; then
       echo "DEBUG: No se encontraron las librerías cryptography, cffi o pyOpenSSL instaladas"
       echo "DEBUG: Intentando instalar las librerías de python cryptography, cffi y pyOpenSSL..."
          if ! pip3 install --upgrade cryptography cffi pyOpenSSL  >> "$DEFAULT_LOG_FILE"; then
             error_exit "No se pudieron instalar las librerías cryptography, cffi y pyOpenSSL.  Verifica tu conexión a internet e inténtalo de nuevo"
          fi
          echo "DEBUG: Librerías de python cryptography, cffi y pyOpenSSL instaladas correctamente"
     else
      echo "DEBUG: Las librerías cryptography, cffi y pyOpenSSL están instaladas."
  fi
}


# Funcion para validar un nombre de dominio
validate_domain() {
    local domain="$1"
    if [[ -z "$domain" ]]; then
       return 1
    fi

    if ! echo "$domain" | grep -q '\.'; then
         return 1; # Retorna 1 si no contiene punto
    fi
    return 0; # Retorna 0 si es válido
}


# Función para listar los certificados válidos encontrados
list_valid_certs() {
    local cert_domains=()
    local cert_dirs=()
    
    echo "DEBUG: Buscando certificados en $BASE_DIR"
     if [[ ! -d "$BASE_DIR" ]]; then
       echo "DEBUG: El directorio $BASE_DIR no existe"
       echo "No se encontraron certificados válidos en el directorio: $BASE_DIR"
      return 1
    fi

    find "$BASE_DIR" -maxdepth 1 -type d  -print0 | while IFS= read -r -d $'\0' dir; do
        if [[ "$dir" != "$BASE_DIR" ]] && [[ -d "$dir" ]]; then # Añadida comprobación del subdirectorio
            domain_name=$(basename "$dir")
             
             if certbot certificates | grep "Domain: $domain_name" > /dev/null; then
                 cert_domains+=("$domain_name")
                 cert_dirs+=("$dir")
                  echo "DEBUG: Encontrado el certificado para el dominio: $domain_name en $dir"
             else
                  echo "DEBUG: El certificado para el dominio: $domain_name no es valido o no existe"
             fi
        fi
   done


  if [[ ${#cert_domains[@]} -gt 0 ]]; then
       echo "Certificados válidos encontrados en: $BASE_DIR"
       for i in "${!cert_domains[@]}"; do
           echo "$((i+1)). ${cert_domains[$i]} (Directorio: ${cert_dirs[$i]})"
       done
      return 0 # Retorna 0 si se encontraron uno o más certificados válidos
   else
    echo "No se encontraron certificados válidos en el directorio: $BASE_DIR"
    return 1; # Retorna 1 si no se encontró ningún certificado válido
  fi
}

# Función para inspeccionar un certificado
inspect_cert() {
    local cert_dir="$1"
     local cert_domain=$(basename "$cert_dir")
  if [[ ! -d "$cert_dir" ]]; then
    error_exit "El directorio del certificado '$cert_dir' no existe."
  fi
   
   certbot certificates  | grep "Domain: $cert_domain" -A 10
}

# Función para renovar un certificado
renew_cert() {
    local cert_domain="$1"
    echo "Renovando certificado para el dominio: $cert_domain"
   certbot renew --cert-name "$cert_domain" >> "$DEFAULT_LOG_FILE" || error_exit "Error al renovar el certificado para el dominio: $cert_domain"
    echo "Certificado para el dominio '$cert_domain' renovado correctamente."
}


# Función para crear un nuevo certificado
create_cert() {
  local domains="$1"
  local email="$2"
  local webroot_path="$3"

    echo "Creando un nuevo certificado para los dominios: $domains"
  if ! certbot certonly --email "$email" --agree-tos --domains "$domains" --non-interactive  --authenticator webroot --webroot-path "$webroot_path" >> "$DEFAULT_LOG_FILE" 2>&1; then
         error_exit "Error al crear el certificado, revisa los logs para más información."
    fi
   echo "Certificado para los dominios '$domains' generado correctamente."
}


# Funcion para crear un archivo de configuracion de apache
create_apache_conf() {
    local domain="$1"
    local webroot_path="$2"
    local conf_file="$DEFAULT_APACHE_SITES_DIR/$domain.conf"
    local cert_path="/etc/letsencrypt/live/$domain" #RUTA FIJA

    if [[ -f "$conf_file" ]]; then
       error_exit "Ya existe un archivo de configuración para este dominio: $conf_file"
    fi


  cat << EOF > "$conf_file"
<VirtualHost *:80>
    ServerName $domain
    ServerAlias www.$domain
    Redirect permanent / https://$domain/
</VirtualHost>

<VirtualHost *:443>
    ServerName $domain
    ServerAlias www.$domain

    DocumentRoot "$webroot_path"

    SSLEngine on
    SSLCertificateFile "$cert_path/fullchain.pem"
    SSLCertificateKeyFile "$cert_path/privkey.pem"
    
    <Directory "$webroot_path">
          Options Indexes FollowSymLinks
          AllowOverride All
          Require all granted
      </Directory>
</VirtualHost>
EOF
  if [[ ! -f "$conf_file" ]]; then
     error_exit "Error al crear el archivo de configuración de apache"
  fi
  echo "Archivo de configuración creado correctamente en $conf_file"
  
}

#Funcion para mover el archivo conf a sites-enabled
move_apache_conf() {
  local domain="$1"
   local conf_file="$DEFAULT_APACHE_SITES_DIR/$domain.conf"
   local enabled_file="$DEFAULT_APACHE_ENABLED_DIR/$domain.conf"

   if [[ -f "$enabled_file" ]]; then
        error_exit "El archivo de configuración para el dominio '$domain' ya existe en '$DEFAULT_APACHE_ENABLED_DIR'"
   fi
    if ! sudo mv "$conf_file" "$enabled_file" ; then
        error_exit "Error al mover el archivo '$conf_file' a '$DEFAULT_APACHE_ENABLED_DIR'"
    fi
  echo "Archivo de configuración movido correctamente a: $enabled_file"
}


# Main
main() {
    # Verifica si certbot está instalado
    check_certbot

    # Verifica y actualiza certbot
    check_and_update_certbot

     # Verifica librerías python
    check_python_libs
    
    local webroot_path=""
    local create_cert_mode=0 #0 no , 1 si

    # Comprobar si hay certificados existentes
    if list_valid_certs; then
        while true; do
           read -r -p "¿Desea crear un nuevo certificado, renovar uno existente, inspeccionar uno existente, crear archivo .conf para apache o salir? (nuevo/renovar/inspeccionar/crear_conf/salir): " action
           case "$action" in
              [nN]|[nN][uU][eE][vV][oO])
                create_cert_mode=1 #Ponemos a 1 la variable para luego evitar el bucle
                read -r -p "Introduzca la ruta al directorio webroot: " webroot_path
                if [[ -z "$webroot_path" ]]; then
                     error_exit "Debe proporcionar la ruta al directorio webroot. No se puede continuar"
                fi
                 read -r -p "Introduzca los nombres de dominio para el certificado (separados por comas): " domains
                  if [[ -z "$domains" ]]; then
                     error_exit "Debe proporcionar al menos un nombre de dominio."
                 fi
                
                #Verificar la validez del dominio
                 for domain in $(echo "$domains" | tr ',' '\n'); do
                   if ! validate_domain "$domain"; then
                        error_exit "El dominio '$domain' no es un nombre de dominio válido, verifica la sintaxis"
                   fi
                 done

                read -r -p "Introduzca su dirección de correo electrónico: " email
                if [[ -z "$email" ]]; then
                   error_exit "Debe proporcionar una dirección de correo electrónico."
                fi
                  create_cert "$domains" "$email" "$webroot_path"
                 break
              ;;
            [rR]|[rR][eE][nN][oO][vV][aA][rR])
             read -r -p "Introduzca el número del certificado que desea renovar: " cert_num
                 if [[ "$cert_num" =~ ^[0-9]+$ ]] && [[ "$cert_num" -gt 0 ]]; then
                     local cert_domains=()
                      find "$BASE_DIR" -maxdepth 1 -type d -print0 | while IFS= read -r -d $'\0' dir; do
                        if [[ "$dir" != "$BASE_DIR" ]]; then
                            domain_name=$(basename "$dir")
                            if certbot certificates | grep "Domain: $domain_name" > /dev/null; then
                               cert_domains+=("$domain_name")
                           fi
                        fi
                      done
                    if [[ "$cert_num" -le "${#cert_domains[@]}" ]]; then
                         renew_cert "${cert_domains[$((cert_num-1))]}"
                          break #Volver al inicio del bucle para preguntar la acción
                     else
                       echo "Número de certificado inválido."
                       continue
                   fi
                 else
                     echo "Número de certificado inválido."
                  continue
               fi
              ;;
             [iI]|[iI][nN][sS][pP][eE][cC][cC][iI][oO][nN][aA][rR])
                read -r -p "Introduzca el número del certificado que desea inspeccionar: " cert_num
                 if [[ "$cert_num" =~ ^[0-9]+$ ]] && [[ "$cert_num" -gt 0 ]]; then
                     local cert_dirs=()
                     find "$BASE_DIR" -maxdepth 1 -type d -print0 | while IFS= read -r -d $'\0' dir; do
                         if [[ "$dir" != "$BASE_DIR" ]]; then
                           domain_name=$(basename "$dir")
                             if certbot certificates | grep "Domain: $domain_name" > /dev/null; then
                                cert_dirs+=("$dir")
                           fi
                        fi
                   done
                   if [[ "$cert_num" -le "${#cert_dirs[@]}" ]]; then
                         inspect_cert "${cert_dirs[$((cert_num-1))]}"
                        continue #Volver al inicio del bucle para preguntar la acción
                     else
                         echo "Número de certificado inválido."
                         continue
                   fi
               else
                   echo "Número de certificado inválido."
                    continue
               fi
           ;;
            [cC]|[cC][rR][eE][aA][rR]_[cC][oO][nN][fF])
                read -r -p "Introduzca el nombre del dominio para el archivo de configuración de apache: " domain
                 if [[ -z "$domain" ]]; then
                   error_exit "Debe proporcionar un nombre de dominio para el archivo de configuración de apache."
                 fi

                 if ! validate_domain "$domain"; then
                      error_exit "El dominio '$domain' no es un nombre de dominio válido, verifica la sintaxis"
                  fi
                 read -r -p "Introduzca la ruta del directorio webroot: " webroot_path
                  if [[ -z "$webroot_path" ]]; then
                    error_exit "Debe proporcionar la ruta al directorio webroot para crear el archivo .conf"
                   fi
                  create_apache_conf "$domain" "$webroot_path"
                  move_apache_conf "$domain"
                break
             ;;

          [sS]|[sS][aA][lL][iI][rR]) exit 0;;
          *) echo "Opción no válida. Por favor, elija 'nuevo', 'renovar', 'inspeccionar', 'crear_conf' o 'salir'."; continue;;
        esac
      done
    else
        echo "No se encontraron certificados, por favor, crea un certificado"
        read -r -p "Introduzca la ruta al directorio webroot: " webroot_path
          if [[ -z "$webroot_path" ]]; then
            error_exit "Debe proporcionar la ruta al directorio webroot. No se puede continuar"
          fi
          read -r -p "¿Desea crear un nuevo certificado o salir? (nuevo/salir): " action
          case "$action" in
           [nN]|[nN][uU][eE][vV][oO])
             read -r -p "Introduzca los nombres de dominio para el certificado (separados por comas): " domains
                if [[ -z "$domains" ]]; then
                    error_exit "Debe proporcionar al menos un nombre de dominio."
                 fi
                  #Verificar la validez del dominio
                  for domain in $(echo "$domains" | tr ',' '\n'); do
                      if ! validate_domain "$domain"; then
                         error_exit "El dominio '$domain' no es un nombre de dominio válido, verifica la sintaxis"
                      fi
                  done
                read -r -p "Introduzca su dirección de correo electrónico: " email
                 if [[ -z "$email" ]]; then
                   error_exit "Debe proporcionar una dirección de correo electrónico."
                 fi
               create_cert "$domains" "$email" "$webroot_path"
               create_cert_mode=1 #Ponemos a 1 la variable para luego evitar el bucle
            ;;
          [sS]|[sS][aA][lL][iI][rR]) exit 0;;
          *) echo "Opción no válida. Por favor, elija 'nuevo' o 'salir'."; continue;;
        esac
    fi
     #Preguntar de nuevo si se crea un certificado
     if [[ $create_cert_mode -eq 1 ]]; then
        while true; do
         read -r -p "¿Desea crear un archivo .conf para apache o salir? (crear_conf/salir): " action
           case "$action" in
              [cC]|[cC][rR][eE][aA][rR]_[cC][oO][nN][fF])
                 read -r -p "Introduzca el nombre del dominio para el archivo de configuración de apache: " domain
                  if [[ -z "$domain" ]]; then
                     error_exit "Debe proporcionar un nombre de dominio para el archivo de configuración de apache."
                  fi

                  if ! validate_domain "$domain"; then
                       error_exit "El dominio '$domain' no es un nombre de dominio válido, verifica la sintaxis"
                  fi
                 read -r -p "Introduzca la ruta del directorio webroot: " webroot_path
                    if [[ -z "$webroot_path" ]]; then
                        error_exit "Debe proporcionar la ruta al directorio webroot para crear el archivo .conf"
                    fi
                    create_apache_conf "$domain" "$webroot_path"
                    move_apache_conf "$domain"
                 break
               ;;
             [sS]|[sS][aA][lL][iI][rR]) exit 0;;
            *) echo "Opción no válida. Por favor, elija 'crear_conf' o 'salir'."; continue;;
         esac
        done
     fi
}

# Ejecuta el main
main "$@"
