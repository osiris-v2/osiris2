import time
import os
import requests
from datetime import datetime
import sys
print("ECONO IMPORT:",time.time())

PAISES_A_MONITOREAR = []

def set_country(paises):
    global PAISES_A_MONITOREAR
    PAISES_A_MONITOREAR = paises
    print("Establecido país:",paises)

# Diccionario de indicadores económicos.
# 'Nombre amigable': 'Código del indicador en la API del Banco Mundial'
# Puedes encontrar más códigos en: https://data.worldbank.org/indicator
INDICADORES_ECONOMICOS = {
    "🌍 PIB per cápita (USD)": "NY.GDP.PCAP.CD",      # Producto Interno Bruto per cápita (dólares actuales)
    "📈 Inflación (IPC anual %)": "FP.CPI.TOTL.ZG",   # Tasa de inflación, precios al consumidor (% anual)
    "👷‍♂️ Tasa de Desempleo (%)": "SL.UEM.TOTL.ZS",    # Tasa de desempleo total (% de la fuerza laboral total)
    "📊 Deuda Pública (% PIB)": "GC.DOD.TOTL.GD.ZS",  # Deuda bruta del gobierno central (% del PIB)
    "📊 Deuda a Corto Plazo (% del total de la Deuda Externa)": "DT.DOD.DSTC.ZS",  # Deuda a corto plaze (% del total de la deuda externa)
    "🧑‍🤝‍🧑 Población total": "SP.POP.TOTL",            # Población total
    "💰 Balanza Comercial (USD)": "BN.GSR.GNFS.CD",   # Exportaciones netas de bienes y servicios (balanza comercial)
    "🏥 Gasto en Salud (% PIB)": "SH.XPD.CHEX.GD.ZS"  # Gasto en salud (% del PIB)
}

# Año de los datos a buscar.
# La API del Banco Mundial a menudo tiene los datos más recientes consolidados para el año anterior.
# Por ejemplo, para 2024, los datos más recientes completos suelen ser de 2022 o 2023.
AÑO_DE_LOS_DATOS = 2022

# Intervalo de refresco en segundos.
# ¡Cuidado con el "rate limit" de las APIs si usas una diferente!
INTERVALO_REFRESCO_SEGUNDOS = 15

# Intervalo de chequeo de la tecla 'q' durante el tiempo de espera.
# Un valor más pequeño hace que la detección sea más rápida, pero puede consumir un poco más de CPU.
INTERVALO_CHEQUEO_TECLA = 1

# --- FIN DE LA CONFIGURACIÓN ---

# --- Importaciones de módulos específicos de la plataforma ---
# Estos módulos se importan globalmente, pero solo si el sistema operativo lo soporta.
if sys.platform == 'win32':
    import msvcrt # Para lectura de teclado no bloqueante en Windows
else: # Para sistemas Unix-like (Linux, macOS)
    import select # Para comprobar si hay entrada disponible sin bloquear
    import tty    # Para manipular las configuraciones del terminal
    import termios # Para guardar y restaurar las configuraciones del terminal

# Variable global para almacenar la configuración original del terminal en sistemas Unix-like
# Es crucial para restaurar el terminal a su estado normal al salir.
original_terminal_settings = None

# --- Funciones para la interacción y recolección de datos ---

def limpiar_pantalla():
    """Limpia la consola para una visualización dinámica."""
    os.system('cls' if os.name == 'nt' else 'clear')

