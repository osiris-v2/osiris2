# --- RUTAS ABSOLUTAS ---
ROOT_DIR    := $(shell pwd)
NODO_DIR    := $(ROOT_DIR)/nodo_musculo
CEREBRO_DIR := $(ROOT_DIR)/cerebro_semilla

BIN_NODO    := $(NODO_DIR)/bin/osiris_node
BIN_CEREBRO := $(CEREBRO_DIR)/target/release/cerebro_semilla
CARGO       := /root/.cargo/bin/cargo


# --- CONFIGURACION DE EJECUCION ---
VIDEO_URL ?= "https://www.w3schools.com/html/mov_bbb.mp4"
CYAN := \033[0;36m

# --- CONFIGURACION ---
CC      := gcc
# --- FLAGS ---
#CFLAGS  := -I$(NODO_DIR)/include -Wall -Wextra -Wno-override-init -O2 -D_GNU_SOURCE -DCONFIG_VERSION=\"$(shell cat $(NODO_DIR)/include/VERSION)\"
#CFLAGS := -I$(NODO_DIR)/include -Wall -Wno-unused-parameter -Wno-implicit-fallthrough -Wno-override-init -O2 -D_GNU_SOURCE -DCONFIG_VERSION=\"$(shell cat $(NODO_DIR)/include/VERSION)\"
CFLAGS := -I$(NODO_DIR)/include -Wall -Wno-unused-parameter -Wno-implicit-fallthrough -O2 -D_GNU_SOURCE -fcommon -DCONFIG_VERSION=\"$(shell cat $(NODO_DIR)/include/VERSION)\"
LDFLAGS := -lpthread -lm -lSDL2 -lGL -ldl

# --- FUENTES DEL NODO (TRASPLANTE COMPLETADO) ---
SRC_NODO := $(NODO_DIR)/src/main.c \
            $(NODO_DIR)/src/core/vm.c \
            $(NODO_DIR)/src/mem/rb_csp.c \
            $(NODO_DIR)/src/uranio_safe.c \
            $(NODO_DIR)/src/drivers/hw_probe.c \
            $(NODO_DIR)/src/drivers/sdl_core.c \
            $(NODO_DIR)/src/drivers/net_probe.c \
            $(NODO_DIR)/src/core/fgn_runtime.c \
            $(NODO_DIR)/src/core/dispatcher.c \
            $(NODO_DIR)/src/drivers/acero_loader.c \
            $(NODO_DIR)/src/drivers/acero_gl_legacy.c \
            $(NODO_DIR)/src/drivers/osiris_js_bridge.c \
            $(NODO_DIR)/src/drivers/cutils.c \
            $(NODO_DIR)/src/drivers/dtoa.c \
            $(NODO_DIR)/src/drivers/libregexp.c \
            $(NODO_DIR)/src/drivers/libunicode.c \
            $(NODO_DIR)/src/math/fgn_math.c \
            $(NODO_DIR)/src/drivers/quickjs.c 

# --- COLORES ---
GREEN  := \033[0;32m
YELLOW := \033[1;33m
NC     := \033[0m

.PHONY: all nodo cerebro clean setup

all: setup cerebro nodo
	@echo "\n$(GREEN)>>> PROYECTO OSIRIS: SISTEMA Y DRIVERS CONSOLIDADOS <<<$(NC)"

setup:
	@mkdir -p logs
	@mkdir -p $(NODO_DIR)/bin

cerebro:
	@echo "$(YELLOW)[FORJA] Compilando Cerebro (Rust)...$(NC)"
	@cd $(CEREBRO_DIR) && $(CARGO) build --release

nodo:
	@echo "[FORJA] Compilando Nodo Musculo con QuickJS 2025 Local..."
	$(CC) $(SRC_NODO) -o $(BIN_NODO) $(CFLAGS) $(LDFLAGS)
	@echo "[OK] Acero templado. Binario en $(BIN_NODO)"


clean:
	@echo "$(YELLOW)[LIMPIEZA] Eliminando rastros de carbono...$(NC)"
	@rm -rf $(NODO_DIR)/bin
	@rm -rf $(CEREBRO_DIR)/target
	@rm -f logs/*.log







#RUNS
run_semilla:
	@echo "$(CYAN)[EJECUCION] Iniciando Cerebro Semilla (Servidor Rust)...$(NC)"
	@# Ejecutamos el binario de Rust pasando la URL del video
	@$(BIN_CEREBRO) $(VIDEO_URL)

run_nodo:
	@echo "$(CYAN)[EJECUCION] Iniciando Nodo Musculo (Cliente C/JS)...$(NC)"
	@# Ejecutamos el nodo. Asegurate de que el Cerebro este corriendo antes.
	@$(BIN_NODO)
