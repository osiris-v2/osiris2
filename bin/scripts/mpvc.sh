#!/bin/bash

# Variable para almacenar el directorio actual
current_dir="$OSIRIS000_BASEPATH/bin/com/datas/ffmpeg/tv"

# Variable para almacenar la instancia actual de mpv
mpv_pid=""
mpv_socket="/tmp/mpv_socket_$$"

# Función para listar archivos multimedia y directorios
list_files() {
    echo "Archivos y directorios en: $current_dir"
    local i=1
    declare -gA item_map

    # Primero listamos los archivos
    for file in "$current_dir"/*; do
        if [[ -f "$file" && "$file" =~ \.(ts|m3u8|mp4|mkv|mp3|avi|flac|ogg|wav|jpg|jpeg|png|gif|bmp|tif|tiff)$ ]]; then
            echo "$i) $(basename "$file")"
            item_map[$i]="$file"
            ((i++))
        fi
    done

    # Luego listamos los directorios
    for dir in "$current_dir"/*/; do
        if [[ -d "$dir" ]]; then
            echo "$i) $(basename "$dir")/"
            item_map[$i]="$dir"
            ((i++))
        fi
    done
}



play_file() {
    local input="$1"

    if [[ "$input" =~ ^http ]]; then
        # Si el argumento es una URL, usarlo directamente
        file="$input"
        echo "FILE:".$file
    elif [[ -n "${item_map[$input]}" ]]; then
        # Si el argumento es un número y corresponde a un archivo en item_map
        file="${item_map[$input]}"
    else
        echo "Número de archivo no válido o URL no accesible."
        return
    fi

    # Si ya hay un proceso de mpv corriendo, lo cambia a otro archivo sin reiniciar
    if [[ -n "$mpv_pid" ]]; then
        echo "loadfile \"$file\" replace" | socat - "$mpv_socket"
    else 
        # Ejecutar mpv en segundo plano y redirigir la salida
        mpv  --geometry=800x600 --no-keepaspect --fs --audio-device=pulse --input-ipc-server="$mpv_socket" "$file" > /dev/null 2>&1 &
        mpv_pid=$!
    fi
}




# Función para cambiar de directorio
change_directory() {
    local index="$1"
    local dir="${item_map[$index]}"

    if [[ -z "$dir" || ! -d "$dir" ]]; then
        echo "Número de directorio no válido."
        return
    fi

    current_dir="$dir"
}

# Función para matar el reproductor activo
kill_mpv() {
    if [[ -n "$mpv_pid" ]]; then
        kill "$mpv_pid"
        wait "$mpv_pid" 2>/dev/null
        mpv_pid=""
        echo "Reproductor mpv detenido."
    else
        echo "No hay reproductor activo."
    fi
}

# Bucle principal de comandos
while true; do
    echo
    echo "Comando (ls, ls .., play n, kill, salir):"
    read -r cmd args

    case "$cmd" in
        ls)
            if [[ "$args" == ".." ]]; then
                current_dir=$(dirname "$current_dir")
            elif [[ "$args" =~ ^[0-9]+$ ]]; then
                change_directory "$args"
            fi
            list_files
            ;;
        play)
            if [[ -n "$args" && "$args" =~ ^[0-9]+$ ]]; then
                play_file "$args"
            else
                echo "Debe especificar un número de archivo válido."
            fi
            ;;
        lasturl)
            play_file "$(cat $OSIRIS000_BIN/com/datas/lasturl.txt)"
            ;;
        kill)
            kill_mpv
            ;;
        salir)
            kill_mpv
            echo "Saliendo..."
            break
            ;;
        *)
            echo "Comando no reconocido."
            ;;
    esac
done

# Limpieza del socket al salir
rm -f "$mpv_socket"
