#!/bin/bash
# PROYECTO OSIRIS - MONITOR DE TELEMETRIA AVANZADA
# VERSION: DUREZA 256 - REVISION: 2026-01-17
# ASCII PURO - SIN ACENTOS
clear;reset;clear
while true; do
    clear
    echo 
    #"========================================================================"
    echo "          SISTEMA OSIRIS - CONSOLA DE INGENIERIA (DUREZA 256)           "
    echo "          REPORTE: $(date '+%Y-%m-%d %H:%M:%S')                         "
    echo 
    #"========================================================================"
    
    # 1. METRICAS DE PROCESOS CRITICOS (Nodo C, Cerebro Rust, Satelite Python)
    printf "%-12s %-8s %-8s %-8s %-12s %-12s\n" "PROCESO" "PID" "CPU(%)" "MEM(%)" "VIRT(MB)" "RES(MB)"
    echo 
    #"------------------------------------------------------------------------"
    
    ps aux | grep -E "osiris_node|cerebro_semilla|audio_engine.py" | grep -v grep | awk '{
        # $5 es VSZ (Kbytes), $6 es RSS (Kbytes)
        virt_mb = $5/1024;
        res_mb = $6/1024;
        printf "%-12s %-8s %-8s %-8s %-12.2f %-12.2f\n", $11, $2, $3, $4, virt_mb, res_mb
    }'

    echo 
    #"------------------------------------------------------------------------"
    
    # 2. ANALISIS DE MEMORIA URANIO (VIRTUAL VS RESIDENTE)
    # Calculamos la reserva de direccionamiento que mencionamos
    node_data=$(ps aux | grep "osiris_node" | grep -v grep | awk '{print $5, $6}')
    if [ ! -z "$node_data" ]; then
        v_mem=$(echo $node_data | awk '{print $1/1024}')
        r_mem=$(echo $node_data | awk '{print $2/1024}')
        reserva=$(echo "$v_mem - $r_mem" | bc)
        echo "ANALISIS NODO MUSCULO:"
        echo " > Reserva Uranio (Buffer Pasivo): ${reserva} MB"
        echo " > Eficiencia de Mapeo: $(echo "scale=2; ($r_mem/$v_mem)*100" | bc)%"
    fi

    echo 
    #"------------------------------------------------------------------------"

    # 3. METRICAS GLOBALES Y LATENCIA ESTIMADA
    # Reflejamos el consumo real que mencionaste (< 3GB neto)
    free -m | awk 'NR==2{
        used=$3; total=$2;
        printf "RAM SISTEMA: %dMB / %dMB (Neto Usado: %.2f%%)\n", used, total, used*100/total 
    }'
    
    # Carga por Core (Para verificar el balanceo de los 4 nucleos)
    load=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f1)
    echo "CARGA GLOBAL CPU: $load (Balanceo Multihilo activo)"
    
    echo 
    #"========================================================================"
    echo " ESTADO: TRANSMITIENDO VIDEO | PROTOCOLO: FGN | DUREZA: 256"
    echo 
    #"========================================================================"

    sleep 5
done