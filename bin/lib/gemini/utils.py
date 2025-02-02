import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
from io import BytesIO
import re
import json
import requests
import osiris2
#import hashlib
import subprocess
#import google.generativeai as genai
#import time
import os
import random
import string
import lib.core  as core



#print("UTILS")

def_image_editor = "mtpaint"





def dynmodule(nombre_modulo):
    core.dynmodule(nombre_modulo)
#dynmodule("PRUEBA")

def obtener_datos_multimedia(ruta_archivo):
    """
    Obtiene datos relevantes de un archivo multimedia usando ffprobe y los devuelve en un objeto.

    Args:
        ruta_archivo: La ruta completa al archivo multimedia.

    Returns:
        Un diccionario con los datos relevantes del archivo multimedia, o None si ocurre un error.
    """

    try:
        # Ejecuta ffprobe y captura la salida
        comando = ['com/osiris_env/ffmpeg/bin/ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', ruta_archivo]
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        datos_json = json.loads(resultado.stdout)

        # Extrae información relevante (puedes personalizar esto según tus necesidades)
        datos_multimedia = {
            "formato": datos_json['format']['format_name'],
            "duracion": datos_json['format']['duration'],
            "tamano": datos_json['format']['size'],
            "aspecto": None, #Se calcula más abajo
            "codecs": {},
            "dimensiones": None, #Se calcula más abajo

        }

        # Extraer codecs de cada stream (vídeo y audio)
        for stream in datos_json['streams']:
            codec_type = stream['codec_type']
            codec_name = stream['codec_name']
            datos_multimedia["codecs"][codec_type] = codec_name
            if codec_type == 'video':
                datos_multimedia["dimensiones"] = f"{stream['width']}x{stream['height']}"
                # Calcular el aspect ratio (relación de aspecto)
                try:
                  aspect_ratio = float(stream['width']) / float(stream['height'])
                  datos_multimedia["aspecto"] = f"{aspect_ratio:.2f}"
                except (KeyError, ZeroDivisionError):
                  datos_multimedia["aspecto"] = "N/A"


        return datos_multimedia

    except FileNotFoundError:
        print(f"Error: ffprobe no encontrado. Asegúrate de que esté instalado y en tu PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar ffprobe: {e}")
        print(f"Salida de error: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print("Error al decodificar la salida JSON de ffprobe.")
        return None
    except KeyError as e:
        print(f"Error: Clave no encontrada en la respuesta JSON de ffprobe: {e}")
        return None


# Ejemplo de uso
#ruta = "/ruta/a/tu/archivo.mp4"  # Reemplaza con la ruta de tu archivo
#datos = obtener_datos_multimedia(ruta)

#if datos:
#    print(json.dumps(datos, indent=4)) # Imprime el diccionario en formato JSON legible.











def generar_nombre_imagen(longitud=10, tipo_caracteres='alfanumerico', extension=".jpg"):
    """Genera un nombre de archivo aleatorio con opciones de personalización"""
    if tipo_caracteres == 'alfanumerico':
        caracteres = string.ascii_letters + string.digits
    elif tipo_caracteres == 'letras':
        caracteres = string.ascii_letters
    elif tipo_caracteres == 'numeros':
        caracteres = string.digits
    else:
        raise ValueError("tipo_caracteres debe ser 'alfanumerico', 'letras' o 'numeros'")

    return ''.join(random.choice(caracteres) for i in range(longitud)) + extension





def ini():
    print("widgets modules to gemini")


def dialog_window(text=""):
    ventana_dialogo = tk.Toplevel()
    ventana_dialogo.title("Ventana de Diálogo")
    ventana_dialogo.geometry("400x560")
    ventana_dialogo.wm_attributes("-topmost", True) # Siempre encima

    text_area = scrolledtext.ScrolledText(ventana_dialogo, wrap=tk.WORD, undo=True)
    text_area.insert(tk.END, text)
    text_area.pack(expand=True, fill="both")
    text_area.config(font=("Consolas", 12), background="#f0f0f0", foreground="#333333")
    text_area.focus()

    # Menú contextual para el textarea
    menu_contextual = tk.Menu(ventana_dialogo, tearoff=0)
    menu_contextual.add_command(label="Copiar", command=lambda: text_area.event_generate("<<Copy>>"))
    menu_contextual.add_command(label="Pegar", command=lambda: text_area.event_generate("<<Paste>>"))
    menu_contextual.add_command(label="Cortar", command=lambda: text_area.event_generate("<<Cut>>"))

    text_area.bind("<Button-3>", lambda event: menu_contextual.post(event.x_root, event.y_root) if text_area.config('state')[-1] == 'normal' else None)
    text_area.bind("<Button-1>", lambda event: menu_contextual.unpost() if menu_contextual.winfo_ismapped() else None)

    texto_obtenido = "" # Variable para almacenar el texto

    def enviar_texto():
        nonlocal texto_obtenido # Necesario para modificar la variable fuera del scope
        texto_obtenido = text_area.get("1.0", tk.END).strip()
        ventana_dialogo.destroy()

    boton_enviar = tk.Button(ventana_dialogo, text="Enviar", command=enviar_texto)
    boton_enviar.pack(pady=10)

    ventana_dialogo.wait_window()  # Espera a que se cierre la ventana antes de continuar
    return texto_obtenido # Retorna el texto obtenido





def show_text_window(text):
    ventana_secundaria = tk.Toplevel()
    ventana_secundaria.title("Contenido de la conversación")
    ventana_secundaria.geometry("800x600")
    ventana_secundaria.minsize(800, 400)  # Establece un tamaño mínimo
    ventana_secundaria.wm_attributes("-topmost", True) # Siempre encima


    text_widget = scrolledtext.ScrolledText(ventana_secundaria, wrap="word", undo=True)
    text_widget.insert(tk.END, text)
    text_widget.pack(expand=True, fill="both")  # Permite que el widget se expanda
    text_widget.config(state=tk.NORMAL, font=("Consolas", 12), background="#f0f0f0", foreground="#333333")
    text_widget.focus()

    # Crea un frame para contener los botones, con tamaño fijo
    button_frame = tk.Frame(ventana_secundaria, height=50)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)
    button_frame.config(pady=10)
    button_frame.pack_propagate(False)  # Evita que el frame se redimensione

    def save_text_to_file(text_widget):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if filename:
            try:
                with open(filename, "w", encoding='utf-8') as f:
                    f.write(text_widget.get("1.0", tk.END))
                print(f"Contenido guardado en {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando el archivo: {e}")

    save_button = tk.Button(button_frame, text="Guardar como...", command=lambda: save_text_to_file(text_widget))
    save_button.pack(side=tk.LEFT, padx=5)

    close_button = tk.Button(button_frame, text="Cerrar", command=ventana_secundaria.destroy)
    close_button.pack(side=tk.RIGHT, padx=5)

    def extract_code_blocks(text):
        code_blocks = {}
        pattern = r"```(\w+)\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        for language, code in matches:
            if language not in code_blocks:
                code_blocks[language] = []
            code_blocks[language].append(code.strip())
        return code_blocks

    def create_code_window(code, language):
        code_window = tk.Toplevel(ventana_secundaria)
        code_window.title(language)

        code_widget = scrolledtext.ScrolledText(code_window, wrap="word", undo=True)
        code_widget.insert(tk.END, code)
        code_widget.pack(expand=True, fill="both")  # Permite que el widget se expanda
        code_widget.config(state=tk.NORMAL, font=("Consolas", 12), background="#f0f0f0", foreground="#333333")
        code_widget.focus()

        button_frame_code = tk.Frame(code_window)  # Frame para los botones de la ventana de código
        button_frame_code.pack(side=tk.BOTTOM, fill=tk.X)

        def save_code():
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{language}",
                filetypes=[(f"{language.capitalize()} files", f"*.{language}"), ("All files", "*.*")]
            )
            if filename:
                try:
                    with open(filename, "w", encoding='utf-8') as f:
                        f.write(code)
                    print(f"Código guardado en {filename}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error guardando el código: {e}")

        save_button_code = tk.Button(button_frame_code, text="Guardar", command=save_code)
        save_button_code.pack(side="left", padx=5, pady=5)

        close_button_code = tk.Button(button_frame_code, text="Cerrar", command=code_window.destroy)
        close_button_code.pack(side="left", padx=5, pady=5)

        # Menú contextual para la ventana de código
        menu_contextual = tk.Menu(code_window, tearoff=0)
        menu_contextual.add_command(label="Copiar", command=lambda: code_widget.event_generate("<<Copy>>"))
        menu_contextual.add_command(label="Pegar", command=lambda: code_widget.event_generate("<<Paste>>"))
        menu_contextual.add_command(label="Cortar", command=lambda: code_widget.event_generate("<<Cut>>"))
        menu_contextual.add_command(label="Deshacer", command=lambda: handle_edit_command(code_widget, "undo"))
        menu_contextual.add_command(label="Rehacer", command=lambda: handle_edit_command(code_widget, "redo"))

        code_widget.bind("<Button-3>", lambda event: menu_contextual.post(event.x_root, event.y_root) if code_widget.config('state')[-1] == 'normal' else None)
        code_widget.bind("<Button-1>", lambda event: menu_contextual.unpost() if menu_contextual.winfo_ismapped() else None)

        # Atajos de teclado para la ventana de código
        code_widget.bind("<Control-z>", lambda event: handle_edit_command(code_widget, "undo"))
        code_widget.bind("<Control-y>", lambda event: handle_edit_command(code_widget, "redo"))

    def handle_extract_code():
        updated_text = text_widget.get("1.0", tk.END)
        code_blocks = extract_code_blocks(updated_text)
        if code_blocks:
            for language, codes in code_blocks.items():
                for code in codes:
                    create_code_window(code, language)
        else:
            messagebox.showinfo("Información", "No se encontraron bloques de código en la respuesta.")

    extract_button = tk.Button(button_frame, text="Extraer Código", command=handle_extract_code)
    extract_button.pack(side=tk.LEFT, padx=5)

    # Menú contextual para la ventana principal
    menu_contextual = tk.Menu(ventana_secundaria, tearoff=0)
    menu_contextual.add_command(label="Copiar", command=lambda: text_widget.event_generate("<<Copy>>"))
    menu_contextual.add_command(label="Pegar", command=lambda: text_widget.event_generate("<<Paste>>"))
    menu_contextual.add_command(label="Cortar", command=lambda: text_widget.eventgenerate("<<Cut>>"))
    menu_contextual.add_command(label="Deshacer", command=lambda: handle_edit_command(text_widget, "undo"))
    menu_contextual.add_command(label="Rehacer", command=lambda: handle_edit_command(text_widget, "redo"))

    text_widget.bind("<Button-3>", lambda event: menu_contextual.post(event.x_root, event.y_root) if text_widget.config('state')[-1] == 'normal' else None)
    text_widget.bind("<Button-1>", lambda event: menu_contextual.unpost() if menu_contextual.winfo_ismapped() else None)

    # Atajos de teclado para la ventana principal
    text_widget.bind("<Control-z>", lambda event: handle_edit_command(text_widget, "undo"))
    text_widget.bind("<Control-y>", lambda event: handle_edit_command(text_widget, "redo"))

