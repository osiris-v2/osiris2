import re
import json
import urllib.parse
import time
import shlex
import subprocess
from .cro_definitions import osiris_definitions # <--- IMPORTACION DE DEFINICIONES

INFO = """
Module Cro Parser Info
Osiris internal python library
"""

import urllib.parse
# Asumiendo que 'requests' y un módulo de base de datos interna de Osiris están disponibles
# import requests
# import osiris_internal_db

def execute_search_action(payload):
    print("-----------=========?¿")
    print(str(payload))
    mode = payload.get("mode")
    command_type = payload.get("command_type")
    action_details = payload.get("action_details", {}) # Diccionario con los detalles específicos de la acción

    print(f"DEBUG: Ejecutando acción de búsqueda para el modo: {mode}, tipo: {command_type}")

    if command_type == "URL_SEARCH":
        # Manejo de búsquedas en Google o Bing
        url_template = action_details.get("URL_TEMPLATE")
        query = action_details.get("QUERY")
        search_type = action_details.get("TYPE") # Puede ser una lista si ALLOW_MULTIPLE es True

        if not url_template or not query:
            print("ERROR: Parámetros URL_TEMPLATE o QUERY faltantes para URL_SEARCH.")
            return "Error en la ejecución de búsqueda URL."

        # Asegurarse de que search_type sea una lista para iterar
        if isinstance(search_type, str):
            search_type = [search_type]

        results = []
        for s_type in search_type:
            # Codificar la consulta para URL
            encoded_query = urllib.parse.quote_plus(query)
            # Reemplazar marcadores de posición en la plantilla URL
            final_url = url_template.replace("{QUERY}", encoded_query).replace("{TYPE}", s_type)

            print(f"Simulando búsqueda en URL: {final_url}")

            # Aquí iría el código real para hacer la petición HTTP
            # try:
            #     response = requests.get(final_url)
            #     response.raise_for_status() # Lanza un error para códigos de estado HTTP erróneos
            #     results.append(f"Resultado de {s_type} de {final_url}: (contenido simulado o resumido)")
            #     # Procesar el contenido de la respuesta aquí
            # except requests.exceptions.RequestException as e:
            #     results.append(f"Error al conectar con {final_url}: {e}")
            results.append(f"Simulación exitosa para tipo '{s_type}' en {final_url}. Se procesaría la respuesta web.")

        return "\n".join(results)

    elif command_type == "DB_SEARCH":
        # Manejo de búsquedas en la base de conocimiento interna de Osiris
        db_query_template = action_details.get("DB_QUERY_TEMPLATE")
        query = action_details.get("QUERY")
        tags = action_details.get("TAGS", "")

        if not db_query_template or not query:
            print("ERROR: Parámetros DB_QUERY_TEMPLATE o QUERY faltantes para DB_SEARCH.")
            return "Error en la ejecución de búsqueda DB interna."

        # Construir la consulta SQL
        final_db_query = db_query_template.replace("{QUERY}", query).replace("{TAGS}", tags)

        print(f"Simulando búsqueda en base de datos interna con consulta: '{final_db_query}'")
        # Aquí iría el código real para interactuar con la base de datos interna de Osiris
        # try:
        #     db_connection = osiris_internal_db.connect()
        #     cursor = db_connection.cursor()
        #     cursor.execute(final_db_query)
        #     db_results = cursor.fetchall()
        #     db_connection.close()
        #     if db_results:
        #         return f"Resultados de la base de datos interna: {db_results}"
        #     else:
        #         return "No se encontraron resultados en la base de datos interna."
        # except Exception as e:
        #     return f"Error al consultar la base de datos interna: {e}"
        return f"Simulación exitosa para búsqueda en base de datos interna. Se ejecutaría: '{final_db_query}' y se devolverían los resultados."

    else:
        return f"Tipo de comando de búsqueda desconocido: {command_type}"






