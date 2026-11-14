# Osiris Suite (C + SDL2)

| Carpeta | Qué es |
|---|---|
| `share-lib-sdl-c/` | Librería compartida `osl_*` **v0.2**: memoria segura, JSON, ficheros, procesos, fuentes, GUI SDL2, gráficos y diálogos. Docs (incluye **manual técnico** y referencia): `share-lib-sdl-c/docs/index.html` |
| `share-fonts/` | Fuentes TTF compartidas (DejaVu incluida) + `fonts-sync.sh` para buscar en el sistema o descargar |
| `osiris-launcher-c/` | **Lanzador de programas** (usa la librería). Manual: `osiris-launcher-c/manual/index.html` |
| `osiris-player-c/` | **Reproductor FFmpeg + SDL2** con opciones de red, yt-dlp y probador de enlaces (usa la librería). Manual: `osiris-player-c/manual/index.html` |
| `osiris-downloader-c/` | Descargador sobre yt-dlp (versión autónoma; migración a `osl` descrita en la doc de la librería) |

## Compilar
    ./install-deps.sh        # SDL2, SDL2_ttf, SDL2_image (iconos), yt-dlp... (Debian/Ubuntu, Fedora, Arch, macOS)
    ./build-all.sh           # tests + librería + lanzador + reproductor + descargador
    # pruebas completas del reproductor (necesita ffmpeg y python3; ~3 min): ./osiris-player-c/tests/run-tests.sh
    ./osiris-launcher-c/build/osiris-launcher

Cada programa también se compila por separado (`cd osiris-launcher-c && ./build.sh`).
**Mantén las carpetas juntas**: los programas usan `../share-lib-sdl-c` y `../share-fonts`.
