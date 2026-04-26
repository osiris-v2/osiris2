#!/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          OSIRIS - Interfaz Mistral AI  (mistral2.py)            ║
║          Adaptado desde gemini2.py  →  Mistral API              ║
║          + mistral_context.py integrado via dynmodule           ║
╚══════════════════════════════════════════════════════════════════╝
"""
import sys
import os
import json
from mistralai import Mistral
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
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
#  str_c (plantillas SRT)
# ─────────────────────────────────────────────────────────────────
try:
    import lib.gemini.str_c as strimp
    srt_c_import = strimp.srt_c
except Exception:
    srt_c_import = {}

# ─────────────────────────────────────────────────────────────────
#  Importaciones dinámicas  (igual que gemini2.py)
# ─────────────────────────────────────────────────────────────────
try:
    core.dynmodule("lib.gemini.utils", "win")
    win = core.win
    core.dynmodule("lib.gemini.cro_parser", "CROPARSER")
    croparser = core.CROPARSER
    core.dynmodule("lib.gemini.audio_parser", "AP")
    audioparser = core.AP
    core.dynmodule("lib.cuarzo", "aceroK")
    acero = core.aceroK
    core.dynmodule("lib.gemini.load_osiris_context", "LOC")
    LOC = core.LOC
    core.dynmodule("lib.gemini.command_map", "ComMap")
    ComMap = core.ComMap
    commands_map = ComMap.commands_map
    core.dynmodule("lib.gemini.sftp", "SSHC")
    SSHC = core.SSHC
    core.dynmodule("lib.fftv", "fftv")
    FFTV = core.fftv
except Exception as E:
    print("ERDyM:", E)
    commands_map = {}

# ─────────────────────────────────────────────────────────────────
#  mistral_context  →  carga dinámica via dynmodule
# ─────────────────────────────────────────────────────────────────
mctx        = None   # módulo gestor de contexto
MCX_MANAGER = None   # instancia MistralContextManager

try:
    core.dynmodule("lib.gemini.mistral_context", "MCTX")
    mctx = core.MCTX
    print("[CTX] mistral_context cargado via dynmodule ✅")
except Exception as _mctx_err:
    print(f"[CTX] mistral_context no disponible ({_mctx_err}). Usando historial simple.")

# ─────────────────────────────────────────────────────────────────
#  Sesión
# ─────────────────────────────────────────────────────────────────
DYN_CONTEXT = {
    "info": "Mantiene una copia del contexto dividido en segmentos "
            "(preguntas/respuestas) serializado por claves con distinto "
            "significado | timestamp | relevancia | funcion | glyph | CRO | ..."
}

sessname = "Def_ses_name"

def _init_sessid():
    global sessname
    bytess = str(time.time()).encode("utf-8")
    sid    = hashlib.md5(bytess).hexdigest()
    sessname = "SESSID_" + sid
    return sid

sessid = _init_sessid()
print("SESSION INICIADA ID/NAME:", sessid, sessname)

script_dir         = Path(__file__).resolve().parent
log_file           = "com/datas/conversation_log_" + sessname + "_.txt"
def_audio_dir      = "com/datas/ai/audio/"
def_audio_lrequest = def_audio_dir + "last_request.mp3"
def_audio_flag     = def_audio_dir + "readmp3.flag"
sftp_global_connector = None

# ─────────────────────────────────────────────────────────────────
#  Audio helpers
# ─────────────────────────────────────────────────────────────────
def apf():
    try: audioparser.flags([def_audio_flag])
    except Exception as e: print("apf ERR:", e)

def apr():
    try: audioparser.flags_r([def_audio_flag])
    except Exception as e: print("apr ERR:", e)

def apa(text):
    """
    TTS wrapper. Guarda primero en disco (def_audio_lrequest) y lanza
    ffplay en background para no bloquear el hilo principal.
    Evita llamar a gTTS con texto vacío (crashea silenciosamente).
    """
    try:
        # pt_audio puede dejar el texto vacío si solo había emojis/código
        clean = pt_audio(text).strip()
        if not clean:
            print("apa: texto vacío tras limpieza, sin audio.")
            return
        audioparser.text_to_speech(clean, "es", def_audio_lrequest)
    except Exception as e:
        print("apa ERR:", e)

def pt_audio(text):
    """
    Limpia texto para gTTS:
    - Elimina bloques de código completos (```...```)
    - Elimina emojis y símbolos que gTTS no puede pronunciar
    - Conserva letras, números, puntuación básica y espacios
    """
    # Eliminar bloques de código
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Eliminar URLs
    text = re.sub(r"https?://\S+", "", text)
    # Eliminar emojis y símbolos Unicode especiales
    text = re.sub(
        r"[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F]+",
        " ", text
    )
    # Eliminar chars problemáticos para TTS pero conservar puntuación normal
    text = re.sub(r"[*#`\[\]\{\}<>|\\^~]", " ", text)
    # Colapsar espacios múltiples
    text = re.sub(r" {2,}", " ", text)
    return text.strip()

def HeloEnterVoide():
    apf()
    try: audioparser.text_to_speech("hola has entrado en osiris", "es", def_audio_lrequest)
    except Exception: pass
    apf()

def while_args(argS):
    try:
        for a in argS:
            main([a])
            time.sleep(1)
    except Exception as e:
        print("while_args ERR:", e)

try:   print("CRO Info:", croparser.INFO)
except Exception: pass

try:   core.log_event("mistral2.py", "Inicio", "No hay mas detalles", error="None")
except Exception: pass

# ─────────────────────────────────────────────────────────────────
#  API KEY  (cifrado Fernet)
# ─────────────────────────────────────────────────────────────────
ruta_archivo_key = "com/datas/mistral_key.enc"
clave_cifrado    = b'N9t9dYNn2fjc8CRT0_eChnH5xDETGSvMOM5qxqyvSUs='

def obtener_key_mistral(nkey=""):
    global clave_cifrado, ruta_archivo_key
    if nkey == "resetkey":
        if os.path.isfile(ruta_archivo_key):
            os.remove(ruta_archivo_key)
            print("Clave eliminada.")
    while True:
        if os.path.isfile(ruta_archivo_key):
            try:
                with open(ruta_archivo_key, "rb") as f:
                    key_cifrada = f.read()
                key_descifrada = Fernet(clave_cifrado).decrypt(key_cifrada).decode()
                print("Key Mistral encontrada y descifrada.")
                return key_descifrada
            except Exception as e:
                print(f"Error descifrando: {e} — se pedirá nueva clave.")
        webbrowser.open_new_tab("https://console.mistral.ai/api-keys/")
        key = input("Pega tu key de Mistral (o '--reset' para borrar): ")
        if key == "--reset":
            if os.path.isfile(ruta_archivo_key):
                os.remove(ruta_archivo_key)
                print("Clave eliminada.")
                if nkey == "new":
                    return obtener_key_mistral()
            else:
                print("No hay clave.")
            continue
        key_cifrada = Fernet(clave_cifrado).encrypt(key.encode())
        with open(ruta_archivo_key, "wb") as f:
            f.write(key_cifrada)
        print("Key cifrada y guardada.")
        try: pyperclip.copy(key)
        except Exception: pass
        return key

# ─────────────────────────────────────────────────────────────────
#  Variables globales
# ─────────────────────────────────────────────────────────────────
current_path  = os.path.abspath(__file__)
version_file  = os.path.splitext(os.path.basename(current_path))[0]

auto_response_window  = False
auto_cromode          = False
auto_ap               = False
cro_loaded            = False
LIMIT_WHILE_ARGS      = 10
MODE_CRO_GLOBAL_ACTIVE = False
context_mode          = "fast"

conversation_context = f"""
#Interfaz de comunicación con Mistral AI
#Interfaz Name: Osiris
#Version: {version_file}
#Idioma: Español
Instrucciones: ¡Bienvenido a Osiris (Mistral)! Usa emojis para dinamizar la conversación.
Escribe --help para ver comandos disponibles.
"""

conversation_messages = []   # historial simple (fallback si mctx no está)

# ─────────────────────────────────────────────────────────────────
#  Modelos disponibles
# ─────────────────────────────────────────────────────────────────
mistral_models = [
    "mistral-small-latest",    # 0 - Rápido y eficiente
    "mistral-medium-latest",   # 1 - Equilibrado
    "mistral-large-latest",    # 2 - Más potente
    "open-mistral-7b",         # 3 - Open source 7B
    "open-mixtral-8x7b",       # 4 - MoE 8x7B
    "open-mixtral-8x22b",      # 5 - MoE 8x22B
    "codestral-latest",        # 6 - Especializado en código
    "mistral-embed",           # 7 - Embeddings
]

# ─────────────────────────────────────────────────────────────────
#  Inicialización API
# ─────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("MISTRAL_API_KEY", "")
mistral_model = mistral_models[0]
client       = None

if not API_KEY:
    try:
        API_KEY = obtener_key_mistral()
    except Exception as e:
        print("ERROR API KEY:", e)

if API_KEY:
    try:
        client = Mistral(api_key=API_KEY)
        print(f"Cliente Mistral inicializado. Modelo por defecto: {mistral_model}")
    except Exception as e:
        print("ERROR inicializando cliente Mistral:", e)

# ─────────────────────────────────────────────────────────────────
#  Selección de modelo
# ─────────────────────────────────────────────────────────────────
def select_model():
    global mistral_models, mistral_model, conversation_context, client
    menu = " Seleccione un modelo Mistral a usar:\n"
    for i, x in enumerate(mistral_models):
        menu += f"\n ({i+1}) {x}"
    sel = f"\n{menu}\n\n Seleccione Uno: >>> "
    conversation_context += sel
    inp = input(sel)
    try:
        idx = int(inp.strip()) - 1
        if 0 <= idx < len(mistral_models):
            mistral_model = mistral_models[idx]
            print(f"\n Cambiando a modelo: {mistral_model}\n")
            conversation_context += inp + f"\nCambiando a modelo: {mistral_model}\n"
        else:
            print("Índice fuera de rango, usando:", mistral_model)
    except Exception:
        print("Selección inválida, usando modelo por defecto:", mistral_model)

try:
    select_model()
    print("Select Model OK")
except Exception as e:
    print("ERROR Select Model:", e)

# ─────────────────────────────────────────────────────────────────
#  Init gestor de contexto  (después de select_model)
# ─────────────────────────────────────────────────────────────────
def _init_context_manager():
    """Inicializa MCX_MANAGER una vez que client y mistral_model están listos."""
    global MCX_MANAGER, mctx
    if mctx is None or client is None:
        return
    try:
        MCX_MANAGER = mctx.MistralContextManager(
            mistral_client = client,
            mistral_model  = mistral_model,
            token_limit    = 32_000,
            verbose        = True
        )
        # Fragmento de sistema esencial — siempre anclado
        MCX_MANAGER.add_system(
            f"Sistema OSIRIS v{version_file} · Mistral AI · Sesión: {sessname}\n"
            f"Idioma: Español. Usa emojis. Escribe --help para ver comandos.",
            essential=True
        )
        print(f"[CTX] MistralContextManager listo. Límite: 32 000 tokens.")
    except Exception as e:
        print(f"[CTX] Error iniciando MCX_MANAGER: {e}")
        MCX_MANAGER = None

_init_context_manager()

# ─────────────────────────────────────────────────────────────────
#  Variables auxiliares
# ─────────────────────────────────────────────────────────────────
load             = ""
last_response    = ""
topic            = ""
autosave_enabled = True
def_image_editor = "mtpaint"
srt_c            = srt_c_import if srt_c_import else {}

fecha_hora = ""

def fecha_hora_g():
    global fecha_hora
    fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
    return fecha_hora

fecha_hora = fecha_hora_g()

# ─────────────────────────────────────────────────────────────────
#  Utilidades de archivo
# ─────────────────────────────────────────────────────────────────
def is_file(filepath):
    return os.path.isfile(filepath)

def read_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")
        return None

def save_file(filepath, content):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(filepath, 0o755)
        print(f"Guardado: {filepath}")
    except Exception as e:
        print(f"Error guardando {filepath}: {e}")

def decode_img(base64_data):
    image = Image.open(io.BytesIO(base64_data))
    image.show()
    image.save("com/datas/ffmpeg/my_image.png")

# ─────────────────────────────────────────────────────────────────
#  show_text_window
# ─────────────────────────────────────────────────────────────────
def show_text_window(text):
    try:
        rtext = acero.main(text)
        print("Win Cuarzo (acero):", rtext)
        if rtext:
            main(rtext)
    except Exception:
        try:
            win.show_text_window(text)
        except Exception as e:
            print("show_text_window ERR:", e)

# ─────────────────────────────────────────────────────────────────
#  CRO helpers
# ─────────────────────────────────────────────────────────────────
def croreturn(CROreturn_dict):
    """Procesa el dict de retorno CRO y lo registra en el gestor de contexto."""
    CROreturn_text = ""
    is_error = False
    for key, value in CROreturn_dict.items():
        if key.startswith("output_"):
            parts = key.split("_")
            header = f"\n--- Salida Sistema ({parts[1] if len(parts)>1 else ''} {parts[2] if len(parts)>2 else ''}) ---"
            print(header)
            print(value)
            CROreturn_text += header + "\n" + str(value)
        elif key.startswith("error_output_"):
            parts = key.split("_")
            header = f"\n--- Error Sistema ({parts[2] if len(parts)>2 else ''} {parts[3] if len(parts)>3 else ''}) ---"
            print(header)
            print(f"Stdout: {value.get('stdout','')}")
            print(f"Stderr: {value.get('stderr','')}")
            print(f"Return Code: {value.get('returncode','')}")
            CROreturn_text += (header + f"\nStdout: {value.get('stdout','')}"
                               f"\nStderr: {value.get('stderr','')}"
                               f"\nReturn Code: {value.get('returncode','')}")
            is_error = True
        # BUG FIX: eliminado el 'break' original — procesaba solo la primera
        # clave del dict ignorando el resto de acciones CRO de la respuesta.

    # ── Registrar en el gestor de contexto ──────────────────────
    if MCX_MANAGER:
        if is_error:
            MCX_MANAGER.add_cro_error(CROreturn_text)
        else:
            relevant = len(CROreturn_text.strip()) > 20
            MCX_MANAGER.add_cro_output(CROreturn_text, relevant=relevant)

    return CROreturn_text


def arw():
    if auto_response_window:
        main(["--sla"])
    else:
        print()

def aap_check():
    if auto_ap:
        main(["--ap"])
    else:
        print()

# ─────────────────────────────────────────────────────────────────
#  generate_response  ← INTEGRACIÓN PRINCIPAL CON mctx
# ─────────────────────────────────────────────────────────────────
def generate_response(user_input, mode=""):
    """
    Genera una respuesta Mistral.
    Si MCX_MANAGER está disponible usa el gestor de contexto inteligente
    (con compresión automática, anclaje CRO, etc.).
    Si no, usa conversation_messages como fallback.
    """
    global conversation_context, last_response, conversation_messages
    global client, mistral_model, context_mode, MCX_MANAGER

    # ── Mantener string legacy (para --sw, --sc, --exp...) ──────
    conversation_context += "\nUser: " + user_input + "\n"

    # ── Construir mensajes ───────────────────────────────────────
    if MCX_MANAGER:
        MCX_MANAGER.add_user(user_input)
        messages = MCX_MANAGER.build_messages(
            system_prompt=(
                "Eres Osiris, asistente AI en español. "
                "Usa emojis para dinamizar. "
                "Si CROmode está activo usa bloques ```CRO para acciones del sistema."
            )
        )
    else:
        # fallback: historial simple
        conversation_messages.append({"role": "user", "content": user_input})
        messages = conversation_messages

    try:
        response      = client.chat.complete(model=mistral_model, messages=messages)
        response_text = response.choices[0].message.content

        # ── Detectar CRO ─────────────────────────────────────────
        has_cro = bool(re.search(r"```CRO", response_text))

        # ── Registrar respuesta ──────────────────────────────────
        if MCX_MANAGER:
            MCX_MANAGER.add_ai(response_text, has_cro=has_cro)
        else:
            conversation_messages.append({"role": "assistant", "content": response_text})

        if context_mode == "fast":
            conversation_context += response_text + "\n"

        if mode != "nolastresponse":
            last_response = response_text
            return response_text
        else:
            return "EXIT_LR"

    except Exception as e:
        print(f"Error generando contenido: {e}")
        return None

# ─────────────────────────────────────────────────────────────────
#  Funciones de guardado y búsqueda
# ─────────────────────────────────────────────────────────────────
def save_request(user_input):
    save_file("com/datas/lastrequest.mistral", user_input)

def save_answer(save=""):
    global last_response
    if save == "":
        save = "com/datas/lastanswer.mistral"
    save_file(save, last_response)

def save_context():
    save_file("com/datas/context.mistral", conversation_context)

def autosave():
    if autosave_enabled:
        save_answer()
        save_context()

def generate_new_questions(base_question):
    return [
        f"¿Podrías profundizar más sobre {base_question}?",
        f"¿Cuál es un ejemplo de {base_question}?",
        f"¿Cómo se relaciona {base_question} con otras ideas?",
        f"¿Qué otros aspectos de {base_question} podríamos explorar?",
        f"¿Cuáles son las implicaciones de {base_question}?"
    ]

def search_context(term, load_ctx=False):
    global load, conversation_context
    results = [l for l in conversation_context.splitlines() if term in l]
    if results:
        print("Resultados:")
        for l in results: print(" -", l)
        if load_ctx:
            load = "\n".join(results)
            print("Contexto cargado.")
    else:
        print("No se encontraron coincidencias.")
    return results

def load_config(config_file):
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        print("Configuración cargada.")
        return config
    except Exception as e:
        print(f"Error cargando config: {e}")
        return {}

def log_interaction(user_input, response_text):
    global log_file
    try:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"{datetime.now()} - User: {user_input}\n {response_text}\n\n")
    except Exception as e:
        print(f"Error log: {e}")

def set_model_params(params):
    try:
        model_params = {"temperature": 0.9}
        for param in params:
            k, v = param.split("=")
            model_params[k] = float(v) if "." in v else int(v)
        print("Parámetros configurados:", model_params)
    except Exception as e:
        print(f"Error configurando params: {e}")

def toggle_autosave(enable=True):
    global autosave_enabled
    autosave_enabled = enable
    print("Autosave", "activado." if enable else "desactivado.")

# ─────────────────────────────────────────────────────────────────
#  VIDEO TRANSLATE
# ─────────────────────────────────────────────────────────────────
def _extraer_audio_ffmpeg(video_path, audio_out):
    for ffmpeg_bin in ["/usr/local/ffmpeg/bin/ffmpeg", "ffmpeg"]:
        cmd = [ffmpeg_bin, "-y", "-loglevel", "error", "-i", video_path,
               "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return True, ""
    return False, r.stderr

def _transcribir_con_mistral(audio_path):
    """
    Transcribe audio via Mistral API (Voxtral).
    SDK >= julio 2025: el método es .complete() no .create()
    Modelo: voxtral-mini-latest (antes whisper-large-v3, ya no existe en la API pública)
    """
    global client
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        # ── CORRECCIÓN: .complete() en lugar de .create() ──────────
        # El SDK de mistralai cambió el método al lanzar Voxtral (jul-2025).
        # Referencia: https://docs.mistral.ai/capabilities/audio_transcription
        response = client.audio.transcriptions.complete(
            model="voxtral-mini-latest",
            file={
                "content": audio_bytes,
                "file_name": os.path.basename(audio_path),
            },
            language="es"
        )
        return response.text, True
    except Exception as e:
        print(f"Transcripción Mistral API error: {e} — intentando Whisper local…")
        return _transcribir_whisper_local(audio_path)

def _transcribir_whisper_local(audio_path):
    try:
        r = subprocess.run(
            ["whisper", audio_path, "--language", "es",
             "--output_format", "txt", "--output_dir", "/tmp"],
            capture_output=True, text=True
        )
        txt_tmp = os.path.join("/tmp", os.path.splitext(os.path.basename(audio_path))[0] + ".txt")
        if os.path.isfile(txt_tmp):
            with open(txt_tmp, "r", encoding="utf-8") as f:
                return f.read(), True
        return "[Whisper no pudo generar transcripción]", False
    except FileNotFoundError:
        return "[Whisper no instalado. pip install openai-whisper]", False

def _generar_srt_con_mistral(transcripcion, prompt_extra, srt_config):
    prompt = f"""
