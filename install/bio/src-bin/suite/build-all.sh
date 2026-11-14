#!/usr/bin/env bash
# Compila y prueba toda la suite.
set -e
cd "$(dirname "$0")"
echo "== Librería: tests =="; (cd share-lib-sdl-c && make test && make lib)
echo "== Lanzador ==";        (cd osiris-launcher-c && make test && make release)
echo "== Reproductor ==";     (cd osiris-player-c && ./build.sh)
echo "== Descargador ==";     (cd osiris-downloader-c && ./build.sh)
echo; echo "Listo:"; ls -1 osiris-launcher-c/build/osiris-launcher osiris-player-c/build/osiris-player osiris-downloader-c/build/osiris-downloader
