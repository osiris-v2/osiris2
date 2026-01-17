CC = gcc
CFLAGS = -Ofast -march=native -Wall -lpthread
SRC = src/main.c src/core/vm.c src/mem/rb_csp.c 
OBJ = $(SRC:.c=.o)
BIN = bin/osiris_node

all: $(BIN)

$(BIN): $(OBJ)
	@mkdir -p bin
	$(CC) $(CFLAGS) $(OBJ) -o $(BIN)
	@echo "[OK] Nodo Musculo listo en $(BIN)"

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf src/*.o src/**/*.o bin/
