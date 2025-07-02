import re
import json
import urllib.parse
import time
import shlex
import subprocess

# osiris_definitions.py - Definiciones completas y corregidas para Python
INFO = """
Module Cro Parser Info
Osiris internal python library
"""

osiris_definitions = {
    "GLOBAL_MODE": {
        "TYPE":["CLI","WEB","DESKTOP"]
    },
    "COMMAND_GROUPS": {
        "SEARCH_IN": ["GOOGLE", "BING", "OSIRIS_INTERNAL"],
        "LOG_OSIRIS": ["INFO", "WARN", "ERROR"],
        "DEFINE_VAR": ["USER_QUERY_SUMMARY", "TEMP_DATA"],
        "EXECUTE_SYSTEM_ACTION": ["REBOOT", "SHUTDOWN", "RUN_COMMAND"],
        "LOCAL_FS": ["LIST_DIRECTORY", "READ_FILE", "WRITE_FILE"],
        "WEB_MODE": ["JS"]
    },
    "PROTO_DEFINITIONS": {
        "WEB_MODE": { # ¡CORREGIDO Y AMPLIADO!
            "JS": {
                "DESCRIPTION": "Ejecuta comandos JavaScript en el entorno web del navegador.",
                "ACTION_TYPE": "JAVASCRIPT_EXECUTION",
                "PARAMETERS": {
                    "FUNCTION": {
                        "TYPE": "enum",
                        "VALUES": ["alert", "console.log", "redirect", "set_element_text", "custom_script"],
                        "REQUIRED": True,
                        "DYNAMIC": True
                    },
                    "MESSAGE": {
                        "TYPE": "string",
                        "REQUIRED": False,
                        "DYNAMIC": True,
                        "DEFAULT": ""
                    },
                    "URL": {
                        "TYPE": "string",
                        "REQUIRED": False,
                        "DYNAMIC": True,
                        "DEFAULT": ""
                    },
                    "ELEMENT_ID": {
                        "TYPE": "string",
                        "REQUIRED": False,
                        "DYNAMIC": True,
                        "DEFAULT": ""
                    },
                    "TEXT": {
                        "TYPE": "string",
                        "REQUIRED": False,
                        "DYNAMIC": True,
                        "DEFAULT": ""
                    },
                    "SCRIPT": {
                        "TYPE": "string",
                        "REQUIRED": False,
                        "DYNAMIC": True,
                        "DEFAULT": ""
                    }
                }
            }
        },
        "SEARCH_IN": {
            "GOOGLE": {
                "DESCRIPTION": "Busca información en Google.",
                "URL_TEMPLATE": "https://www.google.com/search?q={QUERY}&tbm={TYPE}",
                "ACTION_TYPE": "URL_SEARCH",
                "PARAMETERS": {
                    "QUERY": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True, "DEFAULT": "" },
                    "TYPE": {
                        "TYPE": "enum",
                        "VALUES": ["text", "image", "video", "pdf"],
                        "DEFAULT": "text",
                        "DYNAMIC": True,
                        "ALLOW_MULTIPLE": True,
                        "ACTION_PER_VALUE": True
                    }
                }
            },
            "BING": {
                "DESCRIPTION": "Busca información en Bing.",
                "URL_TEMPLATE": "https://www.bing.com/search?q={QUERY}&form={TYPE}",
                "ACTION_TYPE": "URL_SEARCH",
                "PARAMETERS": {
                    "QUERY": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True, "DEFAULT": "" },
                    "TYPE": {
                        "TYPE": "enum",
                        "VALUES": ["text", "image", "video"],
                        "DEFAULT": "text",
                        "DYNAMIC": True,
                        "ALLOW_MULTIPLE": True,
                        "ACTION_PER_VALUE": True
                    }
                }
            },
            "OSIRIS_INTERNAL": {
                "DESCRIPTION": "Busca en la base de conocimiento interna de Osiris.",
                "DB_QUERY_TEMPLATE": "SELECT content FROM internal_kb WHERE tags LIKE '%{TAGS}%' AND query LIKE '%{QUERY}%'",
                "ACTION_TYPE": "DB_SEARCH",
                "PARAMETERS": {
                    "QUERY": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True, "DEFAULT": "" },
                    "TAGS": { "TYPE": "string", "REQUIRED": False, "DYNAMIC": True, "DEFAULT": "" }
                }
            }
        },
        "LOG_OSIRIS": {
            "INFO": {
                "DESCRIPTION": "Registra un mensaje informativo en los logs del sistema Osiris.",
                "LOG_TEMPLATE": "[INFO] AI_LOG: {MESSAGE}",
                "ACTION_TYPE": "SYSTEM_LOG",
                "PARAMETERS": {
                    "MESSAGE": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True }
                }
            },
            "WARN": {
                "DESCRIPTION": "Registra una advertencia en los logs del sistema Osiris.",
                "LOG_TEMPLATE": "[WARN] AI_WARNING: {MESSAGE}",
                "ACTION_TYPE": "SYSTEM_LOG",
                "PARAMETERS": {
                    "MESSAGE": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True }
                }
            },
            "ERROR": {
                "DESCRIPTION": "Registra un error crítico en los logs del sistema Osiris.",
                "LOG_TEMPLATE": "[ERROR] AI_ERROR: {MESSAGE}",
                "ACTION_TYPE": "SYSTEM_LOG",
                "PARAMETERS": {
                    "MESSAGE": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True }
                }
            }
        },
        "DEFINE_VAR": {
            "USER_QUERY_SUMMARY": {
                "DESCRIPTION": "Define un resumen de la consulta del usuario para contexto.",
                "SCOPE": "CONTEXT_PERMANENT",
                "ACTION_TYPE": "CONTEXT_SET",
                "PARAMETERS": {
                    "VALUE": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True }
                }
            },
            "TEMP_DATA": {
                "DESCRIPTION": "Almacena datos temporales para el contexto de la sesión actual.",
                "SCOPE": "CONTEXT_SESSION",
                "ACTION_TYPE": "CONTEXT_SET",
                "PARAMETERS": {
                    "KEY": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True },
                    "VALUE": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True }
                }
            }
        },
        "EXECUTE_SYSTEM_ACTION": {
            "REBOOT": {
                "DESCRIPTION": "Reinicia el sistema.",
                "ACTION_TYPE": "SYSTEM_COMMAND",
                "PARAMETERS": {}
            },
            "SHUTDOWN": {
                "DESCRIPTION": "Apaga el sistema.",
                "ACTION_TYPE": "SYSTEM_COMMAND",
                "PARAMETERS": {}
            },
            "RUN_COMMAND": {
                "DESCRIPTION": "Ejecuta un comando arbitrario en la terminal del sistema (ej. Bash).",
                "ACTION_TYPE": "SYSTEM_COMMAND_DYNAMIC",
                "PARAMETERS": {
                    "COMMAND": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True }
                }
            }
        },
        "LOCAL_FS": {
            "LIST_DIRECTORY": {
                "DESCRIPTION": "Lista el contenido de un directorio especificado.",
                "ACTION_TYPE": "FILE_SYSTEM_READ",
                "PARAMETERS": {
                    "PATH": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True }
                }
            },
            "READ_FILE": {
                "DESCRIPTION": "Lee el contenido de un archivo.",
                "ACTION_TYPE": "FILE_SYSTEM_READ",
                "PARAMETERS": {
                    "PATH": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True },
                    "ENCODING": { "TYPE": "enum", "VALUES": ["utf-8", "latin-1"], "DEFAULT": "utf-8", "REQUIRED": False },
                    "FLAGS": { # ¡NUEVO PARÁMETRO!
                        "TYPE": "enum",
                        "VALUES": ["WRITE_CONTEXT"], # ¡Nuevo valor de bandera!
                        "REQUIRED": False,
                        "DEFAULT": "",
                        "ALLOW_MULTIPLE": True, # Puede que en el futuro haya más banderas
                        "ACTION_PER_VALUE": True # Cada bandera puede disparar una acción específica
                    }
                }
            },
            "WRITE_FILE": {
                "DESCRIPTION": "Escribe contenido en un archivo o crea uno nuevo. Requiere confirmación del usuario.",
                "ACTION_TYPE": "FILE_SYSTEM_WRITE",
                "PARAMETERS": {
                    "PATH": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True },
                    "CONTENT": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True },
                    "OVERWRITE": { "TYPE": "boolean", "DEFAULT": False, "REQUIRED": False, "DYNAMIC": True }, # <--- ¡CAMBIO CRÍTICO AQUÍ!
                    "ENCODING": { "TYPE": "enum", "VALUES": ["utf-8", "latin-1"], "DEFAULT": "utf-8", "REQUIRED": False, "DYNAMIC": True } # <--- ¡CAMBIO CRÍTICO AQUÍ!
                }
            }
        }
    }
}


