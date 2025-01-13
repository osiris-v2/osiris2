#!/bin/bash

# Script para detectar y matar procesos zombie y sus procesos padre

echo "Detectando procesos zombie..."

# Buscar todos los procesos zombie (estado Z)
zombie_pids=$(ps aux | awk '$8=="Z" {print $2}')

if [ -z "$zombie_pids" ]; then
    echo "No se encontraron procesos zombie."
    return 0
fi

echo "Se encontraron los siguientes procesos zombie: $zombie_pids"

for zombie_pid in $zombie_pids; do
    echo "Procesando zombie PID: $zombie_pid"
    # Obtener el PID del proceso padre (PPID) del proceso zombie
    ppid=$(ps -o ppid= -p "$zombie_pid" | awk '{print $1}')

    if [ -z "$ppid" ]; then
        echo "No se pudo determinar el proceso padre para el PID: $zombie_pid"
        continue
    fi

    echo "El proceso padre del zombie (PPID): $ppid"

    # Enviar la señal SIGCHLD al proceso padre para intentar que elimine los zombies
    echo "Intentando enviar SIGCHLD al proceso padre $ppid..."
    kill -s SIGCHLD "$ppid" 
    proceso="El proceso padre fue informado"
    # Esperar un momento para que el proceso padre recoja al zombie
    sleep 1
    # Verificar si el proceso zombie sigue existiendo
    #if ps -p "$zombie_pid"; then
    #    echo "El proceso zombie sigue existiendo: $proceso"
    #else
    #    echo "El proceso zombie fue recogido por su proceso padre."
    #fi

ps -p "$ppid" -f 

#    echo "Proceso zombie $zombie_pid terminado."
done

echo "Todos los procesos zombie han sido procesados."
