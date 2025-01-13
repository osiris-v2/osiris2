#!/bin/bash

# Archivo a reproducir (puede ser un archivo local o una URL)
GIF_PATH="$1"

# Verifica si el archivo fue especificado
if [[ -z "$GIF_PATH" ]]; then
    echo "Debe especificar un archivo o URL para reproducir."
    exit 1
fi

# Ruta para el socket (no se usa directamente en este caso, pero puede ser útil para otras aplicaciones)
vlc_socket="/tmp/vlc_socket_$$"

# Función para iniciar VLC
start_vlc() {
    # Inicia VLC en segundo plano con las opciones adecuadas para video y audio
    cvlc --no-fullscreen --loop "$GIF_PATH" > /dev/null 2>&1 &
    vlc_pid=$!
    echo "VLC iniciado con PID $vlc_pid"
}

# Crea el socket y ejecuta VLC
start_vlc

# Limpieza del socket al salir (actualmente no se usa, pero se deja para posibles usos futuros)
#trap "rm -f '$vlc_socket'; kill $vlc_pid" EXIT
