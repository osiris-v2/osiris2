# main.py
# Este es el archivo principal para mi_proyecto_osiris.
# Desarrollado por Osiris AI.
import os
from session_module import iniciar_sesion_modulo # Importar el nuevo modulo

def iniciar_proyecto():
    print("¡El proyecto mi_proyecto_osiris ha iniciado con exito!")
    print("----------------------------------------------------")
    # La funcion listar_archivos_proyecto() solo muestra la intencion del comando 'ls'.
    # Para la salida real de 'ls', usamos un CRO.
    # print("Archivos en el proyecto mi_proyecto_osiris:")
    # comando_ls = "ls ./projects/mi_proyecto_osiris"
    # print(f"Ejecutando: {comando_ls}")
    leer_readme_proyecto()
    leer_ia_control()
    iniciar_sesion_modulo() # Nueva llamada a la funcion del modulo de sesion

def leer_readme_proyecto():
    print("\\n--- Contenido de readme.txt ---")
    readme_path = "./projects/mi_proyecto_osiris/readme.txt"
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except FileNotFoundError:
        print(f"Error: El archivo {readme_path} no fue encontrado.")
    except Exception as e:
        print(f"Ocurrio un error al leer readme.txt: {e}")
    print("-------------------------------")

def leer_ia_control():
    print("\\n--- Contenido de ia_control ---")
    ia_control_path = "./projects/mi_proyecto_osiris/ia_control"
    try:
        with open(ia_control_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except FileNotFoundError:
        print(f"Error: El archivo {ia_control_path} no fue encontrado.")
    except Exception as e:
        print(f"Ocurrio un error al leer ia_control: {e}")
    print("-------------------------------")


if __name__ == "__main__":
    iniciar_proyecto()
