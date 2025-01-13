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
import lib.multiprocess as osiris2
import lib.gemini.utils as win
import time
import hashlib

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
conversation_context = f"""
#Interfaz de comunicación con Gemini AI de Google
#Interfaz Name: Osiris
#Version: {version_file}
#Idioma: Español
Intrucciones:
Gracias BRO.
COMIENZA LA CONVERSACIÓN.
"""


gemini_models = ["gemini-1.5-flash",
		         "gemini-1.5-flash-8b",
		         "gemini-1.5-pro",
                 "gemini-1.0-pro",
                 "text-embedding-004",
                 "aqa"]


# Define la clave API (si ya existe)
API_KEY = os.getenv("GOOGLE_API_KEY")

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




def select_model():
    global gemini_models,conversation_context
    seleccione_modelo = f" Selecciones un modelo a usar:\n"
    for index, x in enumerate(gemini_models):
        seleccione_modelo += f"\n ({index}) {x}  "
    print("\n")
    sel = f"\n{seleccione_modelo} \n Seleccione Uno: >>> "
    conversation_context += sel
    inp = input(sel)
    conversation_context += inp + "\n"


select_model()



"""
Contesta siempre en ESPAÑOL aunque se te pregunte en otro idioma y no se te explicite otro a usar.
Usa emojis para dinamizar las conversaciones.

"""



load = ""
last_response = ""
topic = ""  # Tema de conversación
autosave_enabled = True  # Estado del autosave

def_image_editor = "lazpaint"


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
    win.show_text_window(text)



personajes = {}
modos = {}


modos["critica"] = """
Modo de expresión: Crítica ácida.
Por lo tanto tienes que criticar al personaje señalado.
"""

personajes["sanchez"] = """
Personaje a usar: Pedro Sánchez.
Características del personaje:
Presidente del gobierno de España.
Motes: Sanchinflas, Su Sanchidad, Pinocho.
"""


srt_c = {}


srt_c["fuente_weight"] = """

Usa para esta segmentacion:
Usa fuente tipo:
Tamaño rango 36 - 90
Colores: Claros Brillantes 
Emojis:
Tamaño rango 90 - 165
Colores: Brillantes medios

"""

def video_translate(video_file_name="",prompt=""):
    global personajes,last_response,conversation_context,srt_c,modos
    if video_file_name.startswith('http://') or video_file_name.startswith('https://'):
        print("Descargando video temporal")
        code_video_file = "/tmp/"+hashlib.md5(video_file_name.encode()).hexdigest()+".mp4"
        process = subprocess.run(["yt-dlp","--cookies-from-browser","chrome","-o",code_video_file,video_file_name], capture_output=True, text=True)
        video_download_url = video_file_name
        video_file_name = code_video_file
        print("Video File:",video_file_name)
        input_video_info = f"Se ha descargado un vídeo desde: {video_download_url} \n"
        input_video_info += f"Se ha guardado el vídeo en disco con path: {video_file_name} \n"
    else:
#        video_file_name="com/datas/ffmpeg/anon.mp4"
        print("video_file")
        code_video_file = "/tmp/"+hashlib.md5(video_file_name.encode()).hexdigest()+".mp4"
        input_video_info = "VIDEO PATH"
        return
        #vídeo file
