#!/bin/bash

# Rutas de binarios
BIN_C="./nodo_musculo/bin/osiris_node"
BIN_RUST="./cerebro_semilla/target/release/cerebro_semilla"

echo "--- INICIANDO SISTEMA DUAL PROYECTO SEMILLA ---"

# 1. Lanzar el Nodo (C) en SEGUNDO PLANO primero
# Redirigimos su salida al log para que no ensucie la consola
$BIN_C > ./logs/node.log 2>&1 &
NODE_PID=$!

echo "[OK] Nodo Músculo (C) iniciado en el fondo (PID: $NODE_PID)"
sleep 1

# 2. Lanzar el Cerebro (Rust) en PRIMER PLANO
# Esto permite que el loop de "read_line" capture tu teclado correctamente
echo "[OK] Iniciando Consola de Mando (Rust)..."
echo "------------------------------------------"
$BIN_RUST

# Al salir de Rust (comando 'exit'), limpiamos el nodo
kill $NODE_PID
echo "--- SISTEMA APAGADO ---"