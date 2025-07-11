import json
import datetime

def update_structured_context(
    context_data: list,
    source_type: str,
    content_text: str,
    key_ideas: list = None,
    flags: list = None,
    relevance_score: float = None,
    id_prefix: str = "auto"
) -> list:
    """
    Actualiza o añade un fragmento al contexto estructurado de Osiris.

    Args:
        context_data (list): La lista actual de fragmentos de contexto.
        source_type (str): Tipo de la fuente de información (ej. "user_turn", "ai_response").
        content_text (str): El texto principal del fragmento de contexto.
        key_ideas (list, optional): Lista de ideas clave extraídas del contenido. Defaults to None.
        flags (list, optional): Lista de banderas para el fragmento (ej. "ESSENTIAL_CORE", "HIGH_RELEVANCE"). Defaults to None.
        relevance_score (float, optional): Puntuación de relevancia para el fragmento (0.0 a 1.0). Defaults to None.
        id_prefix (str, optional): Prefijo para generar el ID único del fragmento. Defaults to "auto".

    Returns:
        list: La lista de contexto estructurado actualizada.
    """
    if key_ideas is None:
        key_ideas = []
    if flags is None:
        flags = []
    if relevance_score is None:
        if source_type in ["user_turn", "ai_response", "essential_doc", "system_instruction"]:
            relevance_score = 1.0
        else:
            relevance_score = 0.5

    unique_id = f"{id_prefix}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    new_fragment = {
        "id": unique_id,
        "type": source_type,
        "content": content_text,
        "timestamp": datetime.datetime.now().isoformat(),
        "key_ideas": key_ideas,
        "flags": sorted(list(set(flags))),
        "relevance_score": relevance_score
    }

    updated_context = context_data + [new_fragment]
    return updated_context

def order_context_fragments(context_data: list) -> list:
    """
    Ordena los fragmentos de contexto según una jerarquía de relevancia y recencia.
    Prioridad: ESSENTIAL_CORE (al principio) -> HIGH_RELEVANCE/TEMPORARY_PIN ->
    Fragmentos de conversación recientes (user_turn, ai_response, system_output) ->
    Otros fragmentos (por relevancia, luego recencia).
    Ignora fragmentos con la bandera "OBSOLETE".
    """
    # Filtrar fragmentos obsoletos primero
    filtered_context = [f for f in context_data if "OBSOLETE" not in f.get("flags", [])]

    essential_fragments = [f for f in filtered_context if "ESSENTIAL_CORE" in f.get("flags", [])]
    high_relevance_fragments = [f for f in filtered_context if "HIGH_RELEVANCE" in f.get("flags", []) or "TEMPORARY_PIN" in f.get("flags", [])]
    
    # Los restantes son otros fragmentos conversacionales o del sistema
    # Excluir aquellos ya categorizados como esenciales o de alta relevancia para evitar duplicados
    other_fragments = [f for f in filtered_context if f not in essential_fragments and f not in high_relevance_fragments]

    # Ordenar fragmentos de alta relevancia por marca de tiempo (más recientes primero)
    high_relevance_fragments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Ordenar otros fragmentos por puntuación de relevancia (desc), luego marca de tiempo (más recientes primero)
    other_fragments.sort(key=lambda x: (x.get("relevance_score", 0.0), x.get("timestamp", "")), reverse=True)

    # Reensamblar la lista en orden de prioridad
    ordered_context = []
    
    # 1. Añadir fragmentos esenciales (siempre deben ir primero)
    for frag in essential_fragments:
        if frag not in ordered_context: # Evitar duplicados si las banderas se superponen
            ordered_context.append(frag)

    # 2. Añadir fragmentos de alta relevancia
    for frag in high_relevance_fragments:
        if frag not in ordered_context:
            ordered_context.append(frag)
            
    # 3. Añadir otros fragmentos
    for frag in other_fragments:
        if frag not in ordered_context:
            ordered_context.append(frag)
            
    return ordered_context