class CROParser:
    # Constructor modificado: ya no necesita recibir osiris_definitions como argumento
    def __init__(self):
        # Utiliza directamente la variable osiris_definitions importada
        self.osiris_definitions = osiris_definitions
        self.parsed_actions = []
        self.errors = []
        self.warnings = []

    def _log_error(self, message):
        self.errors.append(f"ERROR: {message}")
        print(f"ERROR: {message}") # Para depuración
    def _log_warning(self, message):
        self.warnings.append(f"WARNING: {message}")
        print(f"WARNING: {message}") # Para depuración

    def _validate_and_prepare_action(self, group_name, target_member, current_params):
        """
        Valida los parámetros de un miembro objetivo y prepara las acciones concretas.
        Puede generar múltiples acciones si un parámetro es ALLOW_MULTIPLE y ACTION_PER_VALUE.
        """
        actions = []
        if group_name not in self.osiris_definitions["PROTO_DEFINITIONS"] or target_member not in self.osiris_definitions["PROTO_DEFINITIONS"][group_name]:
            self._log_error(f"Definición de protocolo no encontrada para {group_name} -> {target_member}")
            return []

        proto_def = self.osiris_definitions["PROTO_DEFINITIONS"][group_name][target_member]
        
        template_key = next((k for k in proto_def.keys() if 'TEMPLATE' in k.upper()), None)
        base_template = proto_def.get(template_key)
        action_type = proto_def.get("ACTION_TYPE")

        if not action_type:
            self._log_error(f"Missing ACTION_TYPE in proto definition for {group_name} -> {target_member}")
            return []

        param_sets_to_process = [{}] # Start with one empty set of params for default processing

        # Iterate over each parameter defined in the PROTO_DEFINITIONS
        for param_name, param_def in proto_def.get("PARAMETERS", {}).items():
            value_from_ai = current_params.get(param_name)
            
            is_dynamic = param_def.get("DYNAMIC", False)
            is_required = param_def.get("REQUIRED", False)
            default_value = param_def.get("DEFAULT")
            param_type = param_def.get("TYPE", "string")
            allowed_values = param_def.get("VALUES", [])
            allow_multiple = param_def.get("ALLOW_MULTIPLE", False)
            action_per_value = param_def.get("ACTION_PER_VALUE", False)

            if not is_dynamic and value_from_ai is not None:
                self._log_warning(f"AI attempted to set static parameter '{param_name}' for {group_name}->{target_member}. Value '{value_from_ai}' ignored.")
                continue

            if value_from_ai is None:
                if is_required and default_value is None:
                    self._log_error(f"Missing required parameter '{param_name}' for {group_name}->{target_member}. Skipping action.")
                    return []
                else:
                    value_to_use = default_value
            else:
                value_to_use = value_from_ai
            
            validated_values = []
            if value_to_use is not None:
                if allow_multiple and isinstance(value_to_use, str):
                    raw_values = [v.strip() for v in value_to_use.split(',')]
                else:
                    raw_values = [value_to_use]
                
                for val in raw_values:
                    valid_val = val
                    if param_type == "enum":
                        if val not in allowed_values:
                            self._log_warning(f"Invalid enum value '{val}' for parameter '{param_name}' in {group_name}->{target_member}. Using default or skipping.")
                            if default_value is not None and default_value in allowed_values:
                                valid_val = default_value
                            else:
                                continue
                    # Type conversion for booleans
                    if param_type == "boolean":
                        if isinstance(valid_val, str):
                            if valid_val.lower() == "true":
                                valid_val = True
                            elif valid_val.lower() == "false":
                                valid_val = False
                            else:
                                self._log_warning(f"Invalid boolean string '{val}' for parameter '{param_name}' in {group_name}->{target_member}. Defaulting to False.")
                                valid_val = False 
                        elif not isinstance(valid_val, bool):
                            valid_val = bool(valid_val) # Coerce other types
                    
                    validated_values.append(valid_val)
            
            if not validated_values and is_required:
                self._log_error(f"No valid value found for required parameter '{param_name}' for {group_name}->{target_member}. Skipping action.")
                return []
            
            if action_per_value and validated_values:
                new_param_sets = []
                for current_set in param_sets_to_process:
                    for val in validated_values:
                        new_set = current_set.copy()
                        new_set[param_name] = val
                        new_param_sets.append(new_set)
                param_sets_to_process = new_param_sets
            elif validated_values:
                val_to_apply = validated_values[0] if validated_values else None
                for current_set in param_sets_to_process:
                    current_set[param_name] = val_to_apply
            else:
                for current_set in param_sets_to_process:
                    current_set[param_name] = default_value

        # Generate concrete actions from the param_sets_to_process
        for final_params_set in param_sets_to_process:
            concrete_template = base_template
            if concrete_template:
                try:
                    processed_params_for_template = {}
                    for k, v in final_params_set.items():
                        if isinstance(v, str) and action_type in ["URL_SEARCH", "DB_SEARCH"]:
                            processed_params_for_template[k] = urllib.parse.quote_plus(v)
                        else:
                            processed_params_for_template[k] = v

                    concrete_template = concrete_template.format(**processed_params_for_template)
                except KeyError as e:
                    self._log_error(f"Missing parameter in template for {group_name}->{target_member}: {e}. Template: {base_template}. Parameters: {final_params_set}")
                    continue

            actions.append({
                "group_name": group_name,
                "member": target_member,
                "action_type": action_type,
                "template": concrete_template,
                "parameters": final_params_set,
                "raw_cro_lines": []
            })
        
        return actions

    def parse(self, ai_response_text: str):
        self.parsed_actions = []
        self.errors = []
        self.warnings = []

        cro_blocks = re.findall(r"```CRO\s*\n(.*?)\n```", ai_response_text, re.DOTALL)

        if not cro_blocks:
            return []

        for block_content in cro_blocks:
            lines = block_content.split('\n')

            current_group_name = None
            current_targets = []
            current_params = {}
            current_raw_cro_lines = []

            in_heredoc_mode = False
            heredoc_var_name = None
            heredoc_delimiter = None
            heredoc_content_buffer = []

            in_triple_quote_mode = False
            triple_quote_var_name = None
            triple_quote_content_buffer = []

            def _process_current_command_group():
                """Helper para procesar el grupo de comando actual y sus parámetros."""
                nonlocal current_group_name, current_targets, current_params, current_raw_cro_lines
                if current_group_name and current_targets:
                    for target_member in current_targets:
                        new_actions = self._validate_and_prepare_action(
                            current_group_name, 
                            target_member, 
                            current_params
                        )
                        for action in new_actions:
                            action["raw_cro_lines"] = list(current_raw_cro_lines)
                            self.parsed_actions.append(action)
                
                current_group_name = None
                current_targets = []
                current_params = {}
                current_raw_cro_lines = []

            for line_idx, line in enumerate(lines):
                clean_line = line.rstrip('\r\n')

                if in_triple_quote_mode:
                    current_raw_cro_lines.append(clean_line)
                    # Corregido: `"""` en lugar de `"""`
                    if clean_line.strip() == '"""':
                        current_params[triple_quote_var_name] = "\n".join(triple_quote_content_buffer)
                        in_triple_quote_mode = False
                        triple_quote_var_name = None
                        triple_quote_content_buffer = []
                    else:
                        triple_quote_content_buffer.append(clean_line)
                    continue

                if in_heredoc_mode:
                    current_raw_cro_lines.append(clean_line)
                    if clean_line.strip() == heredoc_delimiter:
                        current_params[heredoc_var_name] = "\n".join(heredoc_content_buffer)
                        in_heredoc_mode = False
                        heredoc_var_name = None
                        heredoc_delimiter = None
                        heredoc_content_buffer = []
                    else:
                        heredoc_content_buffer.append(clean_line)
                    continue

                stripped_line = clean_line.strip()
                if not stripped_line:
                    continue
                
                initiator_match = re.match(r"^([A-Z_]+)\_\* (.+)$", stripped_line)
                if initiator_match:
                    _process_current_command_group()
                    
                    group_name = initiator_match.group(1)
                    members_str = initiator_match.group(2)
                    
                    if group_name not in self.osiris_definitions["COMMAND_GROUPS"]:
                        self._log_error(f"Unknown command group '{group_name}' in line: '{stripped_line}'")
                        continue
                    
                    valid_members = []
                    for member in [m.strip() for m in members_str.split(',')]:
                        if member in self.osiris_definitions["COMMAND_GROUPS"][group_name]:
                            valid_members.append(member)
                        else:
                            self._log_warning(f"Invalid member '{member}' for group '{group_name}' in line: '{stripped_line}'")
                    if not valid_members:
                        self._log_warning(f"No valid members found for group '{group_name}' in line: '{stripped_line}'. Skipping initiator.")
                        continue

                    current_group_name = group_name
                    current_targets = valid_members
                    current_params = {}
                    current_raw_cro_lines.append(clean_line)

                elif (triple_quote_start_match := re.match(r"^([A-Z_]+)=\"\"\"(.*)$", stripped_line)):
                    if not current_group_name or not current_targets:
                        self._log_error(f"Triple-quoted parameter line '{stripped_line}' found without a preceding initiator line (command). Ignoring.")
                        continue

                    param_name_for_triple_quote = triple_quote_start_match.group(1)
                    initial_content_on_same_line = triple_quote_start_match.group(2)

                    in_triple_quote_mode = True
                    triple_quote_var_name = param_name_for_triple_quote
                    triple_quote_content_buffer = []

                    # Corregido: `"""` en lugar de `"""`
                    if initial_content_on_same_line.strip().endswith('"""'):
                        content_found = initial_content_on_same_line.strip()[:-3].rstrip()
                        current_params[triple_quote_var_name] = content_found
                        
                        in_triple_quote_mode = False
                        triple_quote_var_name = None
                    else:
                        if initial_content_on_same_line:
                            triple_quote_content_buffer.append(initial_content_on_same_line)

                    current_raw_cro_lines.append(clean_line)
                    continue
                    
                elif re.match(r"^([A-Z_]+)=<<<([A-Z_]+)$", stripped_line):
                    heredoc_start_match = re.match(r"^([A-Z_]+)=<<<([A-Z_]+)$", stripped_line)
                    if not current_group_name or not current_targets:
                        self._log_error(f"Heredoc parameter line '{stripped_line}' found without a preceding initiator line (command). Ignoring.")
                        continue
                    
                    var_name = heredoc_start_match.group(1)
                    delimiter = heredoc_start_match.group(2)
                    
                    if not delimiter:
                        self._log_error(f"Heredoc delimiter cannot be empty in line: '{stripped_line}'")
                        continue 
                    
                    in_heredoc_mode = True
                    heredoc_var_name = var_name
                    heredoc_delimiter = delimiter
                    heredoc_content_buffer = []
                    current_raw_cro_lines.append(clean_line)
                    continue
                    
                elif re.match(r"^([A-Z_]+)=\"(.*?)\"$", stripped_line):
                    param_match = re.match(r"^([A-Z_]+)=\"(.*?)\"$", stripped_line)
                    if not current_group_name or not current_targets:
                        self._log_error(f"Parameter line '{stripped_line}' found without a preceding initiator line (command). Ignorando.")
                        continue
                    
                    param_name = param_match.group(1)
                    param_value = param_match.group(2)
                    current_params[param_name] = param_value
                    current_raw_cro_lines.append(clean_line)
                
                else:
                    self._log_warning(f"Unrecognized CRO syntax or misplaced line: '{stripped_line}'. Saltando.")
            
            _process_current_command_group()
            
            if in_heredoc_mode:
                self._log_error(f"Heredoc for variable '{heredoc_var_name}' started with delimiter '{heredoc_delimiter}' was not closed correctly within the CRO block.")
            if in_triple_quote_mode:
                 self._log_error(f"Triple-quoted block for variable '{triple_quote_var_name}' was not closed correctly within the CRO block.")

        return self.parsed_actions


