Dada la arquitectura actual de gemini.py y la guía de Osiris, podemos establecer una estrategia para abordar el problema del contexto en expansión y los errores por exceso de tokens (429).
La estrategia se centrará en una gestión de contexto escalonada e inteligente, donde la IA (yo) juega un papel activo en la curación y optimización de la información, apoyada por nuevas capacidades CRO y la infraestructura de Osiris.
Estrategia Integral para la Gestión de Contexto en Osiris
El objetivo es mantener el conversation_context dentro de los límites del modelo sin perder información crucial o la coherencia de la conversación. Esto se logrará mediante una combinación de monitoreo, resumen inteligente y persistencia selectiva.
1. Monitoreo Proactivo del Contexto (Rol del Sistema/gemini.py)
Implementación: El gemini.py (o un módulo de gestión de contexto asociado) deberá medir continuamente el tamaño actual del conversation_context en términos de tokens. Para ello, necesitará conocer el límite de tokens del modelo actual (gemini-2.5-flash-preview-05-20 tiene un límite alto, pero otros modelos pueden ser más restrictivos).
Umbrales: Se establecerán dos umbrales clave:
Umbral de Advertencia/Iniciación (Ej. 70-80% del límite): Cuando el contexto alcance este tamaño, se activará una señal o un mecanismo para que la IA (yo) considere una acción de optimización.
Umbral Crítico/Forzado (Ej. 90-95% del límite): Si el contexto llega a este punto, el sistema debería forzar una acción de poda o resumen automático si la IA no ha actuado o si la situación es apremiante.
2. Gestión de Contexto por Capas (Rol de la IA y Nuevas Capacidades CRO)
Esta es la parte central donde la IA interviene activamente:
Capa 1: Contexto Activo (Ventana de Conversación Reciente)
Descripción: Los N turnos más recientes de la conversación (ej. las últimas 5-10 interacciones completas de usuario y AI) se mantendrían siempre intactos en el conversation_context. Esto asegura que la IA tenga la información más fresca y directa para responder.
Mecanismo: El sistema, al recibir una solicitud de la IA para resumir o podar, priorizaría mantener esta ventana sin modificar.
Capa 2: Contexto Resumido (Historial Condensado)
Descripción: La información de los turnos de conversación más antiguos (los que están fuera de la "ventana de conversación reciente") sería procesada y resumida. Este resumen sería conciso, capturando los puntos clave, decisiones, comandos ejecutados con éxito y sus resultados.
Mecanismo CRO (Propuesta de Adición a osiris_definitions):
CONTEXT_MANAGEMENT_* SUMMARIZE_HISTORY: Yo (la IA) emitiría este comando cuando el umbral de advertencia se alcance, o cuando identifique un punto lógico en la conversación para resumir.
"CONTEXT_MANAGEMENT": {
    "SUMMARIZE_HISTORY": {
        "DESCRIPTION": "Resume los turnos más antiguos de la conversación para reducir el tamaño del contexto. Los N turnos más recientes se mantienen completos, y se busca alcanzar un porcentaje objetivo de tokens.",
        "ACTION_TYPE": "AI_CONTEXT_OPTIMIZATION",
        "PARAMETERS": {
            "KEEP_LAST_TURNS": { "TYPE": "integer", "REQUIRED": True, "DYNAMIC": True, "DEFAULT": 5, "NOTES": "Número de turnos recientes a mantener sin resumir." },
            "TARGET_TOKEN_PERCENTAGE": { "TYPE": "integer", "REQUIRED": True, "DYNAMIC": True, "DEFAULT": 75, "NOTES": "Porcentaje del límite de tokens al que se intenta reducir el contexto." }
        }
    }
}
Cómo funcionaría:
La IA genera el CRO SUMMARIZE_HISTORY.
El cro_parser (post-reestructuración) y el "Ejecutor" en gemini.py identificarían los turnos a resumir.
El sistema podría entonces hacer una llamada interna a la propia IA (o a un módulo de resumen dedicado) con un prompt específico para que genere un resumen de esos turnos históricos.
El conversation_context se actualizaría reemplazando los turnos largos por el resumen compacto.
Capa 3: Base de Conocimiento Permanente (Información Curada y Esencial)
Descripción: La información más crítica y duradera (arquitectura del sistema, guías de operación, decisiones de diseño, objetivos a largo plazo, resultados de diagnósticos importantes, especificaciones como osiris_definitions y los futuros NOMBREx.read.info.ai) se almacenaría de forma persistente y fuera del contexto activo.
Mecanismo CRO (Propuesta de Adición a osiris_definitions):
CONTEXT_MANAGEMENT_* PERSIST_KEY_INFO: Yo (la IA) usaría este comando para "archivar" activamente información importante una vez que se ha resuelto o establecido.
"CONTEXT_MANAGEMENT": {
    "PERSIST_KEY_INFO": {
        "DESCRIPTION": "Extrae y almacena información clave (decisiones, resultados, metas) de la conversación en la base de conocimiento interna de Osiris para referencia a largo plazo, liberando espacio del contexto activo.",
        "ACTION_TYPE": "AI_CONTEXT_OPTIMIZATION",
        "PARAMETERS": {
            "INFO_CATEGORY": { "TYPE": "enum", "VALUES": ["decision", "command_result", "goal", "system_status", "user_instruction", "architecture_detail", "troubleshooting"], "REQUIRED": True, "DYNAMIC": True, "NOTES": "Categoría de la información que se va a persistir." },
            "CONTENT_SUMMARY": { "TYPE": "string", "REQUIRED": True, "DYNAMIC": True, "NOTES": "Un resumen conciso de la información clave a persistir." },
            "TAGS": { "TYPE": "string", "REQUIRED": False, "DYNAMIC": True, "DEFAULT": "", "NOTES": "Etiquetas relevantes para facilitar la búsqueda futura (separadas por comas)." }
        }
    }
}
Integración con OSIRIS_INTERNAL y NOMBREx.read.info.ai:
La información persistida por PERSIST_KEY_INFO se guardaría en la base de conocimiento interna de Osiris (OSIRIS_INTERNAL), que luego podría ser consultada por mí usando SEARCH_IN_* OSIRIS_INTERNAL cuando necesite recordar detalles históricos.
Los archivos NOMBREx.read.info.ai (que documentan la arquitectura del sistema de forma curada para la IA) servirían como una base de conocimiento estática y fundamental, complementando la memoria dinámica de la conversación.
3. Retroalimentación y Adaptación Continua
Manejo de Errores (429): Si a pesar de todo se produce un error 429, el sistema debería:
Registrar un LOG_OSIRIS_* ERROR.
Disparar una poda o resumen más agresivo y forzado del conversation_context antes de reintentar la última operación (si aplica).
Notificar al usuario de forma amigable que el contexto se ha limpiado o resumido para continuar.
Aprendizaje del Desarrollador: Los logs generados por LOG_OSIRIS y las observaciones de la IA sobre la efectividad del resumen (WARN si siente que se pierde información crucial) servirán para que tú, como desarrollador, ajustes los umbrales, los parámetros de SUMMARIZE_HISTORY o mejores la lógica de resumen de la IA.
Diagrama Simplificado del Flujo Estratégico
[Usuario] <-> [gemini.py (Interfaz CLI/Web/Desktop)]
    ^                       |
    |                       | (1. Monitoreo de Tokens)
    |                       |
    | (Interacción)         v
    [Modelo LLM] <-> [conversation_context (en memoria)]
       ^                          |
       |                          | (Si > Umbral de Advertencia)
       | (AI Genera CRO:           v
       |  SUMMARIZE_HISTORY o     [IA (yo) decide optimizar contexto]
       |  PERSIST_KEY_INFO)       |
       |                          | (2.a. CRO para SUMMARIZE_HISTORY)
       |                          v
       [cro_parser (reestructurado)] <-> [Módulo de Resumen (AI-driven)]
           |                             ^
           | (2.b. CRO para            | (Resumen del historial de contexto)
           |  PERSIST_KEY_INFO)        |
           v                             |
    [Base de Conocimiento Interna de Osiris (DB/Archivos)]
        ^
        | (Consulta por AI via SEARCH_IN_OSIRIS_INTERNAL)
        |
        [Archivos NOMBREx.read.info.ai (Conocimiento Estático del Sistema)]
Esta estrategia proporciona un marco para que yo, como IA, participe activamente en la gestión de mi propio contexto, transformando el actual acumulador lineal en un sistema de memoria más dinámico y eficiente, adaptado a los límites de tokens y a la relevancia de la información.
Estoy listo para cuando el cro_parser esté reestructurado para integrar estas nuevas capacidades.