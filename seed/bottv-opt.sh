#!/bin/bash
source /etc/environment

# --- CONFIGURACION ---
ARCHIVO_ENTRADA="../bin/com/datas/ffmpeg/canales_activos.txt"
ARCHIVO_MAESTRO_JSON="../bin/com/datas/ffmpeg/canales.json"
TXT_ACTIVOS="../bin/com/datas/ffmpeg/canales_activos.txt"
TXT_INACTIVOS="../bin/com/datas/ffmpeg/canales_inactivos.txt"
JSON_ACTIVOS="../bin/com/datas/ffmpeg/activos.json"
JSON_INACTIVOS="../bin/com/datas/ffmpeg/inactivos.json"

TIEMPO_MUESTREO=0.5 
TIEMPO_ORDEN=60     
DEBUG=1

# Preparar entorno y forzar permisos iniciales
mkdir -p "$(dirname "$ARCHIVO_MAESTRO_JSON")"
if [[ ! -f "$ARCHIVO_MAESTRO_JSON" || ! -s "$ARCHIVO_MAESTRO_JSON" ]]; then
    echo "[]" > "$ARCHIVO_MAESTRO_JSON"
    chmod 644 "$ARCHIVO_MAESTRO_JSON"
fi

# --- MEMORIA VOLÁTIL ---
declare -A ACCESIBLES
declare -A INACCESIBLES
declare -A ULTIMA_URL
declare -A CANAL_NAME
declare -A CANAL_DESC
declare -A CANAL_XDATA
declare -A URL_ORIGINAL

log() {
    [[ $DEBUG -eq 1 ]] && echo -e "\e[1;34m[DEBUG]\e[0m \e[33m$(date +'%H:%M:%S')\e[0m - $1"
}

sincronizar_y_limpiar() {
    log "\e[1;35m[VOLCADO]\e[0m Sincronizando y fijando permisos..."
    
    local temp_json=$(mktemp)
    cp "$ARCHIVO_MAESTRO_JSON" "$temp_json"

    for hash in "${!URL_ORIGINAL[@]}"; do
        local url_id="${URL_ORIGINAL[$hash]}"
        local acc_c=${ACCESIBLES[$hash]:-0}
        local inacc_c=${INACCESIBLES[$hash]:-0}
        local url_viva=${ULTIMA_URL[$hash]}
        
        local hist=$(jq -r ".[] | select(.url_archivo == \"$url_id\") | \"\(.accesible)//\(.inaccesible)\"" "$temp_json" 2>/dev/null)
        local a_h=$(echo "$hist" | cut -d'/' -f1); [[ ! "$a_h" =~ ^[0-9]+$ ]] && a_h=0
        local i_h=$(echo "$hist" | cut -d'/' -f3); [[ ! "$i_h" =~ ^[0-9]+$ ]] && i_h=0

        local a_t=$((a_h + acc_c))
        local i_t=$((i_h + inacc_c))
        local sc=$(printf "scale=4; %d / (%d + %d + 0.0001)\n" "$a_t" "$a_t" "$i_t" | bc -l)
        
        local is_active=0; [[ $acc_c -gt 0 ]] && is_active=1

        local item=$(jq -n \
            --arg ca "${CANAL_NAME[$hash]}" --arg ur "$url_viva" --arg ua "$url_id" \
            --arg de "${CANAL_DESC[$hash]}" --arg xd "${CANAL_XDATA[$hash]}" \
            --arg sc "$sc" --arg ac "$a_t" --arg in "$i_t" \
            --arg act "$is_active" --arg ts "$(date +%s)" \
            '{canal: $ca, url_archivo: $ua, url: $ur, descripcion: $de, xdata: $xd, score: ($sc|tonumber), accesible: ($ac|tonumber), inaccesible: ($in|tonumber), active: ($act|tonumber), ultimo_check: ($ts|tonumber)}')

        local step_json=$(mktemp)
        jq "del(.[] | select(.url_archivo == \"$url_id\")) + [$item]" "$temp_json" > "$step_json" && mv "$step_json" "$temp_json"
    done

    # Mover al Maestro y FORZAR PERMISOS DE LECTURA
    mv "$temp_json" "$ARCHIVO_MAESTRO_JSON"
    chmod 644 "$ARCHIVO_MAESTRO_JSON"

    # --- GENERACIÓN DE ARCHIVOS DERIVADOS ---
    jq '[.[] | select(.active == 1)] | sort_by(.score) | reverse' "$ARCHIVO_MAESTRO_JSON" > "$JSON_ACTIVOS"
    jq '[.[] | select(.active == 0)]' "$ARCHIVO_MAESTRO_JSON" > "$JSON_INACTIVOS"
    jq -r '.[] | select(.active == 1) | "[canal:\"\(.canal)\",url:\"\(.url_archivo)\",descripcion:\"\(.descripcion)\",xdata:\"\(.xdata)\"]"' "$ARCHIVO_MAESTRO_JSON" > "$TXT_ACTIVOS"
    jq -r '.[] | select(.active == 0) | "[canal:\"\(.canal)\",url:\"\(.url_archivo)\",descripcion:\"\(.descripcion)\",xdata:\"\(.xdata)\"]"' "$ARCHIVO_MAESTRO_JSON" > "$TXT_INACTIVOS"

    # Asegurar permisos en todos los archivos generados
    chmod 644 "$JSON_ACTIVOS" "$JSON_INACTIVOS" "$TXT_ACTIVOS" "$TXT_INACTIVOS"

    # Limpiar RAM
    ACCESIBLES=(); INACCESIBLES=(); ULTIMA_URL=(); CANAL_NAME=(); CANAL_DESC=(); CANAL_XDATA=(); URL_ORIGINAL=()
    log "\e[1;32m[OK]\e[0m Persistencia completa con permisos 644."
}