class CROTranslator:
    def __init__(self, global_mode: str, require_confirmation_for_dangerous_actions: bool = True):
        # Accede a las definiciones de osiris_definitions importadas directamente
        self.osiris_definitions = osiris_definitions
        self.global_mode = global_mode.upper()
        self.require_confirmation = require_confirmation_for_dangerous_actions
        self.translation_errors = []

    def translate_action(self, action: dict) -> dict:
        """
        Traduce una única acción CRO parseada a una representación ejecutable.
        Esta función central contendrá la lógica para cada action_type.
        """
        translated_output = {
            "action_type": action["action_type"],
            "group": action["group_name"],
            "member": action["member"],
            "execution_context": self.global_mode,
            "needs_confirmation": False,
            "executable_command": None,
            "message": None,
            "post_processing_hint": None,
            "error": None
        }

        try:
            params = action["parameters"]
            action_type = action["action_type"]
            member = action["member"]

            # Accede a self.osiris_definitions para las definiciones de PROTO_DEFINITIONS
            proto_def = self.osiris_definitions["PROTO_DEFINITIONS"][action["group_name"]][member]

            if action_type == "URL_SEARCH":
                if self.global_mode in ["CLI", "DESKTOP"]:
                    url = action["template"]
                    quoted_url = shlex.quote(url)
                    translated_output["executable_command"] = f"curl -sL {quoted_url}"
                    translated_output["message"] = f"Se realizará una búsqueda web en {action['group_name']} y se recuperará el contenido."
                    translated_output["post_processing_hint"] = "El contenido recuperado (HTML) puede requerir limpieza/parsing para extraer información."
                elif self.global_mode == "WEB":
                    translated_output["executable_command"] = {
                        "type": "FETCH_URL",
                        "url": action["template"],
                        "method": "GET"
                    }
                    translated_output["message"] = "Se realizará una solicitud de red para obtener información."
                    translated_output["post_processing_hint"] = "El motor web procesará la respuesta obtenida."
                else:
                    translated_output["error"] = f"Acción '{action_type}' no soportada en modo '{self.global_mode}'."
            elif action_type == "DB_SEARCH":
                translated_output["executable_command"] = {
                    "type": "CALL_INTERNAL_DB_FUNCTION",
                    "query_template": action["template"],
                    "parameters": params
                }
                translated_output["message"] = f"Se realizará una búsqueda en la base de conocimiento interna."

            elif action_type == "SYSTEM_LOG":
                translated_output["executable_command"] = {
                    "type": "INTERNAL_LOG",
                    "level": member.upper(),
                    "message": action["template"]
                }
                translated_output["message"] = f"Mensaje de registro: {member.upper()}."

            elif action_type == "CONTEXT_SET":
                translated_output["executable_command"] = {
                    "type": "SET_CONTEXT_VARIABLE",
                    "var_name": member,
                    "value": params.get("VALUE")
                }
                translated_output["message"] = f"Contexto de usuario actualizado."

            elif action_type == "SYSTEM_COMMAND": # REBOOT, SHUTDOWN
                if self.global_mode in ["CLI", "DESKTOP"]:
                    command_map = {
                        "REBOOT": "sudo reboot now",
                        "SHUTDOWN": "sudo shutdown now"
                    }
                    translated_output["executable_command"] = command_map.get(member)
                    translated_output["needs_confirmation"] = self.require_confirmation
                    translated_output["message"] = f"Se ha solicitado la acción de sistema '{member}'. Requiere confirmación."
                else:
                    translated_output["error"] = f"Acción de sistema '{action_type}' no válida en modo '{self.global_mode}'."

            elif action_type == "SYSTEM_COMMAND_DYNAMIC": # RUN_COMMAND
                if self.global_mode in ["CLI", "DESKTOP"]:
                    command_to_run = params.get("COMMAND")
                    if command_to_run:
                        translated_output["executable_command"] = f"bash -c {shlex.quote(command_to_run)}"
                        translated_output["needs_confirmation"] = self.require_confirmation
                        translated_output["message"] = f"Se propone ejecutar el comando: '{command_to_run}'. Requiere confirmación."
                    else:
                        translated_output["error"] = "RUN_COMMAND no especifica un comando."
                else:
                    translated_output["error"] = f"Ejecución de comando de sistema dinámico '{action_type}' no válida en modo '{self.global_mode}'."

            elif action_type == "JAVASCRIPT_EXECUTION":
                js_function = params.get("FUNCTION")
                js_script_output = ""
                
                if self.global_mode != "WEB":
                    translated_output["error"] = f"Acción '{action_type}' no válida en modo '{self.global_mode}'."
                else:
                    if js_function == "alert":
                        message = json.dumps(params.get("MESSAGE", ""))
                        js_script_output = f"alert({message});"
                    elif js_function == "console.log":
                        message = json.dumps(params.get("MESSAGE", ""))
                        js_script_output = f"console.log({message});"
                    elif js_function == "redirect":
                        url = json.dumps(params.get("URL", ""))
                        js_script_output = f"window.location.href = {url};"
                    elif js_function == "set_element_text":
                        element_id = json.dumps(params.get("ELEMENT_ID", ""))
                        text = json.dumps(params.get("TEXT", ""))
                        js_script_output = f"document.getElementById({element_id}).innerText = {text};"
                    elif js_function == "custom_script":
                        js_script_output = params.get("SCRIPT", "")
                        translated_output["needs_confirmation"] = self.require_confirmation
                        if not js_script_output:
                            translated_output["error"] = "custom_script requiere el parámetro 'SCRIPT'."
                    else:
                        translated_output["error"] = f"Función JavaScript desconocida: '{js_function}'."
                    
                    translated_output["executable_command"] = js_script_output
                    translated_output["message"] = f"Se ha generado un script JavaScript para '{js_function}'."

            elif action_type == "FILE_SYSTEM_READ": # LIST_DIRECTORY, READ_FILE
                if self.global_mode in ["CLI", "DESKTOP"]:
                    path = params.get("PATH")
                    if path:
                        quoted_path = shlex.quote(path)
                        if member == "LIST_DIRECTORY":
                            detail_flag = "-la" if params.get("DETAIL") else ""
                            translated_output["executable_command"] = f"ls {detail_flag} {quoted_path}".strip()
                            translated_output["message"] = f"Se listará el contenido de: '{path}'."
                            translated_output["needs_confirmation"] = self.require_confirmation
                        elif member == "READ_FILE":
                            translated_output["executable_command"] = f"cat {quoted_path}"
                            translated_output["message"] = f"Se leerá el archivo: '{path}'."
                            translated_output["needs_confirmation"] = self.require_confirmation
                    else:
                        translated_output["error"] = f"Acción '{member}' requiere el parámetro 'PATH'."
                else:
                    translated_output["error"] = f"Acción de sistema de archivos '{action_type}' no válida en modo '{self.global_mode}'."

            elif action_type == "FILE_SYSTEM_WRITE": # WRITE_FILE
                if self.global_mode in ["CLI", "DESKTOP"]:
                    path = params.get("PATH")
                    content = params.get("CONTENT")
                    content = content.replace('"""', '"""')
                    content = content.replace('\\n', '\n')  #  ← Testing
                    overwrite = params.get("OVERWRITE", False)
                    
                    if path and content is not None:
                        quoted_path = shlex.quote(path)
                        heredoc_delimiter = "EOF_OSIRIS_CONTENT"
                        redirect_operator = ">" if overwrite else ">>"
                        
                        command_string = f"cat {redirect_operator} {quoted_path} <<'{heredoc_delimiter}'\n{content}\n{heredoc_delimiter}"
                        
                        translated_output["executable_command"] = command_string
                        translated_output["needs_confirmation"] = self.require_confirmation
                        translated_output["message"] = f"Se propone escribir en el archivo: '{path}'. Requiere confirmación."
                    else:
                        translated_output["error"] = "WRITE_FILE requiere PATH y CONTENT."
                else:
                    translated_output["error"] = f"Acción de sistema de archivos '{action_type}' no válida en modo '{self.global_mode}'."

            else:
                translated_output["error"] = f"Tipo de acción desconocido o no implementado para traducción: '{action_type}'."

        except Exception as e:
            translated_output["error"] = f"Error inesperado durante la traducción de {action['group_name']}->{action['member']}: {e}"
            self.translation_errors.append(translated_output["error"])

        return translated_output

    def translate_all_actions(self, parsed_actions: list) -> list:
        """
        Traduce una lista de acciones CRO parseadas.
        """
        all_translated = []
        for action in parsed_actions:
            all_translated.append(self.translate_action(action))
        return all_translated

    def get_errors(self) -> list:
        """Devuelve los errores encontrados durante la traducción.\\"""
        return self.translation_errors