def obtener_datos_indicador_banco_mundial(codigo_pais, codigo_indicador, año):
    """
    Obtiene datos de un indicador específico para un país y año dados desde la API del Banco Mundial.
    Devuelve un diccionario con los datos o un estado de error.
    """
    url = f"http://api.worldbank.org/v2/country/{codigo_pais}/indicator/{codigo_indicador}?format=json&date={año}"
    
    try:
        # Añadimos un un timeout para evitar que la solicitud se quede colgada
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP 4xx/5xx
        data = response.json()

        # La estructura de la respuesta del Banco Mundial es un poco peculiar:
        # [0] contiene metadatos sobre la consulta.
        # [1] contiene la lista de observaciones de datos.
        if data and len(data) > 1 and data[1] and data[1][0] and data[1][0]['value'] is not None:
            valor = data[1][0]['value']
            nombre_pais = data[1][0]['country']['value']
            fecha_dato = data[1][0]['date'] # Año en el que se publicó el dato

            return {
                "status": "ok",
                "nombre_pais": nombre_pais,
                "valor": valor,
                "año_dato": fecha_dato
            }
        else:
            # Los datos pueden estar vacíos o el valor es nulo (no disponible para ese año/indicador)
            return {
                "status": "no_disponible",
                "mensaje": "Datos no disponibles para este indicador/año.",
                "codigo_pais": codigo_pais,
                "codigo_indicador": codigo_indicador
            }

    except requests.exceptions.HTTPError as http_err:
        # Errores HTTP como 404, 500, etc.
        return {
            "status": "error",
            "mensaje": f"Error HTTP: {http_err}",
            "codigo_pais": codigo_pais,
            "codigo_indicador": codigo_indicador
        }
    except requests.exceptions.ConnectionError as conn_err:
        # Errores de conexión (DNS, rechazo de conexión)
        return {
            "status": "error",
            "mensaje": f"Error de Conexión: {conn_err}",
            "codigo_pais": codigo_pais,
            "codigo_indicador": codigo_indicador
        }
    except requests.exceptions.Timeout as timeout_err:
        # La solicitud superó el tiempo límite
        return {
            "status": "error",
            "mensaje": f"Timeout de la solicitud: {timeout_err}",
            "codigo_pais": codigo_pais,
            "codigo_indicador": codigo_indicador
        }
    except requests.exceptions.RequestException as req_err:
        # Cualquier otro error de requests
        return {
            "status": "error",
            "mensaje": f"Error de solicitud: {req_err}",
            "codigo_pais": codigo_pais,
            "codigo_indicador": codigo_indicador
        }
    except ValueError: # Error al parsear JSON
        return {
            "status": "error",
            "mensaje": "Respuesta inválida (no es JSON válido).",
            "codigo_pais": codigo_pais,
            "codigo_indicador": codigo_indicador
        }
    except Exception as e:
        # Cualquier otro error inesperado
        return {
            "status": "error",
            "mensaje": f"Error inesperado: {e}",
            "codigo_pais": codigo_pais,
            "codigo_indicador": codigo_indicador
        }

def formatear_valor(nombre_indicador, valor):
    """Formatea el valor numérico según el tipo de indicador para mayor legibilidad."""
    if valor is None:
        return "N/A"

    # Ejemplos de formato. Puedes añadir más lógicas si lo necesitas.
    if "PIB" in nombre_indicador or "Balanza Comercial" in nombre_indicador:
        return f"${valor:,.0f}" # Formato de moneda sin decimales (ej: $1,234,567)
    elif "Inflación" in nombre_indicador or "Desempleo" in nombre_indicador or "Deuda Pública" in nombre_indicador or "Gasto en Salud" in nombre_indicador:
        return f"{valor:,.2f}%" # Formato de porcentaje con dos decimales (ej: 5.25%)
    elif "Población" in nombre_indicador:
        return f"{valor:,.0f}" # Formato de número entero sin decimales (ej: 123,456,789)
    else:
        return f"{valor:,.2f}" # Formato por defecto con dos decimales

# --- Funciones para la detección de la tecla 'q' (multiplataforma) ---

def configurar_terminal_unix():
    """Configura el terminal en modo 'cbreak' para lectura de caracteres sin bloqueo (Unix-like)."""
    global original_terminal_settings
    fd = sys.stdin.fileno() # Obtiene el descriptor de archivo de la entrada estándar
    original_terminal_settings = termios.tcgetattr(fd) # Guarda la configuración actual
    tty.setcbreak(fd) # Establece el modo cbreak: entrada de un carácter a la vez, sin eco

def restaurar_terminal_unix():
    """Restaura la configuración original del terminal (Unix-like)."""
    # Solo restauramos si original_terminal_settings fue establecido (es decir, si no hubo error inicial)
    if original_terminal_settings:
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, original_terminal_settings) # Restaura la configuración

