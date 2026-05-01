LOCAL_FS_WRITE_FILE
PATH="/var/osiris2/DOCS/LIBSFTPAI.md"
CONTENT="""
# Manual de Usuario para Cliente SSH Avanzado

## Introducción

El Cliente SSH Avanzado es una herramienta gráfica que permite gestionar conexiones SSH, ejecutar comandos remotos, transferir archivos y crear túneles SSH de manera intuitiva. Este manual cubre todas las funcionalidades disponibles en la aplicación.

## Requisitos del Sistema

- Sistema operativo: Linux, Windows o macOS
- Python 3.7 o superior
- Bibliotecas requeridas: paramiko, tkinter

## Instalación

1. Asegúrese de tener Python 3.7 o superior instalado en su sistema.
2. Instale las bibliotecas requeridas ejecutando:
   ```
   pip install paramiko
   ```
3. Descargue el archivo `sftp.py` y colóquelo en el directorio deseado.
4. Ejecute el archivo con Python:
   ```
   python sftp.py
   ```

## Interfaz de Usuario

La interfaz de usuario está organizada en varias secciones:

1. **Conexión SSH**: Para establecer y gestionar conexiones SSH.
2. **Comandos**: Para ejecutar comandos remotos.
3. **Transferencia de Archivos**: Para subir y descargar archivos.
4. **Túneles SSH**: Para crear y gestionar túneles SSH.

## Conexión SSH

### Establecer una Conexión

1. Complete los campos en la sección "Conexión SSH":
   - **Hostname**: Dirección IP o nombre de dominio del servidor remoto.
   - **Puerto**: Puerto SSH (por defecto 22).
   - **Usuario**: Nombre de usuario para la autenticación.
   - **Contraseña**: Contraseña para la autenticación.
   - **Directorio Inicial**: Directorio remoto donde se establecerá la conexión (opcional).
2. Haga clic en el botón "Conectar".

### Desconectar

1. Haga clic en el botón "Desconectar" para cerrar la conexión SSH actual.

## Ejecución de Comandos

### Ejecutar un Comando

1. Ingrese el comando que desea ejecutar en el campo "Comando".
2. Haga clic en el botón "Ejecutar".
3. La salida del comando se mostrará en el área de texto "Salida del Comando".

### Comandos Disponibles

Aquí hay una lista de comandos útiles que pueden ejecutarse:

- `ls -la`: Listar archivos y directorios.
- `pwd`: Mostrar el directorio actual.
- `cd [directorio]`: Cambiar de directorio.
- `mkdir [directorio]`: Crear un nuevo directorio.
- `rm [archivo]`: Eliminar un archivo.
- `rmdir [directorio]`: Eliminar un directorio.
- `cp [origen] [destino]`: Copiar un archivo.
- `mv [origen] [destino]`: Mover un archivo.
- `cat [archivo]`: Mostrar el contenido de un archivo.
- `nano [archivo]`: Editar un archivo con nano.
- `vim [archivo]`: Editar un archivo con vim.
- `chmod [permisos] [archivo]`: Cambiar los permisos de un archivo.
- `chown [usuario]:[grupo] [archivo]`: Cambiar el propietario de un archivo.
- `ps aux`: Mostrar los procesos en ejecución.
- `top`: Mostrar los procesos en tiempo real.
- `kill [PID]`: Terminar un proceso.
- `df -h`: Mostrar el uso del disco.
- `free -m`: Mostrar el uso de la memoria.
- `ifconfig`: Mostrar la configuración de red.
- `ping [host]`: Ping a un host.
- `traceroute [host]`: Traceroute a un host.
- `netstat -tuln`: Mostrar las conexiones de red.
- `wget [URL]`: Descargar un archivo desde una URL.
- `curl [URL]`: Obtener el contenido de una URL.
- `ssh [usuario]@[host]`: Conectarse a un host remoto.
- `scp [origen] [destino]`: Copiar un archivo a un host remoto.
- `rsync [origen] [destino]`: Sincronizar archivos con un host remoto.

## Transferencia de Archivos

### Subir un Archivo

1. Seleccione el archivo local que desea subir haciendo clic en el botón "Examinar".
2. Ingrese la ruta remota donde se subirá el archivo en el campo "Archivo Remoto".
3. Haga clic en el botón "Subir".

### Descargar un Archivo

1. Ingrese la ruta remota del archivo que desea descargar en el campo "Archivo Remoto".
2. Seleccione la ubicación local donde se descargará el archivo haciendo clic en el botón "Examinar".
3. Haga clic en el botón "Descargar".

## Túneles SSH

### Crear un Túnel

1. Ingrese el puerto local en el campo "Puerto Local".
2. Ingrese el host remoto en el campo "Host Remoto".
3. Ingrese el puerto remoto en el campo "Puerto Remoto".
4. Haga clic en el botón "Crear Túnel".

### Cerrar un Túnel

1. Ingrese el puerto local del túnel que desea cerrar en el campo "Puerto Local".
2. Haga clic en el botón "Cerrar Túnel".

## Historial de Comandos

Para ver el historial de comandos ejecutados:

1. Ejecute el comando `history` en el campo "Comando".
2. Haga clic en el botón "Ejecutar".
3. El historial de comandos se mostrará en el área de texto "Salida del Comando".

## Información de Sesión

Para obtener información sobre la sesión actual:

1. Ejecute el comando `session_info` en el campo "Comando".
2. Haga clic en el botón "Ejecutar".
3. La información de la sesión se mostrará en el área de texto "Salida del Comando".

## Solución de Problemas

### Problemas de Conexión

- Asegúrese de que el servidor remoto esté en funcionamiento y accesible.
- Verifique que el hostname, el puerto y las credenciales sean correctos.
- Asegúrese de que el firewall no esté bloqueando la conexión SSH.

### Problemas de Transferencia de Archivos

- Verifique que las rutas locales y remotas sean correctas.
- Asegúrese de que tenga permisos para acceder a los archivos y directorios.
- Compruebe que haya suficiente espacio en disco en el servidor remoto.

### Problemas de Túneles SSH

- Asegúrese de que el puerto local no esté en uso por otra aplicación.
- Verifique que el host remoto y el puerto remoto sean accesibles.
- Compruebe que el firewall no esté bloqueando el tráfico del túnel.

## Conclusión

El Cliente SSH Avanzado proporciona una interfaz gráfica intuitiva para gestionar conexiones SSH, ejecutar comandos remotos, transferir archivos y crear túneles SSH. Este manual cubre todas las funcionalidades disponibles en la aplicación y proporciona instrucciones detalladas para su uso efectivo.
"""
OVERWRITE="True"