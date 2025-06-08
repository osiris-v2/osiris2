#!/usr/bin/env python3

import os
import sys
import re
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog,
    QCheckBox, QRadioButton, QGroupBox, QComboBox,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QMenu, QMessageBox, QAbstractItemView, QSizePolicy, QTabWidget,
    QAction, QDockWidget, QToolBar, QStatusBar
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, pyqtSlot, QProcess, QSettings, Qt, QUrl, QTimer, QSize
)
from PyQt5.QtGui import QDesktopServices, QIcon, QIntValidator # Importar QIntValidator directamente

# Interfaz Name: Osiris Downloader AI
# Version: 6.0.0 (Fix: Double Alert, Enhanced Vertical Resizing, Integrated Dir Selector)
# Idioma: Español
# Instrucciones: ¡Bienvenido a Osiris Downloader AI! 🚀
# Usa emojis para dinamizar la conversación.

# --- Clase del Hilo de Descarga (Worker) ---
# Este hilo se encarga de ejecutar el comando yt-dlp y parsear su salida
# para actualizar la interfaz gráfica sin bloquearla.
class DownloadWorker(QThread):
    """
    QThread para gestionar un único proceso de descarga de yt-dlp.
    Emite señales para actualizaciones de progreso, finalización y errores.
    """
    # Señales emitidas por este worker:
    progress_update = pyqtSignal(str, float, str, str) # URL, porcentaje, velocidad, eta
    status_update = pyqtSignal(str, str, str) # URL, estado (ej. "Descargando"), o una línea de log raw
    download_finished = pyqtSignal(str, int) # URL, código de salida (0 para éxito)
    download_error = pyqtSignal(str, str) # URL, mensaje de error

    def __init__(self, url: str, output_dir: str, file_name_template: str, 
                 format_option: str, additional_options: dict, parent=None):
        super().__init__(parent)
        self.url = url
        self.output_dir = output_dir
        self.file_name_template = file_name_template
        self.format_option = format_option
        self.additional_options = additional_options
        self._is_stopped = False # Bandera para detener la descarga de forma controlada
        self.process: subprocess.Popen = None # Referencia al proceso subprocess
        
        # Expresión regular para parsear la línea de progreso de yt-dlp
        self.progress_regex = re.compile(
            r'\[download\]\s+(?P<percentage>\d+\.\d+)% of (~(?P<size>[\d\.]+[KMGT]?iB))? at (?P<speed>[\d\.]+[KMG]?iB/s)? ETA (?P<eta>[\d\:]+)?'
        )
        # Expresión regular para capturar el nombre del archivo de destino (útil para el log)
        self.file_destination_regex = re.compile(r'\[download\] Destination: (.+)')

    def run(self):
        """
        Método principal de ejecución para el hilo.
        Construye y ejecuta el comando yt-dlp.
        """
        if self._is_stopped:
            self.status_update.emit(self.url, "Cancelado", "")
            return

        self.status_update.emit(self.url, "Inicializando...", "")
        
        command = self._build_ytdlp_command()
        # Log del comando completo
        self.status_update.emit(self.url, "LOG", f"# Comando yt-dlp ejecutado:\n# {' '.join(command)}")

        try:
            # Usando subprocess.Popen directamente para leer stdout/stderr
            # Esto permite un control más granular sobre el parsing del progreso.
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Unir stdout y stderr para un parsing más fácil
                text=True,                 # Decodificar la salida como texto
                bufsize=1,                 # Procesar línea por línea (line-buffered)
                universal_newlines=True    # Manejar saltos de línea multi-plataforma
            )
            
            self.status_update.emit(self.url, "Descargando...", "")
            
            for line in self.process.stdout:
                if self._is_stopped:
                    self.process.terminate() # Solicitar terminación amigable
                    self.status_update.emit(self.url, "Cancelado por usuario", "")
                    break
                
                # Emitir la línea cruda de salida para el log principal
                self.status_update.emit(self.url, "LOG", line.strip())
                
                # Parsear información de progreso
                match = self.progress_regex.search(line)
                if match:
                    percentage = float(match.group('percentage'))
                    speed = match.group('speed') if match.group('speed') else 'N/A'
                    eta = match.group('eta') if match.group('eta') else 'N/A'
                    self.progress_update.emit(self.url, percentage, speed, eta)
                
                # Capturar el nombre del archivo de destino una vez que yt-dlp lo informe
                file_match = self.file_destination_regex.search(line)
                if file_match:
                    self.status_update.emit(self.url, "Destino:", file_match.group(1))
                
            self.process.wait() # Esperar a que el proceso termine completamente
            exit_code = self.process.returncode

            if self._is_stopped:
                self.download_finished.emit(self.url, -1) # -1 para indicar cancelación por usuario
            elif exit_code == 0:
                self.status_update.emit(self.url, "Completado", "")
                self.download_finished.emit(self.url, 0)
            else:
                # Leer cualquier salida restante si el proceso falló
                remaining_output = ""
                try:
                    remaining_output = self.process.stdout.read()
                except ValueError: # If stream is closed
                    pass
                error_message = f"yt-dlp salió con código {exit_code}:\n{remaining_output}"
                self.download_error.emit(self.url, error_message)
                self.status_update.emit(self.url, f"Error (código {exit_code})", "")

        except FileNotFoundError:
            msg = "Error: yt-dlp no encontrado. Asegúrate de que esté instalado y en tu PATH. 💥"
            self.download_error.emit(self.url, msg)
            self.status_update.emit(self.url, "Error: yt-dlp no encontrado", "")
        except Exception as e:
            msg = f"Error inesperado al ejecutar yt-dlp: {e} 💔"
            self.download_error.emit(self.url, msg)
            self.status_update.emit(self.url, "Error inesperado", "")

    def stop(self):
        """Marca la bandera para detener el proceso de descarga y termina el subprocess."""
        self._is_stopped = True
        if self.process and self.process.poll() is None: # Si el proceso aún está corriendo
            self.process.terminate() # Solicitar terminación amigable
            # Añadir un pequeño retraso y luego forzar la terminación si es necesario
            QTimer.singleShot(1000, lambda: self.process.kill() if self.process.poll() is None else None)
            self.status_update.emit(self.url, "Solicitando detención...", "")

    def _build_ytdlp_command(self) -> list:
        """Construye la lista de comandos de yt-dlp basándose en las opciones seleccionadas."""
        command = ["yt-dlp"]

        # Directorio de salida y plantilla de nombre de archivo
        output_template = os.path.join(self.output_dir, self.file_name_template)
        command.extend(["-o", f"{output_template}.%(ext)s"])

        # Selección de formato
        if self.format_option in ["mp3", "aac", "flac", "wav", "opus"]:
            command.extend(["-x", "--audio-format", self.format_option])
            # Si se seleccionó solo audio con un formato específico desde opciones avanzadas
            # y el formato principal no es ya el mismo formato de audio avanzado
            if self.additional_options["audio_format"] and \
               self.additional_options["audio_format_val"] and \
               self.additional_options["audio_format_val"] != self.format_option:
                command[-1] = self.additional_options["audio_format_val"] # Override with custom audio format
        else:
            # Para formatos de video, generalmente queremos mejor video + best audio.
            command.extend(["-f", "bestvideo+bestaudio/best"]) 
            if self.format_option: # Si se selecciona un contenedor de video específico (mp4, mkv, webm)
                command.extend(["--recode-video", self.format_option])

        # Opciones adicionales
        if self.additional_options["audio_only"]:
             # Ya se maneja si el formato principal es audio_only. Si no, añadir -x
            if self.format_option not in ["mp3", "aac", "flac", "wav", "opus"]:
                command.extend(["-x"])
                if self.additional_options["audio_format"] and self.additional_options["audio_format_val"]:
                     # Solo añade --audio-format si no es el mismo que el formato principal de audio ya seleccionado
                     if self.format_option not in ["mp3", "aac", "flac", "wav", "opus"] or \
                        self.additional_options["audio_format_val"] != self.format_option:
                        command.extend(["--audio-format", self.additional_options["audio_format_val"]])
                else: # Default to mp3 if audio_only is checked but no specific audio format selected
                    # Evitar duplicar si el formato principal ya es mp3
                    if self.format_option != "mp3":
                        command.extend(["--audio-format", "mp3"])

        if self.additional_options["limit_speed"] and self.additional_options["speed_limit_val"]:
            command.extend(["-r", self.additional_options["speed_limit_val"]])

        if self.additional_options["max_quality"]:
            # Esto puede ser redundante si el formato ya es 'bestvideo+bestaudio'
            # pero es seguro si hay otros -f que pudieran ser sobreescritos
            if "bestvideo+bestaudio" not in command: # Evitar duplicados
                command.extend(["-f", "bestvideo+bestaudio"]) 

        if self.additional_options["embed_thumbnail"]:
            command.append("--embed-thumbnail")
        if self.additional_options["embed_metadata"]:
            command.append("--embed-metadata")
        
        if self.additional_options["add_headers"] and self.additional_options["headers_val"]:
            headers_str = self.additional_options["headers_val"]
            if headers_str:
                for header in headers_str.split(';'):
                    header = header.strip()
                    if ':' in header:
                        command.extend(["--add-header", header])
        
        if self.additional_options["cookies_from_browser"] and self.additional_options["browser_val"]:
            command.extend(["--cookies-from-browser", self.additional_options["browser_val"]])
        
        if self.additional_options["username"] and self.additional_options["username_val"]:
            command.extend(["--username", self.additional_options["username_val"]])
        if self.additional_options["password"] and self.additional_options["password_val"]:
            command.extend(["--password", self.additional_options["password_val"]]) # yt-dlp handles securely

        if self.additional_options["playlist_start"] and self.additional_options["playlist_start_val"]:
            command.extend(["--playlist-start", self.additional_options["playlist_start_val"]])
        if self.additional_options["playlist_end"] and self.additional_options["playlist_end_val"]:
            command.extend(["--playlist-end", self.additional_options["playlist_end_val"]])
        
        if self.additional_options["proxy"] and self.additional_options["proxy_val"]:
            command.extend(["--proxy", self.additional_options["proxy_val"]])
        
        if self.additional_options["custom_args"] and self.additional_options["custom_args_val"]:
            custom_args_list = self.additional_options["custom_args_val"].strip().split()
            command.extend(custom_args_list)

        command.append(self.url)
        return command