#        return
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
        conversation_context += str(vfm)
        raise ValueError("ERR IN VIDEO SEND FAILED:\n"+str(vfm)+"\n")
    else:
        input_video_info += f"Se ha subido el vídeo a Gemini-video a la url: {video_file.uri} \n"


    # Create the prompt.
    prompti = "Tu eres gemini-video Tu tarea es Subtitular vídeos, hazlo en formato .srt con este formato ```srt  (traducion en formato srt) ``` "
    prompti += "\n Usa Arial como fuente predeterminada pero puedes usar otras si lo requiere el contexto del video."
 #   prompti +="\ncolorea los emojis y hazlos en tamaños variables dentro del rango." 
    prompti +="\nEtiquetas permitidas en el srt <font size=value color=value face=value></font><b></b> usa colores brillantes claros para el texto ajustandolos en formato hexadecimal."
    prompti += "Transcribe y traduce el audio del video en español si no se especifica otro idioma.  Para cada frase o sección significativa del diálogo, proporciona un subtítulo con una duración máxima de 5 segundos. Si la frase es más larga, divídala en múltiples subtítulos. Asegúrate de que la traducción sea precisa y neutral. Usa emojis que reflejen el tono y el contenido emocional de cada parte del discurso (por ejemplo, 😡 para la ira, 💣 para una explosión, etc.). Evita emojis que puedan resultar inapropiados o que puedan cambiar el significado de la traducción."
    prompti +="\nUsa el formato que permita .srt usando html y styles permitidos con fuentes con rango entre 17 y 21 si no se especifica otro, que el vídeo va a ser procesado por ffmpeg entonces son válidas."




    prompt_creative = """


Tu eres gemini-video. Tu tarea es generar un archivo .srt con subtítulos para el vídeo que te estoy proporcionando. Debes traducir todo al español si no se te indica otro idioma más adelante.  

Tu objetivo es crear subtítulos precisos y contextualmente relevantes,  que reflejen con exactitud el contenido del vídeo sin añadir interpretaciones subjetivas o sensacionalistas. Prioriza la objetividad y la neutralidad.

1. **Transcripción y Traducción:** Transcribe el audio del vídeo con la mayor precisión posible y traduce todo al español excepto que se te explicite otro distinto. Si hay secciones sin audio o con audio irrelevante para la traducción (ej: música de fondo, sonidos ambientales), describe brevemente el contenido visual en español.

2. **Generación del archivo .srt:** Genera un archivo .srt que incluya:

    * **Formato SRT:** El archivo debe cumplir estrictamente el formato .srt.

    * **Etiquetas HTML:** Utiliza las siguientes etiquetas HTML dentro de cada línea de texto del subtítulo para controlar el estilo: `<font size="value" color="value" face="value"></font>` y `<b></b>`.

        * **`size`:** El tamaño de la fuente (entre 16 y 22) de forma que si el formato del vídeo es predominante vertical use fuentes más pequeñas y horizontal más grandes.  Utiliza diferentes tamaños para enfatizar ciertas palabras o frases,  manteniendo un equilibrio visual.
        * **`color`:** El color de la fuente en formato hexadecimal (ej: `#FF0000` para rojo).  Emplea una paleta de colores que sea consistente y que refleje la atmósfera del vídeo, pero evita colores demasiado saturados y oscuros o que distraigan la atención, usa colores claros porque el video se va a montar sobre un faldón oscuro.  Prioriza la legibilidad.
        * **`face`:** Utiliza fuentes como "Noto Sans", "Dejavu Sans" o Tahoma, manteniendo la coherencia en toda la secuencia.
        * **`b`:** Utiliza `<b></b>` para texto en negrita de forma estratégica, solo para enfatizar palabras clave o frases importantes.
        * **Los valores de los atributos en las etiquetas font del subtitulado deben ir entrecomillados.

    * **Estructura:** Cada línea del .srt contendrá la traducción al español. Si hay una sección sin audio o con audio ininteligible, escribe una descripción breve y objetiva en español dentro de las etiquetas HTML. Ejemplo: `<font size=18 color=#808080 face=Arial>Música de fondo</font>` o `<font size=18 color=#808080 face=Arial>Imágenes de destrucción</font>`.

    * **Emojis:** Incluye emojis descriptivos (evitando los ambiguos o inapropiados) en cada línea para reflejar el tono y el contenido emocional. Envuelve los emojis en etiquetas HTML para controlar su estilo y un espacio en blanco entre ellos.

    * **Duración y Espaciado:** La duración máxima de cada subtítulo debe ser de 5 segundos como máximo priorizando entre 2 y 2.5 segundos de intervalo de tiempo de transcripción cuando sea posible para una lectura fluida (importante). El intervalo mínimo entre subtítulos debe ser de 2 segundos y el máximo de 5 segundos.  Si un tramo de vídeo requiere un intervalo mayor a 5 segundos sin traducción, crea una nueva entrada en el archivo .srt con una descripción contextual concisa y objetiva (ej:  "Escena mostrando un convoy militar", "Plano secuencia de una calle desierta") y ajusta la temporización correctamente.

3. **Precisión, Objetividad y Contexto:** Prioriza la precisión en la traducción y la descripción objetiva de las partes sin diálogo.  El objetivo es ofrecer al espectador la información visual y auditiva más precisa posible, evitando interpretaciones o juicios de valor.  Manten la creatividad en el diseño visual, pero siempre subordinada a la objetividad y la veracidad del contenido.


**Ejemplo para un vídeo que durase 10 segundos:**

```srt
1
00:00:0,500 --> 00:00:3,000
<font size="19" color="#D2691E" face="Verdana">El portavoz afirma: "Nuestra operación comienza ahora."</font>  <font size=21 color=#F11C00 face=impact>⚔️</font> <font size=20 color=#FF8C00 face=impact>💥</font>

2
00:00:4,000 --> 00:00:7,000
<font size="18" color="#808080" face="Dejavu Sans">Imágenes de una explosión. Se observa humo negro.</font>

3
00:00:7,000 --> 00:00:9,500
<font size="20" color="#B22222" face="Noto Sans">“El objetivo ha sido alcanzado.”</font> <font size="21" color="#0000FF" face="impact">🎯</font>

```

Instrucciones complementarias:

Usa emojis pero para los emojis si puedes usar distintos colores que expresen su naturaleza, por ejemplo para el emoji de una explosion una fuente roja variable y un tamaño un punto mayor que el texto, y así con todos, juega con eso.

Asegúrate de que la duración de cada subtítulo coincida exactamente con la duración de la frase hablada en el vídeo.  Prioriza la precisión temporal sobre la duración máxima de 5 segundos por subtítulo; si una frase es más larga de 5 segundos, divídela en varios subtítulos que mantengan la sincronización precisa con la voz.

Debes generar un solo archivo srt





""" + srt_c["fuente_weight"] + "\n"




    prompti = """


Eres Gemini-video. Genera un archivo SRT con subtítulos en el idioma especificado (por defecto, español si no se te indica otro distinto más adelante).

Prioridades:

1. Precisión en la transcripción y traducción.
2. Sincronización temporal exacta.  **Los subtítulos deben tener una duración de entre 1 y 2 segundos.  En casos excepcionales un subtítulo puede durar hasta 5 segundos máximo. Por lo tanto predomina una longitud de textos medios-cortos.


Formato:

* Cumple estrictamente el formato SRT.
* Usa etiquetas HTML: `<font size="18-22" color="#hexadecimal" face="Noto Sans/DejaVu Sans/">texto</font>` y `<b>texto importante</b>`.  Prioriza colores claros y legibles.  **Utiliza una variedad de colores para hacer los subtítulos más atractivos.**
* Incluye emojis relevantes con **tamaño y color variable para mayor impacto visual.**  **Proporciona emojis con tamaños entre 1 y 3 unidades mayores al tamaño de fuentes utilizados y utiliza colores que reflejen la emoción o el significado del emoji.  Por ejemplo, un emoji de fuego (🔥) podría ser rojo o naranja, mientras que un emoji de hielo (🧊) podría ser azul claro.
* Usa Fuentes de tamaño 18-22 si no se te indican otras más adelante.
Ejemplo:

```srt
1
00:00:00,500 --> 00:00:02,000
<font size="19" color="#D2691E" face="Noto Sans">El portavoz afirma:</font>
2
00:00:02,000 --> 00:00:03,500
<font size="21" color="#FFA500" face="Noto Sans">"Nuestra operación comienza ahora."</font>  <font size=24 color=#F11C00 face=impact>⚔️</font> <font size=28 color=#FF8C00 face=impact>💥</font>
```

Debes generar solamente 1 archivo SRT. SÓLO UNO.


"""



    prompti = prompt_creative


    if prompt == "":
        prompt = prompti 
    else:
        prompt = prompti + prompt 
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
        with open(vtranslate,"w",encoding='utf-8') as f:
            f.write(matches[0])

        force_style_sub = "Fontsize=20,Fontcolor=blue@0.2,BackColour=black@0.5,BorderStyle=5"
        force_style_sub = "Alignament=6,BackColour=&H30000000,BorderStyle=4,Fontsize=18,FontName=Arial,PrimaryColour=&H00FFFFFF"
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
        "com":["/usr/bin/ffmpeg","-y","-loglevel","error","-i",video_file_name,
        "-af","aresample=async=1,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-vf","subtitles="+vtranslate+":force_style='"+force_style_sub+"'",
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
                print("Error al ejecutar el comando ffmpeg:")
                print(f"Código de retorno: {resultado.returncode}")
                print(f"Salida de error: {stderr}")
                return False  # Indica fallo
            else:
                print("Comando ffmpeg ejecutado correctamente.")
                print(f"Código de retorno: {resultado.returncode}")
                task_done = f""" 
                Se ha descargado un vídeo desde

                """
                # El comando se ejecutó correctamente
        except FileNotFoundError:
            print("Error: El comando ffmpeg no se encontró. Asegúrate de que esté instalado y en tu PATH.")
            return False
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            return False


        obj = {
        "mode":"bg",
        "name":None,
        "com":["dsk/dskv","--video",subtitulado_out]
        }
        o2mp = osiris2.multiprocess(obj)

        print("\nRealizando Inferencia 2 ....")
        send_text = f"\nTu eres genini-text. Acabo de enviar un video a gemini-video con este promt: {prompt} \nY esta fue la respuesta completa en bruto de Gemini-video antes de procesarla:\n{response.text}\nSe realizaron correctamente las siguientes tareas de procesamiento: {input_video_info}\nSe finalizó el procesamiento ejecutando correctamente el siguiente conmando: {str(comando_ffmpeg)}\nRealiza instrucciones solicitadas anteriormente a gemini-text por gemini-video en caso de existir, si no existen, sólamente realiza una revisión informativa.\n"
        print(f"\n{send_text}\n")
        response_return = generate_response(send_text)
        print("\n\n",response_return)
#        last_response = " ".join(comando_ffmpeg)


    else:
        print("No se generó el archivo de subtitulos correctamente")
        return



    # Print the response, r







def screen_shot():
    process = subprocess.run(["python3", "com/screenshot.py"], capture_output=True, text=True)
    output = process.stdout.strip().splitlines()  # Limpiar y dividir en líneas

    # Comprobación del formato de salida
    if len(output) < 3:
        print("Fallo: la salida no tiene suficientes líneas.")
        return
    
    # Filtrar la salida
    coordinates_line = output[0]  # Primera línea
    image_path_line = output[1]  # Segunda línea
    text_lines = output[2:]  # Resto de líneas

    # Verificar que las líneas cumplen con el formato esperado
    if not coordinates_line.startswith("Coordinates:") or not image_path_line.startswith("ImagePath:"):
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


def generate_response(user_input):
    """Genera una respuesta del modelo basada en la entrada del usuario."""
    global conversation_context, last_response
    conversation_context += "User: "+user_input+"\n"
    try:
        response = model.generate_content(conversation_context)
        response_text = response.text
        conversation_context += "AI: "+ response_text+"\n"
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
    log_file = "com/datas/conversation_log.txt"
    try:
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"{datetime.now()} - User: {user_input}\nAI: {response_text}\n\n")
        print("Interacción registrada en el log.")
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