Eres un subtitulador profesional. Genera un archivo .srt con subtítulos.

TRANSCRIPCIÓN DEL AUDIO:
{transcripcion}

INSTRUCCIONES:
- Traduce y subtitula al español (salvo indicación contraria).
- Genera UN SOLO archivo SRT en formato estricto .srt.
- Usa etiquetas HTML: <font size="18-22" color="#hex" face="Noto Sans">texto</font>
- Usa <b>texto</b> para palabras clave.
- Incluye emojis descriptivos con tamaño y color variable.
- Duración máxima por subtítulo: 5 s (preferir 2-2.5 s).
- Colores claros y brillantes (fondo oscuro).

{srt_config}
{prompt_extra}

Devuelve ÚNICAMENTE el bloque srt:
```srt
(contenido aquí)
```
SÓLO UN bloque srt.
"""
    return generate_response(prompt)

def video_translate(video_file_name="", prompt="", args=None):
    global last_response, conversation_context, srt_c, script_dir, MCX_MANAGER

    mprompt = ""
    if args:
        for arg in args:
            print(f"  @@@@Detected: {arg}")
            xarg = arg[1:]
            if xarg in srt_c:
                mprompt += srt_c[xarg]
        print("End Args")
    else:
        print("No Args")

    if mprompt:
        prompt = mprompt + prompt

    input_video_info = ""

    # ── 1. Descargar / localizar vídeo ────────────────────────────
    if video_file_name.startswith(("http://", "https://")):
        print("Descargando vídeo temporal…")
        os.makedirs("com/tmp", exist_ok=True)
        code_video_file = "com/tmp/" + hashlib.md5(video_file_name.encode()).hexdigest() + ".mp4"
        subprocess.run(["yt-dlp", "-o", code_video_file, video_file_name],
                       capture_output=True, text=True)
        input_video_info = f"Descargado desde: {video_file_name}\nGuardado en: {code_video_file}\n"
        video_file_name = code_video_file
    else:
        code_video_file = video_file_name
        input_video_info = f"VIDEO PATH LOCAL: {video_file_name}\n"

    # ── 2. Extraer audio ─────────────────────────────────────────
    audio_path = code_video_file + ".audio.wav"
    print("Extrayendo audio con ffmpeg…")
    ok, err = _extraer_audio_ffmpeg(video_file_name, audio_path)
    if not ok:
        msg = f"[ERROR extrayendo audio: {err}]"
        print(msg)
        conversation_context += msg + "\n"
        if MCX_MANAGER:
            MCX_MANAGER.add_cro_error(msg)
        return

    try:
        Datos_video = win.obtener_datos_multimedia(code_video_file)
        print("DATOS VIDEO:\n", Datos_video)
        input_video_info += f"Datos multimedia: {Datos_video}\n"
    except Exception: pass

    # ── 3. Transcribir audio ──────────────────────────────────────
    print("Transcribiendo audio con Mistral API…")
    transcripcion, trans_ok = _transcribir_con_mistral(audio_path)
    if not trans_ok:
        print("⚠️  Transcripción con warnings. Continuando…")
    print(f"Transcripción ({len(transcripcion)} chars):\n{transcripcion[:500]}…\n")
    input_video_info += f"Transcripción:\n{transcripcion}\n"
    conversation_context += input_video_info
    if MCX_MANAGER:
        MCX_MANAGER.add_cro_output(f"[VIDEO] {input_video_info}", relevant=True)

    # ── 4. Generar SRT ────────────────────────────────────────────
    srt_config = srt_c.get("def", "")
    print("\nGenerando SRT con Mistral…\n")
    response_text = _generar_srt_con_mistral(transcripcion, prompt, srt_config)
    if not response_text:
        print("No se obtuvo respuesta para el SRT.")
        return
    print(response_text)

    matches = re.findall(r"```srt\n(.*?)\n```", response_text, re.DOTALL)
    if len(matches) != 1:
        print("No se generó el SRT correctamente.")
        conversation_context += response_text
        return

    # ── 5. Guardar SRT y recomponer vídeo ─────────────────────────
    subtitulado_out = code_video_file + ".subtitulado.mp4"
    vtranslate      = subtitulado_out + ".translate.srt"
    input_video_info += f"SRT: {vtranslate}\nContenido:\n{matches[0]}\n"
    with open(vtranslate, "w", encoding="utf-8") as f:
        f.write(matches[0])

    force_style = "BackColour=&H90000000,BorderStyle=4,FontName=NotoColorEmoji,Alignament=6"
    for ffmpeg_bin in ["/usr/local/ffmpeg/bin/ffmpeg", "ffmpeg"]:
        comando_ffmpeg = [
            ffmpeg_bin, "-y", "-loglevel", "error", "-i", video_file_name,
            "-af", "aresample=async=1,loudnorm=I=-16:TP=-1.5:LRA=11",
            "-vf", f"scale=-2:720,subtitles={vtranslate}:force_style='{force_style}'",
            "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            "-c:v", "libx264", "-c:a", "aac", "-crf", "21",
            subtitulado_out
        ]
        print("\n#################################################")
        print("→ Procesando vídeo…  Espere…")
        print("#################################################\n")
        resultado = subprocess.run(comando_ffmpeg, capture_output=True, text=True)
        if resultado.returncode == 0:
            break

    if resultado.returncode != 0:
        e1 = f"Error ffmpeg: {resultado.returncode}\n{resultado.stderr}"
        print(e1)
        conversation_context += e1
        if MCX_MANAGER:
            MCX_MANAGER.add_cro_error(e1)
        return False

    print(f"ffmpeg OK. Código: {resultado.returncode}")
    conversation_context += "ffmpeg ejecutado correctamente.\n"

    # ── 6. Abrir vídeo ────────────────────────────────────────────
    obj = {"mode": "bg", "name": None,
           "com": ["dsk/dskv", "--video", str(script_dir) + "/../" + subtitulado_out]}
    osiris2.multiprocess(obj)

    # ── 7. Informe final ──────────────────────────────────────────
    print("\nRealizando Inferencia final (revisión informativa)…")
    send_text = (
        f"\nEres Mistral-text. Se procesó un vídeo con prompt:\n{prompt}\n"
        f"Tareas realizadas:\n{input_video_info}\n"
        f"Comando ffmpeg: {' '.join(comando_ffmpeg)}\n"
        f"Realiza una revisión informativa.\n"
    )
    response_return = generate_response(send_text)
    print("\n\n", response_return)
    last_response = " ".join(comando_ffmpeg)

# ─────────────────────────────────────────────────────────────────
#  Screenshot
# ─────────────────────────────────────────────────────────────────
def screen_shot():
    process = subprocess.run(["python3", "com/screenshot.py"], capture_output=True, text=True)
    output  = process.stdout.strip().splitlines()
    print(output)
    if len(output) < 3:
        show_text_window(f"FALLO: {process},{output}")
        return
    coord_line = output[0]
    img_line   = output[1]
    txt_lines  = output[2:]
    if not coord_line.startswith("Coordinates:") or not img_line.startswith("ImagePath:"):
        show_text_window(f"FALLO formato: {process},{output}")
        return
    image_path_value = img_line.split(":", 1)[1].strip()
    text_started = False
    text_output  = []
    for line in txt_lines:
        if line.startswith("Text:"):
            text_output.append(line.split(":", 1)[1].strip() if not text_started else line.strip())
            text_started = True
        elif text_started:
            text_output.append(line.strip())
    if text_output:
        print("Text:", " ".join(text_output))
    generate_with_image(image_path_value, "\n".join(text_output))

# ─────────────────────────────────────────────────────────────────
#  Imagen con Mistral Vision
# ─────────────────────────────────────────────────────────────────
def generate_with_image(image_path, ask):
    global last_response, client, mistral_model
    try:
        image = win.load_image(image_path)
    except Exception:
        image = None
    if not image and not image_path.startswith(("http://", "https://")):
        print("No se pudo cargar la imagen.")
        return None
    try:
        if image_path.startswith(("http://", "https://")):
            image_content = {"type": "image_url", "image_url": image_path}
        else:
            with open(image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode("utf-8")
            ext      = os.path.splitext(image_path)[1].lower()
            mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                        ".png": "image/png",  ".gif": "image/gif", ".webp": "image/webp"}
            mime_type     = mime_map.get(ext, "image/jpeg")
            image_content = {"type": "image_url",
                             "image_url": f"data:{mime_type};base64,{img_data}"}

        # Para imágenes usamos llamada directa (no pasa por el gestor de contexto)
        messages = [{"role": "user", "content": [
            {"type": "text", "text": ask + "\nResponde en Español."},
            image_content
        ]}]
        response       = client.chat.complete(model=mistral_model, messages=messages)
        generated_text = response.choices[0].message.content
        last_response  = generated_text
        print("\nResponse Image.\n\n" + generated_text)
        show_text_window(generated_text)
        xresponse = f"Envié imagen {image_path} a Mistral, pregunta:\n{ask}\nInterpretó:\n"
        main(f"{xresponse} {generated_text}")
    except Exception as e:
        print("Error consulta imagen:", e)
        return None
    return None

# ─────────────────────────────────────────────────────────────────
#  --info mejorado  (incluye estado del gestor de contexto)
# ─────────────────────────────────────────────────────────────────
def print_info():
    sep = "═" * 65
    print(f"""
{sep}
  OSIRIS · Interfaz Mistral AI  ·  {version_file}
{sep}
  Modelo activo   : {mistral_model}
  API Key         : {'✅ Cargada' if API_KEY else '❌ No disponible'}
  Session ID      : {sessid}
  CROmode         : {'ON  🟢' if auto_cromode else 'OFF 🔴'}
  AudioParser     : {'ON  🟢' if auto_ap else 'OFF 🔴'}
  AutoRespWindow  : {'ON  🟢' if auto_response_window else 'OFF 🔴'}
  Context Mode    : {context_mode}
  Autosave        : {'ON  🟢' if autosave_enabled else 'OFF 🔴'}
  Log File        : {log_file}
  Fecha/Hora      : {fecha_hora_g()}
{sep}""")

    # ── Estado gestor de contexto ────────────────────────────────
    if MCX_MANAGER:
        MCX_MANAGER.print_status()
    else:
        print(f"  [CTX] Gestor de contexto: ⚠️  no disponible (historial simple)\n")

    print(f"{sep}\n  MODELOS DISPONIBLES:\n")
    for i, m in enumerate(mistral_models):
        marca = " ◀ activo" if m == mistral_model else ""
        print(f"    ({i+1}) {m}{marca}")

    print(f"""
{sep}
  COMANDOS DE MENÚ  (Glyphs Osiris-Mistral)
{sep}
  ── CONVERSACIÓN ──────────────────────────────────────────────
  <texto>                Enviar mensaje al modelo
  --sd  <texto>          Enviar texto directamente
  --dialog / --ask       Ventana de diálogo para prompt
  --nq  <pregunta>       Generar preguntas relacionadas
  --r  / --reset         Resetear todo el estado
  --cc / --clearcontext  Limpiar contexto de conversación

  ── CONTEXTO INTELIGENTE ──────────────────────────────────────
  --ctx                  Ver estado del gestor de contexto
  --ctx-list             Listar todos los fragmentos activos
  --ctx-compress         Forzar compresión manual
  --ctx-export [path]    Exportar contexto a JSON
  --ctx-import <path>    Importar contexto desde JSON
  --ctx-reset            Resetear gestor (conserva esenciales)
  --ctm                  Conmutar modo string (fast/off)

  ── CARGA / CONTEXTO ARCHIVO ──────────────────────────────────
  --l   <archivo>        Cargar archivo en buffer load
  --al  <texto>          Añadir load + texto y enviar
  --sl                   Mostrar buffer load
  --la  / --loadanswer   Cargar última respuesta en buffer
  --loc <archivo>        Cargar contexto Osiris (LOC)
  --arc                  Añadir última respuesta al contexto
  --s   <término>        Buscar en el contexto
  --lsel <archivo>       Cargar contexto seleccionado
  --lm  <arc1> <arc2>    Cargar múltiples archivos
  --lc  <json>           Cargar config desde JSON
  --st  <tema>           Establecer tema de conversación

  ── ARCHIVOS ──────────────────────────────────────────────────
  --sa  [archivo]        Guardar última respuesta
  --sc                   Guardar contexto string completo
  --sav [nombre]         Guardar sesión
  --sr  <texto>          Guardar solicitud
  --as  / --autosave     Ejecutar autosave
  --ta  on|off           Activar/desactivar autosave
  --ls  [dir]            Listar archivos en com/datas/
  --exp <nombre>         Exportar contexto (win)
  --imp <nombre>         Importar contexto (win)

  ── IMAGEN & PANTALLA ─────────────────────────────────────────
  --li  <imagen|URL>     Cargar imagen → Mistral Vision
  --li  --fd             Seleccionar imagen con File Dialog
  --ss  / --screenshot   Capturar pantalla y analizar
  --sw  / --showwin      Mostrar contexto en ventana
  --sla / --showlastanswer  Última respuesta en ventana
  --di  <base64>         Decodificar imagen base64

  ── VÍDEO ─────────────────────────────────────────────────────
  --tvl <url|path> [prompt]  Pipeline completo:
       1) Descarga (yt-dlp si URL)
       2) Extrae audio (ffmpeg)
       3) Transcribe (Mistral API / Whisper local)
       4) Genera SRT (Mistral)
       5) Recompone vídeo (ffmpeg)
       6) Abre resultado
  --tvl <url> --dialog   Prompt extra via diálogo

  ── AUDIO ─────────────────────────────────────────────────────
  --ap  / --audio-parser        TTS última respuesta
  --apr / --audio-parser-repeat Repetir último audio
  --aap / --auto-audio-parser   Toggle TTS automático
  --asla <nombre>               Guardar último audio

  ── MODOS ─────────────────────────────────────────────────────
  --cm  / --cromode             Activar/desactivar CROmode
  --cmc / --cromode-commute     Conmutar CROmode sin recargar
  --arw / --auto_response_window  Toggle ventana auto-respuesta

  ── MODELO ────────────────────────────────────────────────────
  --nmodel                      Seleccionar modelo de la lista
  --lms / --listmodels          Listar modelos disponibles
  --sp  param=valor             Configurar parámetros
  --resetkey                    Borrar y pedir nueva API key

  ── SISTEMA ───────────────────────────────────────────────────
  --diagnostic server|system|memory   Diagnóstico
  --sshc [cmd]                  Conexión SSH/SFTP
  --log  <texto>                Registrar en log
  --i / --info / --help         Esta pantalla
{sep}
  VARIABLES @ (para --tvl):
