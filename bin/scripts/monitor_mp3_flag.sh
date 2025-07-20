#!/bin/bash

# Directorio base donde se encuentran el archivo de audio y el de bandera
AUDIO_DIR="/var/osiris2/bin/com/datas/ai/audio"
FLAG_FILE="${AUDIO_DIR}/readmp3.flag" # Ruta completa para el flag
DEFAULT_AUDIO_FILE="${AUDIO_DIR}/last_request.mp3" # Ruta completa para el audio por defecto

FFPLAY_COMMAND_BASE="ffplay -nodisp -autoexit -hide_banner -volume 88" # Comando base para ffplay

# Función para detener cualquier proceso ffplay existente que esté reproduciendo archivos del directorio AUDIO_DIR
stop_ffplay() {
    # Busca procesos ffplay que estén reproduciendo archivos dentro de AUDIO_DIR
    PIDS=$(pgrep -f "ffplay.*${AUDIO_DIR}")
    if [ -n "$PIDS" ]; then
        echo "Cerrando procesos ffplay existentes del directorio ${AUDIO_DIR}: $PIDS"
        kill -9 $PIDS > /dev/null 2>&1
        sleep 0.5
    fi
}

# Función para iniciar ffplay en segundo plano con un archivo específico
start_ffplay() {
    local file_to_play="$1"
    stop_ffplay # Detener cualquier ffplay anterior antes de iniciar uno nuevo
    echo "Iniciando ffplay para ${file_to_play}"
    nohup ${FFPLAY_COMMAND_BASE} "${file_to_play}" > /dev/null 2>&1 &
    FFPLAY_PID=$!
    echo "ffplay iniciado con PID: ${FFPLAY_PID}"
}

# --- Inicialización ---

# 1. Asegurarse de que el directorio de audio exista
if [ ! -d "${AUDIO_DIR}" ]; then
    echo "El directorio de audio ${AUDIO_DIR} no existe. Creándolo."
    mkdir -p "${AUDIO_DIR}"
fi

# 2. Reproducir last_request.mp3 al inicio (si existe)
if [ -f "${DEFAULT_AUDIO_FILE}" ]; then
    echo "Reproduciendo archivo de audio por defecto al inicio: ${DEFAULT_AUDIO_FILE}"
    start_ffplay "${DEFAULT_AUDIO_FILE}"
else
    echo "Archivo de audio por defecto '${DEFAULT_AUDIO_FILE}' no encontrado. No se reproducira al inicio."
fi

LAST_FLAG_CONTENT="" # Variable para almacenar el contenido anterior del flag

echo "Iniciando monitoreo de ${FLAG_FILE}..."

# Bucle principal de monitoreo
while true; do
    if [ -f "${FLAG_FILE}" ]; then
        CURRENT_FLAG_CONTENT=$(cat "${FLAG_FILE}")
        # Eliminar espacios en blanco y saltos de línea para una comparación limpia
        CURRENT_FLAG_CONTENT=$(echo "${CURRENT_FLAG_CONTENT}" | tr -d '
\r ' | xargs)

        # Si el contenido del archivo de bandera ha cambiado
        if [ "$CURRENT_FLAG_CONTENT" != "$LAST_FLAG_CONTENT" ]; then
            echo "Cambio detectado en ${FLAG_FILE}. Contenido nuevo: '${CURRENT_FLAG_CONTENT}'"

            TARGET_AUDIO_FILE="" # Archivo que intentaremos reproducir

            # Si el contenido del flag no está vacío, intentar usarlo
            if [ -n "$CURRENT_FLAG_CONTENT" ]; then
                # Construir la ruta completa del archivo de audio basada en el contenido del flag
                # Asumimos que el contenido del flag es solo el nombre del archivo dentro de AUDIO_DIR
                PROPOSED_AUDIO_FILE="${AUDIO_DIR}/${CURRENT_FLAG_CONTENT}"
                if [ -f "${PROPOSED_AUDIO_FILE}" ]; then
                    TARGET_AUDIO_FILE="${PROPOSED_AUDIO_FILE}"
                else
                    echo "Advertencia: El archivo '${PROPOSED_AUDIO_FILE}' especificado en el flag no existe. Reproduciendo el archivo por defecto."
                    TARGET_AUDIO_FILE="${DEFAULT_AUDIO_FILE}"
                fi
            else
                # Si el flag está vacío, reproducir el archivo por defecto
                echo "El archivo de bandera está vacío. Reproduciendo el archivo por defecto."
                TARGET_AUDIO_FILE="${DEFAULT_AUDIO_FILE}"
            fi

            # Si se ha determinado un archivo para reproducir, iniciar ffplay
            if [ -n "$TARGET_AUDIO_FILE" ]; then
                start_ffplay "${TARGET_AUDIO_FILE}"
            else
                # Esto solo ocurriría si DEFAULT_AUDIO_FILE tampoco existe y el flag estaba vacío.
                echo "No se encontro ningun archivo de audio para reproducir."
                stop_ffplay # Asegurarse de que no haya nada sonando
            fi

            LAST_FLAG_CONTENT="$CURRENT_FLAG_CONTENT" # Actualiza el último contenido conocido
        fi
    else
        # Si el archivo de bandera no existe (o ha sido eliminado),
        # y anteriormente sí existía o había contenido, detiene la reproducción y reproduce el por defecto.
        if [ -n "$LAST_FLAG_CONTENT" ]; then
            echo "${FLAG_FILE} no encontrado. Deteniendo ffplay si está activo y volviendo a reproducir por defecto."
            stop_ffplay
            if [ -f "${DEFAULT_AUDIO_FILE}" ]; then
                start_ffplay "${DEFAULT_AUDIO_FILE}"
            else
                echo "Archivo de audio por defecto '${DEFAULT_AUDIO_FILE}' no encontrado. No se reproducira al inicio."
            fi
            LAST_FLAG_CONTENT="" # Resetea el estado para indicar que el archivo no existe
        fi
    fi
    sleep 1 # Espera 1 segundo antes de la siguiente verificación.
done
