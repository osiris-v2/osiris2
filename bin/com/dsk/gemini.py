# dsk/consola.py
import os
import sys
import subprocess
import time

# Ajusta la ruta al archivo gemini.py si es necesario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import gemini

def main():
    """Función principal que maneja la interacción de consola."""

    # Iniciar el proceso de gemini.py en un hilo separado
    gemini_process = subprocess.Popen(["python3", "gemini.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Proceso de Gemini iniciado.")

    while True:
        # Leer input del usuario
        try:
            user_input = input(">>>gemini> ")
        except KeyboardInterrupt:
            print("\nSaliendo...")
            gemini_process.terminate()  # Termina el proceso gemini.py
            break

        # Enviar input al proceso de gemini.py
        gemini_process.stdin.write(f"{user_input}\n".encode('utf-8'))
        gemini_process.stdin.flush()

        # Leer y mostrar la respuesta de gemini.py
        while True:
            line = gemini_process.stdout.readline().decode('utf-8').strip()
            if line:
                print(line)
            else:
                time.sleep(0.1)  # Espera un poco si no hay salida

if __name__ == "__main__":
    main()
