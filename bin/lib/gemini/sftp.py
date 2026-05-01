# Módulo SSH mejorado con interfaz gráfica y funcionalidad avanzada

import paramiko
import getpass
import os
import asyncio
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, Tuple, Dict, Any

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSHConnector:
    _instance = None
    _connection_details = {} # Almacena dirección, puerto y contraseña para reconexión

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SSHConnector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'): # Evitar reinicialización si ya se ha hecho
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.sftp_client = None
            self.connected = False
            self._initialized = True
            self._session_id = None
            self._tunnels = {}
            self._active_commands = {}
            self._command_history = []
            self._file_transfer_queue = asyncio.Queue()
            self._file_transfer_tasks = set()

    async def _prompt_for_connection_details(self, initial_prompt=True):
        print("--- Menú de Conexión SSH ---")
        if not initial_prompt and self.connected:
            print("Actualmente conectado. Desea desconectar o reconectar?")
            action = input("('d' para desconectar, 'r' para reconectar, cualquier otra tecla para no hacer nada): ").lower()
            if action == 'd':
                await self.disconnect()
            elif action == 'r':
                print("Intentando reconectar con los datos guardados...")
                return True # Intentar reconectar con los datos existentes
            else:
                return False # No hacer nada si ya está conectado y no pide desconectar/reconectar

        if self._connection_details and initial_prompt:
            print(f"Detalles de conexión guardados: {self._connection_details.get('hostname')}:{self._connection_details.get('port', 22)}")
            choice = input("¿Desea reconectar con los datos guardados? (s/n, o Enter para S): ").lower()
            if choice in ['', 's']:
                print("Intentando reconectar con los datos guardados...")
                return True

        print("Ingrese los nuevos detalles de conexión:")
        hostname = input("Dirección IP o Hostname: ").strip()
        port = input("Puerto SSH (por defecto 22): ").strip()
        port = int(port) if port.isdigit() else 22
        username = input("Nombre de usuario: ").strip()
        password = getpass.getpass("Contraseña (no visible): ").strip()
        initial_dir = input("Directorio de inicio (opcional, ej: /home/usuario): ").strip()

        self._connection_details.update({
            'hostname': hostname,
            'port': port,
            'username': username,
            'password': password,
            'initial_dir': initial_dir if initial_dir else None
        })
        return False # Indicar que se han introducido nuevos datos

    async def connect(self):
        if self.connected:
            print("Ya estás conectado a SSH.")
            return True

        if await self._prompt_for_connection_details(initial_prompt=True):
            # Intentar reconectar con detalles guardados si el prompt lo sugiere
            pass # Los detalles ya están en _connection_details

        details = self._connection_details
        if not details.get('hostname') or not details.get('username') or not details.get('password'):
            print("Error: Faltan detalles de conexión esenciales.")
            self.connected = False
            return False

        try:
            print(f"Conectando a {details['hostname']}:{details['port']} como {details['username']}...")
            self.client.connect(
                hostname=details['hostname'],
                port=details['port'],
                username=details['username'],
                password=details['password'],
                timeout=10 # Añadir un timeout de conexión
            )
            self.sftp_client = self.client.open_sftp()
            self.connected = True
            self._session_id = os.urandom(16).hex() # Generar un ID de sesión único
            print(f"¡Conexión SSH y SFTP establecida con éxito! 🎉 (Sesión ID: {self._session_id})")
            if details['initial_dir']:
                try:
                    self.sftp_client.chdir(details['initial_dir'])
                    print(f"Directorio de inicio establecido en: {details['initial_dir']}")
                except Exception as e:
                    print(f"Advertencia: No se pudo cambiar al directorio de inicio {details['initial_dir']}: {e}")
            return True
        except paramiko.AuthenticationException:
            print("Error de autenticación. Nombre de usuario o contraseña incorrectos. ❌")
        except paramiko.SSHException as e:
            print(f"Error SSH: {e} ❌")
        except Exception as e:
            print(f"Error inesperado al conectar: {e} ❌")

        self.connected = False
        return False

    async def disconnect(self):
        if self.connected:
            try:
                if self.sftp_client:
                    self.sftp_client.close()
                    self.sftp_client = None
                self.client.close()
                self.connected = False
                self._session_id = None
                print("Conexión SSH y SFTP cerrada. Adiós! 👋")
            except Exception as e:
                print(f"Error al cerrar la conexión: {e}")
        else:
            print("No hay conexión SSH activa para cerrar.")

    async def reconnect_if_broken(self):
        if not self.connected:
            print("La conexión se ha perdido o no está activa. Intentando reconectar...")
            return await self.connect()
        return True # Ya está conectado

    async def get_sftp_client(self):
        if not await self.reconnect_if_broken():
            print("No se pudo restablecer la conexión SFTP. 😞")
            return None
        return self.sftp_client

    async def execute_command(self, command):
        if not await self.reconnect_if_broken():
            print("No se pudo ejecutar el comando: conexión no activa. 😞")
            return None, None, None # stdout, stderr, exit_status

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            # Leer toda la salida para evitar interbloqueos
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            # Registrar el comando en el historial
            self._command_history.append({
                'command': command,
                'output': output,
                'error': error,
                'exit_status': exit_status,
                'timestamp': asyncio.get_event_loop().time()
            })

            if exit_status != 0:
                print(f"Comando '{command}' falló con código {exit_status}. Error: {error}")
            return output, error, exit_status
        except paramiko.SSHException as e:
            print(f"Error SSH al ejecutar comando: {e}. La conexión podría haberse roto.")
            self.connected = False # Marcar como rota para forzar reconexión
            return None, str(e), -1
        except Exception as e:
            print(f"Error inesperado al ejecutar comando: {e}")
            return None, str(e), -1

    async def upload_file(self, local_path, remote_path):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Subiendo archivo {local_path} a {remote_path}...")
            sftp.put(local_path, remote_path)
            print("¡Archivo subido con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al subir el archivo: {e}")
            return False

    async def download_file(self, remote_path, local_path):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Descargando archivo {remote_path} a {local_path}...")
            sftp.get(remote_path, local_path)
            print("¡Archivo descargado con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al descargar el archivo: {e}")
            return False

    async def create_tunnel(self, local_port, remote_host, remote_port):
        if not self.connected:
            print("No hay conexión SSH activa. 😞")
            return False

        try:
            transport = self.client.get_transport()
            if not transport:
                print("No se pudo obtener el transporte SSH. 😞")
                return False

            print(f"Creando túnel desde {local_port} a {remote_host}:{remote_port}...")
            tunnel = transport.open_channel(
                'direct-tcpip',
                (remote_host, remote_port),
                ('localhost', local_port)
            )
            self._tunnels[local_port] = tunnel
            print(f"¡Túnel creado con éxito! 🎉 (Puerto local: {local_port})")
            return True
        except Exception as e:
            print(f"Error al crear el túnel: {e}")
            return False

    async def close_tunnel(self, local_port):
        if local_port not in self._tunnels:
            print(f"No hay túnel activo en el puerto {local_port}. 😞")
            return False

        try:
            print(f"Cerrando túnel en el puerto {local_port}...")
            self._tunnels[local_port].close()
            del self._tunnels[local_port]
            print("¡Túnel cerrado con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al cerrar el túnel: {e}")
            return False

    async def list_files(self, remote_path='.'):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return None

        try:
            print(f"Listando archivos en {remote_path}...")
            files = sftp.listdir(remote_path)
            print(f"Archivos en {remote_path}:")
            for file in files:
                print(f" - {file}")
            return files
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            return None

    async def get_file_info(self, remote_path):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return None

        try:
            print(f"Obteniendo información del archivo {remote_path}...")
            file_info = sftp.stat(remote_path)
            print(f"Información del archivo {remote_path}:")
            print(f" - Tamaño: {file_info.st_size} bytes")
            print(f" - Permisos: {oct(file_info.st_mode)}")
            print(f" - Última modificación: {file_info.st_mtime}")
            return file_info
        except Exception as e:
            print(f"Error al obtener información del archivo: {e}")
            return None

    async def change_permissions(self, remote_path, permissions):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Cambiando permisos de {remote_path} a {permissions}...")
            sftp.chmod(remote_path, permissions)
            print("¡Permisos cambiados con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al cambiar permisos: {e}")
            return False

    async def change_owner(self, remote_path, owner, group=None):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Cambiando propietario de {remote_path} a {owner}:{group}...")
            sftp.chown(remote_path, owner, group)
            print("¡Propietario cambiado con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al cambiar propietario: {e}")
            return False

    async def create_directory(self, remote_path):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Creando directorio {remote_path}...")
            sftp.mkdir(remote_path)
            print("¡Directorio creado con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al crear directorio: {e}")
            return False

    async def remove_directory(self, remote_path):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Eliminando directorio {remote_path}...")
            sftp.rmdir(remote_path)
            print("¡Directorio eliminado con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al eliminar directorio: {e}")
            return False

    async def remove_file(self, remote_path):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Eliminando archivo {remote_path}...")
            sftp.remove(remote_path)
            print("¡Archivo eliminado con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al eliminar archivo: {e}")
            return False

    async def rename_file(self, old_path, new_path):
        sftp = await self.get_sftp_client()
        if not sftp:
            print("No se pudo obtener el cliente SFTP. 😞")
            return False

        try:
            print(f"Renombrando archivo {old_path} a {new_path}...")
            sftp.rename(old_path, new_path)
            print("¡Archivo renombrado con éxito! 🎉")
            return True
        except Exception as e:
            print(f"Error al renombrar archivo: {e}")
            return False

    async def get_command_history(self):
        print("Historial de comandos ejecutados:")
        for i, cmd in enumerate(self._command_history, 1):
            print(f"{i}. {cmd['command']} (Estado: {cmd['exit_status']})")
        return self._command_history

    async def get_session_info(self):
        if not self.connected:
            print("No hay sesión SSH activa. 😞")
            return None

        session_info = {
            'session_id': self._session_id,
            'hostname': self._connection_details.get('hostname'),
            'port': self._connection_details.get('port'),
            'username': self._connection_details.get('username'),
            'initial_dir': self._connection_details.get('initial_dir'),
            'connected': self.connected,
            'tunnels': list(self._tunnels.keys()),
            'command_count': len(self._command_history)
        }
        print("Información de la sesión:")
        for key, value in session_info.items():
            print(f" - {key}: {value}")
        return session_info

    async def queue_file_transfer(self, local_path, remote_path, is_upload=True):
        await self._file_transfer_queue.put((local_path, remote_path, is_upload))
        if not self._file_transfer_tasks:
            asyncio.create_task(self._process_file_transfer_queue())

    async def _process_file_transfer_queue(self):
        while not self._file_transfer_queue.empty():
            local_path, remote_path, is_upload = await self._file_transfer_queue.get()
            if is_upload:
                await self.upload_file(local_path, remote_path)
            else:
                await self.download_file(remote_path, local_path)
            self._file_transfer_queue.task_done()

