import json
import os
import glob
from datetime import datetime

import lib.core as core
core.dynmodule("lib.serializes","serialize")
print(core.serialize.INFO)


# --- Definición de Marcadores para el Contexto ---
MARKERS = {
    "human_start": "--- INICIO INSTRUCCION HUMANA ---\n",
    "human_end": "\n--- FIN INSTRUCCION HUMANA ---\n",
    "ai_instruction_start": "--- INICIO INSTRUCCION IA ---\n",
    "ai_instruction_end": "\n--- FIN INSTRUCCION IA ---\n",
    "metadata_start": "--- INICIO METADATA ---\n",
    "metadata_end": "\n--- FIN METADATA ---\n",
    "file_start": "--- INICIO ARCHIVO: {} ---\n",
    "file_end": "\n--- FIN ARCHIVO: {} ---\n",
    "path_info_start": "--- INICIO INFO DE PATH: {} ---\n",
    "path_info_end": "\n--- FIN INFO DE PATH ---\n"
}

# --- Estimación de Tokens (Aproximada) ---
# Usamos una heurística simple: 1 token ~ 4 caracteres para texto en inglés/español.
def _estimate_tokens(text):
    return len(text) // 4

# --- Función para Resolver Rutas Absolutas ---
def _resolve_path(base, relative_path):
    if not os.path.isabs(relative_path):
        return os.path.abspath(os.path.join(base, relative_path))
    return os.path.abspath(relative_path)

# --- Función para Añadir Contenido al Contexto con Gestión de Tokens y Truncamiento ---
def _add_to_context_string(
    context_builder,
    content_to_add,
    marker_start,
    marker_end,
    current_tokens_count,
    max_tokens_limit,
    warnings_list,
    identifier=""
):
    """
    Añade contenido a la cadena del contexto, gestionando límites de tokens y truncamiento.
    Retorna (nueva_cadena_contexto, nuevos_tokens_totales).
    """
    if not content_to_add:
        return context_builder, current_tokens_count

    # Los marcadores siempre se cuentan y se priorizan.
    total_markers_tokens = _estimate_tokens(marker_start + marker_end)

    if current_tokens_count + total_markers_tokens >= max_tokens_limit:
        warnings_list.append(
            f"Advertencia: No se pudo añadir '{identifier}' (marcadores) sin exceder el límite de tokens "
            f"({current_tokens_count}/{max_tokens_limit} tokens). Elemento omitido. ✂️"
        )
        return context_builder, current_tokens_count

    content_tokens = _estimate_tokens(content_to_add)

    # Si el contenido completo más marcadores excede el límite
    if current_tokens_count + total_markers_tokens + content_tokens > max_tokens_limit:
        remaining_tokens_for_content = max_tokens_limit - current_tokens_count - total_markers_tokens
        
        # Calcular cuántos caracteres podemos permitir para el contenido truncado
        # (Esto es una aproximación, puede no ser exacto al token)
        truncate_chars = remaining_tokens_for_content * 4 
        
        if truncate_chars <= 0: # Ni siquiera cabe una pequeña porción del contenido
            warnings_list.append(
                f"Advertencia: El elemento '{identifier}' fue omitido porque excede el límite de tokens "
                f"({current_tokens_count}/{max_tokens_limit} tokens disponibles). Considera refinar tus filtros. ✂️"
            )
            return context_builder, current_tokens_count
            
        truncated_content = content_to_add[:truncate_chars]
        
        # Ajustar para asegurar que los marcadores caben al menos
        if len(truncated_content) < len(content_to_add):
            warnings_list.append(
                f"Advertencia: El elemento '{identifier}' fue truncado para no exceder el límite de tokens "
                f"({current_tokens_count + total_markers_tokens + _estimate_tokens(truncated_content)}/{max_tokens_limit} tokens). Considera refinar tus filtros. ✂️"
            )
        
        context_builder.append(marker_start)
        context_builder.append(truncated_content)
        context_builder.append(marker_end)
        return context_builder, current_tokens_count + total_markers_tokens + _estimate_tokens(truncated_content)

    # Si todo cabe
    context_builder.append(marker_start)
    context_builder.append(content_to_add)
    context_builder.append(marker_end)
    return context_builder, current_tokens_count + total_markers_tokens + content_tokens

