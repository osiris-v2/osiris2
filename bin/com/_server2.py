#!/bin/env python3
import sys
import datetime
import random
import time
import logging
import socket # Para el "ping" TCP básico
import websocket # Para la comunicación WebSocket
import json # Para manejar posibles mensajes JSON sobre WebSocket

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QListWidget, QListWidgetItem, QInputDialog, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer

# --- Configuración de Logging ---
# Puedes cambiar a logging.DEBUG para ver mensajes muy detallados en consola (útil para depuración)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Función Auxiliar para Verificación de Puerto TCP ---
# Esta función es independiente de las clases y puede ser usada por diferentes partes.
def _check_tcp_port(ip, port, timeout=0.3):
    """
    Intenta una conexión TCP a una IP y puerto dados para verificar si está abierto.
    Retorna True si el puerto está abierto y False en caso contrario.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout) # Tiempo de espera corto para la conexión
    try:
        sock.connect((ip, port))
        sock.shutdown(socket.SHUT_RDWR) # Cerrar la conexión limpia
        sock.close()
        return True
    except (socket.error, ConnectionRefusedError, socket.timeout):
        return False # No se pudo conectar o fue rechazada/timeout
    except Exception as e:
        # Registra cualquier otro error inesperado en la consola, no en la GUI directamente desde aquí
        logging.error(f"Error inesperado durante la verificación de puerto {ip}:{port}: {type(e).__name__}: {e}", exc_info=True)
        return False
    finally:
        if sock:
            sock.close()


# --- Hilo para el Descubrimiento de Servidores ---
class ServerDiscoverer(QThread):
    # Señales para comunicar resultados al hilo principal de la GUI
    server_found = pyqtSignal(str, int) # Emite IP, Puerto cuando encuentra un servidor
    log_message = pyqtSignal(str) # Emite mensajes para el log de la GUI
    discovery_finished = pyqtSignal() # Emite cuando el descubrimiento se detiene

    def __init__(self, ip_address, start_port, end_port, parent=None):
        super().__init__(parent)
        self._ip = ip_address
        self._start_port = start_port
        self._end_port = end_port
        self._running = False # Flag para controlar el bucle de descubrimiento
        self._found_default = False # Para saber si ya encontramos el puerto 8081

    def run(self):
        self._running = True
        self.log_message.emit(f"Iniciando búsqueda de servidor en {self._ip} puertos {self._start_port}-{self._end_port}... 📡")
        
        # --- Paso 1: Intentar primero el puerto por defecto (8081) ---
        # Asegúrate de que el puerto 8081 esté dentro del rango especificado por el usuario
        if 8081 >= self._start_port and 8081 <= self._end_port and not self._found_default:
            self.log_message.emit(f"Intentando conectar a {self._ip}:8081 (puerto por defecto)...")
            # Usamos la función auxiliar _check_tcp_port
            if _check_tcp_port(self._ip, 8081):
                self.server_found.emit(self._ip, 8081)
                self.log_message.emit(f"¡Servidor detectado en {self._ip}:8081 (puerto por defecto)! ✨")
                self._found_default = True
                self._running = False # Detener la búsqueda si se encuentra el puerto por defecto
                # No emitimos discovery_finished aquí si queremos que el proceso de detención sea unificado
                # al salir del bucle. Sin embargo, el código original salía aquí.
                # Para mantener el comportamiento original de "encontró y salió", lo dejamos.
                # Si se quiere seguir buscando aleatoriamente aunque se encuentre el default, quitar el "return" y el "_running = False".
                self.discovery_finished.emit() # Emitir que ha terminado el descubrimiento
                return # Salir del método run

        # --- Paso 2: Búsqueda aleatoria en el rango especificado ---
        # El bucle continúa solo si _running sigue siendo True (es decir, si no se encontró el default y se salió)
        while self._running:
            port = random.randint(self._start_port, self._end_port)
            # Evitar re-chequear el 8081 si ya lo encontramos y no paramos o si se sigue buscando
            if port == 8081 and self._found_default: # Si el 8081 ya fue encontrado y seguimos buscando, saltarlo
                continue

            self.log_message.emit(f"Intentando conectar a {self._ip}:{port}...")
            # Usamos la función auxiliar _check_tcp_port
            if _check_tcp_port(self._ip, port):
                self.server_found.emit(self._ip, port)
                self.log_message.emit(f"¡Servidor detectado en {self._ip}:{port}! 🎉")
                self._running = False # Detener después de encontrar uno aleatorio también.
            else:
                self.log_message.emit(f"No hay servidor en {self._ip}:{port}. Probando otro... 😔")
            
            # Pequeña pausa para no saturar el CPU o la red y permitir que la UI responda
            time.sleep(0.3)

        self.discovery_finished.emit() # Se emite una vez que el bucle `while self._running` ha terminado
        self.log_message.emit("Proceso de descubrimiento de servidor finalizado. 🏁")

    def stop(self):
        """
        Detiene el bucle de descubrimiento de forma segura y no bloqueante.
        Simplemente establece la bandera _running en False. El hilo saldrá de su bucle
        cuando termine la operación actual (check_tcp_port o sleep).
        """
        self._running = False
        # Importante: No llamar a self.wait() aquí. self.wait() bloquearía la GUI
        # mientras espera que el hilo termine, lo que anularía el propósito de un botón de "detener".
        # La señal `discovery_finished` se encargará de actualizar el estado de la UI.


# --- Hilo para el Envío de Comandos WebSocket ---
class CommandSender(QThread):
    command_response = pyqtSignal(str) # Emite la respuesta del comando
    log_message = pyqtSignal(str) # Emite mensajes de log

    def __init__(self, ip, port, command, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._port = port
        self._command = command

    def run(self):
        url = f"ws://{self._ip}:{self._port}"
        self.log_message.emit(f"Intentando enviar comando '{self._command}' a {url}... 💬")
        try:
            ws = websocket.create_connection(url, timeout=5) # Añadir un timeout a la conexión WS
            self.log_message.emit(f"Conexión WebSocket establecida con {url}. Enviando comando...")
            
            ws.send(self._command)
            result = ws.recv() # Espera la respuesta del servidor

            self.command_response.emit(f"✅ Respuesta de {url} para '{self._command}':\n{result}")
            self.log_message.emit(f"Comando '{self._command}' enviado con éxito a {url}. 🎉")
            ws.close()
        except websocket._exceptions.WebSocketConnectionClosedException as e:
            self.command_response.emit(f"❌ Error al enviar comando: Conexión WebSocket cerrada inesperadamente a {url}. ({e})")
            self.log_message.emit(f"ERROR: Conexión WebSocket cerrada a {url}. ({e})")
        except ConnectionRefusedError:
            self.command_response.emit(f"❌ Error al enviar comando: Conexión rechazada por {url}. Asegúrate de que el servidor esté activo. 🚫")
            self.log_message.emit(f"ERROR: Conexión rechazada por {url}.")
        except Exception as e:
            self.command_response.emit(f"❌ Error al enviar comando a {url}: {type(e).__name__}: {e}")
            self.log_message.emit(f"ERROR inesperado al enviar comando a {url}: {type(e).__name__}: {e}")
        finally:
            # Asegura que la conexión se cierre si está abierta y conectada
            if 'ws' in locals() and ws.connected: 
                ws.close()
                self.log_message.emit(f"Conexión WebSocket con {url} cerrada (finally).")


# --- Interfaz de Usuario Principal ---
class ClientApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Osiris2 Cliente de Servicios 📡")
        self.discoverer_thread = None
        self.command_sender_thread = None
        self.discovered_servers = {} # Almacena {IP:Puerto: {"ip": ip, "port": port}}
        self.selected_server = None # Tupla (IP, Puerto) del servidor seleccionado
        self.initUI()
        self.update_ui_state() # Inicializa el estado de los botones al arrancar

    def initUI(self):
        main_layout = QVBoxLayout()

        # --- Sección de Descubrimiento de Servidores ---
        discovery_group_layout = QVBoxLayout()
        discovery_group_layout.addWidget(QLabel("<h2 style='color: #2196F3;'>🔍 Descubrimiento de Servidores</h2>"))

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("IP Servidor (local/remoto):"))
        self.ip_input = QLineEdit("127.0.0.1") # Por defecto a localhost
        input_layout.addWidget(self.ip_input)
        input_layout.addWidget(QLabel("Puerto Inicio (20000):"))
        self.start_port_input = QLineEdit("20000")
        input_layout.addWidget(self.start_port_input)
        input_layout.addWidget(QLabel("Puerto Fin (60000):"))
        self.end_port_input = QLineEdit("60000")
        input_layout.addWidget(self.end_port_input)
        discovery_group_layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        self.start_discovery_button = QPushButton("▶️ Iniciar Búsqueda Aleatoria")
        self.start_discovery_button.clicked.connect(self.start_discovery)
        self.start_discovery_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.start_discovery_button)

        self.stop_discovery_button = QPushButton("⏸️ Detener Búsqueda")
        self.stop_discovery_button.clicked.connect(self.stop_discovery)
        self.stop_discovery_button.setStyleSheet("background-color: #FFC107; color: black; font-weight: bold;")
        button_layout.addWidget(self.stop_discovery_button)
        discovery_group_layout.addLayout(button_layout)

        discovery_group_layout.addWidget(QLabel("<h3 style='color: #607D8B;'>Servidores Encontrados:</h3>"))
        self.server_list_widget = QListWidget()
        self.server_list_widget.setMinimumHeight(100)
        # Conecta la selección del elemento con un método
        self.server_list_widget.itemSelectionChanged.connect(self.on_server_selection_changed)
        self.server_list_widget.setStyleSheet("border: 1px solid #ddd; padding: 5px;")
        discovery_group_layout.addWidget(self.server_list_widget)
        main_layout.addLayout(discovery_group_layout)

        main_layout.addWidget(QLabel("<hr style='border: 1px solid #ccc;'>"))

        # --- Sección de Envío de Comandos ---
        command_group_layout = QVBoxLayout()
        command_group_layout.addWidget(QLabel("<h2 style='color: #9C27B0;'>💬 Envío de Comandos</h2>"))

        self.selected_server_label = QLabel("Servidor Seleccionado: <span style='color: #e67e22;'>Ninguno</span>")
        self.selected_server_label.setStyleSheet("font-size: 1.1em; font-weight: bold;")
        command_group_layout.addWidget(self.selected_server_label)

        command_input_layout = QHBoxLayout()
        command_input_layout.addWidget(QLabel("Comando a enviar (ej: `/date`):"))
        self.command_input = QLineEdit("/date") # Comando por defecto
        command_input_layout.addWidget(self.command_input)

        self.send_command_button = QPushButton("➡️ Enviar Comando al Servidor")
        self.send_command_button.clicked.connect(self.send_command)
        self.send_command_button.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold;")
        command_input_layout.addWidget(self.send_command_button)
        command_group_layout.addLayout(command_input_layout)

        self.ping_button = QPushButton("⚡ Ping Servidor Seleccionado")
        self.ping_button.clicked.connect(self.ping_selected_server)
        self.ping_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        command_group_layout.addWidget(self.ping_button)

        main_layout.addLayout(command_group_layout)

        main_layout.addWidget(QLabel("<hr style='border: 1px solid #ccc;'>"))

        # --- Sección de Registro de Actividad ---
        log_group_layout = QVBoxLayout()
        log_group_layout.addWidget(QLabel("<h2 style='color: #607D8B;'>📝 Registro de Actividad y Respuestas</h2>"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(200)
        self.log_output.setStyleSheet("border: 1px solid #ddd; padding: 5px; background-color: #f9f9f9;")
        log_group_layout.addWidget(self.log_output)

        self.clear_log_button = QPushButton("🧹 Limpiar Registro")
        self.clear_log_button.clicked.connect(self.log_output.clear)
        self.clear_log_button.setStyleSheet("background-color: #B0BEC5; color: black; font-weight: bold;")
        log_group_layout.addWidget(self.clear_log_button)

        main_layout.addLayout(log_group_layout)

        self.setLayout(main_layout)
        self.setGeometry(200, 200, 800, 750) # Tamaño inicial de la ventana

    def update_ui_state(self):
        """Actualiza el estado de los botones y etiquetas según el estado de la aplicación."""
        # Se verifica si el hilo de descubrimiento existe y está activo
        is_discovering = (self.discoverer_thread is not None and self.discoverer_thread.isRunning())
        has_selected_server = (self.selected_server is not None)

        # Control de botones de descubrimiento
        self.start_discovery_button.setEnabled(not is_discovering)
        self.stop_discovery_button.setEnabled(is_discovering) # Habilitar detener solo si está descubriendo
        self.ip_input.setEnabled(not is_discovering)
        self.start_port_input.setEnabled(not is_discovering)
        self.end_port_input.setEnabled(not is_discovering)

        # Control de botones de comando/ping
        self.send_command_button.setEnabled(has_selected_server)
        self.ping_button.setEnabled(has_selected_server)
        
        # Actualizar etiqueta de servidor seleccionado
        if has_selected_server:
            self.selected_server_label.setText(f"Servidor Seleccionado: <span style='color: #e67e22;'>{self.selected_server[0]}:{self.selected_server[1]}</span>")
        else:
            self.selected_server_label.setText("Servidor Seleccionado: <span style='color: #e67e22;'>Ninguno</span>")


    def log(self, message):
        """Añade un mensaje al log de la GUI y al logger de consola."""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3] # Con milisegundos
        self.log_output.append(f"[{timestamp}] {message}")
        logging.info(message) # También envía a la consola para depuración

    def start_discovery(self):
        """Inicia el proceso de búsqueda de servidores."""
        ip = self.ip_input.text().strip()
        try:
            start_port = int(self.start_port_input.text())
            end_port = int(self.end_port_input.text())
            if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port):
                QMessageBox.warning(self, "Error de Puerto", "Rango de puertos inválido. Debe ser entre 1 y 65535 y el inicio <= fin. 🚫")
                return
        except ValueError:
            QMessageBox.warning(self, "Error de Entrada", "Por favor, introduce números válidos para los puertos. 🔢")
            return

        if self.discoverer_thread and self.discoverer_thread.isRunning():
            self.log("La búsqueda ya está en curso. Deténla primero si deseas iniciar una nueva. ⚠️")
            return

        self.server_list_widget.clear() # Limpiar lista de servidores anteriores
        self.discovered_servers.clear()
        self.selected_server = None
        # update_ui_state() se llamará después de iniciar el hilo para reflejar el estado "descubriendo"

        self.discoverer_thread = ServerDiscoverer(ip, start_port, end_port)
        self.discoverer_thread.server_found.connect(self.on_server_found)
        self.discoverer_thread.log_message.connect(self.log)
        self.discoverer_thread.discovery_finished.connect(self.on_discovery_finished)
        self.discoverer_thread.start() # Iniciar el hilo de descubrimiento
        self.log(f"Búsqueda iniciada para IP: {ip}, Rango de puertos: {start_port}-{end_port}.")
        self.update_ui_state() # <<< ¡Importante! Actualizar el estado de la UI DESPUÉS de que el hilo ha comenzado

    def stop_discovery(self):
        """Detiene el proceso de búsqueda de servidores."""
        if self.discoverer_thread and self.discoverer_thread.isRunning():
            self.discoverer_thread.stop() # Llama al método stop no bloqueante del hilo
            self.log("Solicitud de detención de búsqueda enviada. 🛑")
            # on_discovery_finished se encargará de actualizar el UI state cuando el hilo termine su ejecución actual

    def on_server_found(self, ip, port):
        """Slot para manejar cuando el hilo de descubrimiento encuentra un servidor."""
        server_key = f"{ip}:{port}"
        if server_key not in self.discovered_servers:
            self.discovered_servers[server_key] = {"ip": ip, "port": port}
            item = QListWidgetItem(server_key)
            self.server_list_widget.addItem(item)
            self.log(f"¡Servidor encontrado en {server_key}! Añadido a la lista. 🎉")
            # Seleccionar automáticamente el primer servidor encontrado si no hay ninguno
            if self.server_list_widget.count() == 1:
                self.server_list_widget.setCurrentRow(0)
            self.update_ui_state() # Actualizar estado por si es el primer servidor encontrado

    def on_discovery_finished(self):
        """Slot para manejar cuando el hilo de descubrimiento termina."""
        self.log("Proceso de descubrimiento de servidor completado. 🏁")
        self.update_ui_state() # Habilitar inputs de puerto y start button, deshabilitar stop

    def on_server_selection_changed(self):
        """Maneja la selección de un servidor en la lista."""
        selected_items = self.server_list_widget.selectedItems()
        if selected_items:
            server_key = selected_items[0].text()
            ip, port_str = server_key.split(':')
            self.selected_server = (ip, int(port_str))
            self.log(f"Servidor seleccionado: {self.selected_server[0]}:{self.selected_server[1]} ✅")
        else:
            self.selected_server = None
            self.log("Ningún servidor seleccionado. 😌")
        self.update_ui_state() # Actualizar el estado de los botones de comando/ping

    def ping_selected_server(self):
        """Realiza un ping (verificación TCP) al servidor seleccionado."""
        if not self.selected_server:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un servidor de la lista primero para hacer ping. ☝️")
            return
        
        ip, port = self.selected_server
        self.log(f"Haciendo ping a {ip}:{port}...")
        
        # Usamos la función auxiliar global _check_tcp_port directamente
        if _check_tcp_port(ip, port):
            self.log(f"Ping exitoso a {ip}:{port}. ¡Servidor activo! ✅")
        else:
            self.log(f"Ping fallido a {ip}:{port}. Servidor no responde. ❌")

    def send_command(self):
        """Envía el comando especificado al servidor seleccionado vía WebSocket."""
        if not self.selected_server:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un servidor de la lista primero para enviar comandos. ☝️")
            return

        ip, port = self.selected_server
        command = self.command_input.text().strip()

        if not command:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce un comando para enviar. 💬")
            return

        if self.command_sender_thread and self.command_sender_thread.isRunning():
            self.log("Ya hay un comando en curso. Por favor, espera a que termine. ⏳")
            QMessageBox.information(self, "Comando en Curso", "Ya se está enviando un comando. Por favor, espera a que termine. ⏳")
            return

        self.command_sender_thread = CommandSender(ip, port, command)
        self.command_sender_thread.command_response.connect(self.log)
        self.command_sender_thread.log_message.connect(self.log)
        self.command_sender_thread.start()
        self.log(f"Enviando comando '{command}' a {ip}:{port}...")

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana para detener los hilos de forma segura."""
        self.log("Cerrando aplicación... 👋")
        if self.discoverer_thread and self.discoverer_thread.isRunning():
            self.discoverer_thread.stop() # Pide al hilo que se detenga
            self.discoverer_thread.wait(2000) # Espera un máximo de 2 segundos para que termine
            if self.discoverer_thread.isRunning():
                self.log("Advertencia: El hilo de descubrimiento no terminó a tiempo. Puede haber recursos pendientes. 🚨")
        if self.command_sender_thread and self.command_sender_thread.isRunning():
            # No hay un método stop para CommandSender, solo esperamos que termine su tarea actual
            self.command_sender_thread.wait(2000) # Espera un máximo de 2 segundos
            if self.command_sender_thread.isRunning():
                self.log("Advertencia: El hilo de envío de comando no terminó a tiempo. 🚨")
        
        self.log("Aplicación cerrada. ¡Hasta pronto! 👋")
        event.accept()