class SSHGUI(tk.Tk):
    def __init__(self, connector):
        super().__init__()
        self.connector = connector
        self.title("Cliente SSH Avanzado")
        self.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        # Frame de conexión
        connection_frame = ttk.LabelFrame(self, text="Conexión SSH")
        connection_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(connection_frame, text="Hostname:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.hostname_entry = ttk.Entry(connection_frame)
        self.hostname_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(connection_frame, text="Puerto:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_entry = ttk.Entry(connection_frame)
        self.port_entry.insert(0, "22")
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(connection_frame, text="Usuario:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(connection_frame)
        self.username_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(connection_frame, text="Contraseña:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(connection_frame, show="*")
        self.password_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(connection_frame, text="Directorio Inicial:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.initial_dir_entry = ttk.Entry(connection_frame)
        self.initial_dir_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.EW)

        self.connect_button = ttk.Button(connection_frame, text="Conectar", command=self.connect)
        self.connect_button.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)

        self.disconnect_button = ttk.Button(connection_frame, text="Desconectar", command=self.disconnect)
        self.disconnect_button.grid(row=5, column=1, padx=5, pady=5, sticky=tk.E)

        # Frame de comandos
        command_frame = ttk.LabelFrame(self, text="Comandos")
        command_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(command_frame, text="Comando:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.command_entry = ttk.Entry(command_frame)
        self.command_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        self.execute_button = ttk.Button(command_frame, text="Ejecutar", command=self.execute_command)
        self.execute_button.grid(row=0, column=2, padx=5, pady=5)

        self.command_output = tk.Text(command_frame, height=10)
        self.command_output.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)

        # Frame de transferencia de archivos
        transfer_frame = ttk.LabelFrame(self, text="Transferencia de Archivos")
        transfer_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(transfer_frame, text="Archivo Local:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.local_file_entry = ttk.Entry(transfer_frame)
        self.local_file_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        self.browse_local_button = ttk.Button(transfer_frame, text="Examinar", command=self.browse_local_file)
        self.browse_local_button.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(transfer_frame, text="Archivo Remoto:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.remote_file_entry = ttk.Entry(transfer_frame)
        self.remote_file_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        self.upload_button = ttk.Button(transfer_frame, text="Subir", command=self.upload_file)
        self.upload_button.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        self.download_button = ttk.Button(transfer_frame, text="Descargar", command=self.download_file)
        self.download_button.grid(row=2, column=1, padx=5, pady=5, sticky=tk.E)

        # Frame de túneles
        tunnel_frame = ttk.LabelFrame(self, text="Túneles SSH")
        tunnel_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(tunnel_frame, text="Puerto Local:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.local_port_entry = ttk.Entry(tunnel_frame)
        self.local_port_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(tunnel_frame, text="Host Remoto:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.remote_host_entry = ttk.Entry(tunnel_frame)
        self.remote_host_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(tunnel_frame, text="Puerto Remoto:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.remote_port_entry = ttk.Entry(tunnel_frame)
        self.remote_port_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        self.create_tunnel_button = ttk.Button(tunnel_frame, text="Crear Túnel", command=self.create_tunnel)
        self.create_tunnel_button.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)

        self.close_tunnel_button = ttk.Button(tunnel_frame, text="Cerrar Túnel", command=self.close_tunnel)
        self.close_tunnel_button.grid(row=3, column=1, padx=5, pady=5, sticky=tk.E)

        # Configurar el peso de las columnas y filas
        self.columnconfigure(0, weight=1)
        command_frame.columnconfigure(1, weight=1)
        transfer_frame.columnconfigure(1, weight=1)
        tunnel_frame.columnconfigure(1, weight=1)

    def connect(self):
        hostname = self.hostname_entry.get()
        port = self.port_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        initial_dir = self.initial_dir_entry.get()

        self.connector._connection_details.update({
            'hostname': hostname,
            'port': int(port) if port.isdigit() else 22,
            'username': username,
            'password': password,
            'initial_dir': initial_dir if initial_dir else None
        })

        asyncio.create_task(self._connect())

    async def _connect(self):
        if await self.connector.connect():
            messagebox.showinfo("Conexión SSH", "¡Conexión SSH y SFTP establecida con éxito! 🎉")
        else:
            messagebox.showerror("Error de Conexión", "No se pudo establecer la conexión SSH. 😔")

    def disconnect(self):
        asyncio.create_task(self._disconnect())

    async def _disconnect(self):
        await self.connector.disconnect()
        messagebox.showinfo("Desconexión SSH", "Conexión SSH y SFTP cerrada. Adiós! 👋")

    def execute_command(self):
        command = self.command_entry.get()
        asyncio.create_task(self._execute_command(command))

    async def _execute_command(self, command):
        output, error, status = await self.connector.execute_command(command)
        self.command_output.delete(1.0, tk.END)
        if status == 0:
            self.command_output.insert(tk.END, f"--- Salida del comando '{command}' ---\n")
            self.command_output.insert(tk.END, output)
        else:
            self.command_output.insert(tk.END, f"Comando '{command}' falló con código {status}. Error: {error}")

    def browse_local_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.local_file_entry.delete(0, tk.END)
            self.local_file_entry.insert(0, file_path)

    def upload_file(self):
        local_path = self.local_file_entry.get()
        remote_path = self.remote_file_entry.get()
        if local_path and remote_path:
            asyncio.create_task(self._upload_file(local_path, remote_path))
        else:
            messagebox.showerror("Error", "Por favor, seleccione un archivo local y especifique una ruta remota.")

    async def _upload_file(self, local_path, remote_path):
        if await self.connector.upload_file(local_path, remote_path):
            messagebox.showinfo("Subida de Archivo", "¡Archivo subido con éxito! 🎉")
        else:
            messagebox.showerror("Error", "No se pudo subir el archivo. 😞")

    def download_file(self):
        remote_path = self.remote_file_entry.get()
        local_path = filedialog.asksaveasfilename()
        if remote_path and local_path:
            asyncio.create_task(self._download_file(remote_path, local_path))
        else:
            messagebox.showerror("Error", "Por favor, especifique una ruta remota y seleccione una ubicación local.")

    async def _download_file(self, remote_path, local_path):
        if await self.connector.download_file(remote_path, local_path):
            messagebox.showinfo("Descarga de Archivo", "¡Archivo descargado con éxito! 🎉")
        else:
            messagebox.showerror("Error", "No se pudo descargar el archivo. 😞")

    def create_tunnel(self):
        local_port = self.local_port_entry.get()
        remote_host = self.remote_host_entry.get()
        remote_port = self.remote_port_entry.get()
        if local_port and remote_host and remote_port:
            asyncio.create_task(self._create_tunnel(int(local_port), remote_host, int(remote_port)))
        else:
            messagebox.showerror("Error", "Por favor, especifique el puerto local, el host remoto y el puerto remoto.")

    async def _create_tunnel(self, local_port, remote_host, remote_port):
        if await self.connector.create_tunnel(local_port, remote_host, remote_port):
            messagebox.showinfo("Creación de Túnel", "¡Túnel creado con éxito! 🎉")
        else:
            messagebox.showerror("Error", "No se pudo crear el túnel. 😞")

    def close_tunnel(self):
        local_port = self.local_port_entry.get()
        if local_port:
            asyncio.create_task(self._close_tunnel(int(local_port)))
        else:
            messagebox.showerror("Error", "Por favor, especifique el puerto local.")

    async def _close_tunnel(self, local_port):
        if await self.connector.close_tunnel(local_port):
            messagebox.showinfo("Cierre de Túnel", "¡Túnel cerrado con éxito! 🎉")
        else:
            messagebox.showerror("Error", "No se pudo cerrar el túnel. 😞")

def main():
    connector = SSHConnector()
    app = SSHGUI(connector)
    app.mainloop()

if __name__ == "__main__":
    main()