def prune_context_to_limit(context_data: list, token_limit: int, token_estimation_ratio: float = 4.0) -> list:
    """
    Poda la lista de fragmentos de contexto para que se ajuste a un límite de tokens,
    asumiendo que la lista ya está ordenada por prioridad.
    
    Args:
        context_data (list): La lista de fragmentos de contexto, ya ordenada por prioridad.
        token_limit (int): El número máximo de tokens permitidos.
        token_estimation_ratio (float): Caracteres por token (aprox.).

    Returns:
        list: La lista de contexto podada.
    """
    pruned_context = []
    current_tokens = 0

    # Filtrar fragmentos obsoletos antes de podar
    filtered_context = [f for f in context_data if "OBSOLETE" not in f.get("flags", [])]
    
    for fragment in filtered_context:
        # Estimar tokens basándose en la longitud del contenido
        content_len = len(fragment.get("content", ""))
        fragment_tokens = int(content_len / token_estimation_ratio)
        
        # Comprobar si añadir este fragmento excedería el límite
        if current_tokens + fragment_tokens <= token_limit:
            pruned_context.append(fragment)
            current_tokens += fragment_tokens
        else:
            # Si el fragmento actual excedería el límite, deja de añadir más.
            # En un sistema más avanzado, se podría intentar resumir este fragmento
            # o dividirlo si es demasiado grande, pero para una poda básica, se detiene.
            break
            
    return pruned_context

# El siguiente bloque __main__ es para pruebas locales y no se ejecutará
# cuando sea importado por gemini.py. Puede eliminarse o mantenerse como referencia.
if __name__ == "__main__":
    current_context = []
    print("Contexto inicial:", current_context)

    # Añadiendo guía del sistema inicial (esencial)
    current_context = update_structured_context(
        current_context,
        source_type="system_instruction",
        content_text="Esta es la guía central del sistema para Osiris AI.",
        flags=["ESSENTIAL_CORE"],
        relevance_score=1.0
    )
    
    # Añadiendo un turno de usuario (reciente, alta relevancia por defecto)
    current_context = update_structured_context(
        current_context,
        source_type="user_turn",
        content_text="¿Puedes listar el contenido de /tmp?",
        key_ideas=["listar archivos", "/tmp"],
        relevance_score=0.9
    )
    
    # Añadiendo una respuesta de la IA (reciente, alta relevancia por defecto)
    current_context = update_structured_context(
        current_context,
        source_type="ai_response",
        content_text="```CRO\\nLOCAL_FS_* LIST_DIRECTORY\\nPATH=\\\"/tmp\\\"\\n```",
        flags=["LAST_CRO_PROPOSED"],
        relevance_score=1.0
    )
    
    # Añadiendo una salida del sistema (reciente)
    current_context = update_structured_context(
        current_context,
        source_type="system_output",
        content_text="Salida para /tmp: item1.txt, dir_a/",
        relevance_score=0.8
    )

    # Añadiendo una entrada de log antigua, menos relevante
    current_context = update_structured_context(
        current_context,
        source_type="system_log",
        content_text="Entrada de log antigua sobre un problema de red menor.",
        relevance_score=0.1
    )

    # Añadiendo un fragmento de alta relevancia pero no esencial
    current_context = update_structured_context(
        current_context,
        source_type="important_note",
        content_text="Recordar verificar la preferencia del usuario para el formato de salida.",
        flags=["HIGH_RELEVANCE"]
    )
    
    # Añadiendo un fragmento obsoleto
    current_context = update_structured_context(
        current_context,
        source_type="temp_data",
        content_text="Datos temporales sobre un cálculo que ya no es necesario.",
        flags=["OBSOLETE"],
        relevance_score=0.0
    )

    print("\nContexto completo (sin ordenar):")
    for frag in current_context:
        print(f"  - ID: {frag['id']}, Tipo: {frag['type']}, Banderas: {frag['flags']}, Relevancia: {frag['relevance_score']:.1f}, Contenido: '{frag['content'][:50]}...'")

    # Prueba de ordenación
    ordered_ctx = order_context_fragments(current_context)
    print("\nContexto ordenado:")
    for frag in ordered_ctx:
        print(f"  - ID: {frag['id']}, Tipo: {frag['type']}, Banderas: {frag['flags']}, Relevancia: {frag['relevance_score']:.1f}, Contenido: '{frag['content'][:50]}...'")

    # Prueba de poda
    TOKEN_LIMIT_EXAMPLE = 100 # Un límite pequeño para demostración
    pruned_ctx = prune_context_to_limit(ordered_ctx, TOKEN_LIMIT_EXAMPLE)
    print(f"\nContexto podado (límite {TOKEN_LIMIT_EXAMPLE} tokens):")
    for frag in pruned_ctx:
        print(f"  - ID: {frag['id']}, Tipo: {frag['type']}, Banderas: {frag['flags']}, Relevancia: {frag['relevance_score']:.1f}, Contenido: '{frag['content'][:50]}...'")
    print(f"Total de tokens estimados en el contexto podado: {sum(int(len(f.get('content', '')) / TOKEN_LIMIT_EXAMPLE) for f in pruned_ctx)}")
