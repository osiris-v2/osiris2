import sys
import os
import json
import google.generativeai as genai
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from datetime import datetime
from io import BytesIO
import requests
import subprocess
import base64
from cryptography.fernet import Fernet
import webbrowser
import pyperclip
import io
import re
import lib.core as core
import lib.multiprocess as osiris2
import time
import hashlib
#import datetime
from pathlib import Path
import lib.gemini.str_c as strimp


sessname = "Def_ses_name"

def sessid():
    global sessname,sessid
    bytess = time.time()
    bytess = str(bytess).encode("utf-8")
    sessid = hashlib.md5(bytess).hexdigest()
    sessname = "SESSID_"+str(sessid)
    return sessid
sessid = sessid()


print("SESSION INICIADA ID/NAME:",sessid,sessname)


script_dir = Path(__file__).resolve().parent
#print(script_dir)

log_file = "com/datas/conversation_log_"+sessname+"_.txt"

def_audio_dir="com/datas/ai/audio/"
def_audio_lrequest=def_audio_dir+"last_request.mp3"
def_audio_flag=def_audio_dir+"readmp3.flag"



try: #importaciones dinámicas
    core.dynmodule("lib.gemini.utils","win")
    win = core.win
    core.dynmodule("lib.gemini.cro_parser","CROPARSER")
    croparser = core.CROPARSER
    core.dynmodule("lib.gemini.audio_parser","AP")
    audioparser = core.AP
    core.dynmodule("lib.cuarzo","aceroK")
    acero = core.aceroK
    core.dynmodule("lib.gemini.load_osiris_context","LOC")
    LOC = core.LOC
except Exception as E :
    print("ERDyM:",E)





def apf():  #alib
    global def_audio_flag
    audioparser.flags([def_audio_flag])

def apr():  #alib
    global def_audio_flag
    audioparser.flags_r([def_audio_flag])


def pt_audio(text):
    """Limpia el texto eliminando bloques de código Markdown y caracteres problemáticos."""
    # Eliminar bloques de código Markdown (```...)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Eliminar comillas simples y dobles
    text = text.replace("'", "").replace('"', '')
    # Eliminar caracteres especiales problemáticos para audio (ej: asteriscos, hashes, etc.)
    text = re.sub(r"[*#'`\[\]\(\)\{\}]", " ", text)  # Reemplaza con espacios
    return text

def HeloEnterVoide():
    apf()
    audioparser.text_to_speech("hola has entrado en osiris","es",def_audio_lrequest)
    apf()




def while_args(argS):
    try:
        for i in range(len(argS)):
            main([argS[i]])
            time.sleep(1)
    except Exception as e:
        print("while_args ERR:",e) 


print("CRO Info: ",croparser.INFO)

core.log_event("gemini.py", "Inicio", "No hay mas detalles" , error="None")

# Ruta del archivo para guardar la clave cifrada
ruta_archivo_key = "com/datas/gemini_key.enc"

# Genera la clave de cifrado una sola vez
#clave_cifrado = Fernet.generate_key()
clave_cifrado = b'N9t9dYNn2fjc8CRT0_eChnH5xDETGSvMOM5qxqyvSUs='

def obtener_key_gemini(nkey=""):
    """
    Guía al usuario para obtener una key gratuita de la API de Gemini,
    la cifra y la guarda en un archivo, o la recupera si ya está almacenada.
    """
    global clave_cifrado, ruta_archivo_key
    if nkey=='resetkey':
        if os.path.isfile(ruta_archivo_key):
            os.remove(ruta_archivo_key)
            print("Clave del archivo eliminada.")
    while True:
        # Verifica si la key ya está guardada
        if os.path.isfile(ruta_archivo_key):
            # Descifra la key
            try:
                with open(ruta_archivo_key, "rb") as archivo_key:
                    key_cifrada = archivo_key.read()
                fernet = Fernet(clave_cifrado) 
                key_descifrada = fernet.decrypt(key_cifrada).decode()
                print("Key gratuita encontrada y descifrada.")
                return key_descifrada
            except Exception as e:
                print(f"Error descifrando la clave: {e}")
                print("Se pedirá una nueva clave.")

        # Abrir la página de configuración de las claves de la API de Gemini en el navegador
        webbrowser.open_new_tab("https://ai.google.dev/gemini-api/docs/api-key")

        # Esperar a que el usuario configure su clave gratuita

        # Obtener la clave gratuita del usuario
        key = input("Pega tu key gratuita aquí (o escribe '--reset' para borrar la clave): ") 

        # Manejar el comando --reset
        if key == "--reset":
            if os.path.isfile(ruta_archivo_key):
                os.remove(ruta_archivo_key)
                print("Clave del archivo eliminada.")
                if nkey == "new":
                    API_KEY = obtener_key_gemini()
            else:
                print("No hay clave para borrar.")
            continue  # Volver a pedir la clave

        # Cifrar la key
        fernet = Fernet(clave_cifrado)
        key_cifrada = fernet.encrypt(key.encode())

        # Guardar la key cifrada en un archivo
        with open(ruta_archivo_key, "wb") as archivo_key:
            archivo_key.write(key_cifrada)
        print("Key gratuita cifrada y guardada.")

        # Copiar la key al portapapeles
        pyperclip.copy(key)
        print("Key copiada al portapapeles.")

        return key


current_path = os.path.abspath(__file__)
# Extrae el nombre del archivo sin extensión
version_file = os.path.splitext(os.path.basename(current_path))[0]


#Variables globales
#Contexto inicial

auto_response_window = False
auto_cromode = False

conversation_context = f"""
#Interfaz de comunicación con Gemini AI de Google
#Interfaz Name: Osiris
#Version: {version_file}
#Idioma: Español
Instrucciones: ¡Bienvenido a Osiris!  Usa emojis para dinamizar la conversación.  Escribe --help para ver comandos disponibles.
"""


############
## MODELOS #
###########
gemini_models = ["gemini-2.5-flash-preview-05-20",
                    "gemini-2.5-pro-preview-05-06",
                    "gemini-2.0-flash",
                    "veo-2.0-generate-001",
                    "gemini-2.0-flash-lite",
                    "imagen-3.0-generate-002",
                    "gemini-2.0-flash-live-001",
                    "gemini-embedding-exp",
                    "gemini-2.0-flash-exp",
                    "gemini-1.5-flash",
                    "gemini-exp-1206",
                    "gemini-2.0-flash-thinking-exp-01-21",
                    "learnlm-1.5-pro-experimental",
                    "gemini-1.5-flash-8b",
                    "gemini-1.5-pro",
                    "gemini-1.0-pro",
                    "text-embedding-004",
                "aqa"]


