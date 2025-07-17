# main.py
# Este es el archivo principal para mi_proyecto_osiris.
# Desarrollado por Osiris AI.
import os
from session_module import iniciar_sesion_modulo, set_session_context, get_session_context

def iniciar_proyecto():
    print("¡El proyecto mi_proyecto_osiris ha iniciado con exito!")
    print("----------------------------------------------------")
    leer_readme_proyecto()
    leer_ia_control()
    
    # NUEVA INTEGRACION: Inicializar y usar el micronucleo de contexto
    iniciar_sesion_modulo() # Ya inicializa el micronucleo y establece "estado_micronucleo"

    print("\\n--- Demostrando el Micronucleo de Contexto Dinamico ---")
    set_session_context("ultima_accion_ai", "ejecucion_main_py_verificada")
    set_session_context("timestamp_ultima_accion", "2025-07-17_DEMO")
    
    accion = get_session_context("ultima_accion_ai")
    timestamp = get_session_context("timestamp_ultima_accion")
    
    print(f"Valor del contexto 'ultima_accion_ai': {accion}")
    print(f"Valor del contexto 'timestamp_ultima_accion': {timestamp}")
    print("----------------------------------------------------")

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
