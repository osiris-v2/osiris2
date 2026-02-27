"""
Módulo para la conversión de texto a voz (Text-to-Speech) en Osiris.
Convierte texto a voz, guarda el audio si se indica, y lo reproduce con ffplay.
"""

from gtts import gTTS
import os
import tempfile
import subprocess
import sys
import time
import lib.core as core
import re

print(core.INFO)





# Ejemplo de uso:
# obj = {
#     "mode": "fixed",
#     "name": None,
#     "com": ["ping", "-c", "4", "google.com"],
#     "metadata": {"user": "john_doe"}
# }
# multiprocess(obj)



chflag = False
file = None

def flags(param):
    global file
    file = param[0]
    global chflag
    chflag = True

def flags_r(param):
    global file
    file = param[0]
    flagw()

def flagw():
    global file
#    print(file)
    with open(file,"w+") as z:
        timex = time.time()
        z.write("last_request.mp3 - "+str(timex)) 



def pt_audio(text):
    """Limpia el texto eliminando bloques de código Markdown y caracteres problemáticos."""
    # Eliminar bloques de código Markdown (```...)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Eliminar comillas simples y dobles
    text = text.replace("'", "").replace('"', '')
    # Eliminar caracteres especiales problemáticos para audio (ej: asteriscos, hashes, etc.)
    text = re.sub(r"[*#'`\[\]\(\)\{\}\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002600-\U000027BF]+", " ", text) # Reemplaza con espacios y emojis
#    text = re.sub(r"[*#'`\[\]\(\)\{\}]", " ", text)  # Reemplaza con espacios
    return text


def text_to_speech(text: str, lang: str = 'es', save_path: str = None) -> str | None:
    """
    Convierte el texto a voz, guarda el audio si se indica, y lo reproduce.

    Args:
        text (str): El texto a sintetizar.
        lang (str): El idioma del texto (por defecto 'es').
        save_path (str, optional): Ruta del archivo donde guardar el audio.
                                   Si None, se crea un archivo temporal.

    Returns:
        str | None: Ruta del archivo de audio generado o None si hubo error.
    """
    
    global chflag

    text = pt_audio(text) #Limpia texto para audio
#    print("AUDIO TEXT:",text)

#    print(f"Osiris-TTS: Iniciando conversión de texto a voz para: '{text[:1]}...' (Idioma: {lang})")

    # Intentar crear objeto gTTS
    try:
        tts = gTTS(text=text, lang=lang)
#        print("Osiris-TTS: Objeto gTTS creado con éxito.")
        if chflag == True:
            time.sleep(1)
            flagw()
            cgflag = False
    except Exception as e:
#        print(f"Osiris-TTS ERROR: Fallo al crear el objeto gTTS: {e}", file=sys.stderr)
        return None

    # Definir ruta donde se guardará el audio
    if save_path:
        audio_path = save_path
    else:
        fd, temp_path = tempfile.mkstemp(suffix=".mp3", prefix="osiris_tts_")
        os.close(fd)
        audio_path = temp_path

    # Guardar el archivo de audio
    try:
        tts.save(audio_path)
#        print(f"Osiris-TTS: Audio guardado con éxito en: {audio_path}")
    except Exception as e:
#        print(f"Osiris-TTS ERROR: No se pudo guardar el audio: {e}", file=sys.stderr)
        return None

    # Comprobar si el archivo fue creado correctamente
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        print(f"Osiris-TTS ERROR: Archivo de audio no válido o vacío: {audio_path}", file=sys.stderr)
        if not save_path and os.path.exists(audio_path):
            os.remove(audio_path)
        return None
#    os.remove(audio_path)

#    print(f"Osiris-TTS: Reproduciendo archivo de audio ({os.path.getsize(audio_path)} bytes)...")

    # Reproducir audio con ffplay en background (no bloquea el hilo principal)
    # Timeout=15s causaba cortes en respuestas largas → se elimina communicate()
    player_command = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_path]
    try:
        # Popen sin communicate() → lanza y continúa de inmediato
        subprocess.Popen(
            player_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("....audio....")
    except FileNotFoundError:
        print("Osiris-TTS ERROR: 'ffplay' no instalado o no encontrado en PATH.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Osiris-TTS ERROR inesperado: {e}", file=sys.stderr)
        return None
    # No limpiamos el temporal aquí: ffplay puede seguir leyéndolo
    return audio_path