import os
import subprocess
import time
import signal
import readline

# Diccionario global para almacenar los handlers de procesos
process_handlers = {}

# Información general del módulo
info = """
Módulo Osiris osiris2 - rst-
Multiprocess
Este módulo permite la ejecución de procesos en segundo plano y en bucle.
"""

# Documentación del uso
man = """
MANUAL:
multiprocess(obj)

obj es un diccionario que debe tener los siguientes campos:

- mode: 'fixed' o 'bg'
    * 'fixed': Ejecuta el proceso con un bucle while hasta que termine.
    * 'bg': Ejecuta el proceso en segundo plano y redirige la salida a /dev/null.
    
- name: Nombre del proceso (opcional)
    * Si no se proporciona, se generará un nombre automáticamente (p. ej. proceso_1).

- com: Lista de comandos (obligatorio)
    * Este campo es obligatorio. Si no se proporciona, el programa lanzará un error.

- metadata: Metadatos adicionales opcionales (diccionario)
    * Permite agregar datos como el usuario u otra información adicional.

Ejemplo de uso:
obj = {
    "mode": "fixed",
    "name": "mi_proceso",
    "com": ["ping", "-c", "4", "google.com"],
    "metadata": {"user": "john_doe"}
}
multiprocess(obj)
"""


fixed_pid = None

class ProcessHandler:
    """Clase para manejar un proceso individual."""
    
    def __init__(self, name, process, metadata=None, mode="fixed"):
        self.name = name
        self.process = process
        self.metadata = metadata or {}
        self.date = time.strftime("%Y-%m-%d")
        self.pid = process.pid
        self.mode = mode  # Almacena el modo

    def is_running(self):
        """Verifica si el proceso sigue corriendo."""
        return self.process.poll() is None

    def read_output(self):
        """Lee la salida del proceso sin bloquear el flujo."""
        stdout = self.process.stdout.readline()
        stdout += self.process.stderr.readline()
        if stdout:
            print(f"\nOutput from {self.name}:\n---------------------------------------------\n {stdout}\n---------------------------------------------\n")



class ProcessManager:
    """Clase para gestionar los procesos y sus handlers."""
    
    def __init__(self):
        self.process_counter = 0  # Este es un atributo de instancia

    def start_process(self, name, command, cwd=".", metadata=None, mode="fixed"):
        """Inicia un nuevo proceso y devuelve su handler."""
        
        # Generar un nombre automáticamente si no se proporciona uno
        if name is None:
            self.process_counter += 1  # Incrementar el contador de procesos
            name = f"proceso_{self.process_counter}"
        
        # Verificar si el comando está vacío
        if not command:
            raise ValueError("Error: El campo 'com' es obligatorio y no puede estar vacío.")

        # Iniciar el proceso en el modo especificado
        if mode == "bg":
            process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
        # Crear y almacenar el handler del proceso en el diccionario global
        handler = ProcessHandler(name, process, metadata, mode)  # Pasar mode aquí
        process_handlers[name] = handler  # Almacena el handler en el diccionario global
        return handler

    def get_handler(self, name):
        """Obtiene el handler de un proceso por nombre."""
        return process_handlers.get(name)

    def list_processes(self):
        """Devuelve una lista de procesos en ejecución."""
        return [(name, handler) for name, handler in process_handlers.items() if handler.is_running()]

    def get_all_handlers(self):
        """Devuelve todos los handlers de procesos."""
        return process_handlers  # Devuelve el diccionario global completo

    def monitor_process_output(self, name):
        global fixed_pid
        """Monitorea la salida de un proceso en ejecución."""
        handler = self.get_handler(name)  # Obtiene el handler por el nombre
        
        if handler is None:
            print(f"No se encontró el proceso con el nombre: {name}")
            return
        
        if not handler.is_running():
            print(f"El proceso {handler.name} (PID: {handler.pid}) no está en ejecución.")
            return

        # Obtiene el modo del handler
        mode = handler.mode  # Acceder al atributo mode
        fixed_pid = handler.pid
        print(f"Monitoreando la salida del proceso {handler.name} (PID: {handler.pid}):")
        
        try:
            if mode == "bg":
                print("No se puede leer la salida en modo background (bg)")
                return
            
            while handler.is_running():
                handler.read_output()  # Lee y muestra la salida del proceso
                time.sleep(0.1)  # Evita bucles excesivamente rápidos
            fixed_pid = None
        
        except KeyboardInterrupt:
            print("\nInterrupción recibida. Cerrando el proceso...")
            handler.process.terminate()  # Cierra el proceso de manera controlada
            handler.process.wait()  # Espera a que el proceso termine
            print(f"Proceso {handler.name} (PID: {handler.pid}) cerrado.")

        print(f"El proceso {handler.name} (PID: {handler.pid}) ha terminado.")


# Instancia de ProcessManager para gestionar los procesos
process_manager = ProcessManager()

def validate_obj(obj):
    """Valida el objeto de configuración del proceso."""
    if not isinstance(obj, dict):
        raise ValueError("El objeto proporcionado debe ser un diccionario.")
    if 'com' not in obj or not obj['com']:
        raise ValueError("Error: El campo 'com' (comando) es obligatorio y no puede estar vacío.")
    if obj.get('mode') not in {'fixed', 'bg'}:
        raise ValueError("Error: El campo 'mode' debe ser 'fixed' o 'bg'.")

def multiprocess(obj):
    """Función principal para ejecutar un proceso de acuerdo al objeto de configuración."""
    
    # Validar la estructura del objeto de entrada
    validate_obj(obj)

    # Extraer parámetros del objeto
    mode = obj.get('mode', 'fixed')
    name = obj.get('name', None)
    command = obj['com']
    metadata = obj.get('metadata', None)

    # Iniciar el proceso y obtener el handler
    handler = process_manager.start_process(name, command, metadata=metadata, mode=mode)

    # Ejecución en modo 'fixed' con lectura de salida en tiempo real
    if mode == 'fixed':
        print(f"Ejecutando el proceso {handler.name} (PID: {handler.pid}) en modo 'fixed'.")
        process_manager.monitor_process_output(handler.name)  # Llama al método de monitoreo
    else:
        print(f"Proceso {handler.name} (PID: {handler.pid}) ejecutándose en segundo plano (modo 'bg').")

# Ejemplo de uso:
# obj = {
#     "mode": "fixed",
#     "name": None,
#     "com": ["ping", "-c", "4", "google.com"],
#     "metadata": {"user": "john_doe"}
# }
# multiprocess(obj)

