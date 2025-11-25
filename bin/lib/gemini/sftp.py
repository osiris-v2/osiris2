import paramiko
import getpass
import os

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
            print("¡Conexión SSH y SFTP establecida con éxito! 🎉")
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

# Ejemplo de uso (esto no se ejecutará directamente al importar, solo muestra cómo usarlo)
async def main_sftp_example():
    connector = SSHConnector()
    if await connector.connect():
        output, error, status = await connector.execute_command("ls -la")
        if status == 0:
            print("--- Salida del comando 'ls -la' ---")
            print(output)
        
        print("Intentando un comando que falla para probar la reconexión...")
        output_fail, error_fail, status_fail = await connector.execute_command("ls /no/existe")
        if status_fail != 0:
            print(f"Comando fallido (esperado): {error_fail}")
            # La conexión debería intentar reconectarse en el siguiente comando
        
        print("Volviendo a ejecutar un comando para verificar la persistencia...")
        output2, error2, status2 = await connector.execute_command("pwd")
        if status2 == 0:
            print("--- Salida del comando 'pwd' ---")
            print(output2)
        
        await connector.disconnect()
    else:
        print("No se pudo establecer la conexión SSH. 😔")

#Para que el ejemplo se ejecute si el archivo se corre directamente (no lo hará en Osiris)
#if __name__ == "__main__":
#    import asyncio
#    asyncio.run(main_sftp_example())
