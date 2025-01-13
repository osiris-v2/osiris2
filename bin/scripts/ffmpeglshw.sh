#!/bin/bash

# Función para listar dispositivos de captura de audio
listar_audio() {
    echo "=== Dispositivos de Captura de Audio ==="
    arecord -l | grep "^card" | awk -F'[][]' '{print "Card " $2 ", Device " $4 ": " $6}' | nl -w1 -s': '
}

# Función para listar dispositivos de captura de video usando ffmpeg
listar_video() {
    echo "=== Dispositivos de Captura de Video ==="
    ffmpeg -f v4l2 -list_formats all -i dummy 2>&1 | grep "video" | nl -w1 -s': '
}

# Función para listar pantallas disponibles
listar_pantallas() {
    echo "=== Pantallas Disponibles ==="
    xrandr --listmonitors | grep "^ " | nl -w1 -s': '
}

# Listar dispositivos y capturar selección del usuario con validación
listar_audio
audio_count=$(arecord -l | grep "^card" | wc -l)
if [ $audio_count -gt 0 ]; then
    while true; do
        read -p "Seleccione el número del dispositivo de audio: " audio_num
        if [ "$audio_num" -ge 1 ] && [ "$audio_num" -le $audio_count ]; then
            audio_device=$(arecord -l | grep "^card" | awk -F'[][]' '{print "" $2 "," $4}' | sed -n "${audio_num}p")
            break
        else
            echo "Opción no válida. Por favor, seleccione un número entre 1 y $audio_count."
        fi
    done
else
    echo "No hay dispositivos de audio disponibles."
    audio_device="hw:0,0"  # Establecer un valor por defecto o dejar vacío
fi

listar_video
video_count=$(ffmpeg -f v4l2 -list_formats all -i dummy 2>&1 | grep "video" | wc -l)
if [ $video_count -gt 0 ]; then
    while true; do
        read -p "Seleccione el número del dispositivo de video: " video_num
        if [ "$video_num" -ge 1 ] && [ "$video_num" -le $video_count ]; then
            video_device=$(ffmpeg -f v4l2 -list_formats all -i dummy 2>&1 | grep "video" | sed -n "${video_num}p" | awk '{print $2}')
            break
        else
            echo "Opción no válida. Por favor, seleccione un número entre 1 y $video_count."
        fi
    done
else
    echo "No hay dispositivos de video disponibles."
    video_device=""  # Establecer un valor por defecto o dejar vacío
fi

listar_pantallas
pantalla_count=$(xrandr --listmonitors | grep "^ " | wc -l)
if [ $pantalla_count -gt 0 ]; then
    while true; do
        read -p "Seleccione el número de la pantalla para capturar: " pantalla_num
        if [ "$pantalla_num" -ge 1 ] && [ "$pantalla_num" -le $pantalla_count ]; then
            display=$(xrandr --listmonitors | grep "^ " | sed -n "${pantalla_num}p" | awk '{print $4}')
            break
        else
            echo "Opción no válida. Por favor, seleccione un número entre 1 y $pantalla_count."
        fi
    done
else
    echo "No hay pantallas disponibles."
    display=":0.0"  # Establecer un valor por defecto o dejar vacío
fi

# Pedir la clave de transmisión de YouTube
read -p "Ingrese su clave de transmisión de YouTube: " youtube_key

# Construir el comando FFmpeg para captura de pantalla
ffmpeg_command_screen="sudo -u osiris ffmpeg -y -re -f x11grab -video_size 1280x720 -framerate 30 -i ${display} -f alsa -ac 2 -i ${audio_device} -c:v libx264 -preset ultrafast -tune zerolatency -b:v 1500k -maxrate 1500k -bufsize 3000k -g 60 -c:a aac -b:a 128k -f flv rtmp://a.rtmp.youtube.com/live2/${youtube_key}"

# Construir el comando FFmpeg para captura de video desde cámara
ffmpeg_command_video="sudo -u osiris ffmpeg -y -re -f v4l2 -framerate 30 -video_size 1280x720 -i ${video_device} -f alsa -ac 2 -i ${audio_device} -c:v libx264 -preset ultrafast -tune zerolatency -b:v 1500k -maxrate 1500k -bufsize 3000k -g 60 -c:a aac -b:a 128k -f flv rtmp://a.rtmp.youtube.com/live2/${youtube_key}"

# Mostrar los comandos generados y permitir al usuario decidir si desea proceder
echo "=== Comando FFmpeg para Captura de Pantalla ==="
echo $ffmpeg_command_screen

echo "=== Comando FFmpeg para Captura de Video desde Cámara ==="
echo $ffmpeg_command_video

# Validar si el usuario quiere proceder con el comando
while true; do
    read -p "¿Desea ejecutar el comando de captura de pantalla? (s/n): " ejecutar_screen
    if [ "$ejecutar_screen" == "s" ]; then
        eval $ffmpeg_command_screen
        break
    elif [ "$ejecutar_screen" == "n" ]; then
        break
    else
        echo "Opción no válida. Por favor, elija 's' o 'n'."
    fi
done

while true; do
    read -p "¿Desea ejecutar el comando de captura de video? (s/n): " ejecutar_video
    if [ "$ejecutar_video" == "s" ]; then
        eval $ffmpeg_command_video
        break
    elif [ "$ejecutar_video" == "n" ]; then
        break
    else
        echo "Opción no válida. Por favor, elija 's' o 'n'."
    fi
done
