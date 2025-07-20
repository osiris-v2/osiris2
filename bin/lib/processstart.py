import time
import datetime
import subprocess
import os
import threading
import signal
import sys
import multiprocessing
import random
INFO = "MODULE PROCCESSSTART LIB LOADED"
#print("Import module processstart")

prueba = False
estado_proceso = False
pid_queue = multiprocessing.Queue()  # Cola compartida para almacenar el PID del proceso hijo
pid_proceso = None
yt_last_args = False


def ps(Xargs, foreground_d="False"): 
    funcion_proceso(Xargs, foreground=foreground_d)

def funcion_proceso(args, foreground=False): # Añadido argumento foreground
    global estado_proceso
    global pid_proceso
    try:
        if foreground:
            # Ejecutar en primer plano
            try:
                print("Iniciando proceso en primer plano:",args)
                subprocess.run(args, check=True, bufsize=0, close_fds=True, restore_signals=True, shell=False, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)  # Modificado para usar stdin, stdout, stderr
                pid_proceso = None # No hay pid en foreground
                print("Proceso en primer plano finalizado.")
            except subprocess.CalledProcessError as e:
                print(f"Error en el proceso en primer plano (código de retorno {e.returncode}): {e}")
            except Exception as e:
                print(f"Error inesperado en el proceso en primer plano: {e}")
            finally:
                estado_proceso = False

        else:
            # Ejecutar en segundo plano (como antes)
            proceso = multiprocessing.Process(target=_funcion_interna, args=(args,))
            proceso.start()
            pid_proceso = pid_queue.get()  # Obtenemos el PID del proceso hijo desde la cola
            proceso.join()  # Esperamos a que el proceso hijo se inicie completamente
            print("Iniciado proceso PID:", pid_proceso)
        
    except Exception as e:
        print("Error al iniciar el proceso:", e)
    finally:
        if not foreground: #Solo en segundo plano
            estado_proceso = True


def _funcion_interna(args):
    try:
        proceso = subprocess.Popen(args, bufsize=0, close_fds=True, restore_signals=True, shell=False, stdin=None, stdout=None, stderr=subprocess.DEVNULL)
        pid_proceso = proceso.pid
        pid_queue.put(pid_proceso)  # Pasamos el PID del proceso hijo a la cola
        print("Iniciado Hilo", pid_proceso)
        proceso.wait() #esperar a que termine el proceso
    except Exception as e:
        print("Error Popen:", e)
        return

def detener_proceso():
    global estado_proceso
    global pid_proceso
    if estado_proceso:
        try:
            if pid_proceso is not None:
                os.kill(pid_proceso, signal.SIGTERM) # Primero SIGTERM, luego SIGKILL si es necesario
                time.sleep(1) # Dar tiempo para terminar limpiamente
                if proceso.poll() is None: # Verificar si sigue activo
                    os.kill(pid_proceso, signal.SIGKILL)
                estado_proceso = False
                print("Detenido proceso PID:", pid_proceso)
                pid_proceso = None
        except ProcessLookupError:
            print("Proceso ya finalizado")
        except Exception as e:
            print("Error al detener el proceso:", e)
    else:
        print("No existe proceso abierto")