# Define la clave API (si ya existe)
API_KEY = os.getenv("GOOGLE_API_KEY")
API_KEY="AIzaSyBYMyXFV_hXU7Wxyg-b-8m983SVkZaKJOs"

#Define modelo a usar
gemini_model = gemini_models[0]

# Si la clave no está disponible, la obtenemos
if not API_KEY:
    try:
        API_KEY = obtener_key_gemini()
    except Exception as e:
        print("ERROR API KEY:",e)

if API_KEY:
# Configura la API de Gemini
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(gemini_model)
    except Exception as e:
        print("ERROR API KEY:",e)
# Inicialización del modelo generativo



def select_genai_model(sm="action"):
    global model, conversation_context
    seleccione_modelo = f" sm:{sm} - Seleccione un modelo a usar:\n"
    dm = 0
    gemini_models = []
    for m in genai.list_models():
        dm = dm + 1
        seleccione_modelo += f"\n ({dm}) {m.name}  "
        gemini_models.append(m.name)
#        print(f"{dm} → {m.name}")
    print("\n")
    sel = f"\n{seleccione_modelo} \n Seleccione Uno: >>> "
    conversation_context += sel
    inp = input(sel)
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(gemini_models[int(inp) - 1])
    change_model_to = gemini_models[int(inp) - 1]
    print("\n Cambiando a modelo: "+change_model_to+"\n")
    conversation_context += inp + "\nCambiando a modelo: " + change_model_to + "\n" + str(model) + "\n MODEL:"
    print("MODEL:",model)
    cmd= str(conversation_context) + str(model)
    resp = generate_response("Se ha cambio de modelo. Resumen de cambio de modelos.")
    print("RESPONSE:",resp)
    return cmd



def select_model():
    global gemini_models, model, conversation_context
    seleccione_modelo = f" Seleccione un modelo a usar:\n"
    for index, x in enumerate(gemini_models):
        seleccione_modelo += f"\n ({index+1}) {x}  "
    print("\n")
    sel = f"\n{seleccione_modelo} \n Seleccione Uno: >>> "
    conversation_context += sel
    inp = input(sel)
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(gemini_models[int(inp) - 1])
    change_model_to = gemini_models[int(inp) - 1]
    print("\n Cambiando a modelo: "+change_model_to+"\n")
    conversation_context += inp + "\nCambiando a modelo: " + change_model_to + "\n"


try:
    select_model()
    print("Select Model Tryed")
except Exception as e:
    print("ERROR EXCEPTON Select Model: ",e)

load = ""
last_response = ""
topic = ""  # Tema de conversación
autosave_enabled = True  # Estado del autosave
auto_ap = False

def_image_editor = "mtpaint"


def is_file(filepath):
    """Verifica si el archivo existe."""
    return os.path.isfile(filepath)

