import sys
import speech_recognition as sr
import threading
import platform
import subprocess
import json
import lib.core as core
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox,QComboBox)
from PyQt5.QtCore import QThread, pyqtSignal
import os
def generar_comando_gemini(archivo_audio, nombre_archivo, prompt):
    """
    Genera el comando gemini3.py --tvl para procesar el audio.

    Args:
        archivo_audio (str): Ruta al archivo de audio.
        nombre_archivo (str): Nombre del archivo (sin extensión).
        prompt (str): Prompt para Gemini.

    Returns:
        str: El comando gemini3.py --tvl.
    """
    comando = f"gemini3.py --tvl {archivo_audio} \"{prompt}\""
    return comando
def generar_nombre_archivo(datos_audio):
    """
    Genera un nombre de archivo basado en los subsegmentos del audio.

    Args:
        datos_audio (dict): Diccionario con la información estructurada del audio.

    Returns:
        str: Un nombre de archivo.
    """
    # Extraer los dos primeros subsegmentos (si existen) para generar el nombre del archivo
    segmentos = datos_audio.get("segmentos", [])
    subsegmento1 = segmentos[0].get("tipo_segmento", "desconocido") if len(segmentos) > 0 else "inicio"
    subsegmento2 = segmentos[1].get("tipo_segmento", "desconocido") if len(segmentos) > 1 else "continuacion"
    nombre_archivo = f"nombre_{subsegmento1}_{subsegmento2}".replace(" ", "_")
    return nombre_archivo
def crear_prompt(datos_audio):
    """
    Crea un prompt optimizado para Gemini basado en los datos del audio.
    Args:
        datos_audio (dict): Diccionario con la información estructurada del audio.
    Returns:
        str: Un prompt para Gemini.
    """
    # Extraer informacion relevante para construir el prompt.
    segmentos = datos_audio.get("segmentos", [])
    prompt = "Instrucciones para Gemini: \n"

    for i, segmento in enumerate(segmentos):
        tiempo_inicio = segmento.get("tiempo_inicio")
        tiempo_fin = segmento.get("tiempo_fin")
        duracion = segmento.get("duracion")
        tiene_voz = segmento.get("tiene_voz")
        edad = segmento.get("edad") if tiene_voz else "N/A"
        sexo = segmento.get("sexo") if tiene_voz else "N/A"
        emocion = segmento.get("sensacion") if segmento.get("sensacion") else "N/A"
        ruidos = segmento.get("ruidos") if not tiene_voz else "N/A"
        tipo_ruidos = segmento.get("tipo_ruidos") if not tiene_voz else "N/A"
        
        prompt += f"Segmento {i+1}: Tiempo {tiempo_inicio}-{tiempo_fin} ({duracion}s). "
        if tiene_voz:
             prompt += f"Voz detectada (Edad: {edad}, Sexo: {sexo}, Emoción: {emocion}).\n"
        else:
             prompt += f"Sin voz. Ruidos: {ruidos} ({tipo_ruidos}), Sensación: {emocion}.\n"

    # Aquí se podría añadir lógica más compleja para personalizar el prompt en función de los datos.
    prompt += "Genera subtítulos creativos y precisos para este audio."
    return prompt

def comprobar_microfono(texto_transcripcion=None):
    """
    Comprueba si un micrófono está disponible en el sistema.
    Retorna True o false y actualiza el cuadro de texto de la GUI.
    """
    sistema = platform.system()
    try:
        reconocedor = sr.Recognizer()
        microfono = sr.Microphone()
        with microfono as source:
         reconocedor.adjust_for_ambient_noise(source)
         return True
    except sr.exceptions.WaitTimeoutError:
        print("Error: No se detectó ningún sonido del micrófono en 5 segundos. Asegúrate de que esté conectado y funcionando.")
        if  texto_transcripcion!= None :
           texto_transcripcion.insertPlainText("Error: No se detectó ningún sonido del micrófono. Asegúrate de que esté conectado y funcionando.\n")
        return False
    except Exception as e:
        print("Error con reconocimiento, probablemente falten librerías: ",e)
        if  texto_transcripcion!= None :
           texto_transcripcion.insertPlainText("Error con reconocimiento, probablemente falten librerías: "+str(e)+"\n")
        return False