def handle_edit_command(widget, command):
    try:
        widget.edit(command)
    except tk.TclError:
        print(f"No se puede realizar '{command}' en este momento.")


##### OTRAS FUNCIONES

def export_context(filename,conversation_context):
    """Exporta el contexto de la conversación a un archivo JSON."""
    try:
        with open("com/datas/" +filename, 'w', encoding='utf-8') as f:
            json.dump({"context": conversation_context}, f)
        print(f"Contexto exportado a {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Error exportando contexto: {e}")

def import_context(filename):
    """Importa el contexto de una conversación desde un archivo JSON."""
    global conversation_context
    try:
        with open("com/datas/" +filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            conversation_context = data.get("context", "")
        print(f"Contexto importado desde {filename}")
        return conversation_context
    except Exception as e:
        messagebox.showerror("Error", f"Error importando contexto: {e}")


def load_image(file_path):
    global def_image_editor
    """Carga y muestra una imagen desde un archivo local o una URL usando PIL."""
    try:
        # Verifica si el file_path es una URL
        if file_path.startswith('http://') or file_path.startswith('https://'):
            response = requests.get(file_path)
            response.raise_for_status()  # Lanza un error si la respuesta no es exitosa
            img = Image.open(BytesIO(response.content))  # Carga la imagen desde el contenido de la respuesta
        else:
            img = Image.open(file_path)  # Carga la imagen desde la ruta local
            process = subprocess.Popen(
                    [def_image_editor, file_path],
                    stdin=subprocess.PIPE, # Puedes usar esto para enviar entradas si es necesario
                    stdout=subprocess.DEVNULL,    
                    stderr=subprocess.DEVNULL,       # Redirige la salida de error
                    preexec_fn=os.setpgrp,  # Ejecuta en segundo plano
                )
#        img.show()  # Muestra la imagen
        return img
    except Exception as e:
        messagebox.showerror("Error", f"Error cargando la imagen {file_path}: {e}")
        return None









