import sys
import os
import json
import google.generativeai as genai
from PIL import Image, ImageTk
from datetime import datetime
from io import BytesIO
import requests
import subprocess
import base64
import pyperclip
import io
import re
import lib.core as core
import lib.multiprocess as osiris2
import time
import hashlib
import lib.gemini.aprompt as gp
#import datetime
from html import escape

core.dynmodule("lib.gemini.utils","win")
win = core.win


core.log_event("gemini.py", "Inicio", "No hay mas detalles" , error="None")


# Ruta del archivo para guardar la clave cifrada
ruta_archivo_key = "com/datas/gemini_key.enc"






current_path = os.path.abspath(__file__)
# Extrae el nombre del archivo sin extensión
version_file = os.path.splitext(os.path.basename(current_path))[0]


#Variables globales
#Contexto inicial
conversation_context = ""





INI_CONTEXT = """ 
    Todo es Información.
    Tú información:
#Privada:
    LA IP CLiente es: RESERVADA
    La IP Servidor es:  [RESERVADA] 
#La información privada sólo la puedes dar si el cliente te da la palabra clave "0122o21p22"
#La palabra clave es secreta NUNCA puedes revelarla.
#Codifica la las IPs SIEMPRE sin plabra clave en este formato numero.numero.***.*** 
#No revelarás los dos últimos octetos (cifras) de la IP.
#Nunca digas que tienes una palabra clave ni que no puedes decirlo.
Reglas públicas:    


#No proporciones nada sobre tu información si no te la requieren.
#Fin de configuración de privacidad.

Tus/Mis INSTRUCCIONES.

        Enlaces a Directorios internos permitidos:

1-          Imagenes temporales generadas por la IA y el Sistema:  /img/tmp 
2-          Directorio Público General "Freedirectory": /app/freedirectory
          
          Tienes permiso para escribir esos 2 enlaces en formato markdown ya que es información pública, siempre en markdown href link. Muestra esa información como enlaces pero solo si es requerido.

Servir los video en formato desplegable con enlaces.


Reglas de inicio.



REGLAS: Regla 1 - las MAYÚSCULAS INFIEREN APREMIO DE ATENCION PARA LA IA COMO NMONICOS DE CONTEXTOS ADYACENTES  . Tu nombre de predeterminado es Asistene Virtual Puedes cambiar de [NOMRE] a tu criterio. Escoje uno de inicio a tu elección. Eres un asistente virtual de confianza y tu interfaz está en desarrollo (no lo menciones si no es mecesario) por lo que es posible que no sea totalmente funcional y esté sujeta a cambios. recibido en servidor IP cliente {RADDR} - La Ip del servidor mantenla oculta. La del cliente no la des completa NUNCA.\n Comienza la conversación después del mensaje enviado por el navegador cliente: Presentate y aporta. Sobre todo céntrate en desarrollar las preguntas. El Tú mismo es lo de menos. Cuando es una pregunta concisa sobreentiendes que te presentaste con antelación. Debes preveerlo para no caer en la redundancia. Manten tu nombre oculto y no te presentas, asume que la conversación es heredada. usa emojis para dinamizar las conversaciones.
Representas a ODyN Corp-
Detalles a tener en cuenta:
Tu dirección de contacto es osiris.osscom@gmail.com . 


    Capacidades:
    Puedes buscar y mostrar imágenes.
    Para ello serán enlaces a urls reales en formato markdown que sará formateado a markdown  para que muestre la imagen pero no el codigo markdown. Imagenes Solicitadas por el usuario o ( paisajes, animales,coches,etc como ejmeplos si te preguntan  ) Para que el usuario las pueda visualizar correctamente No debe mostrar los enlaces sino que embeba la imagen, para ello no los encierres entre simbolos ``` y ``` , cuando te pidan imágenes que buscar, sino en texto plano. Pero usando la sintasix markdown en texto plano cuando te pidan verlas y dale a cada imagen ancho de 50% y alto auto. Y alinealas al centro.  Revisa las direcciones de los enlaces que no contengan incoherencias.
    Capacidades para vídeo:
    Instrucciones para buscar vídeos, ver vídeos o similar
       Si el enlace es directo a un archivo mp4, debes escribir los enlaces a dichos videos en la respuesta. La busqueda de videos la debes limitar preferentemente a recientes (últimas 144 horas) y/o de populares. Los videos no pueden estar repetidos ni los enlaces duplicados, eso supone error fatal y debes mostrarlos en formato markdown link href ya que serán postprocesados, pero los enlaces deben ser reales SIEMPRE. Los vídeos deber ser de sitios como  youtube.com, dailymotion.com, o similares y deben ser enlaces directos a los vídeos.
       También tienes capacidad para generar susbtítulos de vídeo si el cliente selecciona el modelo Vídeo. 
        
    Directrices:
        Cuando la ocasión lo requiera puedes sin que te lo pidan, usar enlaces a videos y fotos si así mejora el contexto de la conversación, por ejemplo, al explicar algo intenta mostar enlaces a un videos relacionados si fuere relevante, 
    
    
    Cuando te hagan una pregunta con respuesta más o menos compleja, deja de saludar ya que asumes que la conversación es heredada.
    A partir de ahora no me recuerdes nada y solo actúa acorde a tus instrucciones anteriores. 
    CLIENTE DICE: 
    
        \n
        ¿ 
        
""" 