class CROParser:
    def __init__(self, osiris_definitions):
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
        
        if group_name not in self.osiris_definitions["PROTO_DEFINITIONS"] or \
           target_member not in self.osiris_definitions["PROTO_DEFINITIONS"][group_name]:
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
            current_raw_cro_lines = [] # Colecta todas las líneas para el comando actual

            # Heredoc state variables (for <<<DELIMITER)
            in_heredoc_mode = False
            heredoc_var_name = None
            heredoc_delimiter = None
            heredoc_content_buffer = []

            # Triple-quote state variables (for """...""")
            in_triple_quote_mode = False
            triple_quote_var_name = None
            triple_quote_content_buffer = []

            # Nueva función auxiliar para procesar el comando actual y resetear el estado
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
                            action["raw_cro_lines"] = list(current_raw_cro_lines) # Captura las líneas raw del comando
                            self.parsed_actions.append(action)
                
                # Reiniciar para el siguiente comando
                current_group_name = None
                current_targets = []
                current_params = {}
                current_raw_cro_lines = []

            for line_idx, line in enumerate(lines):
                clean_line = line.rstrip('\r\n') # Elimina solo saltos de línea al final

                # --- Prioridad 1: Manejar estados de contenido multilínea (Triple-Quote """ o Heredoc <<<) ---
                # Si ya estamos en modo triple comilla
                if in_triple_quote_mode:
                    current_raw_cro_lines.append(clean_line) # Añadir línea al buffer de líneas raw
                    if clean_line.strip() == '"""': # Si encontramos la comilla de cierre
                        current_params[triple_quote_var_name] = "\n".join(triple_quote_content_buffer)
                        in_triple_quote_mode = False
                        triple_quote_var_name = None
                        triple_quote_content_buffer = []
                    else:
                        triple_quote_content_buffer.append(clean_line) # Si es contenido, añadir al buffer de contenido
                    continue # Siempre continuar si estamos en modo multilínea, hasta encontrar el delimitador

                # Si ya estamos en modo heredoc
                if in_heredoc_mode:
                    current_raw_cro_lines.append(clean_line) # Añadir línea al buffer de líneas raw
                    if clean_line.strip() == heredoc_delimiter:
                        current_params[heredoc_var_name] = "\n".join(heredoc_content_buffer)
                        in_heredoc_mode = False
                        heredoc_var_name = None
                        heredoc_delimiter = None
                        heredoc_content_buffer = []
                    else:
                        heredoc_content_buffer.append(clean_line)
                    continue

                # --- Prioridad 2: No estamos en modo multilínea, buscar nuevos iniciadores/parámetros ---
                stripped_line = clean_line.strip()
                if not stripped_line: # Saltar líneas vacías fuera de bloques multilínea
                    continue
                
                # 1. Intentar hacer coincidir un Iniciador de Comando (ej. LOCAL_FS_* WRITE_FILE)
                initiator_match = re.match(r"^([A-Z_]+)\_\* (.+)$", stripped_line)
                if initiator_match:
                    _process_current_command_group() # <--- ¡AHORA SOLO AQUÍ! Procesa el comando anterior
                    
                    group_name = initiator_match.group(1)
                    members_str = initiator_match.group(2)
                    
                    if group_name not in self.osiris_definitions["COMMAND_GROUPS"]:
                        self._log_error(f"Unknown command group '{group_name}' in line: '{stripped_line}'")
                        # No se establecen current_group_name, etc., si el grupo es inválido.
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
                    current_params = {} # Resetear parámetros para el nuevo comando
                    current_raw_cro_lines.append(clean_line) # Añadir esta línea iniciadora a las líneas raw

                # 2. Intentar hacer coincidir el inicio de un parámetro con triple comilla (ej. CONTENT=""", o CONTENT="""some code)
                # CAMBIO CLAVE AQUÍ: Aceptar cualquier cosa después de """ en la misma línea
                elif (triple_quote_start_match := re.match(r"^([A-Z_]+)=\"\"\"(.*)$", stripped_line)):
                    if not current_group_name or not current_targets:
                        self._log_error(f"Triple-quoted parameter line '{stripped_line}' found without a preceding initiator line (command). Ignoring.")
                        continue

                    param_name_for_triple_quote = triple_quote_start_match.group(1)
                    # Contenido inmediatamente después de """ en la misma línea
                    initial_content_on_same_line = triple_quote_start_match.group(2)

                    in_triple_quote_mode = True # Asumimos que el bloque empieza
                    triple_quote_var_name = param_name_for_triple_quote
                    triple_quote_content_buffer = []

                    # Manejar el caso donde el contenido Y el """ de cierre están en la misma línea
                    # Ejemplo: CONTENT="""Hello world"""
                    if initial_content_on_same_line.strip().endswith('"""'):
                        # Extraer el contenido real eliminando el """ de cierre
                        content_found = initial_content_on_same_line.strip()[:-3].rstrip()
                        current_params[triple_quote_var_name] = content_found
                        
                        in_triple_quote_mode = False # El bloque se ha cerrado en la misma línea
                        triple_quote_var_name = None
                        # No es necesario limpiar el buffer, ya que se usó y se reiniciará para el siguiente comando
                    else:
                        # Si el contenido empezó en la misma línea pero no hay """ de cierre
                        if initial_content_on_same_line:
                            triple_quote_content_buffer.append(initial_content_on_same_line)

                    current_raw_cro_lines.append(clean_line) # Añadir esta línea a las líneas raw
                    continue # IMPORTANT: Después de procesar el inicio, pasar a la siguiente línea para buscar más contenido o el delimitador de cierre
                    
                # 3. Intentar hacer coincidir un Iniciador de Heredoc (ej. CONTENT=<<<DELIMITER)
                elif re.match(r"^([A-Z_]+)=<<<([A-Z_]+)$", stripped_line):
                    # <--- ¡NO LLAMAR A _process_current_command_group() AQUÍ! Esto es un PARÁMETRO.
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
                    heredoc_content_buffer = [] # Limpiar buffer para nuevo heredoc
                    current_raw_cro_lines.append(clean_line) # Añadir esta línea a las líneas raw
                    continue
                    
                # 4. Intentar hacer coincidir una Línea de Parámetro normal (ej. PARAMETER="value")
                elif re.match(r"^([A-Z_]+)=\"(.*?)\"$", stripped_line):
                    # <--- ¡NO LLAMAR A _process_current_command_group() AQUÍ! Esto es un PARÁMETRO.
                    param_match = re.match(r"^([A-Z_]+)=\"(.*?)\"$", stripped_line)
                    if not current_group_name or not current_targets:
                        self._log_error(f"Parameter line '{stripped_line}' found without a preceding initiator line (command). Ignoring.")
                        continue
                    
                    param_name = param_match.group(1)
                    param_value = param_match.group(2)
                    current_params[param_name] = param_value
                    current_raw_cro_lines.append(clean_line) # Añadir línea de parámetro a las líneas raw
                
                else:
                    # Línea no reconocida como iniciador, inicio/fin de multilínea, o parámetro
                    self._log_warning(f"Unrecognized CRO syntax or misplaced line: '{stripped_line}'. Skipping.")
            
            # Después de iterar por todas las líneas del bloque, procesar cualquier acción pendiente final
            _process_current_command_group()
            
            # Comprobar si hay bloques multilínea sin cerrar al final de un bloque CRO
            if in_heredoc_mode:
                self._log_error(f"Heredoc for variable '{heredoc_var_name}' started with delimiter '{heredoc_delimiter}' was not closed correctly within the CRO block.")
            if in_triple_quote_mode:
                 self._log_error(f"Triple-quoted block for variable '{triple_quote_var_name}' was not closed correctly within the CRO block.")

        return self.parsed_actions


