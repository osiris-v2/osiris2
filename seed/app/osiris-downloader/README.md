# Osiris Downloader AI (C puro + SDL2)

Gestor gráfico de descargas sobre **yt-dlp**, escrito en C (GNU C11), sin C++ ni Dear ImGui.

- Ventana SDL2 + mini-GUI propia de modo inmediato (`src/ui.c`), texto con SDL2_ttf.
- Memoria segura (`src/safe.h`): `safe_ptr`, `safe_free`, `SAFE_MOVE`, `SBuf`.
- Computed gotos en el despacho de eventos (`main.c`) y en el analizador de la salida de yt-dlp (`core.c`).
- Una hebra por descarga; yt-dlp se lanza con `posix_spawnp` (sin shell, sin inyección) y se cancela matando su grupo de procesos.

## Compilar
    ./install-deps.sh     # opcional: instala SDL2, SDL2_ttf, yt-dlp
    ./build.sh            # o: make   /   cmake -S . -B build && cmake --build build
    ./build/osiris-downloader

Plataformas: Linux y macOS (POSIX). En Windows: usar WSL2 o MSYS2 (ver manual).
Manual completo: abre `manual/index.html` en el navegador.
