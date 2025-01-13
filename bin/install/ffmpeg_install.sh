#!/bin/bash

echo "Instalador avanzado de FFmpeg con configuraciones completas"

# Variables de configuración
install_dir="/usr/local/ffmpeg"
src_dir="/tmp/ffmpeg-src"
num_cores=$(nproc)
latest_ffmpeg_url="https://ffmpeg.org/releases/ffmpeg-7.0.1.tar.bz2"

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

# Descargar FFmpeg
echo "Descargando FFmpeg desde $latest_ffmpeg_url..."
wget -O "$src_dir/ffmpeg.tar.bz2" "$latest_ffmpeg_url" || { echo "Error al descargar FFmpeg."; exit 1; }
echo "Extrayendo FFmpeg..."
tar -xjf "$src_dir/ffmpeg.tar.bz2" -C "$src_dir" || { echo "Error al extraer FFmpeg."; exit 1; }

lastdir=$pwd
# Cambiar al directorio fuente
cd "$src_dir/ffmpeg-7.0.1" || { echo "Directorio fuente no encontrado."; exit 1; }


# Configurar FFmpeg con opciones avanzadas
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
  --enable-shared || { echo "Error en la configuración de FFmpeg."; exit 1; }

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

cd $lastdir