accr = ["Se añadió la salida al contexto. El usuario omitió añadir mensaje a esta acción.",
        "Se añadió la salida al contexto. El usuario solicitó dejar un mensaje añadido a la salidad de la ejecución del comando anterior.",
        "No se añadió salida al contexto y el usuario omitió dejar mensaje.",
        "No se añadió la salida al contexto. El usuario solicitó dejar un mensaje a la ejecución del comando anterior."]
             
options_add_context_confirm = """
    ______________________________________________
   |                                              |
   |     Opciones Añadir Salida al Contexto.      |
   |                                              |
   |  1) Añandir salida al contexto y continuar   |
   |  2)      (1 + Añadir mensaje)                |
   |  3) No añadir salida al contexto y continuar | 
   |  4)      (3 + añadir mensaje)                |
   |______________________________________________|

"""




def stdout_to_context():
    global accr, options_add_context_confirm
    """
    Solicita al usuario un numero y lo devuelve como entero.
    Maneja entradas no numericas.
    """
    while True:
        try:
            entrada = input(options_add_context_confirm)
            numero = int(entrada)
            return numero
        except ValueError:
            print("Esa no es una entrada valida. Por favor, introduce solo numeros.")



# --- FUNCIÓN MAIN MODIFICADA PARA EJECUCIÓN SUPERVISADA ---
def main(ai_response_text: str, global_mode: str = "CLI"):

    global accr

    # IMPORTANTE: osiris_definitions ya se importa al inicio de este archivo
    # por lo tanto, está disponible en este scope.

