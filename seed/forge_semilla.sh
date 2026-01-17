#!/bin/bash

# --- PROYECTO SEMILLA: SCRIPT DE FORJA ---

# Colores para la terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- INICIANDO FORJA DE ESTRUCTURA PROYECTO SEMILLA ---${NC}"

# Lista de directorios a crear
DIRS=(
    "nodo_musculo/src/core"
    "nodo_musculo/src/mem"
    "nodo_musculo/src/net"
    "nodo_musculo/src/video"
    "nodo_musculo/bin"
    "cerebro_semilla/src/network"
    "cerebro_semilla/src/security"
    "cerebro_semilla/src/controller"
    "logs"
)

# 1. Creacion de Directorios
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${YELLOW}[AVISO]${NC} El directorio '$dir' ya existe. Saltando..."
    else
        mkdir -p "$dir"
        echo -e "${GREEN}[OK]${NC} Directorio '$dir' creado."
    fi
done

# 2. Creacion de Archivos Base (Vacios si no existen)
FILES=(
    "Makefile"
    "launch_osiris.sh"
    "nodo_musculo/Makefile"
    "nodo_musculo/src/main.c"
    "nodo_musculo/src/core/vm.c"
    "nodo_musculo/src/core/vm.h"
    "nodo_musculo/src/mem/rb_csp.c"
    "nodo_musculo/src/mem/rb_csp.h"
    "nodo_musculo/src/net/protocol.h"
    "nodo_musculo/src/net/seed_client.c"
    "nodo_musculo/src/video/ffmpeg_bridge.c"
    "cerebro_semilla/Cargo.toml"
    "cerebro_semilla/src/main.rs"
    "cerebro_semilla/src/network/protocol.rs"
    "cerebro_semilla/src/security/signer.rs"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}[AVISO]${NC} El archivo '$file' ya existe. Protegiendo contenido..."
    else
        touch "$file"
        echo -e "${GREEN}[OK]${NC} Archivo '$file' forjado."
    fi
done

echo -e "${GREEN}--- FORJA COMPLETADA CON EXITO ---${NC}"
