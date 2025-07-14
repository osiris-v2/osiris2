import re
import json
import urllib.parse # Necesario para codificar URLs
import time 


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
                    "OVERWRITE": { "TYPE": "boolean", "DEFAULT": False, "REQUIRED": False },
                    "ENCODING": { "TYPE": "enum", "VALUES": ["utf-8", "latin-1"], "DEFAULT": "utf-8", "REQUIRED": False }
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
                    # RE-INCORPORADO: Codificar los valores de los parámetros para URL antes de formatear
                    # Esto es CRUCIAL para manejar espacios y caracteres especiales en URLs y queries de DB
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
                "template": concrete_template, # La plantilla final ya formateada
                "parameters": final_params_set, # Los parámetros originales usados para esta instancia de acción
                "raw_cro_lines": [] # Se llenará en el parser principal
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
            lines = block_content.strip().split('\n')
            
            current_group_name = None
            current_targets = []
            current_params = {}
            current_raw_cro_lines = []

            def _process_pending_actions():
                """Helper para procesar acciones de la última línea iniciadora antes de que empiece una nueva o termine el bloque."""
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
                
                # Reset para el siguiente bloque/iniciador
                current_group_name = None
                current_targets = []
                current_params = {}
                current_raw_cro_lines = []


            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Intentar coincidir con una Línea Iniciadora
                initiator_match = re.match(r"^([A-Z_]+)\_\* (.+)$", line)
                if initiator_match:
                    _process_pending_actions() 
                    current_raw_cro_lines.append(line)

                    group_name = initiator_match.group(1)
                    members_str = initiator_match.group(2)
                    
                    if group_name not in self.osiris_definitions["COMMAND_GROUPS"]:
                        self._log_error(f"Grupo de comando desconocido '{group_name}' en línea: '{line}'")
                        current_raw_cro_lines = [] # Limpiar líneas si el grupo es inválido
                        continue
                    
                    valid_members = []
                    for member in [m.strip() for m in members_str.split(',')]:
                        if member in self.osiris_definitions["COMMAND_GROUPS"][group_name]:
                            valid_members.append(member)
                        else:
                            self._log_warning(f"Miembro inválido '{member}' para el grupo '{group_name}' en línea: '{line}'")
                    
                    if not valid_members:
                        self._log_warning(f"No se encontraron miembros válidos para el grupo '{group_name}' en línea: '{line}'. Saltando iniciador.")
                        current_raw_cro_lines = [] # Limpiar líneas si no hay miembros válidos
                        continue
                    
                    current_group_name = group_name
                    current_targets = valid_members
                    current_params = {} # Reset parámetros para nuevos objetivos

                else:
                    # Intentar coincidir con una Línea de Parámetro
                    param_match = re.match(r"^([A-Z_]+)=\"(.*?)\"$", line)
                    if param_match:
                        if not current_group_name or not current_targets:
                            self._log_error(f"Línea de parámetro '{line}' encontrada sin una línea iniciadora precedente. Ignorando.")
                            continue
                        current_raw_cro_lines.append(line)

                        param_name = param_match.group(1)
                        param_value = param_match.group(2)
                        current_params[param_name] = param_value
                    else:
                        self._log_warning(f"Sintaxis CRO no reconocida en línea: '{line}'. Saltando.")
            
            _process_pending_actions() # Procesar cualquier acción restante después de la última línea del bloque

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
                    translated_output["message"] = f"Se realizará una búsqueda web en {action['group']} y se recuperará el contenido."
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
                        elif member == "READ_FILE":
                            translated_output["executable_command"] = f"cat {quoted_path}" # 'cat' es un comando directo de lectura
                            translated_output["message"] = f"Se leerá el archivo: '{path}'."
                    else:
                        translated_output["error"] = f"Acción '{member}' requiere el parámetro 'PATH'."
                else:
                    translated_output["error"] = f"Acción de sistema de archivos '{action_type}' no válida en modo '{self.global_mode}'."


            elif action_type == "FILE_SYSTEM_WRITE": # WRITE_FILE
                if self.global_mode in ["CLI", "DESKTOP"]:
                    path = params.get("PATH")
                    content = params.get("CONTENT")
                    overwrite = params.get("OVERWRITE", False)
                    
                    if path and content is not None:
                        quoted_path = shlex.quote(path)
                        # Para escribir contenido multilínea o con caracteres especiales de forma segura
                        # en Bash, lo mejor es usar un "heredoc" con `cat`.
                        heredoc_delimiter = "EOF_OSIRIS_CONTENT"
                        # Si `overwrite` es True, usa `>` (sobrescribe), si no, `>>` (añade).
                        redirect_operator = ">" if overwrite else ">>"
                        
                        # Genera el comando completo con heredoc
                        command_string = f"cat {redirect_operator} {quoted_path} <<{heredoc_delimiter}\n{content}\n{heredoc_delimiter}"
                        
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





# --- Prototipo de uso con ejemplos revisados ---

proto_cro_content = """
"""


def main(args):
#    print("--- Proceso de Parseo CRO ---")
#    print("args:",args)
    print(args)

    parser = CROParser(osiris_definitions)

    print("PARSER:",parser)
    parsed_results = parser.parse(args)


    if parsed_results:
        #print("Disabled jsondumps")    
        print(json.dumps(parsed_results, indent=4))
        print("""------------------------------------------------------
            """,parsed_results)
    else:
        print("@@@WARN")
        print("No se generaron acciones CRO válidas.")

#    print("\n--- Errores detectados por el Parser ---")
    if parser.errors:
        for err in parser.errors:
            print(err)
    else:
        print()
#        print("No se detectaron errores de sintaxis o de validación de definiciones.")

#    print("\n--- Advertencias detectadas por el Parser ---")
    if parser.warnings:
        for warn in parser.warnings:
            print(warn)
    else:
        print()
#        print("No se detectaron advertencias.")
