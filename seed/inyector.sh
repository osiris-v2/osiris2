#!/bin/bash
# PROYECTO OSIRIS - Script de Maniobra Seed Node
# DUREZA 256 - SINTAXIS FGN

while true; do
    echo "[MANIOBRA] Iniciando Cerebro Semilla..."
    
    # Ejecucion del binario compilado en Rust
    ./target/release/cerebro_semilla
    
    echo ""
    echo "------------------------------------------"
    echo "[ESTADO] Cerebro Semilla ha finalizado."
    echo "1) Inyectar nueva URL (inyector.sh)"
    echo "2) Reiniciar ciclo actual"
    echo "3) Salir al terminal"
    echo "------------------------------------------"
    read -p "Seleccione accion: " opcion

    case $opcion in
        1)
            read -p "Ingrese URL para el Uranio: " url_inyect
            if [ -z "$url_inyect" ]; then
                echo "[ERROR] URL vacia. Abortando inyeccion."
            else
                echo "[INYECCION] Ejecutando inyector.sh..."
                # Llamada al script inyector con la URL ingresada
                ./cerebro_semilla/target/release/cerebro_semilla |./inyector_videourl.sh "$url_inyect"  
            fi
            ;;
        2)
            echo "[REINICIO] Volviendo a lanzar..."
            continue
            ;;
        3)
            echo "[SALIDA] Cerrando interfaz de maniobra."
            break
            ;;
        *)
            echo "[OPCION NO VALIDA] Reintentando..."
            ;;
    esac
done