""")
    for k, v in srt_c.items():
        snippet = v.strip().replace("\n", " ")[:60]
        print(f"    @{k:<12} → {snippet}…")
    print(f"{sep}\n")

# ─────────────────────────────────────────────────────────────────
#  MAIN  ─  gestor de comandos
# ─────────────────────────────────────────────────────────────────
def main(args):
    global mistral_model, client, conversation_context, conversation_messages
    global load, last_response, topic, API_KEY
    global auto_cromode, cro_loaded, auto_response_window, auto_ap
    global def_audio_dir, def_audio_lrequest, def_audio_flag
    global LIMIT_WHILE_ARGS, commands_map, context_mode, MODE_CRO_GLOBAL_ACTIVE
    global autosave_enabled, sftp_global_connector, MCX_MANAGER

    MODE_CRO_GLOBAL_ACTIVE = False

    if isinstance(args, str):
        args = args.split()
    if not args:
        return

    # ── Texto libre (no comando) ───────────────────────────────────
    if not args[0].startswith("--") and not MODE_CRO_GLOBAL_ACTIVE:
        user_input    = " ".join(args)
        response_text = generate_response(user_input)
        print(" \n→", response_text)

        if auto_cromode and response_text:
            apa(response_text)
            CROreturn = croparser.main(response_text)
            print(" *^* \n **CROParser ON** ")
            if not CROreturn:
                print("NOT CRO RESULTS")
            else:
                print("CRO:auto — Entrando en Consola CRO")
                CRT = croreturn(CROreturn)
                conversation_context += CRT
                while True:
                    r_input = input("""
    WCRo StarT - [Exit wCRO writting --exit]
    Ai2Cro>> """)
                    if r_input == "--exit":
                        print("\n  Exiting WCroParser\n")
                        _exit_msg = "[SISTEMA] Operador cerro la consola CRO. CROmode sigue activo."
                        conversation_context += "\n" + _exit_msg + "\n"
                        if MCX_MANAGER:
                            MCX_MANAGER.add_cro_output(_exit_msg, relevant=False)
                        generate_response(_exit_msg, "nolastresponse")
                        break
                    if r_input.startswith("--"):
                        # BUG FIX 5: pasar flag para que main() anidado NO resetee
                        # MODE_CRO_GLOBAL_ACTIVE — usamos variable temporal
                        _prev_cro_state = auto_cromode
                        main(r_input.strip().split())
                        # restaurar: main() resetea MODE_CRO_GLOBAL_ACTIVE a False
                        # pero auto_cromode (la flag real) no se toca
                        continue
                    response_d = generate_response(r_input)
                    apa(response_d)
                    whileCROreturn = croparser.main(response_d)
                    print("-----> WR:", whileCROreturn)
                    # BUG FIX 3: registrar resultado CRO de cada iteracion
                    # en MCX_MANAGER para que el modelo lo vea en el turno siguiente.
                    # Antes solo iba a conversation_context (string legacy ignorado
                    # cuando MCX_MANAGER esta activo).
                    if whileCROreturn:
                        _wt = str(whileCROreturn)
                        conversation_context += _wt
                        if MCX_MANAGER:
                            _wcro_is_error = any(
                                k.startswith("error_output_")
                                for k in whileCROreturn
                            )
                            if _wcro_is_error:
                                MCX_MANAGER.add_cro_error(_wt)
                            else:
                                MCX_MANAGER.add_cro_output(_wt, relevant=True)
                    else:
                        conversation_context += str(whileCROreturn)

        log_interaction(user_input, response_text or "")
        return

    # ─────────────────────────────────────────────────────────────
    try:
        command = args[0]

        # ── Audio ────────────────────────────────────────────────
        if command in ("--apr", "--audio-parser-repeat"):
            apr(); return
        if command in ("--ap", "--audio-parser"):
            print(last_response)
            audioparser.text_to_speech(last_response, "es", def_audio_lrequest)
            apf(); return
        if command in ("--asla", "--audio-save-last-answer"):
            if len(args) > 1:
                subprocess.run(["cp", def_audio_lrequest, def_audio_dir + args[1]])
            else:
                print("--asla ERROR:", args)
            return
        if command in ("--aap", "--auto-audio-parser"):
            auto_ap = not auto_ap
            msg = ("AUTO_AUDIO_PARSER ON: usa texto plano 100%."
                   if auto_ap else "AUTO_AUDIO_PARSER OFF: salida estándar.")
            conversation_context += "\n" + msg + "\n"
            if MCX_MANAGER:
                MCX_MANAGER.add_system(msg, essential=False)
            print("AUTO_AUDIO:", auto_ap); return

        # ── Modos ────────────────────────────────────────────────
        if command in ("--ctm", "--context-mode"):
            context_mode = False if context_mode == "fast" else "fast"
            msg = f"Context Mode → {context_mode}"
            conversation_context += "\n" + msg + "\n"
            print("CONTEXT_MODE:", context_mode); return

        if command in ("--cmc", "--cromode-commute"):
            auto_cromode = not auto_cromode
            print("AUTO CRO MODE:", auto_cromode)
            conversation_context += f"\nAUTOCROMODE → {auto_cromode}\n"; return

        if command in ("--cm", "--cromode"):
            if not auto_cromode:
                auto_cromode = True
                main(["--l", "develop.info"])
                cro_loaded = True
                cro_inst = (
                    "CROMode ACTIVADO. Genera bloques ```CRO para acciones del sistema. "
                    "Siempre confirma antes de WRITE_FILE. "
                    "Usa LOG_OSIRIS INFO para reportar estado."
                )
                conversation_context += "\nAUTOCROMODE ACTIVADO\n"
                # ── Anclar instrucción CRO en el gestor ──────────
                if MCX_MANAGER:
                    MCX_MANAGER.add_cro_instruction(cro_inst)
                main(["--al",
                      "Se cargó y activó --cromode. CROMODE activo a partir de tu "
                      "próxima respuesta. Avisa estado en pocas líneas."])
            else:
                auto_cromode = False
                conversation_context += "\nAUTOCROMODE OFF\n"
            print("AUTO_cromode:", auto_cromode); return

        if command in ("--arw", "--auto_response_window"):
            auto_response_window = not auto_response_window
            conversation_context += f"\nAUTO_RESPONSE_WINDOW → {auto_response_window}\n"
            print("AUTO_RESPONSE_WINDOW:", auto_response_window); return

        # ── Gestor de contexto (comandos --ctx) ──────────────────
        if command == "--ctx" or command == "--context-status":
            if MCX_MANAGER:
                MCX_MANAGER.print_status()
                MCX_MANAGER.list_fragments()
            else:
                print("Gestor de contexto no disponible.")
            return

        if command == "--ctx-list":
            if MCX_MANAGER:
                MCX_MANAGER.list_fragments(show_obsolete=True)
            return

        if command == "--ctx-compress":
            if MCX_MANAGER:
                print("Comprimiendo contexto manualmente…")
                MCX_MANAGER.compress_context()
            else:
                print("Gestor no disponible.")
            return

        if command == "--ctx-export":
            path = args[1] if len(args) > 1 else "com/datas/context_export.json"
            if MCX_MANAGER:
                MCX_MANAGER.export_json(path)
            return

        if command == "--ctx-import":
            if len(args) > 1 and MCX_MANAGER:
                MCX_MANAGER.import_json(args[1])
            return

        if command == "--ctx-reset":
            if MCX_MANAGER:
                keep = input("  ¿Conservar fragmentos esenciales/CRO? (s/n): ").lower()
                MCX_MANAGER.reset(keep_essential=(keep == "s"))
                conversation_messages.clear()
                conversation_context = ""
                print("Gestor de contexto reseteado.")
            return

        # ── Reset key ────────────────────────────────────────────
        if command == "--resetkey":
            API_KEY = obtener_key_mistral("resetkey")
            client  = Mistral(api_key=API_KEY)
            _init_context_manager()
            return

        # ── Modelo ───────────────────────────────────────────────
        if command == "--nmodel":
            conversation_context += "\nSelección de modelos\n"
            select_model()
            ns = "\n NEW MODEL SELECTED \n"
            conversation_context += ns + fecha_hora_g() + "\n"
            # Reiniciar gestor con nuevo modelo
            _init_context_manager()
            main(ns); print(ns); return

        if command in ("--lms", "--listmodels"):
            print("\nModelos Mistral:\n")
            for i, m in enumerate(mistral_models):
                marca = " ◀ activo" if m == mistral_model else ""
                print(f"  ({i+1}) {m}{marca}")
            return

        # ── Info / Help ──────────────────────────────────────────
        if command in ("--i", "--info", "--help"):
            print_info(); return

        # ── SSH/SFTP ─────────────────────────────────────────────
        if command in ("--sshc", "--ssh--connection"):
            import asyncio
            if sftp_global_connector is None:
                sftp_global_connector = SSHC.SSHConnector()
                croparser.set_sftp_connector(sftp_global_connector)
                print("Estableciendo conexiones SSH/SFTP…")
                try:
                    loop = asyncio.get_event_loop_policy().new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(sftp_global_connector.connect())
                finally:
                    loop.close()
            else:
                print("Conexión Global Operativa")
                sftpcom = " ".join(args[1:]) if len(args) > 1 else "pwd"
                if len(args) > 1 and args[1] == "--":
                    asyncio.run(croparser._prompt_for_connection_details())
                else:
                    asyncio.run(croparser.test(sftpcom))
            return

        # ── LOC ──────────────────────────────────────────────────
        if command in ("--loc", "--load-osiris-context"):
            if len(args) < 2:
                print("Uso: --loc <archivo> | --loc help"); return
            if args[1] == "help":
                LOC.load_osiris_context(["--help"])
            else:
                if not os.path.isfile(args[1]):
                    print(f"ADVERTENCIA: '{args[1]}' no existe."); return
                response_loc = LOC.load_osiris_context([args[1]])
                print("LOC RESPONSE\n", response_loc)
                while True:
                    read_i = input(
                        "\n  1) Añadir al contexto actual"
                        "\n  2) Borrar contexto y añadir"
                        "\n  3) No añadir nada"
                        "\n  Seleccione (1/2/3): "
                    )
                    try:
                        opt = int(read_i)
                        if 1 <= opt <= 3: break
                        print("❌ Opción no válida.")
                    except ValueError:
                        print("⚠️  Número por favor.")
                if opt == 1:
                    conversation_context += response_loc
                    if MCX_MANAGER:
                        MCX_MANAGER.add_system(response_loc, essential=False)
                elif opt == 2:
                    main(["--exp", "lastLOC"]); main(["--cc"])
                    conversation_context += response_loc
                    if MCX_MANAGER:
                        MCX_MANAGER.add_system(response_loc, essential=False)
                elif opt == 3:
                    print("No se añadió nada.")
            return

        if command in ("--arc", "--add-response-context"):
            if last_response:
                conversation_context += last_response
                if MCX_MANAGER:
                    MCX_MANAGER.add_system(last_response, essential=False)
                print("Última respuesta añadida al contexto.")
            else:
                print("No hay última respuesta.")
            return

        if command in ("--sla", "--showlastanswer"):
            show_text_window(last_response); return

        # ── Comandos mapeados ────────────────────────────────────
        if command in commands_map:
            print("COMMAND IN LIST:", commands_map[command])

        # ── Config ───────────────────────────────────────────────
        if command in ("--lc", "--loadconfig"):
            if len(args) > 1 and is_file(args[1]):
                config  = load_config(args[1])
                API_KEY = config.get("api_key", API_KEY)
                client  = Mistral(api_key=API_KEY)
                _init_context_manager()
            else:
                print("Archivo de configuración no encontrado.")
            return

        elif command == "--log":
            if len(args) > 1:
                log_interaction(" ".join(args[1:]), last_response)
            return

        elif command in ("--sp", "--setparams"):
            if len(args) > 1: set_model_params(args[1:])
            return

        elif command in ("--ta", "--toggleautosave"):
            toggle_autosave(args[1].lower() == "on" if len(args) > 1 else True); return

        elif command in ("--l", "--load"):
            if len(args) > 1 and is_file(args[1]):
                load = read_file(args[1])
                print(f"Cargado: {args[1]}")
            else:
                print("Archivo no encontrado.")
            return

        elif command in ("--al", "--addload"):
            args.pop(0)
            user_input = " ".join(args)
            if load:
                user_input = load + " " + user_input
                load = ""   # BUG FIX: limpiar buffer tras usarlo.
                            # Sin esto, develop.info (o cualquier archivo cargado)
                            # se antepone a CADA llamada posterior que use --al,
                            # contaminando todos los turnos siguientes.
            response_text = generate_response(user_input)
            print(" \n→", response_text); return

        elif command in ("--sl", "--showload"):
            print(f"load:\n{load}") if load else messagebox.showinfo("Info", "load vacío.")
            return

        elif command in ("--li", "--loadimage"):
            textWithImage = " ".join(args[2:]) if len(args) > 2 else "Interpretar imagen"
            if len(args) > 1 and args[1] == "--fd":
                image_path = filedialog.askopenfilename(
                    initialdir=".", title="Seleccionar imagen",
                    filetypes=(("Imágenes", "*.jpg *.jpeg *.png *.gif"), ("Todos", "*.*"))
                )
                if image_path:
                    generate_with_image(image_path, textWithImage)
                else:
                    messagebox.showinfo("Info", "No se seleccionó imagen.")
            elif len(args) > 1:
                image_path = args[1]
                if is_file(image_path) or image_path.startswith(("http://", "https://")):
                    generate_with_image(image_path, textWithImage)
                else:
                    print("Imagen no encontrada.")
            return

        elif command in ("--sw", "--showwin"):
            show_text_window(conversation_context) if conversation_context else \
                messagebox.showinfo("Info", "No hay texto.")
            return

        elif command in ("--ss", "--screenshot"):
            screen_shot(); return

        elif command in ("--la", "--loadanswer"):
            load = last_response
            print("Cargada última respuesta."); return

        elif command in ("--sav", "--saveload"):
            fn = f"com/datas/{args[1]}.mistral" if len(args) > 1 else "com/datas/saveload.mistral"
            save_file(fn, conversation_context); return

        elif command in ("--sr", "--saverequest"):
            if len(args) > 1: save_request(" ".join(args[1:]))
            return

        elif command in ("--sa", "--saveanswer"):
            save_answer(args[1] if len(args) > 1 else ""); return

        elif command in ("--sc", "--savecontext"):
            save_context(); return

        elif command in ("--as", "--autosave"):
            autosave(); return

        elif command in ("--nq", "--newquestions"):
            if len(args) > 1:
                for q in generate_new_questions(" ".join(args[1:])):
                    print(" -", q)
            return

        elif command in ("--sd", "--send"):
            if len(args) > 1:
                response_text = generate_response(" ".join(args[1:]))
                print(" \n→", response_text)
            return

        elif command in ("--ls", "--listfiles"):
            if len(args) < 2: args.append(".")
            tdir = os.path.join("com/datas/", args[1])
            print(f"Listando {tdir}:")
            try:
                r = subprocess.run(f"ls -ltr \"{tdir}\" | awk '{{print $9, $5}}'",
                                   shell=True, capture_output=True, text=True)
                print(r.stdout)
            except Exception as e:
                print(f"Error: {e}")
            return

        elif command in ("--cc", "--clearcontext"):
            conversation_context = ""
            conversation_messages.clear()
            if MCX_MANAGER:
                keep = input("  ¿Conservar fragmentos esenciales/CRO? (s/n): ").lower()
                MCX_MANAGER.reset(keep_essential=(keep == "s"))
            print("Contexto limpiado."); return

        elif command in ("--lsel", "--loadselect"):
            if len(args) > 1 and is_file(args[1]):
                txt = read_file(args[1])
                conversation_context += txt + "\n"
                if MCX_MANAGER:
                    MCX_MANAGER.add_system(txt, essential=False)
                print("Contexto seleccionado cargado.")
            return

        elif command in ("--lm", "--loadmultiple"):
            for fn in args[1:]:
                if is_file(fn):
                    txt = read_file(fn)
                    conversation_context += txt + "\n"
                    if MCX_MANAGER:
                        MCX_MANAGER.add_system(txt, essential=False)
                    print(f"Cargado: {fn}")
                else:
                    print(f"No encontrado: {fn}")
            return

        elif command in ("--exp", "--export"):
            if len(args) > 1:
                win.export_context(args[1], conversation_context)
            return

        elif command in ("--imp", "--import"):
            if len(args) > 1:
                conversation_context = win.import_context(args[1])
                conversation_context += f"\nContext Imported with {args}\n"
            return

        elif command in ("--s", "--search"):
            args.pop(0)
            lc   = "--load" in args
            term = " ".join(a for a in args if a != "--load").strip()
            if term: search_context(term, lc)
            else:    print("No se especificó término.")
            return

        elif command in ("--st", "--settopic"):
            if len(args) > 1:
                topic = " ".join(args[1:])
                print(f"Tema: {topic}")
            return

        elif command in ("--dialog", "--ask"):
            dtext = win.dialog_window()
            if dtext:
                print(" → ", dtext)
                rt = generate_response(str(dtext))
                print(" → ", rt)
            else:
                print("Sin respuesta.")
            arw(); return

        elif command in ("--di", "--decodeimage"):
            if len(args) > 1:
                decode_img(b"{args[1]}")
                print("DECODE")
            return

        elif command in ("--tvl", "--tvideol"):
            prompt = ""
            if len(args) == 2 and args[1] == "--dialog":
                dialog_h = win.dialog_window()
                Context  = dialog_h.split()
                argsx    = [z for z in Context if z.startswith("@")]
                video_translate(Context[0], "Automatic @def", argsx)
                return
            if len(args) > 2 and args[2] == "--dialog":
                del args[2]
                args.append(win.dialog_window())
            if len(args) > 2:
                prompt = " ".join(args[2:])
            argsx = [z for z in args if z.startswith("@")]
            if len(args) > 1:
                print("Procesando…")
                video_translate(args[1], prompt, argsx)
            else:
                print("Es necesario parámetro de vídeo.")
            print("---FIN VIDEO----"); return

        elif command in ("--r", "--reset"):
            conversation_context = ""
            conversation_messages.clear()
            load = last_response = topic = ""
            if MCX_MANAGER:
                MCX_MANAGER.reset(keep_essential=False)
            print("Todo reseteado."); return

        elif command in ("--diagnostic", "--d"):
            if len(args) > 1:
                opts = {
                    "server": (["sudo","tool/mrls"],         "com/datas/rls.mistral.ctrl"),
                    "system": (["sudo","tool/diagnosis1"],   "com/datas/system_info.mistral.ctrl"),
                    "memory": (["sudo","tool/memory"],       "com/datas/memory.mistral.ctrl"),
                }
                if args[1] in opts:
                    com_d, fileload = opts[args[1]]
                else:
                    print("Parámetro incorrecto (server|system|memory)"); return
            else:
                print("Necesita parámetro (server|system|memory)"); return
            try:   core.ps.ps(com_d)
            except Exception: subprocess.run(com_d)
            print("\nIntentando Reporte…")
            main(["--l", fileload, "Realiza un diagnóstico del sistema"])
            main(["--al", "Realiza reporte"])
            print("\nFin del reporte."); return

        else:
            print(f"Comando desconocido: {command}. Escribe --info para ayuda.")

    except Exception as e:
        if not API_KEY:
            try:
                API_KEY = obtener_key_mistral()
                client  = Mistral(api_key=API_KEY)
                _init_context_manager()
            except Exception as f:
                print("Error API_KEY:", f); return
        print("Error:", e)
        import traceback; traceback.print_exc()


# ─────────────────────────────────────────────────────────────────
#  Arranque
# ─────────────────────────────────────────────────────────────────
init     = 0
HELO     = "\nHELO START - Sistema OSIRIS (Mistral) iniciado a las: " + fecha_hora
use_def  = False

try:
    if len(sys.argv) > 2 and sys.argv[2] == "--preload":
        print("Iniciando precargas…")
        while_args(["--arw", "--cm", "--aap", "--apr"])
        main(HELO)
        main(["--l", "/var/osiris2/bin/tool/loadCore.human.ai"])
        while_args(["--apr"])
        print("Precargas finalizadas.")
    else:
        print("Sin precarga. Carga por defecto.")
        use_def = True
except Exception as e:
    print("Arranque sin preload:", e)
    use_def = True

# Registrar HELO en el gestor de contexto
if MCX_MANAGER:
    MCX_MANAGER.add_system(HELO + "\nComandos (Glyphs): " + str(commands_map),
                           essential=False)

conversation_context += HELO + "\nComandos (Glyphs): " + str(commands_map) + "\n--\n"

if use_def:
    def1 = ["--cm", "--info"]
    while_args(def1)
    print("Cargado con valores por defecto:", " | ".join(def1))

print("Mistral2 Iniciado ✅")

if __name__ == "__main__":
    init += 1
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        main(HELO)