def generar_comando_gemini(archivo_audio, nombre_archivo, prompt):
    """
    Genera el comando gemini3.py --tvl para procesar el audio.

    Args:
        archivo_audio (str): Ruta al archivo de audio.
        nombre_archivo (str): Nombre del archivo (sin extensión).
        prompt (str): Prompt para Gemini.

    Returns:
        str: El comando gemini3.py --tvl.
    """

    comando = f"gemini3.py --tvl {archivo_audio} \"{prompt}\""
    return comando
def generar_nombre_archivo(datos_audio):
    """
    Genera un nombre de archivo basado en los subsegmentos del audio.

    Args:
        datos_audio (dict): Diccionario con la información estructurada del audio.

    Returns:
        str: Un nombre de archivo.
    """
    # Extraer los dos primeros subsegmentos (si existen) para generar el nombre del archivo
    segmentos = datos_audio.get("segmentos", [])
    subsegmento1 = segmentos[0].get("tipo_segmento", "desconocido") if len(segmentos) > 0 else "inicio"
    subsegmento2 = segmentos[1].get("tipo_segmento", "desconocido") if len(segmentos) > 1 else "continuacion"
    nombre_archivo = f"nombre_{subsegmento1}_{subsegmento2}".replace(" ", "_")
    return nombre_archivo
def crear_prompt(datos_audio):
    """
    Crea un prompt optimizado para Gemini basado en los datos del audio.
    Args:
        datos_audio (dict): Diccionario con la información estructurada del audio.
    Returns:
        str: Un prompt para Gemini.
    """
    # Extraer informacion relevante para construir el prompt.
    segmentos = datos_audio.get("segmentos", [])
    prompt = "Instrucciones para Gemini: \n"

    for i, segmento in enumerate(segmentos):
        tiempo_inicio = segmento.get("tiempo_inicio")
        tiempo_fin = segmento.get("tiempo_fin")
        duracion = segmento.get("duracion")
        tiene_voz = segmento.get("tiene_voz")
        edad = segmento.get("edad") if tiene_voz else "N/A"
        sexo = segmento.get("sexo") if tiene_voz else "N/A"
        emocion = segmento.get("sensacion") if segmento.get("sensacion") else "N/A"
        ruidos = segmento.get("ruidos") if not tiene_voz else "N/A"
        tipo_ruidos = segmento.get("tipo_ruidos") if not tiene_voz else "N/A"
        
        prompt += f"Segmento {i+1}: Tiempo {tiempo_inicio}-{tiempo_fin} ({duracion}s). "
        if tiene_voz:
             prompt += f"Voz detectada (Edad: {edad}, Sexo: {sexo}, Emoción: {emocion}).\n"
        else:
             prompt += f"Sin voz. Ruidos: {ruidos} ({tipo_ruidos}), Sensación: {emocion}.\n"

    # Aquí se podría añadir lógica más compleja para personalizar el prompt en función de los datos.
    prompt += "Genera subtítulos creativos y precisos para este audio."
    return prompt

def generar_comentario_humano(datos_audio):
    """
    Genera un comentario para humanos que describe el comando generado.
    Args:
        datos_audio (dict): Diccionario con la información estructurada del audio.
    Returns:
        str: Un comentario para humanos.
    """
    # Extraer información relevante para el comentario
    segmentos = datos_audio.get("segmentos", [])
    num_segmentos = len(segmentos)
    primer_segmento_tipo = segmentos[0].get("tipo_segmento", "desconocido") if num_segmentos > 0 else "N/A"
    comentario = f"Comando Gemini para procesar un audio con {num_segmentos} segmentos. El primer segmento es de tipo '{primer_segmento_tipo}'."
    return comentario

