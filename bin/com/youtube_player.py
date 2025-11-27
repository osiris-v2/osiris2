import sys
import os
import subprocess
import re

def print_help():
    print("""Uso: python3 lib/youtube_player.py <youtube_url> [--user <username>] [--uid <userid>] [--display <display_value>] [--screen <screen_index>]
       --helpme                    Muestra esta ayuda.
       <youtube_url>             La URL del video de YouTube a reproducir.
Opciones avanzadas (si la detección automática falla):
       --user <username>         Especifica el nombre de usuario gráfico (ej. 'osirisuser').
       --uid <userid>            Especifica el UID del usuario gráfico (ej. '1000').
       --display <value>         Fuerza un valor de DISPLAY (ej. ':0', ':1').
       --screen <index>          Fuerza un índice de pantalla para mpv (ej. '0', '1').

Este script intenta reproducir un video de YouTube usando mpv, detectando automáticamente la configuración de pantalla y audio del usuario que inició la sesión gráfica, incluso cuando se ejecuta con sudo.
Asegúrate de tener 'yt-dlp' y 'mpv' instalados.""")

def detect_screen_config(target_user, target_uid, force_display=None, force_screen_index=None):
    """
    Intenta detectar la configuración de pantalla (DISPLAY y mpv --screen index)
    para el usuario objetivo.
    """
    detected_display = ""
    final_mpv_screen_index = str(force_screen_index) if force_screen_index is not None else "0"

    print(f"--- Iniciando Detección y Análisis de Pantallas para usuario '{target_user}' (UID: {target_uid}) ---")

    possible_displays = [":0", ":1"] # Common DISPLAY values to try
    if force_display:
        # Prioritize force_display, add if not already in possible_displays
        if force_display not in possible_displays:
            possible_displays.insert(0, force_display)
        else: # Move to front if already exists
            possible_displays.remove(force_display)
            possible_displays.insert(0, force_display)

    for d_candidate in possible_displays:
        print(f"INFO: Intentando ejecutar xrandr en DISPLAY={d_candidate} como usuario {target_user}...")
        try:
            xrandr_cmd = [
                "sudo", "-u", target_user,
                "DISPLAY=" + d_candidate,
                "xrandr"
            ]
            process = subprocess.run(xrandr_cmd, capture_output=True, text=True, check=False)
            xrandr_output = process.stdout + process.stderr
            xrandr_status = process.returncode

            if xrandr_status == 0:
                print(f"✅ xrandr exit status: {xrandr_status} para DISPLAY={d_candidate}")
                print(f"--- Salida COMPLETA de xrandr para DISPLAY={d_candidate} ---")
                print(xrandr_output)
                print("--- Fin de salida xrandr ---")

                connected_outputs = []
                for line in xrandr_output.splitlines():
                    if " connected" in line:
                        match = re.search(r"^\s*(\S+)\s+connected", line)
                        if match:
                            connected_outputs.append(match.group(1))

                # Logic to find HDMI-0 index (based on user's previous output where HDMI-0 was index 1)
                if "HDMI-0" in connected_outputs:
                    try:
                        detected_index = connected_outputs.index("HDMI-0")
                        final_mpv_screen_index = str(detected_index)
                        print(f"INFO: ✔️ Índice de pantalla HDMI ('HDMI-0') para mpv determinado como: {final_mpv_screen_index} (basado en el orden de 'connected' en xrandr).")
                        detected_display = d_candidate
                        break # Found the HDMI screen, break from loop
                    except ValueError:
                        pass

                elif detected_display == "" and " primary" in xrandr_output:
                    # Check if the primary display is connected in this DISPLAY
                    if any(" connected primary" in line for line in xrandr_output.splitlines()):
                        detected_display = d_candidate
                        print(f"INFO: ✨ Pantalla primaria detectada en DISPLAY={detected_display}. Priorizando este DISPLAY.")
                        if "HDMI" in xrandr_output:
                            print("INFO: 📺 Salida HDMI detectada en la pantalla primaria.")
                        
                        # Attempt to infer screen index for the primary display
                        for idx, output_name in enumerate(connected_outputs):
                            if f"{output_name} connected primary" in xrandr_output: # More robust check
                                final_mpv_screen_index = str(idx)
                                print(f"INFO: Inferido índice de pantalla principal: {final_mpv_screen_index}")
                                break
                        break

                elif detected_display == "":
                    if connected_outputs:
                        detected_display = d_candidate
                        print(f"INFO: 🖥️ Pantalla conectada detectada en DISPLAY={detected_display}. Usando como alternativa.")

            else:
                print(f"❌ WARNING: xrandr falló en DISPLAY={d_candidate}. Status: {xrandr_status}. Mensaje: {xrandr_output.strip()}")

        except FileNotFoundError:
            print(f"ERROR: El comando 'xrandr' no se encontró para el usuario '{target_user}'. Asegúrate de que esté en el PATH o que el usuario tenga permisos.")
            break
        except Exception as e:
            print(f"ERROR inesperado al ejecutar xrandr: {e}")
            break
    
    if force_display:
        print(f"INFO: Usando DISPLAY forzado por el usuario: {force_display}")
        final_display = force_display
    elif detected_display:
        final_display = detected_display
        print(f"INFO: ✔️ Utilizando DISPLAY determinado para mpv: {final_display}")
    else:
        print("⚠️ WARNING: No se pudo detectar una pantalla activa. Usando DISPLAY ':1' como fallback.")
        final_display = ":1"

    if force_screen_index is not None:
        final_mpv_screen_index = str(force_screen_index)
        print(f"INFO: Usando índice de pantalla forzado por el usuario: {final_mpv_screen_index}")
    
    return final_display, final_mpv_screen_index

