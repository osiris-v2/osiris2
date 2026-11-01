# Este archivo contendrá el mapeo de comandos para Gemini.
# Puedes añadir contenido específico aquí si lo necesitas.
# Mapeo de comandos cortos
commands_map = {
            "--arw":["--auto_response_window", "Abre respuestas en ventana (on/off)"],
            "--cm":["--cromode", "Activa modo CRO (on/off) Carga develop.info"],
            "--load": "--l",   # lee y carga el texto de un archivo en memoria
            "--addload": "--al", #add load  añade el texto último cargado en memoria
            "--showload": "--sl", #show load  muestra contenido cargado en memoria
            "--li": ["--loadimage", "Carga una imagen que envia a la IA desde una url, formato --li LINK texto propmt."],
            "--sw": ["--showwin", " Muestra todo el contexto en una ventana"],
            "--arc":["--add-response-context","Añade la última respuesta del modelo al contexto"],
            "--ctm":["--context-mode","Selecciona modo de contexto conmutando, si fast añade preguntas y respuestas al contexto, si False añande sólo las preguntas al contexto"],
            "--sshc":["--ssh-connection","Establece una conexión ssh y sftp persistentes --sshc [argumentos] - También Manejado por CRO "],
            "--saveload": "--sav",
            "--saverequest": "--sr",
            "--saveanswer": "--sa",
            "--savecontext": "--sc",
            "--autosave": "--as",
            "--newquestions": "--nq",
            "--send": "--s",
            "--listfiles": "--ls",
            "--cc":["--clearcontext","Borra el contexto en uso. Expórtese con --exp Nombre antes si quiere conservarlo."],
            "--loadselect": "--lsel",
            "--loadmultiple": "--lm",
            "--info": "--i",
            "--exp": ["--export","Exporta un contexto y lo guarda en disco que puede ser recuperado con --import nombreArchivo "],
            "--imp": ["--import","Importa un contexto previamente guardado con --export nombreArchivo "],
            "--search": "--s",
            "--settopic": "--st",
            "--reset": "--r",
            "--loadconfig": "--lc",  # Nuevo: Cargar configuración
            "--log": "--log",        # Nuevo: Registrar interacciones en el log
            "--setparams": "--sp",   # Nuevo: Configurar parámetros del modelo
            "--toggleautosave": "--ta",  # Nuevo: Activar/desactivar autosave
            "--listmodels":"--lms", #Lista los modelos genai
            "--selectgenailmodel":"--sgm",
            "--aap": ["--audio-auto-parse", "Activa el reproductor de audio automático para cada respuesta  "],
            "--ap":["--audio-parse","Genera el audio de la última respuesta y lo reproduce"],
            "--apr":["--audio-parse-repeat","Reproduce el último audio generado"],
            "--sla":["--show-last-answer","Muestra la última respuesta en una ventana asistente"],
            "--tvl":["--translate-video-link","subtitula video, debe usar semillas (seems @) @ (@subtitulos @fbold @color @creative etc... consultar documentación.) para activar esta funcionalidad explícita"],
            "--li":"--load-image",
            "--asla":"--audio-save-last-answer", #Copia la última respuesta procesada por audio a un nombre pasado como parámetro guardándolo en com/datas.
            "--cmc":"--cromode-commute", #cambia el estado de auto cromode a true / false
            "--ctm":"--context-mode", #Modos de Contexto
            "--loc":"--load-osiris-context" #cargas multiples e instrucciones desde json
}

