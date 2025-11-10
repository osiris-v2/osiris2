#!/bin/bash

# INTERFAZ OSIRIS - SCRIPT DE INSTALACION DE ENTORNO ANDROID EN DEBIAN
# Nombre: instalar_android_debian.sh
# Version: 1.0
# Idioma: Español

# Esta script instalara el JDK, descargara y configurara Android Studio,
# y ajustara las variables de entorno necesarias en Debian.

# INSTRUCCIONES IMPORTANTES:
# 1. Ejecuta este script con sudo: sudo bash instalar_android_debian.sh
# 2. Presta atencion a los mensajes en la terminal, especialmente para las partes manuales.
# 3. La URL de descarga de Android Studio puede cambiar con el tiempo.
#    Si el script falla al descargar, visita developer.android.com/studio
#    para obtener la URL de descarga mas reciente para Linux (archivo .tar.gz)
#    y actualiza la variable 'ANDROID_STUDIO_DOWNLOAD_URL' mas abajo.

# --- CONFIGURACION INICIAL ---

# URL de descarga de Android Studio para Linux (version 2023.3.1.26 - Iguana)
# POR FAVOR, VERIFICA SI ES LA ULTIMA EN developer.android.com/studio
ANDROID_STUDIO_DOWNLOAD_URL="https://redirector.gvt1.com/edgedl/android/studio/ide-zips/2025.1.4.8/android-studio-2025.1.4.8-linux.tar.gz"
ANDROID_STUDIO_FILENAME=$(basename "$ANDROID_STUDIO_DOWNLOAD_URL")
ANDROID_STUDIO_DIR="android-studio"
SDK_INSTALL_DIR="$HOME/Android/Sdk" # Donde Android Studio suele instalar el SDK

# --- FUNCIONES DE REGISTRO Y COMPROBACION ---

# Funcion para mostrar mensajes
log_message() {
  echo ""
  echo "--- OSIRIS: $1 ---"
  echo ""
}

# Funcion para comprobar si el ultimo comando fue exitoso
check_status() {
  if [ $? -eq 0 ]; then
    log_message "✅ PASO COMPLETADO EXITOSAMENTE: $1"
  else
    log_message "❌ ERROR: $1. SCRIPT DETENIDO."
    exit 1
  fi
}

# --- INICIO DEL SCRIPT PRINCIPAL ---

log_message "Iniciando instalacion del entorno de desarrollo Android en Debian..."

# 0. Comprobar permisos de root
if [ "$(id -u)" -ne 0 ]; then
  log_message "Este script debe ejecutarse con sudo. Ejemplo: sudo bash $0"
  exit 1
fi
check_status "Comprobacion de permisos de root."

# 1. Actualizar el sistema e instalar el JDK de Java
log_message "Paso 1: Actualizando la lista de paquetes del sistema e instalando OpenJDK 17."

# Actualizar lista de paquetes
apt update
check_status "Actualizacion de la lista de paquetes."

# Instalar OpenJDK 17 y herramientas esenciales
apt install -y openjdk-17-jdk wget unzip curl
check_status "Instalacion de OpenJDK 17 y herramientas basicas."

# Verificar instalacion de Java
log_message "Verificando la version de Java..."
java_version_output=$(java -version 2>&1)
echo "$java_version_output"
if [[ "$java_version_output" == *"openjdk version \"17."* ]]; then
  check_status "Verificacion de la version de Java (OpenJDK 17)."
else
  log_message "❌ ERROR: Java 17 no parece estar instalado o configurado correctamente. SCRIPT DETENIDO."
  exit 1
fi

log_message "Verificando la version de Javac..."
javac_version_output=$(javac -version 2>&1)
echo "$javac_version_output"
if [[ "$javac_version_output" == *"javac 17."* ]]; then
  check_status "Verificacion de la version de Javac."
else
  log_message "❌ ERROR: Javac 17 no parece estar instalado o configurado correctamente. SCRIPT DETENIDO."
  exit 1
fi

# 2. Descargar Android Studio
log_message "Paso 2: Descargando Android Studio. Esto puede tardar unos minutos."

# Borrar descargas anteriores si existen
rm -f "$ANDROID_STUDIO_FILENAME"

# Descargar Android Studio
wget -O "$ANDROID_STUDIO_FILENAME" "$ANDROID_STUDIO_DOWNLOAD_URL"
check_status "Descarga de Android Studio."

# 3. Extraer y mover Android Studio
log_message "Paso 3: Extrayendo y moviendo Android Studio a /opt."

# Crear directorio /opt/android-studio si no existe y eliminar anterior para limpieza
if [ -d "/opt/$ANDROID_STUDIO_DIR" ]; then
  log_message "Eliminando instalacion anterior de Android Studio en /opt/$ANDROID_STUDIO_DIR para una instalacion limpia."
  rm -rf "/opt/$ANDROID_STUDIO_DIR"
fi

# Extraer el archivo tar.gz
tar -xzf "$ANDROID_STUDIO_FILENAME" -C /opt/
check_status "Extraccion de Android Studio."

# Renombrar el directorio si no tiene el nombre estandar
if [ -d "/opt/android-studio-*" ] && [ ! -d "/opt/$ANDROID_STUDIO_DIR" ]; then
  mv /opt/android-studio-* "/opt/$ANDROID_STUDIO_DIR"
  check_status "Renombrado del directorio de Android Studio."
fi

