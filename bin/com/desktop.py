import osiris2
import datetime
import subprocess
import os
import sys
import importlib
import time
import signal

usuario = os.getlogin()
r_def_mode = def_exec_mode = "bg"
apps = ["dsk1", "dsk2", "dsk3", "dsk4", "dsk5", 
        "dsk6", "dsk7", "makedochtml", "ipinfo", "localnet", "gemini"]

# Variable global para almacenar el PID del proceso en modo fixed
fixed_process_pid = None

def recargar_modulo(nombre_modulo):
    if nombre_modulo in sys.modules:
        print(f"Desmontando el módulo '{nombre_modulo}'...")
        del sys.modules[nombre_modulo]
    print(f"Montando el módulo '{nombre_modulo}'...")
    mod = importlib.import_module(nombre_modulo)
    globals()[nombre_modulo] = mod

recargar_modulo('osiris2')

def kill_fixed_process(sig, frame):
    """Manejador de señal para matar el proceso en modo 'fixed' cuando se hace Control+C."""
    global fixed_process_pid
    if def_exec_mode == "fixed" and fixed_process_pid:
        print(f"Control+C detectado. Matando el proceso con PID {fixed_process_pid}.")
        try:
            os.kill(fixed_process_pid, signal.SIGTERM)
        except ProcessLookupError:
            print(f"El proceso con PID {fixed_process_pid} ya no existe.")
        except PermissionError:
            print(f"No se tiene permiso para matar el proceso con PID {fixed_process_pid}.")
        fixed_process_pid = None  # Limpiar el PID después de matar el proceso

signal.signal(signal.SIGINT, kill_fixed_process)

def iniciar_multiprocess(obj):
    global fixed_process_pid
    try:
        osiris2.multiprocess(obj)
        if def_exec_mode == "fixed":
            fixed_process_pid = osiris2.fixed_pid  # Guardar el PID si estamos en modo 'fixed'
            print("Fixed Pid:", fixed_process_pid)
        print("Proceso iniciado con los siguientes datos:", obj)
    except ValueError as e:
        print(f"Error al iniciar el proceso: {e}")



def mostrar_man():
    """Muestra la documentación del módulo."""
    print(osiris2.man)

def editar_script():
    """Edita el script actual usando nano."""
    subprocess.call(["nano", "-w", "-i", "com/" + os.path.basename(__file__)])





def listar_procesos():
    """Lista todos los procesos y sus detalles."""
    procesos = osiris2.process_manager.get_all_handlers()
    if not procesos:
        print("No hay procesos en ejecución.")
        return

    for nombre, handler in procesos.items():
        print(f"Nombre del proceso: {handler.name}")
        print(f"PID: {handler.pid}")  # Mostrar el PID
        print(f"En ejecución: {'Sí' if handler.is_running() else 'No'}")
        print(f"Metadata: {handler.metadata}\n")


def kill(identifier):
    """Mata el proceso especificado por el número (PID) o por el nombre si está activo."""
    procesos = osiris2.process_manager.get_all_handlers()  # Asumiendo que este es un diccionario de procesos

    # Inicializar una lista para manejar múltiples procesos
    handlers = []

    try:
        # Intentar convertir el identificador a entero (PID)
        numero = int(identifier)  # Si identifier es un número, se convierte
        # Buscar el proceso por PID
        for nombre, proc_handler in procesos.items():
            print(f"Comprobando proceso: {nombre} con PID: {proc_handler.pid}")  # Mensaje de depuración
            if proc_handler.pid == numero:
                handlers.append(proc_handler)  # Almacena el handler si se encuentra
                break  # Se puede salir del bucle, ya que se encontró el PID
    except ValueError:
        # Si no se puede convertir a entero, se asume que es un nombre de proceso
        for nombre, proc_handler in procesos.items():
            if nombre == identifier:
                handlers.append(proc_handler)  # Almacena el handler

    if not handlers:
        print(f"No se encontró un proceso activo con el identificador '{identifier}'.")
        return

    # Intentar matar todos los procesos encontrados
    for handler in handlers:
        if handler.is_running():
            try:
                # Intentar enviar SIGTERM (más suave)
                os.kill(handler.pid, signal.SIGTERM)
                print(f"Enviando SIGTERM al proceso con PID {handler.pid}.")
                # Esperar un poco para que el proceso tenga tiempo de terminar
                time.sleep(1)

                # Verificar si el proceso aún está en ejecución
                if os.path.exists(f"/proc/{handler.pid}"):
                    print(f"Proceso con PID {handler.pid} no se detuvo, intentando con SIGKILL.")
                    os.kill(handler.pid, signal.SIGKILL)  # Enviar SIGKILL (más agresivo)
                    print(f"Enviando SIGKILL al proceso con PID {handler.pid}.")
            except ProcessLookupError:
                print(f"Proceso con PID {handler.pid} no se encontró.")
            except PermissionError:
                print(f"No se tiene permiso para matar el proceso con PID {handler.pid}.")
            except Exception as e:
                print(f"Error al intentar matar el proceso con PID {handler.pid}: {e}")
        else:
            print(f"El proceso con PID {handler.pid} no está en ejecución.")

# Ejemplo de uso:
# kill(1234)  # Para matar por PID
# kill("nombre_del_proceso")  # Para matar todos los procesos con ese nombre



