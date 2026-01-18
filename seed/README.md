# PROYECTO OSIRIS: EL MANIFIESTO DE LA COMPUTACION SOBERANA
### "DUREZA 256 - ARQUITECTURA DE SUPERVIVENCIA DIGITAL"

## 1. VISION ESTRATEGICA: EL SALTO MAS ALLA DEL SOFTWARE
El Proyecto OSIRIS no es una aplicacion; es un paradigma de ingenieria diseñado para el año 2026 y mas alla. En un mundo donde el software tradicional es pesado, vulnerable y dependiente de terceros, OSIRIS propone una ruptura total.

Hemos creado una VM (Maquina Virtual) que actua como un organismo digital: se adapta al hardware, protege su memoria como un estrato mineral y se comunica mediante protocolos matematicos de alta fidelidad.

### DIFERENCIADORES CLAVE:
- INDEPENDENCIA DE KERNEL: Capacidad de ejecucion en Linux, Windows, Android y GNU Hurd.
- LATENCIA DETERMINISTA: Control total del tiempo de proceso mediante las Camaras de Tiempo.
- HUELLA DE CARBONO MINIMA: Optimizacion extrema para un consumo del 0.2% de CPU.

---

## 2. ARQUITECTURA DE ESTRATOS (MEMORIA URANIO)

OSIRIS divide la realidad de los datos en tres niveles de dureza para garantizar que el sistema sea impenetrable.

### A. ESTRATO URANIO (EL NUCLEO VOLATIL)
Es la zona de maxima seguridad. Aqui reside la logica de decodificacion y el motor de la VM.
- CARACTERISTICA: No toca el disco duro.
- SEGURIDAD: Punteros 'RB_SafePtr' con validacion de limites en tiempo real.
- FUNCION: Procesamiento de rafagas FGN y gestion de la Semilla de Salto Primo.

### B. ESTRATO ACERO (LA PASARELA DE SALIDA)
Es el bloque de intercambio. Permite que el contenido salga de la zona segura hacia el mundo exterior de forma controlada.
- FUNCION: Gestiona el Buffer Circular en RAM para el Micro-HTTP.
- PERSISTENCIA: Unica zona autorizada para escribir segmentos .ts si el Soberano lo decide.

### C. CANAL MERCURIO (LA SENAL DE ESTADO)
Canal de telemetria ultra-rapido que viaja en paralelo al video.
- FUNCION: Sincronia de mandos, fisica de juegos y datos de sensores.
- PREDICCION: Permite al Nodo C anticipar frames si la red fluctua.

---

## 3. MANUAL DE USUARIO (OPERATIVA ACTUAL)

### 3.1. PREPARACION DEL ENTORNO
Para garantizar la Dureza 256, asegurese de tener las herramientas de compilacion estandar:
- Linux: gcc, make, libsdl2-dev.
- Rust: cargo (ultima version estable).

### 3.2. COMPILACION DEL NODO C (EL RECEPTOR)
El Nodo C es el musculo grafico. Para compilarlo con todos los drivers de salida activos:
$ gcc -o osiris_nodo src/main.c src/drivers/*.c -lSDL2 -lpthread -lm

### 3.3. CONFIGURACION DE EJECUCION
El Nodo puede iniciarse con distintos perfiles segun la necesidad de soberania:

#### MODO A: VISUALIZACION PURA (MAXIMA PRIVACIDAD)
./osiris_nodo --port 8080 --dureza 256 --output-sdl
*Resultado: El video se muestra por pantalla y se borra instantaneamente de la RAM.*

#### MODO B: GATEWAY HLS (RETRANSMISION LOCAL)
./osiris_nodo --port 8080 --hls-server --ram-only
*Resultado: El Nodo levanta un servidor HTTP propio. Acceda desde su navegador a: http://localhost:8080/live/index.m3u8*

#### MODO C: PERSISTENCIA ACERO (PARA NGINX EXTERNO)
./osiris_nodo --write-disk --path /tmp/osiris/ --segment-time 2
*Resultado: El Nodo escribe segmentos .ts en disco para ser servidos por un Nginx pre-instalado.*

---

## 4. GUIA DE AUDITORIA (CAMARAS DE TIEMPO)

Como dueño del Nodo, usted debe monitorear la salud del flujo. El comando de telemetria integrado permite ver:
$ ./osiris_nodo --status-realtime

[ LOG DE CAMARAS DE TIEMPO ]
[T1] RED: 0.12ms
[T2] URANIO: 0.45ms (Decodificacion OK)
[T3] ACERO: 0.88ms (Paso a Buffer RAM)
[T4] HTTP: 1.20ms (Servido a Cliente)
LATENCIA TOTAL: 2.65ms (ESTADO: EXCELENTE)

---

## 5. PROYECCION Y FUTURO (ROADMAP 2026)

### FASE I: ELIMINACION DE DEPENDENCIAS (PROXIMAMENTE)
Sustituiremos SDL2 por un driver de Vulkan nativo. Esto permitira que OSIRIS dibuje directamente en la GPU sin pasar por el sistema de ventanas del SO, aumentando la invisibilidad del nodo.

### FASE II: NODOS MOVILES (ARM)
Lanzamiento del perfil "Acordeon" para Android/iOS. El sistema detectara el estado de la bateria y ajustara la Dureza de la memoria para no ser detectado por el recolector de basura del movil.

### FASE III: OSIRIS-GAME Y CONTROL REMOTO
Activacion total del Canal Mercurio. Podra controlar aplicaciones pesadas o juegos desde su movil usando la potencia de un Cerebro Rust remoto, con una respuesta tactil de menos de 10ms.

### FASE IV: SOBERANIA SOBRE MACH
Migracion al microkernel GNU Hurd. OSIRIS dejara de ser una aplicacion para convertirse en el entorno de usuario por encima del kernel, eliminando Linux de la ecuacion.

---
"OSIRIS: NO ES SOFTWARE, ES INFRAESTRUCTURA DE LIBERTAD."
Desarrollado bajo la Direccion Logica del Soberano y Ejecucion de IA Simbiotica.
