#!/bin/bash
# OSIRIS V2 - INYECTOR MULTIMEDIA SOBERANO
# SINTAXIS: FGN (ASCII PURO)

cd cerebro_semilla/target/release

URL_ENTRADA=$1

if [ -z "$URL_ENTRADA" ]; then
    echo "ERROR: DEBE PROPORCIONAR UNA URL."
    echo "USO: ./inyector_soberano.sh https://www.youtube.com/watch?v=XXXX"
    exit 1
fi

echo "[OSIRIS] EXRAYENDO STREAM PARA ESTRATO URANIO..."

# --- OPCIONES DE EXTRACCION (DESCOMENTAR SOLO UNA PARA PROBAR) ---

# OPCION 1: EL FILTRO "18" (El mas rapido y compatible, MP4 directo 360p, evita SABR)
#URL_DIRECTA=$(yt-dlp --get-url -f 18 --no-warnings "${URL_ENTRADA}")

# OPCION 1.1: (Use cookies from nrowser, MP4 directo 360p, evita SABR)
#URL_DIRECTA=$(yt-dlp --get-url --no-warnings --cookies-from-browser firefox "${URL_ENTRADA}")


# OPCION 2: COMPATIBILIDAD ANDROID/IOS (Salta el error de JS Runtime y SABR)
# URL_DIRECTA=$(yt-dlp --get-url --extractor-args "youtube:player_client=android,ios" -f "best[ext=mp4]" --no-warnings "${URL_ENTRADA}")

# OPCION 3: BUSQUEDA GENERICA MP4 (Tu comando original con limpieza de avisos)
URL_DIRECTA=$(yt-dlp --get-url --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" --referer "https://www.google.com/" -f "best[ext=mp4]/best" --no-warnings "${URL_ENTRADA}")

# OPCION 4: EXTRACCION TOTAL (Mejor MP4 disponible, requiere que el sistema tenga algun JS basico)
# URL_DIRECTA=$(yt-dlp --get-url -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --no-warnings "${URL_ENTRADA}")

# --- EJECUCION HACIA EL CEREBRO ---

echo $URL_DIRECTA

if [ -n "$URL_DIRECTA" ]; then
    echo "[OSIRIS] URL OBTENIDA. INYECTANDO EN CEREBRO_SEMILLA..."
    # Se pasa la URL como argumento al binario de la plataforma
    ./cerebro_semilla "$URL_DIRECTA"
else
    echo "[OSIRIS] ERROR: NO SE PUDO OBTENER LA URL DIRECTA."
    exit 1
fi

echo "[OSIRIS] FLUJO FINALIZADO."