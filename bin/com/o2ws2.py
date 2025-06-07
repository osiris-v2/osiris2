#!/bin/env python3
import sys
import datetime
import random
import time
import logging
import socket # Para el "ping" TCP básico
import websocket # Para la comunicación WebSocket
import os # Nuevo: Para operaciones de archivo (guardar/cargar servidores)

# CAMBIO CLAVE (ya realizado, pero es el punto): Importación directa de las excepciones de websocket
from websocket import WebSocketConnectionClosedException, WebSocketException 

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit,
                             QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
                             QMenuBar, QMenu, QAction, QDialog, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer

# --- Configuración de Logging ---
# CAMBIO CLAVE: Establecido en DEBUG para ver todos los mensajes de depuración
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Función Auxiliar para Verificación de Puerto TCP ---
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

# --- Hilo para el Descubrimiento de Servidores (Modificado para continuo) ---
class ServerDiscoverer(QThread):
    server_found = pyqtSignal(str, int)
    log_message = pyqtSignal(str)
    discovery_finished = pyqtSignal()

    def __init__(self, ip_address, start_port, end_port, discovery_sleep_time, parent=None):
        super().__init__(parent)
        self._ip = ip_address
        self._start_port = start_port
        self._end_port = end_port
        self._discovery_sleep_time = discovery_sleep_time # Nuevo: tiempo de pausa configurable
        self._running = False
        self._found_ports = set() # Para evitar reportar el mismo puerto múltiples veces

    def run(self):
        self._running = True
        self.log_message.emit(f"Iniciando búsqueda continua de servidor en {self._ip} puertos {self._start_port}-{self._end_port}... 📡")
        
        # --- Paso 1: Intentar primero el puerto por defecto (8081) si está en rango y no se ha chequeado ---
        # Solo lo chequea una vez si está en rango y aún no fue encontrado.
        if 8081 >= self._start_port and 8081 <= self._end_port and 8081 not in self._found_ports:
            self.log_message.emit(f"Intentando conectar a {self._ip}:8081 (puerto por defecto)...")
            if _check_tcp_port(self._ip, 8081):
                self.server_found.emit(self._ip, 8081)
                self.log_message.emit(f"¡Servidor detectado en {self._ip}:8081 (puerto por defecto)! ✨")
                self._found_ports.add(8081) # Añadir a los puertos encontrados

        # --- Paso 2: Búsqueda aleatoria continua en el rango especificado ---
        while self._running:
            port = random.randint(self._start_port, self._end_port)
            
            # Si el puerto ya fue encontrado, buscar otro
            if port in self._found_ports:
                time.sleep(self._discovery_sleep_time / 5.0) # Pausa más corta si el puerto ya fue encontrado
                continue

            self.log_message.emit(f"Intentando conectar a {self._ip}:{port}...")
            if _check_tcp_port(self._ip, port):
                self.server_found.emit(self._ip, port)
                self.log_message.emit(f"¡Servidor detectado en {self._ip}:{port}! 🎉")
                self._found_ports.add(port) # Añadir a los puertos encontrados
            else:
                self.log_message.emit(f"No hay servidor en {self._ip}:{port}. Probando otro... 😔")
            
            # Pausa configurable
            time.sleep(self._discovery_sleep_time)

        self.discovery_finished.emit()
        self.log_message.emit("Proceso de descubrimiento de servidor finalizado. 🏁")

    def stop(self):
        """Detiene el bucle de descubrimiento de forma segura."""
        self._running = False

