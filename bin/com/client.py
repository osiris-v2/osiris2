import websocket
import sys
import time

SERVER_ADDR = "ws://127.0.0.69:8081"
TIMEOUT_SECONDS = 5
SLEEP_BETWEEN_COMMANDS = 0.1

def print_help():
    print(f"""Uso: python3 com/client.py [--help] <comando1> [<comando2> ...]
       --help                    Muestra esta ayuda.
       <comando1> <comando2> ... Los comandos a enviar al servidor WebSocket (ej. /hello /way /date).
                                 Cada comando se enviará secuencialmente en la misma conexión.

Este script conecta a un servidor WebSocket ({SERVER_ADDR}), envía los comandos provistos
como argumentos y muestra las respuestas.
Asegúrate de que 'websocket-client' esté instalado (pip install websocket-client).
""")

def main(args):
    if not args or args[0] == "--help":
        print_help()
        return

    commands_to_send = args

    try:
        print(f"Intentando establecer conexión WebSocket con {SERVER_ADDR}...")
        ws = websocket.create_connection(SERVER_ADDR, timeout=TIMEOUT_SECONDS)
        print("Conexión establecida con el servidor WebSocket.")

        for command in commands_to_send:
            print(f"Enviando: {command}")
            ws.send(command)
            
            # Esperar un momento para la respuesta
            time.sleep(SLEEP_BETWEEN_COMMANDS) 
            result = ws.recv()
            print(f"Recibido para '{command}': {result}")

        ws.close()
        print("Conexión WebSocket cerrada.")

    except websocket._exceptions.WebSocketConnectionClosedException as e:
        print(f"ERROR: La conexión WebSocket se cerró inesperadamente. ¿Está el servidor activo en {SERVER_ADDR}? Detalle: {e}")
        sys.exit(1)
    except websocket._exceptions.WebSocketTimeoutException:
        print(f"ERROR: Tiempo de espera agotado al conectar o recibir mensajes del servidor WebSocket. Asegúrate de que el servidor esté ejecutándose en {SERVER_ADDR}.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR al conectar o interactuar con el servidor WebSocket: {e}")
        # Comprobar si el error es por falta del módulo
        if "No module named 'websocket'" in str(e):
            print("El módulo 'websocket-client' no está instalado. Por favor, instálalo con: pip install websocket-client")
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])
