import time
import auth
import importlib.util
import fhelp
import os
import shlex
import types
import ast
import datetime
import inspect
import readline
import pickle
import cnf
import signal
import lib.osiris.common as common
import sys
import subprocess
import pty
import select
import lib.core as core
# Ruta del binario de osiris
osiris_bin_path = os.path.abspath(__file__)
osiris_bin_dir = os.path.dirname(osiris_bin_path)

import lib.help as hlp


help_com = hlp.help_com

core.signal.signal(signal.SIGINT, core.ctrl_signal)

use_command = ""
set_com=""
def_editor="nano"
def_editor_dsk="gedit"

# Nombre del entorno virtual
nombre_venv = "osiris_env"

# Comandos válidos
valid_commands = ["hls", "shell", "blockchain", "desktop", "gemini", "scanip", "sniff", "fftv", "install","cert","create","gcom"]

# Diccionario para almacenar información sobre los módulos y sus funciones main
module_info = {}
loaded_modules = {}

# Archivo de historial
history_file = cnf.history_file

# Cargar historial de comandos
try:
    with open(history_file, "rb") as file:
        command_history = pickle.load(file)
except (FileNotFoundError, EOFError):
    command_history = []

# Guardar historial de comandos
def save_command_history():
    with open(history_file, "wb") as file:
        pickle.dump(command_history, file)

# Función para habilitar y exportar el entorno virtual
def habilitar_y_exportar_venv(nombre_venv):
    global osiris_bin_dir
    try:
        env_vars = subprocess.Popen(["printenv | grep -i osiris"], stdout=subprocess.PIPE, text=True, shell=True).communicate()[0]
        print(env_vars)
    except Exception as e:
        print("Error 62:", e)
    print("PYTHONPATH:", " | ".join(sys.path))

# Función para verificar la declaración de una función en un módulo
def check_function_declaration(module_name, function_name):
    if module_name in module_info:
        return module_info[module_name].get(function_name, None)

    try:
        with open(f"com/{module_name}.py", "r") as file:
            source_code = file.read()
        module_ast = ast.parse(source_code)

        main_function_found = None

        for node in ast.walk(module_ast):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                main_function_found = True

                num_arguments = len(node.args.args) if node.args else 0
                main_function_one_argument = num_arguments == 1

                break

        module_info[module_name] = {}
        module_info[module_name][function_name] = main_function_found and main_function_one_argument

        return main_function_found and main_function_one_argument

    except ImportError:
        return None

# Validación de funciones
def is_valid_function(function):
    return isinstance(function, (types.FunctionType, types.MethodType))

# Verificar si una función tiene un solo argumento
def has_single_argument(function):
    return len(inspect.signature(function).parameters) == 1

# Limpiar datos de comando
def clear_command_data(command_name):
    if command_name in module_info:
        module_info.pop(command_name)

# Cargar un módulo
def load_module(module_name):
    module_path = os.path.join("com", module_name + ".py")
    if os.path.isfile(module_path):
        main_function = check_function_declaration(module_name, "main")
        if main_function is not None and main_function:
            try:
                module_spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(module)
                loaded_modules[module_name] = module  # Almacenamos el módulo en el diccionario de módulos cargados
                return module
            except ImportError as er3:
                print(f"Error al importar {module_name}.py: {er3}")
                print("Verifique los imports del comando en su archivo. Puede montarlo y usar el modificador --edit")
                return None
        else:
            print(f"La función 'main' en {module_name}.py no está declarada correctamente o no tiene un solo argumento.")
            return None
    else:
        print(f"El archivo {module_name}.py no existe en el directorio 'com'.")
        return None

# Ejecutar el comando del módulo cargado
def execute_module_command(module, args):
    if hasattr(module, "main") and is_valid_function(module.main):
        if has_single_argument(module.main):
            # Ejecuta la función main del módulo y captura la salida
            output = module.main(args[1:])
            sys.stdout.flush()  # Forzar el vaciado del buffer de salida
        else:
            print(f"La función 'main' en {module.__name__}.py debe recibir exactamente un argumento.")
    else:
        print(f"La función 'main' no está definida correctamente en {module.__name__}.py")

# Bucle principal del CLI
def command_line():
    global def_editor, def_editor_dsk, use_command, set_com, nombre_venv

    signal.signal(signal.SIGINT, CTRL_C)
    readline.set_history_length(cnf.history_com_size)
    readline.clear_history()
    for command in command_history:
        readline.add_history(command)

    while True:
        core.signal.signal(signal.SIGINT, core.ctrl_signal)
        try:
            # Imprime el prompt con un color y un salto de línea
            rx = common.print_color(">>> " + use_command, common.Color.GREEN,"\n → ")
            # Imprime el prompt con un color y un salto de línea
            com = input(rx)
            if not com:
                continue

            command_history.append(com)
            save_command_history()
            args = shlex.split(com)

            # Asegúrate de que el primer argumento sea el comando actual
            if set_com and args[0] != set_com:
                args.insert(0, set_com)

            if args[0] == "--reload":
                print("RELOAD ENV")
                # Código de recarga del entorno
                continue

               
            handle_command(args)
        except Exception as e:
            print(f"Exception ERROR 175:\n {e}  \nEscriba o pulse Enter para reentrar\n")            
      
        time.sleep(0.1)