#    print(f"\n--- Iniciando Proceso CRO para el modo: {global_mode.upper()} ---")
#    print(f"Contenido recibido (inicio):\n'{ai_response_text[:200]}{'...' if len(ai_response_text) > 200 else ''}'\n")

    # Instanciación de CROParser: No necesita osiris_definitions como argumento
    parser = CROParser()

    parsed_actions = parser.parse(ai_response_text)

#    print("\n--- Resultados del Parseo CRO ---")
    if parser.errors:
        print("❌ ERRORES DE PARSEO DETECTADOS:")
        for err in parser.errors:
            print(f"  - {err}")
    if parser.warnings:
        print("⚠️ ADVERTENCIAS DE PARSEO DETECTADAS:")
        for warn in parser.warnings:
            print(f"  - {warn}")
    
    if not parsed_actions:
        print("➡️ No se encontraron acciones CRO válidas para procesar.")
        return {} #Devuelve un diccionario vacío

#    print("\n--- Acciones CRO Válidas Encontradas ---")
    # print(json.dumps(parsed_actions, indent=4)) # Para depuración detallada del parseo

    translator = CROTranslator(global_mode=global_mode)
    translated_actions = translator.translate_all_actions(parsed_actions)

#    print("\n--- Traducción de Acciones CRO a Comandos Ejecutables ---")
    if translator.get_errors():
        print("❌ ERRORES DE TRADUCCIÓN DETECTADOS:")
        for err in translator.get_errors():
            print(f"  - {err}")

    final_output_messages = []
    if not translated_actions and not translator.get_errors():
        print("➡️ Ninguna acción CRO pudo ser traducida (posiblemente debido a errores de parseo previos o incompatibilidad de modo).")
    
    system_execution_context = {} 

    for i, action in enumerate(translated_actions):
        print(f"\n--- Procesando Acción Traducida #{i+1} ---")
        print(f"  Grupo: {action['group']}")
        print(f"  Miembro: {action['member']}")
        print(f"  Tipo de Acción: {action['action_type']}")
        print(f"  Contexto de Ejecución: {action['execution_context']}")

        if action['error']:
            print(f"  🚫 ERROR en Traducción: {action['error']}")
            final_output_messages.append(f"ERROR: No se pudo traducir la acción {action['group']}->{action['member']}: {action['error']}")
            continue

        print(f"  Mensaje para el Usuario: {action['message']}")
        
        command_to_execute = action['executable_command']
        
        if action['needs_confirmation'] and isinstance(command_to_execute, str):
            print(f"\n💬 Comando propuesto para ejecución:")
            print(f"   >>> {command_to_execute}")
            
            user_confirm = input("¿Deseas ejecutar este comando? (si/no): ").lower().strip()
            if user_confirm == "si":
                print("✅ Confirmación recibida. Ejecutando comando...")
                try:
                    result = subprocess.run(
                        command_to_execute, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        check=False 
                    )
                    
                    command_output = result.stdout.strip()
                    command_error = result.stderr.strip()

                    if result.returncode == 0:
                        print(f"👍 Comando ejecutado exitosamente.")
                        if command_output:
                            print("\n--- Salida del comando ---")
                            print("COMOUT :",command_output)
                            print("""              """)
