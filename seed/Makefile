# --- RUTAS ABSOLUTAS ---
ROOT_DIR    := $(shell pwd)
NODO_DIR    := $(ROOT_DIR)/nodo_musculo
CEREBRO_DIR := $(ROOT_DIR)/cerebro_semilla

BIN_NODO    := $(NODO_DIR)/bin/osiris_node
BIN_CEREBRO := $(CEREBRO_DIR)/target/release/cerebro_semilla
BIN_ODS     := $(NODO_DIR)/bin/ods_engine
BIN_MONITOR := $(NODO_DIR)/bin/monitor
BIN_SPIDERBOT := $(NODO_DIR)/bin/spiderbot
CARGO       := /root/.cargo/bin/cargo

# --- CONFIGURACION DE EJECUCION ---
VIDEO_URL ?= "https://www.w3schools.com/html/mov_bbb.mp4"

# --- COLORES ---
GREEN  := \033[0;32m
YELLOW := \033[1;33m
CYAN   := \033[0;36m
NC     := \033[0m

# --- CONFIGURACION COMPILADOR ---
CC     := gcc
CFLAGS := -I$(NODO_DIR)/include -Wall -Wno-unused-parameter -Wno-implicit-fallthrough -O2 -D_GNU_SOURCE -fcommon -DCONFIG_VERSION=\"$(shell cat $(NODO_DIR)/include/VERSION 2>/dev/null || echo 1.0)\"
LDFLAGS_NODO := -lpthread -lm -lSDL2 -lGL -ldl
LDFLAGS_ODS  := -lreadline 

# --- FUENTES DEL NODO ---
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
            $(NODO_DIR)/src/drivers/osiris_windows.c \
            $(NODO_DIR)/src/drivers/osiris_js_bridge.c \
            $(NODO_DIR)/src/drivers/cutils.c \
            $(NODO_DIR)/src/drivers/dtoa.c \
            $(NODO_DIR)/src/drivers/libregexp.c \
            $(NODO_DIR)/src/drivers/libunicode.c \
            $(NODO_DIR)/src/math/fgn_math.c \
            $(NODO_DIR)/src/drivers/pta_engine.c  \
            $(NODO_DIR)/src/drivers/quickjs.c \
            $(NODO_DIR)/src/drivers/fgn_ai_core.c 

# --- FUENTES ODS ENGINE ---
SRC_ODS := $(NODO_DIR)/src/core/ods_memoria.c \
           $(NODO_DIR)/src/core/ods_ejecutor.c \
           $(NODO_DIR)/src/core/ods_entrada.c \
           $(NODO_DIR)/src/core/ods_main.c \
           $(NODO_DIR)/src/drivers/ods_red.c

# --- REGLAS PRINCIPALES ---
.PHONY: all nodo cerebro ods monitor clean setup run_semilla run_nodo run_ods run_monitor

all: setup cerebro nodo ods monitor
	@echo "\n$(GREEN)>>> PROYECTO OSIRIS: ECOSISTEMA Y DRIVERS CONSOLIDADOS <<<$(NC)"

setup:
	@mkdir -p logs
	@mkdir -p $(NODO_DIR)/bin

# --- COMPILACION ---

cerebro:
	@echo "$(YELLOW)[FORJA] Compilando Cerebro (Rust)...$(NC)"
	@cd $(CEREBRO_DIR) && $(CARGO) build --release

nodo: setup
	@echo "$(YELLOW)[FORJA] Compilando Nodo Musculo con QuickJS Local...$(NC)"
	$(CC) $(SRC_NODO) -o $(BIN_NODO) $(CFLAGS) $(LDFLAGS_NODO)
	@echo "$(GREEN)[OK] Nodo Osiris templado en $(BIN_NODO)$(NC)"

ods: setup
	@echo "$(YELLOW)[FORJA] Compilando Motor ODS (Engine)...$(NC)"
	$(CC) $(SRC_ODS) -o $(BIN_ODS) $(CFLAGS)  $(LDFLAGS_ODS)
	@echo "$(GREEN)[OK] ODS Engine forjado en $(BIN_ODS)$(NC)"

monitor: setup
	@echo "$(YELLOW)[FORJA] Compilando Monitor de Fase...$(NC)"
	$(CC) $(NODO_DIR)/util/monitor.c -o $(BIN_MONITOR) -lncurses
	@echo "$(GREEN)[OK] Monitor listo en $(BIN_MONITOR)$(NC)"


spiderbot: setup
	@echo "$(YELLOW)[FORJA] Compilando Monitor de Fase...$(NC)"
	$(CC) $(NODO_DIR)/util/spiderbot.c -o $(BIN_SPIDERBOT) -lncurses -lcurl -lsqlite3
	@echo "$(GREEN)[OK] SpiderBot listo en $(BIN_SPIDERBOT)$(NC)"


# --- EJECUCION ---

run_semilla:
	@echo "$(CYAN)[EJECUCION] Iniciando Cerebro Semilla...$(NC)"
	@$(BIN_CEREBRO) $(VIDEO_URL)

run_nodo:
	@echo "$(CYAN)[EJECUCION] Iniciando Nodo Musculo...$(NC)"
	@$(BIN_NODO)

run_ods:
	@echo "$(CYAN)[EJECUCION] Iniciando Engine ODS...$(NC)"
	@$(BIN_ODS)

run_monitor:
	@echo "$(CYAN)[EJECUCION] Lanzando Monitor de Fase...$(NC)"
	@$(BIN_MONITOR)


run_spiderbot:
	@echo "$(CYAN)[EJECUCION] Lanzando Monitor de Fase...$(NC)"
	@$(BIN_SPIDERBOT)



clean:
	@echo "$(YELLOW)[LIMPIEZA] Eliminando rastros de carbono...$(NC)"
	@rm -rf $(NODO_DIR)/bin/*
	@rm -rf $(CEREBRO_DIR)/target
	@rm -f logs/*.log