def analizar_audio(archivo_audio,texto_transcripcion=None):
    """
    Analiza un archivo de audio utilizando un programa externo y retorna la información estructurada.
    Realiza comprobaciones del dispositivo de micrófono y manejo de errores.
    """
    analisis = {}
    # 1. Comprobación del dispositivo de micrófono:
    
    try:
     if not comprobar_microfono(texto_transcripcion):
        print("Error: No se detectó un micrófono. Imposible continuar con el análisis.")
        return None
    except Exception as e:
        print("Error detectando Microfono:",e)
    try:
        # 2. Ejecutar el analizador de audio (aquí es donde grabas el audio):
        print("Grabando audio...")
        if  texto_transcripcion!= None :
            texto_transcripcion.insertPlainText("Grabando Audio...\n") # transcribir al panel
            texto_transcripcion.moveCursor(QtGui.QTextCursor.End)
        # Simulación del analizador de audio
        analisis["segmentos"] = [] #Declaracion de segmentos
        analisis["parametros"] = {} #Declaracion de parametros
        #Segmento 1
        segmento = {}
        segmento["tiempo_inicio"] = "00:00:00"
        segmento["tiempo_fin"] = "00:00:05"
        segmento["duracion"] = 5
        segmento["tiene_voz"] = True
        segmento["edad"] = "30-40"
        segmento["sexo"] = "Masculino"
        segmento["emocion"] = "Neutro"
        segmento["tipo_segmento"] = "Inicio"
        analisis["segmentos"].append(segmento)
        #Segmento 2
        segmento = {}
        segmento["tiempo_inicio"] = "00:00:05"
        segmento["tiempo_fin"] = "00:00:10"
        segmento["duracion"] = 5
        segmento["tiene_voz"] = False
        segmento["ruidos"] = ["Tráfico"]
        segmento["tipo_ruidos"] = "Externo"
        segmento["sensacion"] = "Urbano"
        segmento["tipo_segmento"] = "Continuacion"
        analisis["segmentos"].append(segmento)
        #Parametros
        parametro = {}
        parametro["Frecuencia_cardiaca"] = 80
        analisis["parametros"] = parametro
        
        #Genera Ficheros para pruebas
        f = open("com/audiodata.json","w")
        json.dump(analisis,f,indent=4)
        f.close()
        if  texto_transcripcion!= None :
            texto_transcripcion.insertPlainText("Ejecutando analisis de audio simulado\n") # Transcribe
            texto_transcripcion.moveCursor(QtGui.QTextCursor.End)

        return analisis
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar analizador_de_audio: {e}")
        print(f"Salida del error: {e.stderr}") # Mostrar la salida de error
        return None
    except json.JSONDecodeError as e:
        print(f"Error al decodificar la salida JSON: {e}")
        return None
    except subprocess.TimeoutExpired:
        print("Error: El análisis de audio excedió el tiempo límite.")
        return None
def comprobar_microfono(texto_transcripcion=None):
    """
    Comprueba si un micrófono está disponible en el sistema.
    Retorna True o false y actualiza el cuadro de texto de la GUI.
    """
    sistema = platform.system()
    try:
        reconocedor = sr.Recognizer()
        microfono = sr.Microphone()
        with microfono as source:
         reconocedor.adjust_for_ambient_noise(source)
         return True
    except sr.exceptions.WaitTimeoutError:
        print("Error: No se detectó ningún sonido del micrófono en 5 segundos. Asegúrate de que esté conectado y funcionando.")
        if  texto_transcripcion!= None :
           texto_transcripcion.insertPlainText("Error: No se detectó ningún sonido del micrófono. Asegúrate de que esté conectado y funcionando.\n")
        return False
    except Exception as e:
        print("Error con reconocimiento, probablemente falten librerías: ",e)
        if  texto_transcripcion!= None :
           texto_transcripcion.insertPlainText("Error con reconocimiento, probablemente falten librerías: "+str(e)+"\n")
        return False