ultimo_volcado=$(date +%s)

while true; do
    mapfile -t lineas < <(grep "url:" "$ARCHIVO_ENTRADA" | shuf)
    
    for linea in "${lineas[@]}"; do
        canal=$(echo "$linea" | sed -n 's/.*canal:"\([^"]*\)".*/\1/p')
        url_archivo=$(echo "$linea" | sed -n 's/.*url:"\([^"]*\)".*/\1/p')
        desc=$(echo "$linea" | sed -n 's/.*descripcion:"\([^"]*\)".*/\1/p')
        xdata=$(echo "$linea" | sed -n 's/.*xdata:"\([^"]*\)".*/\1/p')

        [[ -z "$url_archivo" ]] && continue
        h_id=$(echo -n "$url_archivo" | md5sum | cut -d' ' -f1)
        
        URL_ORIGINAL["$h_id"]="$url_archivo"
        CANAL_NAME["$h_id"]="$canal"
        CANAL_DESC["$h_id"]="$desc"
        CANAL_XDATA["$h_id"]="$xdata"

        log "Check: $canal"
        
# Primer intento con ffprobe y timeout de 30s
        if timeout 30s ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1 "$url_archivo" > /dev/null 2>&1; then
            ACCESIBLES["$h_id"]=$(( ${ACCESIBLES["$h_id"]:-0} + 1 ))
            ULTIMA_URL["$h_id"]="$url_archivo"
            log " -> \e[1;32mOK\e[0m"
        else
            # Intento de obtener nueva URL
            n_url=$(timeout 15s ./videourl.sh "$url_archivo")
            
            # Segundo intento con la nueva URL y timeout de 30s
            if [[ -n "$n_url" && "$n_url" != *"ERROR"* ]] && timeout 30s ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1 "$n_url" > /dev/null 2>&1; then
                ACCESIBLES["$h_id"]=$(( ${ACCESIBLES["$h_id"]:-0} + 1 ))
                ULTIMA_URL["$h_id"]="$n_url"
                log " -> \e[1;32mINY OK\e[0m"
            else
                INACCESIBLES["$h_id"]=$(( ${INACCESIBLES["$h_id"]:-0} + 1 ))
                ULTIMA_URL["$h_id"]="${ULTIMA_URL["$h_id"]:-$url_archivo}"
                log " -> \e[1;31mFAIL\e[0m"
            fi
        fi

        ahora=$(date +%s)
        if (( ahora - ultimo_volcado >= TIEMPO_ORDEN )); then
            sincronizar_y_limpiar
            ultimo_volcado=$(date +%s)
            break 
        fi
        sleep "$TIEMPO_MUESTREO"
    done
done