# Establecer permisos correctos
chown -R "$USER":"$USER" "/opt/$ANDROID_STUDIO_DIR"
check_status "Establecimiento de permisos para Android Studio."

log_message "Limpiando archivos de descarga..."
rm -f "$ANDROID_STUDIO_FILENAME"
check_status "Limpieza de archivos temporales."

# 4. Configurar variables de entorno ANDROID_HOME y PATH
log_message "Paso 4: Configurando las variables de entorno ANDROID_HOME y PATH."

BASHRC_FILE="$HOME/.bashrc"
PROFILE_FILE="$HOME/.profile"

# Añadir o actualizar ANDROID_HOME en .bashrc
if grep -q "export ANDROID_HOME" "$BASHRC_FILE"; then
  sed -i "s|export ANDROID_HOME=.*|export ANDROID_HOME=$SDK_INSTALL_DIR|" "$BASHRC_FILE"
  log_message "ANDROID_HOME actualizado en $BASHRC_FILE."
else
  echo "" >> "$BASHRC_FILE"
  echo "# Configuracion de Android Studio anadida por el script de Osiris" >> "$BASHRC_FILE"
  echo "export ANDROID_HOME=$SDK_INSTALL_DIR" >> "$BASHRC_FILE"
  log_message "ANDROID_HOME anadido a $BASHRC_FILE."
fi
check_status "Configuracion de ANDROID_HOME."

# Añadir o actualizar PATH en .bashrc
PATHS_TO_ADD=(
  "$ANDROID_HOME/cmdline-tools/latest/bin"
  "$ANDROID_HOME/platform-tools"
  "$ANDROID_HOME/build-tools/33.0.0" # Puedes ajustar la version si instalas otra
)

for P in "${PATHS_TO_ADD[@]}"; do
  if ! grep -q "export PATH=.*$P" "$BASHRC_FILE"; then
    echo "export PATH=\$PATH:$P" >> "$BASHRC_FILE"
    log_message "$P anadido al PATH en $BASHRC_FILE."
  else
    log_message "$P ya esta en el PATH en $BASHRC_FILE. No se hicieron cambios."
  fi
done
check_status "Configuracion de PATH en $BASHRC_FILE."

# Tambien anadir a .profile si es necesario para sesiones de login no interactivas
# Esto ayuda a que las variables esten disponibles para todo el sistema
if grep -q "export ANDROID_HOME" "$PROFILE_FILE"; then
  sed -i "s|export ANDROID_HOME=.*|export ANDROID_HOME=$SDK_INSTALL_DIR|" "$PROFILE_FILE"
  log_message "ANDROID_HOME actualizado en $PROFILE_FILE."
else
  echo "" >> "$PROFILE_FILE"
  echo "# Configuracion de Android Studio anadida por el script de Osiris" >> "$PROFILE_FILE"
  echo "export ANDROID_HOME=$SDK_INSTALL_DIR" >> "$PROFILE_FILE"
  log_message "ANDROID_HOME anadido a $PROFILE_FILE."
fi

for P in "${PATHS_TO_ADD[@]}"; do
  if ! grep -q "export PATH=.*$P" "$PROFILE_FILE"; then
    echo "export PATH=\$PATH:$P" >> "$PROFILE_FILE"
    log_message "$P anadido al PATH en $PROFILE_FILE."
  else
    log_message "$P ya esta en el PATH en $PROFILE_FILE. No se hicieron cambios."
  fi
done
check_status "Configuracion de PATH en $PROFILE_FILE."

log_message "Para que las variables de entorno surtan efecto en esta sesion, ejecuta:"
echo "  source $BASHRC_FILE"
echo "  source $PROFILE_FILE"

# 5. Pasos Manuales y Verificacion Final
log_message "Paso 5: INSTRUCCIONES MANUALES IMPORTANTES PARA LA CONFIGURACION DE ANDROID STUDIO."
log_message "Por favor, inicia Android Studio por primera vez:"
echo "  /opt/$ANDROID_STUDIO_DIR/bin/studio.sh"
echo ""
echo "Cuando se inicie el asistente de configuracion de Android Studio:"
echo "  - Selecciona 'Custom Setup' (Configuracion Personalizada)."
echo "  - Asegurate de que los siguientes componentes esten seleccionados para su descarga:"
echo "    - Android SDK Platform"
echo "    - Android SDK Platform-Tools"
echo "    - Android Virtual Device (AVD)"
echo "  - Acepta todas las licencias y espera a que la descarga e instalacion finalicen."
echo ""
log_message "¡ESTE PASO ES CRITICO Y DEBE HACERSE MANUALMENTE!"

#lo hacemos automáticamente

source $BASHRC_FILE
/opt/$ANDROID_STUDIO_DIR/bin/studio.sh &

# Verificacion despues de los pasos manuales
log_message "Una vez que hayas completado el asistente de configuracion de Android Studio, puedes verificar la instalacion de ADB."
log_message "Abre una NUEVA TERMINAL y ejecuta:"
echo "  adb --version"
echo ""
echo "Deberias ver la version de ADB. Si no es asi, revisa que el SDK este bien instalado y que las variables de entorno esten cargadas."

log_message "¡INSTALACION DEL ENTORNO DE DESARROLLO ANDROID COMPLETADA! ✨"
log_message "Recuerda que para que los cambios en el PATH se reflejen, es posible que debas reiniciar tu terminal o ejecutar 'source ~/.bashrc'."
log_message "¡Ahora puedes empezar a desarrollar tus aplicaciones Android!" 📱