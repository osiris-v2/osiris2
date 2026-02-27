import re
import json
import urllib.parse

# osiris_definitions.py - Definiciones completas y corregidas para Python
INFO = """
Module Cro Parser Info
Osiris internal python library
import re
import json
import urllib.parse
"""

# osiris_definitions.py - Definiciones completas y corregidas para Python
INFO = """
Module Cro Parser Info
Osiris internal python library
"""

cro_definitions = {
    "GLOBAL_MODE": {
        "TYPE":["CLI","WEB","DESKTOP"]
    },
    "COMMAND_GROUPS": {
        "SEARCH_IN": ["GOOGLE", "BING", "OSIRIS_INTERNAL"],
        "LOG_OSIRIS": ["INFO", "WARN", "ERROR"],
        "DEFINE_VAR": ["USER_QUERY_SUMMARY", "TEMP_DATA"],
        "EXECUTE_SYSTEM_ACTION": ["REBOOT", "SHUTDOWN", "RUN_COMMAND"],
        "LOCAL_FS": ["LIST_DIRECTORY", "READ_FILE", "WRITE_FILE"],
        "WEB_MODE": ["JS"],
        "REMOTE_FS":["SFTP_LS"]
    },
    "PROTO_DEFINITIONS": {
        "REMOTE_FS": {
            "SFTP_LS": {
                "DESCRIPTION": "Lista el contenido de un directorio remoto vía SFTP.",
                "ACTION_TYPE": "SFTP_LIST",
                "PARAMETERS": {
                    "PATH": {
                        "TYPE": "string",
                        "REQUIRED": True,
                        "DYNAMIC": True,
                        "DEFAULT": "."
                    }
                }
            }
        },
        "WEB_MODE": {
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
                "URL_TEMPLATE": "https://www.googleapis.com/customsearch/v1?key=%%API_KEY%%&cx=%%CX_CODE%%",
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
                    "COMMAND": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True },
                        "INTERACTIVE": {
                            "TYPE": "boolean",
                            "REQUIRED": False,
                            "DYNAMIC": True,
                            "DEFAULT": "False",
                            "DESCRIPTION": "Si \'\'True\'\', permite interacción directa con la terminal (no captura salida)."
                        }
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
                    "FLAGS": {
                        "TYPE": "enum",
                        "VALUES": ["WRITE_CONTEXT"],
                        "REQUIRED": False,
                        "DEFAULT": "",
                        "ALLOW_MULTIPLE": True,
                        "ACTION_PER_VALUE": True
                    }
                }
            },
            "WRITE_FILE": {
                "DESCRIPTION": "Escribe contenido en un archivo o crea uno nuevo. Requiere confirmación del usuario.",
                "ACTION_TYPE": "FILE_SYSTEM_WRITE",
                "PARAMETERS": {
                    "PATH": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True },
                    "CONTENT": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True },
                    "OVERWRITE": { "TYPE": "boolean", "DEFAULT": False, "REQUIRED": False, "DYNAMIC": True },
                    "ENCODING": { "TYPE": "enum", "VALUES": ["utf-8", "latin-1"], "DEFAULT": "utf-8", "REQUIRED": False, "DYNAMIC": True }
                }
            }
        }
    }
}