# --- Función Principal: load_osiris_context ---
def load_osiris_context(json_paths, global_base_dir=None):
    """
    Interpreta uno o más archivos .dev.ai.json para construir una cadena de contexto para Gemini AI.

    Args:
        json_paths (list): Una lista de rutas a archivos .dev.ai.json.
                           Si contiene "--help", muestra la ayuda.
        global_base_dir (str, optional): Directorio base global para resolver rutas relativas.
                                         Si None, usa el directorio del archivo JSON actual.

    Returns:
        tuple: (final_context_string, warnings_list)
               final_context_string (str): La cadena de contexto concatenada.
               warnings_list (list): Lista de advertencias generadas durante el procesamiento.
    """
    if json_paths == ["--help"]:
        _print_help_message()
        return "", []

    final_context_parts = [] # Usamos una lista para construir la cadena eficientemente
    warnings = []
    processed_file_paths = set() # Para deduplicación de rutas absolutas
    current_total_tokens = 0
    max_tokens_limit = 1000000 # Límite por defecto (1 millón de tokens)

    # Definimos el orden de las claves para la concatenación dentro de un bloque
    # Esto asume que el parser JSON preserva el orden de inserción, o que estas son las claves esperadas.
    # json.load en Python 3.7+ preserva el orden.
    KEY_ORDER = [
        "maxcontexttokens", # Se procesa primero para establecer el límite
        "fileencoding",
        "human",
        "aiinstruction",
        "metadata",
        "readfile",
        "readdirectoryfiles",
        "readdirectoryfilesrecursive",
        "readdirectorypaths",
        "readdirectorypathrecursive",
        "filterincludeextensions", # Estos son filtros, no contenido directo, se procesan junto con las claves de directorio
        "filterexcludepatterns",   # Se procesan junto con las claves de directorio
        "responseformat" # También una directiva, no contenido directo para el contexto.
    ]

    for json_file_path in json_paths:
        resolved_json_path = _resolve_path(global_base_dir or os.getcwd(), json_file_path)
        
        if not os.path.exists(resolved_json_path):
            warnings.append(f"Error: Archivo JSON '{resolved_json_path}' no encontrado. Saltando. ❌")
            continue
        if not os.path.isfile(resolved_json_path):
            warnings.append(f"Error: La ruta '{resolved_json_path}' no es un archivo JSON válido. Saltando. ❌")
            continue

        local_base_dir = os.path.dirname(resolved_json_path) if global_base_dir is None else global_base_dir

        try:
            with open(resolved_json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            if not isinstance(json_data, list):
                warnings.append(f"Error: El archivo '{resolved_json_path}' no es un arreglo JSON. Saltando. ❌")
                continue

            for block_idx, block in enumerate(json_data):
                if not isinstance(block, dict):
                    warnings.append(f"Advertencia: El elemento {block_idx} en '{json_file_path}' no es un objeto JSON. Saltando. ⚠️")
                    continue

                # Normalizar claves a minúsculas para procesamiento no case-sensitive
                normalized_block = {k.lower(): v for k, v in block.items()}

                # Procesar maxContextTokens primero si está presente para este archivo
                if "maxcontexttokens" in normalized_block and isinstance(normalized_block["maxcontexttokens"], int):
                    max_tokens_limit = normalized_block["maxcontexttokens"]
                    warnings.append(f"Info: Límite de tokens para este contexto establecido en {max_tokens_limit} por '{json_file_path}'.")
                
                block_file_encoding = normalized_block.get("fileencoding", "utf-8")


                # Procesar claves en el orden definido
                for key in KEY_ORDER:
                    if key not in normalized_block:
                        continue
                    
                    value = normalized_block[key]
                    
                    # --- HUMAN ---
                    if key == "human":
                        if isinstance(value, str):
                            final_context_parts, current_total_tokens = _add_to_context_string(
                                final_context_parts, value, MARKERS["human_start"], MARKERS["human_end"],
                                current_total_tokens, max_tokens_limit, warnings, f"instrucción human en bloque {block_idx}"
                            )
                        else:
                            warnings.append(f"Advertencia: 'human' en bloque {block_idx} debe ser un string. Ignorado. ⚠️")

                    # --- AI_INSTRUCTION ---
                    elif key == "aiinstruction":
                        if isinstance(value, str):
                            final_context_parts, current_total_tokens = _add_to_context_string(
                                final_context_parts, value, MARKERS["ai_instruction_start"], MARKERS["ai_instruction_end"],
                                current_total_tokens, max_tokens_limit, warnings, f"instrucción AI en bloque {block_idx}"
                            )
                        else:
                            warnings.append(f"Advertencia: 'aiInstruction' en bloque {block_idx} debe ser un string. Ignorado. ⚠️")

                    # --- METADATA ---
                    elif key == "metadata":
                        if isinstance(value, dict):
                            metadata_str = json.dumps(value, indent=2, ensure_ascii=False)
                            final_context_parts, current_total_tokens = _add_to_context_string(
                                final_context_parts, metadata_str, MARKERS["metadata_start"], MARKERS["metadata_end"],
                                current_total_tokens, max_tokens_limit, warnings, f"metadata en bloque {block_idx}"
                            )
                        else:
                            warnings.append(f"Advertencia: 'metadata' en bloque {block_idx} debe ser un objeto JSON. Ignorado. ⚠️")

                    # --- READFILE ---
                    elif key == "readfile":
                        if isinstance(value, list):
                            for file_rel_path in value:
                                if not isinstance(file_rel_path, str):
                                    warnings.append(f"Advertencia: Elemento no string en 'readFile' de bloque {block_idx}. Ignorado. ⚠️")
                                    continue
                                resolved_file_path = _resolve_path(local_base_dir, file_rel_path)
                                if resolved_file_path in processed_file_paths:
                                    warnings.append(f"Advertencia: El archivo '{resolved_file_path}' ya fue incluido y se omitió una relectura duplicada para optimizar el contexto. ⚠️")
                                    continue
                                
                                try:
                                    with open(resolved_file_path, 'r', encoding=block_file_encoding) as f:
                                        file_content = f.read()
                                    final_context_parts, current_total_tokens = _add_to_context_string(
                                        final_context_parts, file_content,
                                        MARKERS["file_start"].format(resolved_file_path),
                                        MARKERS["file_end"].format(resolved_file_path),
                                        current_total_tokens, max_tokens_limit, warnings, f"archivo '{resolved_file_path}'"
                                    )
                                    processed_file_paths.add(resolved_file_path)
                                except FileNotFoundError:
                                    warnings.append(f"fileRead Path '{resolved_file_path}' Not found y continúa la interpretación.")
                                except Exception as e:
                                    warnings.append(f"Error al leer archivo '{resolved_file_path}': {e}. Continúa la interpretación.")
                        else:
                            warnings.append(f"Advertencia: 'readFile' en bloque {block_idx} debe ser un arreglo de strings. Ignorado. ⚠️")

                    # --- READ_DIRECTORY_FILES / READ_DIRECTORY_FILES_RECURSIVE ---
                    elif key in ["readdirectoryfiles", "readdirectoryfilesrecursive"]:
                        if not isinstance(value, str):
                            warnings.append(f"Advertencia: '{key}' en bloque {block_idx} debe ser un string con la ruta a un directorio. Ignorado. ⚠️")
                            continue

                        dir_rel_path = value
                        resolved_dir_path = _resolve_path(local_base_dir, dir_rel_path)
                        
                        if not os.path.isdir(resolved_dir_path):
                            warnings.append(f"DirectoryRead Path '{resolved_dir_path}' Not found o inaccesible y continúa la interpretación.")
                            continue

                        is_recursive = (key == "readdirectoryfilesrecursive")
                        
                        include_exts = normalized_block.get("filterincludeextensions", [])
                        if not isinstance(include_exts, list):
                            warnings.append(f"Advertencia: 'filterIncludeExtensions' en bloque {block_idx} debe ser un arreglo de strings. Se ignorará el filtro. ⚠️")
                            include_exts = []
                        
                        exclude_patterns = normalized_block.get("filterexcludepatterns", [])
                        if not isinstance(exclude_patterns, list):
                            warnings.append(f"Advertencia: 'filterExcludePatterns' en bloque {block_idx} debe ser un arreglo de strings. Se ignorará el filtro. ⚠️")
                            exclude_patterns = []

                        if not include_exts and "filterincludeextensions" in normalized_block and not is_recursive and not os.path.isdir(resolved_dir_path):
                            # Esta es la condición para el aviso de 'includeExtensions' sin directorio válido asociado.
                            # Puede ser compleja de pinpoint, pero intentamos.
                            # Para un directorio válido, arreglo vacío significa 'todas las extensiones'.
                            warnings.append(f"Advertencia: La clave 'filterIncludeExtensions' en el bloque {block_idx} fue ignorada por falta de una clave de directorio válida asociada. ⚠️")

                        for root, _, files in os.walk(resolved_dir_path):
                            if not is_recursive and root != resolved_dir_path:
                                continue # Solo el nivel superior si no es recursivo

                            for file_name in files:
                                file_path = os.path.join(root, file_name)
                                resolved_file_path = os.path.abspath(file_path) # Asegurar ruta absoluta
                                
                                # Aplicar filtros
                                file_ext = os.path.splitext(file_name)[1].lower()
                                
                                # Exclusión tiene prioridad
                                if any(glob.fnmatch.fnmatch(resolved_file_path, _resolve_path(local_base_dir, p)) for p in exclude_patterns):
                                    #warnings.append(f"Info: Archivo '{resolved_file_path}' excluido por patrón. 🚫")
                                    continue

                                # Inclusión de extensiones
                                if include_exts and file_ext not in [ext.lower() for ext in include_exts]:
                                    #warnings.append(f"Info: Archivo '{resolved_file_path}' excluido por extensión. 🚫")
                                    continue
                                    
                                if resolved_file_path in processed_file_paths:
                                    warnings.append(f"Advertencia: El archivo '{resolved_file_path}' ya fue incluido y se omitió una relectura duplicada para optimizar el contexto. ⚠️")
                                    continue

                                try:
                                    with open(resolved_file_path, 'r', encoding=block_file_encoding) as f:
                                        file_content = f.read()
                                    final_context_parts, current_total_tokens = _add_to_context_string(
                                        final_context_parts, file_content,
                                        MARKERS["file_start"].format(resolved_file_path),
                                        MARKERS["file_end"].format(resolved_file_path),
                                        current_total_tokens, max_tokens_limit, warnings, f"archivo '{resolved_file_path}'"
                                    )
                                    processed_file_paths.add(resolved_file_path)
                                except Exception as e:
                                    warnings.append(f"Error al leer archivo '{resolved_file_path}' desde directorio '{resolved_dir_path}': {e}. Continúa.")

                    # --- READ_DIRECTORY_PATHS / READ_DIRECTORY_PATH_RECURSIVE ---
                    elif key in ["readdirectorypaths", "readdirectorypathrecursive"]:
                        if not isinstance(value, list):
                            warnings.append(f"Advertencia: '{key}' en bloque {block_idx} debe ser un arreglo de strings con rutas a directorios. Ignorado. ⚠️")
                            continue
                        
                        is_recursive_path = (key == "readdirectorypathrecursive")

                        include_exts = normalized_block.get("filterincludeextensions", [])
                        if not isinstance(include_exts, list):
                            warnings.append(f"Advertencia: 'filterIncludeExtensions' en bloque {block_idx} debe ser un arreglo de strings. Se ignorará el filtro. ⚠️")
                            include_exts = []
                        
                        exclude_patterns = normalized_block.get("filterexcludepatterns", [])
                        if not isinstance(exclude_patterns, list):
                            warnings.append(f"Advertencia: 'filterExcludePatterns' en bloque {block_idx} debe ser un arreglo de strings. Se ignorará el filtro. ⚠️")
                            exclude_patterns = []

                        for dir_rel_path in value:
                            if not isinstance(dir_rel_path, str):
                                warnings.append(f"Advertencia: Elemento no string en '{key}' de bloque {block_idx}. Ignorado. ⚠️")
                                continue

                            resolved_dir_path = _resolve_path(local_base_dir, dir_rel_path)
                            
                            if not os.path.isdir(resolved_dir_path):
                                warnings.append(f"DirectoryRead Path '{resolved_dir_path}' Not found o inaccesible y continúa la interpretación.")
                                continue

                            for root, dirs, files in os.walk(resolved_dir_path):
                                if not is_recursive_path and root != resolved_dir_path:
                                    continue # Solo el nivel superior si no es recursivo para paths
                                
                                current_base_for_relative_path = resolved_dir_path # Para calcular la ruta relativa

                                # Recolectar metadata de directorios
                                if root != resolved_dir_path and is_recursive_path: # Incluir subdirectorios si es recursivo
                                    dir_path_abs = os.path.abspath(root)
                                    if dir_path_abs not in processed_file_paths: # deduplicación de directorios
                                        metadata_content = _format_path_metadata(
                                            dir_path_abs,
                                            is_directory=True,
                                            base_path_for_relative=current_base_for_relative_path
                                        )
                                        final_context_parts, current_total_tokens = _add_to_context_string(
                                            final_context_parts, metadata_content,
                                            MARKERS["path_info_start"].format(dir_path_abs),
                                            MARKERS["path_info_end"].format(dir_path_abs),
                                            current_total_tokens, max_tokens_limit, warnings, f"info de path directorio '{dir_path_abs}'"
                                        )
                                        processed_file_paths.add(dir_path_abs)

                                # Recolectar metadata de archivos
                                for file_name in files:
                                    file_path = os.path.join(root, file_name)
                                    resolved_file_path = os.path.abspath(file_path)

                                    # Aplicar filtros
                                    file_ext = os.path.splitext(file_name)[1].lower()
                                    
                                    if any(glob.fnmatch.fnmatch(resolved_file_path, _resolve_path(local_base_dir, p)) for p in exclude_patterns):
                                        continue

                                    if include_exts and file_ext not in [ext.lower() for ext in include_exts]:
                                        continue

                                    if resolved_file_path in processed_file_paths:
                                        warnings.append(f"Advertencia: El path '{resolved_file_path}' ya fue incluido (metadata) y se omitió una relectura duplicada para optimizar el contexto. ⚠️")
                                        continue

                                    metadata_content = _format_path_metadata(
                                        resolved_file_path,
                                        is_directory=False,
                                        base_path_for_relative=current_base_for_relative_path
                                    )
                                    final_context_parts, current_total_tokens = _add_to_context_string(
                                        final_context_parts, metadata_content,
                                        MARKERS["path_info_start"].format(resolved_file_path),
                                        MARKERS["path_info_end"].format(resolved_file_path),
                                        current_total_tokens, max_tokens_limit, warnings, f"info de path archivo '{resolved_file_path}'"
                                    )
                                    processed_file_paths.add(resolved_file_path)
                    
                    # --- FILTROS SIN DIRECTORIO ASOCIADO ---
                    # Esto maneja la advertencia si filterIncludeExtensions está solo
                    elif key == "filterincludeextensions" and not any(k in normalized_block for k in ["readdirectoryfiles", "readdirectoryfilesrecursive", "readdirectorypaths", "readdirectorypathrecursive"]):
                        warnings.append(f"Advertencia: La clave 'filterIncludeExtensions' en el bloque {block_idx} fue ignorada por falta de una clave de directorio válida asociada. ⚠️")
                    
                    # --- RESPONSE_FORMAT (Se registra, no se añade al contexto) ---
                    elif key == "responseformat":
                        if not isinstance(value, str):
                            warnings.append(f"Advertencia: 'responseFormat' en bloque {block_idx} debe ser un string. Ignorado. ⚠️")
                        # No se añade al final_context_parts, es una directriz para la IA.
                        # En una implementación real de Osiris, esta información se pasaría a la configuración de la respuesta.
                        # Por ahora, solo lo reconocemos.
                        pass
                    
                    # --- FILE_ENCODING (Ya procesado para block_file_encoding) ---
                    elif key == "fileencoding":
                        pass # Ya procesado al inicio del bloque
                    
                    # --- MAX_CONTEXT_TOKENS (Ya procesado al inicio del bloque) ---
                    elif key == "maxcontexttokens":
                        pass # Ya procesado al inicio del bloque

        except json.JSONDecodeError as e:
            warnings.append(f"Error: El archivo JSON '{resolved_json_path}' está mal formado: {e}. Saltando. ❌")
        except Exception as e:
            warnings.append(f"Error inesperado al procesar '{resolved_json_path}': {e}. Saltando. ❌")

    final_context_string = "".join(final_context_parts)
    
    # Advertencia final si el contexto aún se acerca al límite (considerando que hubo truncamiento anterior)
    if current_total_tokens >= max_tokens_limit * 0.95:
        warnings.append(f"Advertencia final: El contexto generado es muy extenso ({current_total_tokens}/{max_tokens_limit} tokens). La IA podría tener dificultades. 🥵")
#    final_context_string = final_context_string.replace("\\n", "\n")
    return str(final_context_string) + str(warnings)


# --- Formateador de Metadata de Path ---
def _format_path_metadata(path, is_directory, base_path_for_relative):
    name = os.path.basename(path) if not is_directory else os.path.basename(path)
    if not name and is_directory: # Caso del directorio raíz de la ruta especificada
        name = os.path.basename(os.path.normpath(path))
        if not name: name = path # Si sigue vacío (ej. para '/'), usar la ruta completa

    file_type = "Directorio" if is_directory else "Archivo"
    extension = os.path.splitext(name)[1] if not is_directory else "N/A"
    
    size_bytes = "N/A"
    if not is_directory and os.path.exists(path) and os.path.isfile(path):
        try:
            size_bytes = os.path.getsize(path)
        except OSError:
            pass # No se pudo obtener el tamaño

    mod_date = "N/A"
    if os.path.exists(path):
        try:
            mod_timestamp = os.path.getmtime(path)
            mod_date = datetime.fromtimestamp(mod_timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except OSError:
            pass # No se pudo obtener la fecha de modificación

    relative_path = os.path.relpath(path, base_path_for_relative) if path.startswith(base_path_for_relative) else path

    metadata_str = (
        f"Nombre: {name}\n"
        f"Tipo: {file_type}\n"
        f"Extension: {extension}\n"
        f"Tamaño: {size_bytes} bytes\n"
        f"Fecha Modificación: {mod_date}\n"
        f"Ruta Relativa al Bloque: {relative_path}\n"
    )
    return metadata_str

# --- Mensaje de Ayuda ---
def _print_help_message():
    print("""
    ✨ Ayuda de la Función de Inserción de Fuentes de Proyectos (Osiris Context Loader) ✨
    -----------------------------------------------------------------------------------

    Esta función interpreta archivos '.dev.ai.json' para construir un contexto detallado
    para Gemini AI. Los archivos deben ser un arreglo JSON con uno o más objetos,
    cada uno representando un bloque de contexto.

    📚 Estructura Básica de un Bloque:
    [
      {
        "human": "Instrucciones del usuario...",
        "aiInstruction": "Directrices para la IA...",
        "metadata": { "project": "MyProject", "version": "1.0" },
        "readFile": ["path/to/file1.js", "path/to/file2.txt"],
        "readDirectoryFiles": "path/to/folder",
        "readDirectoryFilesRecursive": "path/to/recursive_folder",
        "readDirectoryPaths": ["path/to/data_folder"],
        "readDirectoryPathRecursive": ["path/to/all_docs"],
        "filterIncludeExtensions": [".js", ".py"],
        "filterExcludePatterns": ["temp/*.log", "node_modules/**"],
        "maxContextTokens": 500000,
        "responseFormat": "Markdown",
        "fileEncoding": "UTF-8"
      }
    ]

    🔑 Claves Admitidas (NO case-sensitive):

    1.  human (string): Texto con instrucciones, explicaciones e indicaciones para la IA.

    2.  aiInstruction (string): Instrucciones operativas directas para la IA sobre cómo procesar
        o priorizar la información del contexto.

    3.  metadata (objeto JSON): Información estructurada sobre el proyecto/componente
        (nombre, versión, autores, tecnologías, etc.).

    4.  readFile (arreglo de strings): Rutas a archivos cuyo contenido se leerá e incluirá.
        Si un archivo no existe, se avisará: "fileRead Path (el path real) Not found".

    5.  readDirectoryFiles (string): Ruta a un directorio. Lee el CONTENIDO de los archivos
        directamente en ese directorio (NO recursivo).

    6.  readDirectoryFilesRecursive (string): Ruta a un directorio. Lee el CONTENIDO de los archivos
        en ese directorio y sus subdirectorios (RECURSIVO).

    7.  readDirectoryPaths (arreglo de strings): Rutas a directorios. No lee el contenido,
        sino que recolecta METADATA de las rutas de archivos/subdirectorios directamente
        en los directorios especificados (NO recursivo).
        Formato de Metadata: Nombre, Tipo, Extensión, Tamaño, Fecha Modificación, Ruta Relativa al Bloque.

    8.  readDirectoryPathRecursive (arreglo de strings): Rutas a directorios. Recolecta METADATA
        de las rutas de archivos/subdirectorios en esos directorios y sus subdirectorios (RECURSIVO).

    9.  filterIncludeExtensions (arreglo de strings): Extensiones de archivo (ej. ".js", ".py").
        Aplicable a claves de lectura de directorios y paths.
        -   Si ausente o arreglo vacío `[]`: "No aplicar filtro de extensión" (se consideran todas).
        -   Si contiene extensiones: Solo los archivos con esas extensiones serán considerados.
        -   Ignorada con advertencia si no hay clave de directorio válida asociada.

    10. filterExcludePatterns (arreglo de strings): Rutas o patrones `glob` (ej. "*.log", "node_modules/**").
        Aplicable a claves de lectura de directorios y paths. Los archivos que coincidan
        serán EXCLUIDOS.
        -   Prioridad: `filterExcludePatterns` siempre tiene prioridad sobre `filterIncludeExtensions`.

    11. maxContextTokens (entero): Límite personalizado de tokens para la cadena de contexto.
        Por defecto: 1,000,000 tokens. Si se excede, se intenta truncar o se omiten elementos
        con advertencia.

    12. responseFormat (string): Indica el formato deseado para la respuesta de la IA (ej. "Markdown", "JSON").
        (Esta directriz no se añade al contexto directamente, pero la función la reconoce).

    13. fileEncoding (string): Codificación de caracteres para los archivos leídos (ej. "UTF-8", "latin-1").
        Por defecto: "UTF-8".

    ⚙️ Funcionamiento General:
    -   La función construye una única cadena de texto final con todo el contenido.
    -   Se utilizan marcadores claros (ej. "--- INICIO ARCHIVO: ---") para distinguir las fuentes.
    -   El orden de concatenación respeta el orden de las claves en el JSON y el orden de los bloques.
    -   Deduplicación Proactiva: Los archivos (contenido o metadata) solo se incluyen una vez.
        Si se intenta incluir un archivo ya procesado, se emite una advertencia y se omite la repetición.
    -   Gestión de Límites: Se estima el tamaño en tokens. Si se acerca al límite, se advierte.
        Si se excede, se truncan o se omiten elementos (excepto 'human' y 'aiInstruction' que tienen máxima prioridad).

    📝 Notas Importantes:
    -   Es tu responsabilidad como humano compositor del JSON evitar configuraciones conflictivas
        que puedan llevar a confusiones lógicas, aunque la deduplicación y las advertencias ayudan.
    -   Las rutas relativas se resuelven a partir del directorio donde se encuentra el archivo .dev.ai.json
        o del 'global_base_dir' si se especifica.

    ¡Usa esta herramienta para darme un contexto rico y estructurado!
    """)



print("LOAD OSIRIS CONTEXT WAS CHARGED")