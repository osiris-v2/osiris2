#!/bin/bash
source "/etc/environment" #Puede deshabilitarlo si no necesita las variables globales OSIRS000
echo "Instalador avanzado de FFmpeg con configuraciones completas"


#Puede CAMBIAR esta dirección desde https://ffmpeg.org/releases/
latest_ffmpeg_url="https://ffmpeg.org/releases/ffmpeg-7.0.1.tar.bz2"

# Variables de configuración
install_dir="/usr/local/osiris2/ffmpeg"


#CAMBIE A SU DIRECTORIO en default_dir A SU NECESIDAD 
#EN ESTE DIRECTORIO SE GENERA EL EJECUTABLE 
#EN /SU_DIRECTORIO/ffmpeg/bin/ffmpeg
#O USE RUTAS RELATIVAS
default_dir="${OSIRIS000_BIN}/com/osiris_env/ffmpeg"

download_dir="/tmp/ffmpeg-downloads" # Directorio de descarga
src_dir="$download_dir/ffmpeg-src"  # Directoio temporal para la descarga y descompresión de ffmpeg

##mkdir -p $install_dir
#mkdir -p $default_dir
# Solicitar al usuario que ingrese un directorio de instalación
read -p "Ingrese el directorio de instalación (por defecto: ${default_dir}): " install_dir

# Usar el valor predeterminado si la entrada está en blanco
install_dir=${install_dir:-$default_dir}

echo "El directorio de instalación es: $install_dir"

num_cores=$(nproc)


# Crear directorios necesarios
mkdir -p "$src_dir" "$install_dir"

# Instalar dependencias necesarias
echo "Instalando dependencias..."
sudo apt-get update
sudo apt-get install -y \
  autoconf automake build-essential cmake git libass-dev libfreetype6-dev \
  libmp3lame-dev libnuma-dev libopus-dev libsdl2-dev \
  libtool libva-dev libvdpau-dev libvorbis-dev libvpx-dev libx264-dev \
  libx265-dev libxcb1-dev libxcb-shm0-dev libxcb-xfixes0-dev pkg-config \
  texinfo wget yasm zlib1g-dev libssl-dev
# Instalar dependencias para libfdk-aac
sudo apt-get install -y libtool autoconf automake
# Descargar fdk-aac
wget https://github.com/mstorsjo/fdk-aac/archive/refs/tags/v2.0.2.tar.gz
# Descomprimir fdk-aac
tar -xzvf v2.0.2.tar.gz
# Compilar e instalar fdk-aac
cd fdk-aac-2.0.2/
./autogen.sh
./configure --prefix=/usr/local/osiris2/fdk-aac
make -j"$num_cores"
sudo make install
cd $src_dir
# Crear el archivo fdk-aac.pc manualmente si no existe
if [ ! -f /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc ]; then
  echo "prefix=/usr/local/osiris2/fdk-aac" | sudo tee /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "exec_prefix=\${prefix}" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "libdir=\${exec_prefix}/lib" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "includedir=\${prefix}/include" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "Name: fdk-aac" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "Description: Fraunhofer FDK AAC library" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "Version: 2.0.2" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "Libs: -L\${libdir} -lfdk-aac" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
  echo "Cflags: -I\${includedir}" | sudo tee -a /usr/local/osiris2/fdk-aac/lib/pkgconfig/libfdk-aac.pc
fi
# Crear enlaces simbólicos para libfdk-aac
if [ ! -f /usr/local/lib/libfdk-aac.so.2 ]; then
	  sudo ln -s /usr/local/osiris2/fdk-aac/lib/libfdk-aac.so.2 /usr/local/lib/libfdk-aac.so.2
 fi

if [ ! -f /usr/local/lib64/libfdk-aac.so.2 ]; then
	 sudo ln -s /usr/local/osiris2/fdk-aac/lib/libfdk-aac.so.2 /usr/local/lib64/libfdk-aac.so.2
fi

# Descargar FFmpeg
echo "Descargando FFmpeg desde $latest_ffmpeg_url..."
wget -O "$src_dir/ffmpeg.tar.bz2" "$latest_ffmpeg_url" || { echo "Error al descargar FFmpeg."; exit 1; }
echo "Extrayendo FFmpeg..."
tar -xjf "$src_dir/ffmpeg.tar.bz2" -C "$src_dir" || { echo "Error al extraer FFmpeg."; exit 1; }

lastdir=$pwd
# Cambiar al directorio fuente
cd "$src_dir/ffmpeg-7.0.1" || { echo "Directorio fuente no encontrado."; exit 1; }

# Configurar PKG_CONFIG_PATH y configurar FFmpeg con opciones avanzadas
export PKG_CONFIG_PATH="/usr/local/osiris2/fdk-aac/lib/pkgconfig:$PKG_CONFIG_PATH"
echo "Configurando FFmpeg..."
./configure \
  --prefix="$install_dir" \
  --enable-gpl \
  --enable-nonfree \
  --enable-libass \
  --enable-libfreetype \
  --enable-libmp3lame \
  --enable-libopus \
  --enable-libvorbis \
  --enable-libvpx \
  --enable-libx264 \
  --enable-libx265 \
  --enable-openssl \
  --enable-libxcb \
  --enable-pic \
  --enable-shared \
  --enable-muxer=hls \
  --enable-protocol=https,tls \
  --enable-libfdk-aac \
  --extra-cflags="-I/usr/local/osiris2/fdk-aac/include" \
  --extra-ldflags="-L/usr/local/osiris2/fdk-aac/lib" || { echo "Error en la configuración de FFmpeg."; exit 1; }

# Compilar FFmpeg
echo "Compilando FFmpeg con $num_cores núcleos..."
make -j"$num_cores" || { echo "Error durante la compilación de FFmpeg."; exit 1; }

# Instalar FFmpeg
echo "Instalando FFmpeg en $install_dir..."
sudo make install || { echo "Error durante la instalación de FFmpeg."; exit 1; }

# Configurar las rutas de las bibliotecas compartidas
echo "Configurando las rutas de las bibliotecas compartidas..."
echo "$install_dir/lib" | sudo tee /etc/ld.so.conf.d/ffmpeg.conf > /dev/null
sudo ldconfig

# Añadir FFmpeg al PATH
echo "Añadiendo FFmpeg al PATH..."
if ! grep -q "$install_dir/bin" ~/.bashrc; then
  echo "export PATH=\"$install_dir/bin:\$PATH\"" >> ~/.bashrc
fi
export PATH="$install_dir/bin:$PATH"

# Verificar instalación
echo "Verificando instalación de FFmpeg..."
ffmpeg -version || { echo "FFmpeg no se instaló correctamente. Verifique las configuraciones."; exit 1; }

# Confirmación final
echo "FFmpeg instalado correctamente y está listo para usar."
echo "instalado en ${install_dir} "
echo "#################################"
ls $install_dir
echo "#################################"
cd $lastdir

# Limpiar archivos temporales

echo "Archivos temporales eliminados."

# Limpiar archivos temporales
echo "Limpiando archivos temporales..."
cd "$download_dir"
rm -rf "$src_dir/ffmpeg-7.0.1"
rm -rf "$src_dir/ffmpeg.tar.bz2"
$default_dir/bin/ffmpeg -muxers | grep hls
ls $install_dir
echo "#################################"
cd $lastdir