# --- Hilo para el Envío de Comandos WebSocket ---
class CommandSender(QThread):
    command_response = pyqtSignal(str)
    log_message = pyqtSignal(str)
    finished_sending = pyqtSignal() # Nuevo: señal para indicar que terminó de enviar

    def __init__(self, ip, port, command, ws_timeout, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._port = port
        self._command = command
        self._ws_timeout = ws_timeout # Almacenar el timeout

    def run(self):
        url = f"ws://{self._ip}:{self._port}"
        self.log_message.emit(f"Intentando enviar comando '{self._command}' a {url}... 💬")
        ws = None # Inicializar ws a None
        try:
            ws = websocket.create_connection(url, timeout=self._ws_timeout) # Usar el timeout configurable
            self.log_message.emit(f"Conexión WebSocket establecida con {url}. Enviando comando...")
            
            ws.send(self._command)
            result = ws.recv()

            self.command_response.emit(f"✅ Respuesta de {url} para '{self._command}':\n{result}")
            self.log_message.emit(f"Comando '{self._command}' enviado con éxito a {url}. 🎉")
            
        except WebSocketConnectionClosedException as e: # Usa la excepción directamente importada
            self.command_response.emit(f"❌ Error al enviar comando: Conexión WebSocket cerrada inesperadamente a {url}. ({e})")
            self.log_message.emit(f"ERROR: Conexión WebSocket cerrada a {url}. ({e})")
        except ConnectionRefusedError:
            self.command_response.emit(f"❌ Error al enviar comando: Conexión rechazada por {url}. Asegúrate de que el servidor esté activo. 🚫")
            self.log_message.emit(f"ERROR: Conexión rechazada por {url}.")
        except WebSocketException as e: # Captura otras excepciones generales de WebSocket
            self.command_response.emit(f"❌ Error de WebSocket al enviar comando a {url}: {type(e).__name__}: {e}")
            self.log_message.emit(f"ERROR de WebSocket inesperado al enviar comando a {url}: {type(e).__name__}: {e}")
        except Exception as e:
            self.command_response.emit(f"❌ Error al enviar comando a {url}: {type(e).__name__}: {e}")
            self.log_message.emit(f"ERROR inesperado al enviar comando a {url}: {type(e).__name__}: {e}")
        finally:
            if ws and ws.connected: # Asegura que la conexión se cierre
                ws.close()
                self.log_message.emit(f"Conexión WebSocket con {url} cerrada (finally).")
            self.finished_sending.emit() # Emitir que se terminó de enviar

# --- Hilo para el Envío Automatizado de Comandos (Stress Test) ---
class AutomatedCommandSender(QThread):
    command_response = pyqtSignal(str)
    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(int, int) # Current, Total
    finished_all = pyqtSignal()

    def __init__(self, ip, port, command, repetitions, delay_ms, ws_timeout, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._port = port
        self._command = command
        self._repetitions = repetitions
        self._delay_seconds = delay_ms / 1000.0
        self._ws_timeout = ws_timeout # Almacenar el timeout
        self._running = False

    def run(self):
        self._running = True
        url = f"ws://{self._ip}:{self._port}"
        self.log_message.emit(f"Iniciando envío automático de '{self._command}' a {url} ({self._repetitions} veces, {self._delay_seconds}s de retardo)... 🚀")

        for i in range(self._repetitions):
            if not self._running:
                self.log_message.emit("Envío automático de comandos detenido por el usuario. 🛑")
                break
            
            self.progress_update.emit(i + 1, self._repetitions)
            self.log_message.emit(f"[{i + 1}/{self._repetitions}] Enviando comando '{self._command}'...")
            
            ws = None # Inicializar ws a None
            try:
                ws = websocket.create_connection(url, timeout=self._ws_timeout) # Usar el timeout configurable
                ws.send(self._command)
                result = ws.recv()
                self.command_response.emit(f"✅ Respuesta [{i + 1}/{self._repetitions}] de {url}: {result[:100]}...") # Limitar para no saturar log
                
            except WebSocketConnectionClosedException as e: # Usa la excepción directamente importada
                self.command_response.emit(f"❌ Error [{i + 1}/{self._repetitions}]: Conexión WebSocket cerrada inesperadamente a {url}. ({e})")
                self.log_message.emit(f"ERROR: Conexión WebSocket cerrada a {url}. ({e})")
                self._running = False # Detener si la conexión se cierra
            except ConnectionRefusedError:
                self.command_response.emit(f"❌ Error [{i + 1}/{self._repetitions}]: Conexión rechazada por {url}. Asegúrate de que el servidor esté activo. 🚫")
                self.log_message.emit(f"ERROR: Conexión rechazada por {url}.")
                self._running = False # Detener si la conexión es rechazada
            except WebSocketException as e: # Captura otras excepciones generales de WebSocket
                self.command_response.emit(f"❌ Error de WebSocket [{i + 1}/{self._repetitions}] a {url}: {type(e).__name__}: {e}")
                self.log_message.emit(f"ERROR de WebSocket inesperado al enviar comando a {url}: {type(e).__name__}: {e}")
                self._running = False
            except Exception as e:
                self.command_response.emit(f"❌ Error [{i + 1}/{self._repetitions}] a {url}: {type(e).__name__}: {e}")
                self.log_message.emit(f"ERROR inesperado al enviar comando a {url}: {type(e).__name__}: {e}")
                self._running = False # Detener ante otros errores críticos
            finally:
                if ws and ws.connected: 
                    ws.close()
            
            if self._running and i < self._repetitions - 1: # No esperar después del último envío
                time.sleep(self._delay_seconds)
        
        self.log_message.emit("Envío automático de comandos finalizado. ✅")
        self.finished_all.emit()

    def stop(self):
        """Detiene el bucle de envío de forma segura."""
        self._running = False

# --- Diálogo de Configuración ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configuración de Osiris2")
        self.setModal(True) # Hace que sea un diálogo modal (bloquea la ventana principal)
        self.config = config if config is not None else {}
        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        # Configuración de Puertos por defecto
        self.default_ip_input = QLineEdit(self.config.get('default_ip', '127.0.0.1'))
        layout.addRow("IP por defecto:", self.default_ip_input)
        self.default_start_port_input = QLineEdit(str(self.config.get('default_start_port', 20000)))
        layout.addRow("Puerto Inicio por defecto:", self.default_start_port_input)
        self.default_end_port_input = QLineEdit(str(self.config.get('default_end_port', 60000)))
        layout.addRow("Puerto Fin por defecto:", self.default_end_port_input)

        # Configuración de Tiempos
        self.ping_timeout_input = QLineEdit(str(self.config.get('ping_timeout', 0.3)))
        layout.addRow("Timeout Ping (segundos):", self.ping_timeout_input)
        self.ws_timeout_input = QLineEdit(str(self.config.get('ws_timeout', 5.0)))
        layout.addRow("Timeout WebSocket (segundos):", self.ws_timeout_input)
        self.discovery_sleep_input = QLineEdit(str(self.config.get('discovery_sleep', 0.3)))
        layout.addRow("Pausa Descubrimiento (segundos):", self.discovery_sleep_input)

        # Configuración de Archivo de Servidores Guardados
        self.saved_servers_filepath_input = QLineEdit(self.config.get('saved_servers_filepath', 'osiris2_servers.txt'))
        layout.addRow("Archivo Servidores Guardados:", self.saved_servers_filepath_input)

        # Nivel de Logging (campo de texto para el nombre del nivel)
        self.logging_level_input = QLineEdit(self.config.get('logging_level', 'INFO'))
        self.logging_level_input.setPlaceholderText("INFO, DEBUG, WARNING, ERROR, CRITICAL")
        layout.addRow("Nivel de Logging:", self.logging_level_input)

        # Botones de Aceptar/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_config(self):
        # Valida y retorna la configuración
        new_config = {}
        try:
            new_config['default_ip'] = self.default_ip_input.text().strip()
            new_config['default_start_port'] = int(self.default_start_port_input.text())
            new_config['default_end_port'] = int(self.default_end_port_input.text())
            
            new_config['ping_timeout'] = float(self.ping_timeout_input.text())
            new_config['ws_timeout'] = float(self.ws_timeout_input.text())
            new_config['discovery_sleep'] = float(self.discovery_sleep_input.text())
            new_config['saved_servers_filepath'] = self.saved_servers_filepath_input.text().strip()

            new_config['logging_level'] = self.logging_level_input.text().strip().upper()
            if new_config['logging_level'] not in ['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL']:
                raise ValueError("Nivel de logging inválido. Debe ser INFO, DEBUG, WARNING, ERROR, CRITICAL.")

            # Validaciones adicionales de rangos y valores
            if not (1 <= new_config['default_start_port'] <= 65535 and 
                    1 <= new_config['default_end_port'] <= 65535 and 
                    new_config['default_start_port'] <= new_config['default_end_port']):
                raise ValueError("Rango de puertos por defecto inválido (1-65535, inicio <= fin).")
            if not (new_config['ping_timeout'] >= 0 and new_config['ws_timeout'] >= 0 and new_config['discovery_sleep'] >= 0):
                raise ValueError("Los tiempos de espera y pausa deben ser mayores o iguales a cero.")

            return new_config
        except ValueError as e:
            QMessageBox.warning(self, "Error de Configuración", f"Valor inválido: {e}. Por favor, corrige la entrada. 🔢")
            return None


# --- Interfaz de Usuario Principal ---
class ClientApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Osiris2 Cliente de Servicios 📡")
        self.discoverer_thread = None
        self.command_sender_thread = None
        self.auto_sender_thread = None # Nuevo hilo para envío automático
        self.discovered_servers = {}
        self.selected_server = None

        # Configuración por defecto (ahora se puede modificar)
        self.app_config = {
            'default_ip': '127.0.0.1',
            'default_start_port': 20000,
            'default_end_port': 60000,
            'ping_timeout': 0.3,
            'ws_timeout': 5.0,
            'discovery_sleep': 0.3,
            'logging_level': 'INFO',
            'saved_servers_filepath': 'osiris2_servers.txt' # Nuevo: ruta para guardar/cargar servidores
        }

        self.initUI()
        self.load_saved_servers() # Nuevo: Cargar servidores guardados al inicio
        self.update_ui_state() # Inicializa el estado de los botones al arrancar

    def initUI(self):
        main_layout = QVBoxLayout()
        
        # --- Configuración de la barra de menú ---
        self.menubar = QMenuBar()
        main_layout.setMenuBar(self.menubar) 
        
        self.file_menu = self.menubar.addMenu("Archivo")
        self.edit_menu = self.menubar.addMenu("Editar")
        self.config_menu = self.menubar.addMenu("Configuración")
        
        # --- Sección de Registro de Actividad (Inicializada PRONTO para que las acciones del menú puedan referenciarla) ---
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


        # --- Acciones del menú (ahora pueden conectarse a self.log_output) ---
        # Acciones del menú Archivo
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)

        # Acciones del menú Editar
        clear_log_action = QAction("Limpiar Registro", self)
        clear_log_action.setShortcut("Ctrl+L")
        clear_log_action.triggered.connect(self.log_output.clear)
        self.edit_menu.addAction(clear_log_action)

        clear_servers_action = QAction("Borrar Servidores Encontrados", self)
        clear_servers_action.triggered.connect(self.clear_discovered_servers)
        self.edit_menu.addAction(clear_servers_action)

        # NUEVO: Acciones para guardar y cargar servidores
        self.edit_menu.addSeparator() # Separador para organizar
        save_servers_action = QAction("💾 Guardar Servidores Encontrados", self)
        save_servers_action.triggered.connect(self.save_current_servers)
        self.edit_menu.addAction(save_servers_action)

        load_servers_action = QAction("📂 Cargar Servidores Guardados", self)
        load_servers_action.triggered.connect(self.load_saved_servers)
        self.edit_menu.addAction(load_servers_action)

        # Acciones del menú Configuración
        settings_action = QAction("⚙️ Ajustes de la Aplicación...", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        self.config_menu.addAction(settings_action)

        # --- Sección de Descubrimiento de Servidores ---
        discovery_group_layout = QVBoxLayout()
        discovery_group_layout.addWidget(QLabel("<h2 style='color: #2196F3;'>🔍 Descubrimiento de Servidores</h2>"))

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("IP Servidor (local/remoto):"))
        self.ip_input = QLineEdit(self.app_config['default_ip']) # Usar valor de configuración
        input_layout.addWidget(self.ip_input)
        input_layout.addWidget(QLabel("Puerto Inicio:"))
        self.start_port_input = QLineEdit(str(self.app_config['default_start_port'])) # Usar valor de configuración
        input_layout.addWidget(self.start_port_input)
        input_layout.addWidget(QLabel("Puerto Fin:"))
        self.end_port_input = QLineEdit(str(self.app_config['default_end_port'])) # Usar valor de configuración
        input_layout.addWidget(self.end_port_input)
        discovery_group_layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        self.start_discovery_button = QPushButton("▶️ Iniciar Búsqueda Continua") # Texto actualizado
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
        self.command_input = QLineEdit("/date")
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

        # Nuevo: Botón para Envío Automático / Stress Test
        self.auto_send_button = QPushButton("💣 Enviar Comando Automático (Stress Test)")
        self.auto_send_button.clicked.connect(self.start_auto_send)
        self.auto_send_button.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold;")
        command_group_layout.addWidget(self.auto_send_button)

        self.stop_auto_send_button = QPushButton("🚫 Detener Envío Automático")
        self.stop_auto_send_button.clicked.connect(self.stop_auto_send)
        self.stop_auto_send_button.setStyleSheet("background-color: #795548; color: white; font-weight: bold;")
        command_group_layout.addWidget(self.stop_auto_send_button)


        main_layout.addLayout(command_group_layout)

        main_layout.addWidget(QLabel("<hr style='border: 1px solid #ccc;'>"))

        # --- Sección de Registro de Actividad (Solo se añade el layout al main_layout) ---
        main_layout.addLayout(log_group_layout)


        self.setLayout(main_layout)
        self.setGeometry(200, 200, 800, 750) # Tamaño inicial de la ventana

    def update_ui_state(self):
        """Actualiza el estado de los botones y etiquetas según el estado de la aplicación."""
        is_discovering = (self.discoverer_thread is not None and self.discoverer_thread.isRunning())
        has_selected_server = (self.selected_server is not None)
        is_sending_single_command = (self.command_sender_thread is not None and self.command_sender_thread.isRunning())
        is_sending_auto = (self.auto_sender_thread is not None and self.auto_sender_thread.isRunning())

        # CAMBIO CLAVE: Mensaje de depuración detallado.
        logging.debug(f"UI State Update: Discovering={is_discovering}, Selected={has_selected_server}, SendingSingle={is_sending_single_command}, SendingAuto={is_sending_auto}")

        # Control de botones de descubrimiento
        self.start_discovery_button.setEnabled(not is_discovering and not is_sending_auto)
        self.stop_discovery_button.setEnabled(is_discovering)
        self.ip_input.setEnabled(not is_discovering)
        self.start_port_input.setEnabled(not is_discovering)
        self.end_port_input.setEnabled(not is_discovering)

        # Control de botones de comando/ping/auto-send
        # El botón de enviar comando individual se habilita si hay un servidor, y NINGÚN envío está en curso.
        self.send_command_button.setEnabled(has_selected_server and not is_sending_auto and not is_sending_single_command)
        
        # CAMBIO CRÍTICO AQUÍ: El botón de PING se habilita solo si hay un servidor seleccionado.
        # No se deshabilita si otras operaciones de envío están en curso, ya que es una operación ligera y no conflictiva.
        self.ping_button.setEnabled(has_selected_server) 

        # El botón de envío automático se habilita si hay un servidor, y NINGÚN envío está en curso.
        self.auto_send_button.setEnabled(has_selected_server and not is_sending_auto and not is_sending_single_command)
        self.stop_auto_send_button.setEnabled(is_sending_auto)
        
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

        self.clear_discovered_servers() # Limpiar lista y estado al iniciar nueva búsqueda
        
        self.discoverer_thread = ServerDiscoverer(
            ip, start_port, end_port, 
            self.app_config['discovery_sleep'] # Usar el tiempo de pausa configurable
        )
        self.discoverer_thread.server_found.connect(self.on_server_found)
        self.discoverer_thread.log_message.connect(self.log)
        self.discoverer_thread.discovery_finished.connect(self.on_discovery_finished)
        self.discoverer_thread.start()
        self.log(f"Búsqueda iniciada para IP: {ip}, Rango de puertos: {start_port}-{end_port}.")
        self.update_ui_state()

    def stop_discovery(self):
        """Detiene el proceso de búsqueda de servidores."""
        if self.discoverer_thread and self.discoverer_thread.isRunning():
            self.discoverer_thread.stop()
            self.log("Solicitud de detención de búsqueda enviada. 🛑")

    def on_server_found(self, ip, port):
        """Slot para manejar cuando el hilo de descubrimiento encuentra un servidor."""
        server_key = f"{ip}:{port}"
        if server_key not in self.discovered_servers:
            self.discovered_servers[server_key] = {"ip": ip, "port": port}
            item = QListWidgetItem(server_key)
            self.server_list_widget.addItem(item)
            self.log(f"¡Servidor encontrado en {server_key}! Añadido a la lista. 🎉")
            
            # CAMBIO CLAVE: Cuando se añade el primer servidor, lo seleccionamos y seteamos selected_server directamente.
            if self.server_list_widget.count() == 1:
                self.server_list_widget.setCurrentRow(0) # Esto solo lo selecciona visualmente.
                self.selected_server = (ip, port) # ¡ESTO ES LO QUE ASEGURA QUE self.selected_server TENGA UN VALOR!
                self.log(f"Primer servidor detectado y seleccionado automáticamente: {self.selected_server[0]}:{self.selected_server[1]} ✅")
            
            # Siempre actualizar el estado de la UI después de añadir un servidor.
            # Esto permitirá que los botones se habiliten si self.selected_server ya está establecido.
            self.update_ui_state() 

    def on_discovery_finished(self):
        """Slot para manejar cuando el hilo de descubrimiento termina."""
        self.log("Proceso de descubrimiento de servidor completado. 🏁")
        self.update_ui_state()

    def on_server_selection_changed(self):
        """Maneja la selección de un servidor en la lista (generalmente por interacción del usuario)."""
        selected_items = self.server_list_widget.selectedItems()
        # El mensaje de depuración detallado se ha movido a update_ui_state para centralizar el monitoreo de estado.
        if selected_items:
            server_key = selected_items[0].text()
            ip, port_str = server_key.split(':')
            self.selected_server = (ip, int(port_str))
            self.log(f"Servidor seleccionado: {self.selected_server[0]}:{self.selected_server[1]} ✅")
        else:
            self.selected_server = None
            self.log("Ningún servidor seleccionado. 😌")
        self.update_ui_state() # Esto es crucial para actualizar el estado de los botones

          
    def ping_selected_server(self):
        """Realiza un ping (verificación TCP) al servidor seleccionado."""
        if not self.selected_server:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un servidor de la lista primero para hacer ping. ☝️")
            return
        
        ip, port = self.selected_server
        self.log(f"Haciendo ping a {ip}:{port}...")
        
        # Usamos la función auxiliar global _check_tcp_port directamente con el timeout de configuración
        if _check_tcp_port(ip, port, timeout=self.app_config['ping_timeout']):
            self.log(f"Ping exitoso a {ip}:{port}. ¡Servidor activo! ✅")
        else:
            self.log(f"Ping fallido a {ip}:{port}. Servidor no responde. ❌")
        
        self.update_ui_state()

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
        
        self.update_ui_state() # Deshabilitar el botón de envío si se inicia uno

        self.command_sender_thread = CommandSender(
            ip, port, command, 
            self.app_config['ws_timeout'] # Usar el timeout configurable
        )
        self.command_sender_thread.command_response.connect(self.log)
        self.command_sender_thread.log_message.connect(self.log)
        self.command_sender_thread.finished_sending.connect(self.on_command_single_finished) # Conectar la señal de fin
        self.command_sender_thread.start()
        self.log(f"Enviando comando '{command}' a {ip}:{port}...")

    def on_command_single_finished(self):
        """Slot para manejar cuando un envío de comando individual termina."""
        self.command_sender_thread = None # Limpiar la referencia al hilo
        self.log("Envío de comando individual finalizado. 👍")
        self.update_ui_state() # Asegurarse de que el estado de los botones es correcto

    def start_auto_send(self):
        """Inicia el envío automático de comandos (stress test)."""
        if not self.selected_server:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un servidor de la lista primero para iniciar el envío automático. ☝️")
            return
        
        ip, port = self.selected_server
        command = self.command_input.text().strip()

        if not command:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce un comando para enviar. 💬")
            return

        repetitions_str, ok_rep = QInputDialog.getText(self, "Envío Automático", "Número de repeticiones:", QLineEdit.Normal, "10")
        if not ok_rep: return
        
        delay_ms_str, ok_delay = QInputDialog.getText(self, "Envío Automático", "Retardo entre envíos (milisegundos):", QLineEdit.Normal, "100")
        if not ok_delay: return

        try:
            repetitions = int(repetitions_str)
            delay_ms = int(delay_ms_str)
            if repetitions <= 0 or delay_ms < 0:
                raise ValueError("Las repeticiones deben ser > 0 y el retardo >= 0.")
        except ValueError as e:
            QMessageBox.warning(self, "Error de Entrada", f"Valor inválido: {e}. Por favor, introduce números válidos. 🔢")
            return

        if self.auto_sender_thread and self.auto_sender_thread.isRunning():
            self.log("Ya hay un envío automático en curso. Detenlo primero si deseas iniciar uno nuevo. ⏳")
            QMessageBox.information(self, "Envío en Curso", "Ya se está realizando un envío automático. Por favor, espera a que termine o deténlo. ⏳")
            return

        self.auto_sender_thread = AutomatedCommandSender(
            ip, port, command, repetitions, delay_ms, 
            self.app_config['ws_timeout'] # Usar el timeout configurable
        )
        self.auto_sender_thread.command_response.connect(self.log)
        self.auto_sender_thread.log_message.connect(self.log)
        self.auto_sender_thread.progress_update.connect(
            lambda current, total: self.log(f"Progreso de envío automático: {current}/{total}")
        )
        self.auto_sender_thread.finished_all.connect(self.on_auto_send_finished)
        self.auto_sender_thread.start()
        self.update_ui_state() # Deshabilitar botones de comando/ping/auto-send

    def stop_auto_send(self):
        """Detiene el envío automático de comandos."""
        if self.auto_sender_thread and self.auto_sender_thread.isRunning():
            self.auto_sender_thread.stop()
            self.log("Solicitud de detención de envío automático enviada. 🛑")

    def on_auto_send_finished(self):
        """Slot para manejar cuando el envío automático de comandos termina."""
        self.log("Envío automático de comandos completado/detenido. ✅")
        self.auto_sender_thread = None # Limpiar la referencia al hilo
        self.update_ui_state() # Habilitar botones de comando/ping nuevamente

    def clear_discovered_servers(self):
        """Borra la lista de servidores encontrados y la selección."""
        self.server_list_widget.clear()
        self.discovered_servers.clear()
        self.selected_server = None
        self.log("Lista de servidores encontrados y selección borradas. 🗑️")
        self.update_ui_state() # Actualizar el estado de la UI (botones de comando/ping)

    def _get_saved_servers_filepath(self):
        """Retorna la ruta completa al archivo de servidores guardados."""
        return self.app_config['saved_servers_filepath']

    def save_current_servers(self):
        """Guarda los servidores actualmente descubiertos en un archivo."""
        filepath = self._get_saved_servers_filepath()
        try:
            with open(filepath, 'w') as f:
                for server_key in self.discovered_servers.keys():
                    f.write(f"{server_key}\n")
            self.log(f"Servidores actuales guardados en: {filepath} 💾")
        except Exception as e:
            self.log(f"❌ Error al guardar servidores en {filepath}: {e}")
            QMessageBox.critical(self, "Error al Guardar", f"No se pudieron guardar los servidores: {e}")

    def load_saved_servers(self):
        """Carga servidores desde un archivo y los añade a la lista descubierta."""
        filepath = self._get_saved_servers_filepath()
        try:
            if not os.path.exists(filepath):
                self.log(f"No se encontró el archivo de servidores guardados: {filepath}. Se creará al guardar. 📂")
                return # No error, just nothing to load

            loaded_count = 0
            with open(filepath, 'r') as f:
                for line in f:
                    server_key = line.strip()
                    if not server_key: continue

                    parts = server_key.split(':')
                    if len(parts) == 2:
                        try:
                            ip = parts[0]
                            port = int(parts[1])
                            # Usar on_server_found para añadir, ya que maneja duplicados y actualización de UI
                            # Directamente llama a on_server_found para mantener la lógica centralizada
                            self.on_server_found(ip, port) 
                            loaded_count += 1 # on_server_found ya añade y actualiza el log/UI, solo contamos aquí
                        except ValueError:
                            self.log(f"Advertencia: Línea inválida en el archivo de guardado: '{line.strip()}'")
                            continue
            self.log(f"Se cargaron {loaded_count} servidores desde {filepath}. 📂")
            self.update_ui_state() # Actualizar UI después de cargar (aunque on_server_found ya lo hace en parte)
        except Exception as e:
            self.log(f"❌ Error al cargar servidores desde {filepath}: {e}")
            QMessageBox.critical(self, "Error al Cargar", f"No se pudieron cargar los servidores: {e}")


    def show_settings_dialog(self):
        """Muestra el diálogo de configuración."""
        dialog = SettingsDialog(self, config=self.app_config)
        if dialog.exec_() == QDialog.Accepted:
            new_config = dialog.get_config()
            if new_config:
                self.app_config.update(new_config)
                self.log("Configuración actualizada. Algunos cambios pueden requerir reiniciar la aplicación. ⚙️")
                # Actualizar los QLineEdit de IP/Puertos con los nuevos valores por defecto
                self.ip_input.setText(self.app_config['default_ip'])
                self.start_port_input.setText(str(self.app_config['default_start_port']))
                self.end_port_input.setText(str(self.app_config['default_end_port']))
                # Actualizar el nivel de logging en runtime
                logging.getLogger().setLevel(getattr(logging, self.app_config['logging_level']))
                self.update_ui_state()

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana para detener los hilos de forma segura."""
        self.log("Cerrando aplicación... 👋")
        # Detener hilo de descubrimiento
        if self.discoverer_thread and self.discoverer_thread.isRunning():
            self.discoverer_thread.stop()
            self.discoverer_thread.wait(1000) # Espera un máximo de 1 segundo
            if self.discoverer_thread.isRunning():
                self.log("Advertencia: Hilo de descubrimiento no terminó a tiempo. 🚨")
        
        # Detener hilo de envío automático
        if self.auto_sender_thread and self.auto_sender_thread.isRunning():
            self.auto_sender_thread.stop()
            self.auto_sender_thread.wait(1000) # Espera un máximo de 1 segundo
            if self.auto_sender_thread.isRunning():
                self.log("Advertencia: Hilo de envío automático no terminó a tiempo. 🚨")

        # Esperar a que el hilo de comando individual termine si está activo
        if self.command_sender_thread and self.command_sender_thread.isRunning():
            self.command_sender_thread.wait(1000) # Espera un máximo de 1 segundo
            if self.command_sender_thread.isRunning():
                self.log("Advertencia: Hilo de envío de comando no terminó a tiempo. 🚨")
        
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
        app = QApplication(sys.argv)

    logging.info("Aplicación Qt de cliente de servicios de Osiris2 inicializada. 🚀")

    if "INIT" in args:
        logging.info("Argumento 'INIT' detectado. Preparando la interfaz de cliente.")

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
    main(sys.argv[1:])