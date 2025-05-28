#!/bin/bash
# osiris_tmux.sh - The main script for setting up the tmux session

script_dir=$(dirname "$(readlink -f "$0")")
cd "$script_dir" # Changed from 'cd $script_dir' for robustness

source '/etc/environment'
source ../com/osiris_env/bin/activate

# These variables can be overridden by environment variables passed from osiris2load.sh
SESSION_NAME="${SESSION_NAME:-my_tmux_session_$(date +%s)}"
COMMAND_PANEL0="${COMMAND_PANEL0:-clear && reset && clear && cd ../../ && bash ./osiris}"
COMMAND_PANEL1="${COMMAND_PANEL1:-clear && reset && clear && ./server.run}"
COMMAND_PANEL2="${COMMAND_PANEL2:-clear && reset && clear && ./client.run}"
COMMAND_PANEL3="${COMMAND_PANEL3:-cd .. && clear && reset && clear && sudo ./osiris_run}"
COMMAND_PANEL4="${COMMAND_PANEL4:-clear && reset && clear && sudo ./freemem2}"
COMMAND_PANEL5="${COMMAND_PANEL5:-cd .. && clear && reset && clear && ./pilottv}"
COMMAND_PANEL6="${COMMAND_PANEL6:-cd .. && clear && reset && clear && sudo ./OPS/ops}"
COMMAND_PANEL7="${COMMAND_PANEL7:-clear && reset && clear && ./progress_tv}"
COMMAND_PANEL8="${COMMAND_PANEL8:-clear && reset && clear && ./progress_hls}"


# Función para limpiar la sesión tmux al finalizar
limpiar_tmux() {
  echo "SALIENDO..."
  if tmux has-session -t "$SESSION_NAME" > /dev/null 2>&1; then
    echo "Limpiando sesión tmux '$SESSION_NAME'..."
    tmux kill-session -t "$SESSION_NAME" || \
      handle_error "Error al matar la sesión tmux: $?"
  fi
  echo "...SALIENDO..."
}

# Manejo de errores centralizado
handle_error() {
  local message="$1"
  echo "$(date) - ERROR: $message" >> "/var/log/tmux_session.log"
  # Aquí puedes agregar acciones adicionales de manejo de errores, como enviar notificaciones por correo electrónico
}


# Crear una nueva sesión de tmux
tmux new-session -d -s "$SESSION_NAME" -n osiris_tmux

# GRUPO IZQUIERDO
# Dividir verticalmente en dos columnas principales (izquierda/derecha)
tmux split-window -h -t "$SESSION_NAME:0.0" -p 66

# Dividir la columna izquierda (server y client arriba, osiris abajo)
tmux split-window -v -t "$SESSION_NAME:0.0" -p 50    # Crear fila superior e inferior
tmux split-window -h -t "$SESSION_NAME:0.0" -p 50    # Dividir fila superior (server y client)

tmux send-keys -t "$SESSION_NAME:0.0" "$COMMAND_PANEL1" C-m  # server
tmux send-keys -t "$SESSION_NAME:0.1" "$COMMAND_PANEL2" C-m  # client
tmux send-keys -t "$SESSION_NAME:0.2" "$COMMAND_PANEL0" C-m  # osiris

# GRUPO DERECHO
# Dividir la columna derecha en tres filas (osiris_run, pilottv+freemem, otvs+progress)
tmux split-window -v -t "$SESSION_NAME:0.3" -p 33    # Crear fila superior (osiris_run)
tmux split-window -v -t "$SESSION_NAME:0.4" -p 50    # Crear fila intermedia

# Configurar osiris_run en la fila superior derecha
tmux send-keys -t "$SESSION_NAME:0.3" "$COMMAND_PANEL3" C-m

# Dividir fila intermedia (pilottv y freemem)
tmux split-window -h -t "$SESSION_NAME:0.4" -p 50
tmux send-keys -t "$SESSION_NAME:0.4" "$COMMAND_PANEL5" C-m  # pilottv
tmux send-keys -t "$SESSION_NAME:0.5" "$COMMAND_PANEL4" C-m  # freemem

# Dividir la fila inferior (otvs, progress_tv, progress_hls)
tmux split-window -h -t "$SESSION_NAME:0.6" -p 50    # Dividir fila inferior (ods )
tmux split-window -v -t "$SESSION_NAME:0.7" -p 50    # Dividir fila inferior en dos columnas (progress_tv, progress_hls)


tmux send-keys -t "$SESSION_NAME:0.6" "$COMMAND_PANEL6" C-m  # otvs
tmux send-keys -t "$SESSION_NAME:0.7" "$COMMAND_PANEL7" C-m  # progress_tv
tmux send-keys -t "$SESSION_NAME:0.8" "$COMMAND_PANEL8" C-m  # progress_hls


# Habilitar el modo ratón y adjuntar la sesión
tmux set-option -t "$SESSION_NAME" mouse on
tmux attach-session -t "$SESSION_NAME"


# Capturar las señales SIGINT (Ctrl+C) y SIGTERM (kill) para ejecutar la limpieza
XPID=$$
echo "program PID ${XPID}"

trap 'limpiar_tmux; kill -9 ${XPID}; exit 0' INT TERM EXIT

# Mantener el script ejecutandose (esto es importante para que la trampa funcione)
wait