#add_context_confirm = add_cc()
                            while True:
                                valor_obtenido = stdout_to_context() # Llama a la funcion
                                if 1 <= valor_obtenido <= 5:
                                    print(f" Seleccionado: {valor_obtenido} ")
                                    if valor_obtenido == 2 or valor_obtenido == 4:
                                        msg = input("""
               Introduzca a continuación su mensaje:
                                        """)
                                    else:
                                        msg = """
                                        El Usuario NO introdujo Comentario-                                    
                                        """
                                    msgF = accr[valor_obtenido - 1] + msg
                                    print("ADD_TO_CONTEX:")
                                    #print(msg)
                                    MSG = """
                                    #SALIDA DEL COMANDO:
                                    #----------------------

                                    """+command_output+"""
                                    #----------------------
                                    #FIN SALIDA DEL COMANDO
                                    #----------------------
                                    """+msgF+"""
                                    -----------------------
                                    """
                                    print(MSG)                                    
                                    system_execution_context[f"output_{action['group']}_{action['member']}_{int(time.time())}"] = MSG
                                    break # Sale del bucle porque la condicion se cumple
                                else:
                                    print(f"El valor {valor_obtenido} no esta entre 1 y 5. Por favor, intentelo de nuevo.")
                    else:
                        print(f"👎 El comando falló con código de salida {result.returncode}.")
                        if command_output:
                            print("\n--- Salida del comando (stdout) ---")
                            print(command_output)
                        if command_error:
                            print("\n--- Salida de error del comando (stderr) ---")
                            print(command_error)
                        system_execution_context[f"error_output_{action['group']}_{action['member']}_{int(time.time())}"] = {"stdout": command_output, "stderr": command_error, "returncode": result.returncode}
                        print("\n(Salida/Error añadidos al contexto de Osiris.)")
                        #return command_error # RETORNA ERROR
                except FileNotFoundError:
                    print(f"❌ Error: El interprete de shell (ej. bash) no se encontró. Asegúrate de que Bash esté disponible en tu PATH.")
                    final_output_messages.append(f"ERROR de ejecución: Intérprete de shell no encontrado para {action['group']}->{action['member']}.")
                except Exception as exec_e:
                    print(f"❌ Error inesperado al ejecutar el comando: {exec_e}")
                    final_output_messages.append(f"ERROR de ejecución: {exec_e} para {action['group']}->{action['member']}.")
            else:
                print("🚫 Ejecución cancelada por el usuario.")
                cancelby = input("Introduce el motivo por el que cancelaste la acción: \n")
                if cancelby:
                    system_execution_context[f"error_output_{action['group']}_{action['member']}_{int(time.time())}"] = {"stderr": "USER CANCEL HUMANO DICE: "+cancelby, "stdout": "HUMAN CANCEL OPERATION", "returncode": 666}
                else:
                    system_execution_context[f"error_output_{action['group']}_{action['member']}_{int(time.time())}"] = {"stderr": "USER CANCEL INPUT CONFIRM ACTION FUE CANCELADO SIN EXPLICAR MOTIVOS", "stdout": "HUMAN", "returncode": 666}
                final_output_messages.append(f"Acción '{action['group']}->{action['member']}' cancelada por el usuario.")
                
        else: # No necesita confirmación o no es un comando de shell (ej. dict para WEB mode fetch)
            print(f"  Comando/Directriz a Ejecutar:")
            if isinstance(command_to_execute, dict):
                print(f"    {json.dumps(command_to_execute, indent=2)}")
            else:
                print(f"    `{command_to_execute}`")
            
            if action['action_type'] == "URL_SEARCH":
                print(f"  (Simulando apertura de URL en el navegador o curl silencioso...)")
            elif action['action_type'] == "DB_SEARCH":
                print(f"  (Simulando búsqueda en la base de datos interna...)")
            elif action['action_type'] == "SYSTEM_LOG":
                print(f"  (Registrando mensaje en los logs de Osiris...)")
            elif action['action_type'] == "CONTEXT_SET":
                print(f"  (Actualizando el contexto interno de Osiris...)")
                system_execution_context[action['executable_command']['var_name']] = action['executable_command']['value']
            elif action['action_type'] == "JAVASCRIPT_EXECUTION" and self.global_mode == "WEB":
                 print(f"  (Simulando ejecución de JavaScript en el navegador...)")
            elif action['action_type'] == "FILE_SYSTEM_READ":
                 print(f"  (Simulando lectura de archivo/directorio...)")
                 if isinstance(command_to_execute, str):
                     try:
                        result = subprocess.run(
                            command_to_execute, 
                            shell=True, 
                            capture_output=True, 
                            text=True, 
                            check=False
                        )
                        if result.returncode == 0:
                            print("\n--- Salida de lectura ---")
                            print(result.stdout.strip())
                            system_execution_context[f"fs_read_output_{action['member']}_{int(time.time())}"] = result.stdout.strip()
                            print("\n(Salida añadida al contexto de Osiris.)")
                        else:
                            print(f"👎 La lectura falló con código de salida {result.returncode}.")
                            print(f"Stderr: {result.stderr.strip()}")
                            system_execution_context[f"fs_read_error_{action['member']}_{int(time.time())}"] = {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "returncode": result.returncode}
                     except Exception as e:
                         print(f"❌ Error en lectura de archivo/directorio: {e}")
                 else:
                     print(" (No se pudo ejecutar la lectura: comando no es string.)")

            if action['post_processing_hint']:
                print(f"  Pista Post-Procesamiento: {action['post_processing_hint']}")
            
            final_output_messages.append(f"✔️ Acción '{action['group']}->{action['member']}' procesada (simulada/directa) exitosamente.")

#    print("\n--- Resumen del Proceso CRO ---")
    if final_output_messages:
        for msg in final_output_messages:
            print(msg)
    else:
        print("No se generaron mensajes de resumen.")
    
#    print("\n--- Contenido de Contexto Acumulado (simulado) ---")
    #print(json.dumps(system_execution_context, indent=2))
    print("\n--- Proceso CRO Finalizado ---")
    return system_execution_context
