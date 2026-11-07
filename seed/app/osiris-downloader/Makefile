# Osiris Downloader AI (C / SDL2) - make [release|debug|clean]
CC      ?= gcc
PKGS    := sdl2 SDL2_ttf
CFLAGS  += -std=gnu11 -Wall -Wextra -Wno-unused-parameter $(shell pkg-config --cflags $(PKGS))
LDLIBS  += $(shell pkg-config --libs $(PKGS)) -lpthread
SRC     := src/main.c src/core.c src/ui.c
BIN     := build/osiris-downloader

all: release
release: CFLAGS += -O2
release: $(BIN)
debug: CFLAGS += -O0 -g -fsanitize=address,undefined
debug: LDLIBS += -fsanitize=address,undefined
debug: $(BIN)

$(BIN): $(SRC) src/safe.h src/core.h src/ui.h
	@mkdir -p build
	$(CC) $(CFLAGS) $(SRC) $(LDLIBS) -o $@
	@echo "OK -> $(BIN)"

clean:
	rm -rf build
.PHONY: all release debug clean
