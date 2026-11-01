import yaml
import toml
import json
from io import StringIO
import re

INFO = "LIBRERIA SERIALIZE"

def clean_string(s):
    """Limpia una cadena eliminando escapes innecesarios."""
    if isinstance(s, str):
        s = s.replace("\\n", "").replace("\\r", "")  # Elimina escapes de newline
        s = s.replace("\\\\", "")  # Elimina backslashes dobles (escapados)
        s = s.replace("\\/", "/")  # Elimina forward slashes escapados
        s = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", s)  # Elimina caracteres de control ASCII
    return s

def clean_json_object(obj):
    """Limpia recursivamente las cadenas dentro de un objeto JSON."""
    if isinstance(obj, dict):
        return {k: clean_json_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_object(elem) for elem in obj]
    elif isinstance(obj, str):
        return clean_string(obj)
    else:
        return obj  # No modificar otros tipos de datos


def serialize(objeto_o_cadena, formato_destino="yaml", accion="deserialize", formato_origen="json"):
    """
    Gestiona la serialización o deserialización de datos:
    - Serializa un objeto Python a YAML o TOML.
    - Deserializa una cadena JSON a un objeto Python y luego lo serializa a YAML o TOML.

    Args:
        objeto_o_cadena: El objeto Python a serializar, o la cadena JSON a deserializar.
        formato_destino (str): Formato de salida deseado ("yaml" o "toml"). Por defecto "yaml".
        accion (str): "serialize" para serializar un objeto directo.
                      "deserialize" para deserializar la entrada (JSON) y luego serializarla.
                      Por defecto "serialize".
        formato_origen (str): Formato de la cadena de entrada si la acción es "deserialize".
                              Actualmente solo soporta "json". Por defecto "json".

    Returns:
        str: La cadena serializada resultante si la operación es exitosa.
        None: Si ocurre un error durante el proceso. Los errores se imprimirán por consola.
    """
    objeto_python_intermedio = None # Este será el objeto Python después de cualquier deserialización.
    cadena_procesada = None
    
    # Asegurarse de que los formatos y acciones sean cadenas válidas
    formato_destino = str(formato_destino).lower()
    accion = str(accion).lower()
    formato_origen = str(formato_origen).lower()

    if accion == "deserialize":
        if not isinstance(objeto_o_cadena, str):
            print("❌ Error: Para la acción 'deserialize', el primer argumento debe ser una cadena (JSON).")
            return None

        if formato_origen == "json":
            try:
                objeto_python_intermedio = json.loads(objeto_o_cadena)
                print("✅ Deserialización de JSON a objeto Python exitosa.")
            except json.JSONDecodeError as e:
                print(f"❌ Error al deserializar de JSON: {e}")
                return None
            except Exception as e:
                print(f"❌ Error inesperado al deserializar de JSON: {e}")
                return None
        else:
            print(f"⚠️ Formato de origen '{formato_origen}' no soportado para deserialización. Actualmente solo 'json'.")
            return None
    elif accion == "serialize":
        objeto_python_intermedio = objeto_o_cadena # Si la acción es serializar, la entrada es directamente el objeto Python.
    else:
        print("❌ Acción no válida. Debe ser 'serialize' o 'deserialize'.")
        return None

    # Si llegamos aquí y tenemos un objeto Python intermedio (o la entrada original), procedemos a serializarlo.
    if objeto_python_intermedio is not None:
        if formato_destino == "yaml":
            try:
                string_io_buffer = StringIO()
                yaml.dump(objeto_python_intermedio, string_io_buffer, indent=2, allow_unicode=True)
                cadena_procesada = string_io_buffer.getvalue()
                print("👍 Serialización a YAML exitosa.")
            except Exception as e:
                print(f"❌ Error al serializar a YAML: {e}")
                return None
        elif formato_destino == "toml":
            try:
                string_io_buffer = StringIO()
                toml.dump(objeto_python_intermedio, string_io_buffer)
                cadena_procesada = string_io_buffer.getvalue()
                print("👍 Serialización a TOML exitosa.")
            except Exception as e:
                print(f"❌ Error al serializar a TOML: {e}")
                return None
        else:
            print(f"⚠️ Formato de destino '{formato_destino}' no válido. Debe ser 'yaml' o 'toml'.")
            return None
    
    return cadena_procesada