# --- Clase Principal de la Aplicación (GUI) ---
class OsirisDownloaderApp(QMainWindow): # Hereda de QMainWindow
    """
    Ventana principal de la aplicación Osiris Downloader.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Osiris Downloader AI 🚀")
        self.setWindowIcon(QIcon(self.resource_path("osiris_icon.png"))) # Establece un icono si existe
        self.resize(1000, 700) # Establecer un tamaño inicial razonable

        # Ruta del directorio de salida (se guarda/carga en la configuración)
        self.output_dir = QSettings("OsirisInnovations", "OsirisDownloaderAI").value(
            "output_directory", os.path.expanduser("~"), type=str
        )
        self.is_downloading = False # Bandera para saber si hay descargas en curso
        self.download_threads = {} # Diccionario para QThreads activos: {URL: DownloadWorker}
        self.download_queue = [] # Lista de URLs pendientes de procesar
        self.current_download_idx = 0 # Índice para el procesamiento secuencial
        self.max_parallel_downloads = 3 # Número máximo de descargas en paralelo simultáneas

        # Variables internas para almacenar el estado de las opciones (se guardan/cargan)
        self.download_mode_parallel = False
        self.format_option_value = "mp4" # Valor por defecto

        # Diccionario para gestionar el estado de todas las opciones adicionales
        # Los valores se inicializan y luego se sincronizan con la GUI y las QSettings
        self.additional_options_vars = {
            "audio_only": False,
            "limit_speed": False,
            "speed_limit_val": "", # Valor de la velocidad
            "max_quality": False,
            "embed_thumbnail": False,
            "embed_metadata": False,
            "auto_output_naming": True, # Nueva opción: nombrar automáticamente
            "custom_output_name": "", # Nueva: nombre de salida personalizado
            "audio_format": False, # Indica si se usará un formato de audio específico
            "audio_format_val": "mp3", # El valor del formato de audio específico
            "add_headers": False,
            "headers_val": "",
            "cookies_from_browser": False,
            "browser_val": "chrome", # Navegador por defecto para cookies
            "username": False,
            "username_val": "",
            "password": False,
            "password_val": "",
            "playlist_start": False,
            "playlist_start_val": "1",
            "playlist_end": False,
            "playlist_end_val": "",
            "proxy": False,
            "proxy_val": "",
            "custom_args": False,
            "custom_args_val": "",
        }

        self.init_ui() # Inicializa la interfaz de usuario
        self.create_docks() # Crea los paneles acoplables
        self.create_menus() # Crea los menús de la ventana principal
        self.load_settings() # Carga las configuraciones guardadas
        self.update_ui_from_settings() # Sincroniza la GUI con las configuraciones cargadas
        
        # Muestra el directorio de salida cargado, ahora en la pestaña de opciones
        # y no en el label principal.
        self.statusBar().showMessage("Osiris Downloader AI listo. ¡Que empiecen las descargas! ✨")


    def resource_path(self, relative_path: str) -> str:
        """Obtiene la ruta absoluta de un recurso."""
        try:
            # PyInstaller crea una carpeta temporal y la guarda en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def init_ui(self):
        """Inicializa el diseño y los widgets principales de la interfaz de usuario central."""
        # Se crea un QWidget central para contener los elementos que no serán dockables
        central_widget = QWidget()
        main_central_layout = QVBoxLayout()
        
        # --- Entrada de URLs ---
        url_group = QGroupBox("URLs para Descargar (una por línea) 🔗")
        url_layout = QVBoxLayout()
        self.urls_text_edit = QTextEdit()
        self.urls_text_edit.setPlaceholderText("Pega tus URLs aquí (ej. YouTube, Vimeo, Twitch, etc.)...")
        # Ya no establecemos un minimumHeight explícito aquí para la flexibilidad.
        self.urls_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Resizable verticalmente
        self._setup_url_text_edit_context_menu() # Añadir menú contextual de clic derecho
        url_layout.addWidget(self.urls_text_edit)
        url_group.setLayout(url_layout)
        main_central_layout.addWidget(url_group)

        # --- Opciones de Descarga (Usando QTabWidget dentro de un QGroupBox colapsable) ---
        self.options_collapsible_group = QGroupBox("Opciones de Descarga ✨")
        # Para que el QGroupBox pueda ser colapsable mediante su título
        self.options_collapsible_group.setCheckable(True) 
        self.options_collapsible_group.setChecked(True) # Por defecto, expandido
        # Conectamos la señal 'toggled' para mostrar/ocultar el contenido
        self.options_collapsible_group.toggled.connect(self.toggle_options_panel)

        options_layout_container = QVBoxLayout() # Contenedor para el QTabWidget
        self.options_tab_widget = QTabWidget()
        self.options_tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 

        # --- Pestaña: General y Nombres ---
        general_naming_tab = QWidget()
        general_naming_layout = QFormLayout()

        # Panel de Selección de Directorio (Movido aquí)
        dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel(f"Seleccionado: {self.output_dir}")
        self.output_dir_label.setWordWrap(True)
        self.output_dir_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        dir_layout.addWidget(self.output_dir_label, 1)
        select_dir_button = QPushButton("Seleccionar")
        select_dir_button.clicked.connect(self.select_output_dir)
        dir_layout.addWidget(select_dir_button)
        general_naming_layout.addRow("Directorio de Salida 📂:", dir_layout)

        # Modo de Descarga (Secuencial/Paralelo)
        mode_layout = QHBoxLayout()
        self.sequential_radio = QRadioButton("Descarga Secuencial ➡️")
        self.sequential_radio.setChecked(True)
        self.parallel_radio = QRadioButton("Descarga en Paralelo ⚡")
        mode_layout.addWidget(self.sequential_radio)
        mode_layout.addWidget(self.parallel_radio)
        general_naming_layout.addRow("Modo:", mode_layout)
        self.sequential_radio.toggled.connect(lambda: self._update_option_var("download_mode_parallel", self.parallel_radio.isChecked()))

        # Selección de Formato
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "MP4 (Video)", "MKV (Video)", "WEBM (Video)",
            "MP3 (Audio Only)", "AAC (Audio Only)", "FLAC (Audio Only)", "WAV (Audio Only)", "OPUS (Audio Only)"
        ])
        self.format_combo.currentIndexChanged.connect(self.update_format_option)
        format_layout.addWidget(self.format_combo)
        general_naming_layout.addRow("Formato de Salida:", format_layout)

        # Nombres de Archivo de Salida
        output_name_layout = QHBoxLayout()
        self.auto_name_checkbox = QCheckBox("Nombrar automáticamente (+1, +2, etc. si múltiple)")
        self.auto_name_checkbox.setChecked(True)
        self.custom_output_name_edit = QLineEdit()
        self.custom_output_name_edit.setPlaceholderText("Nombre de archivo personalizado (sin extensión)")
        self.custom_output_name_edit.setDisabled(True)
        output_name_layout.addWidget(self.auto_name_checkbox)
        output_name_layout.addWidget(self.custom_output_name_edit)
        general_naming_layout.addRow("Nombres de Archivo:", output_name_layout)
        self.auto_name_checkbox.toggled.connect(self.toggle_custom_output_name_field)
        self.auto_name_checkbox.toggled.connect(lambda state: self._update_option_var("auto_output_naming", bool(state)))
        self.custom_output_name_edit.textChanged.connect(lambda text: self._update_option_var("custom_output_name", text))
        
        general_naming_tab.setLayout(general_naming_layout)
        self.options_tab_widget.addTab(general_naming_tab, "General y Nombres ⚙️")

        # --- Pestaña: Opciones Básicas ---
        basic_options_tab = QWidget()
        basic_options_layout = QFormLayout()

        self.audio_only_checkbox = QCheckBox("Extraer solo audio (ignorar video)")
        self.audio_only_checkbox.toggled.connect(lambda state: self._update_option_var("audio_only", bool(state)))
        basic_options_layout.addRow(self.audio_only_checkbox)

        speed_limit_h_layout = QHBoxLayout()
        self.limit_speed_checkbox = QCheckBox("Limitar velocidad de descarga:")
        self.limit_speed_checkbox.toggled.connect(self.toggle_speed_limit_input)
        self.speed_limit_input = QLineEdit()
        self.speed_limit_input.setPlaceholderText("Ej: 500K, 1M (K/M/G para KB/MB/GB/s)")
        self.speed_limit_input.setDisabled(True)
        self.speed_limit_input.textChanged.connect(lambda text: self._update_option_var("speed_limit_val", text))
        speed_limit_h_layout.addWidget(self.limit_speed_checkbox)
        speed_limit_h_layout.addWidget(self.speed_limit_input)
        basic_options_layout.addRow(speed_limit_h_layout)

        self.max_quality_checkbox = QCheckBox("Descargar con la mejor calidad disponible")
        self.max_quality_checkbox.toggled.connect(lambda state: self._update_option_var("max_quality", bool(state)))
        basic_options_layout.addRow(self.max_quality_checkbox)

        self.embed_thumbnail_checkbox = QCheckBox("Incrustar miniatura en el archivo de salida")
        self.embed_thumbnail_checkbox.toggled.connect(lambda state: self._update_option_var("embed_thumbnail", bool(state)))
        basic_options_layout.addRow(self.embed_thumbnail_checkbox)

        self.embed_metadata_checkbox = QCheckBox("Incrustar metadatos (título, descripción, etc.)")
        self.embed_metadata_checkbox.toggled.connect(lambda state: self._update_option_var("embed_metadata", bool(state)))
        basic_options_layout.addRow(self.embed_metadata_checkbox)

        basic_options_tab.setLayout(basic_options_layout)
        self.options_tab_widget.addTab(basic_options_tab, "Opciones Básicas 🛠️")


        # --- Pestaña: Opciones Avanzadas ---
        advanced_options_tab = QWidget()
        advanced_options_layout = QFormLayout()
        
        audio_format_layout = QHBoxLayout()
        self.audio_format_checkbox = QCheckBox("Formato de Audio Específico:")
        self.audio_format_checkbox.toggled.connect(self.toggle_audio_format_combo)
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "aac", "flac", "wav", "opus"])
        self.audio_format_combo.setDisabled(True)
        self.audio_format_combo.currentIndexChanged.connect(lambda: self._update_option_var("audio_format_val", self.audio_format_combo.currentText()))
        audio_format_layout.addWidget(self.audio_format_checkbox)
        audio_format_layout.addWidget(self.audio_format_combo)
        advanced_options_layout.addRow(audio_format_layout)

        headers_layout = QHBoxLayout()
        self.add_headers_checkbox = QCheckBox("Añadir Cabeceras Personalizadas (Key: Value; ...):")
        self.add_headers_checkbox.toggled.connect(self.toggle_headers_input)
        self.headers_input = QLineEdit()
        self.headers_input.setPlaceholderText("User-Agent: Mozilla/5.0; Referer: example.com")
        self.headers_input.setDisabled(True)
        self.headers_input.textChanged.connect(lambda text: self._update_option_var("headers_val", text))
        headers_layout.addWidget(self.add_headers_checkbox)
        headers_layout.addWidget(self.headers_input)
        advanced_options_layout.addRow(headers_layout)

        cookies_layout = QHBoxLayout()
        self.cookies_checkbox = QCheckBox("Usar Cookies del Navegador:")
        self.cookies_checkbox.toggled.connect(self.toggle_browser_combo)
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["chrome", "firefox", "edge", "safari", "opera", "brave"])
        self.browser_combo.setDisabled(True)
        self.browser_combo.currentIndexChanged.connect(lambda: self._update_option_var("browser_val", self.browser_combo.currentText()))
        cookies_layout.addWidget(self.cookies_checkbox)
        cookies_layout.addWidget(self.browser_combo)
        advanced_options_layout.addRow(cookies_layout)

        auth_layout = QHBoxLayout()
        self.username_checkbox = QCheckBox("Usuario:")
        self.username_checkbox.toggled.connect(self.toggle_username_input)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario (ej. para Patreon)")
        self.username_input.setDisabled(True)
        self.username_input.textChanged.connect(lambda text: self._update_option_var("username_val", text))
        auth_layout.addWidget(self.username_checkbox)
        auth_layout.addWidget(self.username_input)
        advanced_options_layout.addRow(auth_layout)

        password_layout = QHBoxLayout()
        self.password_checkbox = QCheckBox("Contraseña:")
        self.password_checkbox.toggled.connect(self.toggle_password_input)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setDisabled(True)
        self.password_input.textChanged.connect(lambda text: self._update_option_var("password_val", text))
        password_layout.addWidget(self.password_checkbox)
        password_layout.addWidget(self.password_input)
        advanced_options_layout.addRow(password_layout)
        
        playlist_range_layout = QHBoxLayout()
        self.playlist_start_checkbox = QCheckBox("Playlist desde item #:")
        self.playlist_start_checkbox.toggled.connect(self.toggle_playlist_start_input)
        self.playlist_start_input = QLineEdit()
        self.playlist_start_input.setPlaceholderText("1")
        self.playlist_start_input.setValidator(QIntValidator(1, 99999))
        self.playlist_start_input.setDisabled(True)
        self.playlist_start_input.textChanged.connect(lambda text: self._update_option_var("playlist_start_val", text))
        
        self.playlist_end_checkbox = QCheckBox("hasta item #:")
        self.playlist_end_checkbox.toggled.connect(self.toggle_playlist_end_input)
        self.playlist_end_input = QLineEdit()
        self.playlist_end_input.setPlaceholderText("fin")
        self.playlist_end_input.setValidator(QIntValidator(1, 99999))
        self.playlist_end_input.setDisabled(True)
        self.playlist_end_input.textChanged.connect(lambda text: self._update_option_var("playlist_end_val", text))
        
        playlist_range_layout.addWidget(self.playlist_start_checkbox)
        playlist_range_layout.addWidget(self.playlist_start_input)
        playlist_range_layout.addWidget(self.playlist_end_checkbox)
        playlist_range_layout.addWidget(self.playlist_end_input)
        advanced_options_layout.addRow("Rango de Playlist:", playlist_range_layout)

        proxy_layout = QHBoxLayout()
        self.proxy_checkbox = QCheckBox("Usar Proxy:")
        self.proxy_checkbox.toggled.connect(self.toggle_proxy_input)
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("Ej: socks5://localhost:9050 o http://user:pass@host:port")
        self.proxy_input.setDisabled(True)
        self.proxy_input.textChanged.connect(lambda text: self._update_option_var("proxy_val", text))
        proxy_layout.addWidget(self.proxy_checkbox)
        proxy_layout.addWidget(self.proxy_input)
        advanced_options_layout.addRow(proxy_layout)

        custom_args_layout = QHBoxLayout()
        self.custom_args_checkbox = QCheckBox("Argumentos Custom de yt-dlp:")
        self.custom_args_checkbox.toggled.connect(self.toggle_custom_args_input)
        self.custom_args_input = QLineEdit()
        self.custom_args_input.setPlaceholderText("Ej: --ignore-errors --no-mtime --verbose")
        self.custom_args_input.setDisabled(True)
        self.custom_args_input.textChanged.connect(lambda text: self._update_option_var("custom_args_val", text))
        custom_args_layout.addWidget(self.custom_args_checkbox)
        custom_args_layout.addWidget(self.custom_args_input)
        advanced_options_layout.addRow(custom_args_layout)

        advanced_options_tab.setLayout(advanced_options_layout)
        self.options_tab_widget.addTab(advanced_options_tab, "Avanzadas ⚙️")

        options_layout_container.addWidget(self.options_tab_widget)
        self.options_collapsible_group.setLayout(options_layout_container) # Establecer el layout dentro del QGroupBox colapsable
        main_central_layout.addWidget(self.options_collapsible_group) # Añadir el grupo colapsable al layout principal

        # --- Botones de Control ---
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Descarga ⬇️")
        self.start_button.clicked.connect(self.start_download)
        self.start_button.setStyleSheet("background-color: #28a745; color: white; padding: 10px; font-weight: bold;")
        
        self.stop_button = QPushButton("Detener Descarga 🛑")
        self.stop_button.clicked.connect(self.stop_all_downloads)
        self.stop_button.setStyleSheet("background-color: #dc3545; color: white; padding: 10px; font-weight: bold;")
        self.stop_button.setDisabled(True)

        self.clear_queue_button = QPushButton("Limpiar Cola 🧹")
        self.clear_queue_button.clicked.connect(self.clear_download_queue)
        self.clear_queue_button.setStyleSheet("background-color: #ffc107; color: black; padding: 10px;")

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_queue_button)
        main_central_layout.addLayout(button_layout)
        
        central_widget.setLayout(main_central_layout)
        self.setCentralWidget(central_widget) # Establecer el widget central de la QMainWindow

        self._apply_styles() # Aplica estilos QSS para una mejor estética

    def create_docks(self):
        """Crea los QDockWidget para la cola de descargas y el registro de salida."""
        # --- Cola de Descargas y Visualización de Progreso (Dockable) ---
        self.download_queue_dock = QDockWidget("Cola de Descargas y Progreso 📊", self)
        self.download_queue_dock.setObjectName("DownloadQueueDock") # Para guardar/cargar estado de dock
        self.download_queue_dock.setAllowedAreas(Qt.AllDockWidgetAreas) # Permitir todas las áreas

        queue_content_widget = QWidget()
        queue_layout = QVBoxLayout(queue_content_widget)
        self.download_table = QTableWidget()
        self.download_table.setColumnCount(5)
        self.download_table.setHorizontalHeaderLabels(["URL", "Progreso", "Estado", "Velocidad", "ETA"])
        self.download_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.download_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.download_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.download_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.download_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.download_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.download_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Permite que la tabla se encoja a su tamaño mínimo de contenido (cabeceras + 1 fila)
        queue_layout.addWidget(self.download_table)
        self.download_queue_dock.setWidget(queue_content_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.download_queue_dock)
        # No se establece minimumHeight en el dock, para que sea flexible.


        # --- Registro de Salida (Dockable) ---
        self.output_log_dock = QDockWidget("Registro de Salida 📝", self)
        self.output_log_dock.setObjectName("OutputLogDock") # Para guardar/cargar estado de dock
        self.output_log_dock.setAllowedAreas(Qt.AllDockWidgetAreas) # Permitir todas las áreas

        log_content_widget = QWidget()
        log_layout = QVBoxLayout(log_content_widget)
        self.output_log_text = QTextEdit()
        self.output_log_text.setReadOnly(True)
        # Ya no establecemos un minimumHeight explícito aquí para la flexibilidad.
        self.output_log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Asegurar que sea expandible
        self.output_log_text.ensureCursorVisible()
        log_layout.addWidget(self.output_log_text)
        self.output_log_dock.setWidget(log_content_widget)
        # Añadirlo al mismo área que el anterior para que se apilen como pestañas por defecto
        self.tabifyDockWidget(self.download_queue_dock, self.output_log_dock)
        # No se establece minimumHeight en el dock, para que sea flexible.


    def create_menus(self):
        """Crea la barra de menú de la QMainWindow."""
        menubar = self.menuBar()
        view_menu = menubar.addMenu("Ver 👀")

        # Acciones para mostrar/ocultar docks
        toggle_queue_action = self.download_queue_dock.toggleViewAction()
        toggle_queue_action.setText("Mostrar Cola de Descargas")
        toggle_queue_action.setToolTip("Muestra u oculta el panel de la cola de descargas")
        view_menu.addAction(toggle_queue_action)

        toggle_log_action = self.output_log_dock.toggleViewAction()
        toggle_log_action.setText("Mostrar Registro de Salida")
        toggle_log_action.setToolTip("Muestra u oculta el panel del registro de salida")
        view_menu.addAction(toggle_log_action)
        
        view_menu.addSeparator()

        # Acción para mostrar/ocultar el panel de opciones (QGroupBox)
        toggle_options_action = QAction("Mostrar/Ocultar Opciones", self)
        toggle_options_action.setCheckable(True)
        toggle_options_action.setChecked(self.options_collapsible_group.isChecked())
        toggle_options_action.triggered.connect(self.options_collapsible_group.setChecked) 
        view_menu.addAction(toggle_options_action)
        self.options_collapsible_group.toggled.connect(toggle_options_action.setChecked) # Sincroniza el action con el groupbox

    def toggle_options_panel(self, checked: bool):
        """Muestra u oculta el contenido del QTabWidget dentro del grupo colapsable."""
        self.options_tab_widget.setVisible(checked)
        # Puedes añadir animaciones aquí si lo deseas, pero QWidget.setVisible es suficiente para funcionalidad.
        # self.options_collapsible_group.adjustSize() # Ajusta el tamaño del grupo padre


    def _setup_url_text_edit_context_menu(self):
        """Configura el menú contextual (clic derecho) para el área de texto de URLs."""
        menu = QMenu(self)
        menu.addAction("Cortar", self.urls_text_edit.cut)
        menu.addAction("Copiar", self.urls_text_edit.copy)
        menu.addAction("Pegar", self.urls_text_edit.paste)
        menu.addSeparator()
        menu.addAction("Seleccionar Todo", self.urls_text_edit.selectAll)
        self.urls_text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.urls_text_edit.customContextMenuRequested.connect(
            lambda pos: menu.exec_(self.urls_text_edit.mapToGlobal(pos))
        )

    def _update_option_var(self, key: str, value):
        """Actualiza el diccionario interno para las opciones."""
        self.additional_options_vars[key] = value

    # --- Métodos para controlar el estado de los widgets de opciones ---
    def toggle_custom_output_name_field(self, checked: bool):
        """Habilita/deshabilita el campo de nombre de salida personalizado."""
        self.custom_output_name_edit.setDisabled(checked)
        if checked: # Si el nombramiento automático está habilitado, borra el nombre personalizado para evitar confusiones
            self.custom_output_name_edit.clear()

    def update_format_option(self, index: int):
        """Actualiza la variable interna del formato de salida según la selección del QComboBox."""
        selected_text = self.format_combo.currentText()
        # Mapea el texto de visualización a los códigos de formato de yt-dlp
        format_map = {
            "MP4 (Video)": "mp4", "MKV (Video)": "mkv", "WEBM (Video)": "webm",
            "MP3 (Audio Only)": "mp3", "AAC (Audio Only)": "aac", "FLAC (Audio Only)": "flac",
            "WAV (Audio Only)": "wav", "OPUS (Audio Only)": "opus"
        }
        self.format_option_value = format_map.get(selected_text, "mp4")
        
        # Deshabilita la opción "Extraer solo audio" si el formato principal ya es solo audio
        if self.format_option_value in ["mp3", "aac", "flac", "wav", "opus"]:
            self.audio_only_checkbox.setChecked(True)
            self.audio_only_checkbox.setDisabled(True)
            self.audio_format_checkbox.setDisabled(True) # Deshabilita el checkbox de formato de audio específico
            self.audio_format_combo.setDisabled(True) # Deshabilita el combo de formato de audio específico
            # Asegurar que la opción interna de audio_format_val se sincronice con el formato principal
            self._update_option_var("audio_only", True) # Fuerza la opción a True
            self._update_option_var("audio_format_val", self.format_option_value)
            self._update_option_var("audio_format", False) # Desactivar el checkbox de formato específico si el principal ya es audio
        else:
            self.audio_only_checkbox.setDisabled(False)
            # Solo re-habilita el checkbox de formato de audio específico si no está ya forzado por audio_only
            if not self.additional_options_vars["audio_only"]:
                self.audio_format_checkbox.setDisabled(False)
            # Re-habilita el combo solo si el checkbox está marcado
            if self.audio_format_checkbox.isChecked():
                self.audio_format_combo.setDisabled(False)


    def toggle_speed_limit_input(self, checked: bool):
        self.speed_limit_input.setDisabled(not checked)
        self._update_option_var("limit_speed", checked)

    def toggle_audio_format_combo(self, checked: bool):
        self.audio_format_combo.setDisabled(not checked)
        self._update_option_var("audio_format", checked) # Actualizar el estado del checkbox
        # Si se desactiva, borrar el valor para que no se use un formato específico
        if not checked:
            self._update_option_var("audio_format_val", "")

    def toggle_headers_input(self, checked: bool):
        self.headers_input.setDisabled(not checked)
        self._update_option_var("add_headers", checked)

    def toggle_browser_combo(self, checked: bool):
        self.browser_combo.setDisabled(not checked)
        self._update_option_var("cookies_from_browser", checked)

    def toggle_username_input(self, checked: bool):
        self.username_input.setDisabled(not checked)
        self._update_option_var("username", checked)
    
    def toggle_password_input(self, checked: bool):
        self.password_input.setDisabled(not checked)
        self._update_option_var("password", checked)

    def toggle_playlist_start_input(self, checked: bool):
        self.playlist_start_input.setDisabled(not checked)
        self._update_option_var("playlist_start", checked)

    def toggle_playlist_end_input(self, checked: bool):
        self.playlist_end_input.setDisabled(not checked)
        self._update_option_var("playlist_end", checked)
        
    def toggle_proxy_input(self, checked: bool):
        self.proxy_input.setDisabled(not checked)
        self._update_option_var("proxy", checked)

    def toggle_custom_args_input(self, checked: bool):
        self.custom_args_input.setDisabled(not checked)
        self._update_option_var("custom_args", checked)

    def select_output_dir(self):
        """Abre un diálogo para seleccionar el directorio de salida."""
        new_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Salida", self.output_dir)
        if new_dir:
            self.output_dir = new_dir
            # Solo actualizamos el QLabel dentro de la pestaña, no el log principal al inicio
            self.output_dir_label.setText(f"Seleccionado: {self.output_dir}")
            self.save_settings() # Guardar la configuración inmediatamente

    def update_output_dir_display(self):
        """Actualiza el QLabel con el directorio de salida actual."""
        self.output_dir_label.setText(f"Seleccionado: {self.output_dir}")
        # Ya no se agrega al log principal aquí, solo cuando el usuario selecciona el directorio.

    def start_download(self):
        """Inicia el proceso de descarga basándose en la entrada del usuario y el modo seleccionado."""
        if not self.output_dir:
            QMessageBox.warning(self, "Error de Directorio", "Por favor, selecciona un directorio de salida antes de iniciar la descarga. ⚠️")
            return

        urls = [url.strip() for url in self.urls_text_edit.toPlainText().splitlines() if url.strip()]
        if not urls:
            QMessageBox.warning(self, "Error de URL", "No se han introducido URLs para descargar. 🚫")
            return

        if self.is_downloading:
            QMessageBox.information(self, "Descarga en Curso", "Ya hay descargas en curso. ¡Espera a que terminen o deténlas! ⏳")
            return

        # Actualizar las variables de opción antes de iniciar la descarga
        self.download_mode_parallel = self.parallel_radio.isChecked()
        self.save_settings() # Guardar las opciones actuales antes de la descarga

        self.is_downloading = True
        self.start_button.setDisabled(True)
        self.stop_button.setDisabled(False)
        self.clear_download_queue_visuals() # Limpiar la tabla y el log visualmente
        
        self.download_queue = urls
        self.current_download_idx = 0
        
        # Poblar la tabla de descargas con todas las URLs iniciales
        self.download_table.setRowCount(len(self.download_queue))
        for row_idx, url in enumerate(self.download_queue):
            self.download_table.setItem(row_idx, 0, QTableWidgetItem(url))
            # Crear y configurar la barra de progreso para cada fila
            progress_bar = QProgressBar()
            progress_bar.setAlignment(Qt.AlignCenter) # Centrar el texto del porcentaje
            progress_bar.setValue(0)
            self.download_table.setCellWidget(row_idx, 1, progress_bar)
            self.download_table.setItem(row_idx, 2, QTableWidgetItem("Pendiente ⏱️"))
            self.download_table.setItem(row_idx, 3, QTableWidgetItem("N/A"))
            self.download_table.setItem(row_idx, 4, QTableWidgetItem("N/A"))
        
        self.output_log_text.append("Osiris: Descargas iniciadas. ¡Preparando el sistema! 🌟")
        
        if self.download_mode_parallel:
            self.start_next_parallel_downloads()
        else:
            self.start_next_sequential_download()

    def stop_all_downloads(self):
        """Solicita a todos los hilos de descarga activos que se detengan."""
        if not self.is_downloading:
            return

        self.output_log_text.append("Osiris: Solicitando la detención de todas las descargas... 🛑")
        
        # Iterar sobre una copia de los hilos para evitar problemas de modificación durante la iteración
        active_threads = list(self.download_threads.values())
        for worker in active_threads:
            worker.stop() # Llama al método stop del worker
            # No se hace worker.wait() aquí para no bloquear la GUI

        # La limpieza final de download_threads se hará en handle_download_finished
        # cuando cada worker reporte su estado de 'Cancelled'.
        # Forzar el final si no hay threads activos y la bandera de descarga está en True
        # (Esto es útil si el usuario hace clic en detener antes de que el worker reporte)
        if not self.download_threads and self.current_download_idx >= len(self.download_queue):
            self.download_process_finished(is_stopped_by_user=True)

    def clear_download_queue(self):
        """Limpia la cola de descarga y la visualización de la tabla."""
        # Primero, detener todas las descargas activas para evitar que los hilos sigan trabajando
        self.stop_all_downloads() 
        # Luego, limpiar la cola lógica y la tabla
        self.clear_download_queue_visuals()
        self.download_queue.clear()
        self.current_download_idx = 0
        self.output_log_text.append("Osiris: Cola de descargas y tabla limpiadas. 🧹")


    def clear_download_queue_visuals(self):
        """Limpia visualmente la tabla y el log, sin detener hilos."""
        for worker in list(self.download_threads.values()): # Iterar sobre una copia
            worker.stop() # Ensure worker terminates
        self.download_threads.clear() # Limpiar el diccionario de hilos
        self.download_table.setRowCount(0)
        self.output_log_text.clear() # Limpiar el log de salida

    def start_next_sequential_download(self):
        """Inicia la siguiente descarga en modo secuencial."""
        # Solo iniciar si hay URLs en la cola y NO hay descargas activas (modo secuencial = 1 a la vez)
        if self.current_download_idx < len(self.download_queue) and not self.download_threads:
            url = self.download_queue[self.current_download_idx]
            self.output_log_text.append(f"Osiris: Iniciando descarga secuencial: {url}...")
            self._start_single_download(url, self.current_download_idx)
        # Importante: No llamar download_process_finished aquí, solo en handle_download_finished

    def start_next_parallel_downloads(self):
        """Inicia descargas en modo paralelo, hasta el límite configurado."""
        
        while len(self.download_threads) < self.max_parallel_downloads and self.current_download_idx < len(self.download_queue):
            url = self.download_queue[self.current_download_idx]
            self.output_log_text.append(f"Osiris: Iniciando descarga en paralelo: {url}...")
            self._start_single_download(url, self.current_download_idx)
            self.current_download_idx += 1 # Moverse a la siguiente URL inmediatamente para el modo paralelo

        # Importante: No llamar download_process_finished aquí, solo en handle_download_finished

    def _start_single_download(self, url: str, row_idx: int):
        """Función auxiliar para crear e iniciar un solo DownloadWorker."""
        # Determinar la plantilla del nombre de archivo
        file_name_template = self.additional_options_vars["custom_output_name"]
        
        if self.additional_options_vars["auto_output_naming"] or not file_name_template:
            # Generar un nombre genérico a partir del host de la URL o usar un base + índice
            safe_url_host = re.sub(r'[^a-zA-Z0-9_\-]', '', QUrl(url).host().split('.')[-2] if QUrl(url).host() else "download")
            
            if len(self.download_queue) > 1:
                # Si hay múltiples descargas, añadir _1, _2, etc.
                file_name_template = f"{safe_url_host}_{row_idx + 1}"
            else:
                # Si es una sola descarga, usar el nombre base generado o custom si está vacío
                file_name_template = safe_url_host 

        worker = DownloadWorker(url, self.output_dir, file_name_template, 
                                self.format_option_value, self.additional_options_vars)
        self.download_threads[url] = worker # Añadir el worker al diccionario de hilos activos
        
        # Conectar las señales del worker a los slots en el hilo principal de la GUI
        worker.progress_update.connect(lambda u, p, s, e: self.update_download_progress(u, p, s, e, row_idx))
        worker.status_update.connect(lambda u, s, l: self.update_download_status(u, s, l, row_idx))
        worker.download_finished.connect(lambda u, code: self.handle_download_finished(u, code, row_idx))
        worker.download_error.connect(lambda u, msg: self.handle_download_error(u, msg, row_idx))
        
        worker.start() # Iniciar el hilo

    @pyqtSlot(str, float, str, str, int)
    def update_download_progress(self, url: str, percentage: float, speed: str, eta: str, row_idx: int):
        """Actualiza la barra de progreso, velocidad y ETA en la tabla."""
        if self.download_table.rowCount() > row_idx:
            progress_bar = self.download_table.cellWidget(row_idx, 1)
            if progress_bar:
                progress_bar.setValue(int(percentage))
            self.download_table.setItem(row_idx, 2, QTableWidgetItem(f"Descargando ({int(percentage)}%)"))
            self.download_table.setItem(row_idx, 3, QTableWidgetItem(speed))
            self.download_table.setItem(row_idx, 4, QTableWidgetItem(eta))

    @pyqtSlot(str, str, str, int)
    def update_download_status(self, url: str, status_msg: str, log_line: str, row_idx: int):
        """Actualiza el mensaje de estado en la tabla y en el log principal."""
        if log_line: # Si es una línea de log raw de yt-dlp
            self.output_log_text.append(f"[{os.path.basename(url) if os.path.basename(url) else url}] {log_line}")
        elif status_msg: # Si es un mensaje de estado generado por la aplicación
            # Actualizar estado en la tabla solo si es un estado de descarga principal
            if not (status_msg.startswith("Descargando") or status_msg == "LOG"): # Evitar sobrescribir con progreso
                if self.download_table.rowCount() > row_idx:
                    self.download_table.setItem(row_idx, 2, QTableWidgetItem(status_msg))
            self.output_log_text.append(f"Osiris ({os.path.basename(url) if os.path.basename(url) else url}): {status_msg}")

    @pyqtSlot(str, int, int)
    def handle_download_finished(self, url: str, exit_code: int, row_idx: int):
        """Maneja la finalización de un worker de descarga."""
        worker = self.download_threads.pop(url, None) # Eliminar el worker finalizado del diccionario
        if worker:
            worker.quit()
            worker.wait() # Asegurar la limpieza del hilo

        if self.download_table.rowCount() > row_idx: # Asegurarse de que la fila aún existe
            if exit_code == 0:
                self.output_log_text.append(f"Osiris: Descarga completada para: {url} ✅")
                self.download_table.setItem(row_idx, 2, QTableWidgetItem("Completado 🎉"))
                # Establecer la barra de progreso al 100%
                progress_bar = self.download_table.cellWidget(row_idx, 1)
                if progress_bar:
                    progress_bar.setValue(100)
                self.download_table.setItem(row_idx, 3, QTableWidgetItem("N/A"))
                self.download_table.setItem(row_idx, 4, QTableWidgetItem("N/A"))
            elif exit_code == -1: # Cancelación por el usuario
                self.output_log_text.append(f"Osiris: Descarga cancelada para: {url} 🛑")
                self.download_table.setItem(row_idx, 2, QTableWidgetItem("Cancelado ❌"))
                self.download_table.setItem(row_idx, 3, QTableWidgetItem("N/A"))
                self.download_table.setItem(row_idx, 4, QTableWidgetItem("N/A"))
            else:
                self.output_log_text.append(f"Osiris: Descarga fallida para: {url} (Código: {exit_code}) 💔")
                self.download_table.setItem(row_idx, 2, QTableWidgetItem(f"Falló ({exit_code}) 💔"))
                # Opcional: mantener la barra de progreso en el último valor o resetearla
                self.download_table.setItem(row_idx, 3, QTableWidgetItem("N/A"))
                self.download_table.setItem(row_idx, 4, QTableWidgetItem("N/A"))
        
        # Lógica para continuar o finalizar, ahora solo aquí
        if self.download_mode_parallel:
            self.start_next_parallel_downloads() # Intentar iniciar otra descarga paralela
        else:
            self.current_download_idx += 1
            self.start_next_sequential_download() # Iniciar la siguiente descarga secuencial (si hay)

        # La condición definitiva para saber si todas las descargas han finalizado
        # (todos los workers han terminado y todas las URLs de la cola han sido procesadas)
        if not self.download_threads and self.current_download_idx >= len(self.download_queue):
            self.download_process_finished()


    @pyqtSlot(str, str, int)
    def handle_download_error(self, url: str, error_message: str, row_idx: int):
        """Maneja un error reportado por un worker de descarga."""
        self.output_log_text.append(f"Osiris: ¡ERROR CRÍTICO! al descargar {url}:\n{error_message} 💥")
        
        if self.download_table.rowCount() > row_idx:
            self.download_table.setItem(row_idx, 2, QTableWidgetItem("Error 💥"))
            progress_bar = self.download_table.cellWidget(row_idx, 1)
            if progress_bar:
                progress_bar.setValue(0) # Resetea o mantiene el último valor
            self.download_table.setItem(row_idx, 3, QTableWidgetItem("N/A"))
            self.download_table.setItem(row_idx, 4, QTableWidgetItem("N/A"))
        
        worker = self.download_threads.pop(url, None)
        if worker:
            worker.quit()
            worker.wait()

        # Continúa con otras descargas, el error no detiene todo el proceso
        if self.download_mode_parallel:
            self.start_next_parallel_downloads()
        else:
            self.current_download_idx += 1
            self.start_next_sequential_download()

        if not self.download_threads and self.current_download_idx >= len(self.download_queue):
            self.download_process_finished()


    def download_process_finished(self, is_stopped_by_user: bool = False):
        """Llamado cuando todas las descargas (secuenciales o paralelas) están completas."""
        self.is_downloading = False
        self.start_button.setDisabled(False)
        self.stop_button.setDisabled(True)
        
        if not is_stopped_by_user:
            self.output_log_text.append("Osiris: ¡Todas las descargas han finalizado! ✅🎉")
            QMessageBox.information(self, "Descargas Completadas", "¡Todas las descargas han terminado! 🎉")
        else:
            self.output_log_text.append("Osiris: Proceso de descarga detenido. 🛑")
            QMessageBox.information(self, "Descargas Detenidas", "Las descargas han sido detenidas por el usuario. 🛑")

    def save_settings(self):
        """Guarda las configuraciones actuales de la UI en QSettings."""
        settings = QSettings("OsirisInnovations", "OsirisDownloaderAI")
        settings.setValue("output_directory", self.output_dir)
        settings.setValue("download_mode_parallel", self.parallel_radio.isChecked())
        settings.setValue("format_option_value", self.format_option_value)
        
        # Guardar el estado de las opciones adicionales
        settings.setValue("audio_only", self.audio_only_checkbox.isChecked())
        settings.setValue("limit_speed", self.limit_speed_checkbox.isChecked())
        settings.setValue("speed_limit_val", self.speed_limit_input.text())
        settings.setValue("max_quality", self.max_quality_checkbox.isChecked())
        settings.setValue("embed_thumbnail", self.embed_thumbnail_checkbox.isChecked())
        settings.setValue("embed_metadata", self.embed_metadata_checkbox.isChecked())
        settings.setValue("auto_output_naming", self.auto_name_checkbox.isChecked())
        settings.setValue("custom_output_name", self.custom_output_name_edit.text())
        settings.setValue("audio_format", self.audio_format_checkbox.isChecked())
        settings.setValue("audio_format_val", self.audio_format_combo.currentText())
        settings.setValue("add_headers", self.add_headers_checkbox.isChecked())
        settings.setValue("headers_val", self.headers_input.text())
        settings.setValue("cookies_from_browser", self.cookies_checkbox.isChecked())
        settings.setValue("browser_val", self.browser_combo.currentText())
        settings.setValue("username", self.username_checkbox.isChecked())
        settings.setValue("username_val", self.username_input.text())
        settings.setValue("password", self.password_checkbox.isChecked())
        settings.setValue("password_val", self.password_input.text())
        settings.setValue("playlist_start", self.playlist_start_checkbox.isChecked())
        settings.setValue("playlist_start_val", self.playlist_start_input.text())
        settings.setValue("playlist_end", self.playlist_end_checkbox.isChecked())
        settings.setValue("playlist_end_val", self.playlist_end_input.text())
        settings.setValue("proxy", self.proxy_checkbox.isChecked())
        settings.setValue("proxy_val", self.proxy_input.text())
        settings.setValue("custom_args", self.custom_args_checkbox.isChecked())
        settings.setValue("custom_args_val", self.custom_args_input.text())

        # Guardar el estado de los docks
        settings.setValue("download_queue_dock_state", self.download_queue_dock.isVisible())
        settings.setValue("output_log_dock_state", self.output_log_dock.isVisible())
        settings.setValue("options_collapsible_group_state", self.options_collapsible_group.isChecked())
        settings.setValue("main_window_geometry", self.saveGeometry())
        settings.setValue("main_window_state", self.saveState())


    def load_settings(self):
        """Carga las configuraciones desde QSettings."""
        settings = QSettings("OsirisInnovations", "OsirisDownloaderAI")
        # Cargar directorio de salida
        self.output_dir = settings.value("output_directory", os.path.expanduser("~"), type=str)
        
        # Cargar modo de descarga
        self.download_mode_parallel = settings.value("download_mode_parallel", False, type=bool)
        self.format_option_value = settings.value("format_option_value", "mp4", type=str)

        # Cargar opciones adicionales en el diccionario interno
        self.additional_options_vars["audio_only"] = settings.value("audio_only", False, type=bool)
        self.additional_options_vars["limit_speed"] = settings.value("limit_speed", False, type=bool)
        self.additional_options_vars["speed_limit_val"] = settings.value("speed_limit_val", "", type=str)
        self.additional_options_vars["max_quality"] = settings.value("max_quality", False, type=bool)
        self.additional_options_vars["embed_thumbnail"] = settings.value("embed_thumbnail", False, type=bool)
        self.additional_options_vars["embed_metadata"] = settings.value("embed_metadata", False, type=bool)
        self.additional_options_vars["auto_output_naming"] = settings.value("auto_output_naming", True, type=bool)
        self.additional_options_vars["custom_output_name"] = settings.value("custom_output_name", "", type=str)
        self.additional_options_vars["audio_format"] = settings.value("audio_format", False, type=bool)
        self.additional_options_vars["audio_format_val"] = settings.value("audio_format_val", "mp3", type=str)
        self.additional_options_vars["add_headers"] = settings.value("add_headers", False, type=bool)
        self.additional_options_vars["headers_val"] = settings.value("headers_val", "", type=str)
        self.additional_options_vars["cookies_from_browser"] = settings.value("cookies_from_browser", False, type=bool)
        self.additional_options_vars["browser_val"] = settings.value("browser_val", "chrome", type=str)
        self.additional_options_vars["username"] = settings.value("username", False, type=bool)
        self.additional_options_vars["username_val"] = settings.value("username_val", "", type=str)
        self.additional_options_vars["password"] = settings.value("password", False, type=bool)
        self.additional_options_vars["password_val"] = settings.value("password_val", "", type=str)
        self.additional_options_vars["playlist_start"] = settings.value("playlist_start", False, type=bool)
        self.additional_options_vars["playlist_start_val"] = settings.value("playlist_start_val", "1", type=str)
        self.additional_options_vars["playlist_end"] = settings.value("playlist_end", False, type=bool)
        self.additional_options_vars["playlist_end_val"] = settings.value("playlist_end_val", "", type=str)
        self.additional_options_vars["proxy"] = settings.value("proxy", False, type=bool)
        self.additional_options_vars["proxy_val"] = settings.value("proxy_val", "", type=str)
        self.additional_options_vars["custom_args"] = settings.value("custom_args", False, type=bool)
        self.additional_options_vars["custom_args_val"] = settings.value("custom_args_val", "", type=str)

        # Cargar el estado de los docks y la ventana principal
        if settings.value("main_window_geometry") is not None:
            self.restoreGeometry(settings.value("main_window_geometry"))
        if settings.value("main_window_state") is not None:
            self.restoreState(settings.value("main_window_state"))
        
        # Restaurar la visibilidad de los docks
        self.download_queue_dock.setVisible(settings.value("download_queue_dock_state", True, type=bool))
        self.output_log_dock.setVisible(settings.value("output_log_dock_state", True, type=bool))
        self.options_collapsible_group.setChecked(settings.value("options_collapsible_group_state", True, type=bool))


    def update_ui_from_settings(self):
        """Aplica las configuraciones cargadas a los widgets de la UI."""
        if self.download_mode_parallel:
            self.parallel_radio.setChecked(True)
        else:
            self.sequential_radio.setChecked(True)
        
        # Establecer ComboBox de formato
        format_display_map = {
            "mp4": "MP4 (Video)", "mkv": "MKV (Video)", "webm": "WEBM (Video)",
            "mp3": "MP3 (Audio Only)", "aac": "AAC (Audio Only)", "flac": "FLAC (Audio Only)",
            "wav": "WAV (Audio Only)", "opus": "OPUS (Audio Only)"
        }
        idx = self.format_combo.findText(format_display_map.get(self.format_option_value, "MP4 (Video)"))
        if idx != -1:
            self.format_combo.setCurrentIndex(idx)
            # No llamar a update_format_option aquí directamente, ya que puede sobrescribir audio_only_checkbox.
            # En su lugar, establecer los estados de los checkboxes directamente.
            
        # Establecer el estado de las opciones adicionales y sus campos de entrada
        # Se hacen en este orden para manejar las dependencias correctamente
        self.auto_name_checkbox.setChecked(self.additional_options_vars["auto_output_naming"])
        self.custom_output_name_edit.setText(self.additional_options_vars["custom_output_name"])
        self.limit_speed_checkbox.setChecked(self.additional_options_vars["limit_speed"])
        self.speed_limit_input.setText(self.additional_options_vars["speed_limit_val"])
        self.max_quality_checkbox.setChecked(self.additional_options_vars["max_quality"])
        self.embed_thumbnail_checkbox.setChecked(self.additional_options_vars["embed_thumbnail"])
        self.embed_metadata_checkbox.setChecked(self.additional_options_vars["embed_metadata"])
        
        # Primero establece audio_only_checkbox antes de audio_format_checkbox
        self.audio_only_checkbox.setChecked(self.additional_options_vars["audio_only"])
        # Si el formato principal es audio, forzar audio_only y deshabilitar sus controles
        if self.format_option_value in ["mp3", "aac", "flac", "wav", "opus"]:
            self.audio_only_checkbox.setChecked(True)
            self.audio_only_checkbox.setDisabled(True)
        else:
            self.audio_only_checkbox.setDisabled(False)

        self.audio_format_checkbox.setChecked(self.additional_options_vars["audio_format"])
        idx = self.audio_format_combo.findText(self.additional_options_vars["audio_format_val"])
        if idx != -1: self.audio_format_combo.setCurrentIndex(idx)

        # Ahora aplicar los toggles para asegurar el estado correcto de habilitado/deshabilitado
        self.toggle_custom_output_name_field(self.auto_name_checkbox.isChecked())
        self.toggle_speed_limit_input(self.limit_speed_checkbox.isChecked())
        # Llamar a toggle_audio_format_combo después de establecer audio_only_checkbox
        # y antes de eso, asegurar que la combo de formato principal ha sido actualizada.
        # Ya update_format_option fue llamado por setCurrentIndex.
        # Ahora, toggle_audio_format_combo ajustará su estado basado en su propio checkbox.
        self.toggle_audio_format_combo(self.audio_format_checkbox.isChecked())

        self.add_headers_checkbox.setChecked(self.additional_options_vars["add_headers"])
        self.headers_input.setText(self.additional_options_vars["headers_val"])
        self.cookies_checkbox.setChecked(self.additional_options_vars["cookies_from_browser"])
        idx = self.browser_combo.findText(self.additional_options_vars["browser_val"])
        if idx != -1: self.browser_combo.setCurrentIndex(idx)
        self.username_checkbox.setChecked(self.additional_options_vars["username"])
        self.username_input.setText(self.additional_options_vars["username_val"])
        self.password_checkbox.setChecked(self.additional_options_vars["password"])
        self.password_input.setText(self.additional_options_vars["password_val"])
        self.playlist_start_checkbox.setChecked(self.additional_options_vars["playlist_start"])
        self.playlist_start_input.setText(self.additional_options_vars["playlist_start_val"])
        self.playlist_end_checkbox.setChecked(self.additional_options_vars["playlist_end"])
        self.playlist_end_input.setText(self.additional_options_vars["playlist_end_val"])
        self.proxy_checkbox.setChecked(self.additional_options_vars["proxy"])
        self.proxy_input.setText(self.additional_options_vars["proxy_val"])
        self.custom_args_checkbox.setChecked(self.additional_options_vars["custom_args"])
        self.custom_args_input.setText(self.additional_options_vars["custom_args_val"])

        self.toggle_headers_input(self.add_headers_checkbox.isChecked())
        self.toggle_browser_combo(self.cookies_checkbox.isChecked())
        self.toggle_username_input(self.username_checkbox.isChecked())
        self.toggle_password_input(self.password_checkbox.isChecked())
        self.toggle_playlist_start_input(self.playlist_start_checkbox.isChecked())
        self.toggle_playlist_end_input(self.playlist_end_checkbox.isChecked())
        self.toggle_proxy_input(self.proxy_checkbox.isChecked())
        self.toggle_custom_args_input(self.custom_args_checkbox.isChecked())


    def closeEvent(self, event):
        """Manejador de eventos para el cierre de la ventana, guarda configuraciones."""
        self.save_settings()
        self.stop_all_downloads() # Asegura que todos los hilos se terminen al cerrar
        event.accept()

    def _apply_styles(self):
        """Aplica estilos CSS (QSS) básicos a la aplicación para una mejor apariencia."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50; /* Azul oscuro - base Osiris */
            }
            QWidget {
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                background-color: #2c3e50; /* Azul oscuro - base Osiris */
                color: #ecf0f1; /* Gris claro */
            }
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
                border: 1px solid #34495e; /* Borde más oscuro */
                border-radius: 6px;
                padding-top: 15px;
                background-color: #34495e; /* Fondo de grupo */
                color: #ecf0f1;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* Centrar el título */
                padding: 0 5px;
                color: #2ecc71; /* Verde brillante para títulos - acento Osiris */
                background-color: #34495e; /* Fondo de título */
                border-radius: 3px;
            }
            /* Estilo para el QGroupBox colapsable */
            QGroupBox#options_collapsible_group::indicator {
                image: url(./icons/arrow_down.png); /* Imagen para flecha abajo (expandido) */
                width: 12px;
                height: 12px;
            }
            QGroupBox#options_collapsible_group::indicator:checked {
                image: url(./icons/arrow_down.png); /* Flecha abajo cuando expandido */
            }
            QGroupBox#options_collapsible_group::indicator:unchecked {
                image: url(./icons/arrow_right.png); /* Flecha derecha cuando colapsado */
            }
            /* Puedes crear estas imágenes o usar un font de iconos si no quieres imágenes */
            /* Alternativa con texto si no tienes imágenes:
            QGroupBox::indicator {
                subcontrol-origin: padding;
                subcontrol-position: left center;
                padding-left: 5px;
                width: 15px;
                font-size: 14px;
            }
            QGroupBox::indicator:checked {
                content: "▼";
            }
            QGroupBox::indicator:unchecked {
                content: "►";
            }
            */

            QPushButton {
                padding: 10px 20px;
                border: 1px solid #2ecc71; /* Borde verde */
                border-radius: 5px;
                background-color: #27ae60; /* Verde más oscuro */
                color: white;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            QPushButton:hover {
                background-color: #2ecc71; /* Verde más claro al pasar el ratón */
                border-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #1abc9c; /* Verde aún más claro al presionar */
            }
            QPushButton:disabled {
                background-color: #7f8c8d; /* Gris para deshabilitado */
                border-color: #95a5a6;
                color: #bdc3c7;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 1px solid #5d748f; /* Borde de entrada */
                border-radius: 4px;
                background-color: #49637c; /* Fondo de entrada */
                color: #ecf0f1;
                selection-background-color: #2980b9; /* Selección azul */
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #3498db; /* Borde azul al enfocar */
            }
            QCheckBox, QRadioButton {
                padding: 5px 0;
                color: #ecf0f1;
            }
            QProgressBar {
                border: 1px solid #5d748f;
                border-radius: 5px;
                text-align: center;
                background-color: #49637c;
                color: #ecf0f1; /* Texto de progreso */
            }
            QProgressBar::chunk {
                background-color: #2ecc71; /* Verde para el progreso */
                border-radius: 4px;
            }
            QTableWidget {
                border: 1px solid #34495e;
                border-radius: 6px;
                gridline-color: #49637c; /* Líneas de la cuadrícula */
                background-color: #34495e;
                color: #ecf0f1;
            }
            QHeaderView::section {
                background-color: #2c3e50; /* Cabeceras de tabla */
                padding: 8px;
                border: 1px solid #34495e;
                font-weight: bold;
                color: #2ecc71; /* Texto de cabecera verde */
            }
            QTableWidgetItem {
                padding: 5px;
                background-color: #49637c; /* Fondo de celda */
                color: #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db; /* Selección azul de celda */
                color: white;
            }
            QScrollBar:vertical {
                border: 1px solid #34495e;
                background: #2c3e50;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #5d748f;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: 1px solid #34495e;
                background: #2c3e50;
                height: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #5d748f;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            /* Estilos para QTabWidget */
            QTabWidget::pane { /* El marco donde se muestran las pestañas */
                border: 1px solid #34495e;
                border-radius: 6px;
                padding: 5px; /* Espacio interno dentro del panel de la pestaña */
                background-color: #34495e;
            }
            QTabWidget::tab-bar {
                left: 5px; /* Mover la barra de pestañas a la derecha del marco */
            }
            QTabBar::tab {
                background-color: #49637c; /* Pestaña inactiva */
                border: 1px solid #5d748f;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                padding: 8px 15px;
                margin-left: 3px;
                color: #ecf0f1;
            }
            QTabBar::tab:selected {
                background-color: #2c3e50; /* Pestaña activa */
                border-color: #2ecc71; /* Borde verde para la pestaña activa */
                border-bottom-color: #2c3e50; /* Misma que el fondo para que parezca que no hay borde */
                color: #2ecc71;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #5d748f; /* Un poco más claro al pasar el ratón */
            }
            QTabBar::tab:selected:hover {
                background-color: #2ecc71; /* Pestaña activa al pasar el ratón */
                color: white;
            }
            /* Estilos para QDockWidget */
            QDockWidget {
                border: 1px solid #34495e;
                titlebar-close-icon: url(./icons/close_icon.png); /* Opcional: icono de cierre */
                titlebar-normal-icon: url(./icons/dock_icon.png); /* Opcional: icono de dock */
            }
            QDockWidget::title {
                text-align: center;
                background: #2c3e50; /* Fondo de la barra de título del dock */
                padding: 5px;
                color: #ecf0f1;
                font-weight: bold;
                border-bottom: 1px solid #2ecc71; /* Línea verde debajo del título */
            }
            QDockWidget::float-button, QDockWidget::close-button {
                border: none;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
            QDockWidget::float-button:hover, QDockWidget::close-button:hover {
                background-color: #5d748f;
            }
            QDockWidget::float-button {
                image: url(./icons/float_icon.png); /* Icono para flotar */
            }
            QDockWidget::close-button {
                image: url(./icons/close_icon.png); /* Icono para cerrar */
            }
            /* Estilos para QStatusBar */
            QStatusBar {
                background-color: #34495e;
                color: #2ecc71;
                padding: 3px;
                border-top: 1px solid #27ae60;
            }
            QStatusBar::item {
                border: none;
            }
            /* Estilos para QMenuBar */
            QMenuBar {
                background-color: #2c3e50;
                color: #ecf0f1;
                border-bottom: 1px solid #34495e;
            }
            QMenuBar::item {
                padding: 5px 10px;
                background: transparent;
            }
            QMenuBar::item:selected { /* Cuando el ratón pasa por encima o está seleccionado */
                background: #34495e;
            }
            QMenuBar::item:pressed {
                background: #2ecc71;
            }
            QMenu {
                background-color: #34495e; /* Fondo del menú desplegable */
                border: 1px solid #5d748f;
                padding: 5px;
                color: #ecf0f1;
            }
            QMenu::item {
                padding: 8px 25px 8px 20px; /* Arriba, derecha, abajo, izquierda */
                border: 1px solid transparent; /* Para que el resaltado sea visible */
            }
            QMenu::item:selected {
                background-color: #2980b9; /* Resaltado azul */
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #5d748f;
                margin: 5px 0px;
            }
        """)

# --- REQUISITOS ADICIONALES PARA ICONOS ---
# Si quieres que los iconos de las flechas del QGroupBox colapsable y los botones
# de cerrar/flotar de los QDockWidget funcionen, necesitarás crear las imágenes
# correspondientes en una carpeta llamada 'icons' en el mismo directorio del script.
# Por ejemplo:
# - icons/arrow_down.png (una flecha apuntando hacia abajo, para cuando el grupo está expandido)
# - icons/arrow_right.png (una flecha apuntando hacia la derecha, para cuando el grupo está colapsado)
# - icons/close_icon.png (un icono de 'X' o similar)
# - icons/float_icon.png (un icono que sugiera "flotar" o "desacoplar")
# - osiris_icon.png (el icono principal de tu aplicación)
#
# Si no quieres crear imágenes, puedes comentar las líneas de `image: url(...)` en el QSS
# y descomentar la sección `content: "▼"` para usar caracteres de texto como indicadores.
# Para los botones de los docks, simplemente se verán como pequeños cuadros sin iconos si no los proporcionas.


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configurar detalles de la aplicación para QSettings
    app.setOrganizationName("OsirisInnovations")
    app.setApplicationName("OsirisDownloaderAI")

    window = OsirisDownloaderApp()
    window.show()
    sys.exit(app.exec_())