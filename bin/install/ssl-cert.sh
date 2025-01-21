#!/bin/bash

script_dir=$(dirname "$(readlink -f "$0")")
cd $script_dir
#nos situamos en bin
cd ..

echo "SD:".$PWD

# Variables por defecto
BASE_DIR="com/datas/cert"
DEFAULT_KEY_SIZE=2048
DEFAULT_CERT_FILE="$BASE_DIR/cert.pem"
TEMP_KEY_FILE="$BASE_DIR/temp_key.pem"
CERT_EXTENSION="pem"

# Función para mostrar un mensaje de error y salir
error_exit() {
  echo "Error: $1" >&2
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

# Función para comprobar que openssl esté instalado
check_openssl() {
   if ! command -v openssl &> /dev/null
   then
      error_exit "OpenSSL no está instalado. Instálalo para poder crear certificados."
   fi
}

# Función para crear el directorio base si no existe
create_base_dir() {
  if [[ ! -d "$BASE_DIR" ]]; then
    echo "Creando directorio base: $BASE_DIR"
    mkdir -p "$BASE_DIR" || error_exit "Error al crear el directorio base: $BASE_DIR"
  fi
}

# Función para listar los certificados válidos encontrados en el directorio base

list_valid_certs() {
  local cert_files=()
  local found_valid=0
  echo "DEBUG: Buscando certificados en $BASE_DIR"
  find "$BASE_DIR" -maxdepth 1 -type f -name "*.${CERT_EXTENSION}" -print0 | while IFS= read -r -d $'\0' file; do
    echo "DEBUG: Encontrado el archivo: $file"
    if openssl x509 -checkend 0 -noout -in "$file" &> /dev/null; then
      echo "DEBUG: Certificado válido: $file"
      cert_files+=("$file")
      found_valid=1 # Marca que se encontró al menos un certificado válido
    else
      echo "DEBUG: Certificado NO válido o caducado: $file"
    fi
    echo "DEBUG: found_valid después del analisis: $found_valid"
  done

  if [[ "$found_valid" -eq 1 ]]; then
    echo "Certificados válidos encontrados en: $BASE_DIR"
     for i in "${!cert_files[@]}"; do
        echo "$((i+1)). ${cert_files[$i]}"
     done
     echo "DEBUG: Retornando 0"
     return 0 # Retorna 0 si se encontraron uno o más certificados válidos
   else
     echo "DEBUG: Retornando 1"
     echo "$BASE_DIR"
    return 1; # Retorna 1 si no se encontró ningún certificado válido
  fi
}

# Función para inspeccionar un certificado
inspect_cert() {
  local cert_file="$1"
  if [[ ! -f "$cert_file" ]]; then
    error_exit "El archivo '$cert_file' no existe."
  fi
  openssl x509 -text -noout -in "$cert_file"
}

# Función para validar el tamaño de la clave RSA
validate_key_size() {
  local key_size="$1"
  if [[ ! "$key_size" =~ ^[0-9]+$ ]]; then
    error_exit "El tamaño de la clave RSA debe ser un número entero positivo."
  fi
  if [[ "$key_size" -le 0 ]]; then
      error_exit "El tamaño de la clave RSA debe ser un número entero positivo."
  fi
  echo "$key_size"
}

# Función para generar un certificado
create_cert() {
  local domains="$1"
  local key_size="$2"
  local key_file="$3"
  local cert_file="$4"

  echo "Generando certificado para: $domains"

  # Generar la clave RSA si no se proporciona
  if [[ -z "$key_file" ]]; then
    echo "Generando una nueva clave RSA..."
    openssl genrsa -out "$TEMP_KEY_FILE" "$(validate_key_size "$key_size")"  || error_exit "Error al generar la clave RSA."
    key_file="$TEMP_KEY_FILE"
  else
      if [[ ! -f "$key_file" ]]; then
         echo "La clave RSA no existe o se va a sobreescribir"
         openssl genrsa -out "$key_file" "$(validate_key_size "$key_size")"  || error_exit "Error al generar la clave RSA."
     fi
  fi
  

  # Crear archivo de configuración para el certificado (SAN)
  temp_conf=$(mktemp)
  echo "[req]" > "$temp_conf"
  echo "prompt = no" >> "$temp_conf"
  echo "distinguished_name = req_distinguished_name" >> "$temp_conf"
  echo "req_extensions = req_ext" >> "$temp_conf"
  echo "" >> "$temp_conf"
  echo "[req_distinguished_name]" >> "$temp_conf"
  echo "CN = $(echo "$domains" | awk -F, '{print $1}')" >> "$temp_conf"
  echo "" >> "$temp_conf"
  echo "[req_ext]" >> "$temp_conf"
  echo "subjectAltName = @alt_names" >> "$temp_conf"
  echo "" >> "$temp_conf"
  echo "[alt_names]" >> "$temp_conf"
  i=1
  for domain in $(echo "$domains" | tr ',' '\n'); do
    echo "DNS.$i = $domain" >> "$temp_conf"
    i=$((i+1))
  done

  # Generar el certificado autofirmado
  openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:"$(validate_key_size "$key_size")" -key "$key_file" -out "$cert_file" -config "$temp_conf" || error_exit "Error al generar el certificado."
  rm "$temp_conf" # Limpia el archivo temporal de configuración

  if [[ "$key_file" == "$TEMP_KEY_FILE" ]]; then
    rm "$TEMP_KEY_FILE" #Elimina archivo temporal si no se especificó clave
  fi

  echo "Certificado generado correctamente en: $cert_file"
}

# Main
main() {
    # Verifica si openssl está instalado
    check_openssl

    #Crea el directorio base si no existe
    create_base_dir

    # Comprobar si hay certificados existentes
    if list_valid_certs; then
       while true; do
        read -r -p "¿Desea crear un nuevo certificado, inspeccionar uno existente o salir? (nuevo/inspeccionar/salir): " action
        case "$action" in
          [nN]|[nN][uU][eE][vV][oO]) break;;
          [iI]|[iI][nN][sS][pP][eE][cC][cC][iI][oO][nN][aA][rR])
            read -r -p "Introduzca el número del certificado que desea inspeccionar: " cert_num
             if [[ "$cert_num" =~ ^[0-9]+$ ]] && [[ "$cert_num" -gt 0 ]]; then
                 local cert_files=()
                   find "$BASE_DIR" -maxdepth 1 -type f -name "*.${CERT_EXTENSION}" -print0 | while IFS= read -r -d $'\0' file; do
                    if openssl x509 -checkend 0 -noout -in "$file" &> /dev/null; then
                       cert_files+=("$file")
                     fi
                   done
                if [[ "$cert_num" -le "${#cert_files[@]}" ]]; then
                      inspect_cert "${cert_files[$((cert_num-1))]}"
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
          [sS]|[sS][aA][lL][iI][rR]) exit 0;;
           *) echo "Opción no válida. Por favor, elija 'nuevo', 'inspeccionar' o 'salir'."; continue;;
         esac
       done
    fi


    # Solicitar los nombres de dominio
    read -r -p "Introduzca los nombres de dominio para el certificado (separados por comas): " domains
    if [[ -z "$domains" ]]; then
        error_exit "Debe proporcionar al menos un nombre de dominio."
    fi
    
    # Solicitar el tamaño de la clave RSA
    while true; do
       read -r -p "Introduzca el tamaño de la clave RSA (por defecto $DEFAULT_KEY_SIZE): " key_size_input
       if [[ -z "$key_size_input" ]]; then
          key_size="$DEFAULT_KEY_SIZE"
          break
       fi
       if [[ "$key_size_input" =~ ^[0-9]+$ ]] && [[ "$key_size_input" -gt 0 ]]; then
         key_size="$key_size_input"
         break
       else
         echo "El tamaño de la clave debe ser un número entero positivo."
       fi
    done

    # Solicitar el nombre del archivo de la clave RSA (opcional)
    read -r -p "Introduzca el nombre del archivo de la clave RSA (o pulse Enter para generar una nueva): " key_file
    if [[ -n "$key_file" ]]; then
        check_file_writable "$key_file"
    fi

    # Solicitar el nombre del archivo del certificado (opcional)
    while true; do
        read -r -p "Introduzca el nombre del archivo del certificado (o pulse Enter para usar '$DEFAULT_CERT_FILE'): " cert_file_input
        if [[ -z "$cert_file_input" ]]; then
           cert_file="$DEFAULT_CERT_FILE"
           break
        fi
        check_file_writable "$cert_file_input"
        if [[ -e "$cert_file_input" ]]; then
            read -r -p "El archivo '$cert_file_input' ya existe. ¿Desea sobrescribirlo? (s/n): " overwrite
            case "$overwrite" in
                [sS]|[sS][iI] ) cert_file="$cert_file_input"; break;;
                *) continue;;
            esac
        else
            cert_file="$cert_file_input"
           break
        fi
    done
    
    # Generar el certificado
    create_cert "$domains" "$key_size" "$key_file" "$cert_file"
}

# Ejecuta el main
main "$@"
