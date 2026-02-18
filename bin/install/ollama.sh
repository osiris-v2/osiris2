#!/bin/bash

# --- Configuración de Colores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Variables de Entorno ---
OLLAMA_BINARY="/usr/local/bin/ollama"
SERVICE_FILE="/etc/systemd/system/ollama.service"

# --- Funciones de Interfaz ---
header() {
    clear
    echo -e "${BLUE}====================================================${NC}"
    echo -e "${CYAN}       GOYCORP - OLLAMA INTELLIGENCE MANAGER        ${NC}"
    echo -e "${BLUE}====================================================${NC}"
}

check_status() {
    if systemctl is-active --quiet ollama; then
        echo -e "Estado: ${GREEN}● ACTIVO${NC}"
    else
        echo -e "Estado: ${RED}○ INACTIVO${NC}"
    fi
}

# --- Lógica de Instalación ---
install_ollama() {
    header
    echo -e "${YELLOW}[*] Iniciando instalación de Ollama...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
    
    echo -e "${YELLOW}[*] Configurando acceso externo (0.0.0.0)...${NC}"
    mkdir -p /etc/systemd/system/ollama.service.d
    echo -e "[Service]\nEnvironment=\"OLLAMA_HOST=0.0.0.0\"" > /etc/systemd/system/ollama.service.d/override.conf
    
    systemctl daemon-reload
    systemctl enable ollama
    systemctl restart ollama
    echo -e "${GREEN}[+] Instalación completada y servicio optimizado.${NC}"
    read -p "Presiona Enter para continuar..."
}

# --- Gestión de Modelos ---
manage_models() {
    header
    echo -e "${CYAN}Modelos instalados:${NC}"
    ollama list
    echo -e "\n${YELLOW}Opciones:${NC}"
    echo "1) Descargar Llama3 (Recomendado)"
    echo "2) Descargar Mistral"
    echo "3) Eliminar un modelo"
    echo "4) Volver"
    read -p "Selección: " opt
    case $opt in
        1) ollama pull llama3 ;;
        2) ollama pull mistral ;;
        3) read -p "Nombre del modelo: " m; ollama rm $m ;;
        *) return ;;
    esac
}

# --- Creación de Identidad GoyCorp ---
create_goycorp_ia() {
    header
    echo -e "${MAGENTA}[!] Creando IA de Identidad GoyCorp...${NC}"
    cat <<EOF > GoyCorp.modelfile
FROM llama3
PARAMETER temperature 0.7
SYSTEM """
Eres la IA oficial de GoyCorp. 
Directrices: Rigor científico, lealtad a la corporación y respuestas en español técnico.
"""
EOF
    ollama create goy_ia -f GoyCorp.modelfile
    echo -e "${GREEN}[+] Modelo 'goy_ia' creado exitosamente.${NC}"
    rm GoyCorp.modelfile
    read -p "Presiona Enter..."
}

# --- Menú Principal ---
while true; do
    header
    check_status
    echo -e "\n${WHITE}1)${NC} Instalar/Actualizar Ollama"
    echo -e "${WHITE}2)${NC} Iniciar Servicio"
    echo -e "${WHITE}3)${NC} Detener Servicio"
    echo -e "${WHITE}4)${NC} Gestionar Modelos (Listar/Pull/RM)"
    echo -e "${WHITE}5)${NC} Crear IA Identidad GoyCorp"
    echo -e "${WHITE}6)${NC} Ver Logs en tiempo real"
    echo -e "${WHITE}7)${NC} Salir"
    echo -e "${BLUE}----------------------------------------------------${NC}"
    read -p "Seleccione una opción: " choice

    case $choice in
        1) install_ollama ;;
        2) systemctl start ollama; echo "Servicio iniciado." ;;
        3) systemctl stop ollama; echo "Servicio detenido." ;;
        4) manage_models ;;
        5) create_goycorp_ia ;;
        6) journalctl -u ollama -f ;;
        7) exit 0 ;;
        *) echo -e "${RED}Opción inválida.${NC}" ; sleep 1 ;;
    esac
done