class HiloReconocimientoVoz(QThread):
    """
    Clase para ejecutar el reconocimiento de voz en un hilo separado para evitar bloquear la interfaz.
    """
    texto_actualizado = pyqtSignal(str)  # Señal para enviar texto a la interfaz
    fin_proceso = pyqtSignal()  # Señal para indicar el fin del proceso
    error_signal = pyqtSignal(str)  # Señal para enviar errores a la interfaz

    def __init__(self, reconocedor, microfono, texto_transcripcion, parent=None):
        super().__init__(parent)
        self.reconocedor = reconocedor
        self.microfono = microfono
        self.texto_transcripcion = texto_transcripcion
        self.correr = True  # Variable para controlar la ejecución del hilo

    def run(self):
        """
        Función principal del hilo que escucha el micrófono y transcribe el audio.
        """
        try:
            with self.microfono as fuente:
                try:
                    self.reconocedor.adjust_for_ambient_noise(fuente)  # Ajusta para el ruido ambiental
                except sr.exceptions.WaitTimeoutError:
                    self.error_signal.emit("Error: No se detectó ningún sonido del micrófono. Asegúrate de que esté conectado y funcionando.")
                    self.fin_proceso.emit()
                    return
                except Exception as e:
                    self.error_signal.emit(f"Error al ajustar para el ruido ambiental: {e}")
                    self.fin_proceso.emit()
                    return

                while self.correr:
                    try:
                        audio = self.reconocedor.listen(fuente, timeout=5)  # Escucha con un timeout de 5 segundos
                        texto = self.reconocedor.recognize_google(audio, language="es-ES")  # Transcribe
                        self.texto_actualizado.emit(texto + "\n")  # Emite la señal con el texto
                    except sr.UnknownValueError:
                        self.texto_actualizado.emit("[Sin entender]\n")  # Emite la señal de "Sin entender"
                    except sr.RequestError as e:
                        self.error_signal.emit(f"Error en la solicitud al servicio de Google: {e}")
                        break  # Sale del bucle
                    except sr.WaitTimeoutError:
                        pass  # Simplemente pasa al siguiente ciclo si no hay audio
                    except Exception as e:
                        self.error_signal.emit(f"Error inesperado durante la transcripción: {e}")
                        break  # Sale del bucle
        except Exception as e:
            self.error_signal.emit(f"Error al iniciar el hilo de grabacion: {e}\n")  # Emite la señal de finalización
        finally:
            self.fin_proceso.emit()
    def detener(self):
        """
        Función para detener el hilo de reconocimiento de voz.
        """
        self.correr = False