# Manejo de comandos
def handle_command(args):
    global use_command, set_com, help_com
    
    

            
    if args[0] == "mount" and len(args) > 1:   #mount para cargar (montar) comandos fuera de la lista
        if args[1] not in valid_commands:
            valid_commands.append(args[1])
            print(f"Montado: {args[1]}")
        else:
            print(f"El comando: {args[1]} ya está montado.") #existe en la lista
        args[0] = "use" #se establede use como primer argumento, contiñúa y establece el comando
    else:
        if args[0] == "reset":  #comando reset para solucionar problemas de cursor en dos pasos 1º use+enter 2º reset+enter
            execute_command(["desktop","com","reset","--mode","fixed"])
            print("Prompt was reseted using desktop command with mode fixed")
            return

    if args[0] == "use" and len(args) == 2:
        use_command = args[1] + "> "
        set_com = args[1]
    elif len(args) >= 2 and args[1] == "use":
        use_command = "" if len(args) == 2 else args[2] + "> "
        set_com = "" if len(args) == 2 else args[2]
    elif args[0] == "--venv":
        habilitar_y_exportar_venv(nombre_venv)
    elif args[0] == "--ods":
        print("Using ODS")
        core.ps.funcion_proceso(            
            ["./OPS/ops"],True
            )
        print("Exit ODS")
    elif len(args) > 1 and args[1] == "--help-com":
        print(help_com)
    elif args[0] == "--lp":
        print("Multiprocess Used in core:")
        try:
            pc_ = core.mp.process_manager.list_processes()
        except Exception as e:
            print("Error Listando Procesos.")
            return
        print("Lista de Procesos:")
        print(pc_)
    elif args[0] == "exit":
        exit_program()
    elif args[0] == "Reset_Password":
        auth.makeauth()
    elif args[0] not in valid_commands:
        print(f"Comando: {args[0]} ")
    elif len(args) > 1 and args[1] == "--reset":
        clear_command_data(args[0])
        loaded_modules.pop(args[0], None)
        print(f"Módulo-comando {args[0]} desmontado")
    elif len(args) > 1 and args[1] == "--edit":
        edit_command(args[0],def_editor)
    elif len(args) > 1 and args[1] == "--edit-dsk":
        edit_command(args[0],def_editor_dsk,"sp")
    else:
        if len(args) > 1 and args[1] == "--help":
            print("Escriba --help-com  para ayuda de comandos predeterminados")
            try:
                print(fhelp.fhelp(args[0]))
            except Exception as e:
                print("No existe HELP para el comando: "+ args[0])
        else:
            execute_command(args)

# Editar un comando
def edit_command(command,editor="nano",action=""):
    def_editor = editor
    ed = os.path.join("com", command + ".py")
    if os.path.isfile(ed):
        if action == "sp" :  # segundo plano
            exec_com_bg = [def_editor,ed]
            _ps = core.mp({
            		"mode":"bg",
          		"name":None,
                        "com":exec_com_bg,
                        "metadata": {"user": usuario,
                            "time_start":timestamp,
			    "command": exec_com_bg
                            }})
        elif def_editor in subprocess.check_output(["ps", "-aux"]).decode():
            subprocess.call([def_editor, ed])
        else:
            subprocess.call([def_editor, ed])
    else:
        print("No se encuentra el módulo a editar, use create [comando] --create para crear uno nuevo")

# Ejecutar un comando cargando el módulo si es necesario
def execute_command(args):
    if args[0] in valid_commands:
        module = loaded_modules.get(args[0]) or load_module(args[0])
        if module:
            execute_module_command(module, args)
    else:
        # Ejecuta comando externo
        execute_external_command(args)

# Ejecuta un comando externo utilizando pty
def execute_external_command(args):
    if args:
        try:
            # Crea un terminal pseudo-tty (pty)
            master_fd, slave_fd = pty.openpty()
            os.setsid(slave_fd)  # Crea una nueva sesión para el proceso

            # Ejecuta el comando en el pty
            process = subprocess.Popen(args, shell=True, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd)

            # Define conjuntos de archivos para select
            read_fds = [sys.stdin, master_fd]

            # Bucle principal para leer la salida del proceso externo y la entrada del usuario
            while True:
                # Utiliza select para esperar eventos de lectura
                readable, _, _ = select.select(read_fds, [], [])

                # Procesar la entrada del usuario
                if sys.stdin in readable:
                    try:
                        com = input(common.print_color(">>> " + use_command, common.Color.RED))
                        if com:
                            # Escribe la entrada del usuario al proceso externo
                            os.write(slave_fd, com.encode())
                    except EOFError:
                        print("Ctrl+d Signal")
                        auth.access()
                        # Si se presiona Ctrl+D, termina la lectura
                        break

                # Procesar la salida del proceso externo
                if master_fd in readable:
                    data = os.read(master_fd, 1024)
                    if not data:
                        # Si el proceso externo ha terminado, termina el bucle
                        break
                    print("\n" + data.decode(), end='\n')

            # Espera a que el proceso termine
            process.wait()

            # Imprime el prompt nuevamente después de que el proceso externo termine
            print(common.print_color(">>> " + use_command, common.Color.RED), end="")

        except Exception as e:
            print(f"Error al ejecutar comando externo: {e}")


# Salir del programa
def exit_program(onoff):
#    return
    exit_decision =  onoff  #"yes" #input("\n¿Desea salir del programa? Escriba 'yes' o 'no': ")
    if exit_decision.lower() == "yes":
        print("\nEXIT PROGRAM\n")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        auth.access()
    elif exit_decision.lower() == "no":
        return
    else:
        exit_program()

# Manejo de señal Ctrl+C
def CTRL_C(signal, frame):
    exit_program("yes")
#    print("EXCPT")
#    print("\nEscriba 'exit' para salir")
#    return

# Ejecutar el CLI
if __name__ == "__main__":
    command_line()
