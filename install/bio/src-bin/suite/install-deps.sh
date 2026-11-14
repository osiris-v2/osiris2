#!/usr/bin/env bash
# Instala dependencias de compilación. NO lo ejecutes con sudo delante (lo usa por dentro).
set -e
if   command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y build-essential pkg-config cmake libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev libavformat-dev libavcodec-dev libswscale-dev libswresample-dev libavutil-dev ffmpeg xdg-utils unzip curl python3
elif command -v dnf     >/dev/null; then sudo dnf install -y gcc make pkgconf-pkg-config cmake SDL2-devel SDL2_ttf-devel SDL2_image-devel ffmpeg-free-devel ffmpeg-free xdg-utils unzip curl python3
elif command -v pacman  >/dev/null; then sudo pacman -S --needed --noconfirm base-devel cmake sdl2 sdl2_ttf sdl2_image ffmpeg xdg-utils unzip curl python
elif command -v brew    >/dev/null; then brew install pkg-config cmake sdl2 sdl2_ttf sdl2_image ffmpeg yt-dlp
else echo "Gestor de paquetes no reconocido: instala SDL2, SDL2_ttf, SDL2_image (opcional), pkg-config y un compilador C."; exit 1; fi
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -e "$HERE/share-fonts/DejaVuSans.ttf" ] || "$HERE/share-fonts/fonts-sync.sh" --download
if ! command -v yt-dlp >/dev/null; then   # solo lo necesita el descargador
  mkdir -p "$HOME/.local/bin"
  curl -fL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o "$HOME/.local/bin/yt-dlp" && chmod +x "$HOME/.local/bin/yt-dlp" || echo "(yt-dlp no instalado: solo lo necesita el descargador)"
fi
echo "Listo. Ejecuta ./build-all.sh"