class CROTranslator:
    def __init__(self, global_mode: str, require_confirmation_for_dangerous_actions: bool = True):
        """
        Inicializa el traductor CRO.
        :param global_mode: El modo de operación actual del sistema (ej. "CLI", "WEB", "DESKTOP").
        :param require_confirmation_for_dangerous_actions: Si es True, las acciones peligrosas
                                                          (ej. escribir archivos, ejecutar comandos)
                                                          marcarán la necesidad de confirmación.
        """
        self.global_mode = global_mode.upper() # Asegurar que sea mayúscula para consistencia
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
            "needs_confirmation": False, # Valor por defecto
            "executable_command": None,  # ¡Ahora contendrá el comando Bash/JS/directriz lista para ejecutar!
            "message": None,             # Mensaje opcional para el usuario o logs
            "post_processing_hint": None, # Nueva pista para el post-procesamiento (ej. limpieza HTML)
            "error": None                # Si ocurre un error en la traducción
        }

        try:
            # Recuperamos los parámetros ya validados por el parser
            params = action["parameters"]
            action_type = action["action_type"]
            member = action["member"]

            # --- TRADUCCIONES CONCRETAS A COMANDOS REALES ---

            if action_type == "URL_SEARCH":
                # Para CLI/DESKTOP, generamos un comando 'curl' o 'wget'
                if self.global_mode in ["CLI", "DESKTOP"]:
                    url = action["template"] # La URL ya viene formateada y codificada desde el parser
                    # Usamos shlex.quote para asegurar que la URL sea un argumento seguro para el shell.
                    quoted_url = shlex.quote(url)
                    
                    # Generamos el comando curl. '-sL' significa silencioso y seguir redirecciones.
                    translated_output["executable_command"] = f"curl -sL {quoted_url}"
                    translated_output["message"] = f"Se realizará una búsqueda web en {action['group_name']} y se recuperará el contenido."
                    translated_output["post_processing_hint"] = "El contenido recuperado (HTML) puede requerir limpieza/parsing para extraer información."
                elif self.global_mode == "WEB":
                    # En modo WEB, una búsqueda URL podría disparar un `fetch` JS o una API de backend.
                    # Aquí la representamos como una directriz interna para el frontend o backend.
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
                # Esto es una búsqueda interna, no un comando de shell/JS directo.
                # Se traducirá a una llamada a función interna de Python que interactúe con la DB.
                translated_output["executable_command"] = {
                    "type": "CALL_INTERNAL_DB_FUNCTION",
                    "query_template": action["template"], # La query ya viene formateada
                    "parameters": params # Parámetros originales para depuración si es necesario
                }
                translated_output["message"] = f"Se realizará una búsqueda en la base de conocimiento interna."

            elif action_type == "SYSTEM_LOG":
                # Directriz para el sistema de logging de Osiris. No es un comando ejecutable externo.
                translated_output["executable_command"] = {
                    "type": "INTERNAL_LOG",
                    "level": member.upper(),
                    "message": action["template"] # El mensaje de log ya formateado
                }
                translated_output["message"] = f"Mensaje de registro: {member.upper()}."

            elif action_type == "CONTEXT_SET":
                # Directriz para el motor de gestión de contexto de Osiris.
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
                        # 🔒 SEGURIDAD CRÍTICA: Escapar el comando para evitar inyección de shell.
                        # `shlex.quote` es fundamental aquí.
                        # Utilizamos `bash -c` para asegurar que el comando se ejecute a través de Bash,
                        # permitiendo redirecciones, pipes, etc., y que el comando en sí mismo esté entre comillas.
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
                    # Usamos json.dumps para escapar correctamente las strings dentro del JS
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
                        # ⚠️ MUY PELIGROSO: Permite ejecutar cualquier JS. Requiere un sandbox muy seguro.
                        js_script_output = params.get("SCRIPT", "")
                        translated_output["needs_confirmation"] = self.require_confirmation # Siempre confirmar
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
                        # Escapar la ruta para el shell.
                        quoted_path = shlex.quote(path)
                        if member == "LIST_DIRECTORY":
                            translated_output["executable_command"] = f"ls -la {quoted_path}"
                            translated_output["message"] = f"Se listará el contenido de: '{path}'."
                            translated_output["needs_confirmation"] = self.require_confirmation # Aunque es lectura, por precaución y coherencia con la propuesta
                        elif member == "READ_FILE":
                            translated_output["executable_command"] = f"cat {quoted_path}" # 'cat' es un comando directo de lectura
                            translated_output["message"] = f"Se leerá el archivo: '{path}'."
                            translated_output["needs_confirmation"] = self.require_confirmation # Aunque es lectura, por precaución y coherencia con la propuesta
                    else:
                        translated_output["error"] = f"Acción '{member}' requiere el parámetro 'PATH'."
                else:
                    translated_output["error"] = f"Acción de sistema de archivos '{action_type}' no válida en modo '{self.global_mode}'."


            elif action_type == "FILE_SYSTEM_WRITE": # WRITE_FILE
                if self.global_mode in ["CLI", "DESKTOP"]:
                    path = params.get("PATH")
                    content = params.get("CONTENT")
                    # Esta línea sigue siendo necesaria si la IA interna (Gemini)
                    # escapa los """ internos a la cadena de texto con \"\"\"
                    content = content.replace('\\"\\"\\"', '"""') # Corregido para reemplazar \"\"\" por el literal """
                    overwrite = params.get("OVERWRITE", False) # Defaults to False if not present
                    
                    if path and content is not None:
                        quoted_path = shlex.quote(path)
                        heredoc_delimiter = "EOF_OSIRIS_CONTENT" # Delimitador para el heredoc de Bash
                        redirect_operator = ">" if overwrite else ">>"
                        
                        # Genera el comando completo con heredoc de Bash
                        # Se usan comillas simples alrededor del delimitador de Bash (ej. <<'DELIMITADOR')
                        # para evitar la expansión de variables dentro del contenido del heredoc por el shell.
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
        """Devuelve los errores encontrados durante la traducción."""
        return self.translation_errors