def kill_all():
    """Lista todos los procesos y sus detalles, y los termina si están en ejecución."""
    procesos = osiris2.process_manager.list_processes()  # Devuelve una lista de tuplas (nombre, pid)
    if not procesos:
        print("No hay procesos en ejecución.")
        return

    # Lista de PIDs para poder matar los procesos
    pids_to_kill = []

    print("Lista de procesos en ejecución:")
    for nombre, pid in procesos:  # Cambiado para desempaquetar directamente la tupla
        handler = osiris2.process_manager.get_handler(nombre)  # Obtiene el handler del proceso por su nombre
        if handler:
            print(f"Nombre del proceso: {handler.name}")
            print(f"PID: {handler.pid}")  # Mostrar el PID
            print(f"En ejecución: {'Sí' if handler.is_running() else 'No'}")
            print(f"Metadata: {handler.metadata}\n")

            # Si el proceso está en ejecución, lo agregamos a la lista de PIDs a matar
            if handler.is_running():
                pids_to_kill.append(handler.pid)

    # Intentar matar todos los procesos en ejecución
    for pid in pids_to_kill:
        try:
            # Intentar enviar SIGTERM (más suave)
            os.kill(pid, signal.SIGTERM)  
            print(f"Enviando SIGTERM al proceso con PID {pid}.")
            # Esperar un poco para que el proceso tenga tiempo de terminar
            time.sleep(1)  

            # Verificar si el proceso aún está en ejecución
            if os.path.exists(f"/proc/{pid}"):
                print(f"Proceso con PID {pid} no se detuvo, intentando con SIGKILL.")
                os.kill(pid, signal.SIGKILL)  # Enviar SIGKILL (más agresivo)
                print(f"Enviando SIGKILL al proceso con PID {pid}.")
        except ProcessLookupError:
            print(f"Proceso con PID {pid} no se encontró.")
        except PermissionError:
            print(f"No se tiene permiso para matar el proceso con PID {pid}.")
        except Exception as e:
            print(f"Error al intentar matar el proceso con PID {pid}: {e}")



def get_mode_from_args(args):
    # Buscar la opción --mode en los argumentos
    if '--mode' in args:
        mode_index = args.index('--mode')
        # Verificar si hay un valor válido después de --mode
        if mode_index + 1 < len(args) and args[mode_index + 1] in ["fixed", "bg"]:
            mode = args[mode_index + 1]
            # Eliminar ambos elementos de la lista de argumentos
            del args[mode_index:mode_index + 2]
            dx = (mode, args)  # Retorna mode y args restantes
            return dx 
        else:
            # Si no hay valor o es inválido, eliminar solo '--mode'
            del args[mode_index]
    dx = (None, args)  # Retorna None si no se encuentra un modo válido
    return dx



def main(args):
    global usuario, def_exec_mode, r_def_mode
    scom = None
    
    args_p = args[1:]
    mode = get_mode_from_args(args_p)
    print("---", mode)

    if mode[0] is not None:
        print(f"Modo seleccionado: {mode[0]}")
        def_exec_mode = mode[0]
        scom = mode[1]
    else:
        def_exec_mode = r_def_mode
        print("---", mode[1])
        print("No se especificó un modo válido con --mode. Utilizando modo predeterminado.")

    
    timestamp = int(time.time())
    print('Args input {timestamp}:', args)

    try:
        if args[0] == "man":
            mostrar_man()
        elif args[0] == "---edit":
            editar_script()
        elif args[0] == "killall":
            kill_all()
        elif args[0] == "kill":
            if len(args) > 1:
#                try:
#                    int(args[1])
#                except:
#                    print("Parámetro PID debe ser un número")
#                    return
#                kill(int(args[1]))
                 kill(args[1])
        elif len(args) == 2 and args[0] == "output":
            osiris2.process_manager.monitor_process_output(args[1])
        elif args[0] in apps:
            args_0 = args[0]
            args.pop(0)
            lcom = " ".join(args)
#            if scom != None:
#                lcom = scom
            obj = {
                "mode": def_exec_mode,  # Cambia a "fixed" si deseas el comportamiento por defecto
                "name": None,  # Se generará automáticamente si es None
                "com": ["python3", "com/dsk/"+args_0+".py"] + args,  # Asegúrate de que este comando sea válido
                "metadata": {"user": usuario,
                            "time_start":timestamp,
			    "command":args_0 +" "+lcom
                            }
            }
            iniciar_multiprocess(obj)
        elif args[0] == "com":
            args.pop(0) 

            if scom != None:
                lcom = scom
            else :
                lcom = args

            obj = {
                "mode": def_exec_mode,  # Cambia a "fixed" si deseas el comportamiento por defecto
                "name": None,  # Se generará automáticamente si es None
                "com": lcom,  # Asegúrate de que este comando sea válido
                "metadata": {"user": usuario,
                            "time_start":timestamp,
                            "command":lcom
                            }
            }


            print(obj)
            def_exec_mode = r_def_mode
            iniciar_multiprocess(obj)

            #subprocess.call(["python3", "com/dsk/dsk2.py"])
            print("FREE ARG")
        elif args[0] == "XARG":
            #subprocess.call(["python3", "com/dsk/dsk2.py"])
            print("FREE ARG")
        elif args[0] == "list_processes":
            listar_procesos()  # Comando para listar procesos
        elif args[0] == "show_handlers":
            print("Contenido de process_handlers:")
            print(osiris2.process_manager.get_all_handlers())

    except Exception as e:
        print("Se ha producido un error:", e)



print(osiris2.info)
print('Creado módulo-comando desktop y fecha y hora: 2024-09-27 08:55:29.392217')

if __name__ == "__main__":
    main()
