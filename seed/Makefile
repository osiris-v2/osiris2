# --- RUTAS ABSOLUTAS ---
ROOT_DIR    := $(shell pwd)
NODO_DIR    := $(ROOT_DIR)/nodo_musculo
CEREBRO_DIR := $(ROOT_DIR)/cerebro_semilla

# Binarios finales
BIN_NODO    := $(NODO_DIR)/bin/osiris_node
BIN_CEREBRO := $(CEREBRO_DIR)/target/release/cerebro_semilla
CARGO       := /root/.cargo/bin/cargo

# --- CONFIGURACION DE EJECUCION ---
VIDEO_URL   ?= "https://www.w3schools.com/html/mov_bbb.mp4" # URL por defecto

# --- COMPILADOR Y FLAGS ---
CC          := gcc
CFLAGS      := -I$(NODO_DIR)/include -Wall -Wextra -Wno-override-init
LDFLAGS     := -lpthread -lm -lSDL2 -lGL

# --- FUENTES DEL NODO ---
SRC_NODO    := $(NODO_DIR)/src/main.c \
               $(NODO_DIR)/src/core/vm.c \
               $(NODO_DIR)/src/mem/rb_csp.c \
               $(NODO_DIR)/src/uranio_safe.c \
               $(NODO_DIR)/src/drivers/hw_probe.c \
               $(NODO_DIR)/src/drivers/sdl_core.c \
               $(NODO_DIR)/src/drivers/net_probe.c \
               $(NODO_DIR)/src/core/fgn_runtime.c \
       		   $(NODO_DIR)/src/core/dispatcher.c

# --- COLORES ---
GREEN  := \033[0;32m
YELLOW := \033[1;33m
CYAN   := \033[0;36m
NC     := \033[0m

.PHONY: all nodo cerebro clean setup run_semilla run_nodo

all: setup cerebro nodo
	@echo "\n$(GREEN)>>> PROYECTO OSIRIS: SISTEMA Y DRIVERS CONSOLIDADOS <<<$(NC)"

setup:
	@mkdir -p logs
	@mkdir -p $(NODO_DIR)/bin

cerebro:
	@echo "$(YELLOW)[FORJA] Compilando Cerebro (Rust)...$(NC)"
	@cd $(CEREBRO_DIR) && $(CARGO) build --release

nodo:
	@echo "$(YELLOW)[FORJA] Compilando Nodo Musculo con Sondas de Hardware...$(NC)"
	@$(CC) $(SRC_NODO) -o $(BIN_NODO) $(CFLAGS) $(LDFLAGS)
	@echo "$(GREEN)[OK] Binario generado en: $(BIN_NODO)$(NC)"

# --- COMANDOS DE EJECUCION ---

run_semilla:
	@echo "$(CYAN)[EJECUCION] Iniciando Cerebro Semilla (Servidor)...$(NC)"
	@$(BIN_CEREBRO) $(VIDEO_URL)

run_nodo:
	@echo "$(CYAN)[EJECUCION] Iniciando Nodo Musculo (Cliente)...$(NC)"
	@$(BIN_NODO)

clean:
	@echo "$(YELLOW)[LIMPIEZA] Eliminando rastros de carbono...$(NC)"
	@rm -rf $(NODO_DIR)/bin
	@rm -rf $(CEREBRO_DIR)/target
	@rm -f logs/*.loghhhh