def play_video(youtube_url, target_user, target_uid, display, screen_index):
    """
    Reproduce el video de YouTube usando yt-dlp y mpv.
    """
    print("--- Resumen de Configuración de Reproducción ---")
    print(f"URL: {youtube_url}")
    print(f"Reproduciendo como usuario: {target_user} (UID: {target_uid})")
    print(f"DISPLAY para mpv: {display}")
    print(f"mpv --screen={screen_index}")

    xdg_runtime_dir = f"/run/user/{target_uid}"
    pulse_server = f"{xdg_runtime_dir}/pulse/native"

    print("Extrayendo URL de stream directo con yt-dlp -f best...")
    try:
        yt_dlp_cmd = ["yt-dlp", "-f", "best", "--get-url", youtube_url]
        process = subprocess.run(yt_dlp_cmd, capture_output=True, text=True, check=True)
        video_stream_url = process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Falló la extracción de la URL del stream de video con yt-dlp. Código de error: {e.returncode}. Mensaje: {e.stderr.strip()}")
        return
    except FileNotFoundError:
        print("ERROR: El comando 'yt-dlp' no se encontró. Asegúrate de que esté instalado y en tu PATH.")
        return
    
    if not video_stream_url:
        print("ERROR: yt-dlp no devolvió una URL de stream válida.")
        return
    print("URL de stream directo obtenida.")

    print(f"Lanzando mpv en pantalla detectada (DISPLAY={display}, --screen={screen_index})...")
    
    mpv_cmd = [
        "sudo", "-u", target_user,
        "env",
        f"DISPLAY={display}",
        f"XDG_RUNTIME_DIR={xdg_runtime_dir}",
        f"PULSE_SERVER={pulse_server}",
        "mpv",
        "--no-terminal", "--fs", "--autofit=100%",
	"--ontop",
        f"--screen={screen_index}",
        video_stream_url
    ]
    
    try:
        subprocess.Popen(mpv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
        print("Comando mpv ejecutado en segundo plano. Si el video no se ve en la pantalla deseada o solo hay audio, verifica el usuario, UID, DISPLAY y el índice de pantalla.")
    except FileNotFoundError:
        print("ERROR: El comando 'mpv' no se encontró. Asegúrate de que esté instalado y en tu PATH.")
        return
    except Exception as e:
        print(f"ERROR inesperado al lanzar mpv: {e}")
        return

def main(args):
    if "--helpme" == args[0]:
        print_help()
        return

    youtube_url = None
    target_user_arg = None
    target_uid_arg = None
    force_display_arg = None
    force_screen_index_arg = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--user" and i + 1 < len(args):
            target_user_arg = args[i+1]
            i += 2
        elif arg == "--uid" and i + 1 < len(args):
            target_uid_arg = args[i+1]
            i += 2
        elif arg == "--display" and i + 1 < len(args):
            force_display_arg = args[i+1]
            i += 2
        elif arg == "--screen" and i + 1 < len(args):
            force_screen_index_arg = int(args[i+1])
            i += 2
        elif youtube_url is None:
            youtube_url = arg
            i += 1
        else:
            print(f"ERROR: Argumento desconocido o malformado: {arg}")
            print_help()
            return

    if youtube_url is None:
        print("ERROR: Debes proporcionar una URL de YouTube.")
        print_help()
        return

    target_user = target_user_arg or os.getenv("SUDO_USER")
    target_uid = target_uid_arg or os.getenv("SUDO_UID")

    if not target_user:
        print("AVISO: No se pudo detectar SUDO_USER. Asumiendo 'osiris' (AJUSTAR SI ES NECESARIO).")
        target_user = "osiris"
    if not target_uid:
        print("AVISO: No se pudo detectar SUDO_UID. Asumiendo '1000' (AJUSTAR SI ES NECESARIO).")
        target_uid = "1000"

    final_display, final_mpv_screen_index = detect_screen_config(
        target_user, target_uid, force_display_arg, force_screen_index_arg
    )
    
    play_video(youtube_url, target_user, target_uid, final_display, final_mpv_screen_index)

if __name__ == "__main__":
    main(sys.argv[1:])
