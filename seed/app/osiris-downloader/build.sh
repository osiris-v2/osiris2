#!/usr/bin/env bash
# Compila con make (o cmake si make no existe). Funciona desde cualquier directorio.
set -e
cd "$(dirname "$0")"
if command -v make >/dev/null; then make release
else cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build && mkdir -p build && cp build/bin/osiris-downloader build/; fi
echo; echo "Ejecuta: ./build/osiris-downloader"
