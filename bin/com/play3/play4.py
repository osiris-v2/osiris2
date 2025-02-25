import subprocess
import threading
import os
import signal

user_agent = ["-headers","user-agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'"]

user_agent = []


ffmpeg_exec="/var/osiris2/bin/com/osiris_env/ffmpeg/bin/ffmpeg"

def reap_children(signum, frame):
    """ Recolectar cualquier proceso hijo terminado """
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except ChildProcessError:
            break

# Configurar el manejador de la señal SIGCHLD
signal.signal(signal.SIGCHLD, reap_children)

def kill_last_process():
    """ Mata el último proceso """
    global last_process
    if last_process:
        pid = last_process.pid
        print(f"Attempting to kill process quickly with SIGKILL: {pid}")
        
        try:
            os.kill(pid, signal.SIGKILL)
            last_process.wait(timeout=5)  # Espera breve para permitir limpieza
        except Exception as e:
            print(f"Quick kill failed or process still running: {e}")

        if last_process.poll() is None:  # Si el proceso sigue en ejecución
            print(f"Attempting to terminate process gracefully: {pid}")
            try:
                last_process.stdin.write(b'q\n')
                last_process.stdin.flush()
                last_process.wait(timeout=5)
            except Exception as e:
                print(f"Graceful termination failed: {e}")
                try:
                    last_process.terminate()
                    last_process.wait(timeout=5)
                except Exception as e:
                    print(f"Forced termination failed: {e}")
        else:
            print(f"Process {pid} has already been terminated.")
        
        last_process = None


def listar_procesos():
     print("FUTURE PLAY 5")


def ejecutar_proceso(command, cwd):
    """ Ejecuta el proceso en segundo plano """
    global last_process

    if last_process:
        print("Killing last process:", last_process)
        kill_last_process()

    # Abrir el proceso en segundo plano
    try:    
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE, close_fds=True)
    except Exception as e :    
        print("ERROR SUBPROCESS:",e)
        return
    last_process = process
    print("\nProcess started with PID:", process.pid,"\n")
    return


def start_ffmpeg(url,com):
    """ Inicia el proceso ffmpeg con los parámetros especificados """
    global last_process
    global last_url
    global command
    global hls_path
    global hls_progress_file
    global ffcom_metadata
    global ffmpeg_exec
    kill_last_process()  # Mata el proceso actual antes de iniciar uno nuevo


#, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE, close_fds=True
    finput = [
    '-y',
    '-re',
    '-loglevel', 'verbose',
    '-f', 'lavfi', '-i', 'color=c=black:s=1280x720',
    '-stream_loop', '-1','-i', url,  # Aplicar stream_loop aquí
    '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
    '-af', 'aresample=async=1,loudnorm=I=-16:TP=-1.5:LRA=11',
    '-filter_complex', '[1:v]scale=-2:720[scaled];[0:v][scaled]overlay=(W-w)/2:(H-h)/2',
    '-map', '0:v',
    '-map', '1:a']
    
    
    _finput = [
    'ffmpeg',
    '-y',
    '-re',
    '-loglevel', 'warning',
    '-f','v4l2',
    '-i','/dev/video0']
    
    
    foutput = ['-threads','2','-c:v', 'libx264', '-preset', 'ultrafast',
    '-tune', 'zerolatency', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
    '-b:v', '0', '-s:v', '856x580', '-maxrate:v', '3000k', '-bufsize:v', '6000k',
    '-g', '20', '-sc_threshold', '50',
    '-ignore_unknown',
    '-strftime', '1',
    '-bsf:v', 'h264_mp4toannexb', '-bsf:a', 'aac_adtstoasc',
    '-f','hls',
    '-hls_time', '2', '-hls_list_size', '30',
    '-segment_list_flags','+live',
    '-hls_flags', '+omit_endlist+delete_segments+append_list',
    '-master_pl_name', 'master_ultrafast.m3u8',
    '-hls_segment_filename', os.path.join(hls_path, '%Y%m%d%H%M%S.ts'),
    os.path.join(hls_path, 'live.m3u8'), '-progress', hls_progress_file,
    '-fflags', '+genpts+igndts+discardcorrupt', '-flags', 'low_delay', '-max_delay', '0',
    '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '1', '-metadata', ffcom_metadata
]

    try:
        user_agent = parse_input(url)
    except Exception as e:
        print("UA ER 136:",e)
        
    
    print("UA: ",user_agent)
    command =   [ffmpeg_exec] + user_agent + finput + foutput
    print(command)
    # si se recibe el comando se sustituye command
    if com:
        com = com
#        command = com
        print("com ¬ ")

    print("Executing command in background:", " ".join(command))
    try:
        print("Creating process...")
        thread = threading.Thread(target=ejecutar_proceso, args=(command, '.'))
        thread.start()
    except Exception as e:
        print("Error starting process:", e)

    last_url = url
    print(f"\n Process started for URL: {url}\n")


def parse_input(parametro):
    global user_agent
    if parametro.startswith("http://") or parametro.startswith("https://"):
        return user_agent
    elif os.path.exists(parametro):
        user_agent = []
        return user_agent


#print("FUNC")




# Inicializa variables globales
last_process = None
last_url = ""
command = []
hls_progress_file = "/var/osiris2/bin/com/datas/progress_hls.txt"
hls_default_input = "/var/osiris2/bin/com/datas/ffmpeg/intro.mp4"
hls_path = "/var/osiris2/html/app/mitv/channels/main/live-ts"
ffcom_metadata = "text=osiristv-hls-main"