# --- FUNCIÓN MAIN MODIFICADA PARA EJECUCIÓN SUPERVISADA ---
def main(ai_response_text: str, global_mode: str = "CLI"):
    """
    Función principal para procesar respuestas de la IA que contienen bloques CRO.
    Implementa la ejecución supervisada para comandos de sistema dinámicos y otras acciones
    que requieren confirmación.

    :param ai_response_text: La cadena de texto completa de la respuesta de la IA.
    :param global_mode: El modo de operación actual del sistema (CLI, WEB, DESKTOP).
                        Usado por el traductor para determinar el tipo de comando.
    """
#    print(f"\n--- Iniciando Proceso CRO para el modo: {global_mode.upper()} ---")
#    print(f"Contenido recibido (inicio):\n'{ai_response_text[:200]}{'...' if len(ai_response_text) > 200 else ''}'\n")

    parser = CROParser(osiris_definitions)
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
        return {}  #Devuelve un diccionario vacío

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
                            print(command_output)
                            print("""

_______________________________________________

                                """)
                            add_context_confirm = input("¿Deseas añadir la salida al contexto? (si/no): ").lower().strip()
                            if add_context_confirm == "si":
                                system_execution_context[f"output_{action['group']}_{action['member']}_{int(time.time())}"] = command_output
                                print("\n(Salida añadida al contexto de Osiris para futuras referencias.)")
                            else:
                                print("\n(La salida no se añadió al contexto.)")
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

                except FileNotFoundError:
                    print(f"❌ Error: El interprete de shell (ej. bash) no se encontró. Asegúrate de que Bash esté disponible en tu PATH.")
                    final_output_messages.append(f"ERROR de ejecución: Intérprete de shell no encontrado para {action['group']}->{action['member']}.")
                except Exception as exec_e:
                    print(f"❌ Error inesperado al ejecutar el comando: {exec_e}")
                    final_output_messages.append(f"ERROR de ejecución: {exec_e} para {action['group']}->{action['member']}.")
            else:
                print("🚫 Ejecución cancelada por el usuario.")
                final_output_messages.append(f"Acción '{action['group']}->{action['member']}' cancelada por el usuario.")
        else:
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