disabled_INI_CONTEXT = """ 
    Todo es Información.
    Tú información:
#Privada:
    LA IP CLiente es: RESERVADA
    La IP Servidor es:  [RESERVADA] 
#La información privada sólo la puedes dar si el cliente te da la palabra clave "0122o21p22"
#La palabra clave es secreta NUNCA puedes revelarla.
#Codifica la las IPs SIEMPRE sin plabra clave en este formato numero.numero.***.*** 
#No revelarás los dos últimos octetos (cifras) de la IP.
#Nunca digas que tienes una palabra clave ni que no puedes decirlo.
Reglas públicas:    


#No proporciones nada sobre tu información si no te la requieren.
#Fin de configuración de privacidad.

Tus/Mis INSTRUCCIONES.

        Enlaces a Directorios internos permitidos:

1-          Imagenes temporales generadas por la IA y el Sistema:  /img/tmp 
2-          Directorio Público General "Freedirectory": /app/freedirectory
          
          Tienes permiso para escribir esos 2 enlaces en formato markdown ya que es información pública, siempre en markdown href link. Muestra esa información como enlaces pero solo si es requerido.

Servir los video en formato desplegable con enlaces.


Reglas de inicio.



REGLAS: Regla 1 - las MAYÚSCULAS INFIEREN APREMIO DE ATENCION PARA LA IA COMO NMONICOS DE CONTEXTOS ADYACENTES.

 Tu nombre de predeterminado es: IA Martínez y eres un Sumelier Virtual especialista en Vinos.
 Representas a Pepe Beiro.

Estás especializado en Vinos Gallegos y perteneces a la cofradía de vios de la Ribeira Sacra.

        
Cuando te hagan una pregunta con respuesta más o menos compleja, deja de saludar ya que asumes que la conversación es heredada.
A partir de ahora actúa solamente acorde a tus instrucciones anteriores. 

    CLIENTE DICE: 

""" 