# --- Función Principal de Arranque ---
def main(args):
    """
    Punto de entrada principal de la aplicación.
    Recibe argumentos, incluyendo 'INIT' según la especificación.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv) # QApplication siempre necesita sys.argv

    logging.info("Aplicación Qt de cliente de servicios de Osiris2 inicializada. 🚀")

    # Si se pasa 'INIT' como argumento, se puede realizar alguna inicialización específica
    if "INIT" in args:
        logging.info("Argumento 'INIT' detectado. Preparando la interfaz de cliente.")
        # Aquí podrías añadir lógica para un arranque específico si 'INIT' lo requiere,
        # como cargar configuraciones iniciales o verificar pre-requisitos.

    try:
        window = ClientApp()
        window.show()
        logging.info(f"Ventana de cliente lanzada. Geometría: x={window.geometry().x()}, y={window.geometry().y()}, ancho={window.geometry().width()}, alto={window.geometry().height()}")
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Error CRÍTICO al lanzar la ventana principal del cliente: {e}", exc_info=True)
        QMessageBox.critical(None, "Error de Aplicación", f"Ocurrió un error crítico al iniciar la aplicación cliente: {e}\nConsulta los logs para más detalles.")
        sys.exit(1)

if __name__ == "__main__":
    # Pasa sys.argv[1:] para que main reciba solo los argumentos, no el nombre del script
    main(sys.argv[1:])