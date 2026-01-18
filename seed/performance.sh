#!/bin/bash
# PROYECTO OSIRIS - MONITOR DE HARDWARE (DUREZA 256)
# ASCII PURO - SIN ACENTOS - REFRESCO 5S

while true; do
    clear
    echo "=========================================================="
    echo "      SISTEMA OSIRIS - TELEMETRIA DE MEMORIA URANIO       "
    echo "      REPORTE: $(date '+%Y-%m-%d %H:%M:%S')               "
    echo "=========================================================="
    echo ""
    
    # Cabecera de columnas
    printf "%-15s %-10s %-10s %-10s %-10s\n" "PROCESO" "PID" "CPU(%)" "MEM(%)" "VIRT(MB)"
    echo "----------------------------------------------------------"

    # Filtrado y procesamiento de datos (Nodo y Cerebro)
    # Buscamos 'nodo_musculo', 'cerebro' y el transcriptor de python
    ps aux | grep -E "nodo_musculo|cerebro|audio_engine.py" | grep -v grep | awk '{
        printf "%-15s %-10s %-10s %-10s %-10.2f\n", $11, $2, $3, $4, $5/1024
    }'

    echo ""
    echo "----------------------------------------------------------"
    # Estado global de la RAM (Dureza 256)
    free -m | awk 'NR==2{printf "ESTADO RAM URANIO: %dMB / %dMB Usado (%.2f%%)\n", $3, $2, $3*100/$2 }'
    echo "=========================================================="
    echo " Presiona [CTRL+C] para finalizar el monitoreo."

    sleep 5
done