from PyQt5 import QtGui
class VentanaPrincipal(QWidget):
    """
    Clase principal que define la interfaz de usuario de la aplicación.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Análisis de Audio y Transcripción en Tiempo Real")
        # Inicializar componentes
        self.reconocedor = sr.Recognizer()
        self.microfono = sr.Microphone()
        self.hilo_reconocimiento = None
        # Crear widgets
        self.area_texto = QTextEdit()
        self.area_texto.setReadOnly(True)  # Hace que no se pueda escribir en la GUI
        self.etiqueta_estado = QLabel("Listo para grabar")
        self.boton_iniciar = QPushButton("Iniciar Grabación")
        self.boton_detener = QPushButton("Detener Grabación")
        self.boton_analizar = QPushButton("Analizar Audio")  # Boton para iniciar el analisis
        self.boton_exportar = QPushButton("Exportar a Archivo")  # Boton para exportar
        self.combo_fuente_audio = QComboBox() # Combo box
        self.combo_fuente_audio.addItem("Microfono")  # Add item to combo box
        self.combo_fuente_audio.addItem("Archivo")  # Add item to combo box

        self.boton_detener.setEnabled(False)  # Empieza desactivado el botón de detener
        self.boton_analizar.setEnabled(False)
       
        # Configurar layouts
        layout_horizontal = QHBoxLayout()
        layout_horizontal.addWidget(self.boton_iniciar)
        layout_horizontal.addWidget(self.boton_detener)
        layout_horizontal.addWidget(self.boton_analizar)
        layout_horizontal.addWidget(self.boton_exportar)
       
        layout_vertical = QVBoxLayout()
        layout_vertical.addWidget(self.combo_fuente_audio) #Agrega Combo a la GUI
        layout_vertical.addWidget(self.area_texto)
        layout_vertical.addWidget(self.etiqueta_estado)
        layout_vertical.addLayout(layout_horizontal)
        self.setLayout(layout_vertical)
        # Conectar eventos
        self.boton_iniciar.clicked.connect(self.iniciar_grabacion)
        self.boton_detener.clicked.connect(self.detener_grabacion)
        self.boton_analizar.clicked.connect(self.analizar_audio_main) # Conectar Boton a funcion
        self.boton_exportar.clicked.connect(self.exportar_texto) # Conectar Boton a funcion

    def iniciar_grabacion(self):
        """
        Inicia el proceso de reconocimiento de voz en un hilo separado.
        """
        self.area_texto.clear() # Limpia el area de texto

        #Funcion para elegir que metodo de grabacion utilizar
        if self.combo_fuente_audio.currentText() == "Microfono":
                self.grabar_micro()
        elif self.combo_fuente_audio.currentText() == "Archivo":
                self.grabar_archivo()
    def detener_grabacion(self):
        """
        Detiene el proceso de reconocimiento de voz.
        """
        if self.hilo_reconocimiento:
            self.hilo_reconocimiento.detener() # Llama a la funcion del hilo
            self.etiqueta_estado.setText("Deteniendo...")
        else:
            self.etiqueta_estado.setText("No hay hilo en ejecución.")

    def actualizar_texto(self, texto):
        """
        Actualiza el área de texto con el texto recibido del hilo de reconocimiento.
        """
        self.area_texto.moveCursor(QtGui.QTextCursor.End)
        self.area_texto.insertPlainText(texto)

    def finalizar_proceso(self):
        """
        Función llamada cuando el hilo de reconocimiento de voz finaliza.
        """
        self.etiqueta_estado.setText("Listo.")
        self.boton_iniciar.setEnabled(True)  # Activa el botón de inicio
        self.boton_detener.setEnabled(False) # Desactiva el botón de detener
        self.boton_analizar.setEnabled(True)
        self.hilo_reconocimiento.wait()  # Espera a que el hilo termine completamente

    def mostrar_error(self, mensaje):
        """
        Muestra un mensaje de error en un QMessageBox.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(mensaje)
        msg.setWindowTitle("Error")
        msg.exec_()
    def exportar_texto(self):
        """
        Exporta el texto del area de texto a un archivo.
        """
        texto = self.area_texto.toPlainText() # Obtiene el texto del area de texto
        if not texto:
            self.mostrar_error("No hay texto para exportar.") #Muestra el error y sale
            return
        nombre_archivo, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", "", "Text Files (*.txt);;All Files (*.*)")
        if nombre_archivo:
            try:
                with open(nombre_archivo, "w", encoding="utf-8") as archivo:
                    archivo.write(texto) #Escribe el texto en el archivo
                self.etiqueta_estado.setText(f"Texto exportado a {nombre_archivo}") #Actualiza la GUI
            except Exception as e:
                self.mostrar_error(f"Error al exportar el texto: {e}") # Envia el Error
    def grabar_micro(self):
        try:
            self.hilo_reconocimiento = HiloReconocimientoVoz(self.reconocedor, self.microfono,self.area_texto) # Crea el hilo
            self.hilo_reconocimiento.texto_actualizado.connect(self.actualizar_texto) # Conecta la señal de texto actualizado
            self.hilo_reconocimiento.fin_proceso.connect(self.finalizar_proceso) # Conecta la señal de finalizacion
            self.hilo_reconocimiento.error_signal.connect(self.mostrar_error) #Conecta con el nuevo mensaje de error en la GUI
            self.etiqueta_estado.setText("Grabando...")
            self.boton_iniciar.setEnabled(False) # Desactiva el botón de inicio
            self.boton_detener.setEnabled(True) # Activa el botón de detener
            self.boton_analizar.setEnabled(False) # Activa el botón de Análisis hasta que tenga datos para hacerlo
            self.hilo_reconocimiento.start() # Inicia el hilo
        except Exception as e: #Gestion de errores de primer nivel
            self.etiqueta_estado.setText(f"Error al Iniciar: {str(e)}")
            self.boton_iniciar.setEnabled(True)  # Asegura que el botón se active de nuevo en caso de error
            self.boton_detener.setEnabled(False)
            self.boton_analizar.setEnabled(False)

    def grabar_archivo(self):
      print("En construccion Funcion para procesar con archivo de audio en un futuro")

    def analizar_audio_main(self):
        """
        Función para accionar el Analisis y preparacion de datos que se enviaran
        a la API para su uso.
        """
        texto = self.area_texto.toPlainText() # Obtiene el texto del area de texto
        if not texto:
            self.mostrar_error("No hay texto para analizar.") #Muestra el error y sale
            return
        self.boton_analizar.setEnabled(False) #El analisis es un proceso unico que no requiere multi ejecucion para evitar confictos
        analisis = analizar_audio("audio.mp3",self.area_texto) #Obtiene datos
        print("\n\n DATOS OBTENIDOS",analisis)
        nombre_archivo = generar_nombre_archivo(analisis)  # nombre del archivo
        print("\n\n ARCHIVO OBTENIDOS",nombre_archivo)
        prompt = crear_prompt(analisis)  # propmt de texto
        print("\n\n EL PROMPT GENERADO",prompt)
        comando_gemini = generar_comando_gemini("audio.mp3",nombre_archivo,prompt)
        self.etiqueta_estado.setText(f"Comando Generado: {comando_gemini}\n")



def main(argv):
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())
    
    
