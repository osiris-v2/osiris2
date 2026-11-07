#!/usr/bin/env bash
# Instala dependencias de compilación (SDL2, SDL2_ttf, fuente) y yt-dlp. NO usar con sudo delante del script.
set -e
if   command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y build-essential pkg-config cmake libsdl2-dev libsdl2-ttf-dev fonts-dejavu-core ffmpeg xdg-utils python3-pip
elif command -v dnf     >/dev/null; then sudo dnf install -y gcc make pkgconf-pkg-config cmake SDL2-devel SDL2_ttf-devel dejavu-sans-fonts ffmpeg-free xdg-utils
elif command -v pacman  >/dev/null; then sudo pacman -S --needed --noconfirm base-devel cmake sdl2 sdl2_ttf ttf-dejavu ffmpeg xdg-utils
elif command -v brew    >/dev/null; then brew install pkg-config cmake sdl2 sdl2_ttf ffmpeg yt-dlp
else echo "Gestor de paquetes no reconocido: instala SDL2, SDL2_ttf, pkg-config y un compilador C manualmente."; exit 1; fi
if ! command -v yt-dlp >/dev/null; then
  echo "Instalando yt-dlp en ~/.local/bin ..."
  mkdir -p "$HOME/.local/bin"
  curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o "$HOME/.local/bin/yt-dlp"
  chmod +x "$HOME/.local/bin/yt-dlp"
fi
echo "Listo. Ahora ejecuta: ./build.sh"