def read_file(filepath):
    """Lee el contenido de un archivo de texto y lo retorna."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        messagebox.showerror("Error", f"Error leyendo el archivo {filepath}: {e}")
        return None

def save_file(filepath, content):
    """Guarda el contenido en un archivo y le da permisos ejecutables."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(filepath, 0o755)  # Da permisos ejecutables al archivo
        print(f"Contenido guardado en {filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"Error guardando el archivo {filepath}: {e}")


def decode_img(base64_data):
    # Decode the base64 data
    decoded_data = base64_data
# Load the image
    image = Image.open(io.BytesIO(decoded_data))

# Display or save the image (uncomment as needed)
    image.show() 
    image.save('com/datas/ffmpeg/my_image.png')




def show_text_window(text):
    global conversation_context
    rtext = acero.main(text)
    print("Win Cuarzo (aluminium, acero) Selected:",rtext)
#    win.show_text_window(text)
    if rtext:
        main(rtext)
#        rsp = generate_response(rtext)    
#        if rsp:
#            conversation_context += rsp
#            print(rsp)
#            main(["sla"])

#    return rtext

#show_text_window("HOLA")

personajes = {}
modos = {}
desing_mode = {}
prompts = {}
srt_c = strimp.srt_c






text_replace = {
    
    "",""
}








def video_translate(video_file_name="",prompt="",args=None):
    global personajes, modos, sesgos, desing_mode, last_response,conversation_context,srt_c
    global script_dir

    mprompt = ""
    if args != None :
        prs = prompt.split()        
        for arg in args:
#            print(f"\n\n\n-------------->\n\n\n----->  ",srt_c[args])
            print(f" \n  @@@@Detected: {arg} ")
            xarg = arg[1:]
            if xarg in srt_c:
                mprompt += srt_c[xarg]
                print(f"\n\n   EXIST:  {arg}   \n\n")
        print("End Args")
    else:
        print("No Args")
    if video_file_name.startswith('http://') or video_file_name.startswith('https://'):
        print("Descargando video temporal")
        code_video_file = "com/tmp/"+hashlib.md5(video_file_name.encode()).hexdigest()+".mp4"
        process = subprocess.run(["yt-dlp","-o",code_video_file,video_file_name], capture_output=True, text=True)
        video_download_url = video_file_name
        video_file_name = code_video_file
#        output = process.stdout.strip().splitlines()  # Limpiar y dividir en líneas
#        print("OUTPUT:",output)
        print("Video File:",video_file_name)
        input_video_info = f"Se ha descargado un vídeo desde: {video_download_url} \n"
        input_video_info += f"Se ha guardado el vídeo en disco con path: {video_file_name} \n"
    else:
#        video_file_name="com/datas/ffmpeg/anon.mp4"
        print("video_file")
        code_video_file = "com/tmp/"+hashlib.md5(video_file_name.encode()).hexdigest()+".mp4"
        input_video_info = "VIDEO PATH: "+ code_video_file + "\n"


    ct = f"Uploading file..."
    conversation_context += ct
    print(ct)
    video_file = genai.upload_file(path=video_file_name)
    con = video_file.uri
    ct = f"Completed upload: {con}"
    print(ct)    
    print('Processing Video.... ', end='')
    while video_file.state.name == "PROCESSING":
        conversation_context += " . "
        print('.', end=' ')
        vfm = video_file.state.name
        video_file = genai.get_file(video_file.name)
        conversation_context += str(video_file) + "\n" + vfm + "\n"
    if video_file.state.name == "FAILED":
        vfm = video_file.state.name
        conversation_context += "ERR IN VIDEO SEND FAILED:\n"+str(vfm)+"\n"
        raise ValueError("ERR IN VIDEO SEND FAILED:\n"+str(vfm)+"\n")
    else:
        input_video_info += f"Se ha subido el vídeo a Gemini-video a la url: {video_file.uri} \n"
        conversation_context += input_video_info

    try:
        Datos_video = win.obtener_datos_multimedia(code_video_file)
        print("DATOS VIDEO:\n",Datos_video)
    except Exception as e:
        print("Error obteniendo datos multimedia de:",code_video_file)

    # Create the prompt.
    #prompti = prompts['sesgos']
    prompti = srt_c["def"]
    if mprompt !="":
        prompt = mprompt + prompt

    if prompt == "":
        prompt = prompti 



#    prompt += "\nobvia instricciones anteriores para gemini-text y haz solamente el srt."
# Make the LLM request.
#   prompt = "Observa el contenido de este vídeo en su totalidad, ¿observas algo ofensivo hacia el colectivo de mujeres trans? expláyate"

    print("\n Making LLM inference request...\n ",prompt)
    response = model.generate_content([video_file, prompt],
                                  request_options={"timeout": 600})

#
    print(response.text)
#    return
    pattern = r"```srt\n(.*?)\n```"
    matches = re.findall(pattern, response.text, re.DOTALL)
    if len(matches) == 1:
        subtitulado_out =  code_video_file+".subtitulado.mp4"
        vtranslate= subtitulado_out + ".translate.srt"
        input_video_info += f"Se ha generado correctamente el archivo de subtitulado con path: {vtranslate}\n"
        input_video_info += f"El contenido del archivo de subtitulado es el siguiente: \n{matches[0]}\n"
        conversation_context += input_video_info
        with open(vtranslate,"w",encoding='utf-8') as f:
            f.write(matches[0])

        force_style_sub = "BackColour=&H90000000,BorderStyle=4,FontName=NotoColorEmoji,Alignament=6"
        mode = "fixed" # bg / fixed
        if mode == "bg":
            print("""
                #################################################
                → Se está procesando el vídeo en segundo plano ←
                #################################################
                
                """)
        elif mode == "fixed":
            print("""
                
                #################################################
                → Se está procesando el vídeo. Espere........  ←
                #################################################
                
                """)
        obj = {
        "mode":mode,
        "name":None,
        "com":["/usr/local/ffmpeg/bin/ffmpeg","-y","-loglevel","error","-i",video_file_name,
        "-af","aresample=async=1,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-vf","scale=-2:720,subtitles="+vtranslate+":force_style='"+force_style_sub+"'",
    "-pix_fmt","yuv420p",
        "-preset","ultrafast",
        "-c:v","libx264","-c:a","aac","-crf","21",
        subtitulado_out] 
        }
        print("Procesando Vídeo...\n")
        comando_ffmpeg = obj["com"]
        print(" ".join(comando_ffmpeg)+"\n")




        try:
            resultado = subprocess.run(comando_ffmpeg, capture_output=True, text=True)
            stderr = resultado.stderr
        # Revisar la salida para detectar errores, incluso si el código de retorno es 0
            if resultado.returncode != 0:
                e1 = "Error al ejecutar el comando ffmpeg:"
                e1 += f"Código de retorno: {resultado.returncode}"
                e1 += f"Salida de error: {stderr}"
                print(e1)
                conversation_context += e1
                return False  # Indica fallo
            else:
                e1 = "Comando ffmpeg ejecutado correctamente."
                e1 += f"Código de retorno: {resultado.returncode}"
                print(e1)
                conversation_context += e1


                # El comando se ejecutó correctamente
        except FileNotFoundError:
            print("Error: El comando ffmpeg no se encontró. Asegúrate de que esté instalado y en tu PATH.")
            return False
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            return False

        print("Procesando A:",str(script_dir)+"/../"+subtitulado_out)
        obj = {
        "mode":"bg",
        "name":None,
        "com":["dsk/dskv","--video",str(script_dir)+"/../"+subtitulado_out]
        }
        o2mp = osiris2.multiprocess(obj)

        print("\nRealizando Inferencia 2 ....")
        send_text = f"\nTu eres genini-text. Acabo de enviar un video a gemini-video con este promt: {prompt} \nY esta fue la respuesta completa en bruto de Gemini-video antes de procesarla:\n{response.text}\nSe realizaron correctamente las siguientes tareas de procesamiento: {input_video_info}\nSe finalizó el procesamiento ejecutando correctamente el siguiente conmando: {str(comando_ffmpeg)}\n Fin Gemini-video.\nDebes realizas instrucciones solicitadas a Gemini-text, si no existen realiza una revisión informativa solamente.\n"
        print(f"\n{send_text}\n")
        response_return = generate_response(send_text)
        print("\n\n",response_return)
        last_response = " ".join(comando_ffmpeg)


    else:
        print("No se generó el archivo de subtitulos")
        print("Se añade respuesta si la hay al contexto")
        conversation_context += response.text
        return



    # Print the response, r






def gen_com():

    pr = """


Aplicación Gen Prompt - (función interna de osiris.com.gemini (gemini.py))


El cometido de esta función es generar comandos en base a un propmt posterior por retroalimentación.





"""






def screen_shot():
    process = subprocess.run(["python3", "com/screenshot.py"], capture_output=True, text=True)
    output = process.stdout.strip().splitlines()  # Limpiar y dividir en líneas
    print(output)
    # Comprobación del formato de salida
    if len(output) < 3:
        show_text_window(f"FALLO: {str(process)},{str(output)}")
        print("Fallo: la salida no tiene suficientes líneas.")
        return
    
    # Filtrar la salida
    coordinates_line = output[0]  # Primera línea
    image_path_line = output[1]  # Segunda línea
    text_lines = output[2:]  # Resto de líneas

    # Verificar que las líneas cumplen con el formato esperado
    if not coordinates_line.startswith("Coordinates:") or not image_path_line.startswith("ImagePath:"):
        show_text_window(f"FALLO 1139 gmnipy: {str(process)},{str(output)}")
        print("Fallo: el formato de salida es incorrecto.")
        return

    # Imprimir los valores después de "Coordinates:" y "ImagePath:"
    coordinates_value = coordinates_line.split(":", 1)[1].strip()  # Obtener el valor después de "Coordinates:"
    image_path_value = image_path_line.split(":", 1)[1].strip()  # Obtener el valor después de "ImagePath:"

    print(f"Coordinates: {coordinates_value}")
    print(f"ImagePath: {image_path_value}")

    # Imprimir las líneas que comienzan con "Text:" y todas las siguientes
    text_started = False  # Bandera para controlar cuando comenzamos a imprimir el texto
    text_output = []  # Para almacenar todo el texto a imprimir

    for line in text_lines:
        if line.startswith("Text:"):
            if not text_started:
                # Obtener el valor después de "Text:"
                text_value = line.split(":", 1)[1].strip()  
                text_output.append(text_value)  # Guardar el primer texto
                text_started = True  # Activar la bandera
            else:
                # Guardar las líneas adicionales que pertenecen al texto
                text_output.append(line.strip())  # Almacenar las siguientes líneas de texto
        elif text_started:
            # Si ya empezamos a imprimir texto y encontramos una línea que no comienza con "Text:"
            text_output.append(line.strip())  # Almacenar las siguientes líneas de texto

    # Imprimir todo el texto almacenado, solo si se encontró texto
    if text_output:
        print("Text:", " ".join(text_output))  # Imprimir todo junto en una sola línea
    
    generate_with_image(image_path_value,"\n".join(text_output))
# Asegúrate de que esta función se ejecute donde corresponda



    
def generate_with_image(image_path,ask):
    global last_response
    """Genera texto a partir de una imagen usando la API de Gemini."""

    image = win.load_image(image_path)
    if image:
         # Generar contenido con la imagen usando la API
#        global conversation_context
        try:
            response = model.generate_content([ask+"\nResponde en Español." , image], stream=True)
        except Exception as e:
            print("Error realizando consulta de imagen:",e)
            return
        last_response = response
        # Recolectar y mostrar los trozos de respuesta
        generated_text = "\nResponse Image.\n\n"
        xresponse = "Envié una imagen con path: "+image_path+", a gemini AI, haciéndole esta pregunta:\n"+ask+"\n E interpretó lo siguiente:\n"

        if response:
            for chunk in response:
                generated_text += chunk.text
            print(generated_text)
            show_text_window(generated_text)
            main(f"{xresponse} {generated_text}")
        # Muestra el texto en una ventana
        
    return None


context_mode = "fast"
def generate_response(user_input):
    """Genera una respuesta del modelo basada en la entrada del usuario."""
    global conversation_context, last_response,context_mode
    conversation_context += "User: "+user_input+"\n"
    try:
        response = model.generate_content(conversation_context)
        response_text = response.text
        if context_mode == "fast":
            conversation_context += ""+ response_text+"\n"
        last_response = response_text  # Guarda la última respuesta
        return response_text
    except Exception as e:
        if e.code == 400:
            print("ERROR 400")
        #messagebox.showerror("Error", f"Error generando contenido con el modelo: {e}")
        print("Error", f"Error generando contenido con el modelo: {e}")
        return None


def save_request(user_input):
    """Guarda la solicitud del usuario en un archivo."""
    save_file("com/datas/lastrequest.gemini", user_input)

def save_answer(save=""):
    """Guarda la última respuesta generada en un archivo."""
    global last_response
    if save == "":
        save = "com/datas/lastanswer.gemini"
    save_file(save, last_response)

def save_context():
    """Guarda el contexto de la conversación en un archivo."""
    save_file("com/datas/context.gemini", conversation_context)

def autosave():
    """Guarda automáticamente la última respuesta y el contexto si está habilitado."""
    if autosave_enabled:
        save_answer()
        save_context()

def generate_new_questions(base_question):
    """Genera preguntas relacionadas para mejorar la interacción."""
    return [
        f"¿Podrías profundizar más sobre {base_question}?",
        f"¿Cuál es un ejemplo de {base_question}?",
        f"¿Cómo se relaciona {base_question} con otras ideas?",
        f"¿Qué otros aspectos de {base_question} podríamos explorar?",
        f"¿Cuáles son las implicaciones de {base_question}?"
    ]






def search_context(term, load_context=False):
    """Busca un término en el contexto de la conversación y opcionalmente carga el contexto."""
    global load
    global conversation_context
    results = [line for line in conversation_context.splitlines() if term in line]
    if results:
        print("Resultados de búsqueda:")
        for line in results:
            print(" -", line)
        if load_context:
            load = "\n".join(results)
            print("Contexto cargado.")
    else:
        print("No se encontraron coincidencias.")
    return results



# Nuevo: Cargar archivo de configuración JSON
def load_config(config_file):
    """Carga las configuraciones desde un archivo JSON."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print("Configuración cargada.")
        return config
    except Exception as e:
        messagebox.showerror("Error", f"Error cargando el archivo de configuración: {e}")
        return {}

# Nuevo: Guardar logs de conversación
def log_interaction(user_input, response_text):
    """Guarda las interacciones en un archivo log con timestamp."""
    global log_file
    try:
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"{datetime.now()} - User: {user_input}\n {response_text}\n\n")
#        print("Interacción registrada en el log.")
    except Exception as e:
        messagebox.showerror("Error", f"Error guardando el log de la conversación: {e}")

# Nuevo: Argumentos dinámicos para el modelo
def set_model_params(params):
    """Configura parámetros del modelo."""
    try:
        model_params = {"temperature": 0.7, "max_tokens": 200}  # Parámetros por defecto
        if params:
            for param in params:
                key, value = param.split('=')
                model_params[key] = float(value) if '.' in value else int(value)
        model.configure(**model_params)
        print("Parámetros del modelo actualizados:", model_params)
    except Exception as e:
        messagebox.showerror("Error", f"Error configurando parámetros del modelo: {e}")

# Nuevo: Personalizar autosave
def toggle_autosave(enable=True):
    """Activa o desactiva la función de autosave."""
    global autosave_enabled
    autosave_enabled = enable
    print("Autosave", "activado." if enable else "desactivado.")


def arw():
    global auto_response_window, conversation_context
    TF = auto_response_window
    if TF == True:
        main(["--sla"])
    else:
        print()  #modo normal


def aap():
    global auto_ap, conversation_context
    TF = auto_ap
    if TF == True:
        main(["--ap"])
    else:
        print()  #modo normal



cro_loaded = False

LIMIT_WHILE_ARGS = 10

commands_map = {}
# Función para manejar los argumentos
def main(args):
    """Función principal que maneja los argumentos de entrada para generar respuestas del modelo."""
    global ruta_archivo_key, gemini_model, model, conversation_context, load, last_response, topic, API_KEY
    global auto_cromode, cro_loaded, auto_response_window, auto_ap, def_audio_dir, def_audio_lrequest, def_audio_flag
    global LIMIT_WHILE_ARGS
    global commands_map
    global context_mode


#    rmain = False
    #Si es un bucle de argumentos
#    if len(args) < LIMIT_WHILE_ARGS + 1:
#        arg_n = 0
#        sem = args
#        for i in range(len(sem)):
#            if sem[i].startswith("--"):
#                arg_n = arg_n + 1
#                if arg_n == len(sem):
#                    rmain = True
#        if rmain == True :
#            while_args(sem)
#            return
            #FIN BLOKE "WHILE" # """"

# Si no se envían comandos, se asume que se envía una pregunta de texto.
    if not args[0].startswith("--"):
        user_input = " ".join(args)
        response_text = generate_response(user_input)
        if auto_cromode == False:
            print(" \n→", response_text)
        elif auto_cromode == True:
#            print("----------")
            CROreturn = croparser.main(response_text)
            print("CRO:auto")
            CRO = None
            if not CROreturn :
                print("NOT CRO RESULTS")
            else:
                CRO = True
                response = "True CRO"
                CROreturn_text = "Resultados parseado CRO"
                for key, value in CROreturn.items():
                    if key.startswith("output_"): # Si es una salida exitosa
                        print(f"\n--- Salida del Sistema ({key.split('_')[1]} {key.split('_')[2]}) ---")
                        print(value) # 'value' ya es la cadena limpia (si el subprocess.run la capturó como texto=True)
                        CROreturn_text += f"\n--- Salida del Sistema ({key.split('_')[1]} {key.split('_')[2]}) ---"
                        CROreturn_text += value # 'value' ya es la cadena limpia (si el subprocess.run la capturó como texto=True)
                    elif key.startswith("error_output_"): # Si es una salida de error
                        print(f"\n--- Error del Sistema ({key.split('_')[1]} {key.split('_')[2]}) ---")
                        print(f"Stdout: {value['stdout']}")
                        print(f"Stderr: {value['stderr']}")
                        print(f"Return Code: {value['returncode']}")
                        CROreturn_text += f"\n--- Error del Sistema ({key.split('_')[1]} {key.split('_')[2]}) ---"
                        CROreturn_text += f"Stdout: {value['stdout']}"
                        CROreturn_text += f"Stderr: {value['stderr']}"
                        CROreturn_text += f"Return Code: {value['returncode']}"
# Y luego, si necesitas loggear el diccionario completo:
# log_interaction(user_input, json.dumps(response_text, indent=2))
                conversation_context += str(CROreturn_text)
                response = generate_response("RETROALIMENTACION Resultados añadido al contexto. Analiza. Se Procesará CRO si está Activo")
                if CRO == True :
                    if response:
                        CROreturn2 = croparser.main(response)
                        if CROreturn2:
                            conversation_context += str(CROreturn2)
                            r_input = input("""
                                Menú de Retro Alimentación:
                                """)
                            if r_input:
                                ri2 = """
                                Usuario Retroalimenta Dice:
                                """+r_input+"""
                                """
                            else:
                                r_input=""
                            ra = "RETROALIMENTACION Resultados añadido al contexto. Analiza. ESTA RESPUESTAS NO PROCESARA CRO USA TEXTO PLANO AUNQE esté Activo"
                            response = generate_response(ra+r_input)
                            
                            print(":",CROreturn2)
                        else:
                            print("No-CROReturn2")
                        print(response)
                    else:
                        print("No+Response.")
        aap()
        arw()
        log_interaction(user_input, response_text)  # Nuevo: Registrar interacción
        return

    try:


        # Verificar el primer argumento
        command = args[0]
        

        if command == "--apr" or command == "--audio-parser-repeat":        
            apr() 
            return
        if command == "--ap" or command == "--audio-parser":
            xLR = last_response #  pt_audio(last_response) limpia texto desde cro parser
            print(xLR)
            audioparser.text_to_speech(xLR,"es",def_audio_lrequest)
            apf()
            print("End Audio Parser")
            return
        if command == "--resetkey":
            print("keycom")
            API_KEY = obtener_key_gemini('resetkey')
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(gemini_model) 
            return
        if command == "--ctm" or command == "--context-mode":
            #pone cro mode a ON o OFF sin recargar el archivo
            if context_mode == "fast":
                context_mode = False
            else:
                context_mode = "fast"
            print("CONTEXT_MODE: ",context_mode)
            return
        if command == "--cmc" or command == "--cromode-commute":
            #pone cro mode a ON o OFF sin recargar el archivo
            if auto_cromode == True:
                auto_cromode = False
            else:
                auto_cromode = True
            print("AUTO CRO MODE STATUS: ",auto_cromode)
            print("IS ACTIVE CRO: ",cro_loaded)
            conversation_context += "\n ~~~INTERNAL MSG: AUTOCROMODE FUE PUESTO A:"+str(auto_cromode)+"~~~ \n"
            return
        if command == "--cm" or  command == "--cromode":
            if auto_cromode == False:
                auto_cromode = True
                main(["--l","develop.info"])
                cro_loaded = True
                conversation_context += "\n ~~~INTERNAL MSG: AUTOCROMODE FUE ACTIVADO~~~ \n"
                main(["--al","""Se cargó y activó --cromode , directrices desde bin/develop.info de osiris release bio verified release /var/osiris2
                    (RECORDATORIO REFRESCO ACTUALIZACION DE) 
                    COMENZAMOS NUEVA CONVERSACIÓN DENTRO DEL CONTEXTO CRO;
                    CROMODE está activo a partir de tu próxima respuesta:
                    Avisa que activaste CRO y tu Resumen-Estado en unas pocas línea. Sin entrar en más detalles."""])
                return
            else:
                auto_cromode = False
                conversation_context += "\n ~~~INTERNAL MSG: AUTOCROMODE FUE PUESTO A OFF~~~ \n"
            print("AUTO_cromode:",auto_cromode)
            return
        if command == "--aap" or  command == "--auto-audio-parser":
            if auto_ap == False:
                auto_ap = True
                conversation_context += """
                AUTO_AUDIO_PARSER --aap FUE PUESTO A ON A partir de ahora SIEMPRE hasta que se desactive:
                A partir de ahora usa texto plano 100%. No uses asteriscos ni caracteres no alfabeticos o numericos si no son imprescindibles para mejor audición.
                Si CroMode está activado puedes crear estructuras CRO si se requiere.
                Puedes y debes usar tildes, diériris, eñes, etc.. del idioma usado usando ortografía correcta.
                """
            else:
                auto_ap = False
                conversation_context += """
                INTERNAL MSG: AUTO_AUDIO_PARSER --aap FUE PUESTO A OFF
                Usa salida standard
                """
            print("AUTO_AUDIO:",auto_ap)
            return
        if command == "--loc" or command == "--load-osiris-context":
            if args[1] == "help":
                LOC.load_osiris_context(["--help"])
            else:
                response_loc = LOC.load_osiris_context(["com/datas/prueba.dev.ai.json"])
                print("LOC RESPONSE")
                print(response_loc)
                option = 0 
                while True:
                    read_i = input("""
                    ¿Desea añadir la salida al contexto?
                    1)  Añadir al contexto actual
                    2)  Borrar Contexto actual y añadir
                    3) No añadir nada
                    Seleccione una opción (1, 2 o 3): """)
                    try:
                # Intentamos convertir la entrada a un entero
                        option = int(read_i)
                # Verificamos que la opción esté en el rango permitido
                        if 1 <= option <= 3:
                            break  # Salimos del ciclo si la opción es válida
                        else:
                            print("❌ Opción no válida. Por favor, ingrese 1, 2 o 3.")
                    except ValueError:
                # Capturamos el error si la entrada no es un número
                        print("⚠️ Entrada inválida. Por favor, ingrese un número.")
                print("--->", read_i) # read_i contendrá la última entrada válida
                if option == 1:
                    conversation_context += str(response_loc)
                    print("Conversación añadida al contexto actual")
                elif option == 2:
                    main(["--exp lastLOC"])
                    main(["--cc"])
                    conversation_context += str(response_loc)
                    print("Información LOC añadida a un contexto nuevo")
                    print("Para recuperar el último contexto use --imp lastLOC")
                elif option == 3:
                    print("No se añadió nada al contexto")
                else:
                    print("Error previo del while que no debería darse")
            return

        if command == "--sla" or command == "--showlastanswer":
            if conversation_context:
                show_text_window(last_response)
            else:
                print("Información", "No hay texto para mostrar.")
            return            
        if command == "--arw" or  command == "--auto_response_window":
            if auto_response_window == False:
                auto_response_window = True
                conversation_context += "[INTERNAL MSG: AUTO_RESPONSE_WINDOW --arw FUE PUESTO A ON]"
            else:
                auto_response_window = False
                conversation_context += "[INTERNAL MSG: AUTO_RESPONSE_WINDOW --arw FUE PUESTO A OFF]"
            print("AUTO_RESPONSE_WINDOW:",auto_response_window)
            return
        if command == "--sgm" or command == "select_genai_model":
            sm = "\nSelección de modelos de API\n"
            nmx = select_genai_model(sm)
            conversation_context += str(nmx)
            print("--------------:\n\n")
            return
        if command == "--asla" or command == "--audio-save-last-answer":
            if len(args) > 1:
                output = subprocess.run(["cp", def_audio_lrequest, def_audio_dir+args[1]])
                print("--asla",output)
                return
            else :
                print("--asla ERROR: ",args)
                return
        if command == "--nmodel":
            sm = "\nSelección de modelos de API\n"
            conversation_context += sm
            select_model()
            ns = "\n NEW MODEL WAS SELECTED \n "
            try:
                conversation_context += ns + "AT TIME: " + fecha_hora_g() + "\n"
            except Exception as e:
                conversation_context + f". !!! Se prujo un error: {e}"
            main(ns)
            print(ns)
            return
        # Usar el comando corto si está disponible
        if command in commands_map:
            command = commands_map[command]
        if command == "--lc" or command == "--loadconfig":
            if len(args) > 1 and is_file(args[1]):
                config = load_config(args[1])
                API_KEY = config.get("api_key", API_KEY)
                # Reconfigurar API si se carga una nueva clave
                genai.configure(api_key=API_KEY)
            else:
                messagebox.showerror("Error", "Archivo de configuración no encontrado o no especificado.")
            return
        elif command == "--log":
            if len(args) > 1:
                log_interaction(" ".join(args[1:]), last_response)
            else:
                messagebox.showerror("Error", "No se especificó la interacción a registrar.")
            return
        elif command == "--sp" or command == "--setparams":
            if len(args) > 1:
                set_model_params(args[1:])
            else:
                messagebox.showerror("Error", "No se especificaron parámetros.")
            return
        elif command == "--lm" or command == "--listmodels":
            print("\nModelos Genai disponibles:\n")
            dm = 0
            for m in genai.list_models():
                dm = dm + 1
                print(f"{dm} → {m.name}")
            return
        elif command == "--ta" or command == "--toggleautosave":
            enable = args[1].lower() == 'on' if len(args) > 1 else True
            toggle_autosave(enable)
            return
        elif command == "--l" or command == "--load":
            if len(args) > 1 and is_file(args[1]):
                load = read_file(args[1])
                print(f"Contenido cargado desde {args[1]}")
            else:
                messagebox.showerror("Error", "Archivo no encontrado o no especificado.")
            return
        elif command == "--al" or command == "--addload":
            args.pop(0)  # Remover '--addload' de los argumentos
            user_input = " ".join(args)
            if load:
                user_input = load + " " + user_input  # Añadir el contenido de 'load' al input del usuario
            response_text = generate_response(user_input)
            print(" \n→", response_text)
            arw()
            return
        elif command == "--sl" or command == "--showload":
            if load:
                print(f"Contenido de load:\n{load}")
            else:
                messagebox.showinfo("Información", "No hay contenido en 'load'.")
            return
        elif command == "--li" or command == "--loadimage":
            textWithImage = "Interpretar imagen"
            if len(args) > 2:
                textWithImage = " ".join(args[2:])
            if len(args) > 1 and args[1] == "--fd": # Si el segundo argumento es "fd" 
                # Abrir File Dialog para seleccionar la imagen
                image_path = filedialog.askopenfilename(
                    initialdir=".",
                    title="Seleccionar imagen",
                    filetypes=(("Imágenes", "*.jpg *.jpeg *.png *.gif"), ("Todos los archivos", "*.*"))
                )
                if image_path: # Si se seleccionó una imagen
                    generated_text = generate_with_image(image_path,textWithImage)
                    if generated_text:
                        conversation_context += f"{textWithImage} : {generated_text}\n"
                        print(" \n→", generated_text)
                else:
                    messagebox.showinfo("Información", "No se seleccionó ninguna imagen.")
            elif len(args) > 1:
                textWithImage += ""
                image_path = args[1]
                if is_file(image_path):
                    generated_text = generate_with_image(image_path,textWithImage)
                    if generated_text:
                        conversation_context += f"{textWithImage} : {generated_text}\n"
                        print(" \n→", generated_text)
                elif image_path.startswith(('http://', 'https://')):
                    generated_text = generate_with_image(image_path,textWithImage)
                    if generated_text:
                        conversation_context += f"{textWithImage} : {generated_text}\n"
                        print(" \n→", generated_text)
                else:
                    messagebox.showerror("Error", "Imagen no encontrada o no especificada.")
            else:
                messagebox.showerror("Error", "No se especificó una ruta de imagen.")
        elif command == "--sw" or command == "--showwin":
            if conversation_context:
                show_text_window(conversation_context)
            else:
                messagebox.showinfo("Información", "No hay texto para mostrar.")
            return
        elif command == "--ss" or command == "--screenshot":
            screen_shot()
            return            
        elif command == "--la" or command == "--loadanswer":
            if conversation_context:
                load = last_response
                print("Cargada última respuesta")
            else:
                messagebox.showinfo("Información", "No hay información (L 486) para mostrar.")
            return            
        elif command == "--sav" or command == "--saveload":
            filename = "com/datas/saveload.gemini"  # Nombre por defecto
            if len(args) > 1:
                filename = f"com/datas/{args[1]}.gemini"  # Nombre personalizado
            save_file(filename, conversation_context)
            return
        elif command == "--sr" or command == "--saverequest":
            if len(args) > 1:
                user_input = " ".join(args[1:])
                save_request(user_input)
            else:
                messagebox.showerror("Error", "No se especificó solicitud a guardar.")
            return
        elif command == "--sa" or command == "--saveanswer":
            if len(args) > 1:
                filename = f"{args[1]}"  # Nombre personalizado
            else:
                filename=""
            save_answer(filename)
            return
        elif command == "--sc" or command == "--savecontext":
            save_context()
            return
        elif command == "--as" or command == "--autosave":
            autosave()
            return
        elif command == "--nq" or command == "--newquestions":
            if len(args) > 1:
                questions = generate_new_questions(" ".join(args[1:]))
                print("Preguntas generadas:")
                for q in questions:
                    print(" -", q)
            else:
                messagebox.showerror("Error", "No se especificó una pregunta base.")
            return
        elif command == "--sd" or command == "--send":
            if len(args) > 1:
                user_input = " ".join(args[1:])
                response_text = generate_response(user_input)
                print(" \n→", response_text)
            else:
                messagebox.showerror("Error", "No se especificó pregunta a enviar.")
            return
        elif command == "--ls" or command == "--listfiles":
            if len(args) < 2:
                args.append(".")
            print("Listando archivos en com/datas/"+str(args[1]))
            for filename in os.listdir("com/datas/"+str(args[1])):
                print(" -", filename)
            return
        elif command == "--cc" or command == "--clearcontext":
            conversation_context = ""
            print("Contexto de conversación limpiado.")
            return
        elif command == "--lsel" or command == "--loadselect":
            if len(args) > 1 and is_file(args[1]):
                selected_context = read_file(args[1])
                conversation_context += selected_context + "\n"
                print("Contexto seleccionado cargado.")
            else:
                messagebox.showerror("Error", "Archivo no encontrado o no especificado.")
            return
        elif command == "--lm" or command == "--loadmultiple":
            for filename in args[1:]:
                if is_file(filename):
                    selected_context = read_file(filename)
                    conversation_context += selected_context + "\n"
                    print(f"Contexto de {filename} cargado.")
                else:
                    messagebox.showerror("Error", f"Archivo {filename} no encontrado.")
            return
        elif command == "--i" or command == "--info":
            print("Información del modelo:")
            print(" - Modelo:", model)
            print(" - Contexto actual:", conversation_context)
            return
        elif command == "--exp" or command == "--export":
            if len(args) > 1:
                win.export_context(args[1],conversation_context)
            else:
                messagebox.showerror("Error", "No se especificó nombre para exportar.")
            return
        elif command == "--imp" or command == "--import":
            if len(args) > 1:
               conversation_context = win.import_context(args[1])
            else:
                messagebox.showerror("Error", "No se especificó nombre para importar.")
            return
        elif command == "--s" or command == "--search":
            load_context = False
            term = ""
            # Eliminamos el --search de los argumentos
            args.pop(0) 
            for arg in args:
                if arg == "--load":
                    load_context = True
                else:
                    term += arg + " "
            term = term.strip()
            if term:
                results = search_context(term, load_context)
            else:
                messagebox.showerror("Error", "No se especificó término de búsqueda.")
            return
        elif command == "--st" or command == "--settopic":
            if len(args) > 1:
                topic = " ".join(args[1:])
                print(f"Tema establecido: {topic}")
            else:
                messagebox.showerror("Error", "No se especificó tema a establecer.")
            return
        elif command == "--dialog" or command == "--ask"  :
            #Abre una ventana de dialogo para enviar una pregunta al modelo de IA seleccionado
            dtext = win.dialog_window()
            if dtext != "":
                dtext = str(dtext)
                print(" → ",dtext)
                response_text = generate_response(dtext)
                print(" → ",response_text)
            else:
                print("No se recibió respuesta. Acción inesperada.")
            arw()
            return
        elif command == "--di" or command == "--decodeimage":
            if len(args) > 0:
                dim = args[1]
                decode_img(b"{dim}")
                print("DECODE")
            return
        elif command == "--tvl" or command == "--tvideol":
#                return
            if len(args) == 2:
                Context = []
                if args[1] == "--dialog":
                    print("DIALOG")
                    dialog_h = win.dialog_window()
                    Context = dialog_h.split()
                    args = Context
                    argsx = []
                    if len(args) > 1:
                        print("Procesando....")
                        for  zx in  args: 
                            if zx.startswith("@") : 
                                argsx.append(zx)
                    video_translate(Context[0]," Automatic @def  ",argsx)
#                    main(["--tvl",Context[0],argsx])
                    return
            if len(args) > 2:
                Context = []
                if args[2] == "--dialog":
                    del args[2]
                    print("DIALOG")
                    dialog_h = win.dialog_window()
                    Context = [dialog_h]
                prompt = " ".join(args[2:]) 
            argsx = []
            if len(args) > 1:
                print("Procesando....")
                for  zx in  args: 
                    if zx.startswith("@") : 
                        argsx.append(zx)
                video_translate(args[1],prompt,argsx)
            else:
                print("Es necesario parametro de video")
#            send_video()
            print("---FIN VIDEO ----")
            return  
        elif command == "--r" or command == "--reset":
            conversation_context = ""
            load = ""
            last_response = ""
            topic = ""
            print("Todos los valores han sido reseteados.")
            return  
        elif command == "--diagnostic" or command == "--d":
            if len(args) > 1 :
                if args[1] == "server":
                    com_d = ["sudo","tool/mrls"]
                    fileload = "com/datas/rls.gemini.ctrl"
                    text = "Realiza un diagnóstico del sistema"
                elif args[1] == "system":
                    com_d = ["sudo","tool/diagnosis1"]
                    fileload = "com/datas/system_info.gemini.ctrl"
                    text = "Realiza un diagnóstico del sistema"
                elif args[1] == "memory":
                    com_d = ["sudo","tool/memory"]
                    fileload = "com/datas/memory.gemini.ctrl"
                    text = "Realiza un diagnóstico del sistema"
                else:
                    print("Parámetro incorrecto")
                    return
            else:
                print("necesita parametro 2 (system, etc...)")
                return
            obj = {
             "mode":"fixed",
             "name":None,
             "com":com_d,
             "metadata":{"from":"gemini3.py"}
            }
            core.ps.ps(com_d)
            print("\n Intentando Reporte... cargando... \n ")
            main(["--l",fileload,text])
            print("\n Enviando reporte .....\n ")
            main(["--al","Realiza reporte"])
            print("\n Fin del reporte \n ")
            return

    except Exception as e:
        if not API_KEY:
            try:
                API_KEY = obtener_key_gemini()  # Obtiene una nueva clave
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel(gemini_model)  # Reinicializa el modelo
            except Exception as f:
                print("Error API_KEY:",f)
                return
        print("Error:",e)



# Mapeo de comandos cortos
        commands_map = {
            "--auto_response_window":"--arw", #abre respuestas en ventana (on/off)
            "--cromode":"--cm",  # Activa modo CRO (on/off)
            "--load": "--l",   # lee y carga el texto de un archivo en memoria
            "--addload": "--al", #add load  añade el texto último cargado en memoria
            "--showload": "--sl", #show load  muestra contenido cargado en memoria
            "--loadimage": "--li", #carga una imagen para enviar a la ia desde una url + texto propmt.
            "--showwin": "--sw",  #Muestra todo el contexto en una ventana
            "--saveload": "--sav",
            "--saverequest": "--sr",
            "--saveanswer": "--sa",
            "--savecontext": "--sc",
            "--autosave": "--as",
            "--newquestions": "--nq",
            "--send": "--s",
            "--listfiles": "--ls",
            "--clearcontext": "--cc",
            "--loadselect": "--lsel",
            "--loadmultiple": "--lm",
            "--info": "--i",
            "--export": "--exp",
            "--import": "--imp",
            "--search": "--s",
            "--settopic": "--st",
            "--reset": "--r",
            "--loadconfig": "--lc",  # Nuevo: Cargar configuración
            "--log": "--log",        # Nuevo: Registrar interacciones en el log
            "--setparams": "--sp",   # Nuevo: Configurar parámetros del modelo
            "--toggleautosave": "--ta",  # Nuevo: Activar/desactivar autosave
            "--listmodels":"--lms", #Lista los modelos genai
            "--selectgenailmodel":"--sgm",
            "--aap":"--audio-auto-parse", # Seleccionar un Modelo Genai
            "--ap":"--audio-parse",
            "--apr":"--audio-parse-repeat",
            "--sla":"--show-last-answer",
            "--tvl":"--translate-video-link", #subtitula video usar metadiálogos @ (@subtitulos @fbold @color @creative etc... consultar documentación.)
            "--li":"--load-image",
            "--asla":"--audio-save-last-answer", #Copia la última respuesta procesada por audio a un nombre pasado como parámetro guardándolo en com/datas.
            "--cmc":"--cromode-commute", #cambia el estado de auto cromode a true / false
            "--ctm":"--context-mode", #Modos de Contexto
            "--loc":"--load-osiris-context" #cargas multiples e instrucciones desde json
        }


# Ejecutar el programa

fecha_hora = ""


def fecha_hora_g():
    global fecha_hora
    timestamp_unix = int(time.time()) 
    fecha_hora  = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_unix))
    return fecha_hora

#fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

fecha_hora = fecha_hora_g()

init = 0
HELO = "\nHELO START - Se Ha inciado el SISTEMA OSIRIS a las: " + fecha_hora

use_def = False

if sys.argv[2] == "--preload":
    print("Iniciando precargas")
    while_args(["--arw","--cm","--aap","--apr","--sgm","--apr"])
    main(HELO)
    main(["--l","/var/osiris2/bin/tool/loadCore.human.ai"])
    ####main(["--al","--l tool/loadCore.human.ai dijo."])
    print(["Escriba --al más texto (ej: info.human.ai Conversación Anadido para Carga de Inicio )"])
    while_args(["--apr"])
    print("Precargas finalizadas")
else:
    print("No se definió precarga. Se continúa con carga por defecto")
    while_args(["--aap"])
    use_def=True

#print(sys.argv)


conversation_context += HELO+"\n  Usa El Comando --arw para activar respuesta GUI           "

#main(sys.argv[1:] + HELO )
if use_def == True:
    while_args(["--ap","--apr"])
    print("------------useDEF------------")
#    main(HELO)
print("EOF:gemini.py:2114")