# Función para manejar los argumentos
def main(args):
    """Función principal que maneja los argumentos de entrada para generar respuestas del modelo."""
    global gemini_model, model, conversation_context, load, last_response, topic, API_KEY


    # Si no se envían comandos, se asume que se envía una pregunta de texto.
    if not args[0].startswith("--"):
        user_input = " ".join(args)
        response_text = generate_response(user_input)
        log_interaction(user_input, response_text)  # Nuevo: Registrar interacción
        print(" \n→", response_text)
        return

    try:
        # Mapeo de comandos cortos
        commands_map = {
            "--load": "--l",
            "--addload": "--al",
            "--showload": "--sl",
            "--loadimage": "--li",
            "--showwin": "--sw",
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
            "--toggleautosave": "--ta"  # Nuevo: Activar/desactivar autosave
        }

        # Verificar el primer argumento
        command = args[0]
        if command == "--nmodel":
            sm = "\nseleccione modelo nuevo\n"
            conversation_context += sm
            select_model()
            ns = "\n NEW MODEL WAS SELECTED \n "
            main(ns)
            print(sm + ns)
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
            
            
        elif command == "--sla" or command == "--showlastanswer":
            if conversation_context:
                show_text_window(last_response)
            else:
                messagebox.showinfo("Información", "No hay texto para mostrar.")
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
            print("Listando archivos en com/datas:")
            for filename in os.listdir("com/datas"):
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

        elif command == "--dialog":
            dtext = win.dialog_window()
            if dtext != "":
                print(" → ",dtext)
                response_text = generate_response(dtext)
                print(" → ",response_text)
            else:
                print("VOID D")
            return

        elif command == "--di" or command == "--decodeimage":
            if len(args) > 0:
                dim = args[1]
                decode_img(b"{dim}")
                print("DECODE")
            return


        elif command == "--tvl" or command == "--tvideol":
            if len(args) > 2:
                prompt = " ".join(args[2:])
            else:
                prompt = ""
            if len(args) > 1:
                print("Procesando....")
#                return

                video_translate(args[1],prompt)

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
        elif command == "--resetkey":
            print("keycom")
            API_KEY = obtener_key_gemini('resetkey')
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(gemini_model) 
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
            osiris2.multiprocess(obj)
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
# Ejecutar el programa
init = 0
HELO = "HELO START"
main(HELO)
if __name__ == "__main__":
    init = init + 1
    if init > 1:
        HELO = ""

    main(sys.argv[1:] + HELO )