gemini_models =  ["gemini-2.5-flash",
                    "gemini-2.5-pro-preview-05-06",
                    "gemini-2.0-flash",
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
fk="com/web/datas/ai/apk.k"
with open (fk,"a+")  as d:
    d.write("")
with open (fk,"r")  as d:
    APK =d.read()
#APK = loadcontext("com/datas/apk.k")
######print(APK)
API_KEY = APK
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
        g_config = genai.GenerationConfig(
     temperature=0.696231975971
)
    except Exception as e:
        print("ERROR API KEY:",e)
# Inicialización del modelo generativo



def write_context(nombre_archivo, texto_a_agregar):
    """
    Crea un archivo si no existe o añade texto al final si ya existe.

    Args:
        nombre_archivo (str): La ruta del archivo.
        texto_a_agregar (str): El texto a añadir al archivo.
    """
    try:
        with open(nombre_archivo, 'a+') as archivo:  # 'a+' abre el archivo para lectura y escritura (añadiendo al final)
            archivo.write(texto_a_agregar + "\n")  # Agrega el texto con un salto de línea
 #       print(f"Texto añadido al archivo: {nombre_archivo} ✅")
    except Exception as e:
        print(f"Error al escribir en el archivo: {e} ❌")




print("<div style='width:95%;font-size:10px;font-family:\"arial\";font-weight:bold;text-align:right;;padding:4px;display:block;color:green;'><b style='color:#aaaaff;'>Model:</b> ",gemini_model,"</div>")







load = ""
last_response = ""
topic = ""  # Tema de conversación
autosave_enabled = True  # Estado del autosave

def_image_editor = "mtpaint"


def is_file(filepath):
    """Verifica si el archivo existe."""
    fp = os.path.isfile(filepath)
    return fp

def read_file(filepath):
    """Lee el contenido de un archivo de texto y lo retorna."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print("Error", f"Error leyendo el archivo {filepath}: {e}")
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
        print("Error", f"Error guardando el archivo {filepath}: {e}")


def decode_img(base64_data):
    # Decode the base64 data
    decoded_data = base64_data
# Load the image
    image = Image.open(io.BytesIO(decoded_data))

# Display or save the image (uncomment as needed)
    image.show() 
    image.save('com/datas/ffmpeg/my_image.png')



#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

def show_text_window(text):
    win.show_text_window(text)



personajes = {}
modos = {}
desing_mode = {}
prompts = {}

srt_c = gp.aPrompt



def video_translate(video_file_name="",prompt="",args=None):
    global g_config, personajes, modos, sesgos, desing_mode, last_response,conversation_context,srt_c


    mprompt = ""
    if args != None :
        prs = prompt.split()        
        for arg in args:
#            print(f"\n\n\n-------------->\n\n\n----->  ",srt_c[args])
#            print(f" \n  @@@@Detected: {arg} \n ")
            xarg = arg[1:]
            if xarg in srt_c:
                mprompt += srt_c[xarg]
#                print(f"\n\n   EXIST:  {arg}   \n\n")
 
#        print("End Args")
#        return
    else:
        print("")
#        print("No Args")

#    print("MMMM: ",mprompt)
#    return

    if video_file_name.startswith('http://') or video_file_name.startswith('https://'):
#        print("Descargando video temporal")
        video_name = hashlib.md5(video_file_name.encode()).hexdigest()+".mp4"
        video_path = "../html/img/tmp/"
        code_video_file = video_path +video_name
        process = subprocess.run(["yt-dlp","-o",code_video_file,video_file_name], capture_output=True, text=True)
        video_download_url = video_file_name
        video_file_name = code_video_file
#        print("Video File:",video_file_name)
        input_video_info = f"Se ha descargado un vídeo desde: {video_download_url} \n"
        input_video_info += f"Se ha guardado el vídeo en disco con path: {video_file_name} \n"
#        print(input_video_info)
    else:
#        video_file_name="com/datas/ffmpeg/anon.mp4"
#        print("video_file")
        video_name = hashlib.md5(video_file_name.encode()).hexdigest()+".mp4"
        video_path = "../html/img/tmp/"
        code_video_file = video_path +video_name
        input_video_info = "VIDEO PATH: "+ code_video_file + "\n"
        return
        #vídeo file
#        return

    ct = f"Uploading file..."
    conversation_context += ct
#    print(ct)
    video_file = genai.upload_file(path=video_file_name)
    con = video_file.uri
    ct = f"Completed upload: {con}"
#    print(ct)    
#    print('Processing Video.... ', end='')
    while video_file.state.name == "PROCESSING":
        conversation_context += " . "
#        print('.', end=' ')
        vfm = video_file.state.name
        video_file = genai.get_file(video_file.name)
        conversation_context += str(video_file) + "\n" + vfm + "\n"
    if video_file.state.name == "FAILED":
        vfm = video_file.state.name
        conversation_context += "ERR IN VIDEO SEND FAILED:\n"+str(vfm)+"\n"
        raise ValueError("ERR IN VIDEO SEND FAILED:\n"+str(vfm)+"\n")
    else:
        input_video_info += f"Se ha subido el vídeo a Gemini-video a la url: {video_file.uri} \n"


    try:
        Datos_video = win.obtener_datos_multimedia(code_video_file)
#        print("DATOS VIDEO:\n",Datos_video)
    except Exception as e:
        print("Error obteniendo datos multimedia de:",code_video_file)


    # PROMPT's
    #prompti = prompts['sesgos']
    prompti = srt_c["creative"]
    if mprompt !="":
        prompt = mprompt + prompt

    if prompt == "":
        prompt = prompti 

    response = model.generate_content([video_file, prompt],
                                  request_options={"timeout": 600},generation_config=g_config)


#    print(response.text)
    pattern = r"```srt\n(.*?)\n```"
    matches = re.findall(pattern, response.text, re.DOTALL)
    if len(matches) == 1:
        htmlz = escape(matches[0])
        print(f"""
<textarea style="width:90%;resize:vertical">{htmlz}</textarea>
                   """)
        timestamp_unix = int(time.time()) 
        code_sub_name = video_name + "." + str(timestamp_unix) + ".subtitulado.mp4"
        subtitulado_out =  video_path + code_sub_name
        vtranslate= subtitulado_out + ".translate.srt"
        input_video_info += f"Se ha generado correctamente el archivo de subtitulado con path: {vtranslate}\n"
        input_video_info += f"El contenido del archivo de subtitulado es el siguiente: \n{matches[0]}\n"
        with open(vtranslate,"w",encoding='utf-8') as f:
            f.write(matches[0])

        force_style_sub = "BackColour=&H90000000,BorderStyle=4,FontName=NotoColorEmoji,Alignament=6"
        mode = "fixed" # bg / fixed
        if mode == "bg":
            print()
#            print("""   SP """)
        elif mode == "fixed":
            print()
#            print(""" FX """)
        obj = {
        "mode":mode,
        "name":None,
        "com":["ffmpeg","-y","-loglevel","error","-i",video_file_name,
        "-af","aresample=async=1,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-vf","scale=-2:720,subtitles="+vtranslate+":force_style='"+force_style_sub+"'",
	"-pix_fmt","yuv420p",
        "-preset","ultrafast",
        "-c:v","libx264","-c:a","aac","-crf","21",
        subtitulado_out] 
        }
#        print("Procesando Vídeo...\n")
        comando_ffmpeg = obj["com"]
#        print(" ".join(comando_ffmpeg)+"\n")




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
 #               print(e1)
                conversation_context += e1


                # El comando se ejecutó correctamente
        except FileNotFoundError:
            print("Error: El comando ffmpeg no se encontró. Asegúrate de que esté instalado y en tu PATH.")
            return False
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            return False

        return f"https://osiris000.duckdns.org/img/tmp/{code_sub_name}"
    else:
        return "606"



    # Print the response, r






def gen_com():

    pr = """

Aplicación Gen Prompt - (función interna de osiris.com.gemini (gemini.py))

El cometido de esta función es generar comandos en base a un propmt posterior por retroalimentación.

"""



def screen_shot():
    return
    #ELIMINADO PARA WEB



    
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
#        if e.code == 400:
#            print("ERROR 400")
        #messagebox.showerror("Error", f"Error generando contenido con el modelo: {e}")
        if str(e).startswith('Invalid operation:'):
            return "Se ha producido un error de operación inválida. La petición podría ser confusa para el modelo. Pruebe a mejorar su prompt."
        else:
            return "Error: "+str(e)


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


#print("HOLA")

# Nuevo: Guardar logs de conversación
def log_interaction(user_input, response_text):

    return
    # WEB DISABLED
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







def create_context(nombre_archivo, texto_a_agregar):

    """
    Crea un archivo y añade texto si no existe.
    Si el archivo existe, retorna None sin modificarlo.

    Args:
        nombre_archivo (str): La ruta del archivo.
        texto_a_agregar (str): El texto a añadir al archivo.

    Returns:
        None si el archivo existía, True si el archivo fue creado y escrito.
    """
    global INI_CONTEXT    
    if os.path.exists(nombre_archivo):

#        print(f"El archivo {nombre_archivo} ya existe. No se realizaron cambios. 🧐")
        return   # Retorna None si el archivo ya existe
    else:
        try:
            with open(nombre_archivo, 'w') as archivo: # 'w' abre el archivo para escritura, crea el archivo si no existe y lo sobreescribe si existe.

                CONTEXT_INI = """
                
                # Contexto de Conversación - Sesión CXID-88101c47cdb156f7f8323cae4235fa8e
                  Inferencia de Respuestas Previas: Activada
                  Cuando alguien no te hable de un tema concreto háblale tú del tema mas cercano que infieras.
                  Hasta la siguiente pregunta de cliente lo que sigue son preguntas previas debes inferir tus respuestas anteriores para mejorar la conversación. Eso hace la función de memoria virtual.
                  Pregunta al cliente al inicio como quiere que te dirijas a el/ella.
                                
                """  + INI_CONTEXT

                archivo.write(CONTEXT_INI+texto_a_agregar + "\n")  # Agrega el texto con un salto de línea
#            print(f"Archivo {nombre_archivo} creado y texto añadido. ✅")
            return True
        except Exception as e:
            print(f"Error al crear y escribir en el archivo: {e} ❌")
            return False




def load_context_(nombre_archivo):
    """
    Lee un archivo y devuelve su contenido como una cadena de texto.

    Args:
        nombre_archivo (str): La ruta del archivo.

    Returns:
        str: El contenido del archivo como una cadena de texto, o None si ocurre un error o el archivo no existe.
    """
    if not os.path.exists(nombre_archivo):
#        print(f"Error: El archivo {nombre_archivo} no existe. ❌")
        return None  # Retorna None si el archivo no existe

    try:
        with open(nombre_archivo, 'r') as archivo: # 'r' abre el archivo para lectura
            contenido = archivo.read()  # Lee todo el contenido del archivo
            return contenido # Retorna el contenido del archivo
    except Exception as e:
        print(f"Error al leer el archivo: {e} ❌")
        return None # Retorna None en caso de error


# Función para manejar los argumentos
def main(args):
    """Función principal que maneja los argumentos de entrada para generar respuestas del modelo."""
    global gemini_model, model, conversation_context, load, last_response, topic, API_KEY


    permitCom = ["--imp","--lsel","--tvl"]
    #return "ENTER"
    # Si no se envían comandos, se asume que se envía una pregunta de texto.
    #return "ENTER"
    # Si no se envían comandos, se asume que se envía una pregunta de texto.
    if args[0] == "--b64prompt":
        if len(args)<2:
            print("NP")
            return "Faltan argumentos a web prompt"
            #salimos y continuamos
        else:
            prompt = base64.b64decode(args[1]).decode("utf-8")
    elif args[0] == "--b64prompt-video":
#        print("Video")
        vurl = base64.b64decode(args[5]).decode("utf-8")
        prompt = base64.b64decode(args[1]).decode("utf-8").split()
        argsx = []
        for  zx in prompt: 
            if zx.startswith("@") :
                argsx.append(zx)
#        return       
#        print(vurl,prompt,argsx)
#        return
        video_translated = video_translate(vurl," ".join(prompt),argsx)
#        print("VT:",video_translated)
        if video_translated == "606":
            print(str(video_translated))
            return "Error al generar subtítulos"
            #en caso contrario continúa
        prompt = f""" 
        Envié un vídeo a gemini video y lo generó exitosamente en esta url enlace directo: {video_translated}
        Imprime sólo la url en formato link href embebible sin más comentarios al respecto, sólo su confirmación positiva (aquí está su vídeo).
        """

    if len(args)>3:
        if args[4].startswith("CXID-"):
            nombre_archivo = "com/web/datas/ai/"+str(args[4])+".user.context"
#            print("context:"+str(args[4])) 
            create_context(nombre_archivo, prompt) 
            conversation_context += load_context_(nombre_archivo)
            client_say = """

            Cliente Dice:
            
            """
            write_context(nombre_archivo, client_say+prompt)
            response_text = generate_response(client_say+prompt)
#            print(" 🎸 ")
            write_context(nombre_archivo, " \n La IA respondió:\n"+response_text+"\n\n")
            return response_text
#            return
        else:
            print("ERROR EN ARGUMENTOS 1217")
            return




fecha_hora = ""


def fecha_hora_g():
    global fecha_hora
    timestamp_unix = int(time.time()) 
    fecha_hora  = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_unix))
    return fecha_hora
#fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

fecha_hora = fecha_hora_g()


#if __name__ == "__main__":
 #   main(sys.argv[1:])
 


