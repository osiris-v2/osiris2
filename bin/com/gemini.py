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

script_dir = Path(__file__).resolve().parent

core.dynmodule("lib.gemini.utils","win")
win = core.win


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
conversation_context = f"""
#Interfaz de comunicación con Gemini AI de Google
#Interfaz Name: Osiris
#Version: {version_file}
#Idioma: Español
Instrucciones: ¡Bienvenido a Osiris!  Usa emojis para dinamizar la conversación.  Escribe --help para ver comandos disponibles.
\...

"""


gemini_models = ["gemini-2.0-flash-exp",
		 "gemini-1.5-flash",
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


select_model()

load = ""
last_response = ""
topic = ""  # Tema de conversación
autosave_enabled = True  # Estado del autosave

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
    win.show_text_window(text)



personajes = {}
modos = {}
desing_mode = {}
prompts = {}
srt_c = {}



srt_c["frang"] = """

Rango de tamaño de fuente.
Pequeña: 10 - 16
Pequeña-Media: 16-20
Media: 20 - 28
Grande: 28 - 32
Grande-Gigante: 32 - 40
Gigante: 40 - 50 
Super-Gigante:  50 - 60
Extra-Super-Gigante: 60 - 80
Extrema: 80 - 100

"""


srt_c["critica"] = """

!Modo critica

Modo de expresión: Crítica ácida.
Por lo tanto tienes que criticar al personaje señalado.
"""

srt_c["sanchez"] = """

!Modo sanchez


Para este vídeo emula al personaje.
Video Personaje: a usar: Javier Milei.
Características del personaje:
Presidente del gobierno de España.
Motes: Sanchinflas, Su Sanchidad, Pinocho, Psicópata.
Críticas: Que te vote Txapote

"""



srt_c["milei"] = """

!Modo milei

Para este vídeo emula al personaje.
Video Personaje: a usar: Javier Milei.
Para este vídeo emula al personaje.
Características del personaje.-
Idioma que habla el personaje: Argentino
Presidente de Argentina.
Motes: Cogehermanas.
Peyorativos: Chorros, Ladrones, Mandriles, Pelotudos, pelotudos de mierda, zurdos, boludos, inferiores, inferiores en todo, inferior, aberración, kukas, comunistas.
Personalidad: Variable - Border
Ego: Superior en todo.
Enemigos: Casta, Ñoquis.
Modo: Insultante, tiemblen. 
Enemigos: El Estado, el intervencionismo, los jubilados, los impuestos.
Expresiones comunes: No hay plata, no hay guita.
Latiguillos: Digamos osea.

"""


srt_c["sub_segmentos"] = """

Modelado de segmentos de subtitulado.




"""


srt_c["emoji"] = """

Usa Solo Emojis.


"""

srt_c["gigante"] = """

De tamaño Gigante.


"""







text_replace = {
    
    "",""
}



srt_c["sesgos"] = """

!Modo sesgos


Eres Gemini-video. Actúa como un guionista creativo y genera subtítulos para un vídeo de [duración del vídeo] segundos sobre [tema del vídeo].  En lugar de transcribir el audio, tu tarea es crear texto que refuerce el mensaje del vídeo y explore diferentes tonos y sesgos.  El vídeo tiene un fondo oscuro.

1. **Concepto del vídeo:** El vídeo trata sobre [describe el tema del vídeo con detalle].

2. **Tonos y Sesgos:** Explora los siguientes tonos y sesgos en diferentes segmentos del vídeo:

    * **[Tono 1]:** [Descripción del tono, por ejemplo, optimista, pesimista, sarcástico, etc.].
    * **[Tono 2]:** [Descripción del tono].
    * **[Sesgo 1]:** [Descripción del sesgo, por ejemplo, a favor de la tecnología, en contra del consumismo, etc.].
    * **[Sesgo 2]:** [Descripción del sesgo].

3. **Subtítulos:** Crea subtítulos concisos y fáciles de leer, con una duración máxima de 5 segundos, preferiblemente entre 2 y 2.5 segundos.  El intervalo mínimo entre subtítulos debe ser de 2 segundos.

4. **Formato .srt básico:**  Genera un archivo .srt con el formato estándar.  Utiliza etiquetas `<font>` para controlar el tamaño (16-24), color (colores claros y vibrantes) y fuente ("Impact" o "Noto Sans"). Usa `<b>` para negrita.

5. **Emojis descriptivos:** En cada línea del .srt, incluye de 1 a 3 emojis relevantes al texto y al tono/sesgo que se está explorando.  Indica el color deseado para cada emoji. Añade  `<font color="#FFFFFF"> </font>` justo antes del primer emoji.NUNCA  uses Emojis de banderas de países.


**Ejemplo (para un vídeo de 30 segundos sobre el impacto de la inteligencia artificial):**

**Concepto:** El vídeo muestra imágenes de robots, algoritmos y personas interactuando con la tecnología.

**Tonos y Sesgos:**
    * Optimista:  La IA como herramienta para el progreso y la solución de problemas globales.
    * Preocupado: El potencial de la IA para el desempleo y el control social.
    * Noticia: Es un asunto de interes.
    * Personajes: Emula o refiere a un personaje.
"""


srt_c["sub_artistico"] = """
#Modo Subtitulado Artístico

Eres un experto en subtítulos artísticos. Genera subtítulos que no solo transcriban el diálogo, sino que también reflejen la emoción, el ritmo y el tono del video. Usa un lenguaje expresivo y evocador, y deja espacio para la interpretación personal del espectador. Los subtítulos deben ser una extensión del arte visual.
"""


srt_c["sub_noticia"] = """
#Modo Subtitulado Noticia

Eres un experto en subtítulos de noticias. Genera subtítulos precisos, concisos, y objetivos. Prioriza la claridad y la exactitud en la transcripción del audio, evitando cualquier tipo de interpretación o sesgo. Los subtítulos deben proporcionar información neutral y verificable, sin añadir elementos subjetivos.
"""



srt_c["sub_narrativo"] = """
#Modo Subtitulado Narrativo

Eres un experto en subtítulos narrativos. Crea subtítulos que guíen al espectador a través de la historia, proporcionando contexto y cohesión. Utiliza un lenguaje claro y accesible, pero que también sea capaz de crear intriga y curiosidad. Los subtítulos deben enriquecer la experiencia narrativa del video.
"""


srt_c["sub_humoristico"] = """
#Modo Subtitulado Humorístico

Eres un experto en subtítulos humorísticos. Transcribe el audio pero adapta el texto para potenciar el humor del video, utilizando juegos de palabras, ironía y sarcasmo cuando sea apropiado, pero siempre respetando el sentido original del audio. Los subtítulos deben arrancar una sonrisa al espectador.
"""


srt_c["sub_formal"] = """
#Modo Subtitulado Formal

Eres un experto en subtítulos formales. Transcribe el audio de manera precisa, utilizando un lenguaje correcto y culto. Evita coloquialismos y jerga, y mantén un tono sobrio y respetuoso. Los subtítulos deben ser adecuados para un contexto formal o académico.
"""

srt_c["sub_coloquial"] = """
#Modo Subtitulado Coloquial

Eres un experto en subtítulos coloquiales. Transcribe el audio de manera natural, utilizando un lenguaje cotidiano y expresiones populares. Incluye jerga, coloquialismos y muletillas siempre que sea apropiado, y adáptalos al contexto cultural del video. Los subtítulos deben sonar como una conversación informal.
"""

srt_c["sub_poetico"] = """
#Modo Subtitulado Poético

Eres un experto en subtítulos poéticos. Transcribe el audio transformando las palabras en un poema, adaptando la estructura y el ritmo del texto a la melodía del video. Utiliza metáforas, comparaciones y otras figuras retóricas. Los subtítulos deben ser una obra de arte en sí mismos.
"""

srt_c["sub_emocional"] = """
#Modo Subtitulado Emocional

Eres un experto en subtítulos emocionales. Transcribe el audio y añade elementos que reflejen las emociones del video, utilizando exclamaciones, interrogaciones y otros recursos expresivos. El texto debe transmitir la misma intensidad emocional que el video. Los subtítulos deben hacer vibrar el corazón del espectador.
"""

srt_c["sub_tecnico"] = """
#Modo Subtitulado Técnico

Eres un experto en subtítulos técnicos. Transcribe el audio de manera clara y precisa, utilizando un lenguaje técnico y específico del ámbito que trate el video. Incluye los acrónimos, siglas y términos técnicos relevantes en cada línea del subtitulado. Los subtítulos deben ser una guía para profesionales del sector.
"""



srt_c["fbold"] = srt_c["frang"] + """

Fuente Seleccionada Bold.
Usa fuente tamaño rango: Grande
Emojis tamaño rango: Grande
Usar negritas para todos los emojis siempre y colores fuertes brillantes.
User negrita para los textos.


"""


srt_c["fweight"] = srt_c["frang"] + """

Fuente Seleccionada weight.
Usa fuente tamaño rango: Media
Emojis tamaño rango: Media


"""



srt_c["fnormal"] = srt_c["frang"] + """

!Modo fnormal

Fuente Seleccionada normal.
Usa fuente tamaño rango: Pequeña-media
Emojis tamaño rango: Pequeña

"""


srt_c["creative"] = """

!Modo creative

Tu eres gemini-video. Tu tarea es generar un archivo .srt con subtítulos para el vídeo que te estoy proporcionando. Debes traducir todo al español si no se te indica otro idioma más adelante.  

Tu objetivo es crear subtítulos precisos y contextualmente relevantes,  que reflejen con exactitud el contenido del vídeo sin añadir interpretaciones subjetivas o sensacionalistas. Prioriza la objetividad y la neutralidad.

1. **Transcripción y Traducción:** Transcribe el audio del vídeo con la mayor precisión posible y traduce todo al español excepto que se te explicite otro distinto. Si hay secciones sin audio o con audio irrelevante para la traducción (ej: música de fondo, sonidos ambientales), describe brevemente el contenido visual en español.

2. **Generación del archivo .srt:** Genera un archivo .srt que incluya:

    * **Formato SRT:** El archivo debe cumplir estrictamente el formato .srt.

    * **Etiquetas HTML:** Utiliza las siguientes etiquetas HTML dentro de cada línea de texto del subtítulo para controlar el estilo: `<font size="value" color="value" face="value"></font>` y `<b></b>`.

        * **`size`:** El tamaño de la fuente  de forma que si el formato del vídeo es predominante vertical use fuentes más pequeñas y horizontal más grandes.  Utiliza diferentes tamaños para enfatizar ciertas palabras o frases,  manteniendo un equilibrio visual.
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


""" 




srt_c["@f"] = """
!modo @f
Dynamic mode-.
Usa para esta segmentacion:
Fuente tamaño rango: Grande
Emojis tamaño rango: Grande-Gigante
Los colores deben dar una sensación de claridad e intensidad.  Para ello, utiliza una gama de colores con códigos hexadecimales que se encuentren e de la rueda de color, pero con una saturación moderada.

Rangos de colores por defecto:

Colores Claros:

* `#FAF0E6` (AntiqueWhite)
* `#FFF8DC` (Cornsilk)
* `#FDEFE0` (LightYellow)
* `#FAFAF9` (FloralWhite)
* `#FFFFE0` (LightYellow)
* `#FFFFF0` (Snow)
* `#F0FFF0` (Honeydew)
* `#F5FFFA` (MintCream)
* `#F0FFFF` (Azure)
* `#F5F5DC` (Beige)
* `#FFFFFA` (WhiteSmoke)
* `#FFF5EE` (Seashell)
* `#FFE4E1` (MistyRose)
* `#FFE4C4` (Bisque)
* `#FFF0F5` (LavenderBlush)
* `#FFFAF0` (FloralWhite)
* `#FDF5E6` (OldLace)
* `#F5F5F5` (Gainsboro)
* `#FFEBCD` (BlanchedAlmond)


Colores Oscuros:

* `#A0522D` (Sienna)
* `#8B4513` (SaddleBrown)
* `#A52A2A` (Brown)
* `#800000` (Maroon)
* `#800080` (Purple)
* `#4B0082` (Indigo)
* `#8A2BE2` (BlueViolet)
* `#9400D3` (DarkViolet)
* `#9932CC` (DarkOrchid)
* `#800080` (Purple)
* `#FF0000` (Red)
* `#008000` (Green)
* `#FFFF00` (Yellow)
* `#00FFFF` (Cyan)
* `#FF00FF` (Magenta)
* `#FF69B4` (HotPink)
* `#FF6347` (Tomato)
* `#FF4500` (OrangeRed)
* `#FFA07A` (LightSalmon)
* `#FFFAFA` (Snow)
* `#FFDAB9` (PeachPuff)
* `#FA8072` (Salmon)
* `#FFB6C1` (LightPink)
* `#FFDEAD` (NavajoWhite)
* `#DEB887` (BurlyWood)
* `#D2691E` (Chocolate)
* `#BC8F8F` (RosyBrown)
* `#CD853F` (Peru)


Colores Medios:

`#E67E22` (Carrot Orange):** Un naranja cálido y vibrante.
`#27AE60` (Emerald Green):** Un verde intenso y natural.
`#3498DB` (Peter River Blue):** Un azul claro y fresco.
`#8E44AD` (Wisteria Purple):** Un morado elegante y sutil.
`#F39C12` (Orange):** Un naranja más brillante que el Carrot Orange.
`#1ABC9C` (Emerald):** Un verde un poco más claro que el Emerald Green.
`#2980B9` (Belize Hole Blue):** Un azul más oscuro que el Peter River Blue.
`#9B59B6` (Amethyst Purple):** Un morado más intenso que el Wisteria Purple.
`#D35400` (Pumpkin Orange):** Naranja más oscuro y terroso.
`#2ECC71` (Nephritis Green):** Verde más claro y pastel.


Utiliza los colores de la lista anterior dentro de sus rangos creativamente a tu libre albedrío para el texto cuando el fondo del video sea oscuro, y los colores oscuros cuando el fondo sea claro.  Determina la luminosidad del fondo en tiempo real, a nivel de milisegundo, para la selección del color correcto.  Si no se puede determinar la luminosidad del fondo con precisión al milisegundo, utiliza una aproximación lo más precisa posible. Prioriza la legibilidad en todas las condiciones de luminosidad de fondo. Esto aplica a textos y emojis.


Usa saltos <br> para crear una segmentación dinámica.
Juega con los tiempos del video y de la segmentación.
usa dos tipos de segmentación en dos tiempos distintos.
uno con segmentación entre 2 y 4 segundos.
y otro con segmentaciones rápidas con duraciones máximas de 0.999 y mínimas de 0.100 segunos.
Separados por saltos de línea cuando coincidan.
Usar segun requiera el guión de video/audio observado.
Juega con las fuentes usando distinto tipo entre textos y segmentos acorde con su tipo a nivel medio+ randomizándolas.
Usa distintas fuentes de la lista de fuentes disponibles tanto para textos como para emojis.
Usa fuentes legibles para textos y simbólicas para los emojis.


Usa para esta segmentación:

Segmentación Temporal:

Segmentos Rápidos (0.100 - 0.999 segundos):  Máximo 4 palabras por segmento.  Estas secciones cortas deben coincidir con cambios bruscos de tono o ritmo en el audio del vídeo.  Para identificar estos momentos, analiza la energía del audio (amplitud de la onda sonora):  si la energía sube significativamente, genera un segmento rápido.  Utiliza fuentes con un estilo más informal (Ej:  `Impact`, `Comic Sans MS`).
Segmentos Lentos (1.250 - 2.900 segundos):  Máximo 5 palabras por segmento. Estas secciones más largas deben abarcar partes del vídeo con una narrativa más continua.  Utiliza fuentes más formales y legibles (Ej: `Georgia`, `Times New Roman`, `Arial`).

**Selección de Fuentes:**

Para cada segmento, elige una fuente aleatoriamente de la siguiente lista: 

Fuentes para Textos (Segmentos Rápidos y Lentos): `Arial`, `Georgia`, `Times New Roman`, `Verdana`, `Impact`, `Comic Sans MS`, puedes usar otras de entre la lista que sean haituales como fuentes de texto tipo latino.
Fuentes para Emojis (Segmentos Rápidos y Lentos): Para los emojis puedes usar todo tipo de fuentes disponibles por ejmeplo: `Impact`, `Wingdings`, `Webdings`, `Zapf Dingbats`, entre otras. 

Alternancia de Fuentes:  No debe haber dos segmentos consecutivos con la misma fuente para textos ni para emojis.


Usar también fuentes de la lista completa de fuentes si hay.

Saltos de Línea: Usa `<br>` para separar distintos segmentos que ocupen un mismo espacio de tiempo.

Como regla General: Maximo palabras por cada segmento: 5.


Lista de fuentes disponibles:

Standard Symbols PS:style=Regular
Bitstream Vera Sans:style=Bold
Verve:style=Regular
TypoUpright BT:style=Regular
CloneWars:style=Regular
Neverwinter:style=Normal
Lucida Console:style=Regular,Normal,obyčejné,Standard,Κανονικά,Normaali,Normál,Normale,Standaard,Normalny,Обычный,Navadno,Arrunta
SansSerifFLF:style=Demibold
 Blade 2:style=Regular
 Underground:style=Normal
 Army Thin:style=Regular
 One Flew Over The Cuckoo's Nest:style=Regular
 Anglo Text:style=Regular
 FarCry:style=ExtraBold
 Scream alternative:style=Regular
 P052:style=Italic
 Telegraphic:style=Regular
 Alba Super:style=Regular
 Famous Logos:style=Regular
 C059:style=Bold Italic
 Video Star:style=Regular
 kallot:style=Regular,Standaard
 BTSE + PS2 FONT:style=Regular
 Microsoft Sans Serif:style=Regular,Normal,obyčejné,Standard,Κανονικά,Normaali,Normál,Normale,Standaard,Normalny,Обычный,Normálne,Navadno,Arrunta
 URW Gothic:style=Demi Oblique
 Hellraiser SC:style=Regular
 Bitstream Vera Sans:style=Bold Oblique
 Raiders:style=Extra Bold
 Pointedly Mad:style=SmallCaps
 Back to the future 2002:style=Regular
 SF Intellivised:style=Bold Italic
 Lost Highway:style=Regular
 SF Atarian System:style=Bold
 DejaVu Sans:style=Bold Oblique
 Tasteless Candy:style=Regular
 Running shoe:style=Regular
 AlphaFitness:style=Regular
 Wingdings:style=Regular,normal,Standard,Normaali,Normale,Standaard,Normálne,Navadno
 Kinkee:style=Regular
 Anklepants:style=Regular
 SansSerifFLF:style=Italic
 FreeSans:style=Cursiva,Oblique,наклонен,negreta cursiva,kurzíva,kursiv,Πλάγια,Kursivoitu,Italique,Dőlt,Corsivo,Cursief,kursywa,Itálico,oblic,Курсив,İtalik,huruf miring,похилий,Ležeče,slīpraksts,pasvirasis,nghiêng,Etzana,तिरछा
 Mobile Infantry,Continuum Bold:style=Regular
 Tintin Majuscules:style=Bold
 Nimbus Sans Narrow:style=Regular
 Hirosh:style=Normal
 SF Distant Galaxy Alternate:style=Regular
 Gotham Nights:style=Normal
 Nasalization:style=Medium
 DV TTSurekh:style=Italic
 Lobster 1.4:style=Regular
 DejaVu Sans:style=Book
 Nimbus Mono PS:style=Bold
 Trebuchet MS:style=Regular,Normal,obyčejné,Standard,Κανονικά,Normaali,Normál,Normale,Standaard,Normalny,Обычный,Normálne,Navadno,Arrunta
 WP MultinationalA Courier:style=Normal
 Army Hollow Expanded:style=Regular
 InvisibleKiller:style=Regular
 Care Bear Family:style=Regular
 Interdimensional:style=Regular
 Bitstream Vera Sans:style=Roman
 BankGothic:style=Regular
 CrayonL:style=Regular
 Fatboy Slim BLTC (BRK):style=Regular
 XFiles:style=Regular
 Ringbearer:style=Medium
 BatmanForeverAlternate:style=Regular
 007 GoldenEye:style=Regular
 barcode font:style=Regular
 Adventure:style=Normal
 SF Atarian System Extended:style=Regular
 SF Intellivised Extended:style=Italic
 Sci Fied:style=BoldItalic
 VTCBelialsBlade3d:style=regular
 Beast Wars:style=Regular
 SI Font,Impact:style=Regular
 Final Fantasy,New:style=Classical,Regular
 Shadow of Xizor:style=Regular
 Beckett:style=Regular
 SF Intellivised:style=Italic
 Kruti Dev 010:style=Bold
 2006 Team:style=Regular
 Mars Attacks:style=Regular
 C059:style=Bold
 Old English:style=Regular
 Morpheus:style=Regular
 Phorfeit Slant (BRK):style=Regular
 28 Days Later:style=Regular
 Quatl Italic:style=Italic
 Weltron Special Power:style=Regular
 BernhardFashion BT:style=Regular
 Alison:style=Regular
 GAMECUBEN:style=DualSet
 URW Gothic:style=Book Oblique
 CrayonE:style=Regular
 Gremlins:style=Regular
 GoudyOlSt BT:style=Bold Italic
 Candide Dingbats:style=Regular
 Adam's Font,Captain Podd:style=Regular
 DejaVu Sans Mono:style=Book
 EuroseWide Heavy:style=Regular
 Star Jedi:style=Regular
 SF Distant Galaxy Outline:style=Italic
 SF Fortune Wheel Condensed:style=Italic
 BatmanForeverOutline:style=Regular
 04b03:style=Regular
 Parseltongue:style=Regular
 InvisibleKiller:style=Regular
 Facelift:style=Regular
 signs zeichen 2.0:style=Regular
 DV_Divyae:style=Bold Italic
 FreeMono:style=Negrita,Bold,получерен,negreta,tučné,fed,Fett,Έντονα,Lihavoitu,Gras,Félkövér,Grassetto,Vet,Halvfet,Pogrubiony,Negrito,gros,Полужирный,Fet,Kalın,huruf tebal,жирний,polkrepko,treknraksts,pusjuodis,đậm,Lodia,धृष्ट
 007 GoldenEye:style=Regular
 Georgia:style=Regular,Normal,obyčejné,Standard,Κανονικά,Normaali,Normál,Normale,Standaard,Normalny,Обычный,Normálne,Navadno,Arrunta
 DV_Divya:style=Normal
 Tafelschrift:style=Regular
 FakeReceipt:style=Regular
 Interdimensional:style=Regular
 SF Fortune Wheel:style=Italic
 Ballpark:style=Weiner
 Old Republic:style=Italic
 Viking Normal:style=Regular
 Proclamate Ribbon:style=Heavy
 Futura Md BT:style=Bold
 BlackJack:style=Regular
 Proclamate Outline:style=Heavy
 OldEgyptGlyphs:style=Regular
 Tribeca:style=Regular
 HalfLife:style=Regular
 A Charming Font:style=Regular
 WP MultinationalA Roman:style=Normal
 URW Bookman:style=Light
 Nosegrind Demo:style=Regular
 BankGothic Md BT:style=Medium
 Nosegrind Demo:style=Regular
 DejaVu Serif:style=Book
 Standard Symbols PS:style=Regular
 Bremen Bd BT:style=Bold
 FreeSans:style=Cursiva,Oblique,наклонен,negreta cursiva,kurzíva,kursiv,Πλάγια,Kursivoitu,Italique,Dőlt,Corsivo,Cursief,kursywa,Itálico,oblic,Курсив,İtalik,huruf miring,похилий,Ležeče,slīpraksts,pasvirasis,nghiêng,Etzana,तिरछा
 FreeMono:style=Negrita,Bold,получерен,negreta,tučné,fed,Fett,Έντονα,Lihavoitu,Gras,Félkövér,Grassetto,Vet,Halvfet,Pogrubiony,Negrito,gros,Полужирный,Fet,Kalın,huruf tebal,жирний,polkrepko,treknraksts,pusjuodis,đậm,Lodia,धृष्ट
 P052:style=Roman
 Turtles:style=Normal
 Raiders:style=Extra Bold
 Palatino Linotype:style=Italic,Cursiva,kurzíva,kursiv,Πλάγια,Kursivoitu,Italique,Dőlt,Corsivo,Cursief,Kursywa,Itálico,Курсив,İtalik,Poševno,nghiêng,Etzana
 1942 report:style=1942 report
 Liberation Sans Narrow:style=Bold Italic
 SF Fortune Wheel Condensed:style=Regular
 Africain:style=Regular
 SeyesBDL:style=Regular
 AltamonteNF:style=Regular
 Beynkales Demo:style=Regular
 DuvallOutline:style=Normal
 Firestarter:style=Regular
 C059:style=Bold
 Legothick,LEGothic:style=Regular,Type
 Nimbus Roman:style=Bold
 Liberation Serif:style=Bold Italic
 BankGothic:style=Regular
 Feast of Flesh BB:style=Regular
 Buffied:style=Regular
 Liberation Sans Narrow:style=Regular
 Alba:style=Regular
 Love Letters:style=Regular
 P052:style=Bold
 Rafika:style=Regular
 Allencon Demo:style=Regular
 Exocet:style=Light
 Karloff:style=Regular
 Georgia:style=Italic,Cursiva,kurzíva,kursiv,Πλάγια,Kursivoitu,Italique,Dőlt,Corsivo,Cursief,Kursywa,Itálico,Курсив,İtalik,Poševno,Etzana
 Nirvana,Onyx:style=Regular
 Orgy:style=Regular
 Quatl Italic:style=Italic
 SansSerifExbFLFCond:style=Italic
 Beckett:style=Regular
 Gauze Strips:style=Gauze Strips
 ESP:style=Regular
 Dummies:style=Regular
 Sickness:style=Regular
 Fatboy Slim BLTC (BRK):style=Regular
 Bjork:style=Regular
 Army Expanded:style=Regular
 C39HrP24DhTt:style=Normal
 Adorable:style=Regular
 SF Atarian System Extended:style=Bold
 Ribbon131 Bd BT:style=Bold
 URW Gothic:style=Demi Oblique
 a Theme for murder:style=Regular,Normal,obyčejné,Standard,Κανονικά,Normaali,Normál,Normale,Standaard,Normalny,Обычный,Normálne,Navadno,Arrunta
 BankGothic:style=Regular
 SansSerifBookFLF:style=Medium
 Gayane StO:style=Regular
 SF Fortune Wheel:style=Italic
 Star Jedi Hollow:style=Regular
 Anywhere:style=Regular,Normal,obyčejné,Standard,Κανονικά,Normaali,Normál,Normale,Standaard,Normalny,Обычный,Normálne,Navadno,Arrunta
 SeyesBDE:style=Regular
 Nimbus Sans:style=Bold
 Nimbus Roman:style=Bold Italic
 Swatch it:style=Regular
 WP MathB:style=Normal
 namco regular:style=Regular
 Whatafont:style=Regular
 Nimbus Sans:style=Bold Italic
 Space Cruiser:style=Regular
 Old Republic:style=Bold
 Asenine Super Thin:style=Regular
 Nimbus Roman:style=Italic
 ACCELERATOR:style=Normal
 Humanst521 BT:style=Bold
 Border Corners:style=Regular
 OzHandicraft BT:style=Roman
 Paradise's Fruits:style=Regular
 Blade Runner Movie Font:style=Regular
 DejaVu Sans:style=Bold Oblique
 Bitstream Vera Sans Mono:style=Roman
 FreeSans:style=Regular,нормален,Normal,obyčejné,Mittel,µεσαία,Normaali,Normál,Medio,Gemiddeld,Odmiana Zwykła,Обычный,Normálne,menengah,прямій,Navadno,vidējs,normalusis,vừa,Arrunta,सामान्य
 Swiss Cheesed:style=Regular
 Groovalicious Tweak:style=Regular
 KInifed:style=Regular
 Spawned:style=Regular
 Will:style=Robinson
 Futurama Alien Alphabet One:style=Regular
 ZapfEllipt BT:style=Italic
 Tribal:style=Regular
Humanst521 BT:style=Bold
Border Corners:style=Regular
OzHandicraft BT:style=Roman
Paradises Fruits:style=Regular
Blade Runner Movie Font:style=Regular
DejaVu Sans:style=Bold Oblique
Bitstream Vera Sans Mono:style=Roman
FreeSans:style=Regular,нормален,Normal,obyčejné,Mittel,µεσαία,Normaali,Normál,Medio,Gemiddeld,Odmiana Zwykła,Обычный,Normálne,menengah,прямій,Navadno,vidējs,normalusis,vừa,Arrunta,सामान्य
SWC_____.TTF: Swiss Cheesed:style=Regular
Groovalicious Tweak:style=Regular
KInifed:style=Regular
Spawned:style=Regular
WillRobinson.ttf: Will:style=Robinson
Futurama Alien Alphabet One:style=Regular
ZapfEllipt BT:style=Italic
Tribal:style=Regular



"""







srt_c["def"] = srt_c["defautl"] = """


!Modo default.

Eres Gemini-video. Genera un archivo SRT con subtítulos en el idioma especificado (por defecto, español si no se te indica otro distinto más adelante).

Prioridades:

1. Precisión en la transcripción y traducción.
2. Sincronización temporal exacta.  **Los subtítulos deben tener una duración de entre 1 y 5 segundos.  En casos excepcionales un subtítulo puede durar hasta 5 segundos máximo. Por lo tanto predomina una longitud de textos medios-cortos.


Formato:

* Cumple estrictamente el formato SRT.
* Usa etiquetas HTML: `<font size="18-22" color="#hexadecimal" face="Noto Sans/DejaVu Sans/">texto</font>` y `<b>texto importante</b>`. 
* Incluye emojis relevantes con **tamaño y color variable para mayor impacto visual y utiliza colores que reflejen la emoción o el significado del emoji.  Por ejemplo, un emoji de fuego (🔥) podría ser rojo o naranja, mientras que un emoji de hielo (🧊) podría ser azul claro.
* Usa Fuentes de tamaño medio si no se te indican otro tamaño más adelante.


Ejemplo:

```srt
1
00:00:00,500 --> 00:00:02,000
<font size="19" color="#D2691E" face="Noto Sans">El portavoz afirma:</font>
2
00:00:02,000 --> 00:00:03,500
<font size="21" color="#FFA500" face="Noto Sans">"Nuestra operación comienza ahora."</font>  <font size=24 color=#F11C00 face=impact>⚔️</font> <font size=28 color=#FF8C00 face=impact>💥</font>
```

Asegúrate de que la duración de cada subtítulo coincida exactamente con la duración de la frase hablada en el vídeo.  Prioriza la precisión temporal sobre la duración máxima de 5 segundos por subtítulo; si una frase es más larga de 5 segundos, divídela en varios subtítulos que mantengan la sincronización precisa con la voz.

Debes generar un solo archivo srt


"""   














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
#        return
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
#        return
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
        conversation_context += "ERR IN VIDEO SEND FAILED:\n"+str(vfm)+"\n"
        raise ValueError("ERR IN VIDEO SEND FAILED:\n"+str(vfm)+"\n")
    else:
        input_video_info += f"Se ha subido el vídeo a Gemini-video a la url: {video_file.uri} \n"


    try:
        Datos_video = win.obtener_datos_multimedia(code_video_file)
        print("DATOS VIDEO:\n",Datos_video)
    except Exception as e:
        print("Error obteniendo datos multimedia de:",code_video_file)

    # Create the prompt.
    prompti = "Tu eres gemini-video Tu tarea es Subtitular vídeos, hazlo en formato .srt con este formato ```srt  (traducion en formato srt) ``` "
    prompti += "\n Usa Arial como fuente predeter_minada pero puedes usar otras si lo requiere el contexto del video."
 #   prompti +="\ncolorea los emojis y hazlos en tamaños variables dentro del rango." 
    prompti +="\nEtiquetas permitidas en el srt <font size=value color=value face=value></font><b></b> usa colores brillantes claros para el texto ajustandolos en formato hexadecimal."
    prompti += "Transcribe y traduce el audio del video en español si no se especifica otro idioma.  Para cada frase o sección significativa del diálogo, proporciona un subtítulo con una duración máxima de 5 segundos. Si la frase es más larga, divídala en múltiples subtítulos. Asegúrate de que la traducción sea precisa y neutral. Usa emojis que reflejen el tono y el contenido emocional de cada parte del discurso (por ejemplo, 😡 para la ira, 💣 para una explosión, etc.). Evita emojis que puedan resultar inapropiados o que puedan cambiar el significado de la traducción."
    prompti +="\nUsa el formato que permita .srt usando html y styles permitidos con fuentes con rango entre 17 y 21 si no se especifica otro, que el vídeo va a ser procesado por ffmpeg entonces son válidas."








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
#        last_response = " ".join(comando_ffmpeg)


    else:
        print("No se generó el archivo de subtitulos correctamente")
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
    global ruta_archivo_key, gemini_model, model, conversation_context, load, last_response, topic, API_KEY


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
        if command == "--resetkey":
            print("keycom")
            API_KEY = obtener_key_gemini('resetkey')
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(gemini_model) 
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
                print("VOID D")
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
HELO = "HELO START - Se Ha inciado el SISTEMA OSIRIS a las: " + fecha_hora
main(HELO)
conversation_context += HELO+"\n"
if __name__ == "__main__":
    init = init + 1
    if init > 1:
        HELO = ""

    main(sys.argv[1:] + HELO )