def get_char_non_blocking_cross_platform():
    """
    Intenta leer un carácter del teclado sin bloquear la ejecución.
    Devuelve el carácter en minúscula si se presiona uno, de lo contrario devuelve None.
    """
    if sys.platform == 'win32':
        if msvcrt.kbhit(): # Comprueba si hay una tecla pulsada
            return msvcrt.getch().decode('utf-8').lower() # Lee la tecla, la decodifica y la convierte a minúscula
        return None
    else: # Para sistemas Unix-like (Linux, macOS)
        # select.select comprueba si sys.stdin tiene datos listos para leer sin bloquear
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1).lower() # Lee un carácter y lo convierte a minúscula
        return None

# --- Función principal del monitor ---

def ejecutar_monitor_economico():
    """Función principal que ejecuta el monitor en un bucle continuo."""
    
    # Comprobar si requests está instalado
    try:
        import requests
    except ImportError:
        print("❌ Error: La librería 'requests' no está instalada.")
        print("Por favor, instálala con: pip install requests")
        return

    # Configura el terminal para entrada no bloqueante en sistemas Unix-like
    if sys.platform != 'win32':
        try:
            configurar_terminal_unix()
        except termios.error as e: # Ahora termios está definido gracias a la importación global
            print(f"❌ Error al configurar el terminal para entrada no bloqueante: {e}")
            print("Es posible que no puedas salir con 'q'. Intenta usar Ctrl+C.")
            # Si hay un error aquí, original_terminal_settings permanecerá None,
            # lo cual es manejado por restaurar_terminal_unix() al final.

    try:
        while True:
            limpiar_pantalla()
            print("Monitoreando:",PAISES_A_MONITOREAR)
            print("🌟 Osiris: Monitor Económico en Acción 🌟")
            print(f"🔄 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🗓️ Datos del año: {AÑO_DE_LOS_DATOS}\n")
            print("---")

            for pais_code in PAISES_A_MONITOREAR:
                # Intentamos obtener el nombre completo del país desde el primer indicador que funcione
                nombre_pais_completo = pais_code # Por defecto, si no se puede obtener
                
                print(f"🌎 {pais_code}:")
                for nombre_indicador, codigo_indicador in INDICADORES_ECONOMICOS.items():
                    resultado = obtener_datos_indicador_banco_mundial(pais_code, codigo_indicador, AÑO_DE_LOS_DATOS)

                    if resultado["status"] == "ok":
                        if "nombre_pais" in resultado:
                            nombre_pais_completo = resultado["nombre_pais"] 
                        valor_formateado = formatear_valor(nombre_indicador, resultado["valor"])
                        print(f"  {nombre_indicador}: {valor_formateado}")
                    elif resultado["status"] == "no_disponible":
                        print(f"  {nombre_indicador}: 🤷 Datos no disponibles.")
                    else:
                        print(f"  {nombre_indicador}: ❌ Error ({resultado['mensaje']}).")
                print("---")
                print(f"\n") # Espacio entre países
            
            print(f"✨ ¡Refrescando en {INTERVALO_REFRESCO_SEGUNDOS} segundos! Pulsa 'q' para salir. ✨")
            print("--help para comandos disponibles (fuera de este modo de monitor)--")

            # Bucle de espera no bloqueante para detectar la tecla 'q'
            tiempo_transcurrido = 0
            while tiempo_transcurrido < INTERVALO_REFRESCO_SEGUNDOS:
                char_leido = get_char_non_blocking_cross_platform()
                if char_leido == 'q':
                    print("\n👋 ¡Saliendo del monitor! ¡Hasta la próxima! 👋")
                    return # Sale de la función, terminando el programa
                time.sleep(INTERVALO_CHEQUEO_TECLA)
                tiempo_transcurrido += INTERVALO_CHEQUEO_TECLA
    finally:
        # Asegura que la configuración del terminal se restaure al salir, incluso si hay un error.
        restaurar_terminal_unix()