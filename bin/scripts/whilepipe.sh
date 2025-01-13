#!/bin/bash

# Configuración: Crear las tuberías nombradas (FIFO) si no existen
mkfifo pipe1 pipe2

# Manejo de señales para limpieza
trap "rm -f pipe1 pipe2; kill 0" SIGINT SIGTERM EXIT

# Función para procesar datos de una tubería
process_pipe() {
    local pipe=$1
    local name=$2
    local log_file=$3

    echo "$name iniciado, esperando datos..." >> "$log_file"

    while true; do
        if read line < "$pipe"; then
            echo "$name procesando: $line" >> "$log_file"
        fi
    done &
}

# Iniciar bucles en segundo plano
process_pipe pipe1 "Bucle 1" "bucle1.log"
process_pipe pipe2 "Bucle 2" "bucle2.log"

# Bucle principal para seleccionar a qué bucle enviar los datos
while true; do
    echo "Input el comando ('1' para enviar a Bucle 1, '2' para enviar a Bucle 2, 'exit' para salir):"
    read comando
    if [ "$comando" == "exit" ]; then
        echo "Saliendo..."
        break
    elif [ "$comando" == "1" ]; then
        echo "Escribe algo para enviar a Bucle 1:"
        read data
        echo "$data" > pipe1
    elif [ "$comando" == "2" ]; then
        echo "Escribe algo para enviar a Bucle 2:"
        read data
        echo "$data" > pipe2
    else
        echo "Comando no reconocido."
    fi
done

# Limpiar al salir (esto se ejecutará debido al trap)
rm pipe1 pipe2
