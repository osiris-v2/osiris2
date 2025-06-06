#!/bin/env python3
import sys
import datetime
import hashlib
import json
import sqlite3
import os
import traceback
import logging

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QMessageBox, QHBoxLayout,
                             QScrollArea, QGridLayout, QFileDialog, QListWidget, QListWidgetItem,
                             QMenuBar, QAction, QInputDialog) # <-- ¡QInputDialog añadido aquí!
from PyQt5.QtCore import Qt, QSize
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

# --- Configuración de Logging ---
# Cambia a logging.DEBUG para ver mensajes muy detallados en consola (útil para depuración)
# Cambia a logging.INFO para menos verbosidad
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes de Rutas ---
# Directorio donde se guardarán las bases de datos y las claves
BLOCKCHAIN_DATA_DIR = "blockchain_data"
# Nombre de la base de datos predeterminada
DEFAULT_DB_NAME = "osiris_blockchain.db"

# --- Funciones Auxiliares (Simulación Osiris) ---
def osiris_command(command, *args):
    """
    Ejecuta un comando en Osiris.
    Args:
        command (str): El comando a ejecutar.
        *args: Argumentos adicionales para el comando.

    Returns:
        str: El resultado de la ejecución del comando.
    """
    try:
        # Implementa la lógica real para ejecutar comandos en Osiris aquí.
        # Esto podría implicar conectarse a un servidor Osiris, enviar el comando
        # y recibir la respuesta.

        # Simulando la salida de Osiris para pruebas. REEMPLAZAR CON LA IMPLEMENTACIÓN REAL.
        # Se ha hecho la salida un poco más útil.
        arg_str = ", ".join(map(str, args))
        result = f"Osiris procesó el comando: '{command}' con args: [{arg_str[:100]}{'...' if len(arg_str) > 100 else ''}]"
        logging.debug(f"Comando Osiris ejecutado: {command} con argumentos: {args}. Resultado: {result}")
        return result
    except Exception as e:
        logging.error(f"Error al ejecutar el comando Osiris: {command} con argumentos: {args}", exc_info=True)
        return f"Error al ejecutar el comando Osiris: {e}"

# --- Clase Block ---
class Block:
    def __init__(self, timestamp, data, previous_hash, block_hash=None, signature=None):
        # timestamp puede ser un objeto datetime o una cadena ISO
        self.timestamp = timestamp if isinstance(timestamp, datetime.datetime) else datetime.datetime.fromisoformat(timestamp)
        self.data = data
        self.previous_hash = previous_hash
        # block_hash se usa para cargar un hash ya existente desde la DB.
        # Si no se provee (ej: al crear un bloque nuevo), se calcula.
        self.hash = block_hash if block_hash else self._calculate_hash_content()
        self.signature = signature

    def _get_hashable_content(self):
        """Devuelve un diccionario con los datos que se usan para calcular el hash."""
        # Se asegura que el timestamp sea una cadena ISO para consistencia en el hashing
        return {
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "previous_hash": self.previous_hash,
        }

    def _calculate_hash_content(self):
        """Calcula el hash SHA256 del contenido del bloque."""
        # Usa json.dumps con sort_keys para garantizar un orden consistente del diccionario
        # crucial para que el hash sea el mismo cada vez que se calcula.
        return hashlib.sha256(
            json.dumps(
                self._get_hashable_content(),
                sort_keys=True,
            ).encode("utf-8"),
        ).hexdigest()

    def _get_signed_message_content(self):
        """Devuelve un diccionario con los datos que se firmarán.
        Incluye el hash del bloque para asegurar que la integridad del hash también está firmada."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash # El hash calculado debe ser parte del mensaje firmado
        }

    def sign_block(self, private_key):
        """Firma el bloque usando la clave privada."""
        message_to_sign = json.dumps(
            self._get_signed_message_content(),
            sort_keys=True
        ).encode('utf-8')

        self.signature = private_key.sign(
            message_to_sign,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256())
        logging.debug(f"Bloque {self.hash} firmado. Firma (primeros 10 bytes): {self.signature[:10].hex()}...")
        return self.signature

    def verify_signature(self, public_key):
        """Verifica la firma del bloque usando la clave pública."""
        if not self.signature:
            logging.warning(f"Intento de verificar firma para bloque {self.hash} pero no tiene firma.")
            return False

        message_to_verify = json.dumps(
            self._get_signed_message_content(),
            sort_keys=True
        ).encode('utf-8')
        logging.debug(f"Verificando firma para bloque {self.hash}. Mensaje a verificar (primeros 50 bytes): {message_to_verify[:50]}...")

        try:
            public_key.verify(
                self.signature,
                message_to_verify,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            logging.debug(f"Firma válida para bloque: {self.hash}")
            return True
        except InvalidSignature:
            logging.warning(f"Firma inválida para bloque: {self.hash}. El contenido o la firma no coinciden.")
            return False
        except Exception as e:
            logging.error(f"Error durante la verificación de firma para bloque {self.hash}: {e}", exc_info=True)
            return False

    def __str__(self):
        """Representación en cadena del bloque para mostrar."""
        signature_display = self.signature.hex() if self.signature else "None"
        return f"""Timestamp: {self.timestamp.isoformat()}
Data: {self.data}
Previous Hash: {self.previous_hash}
Hash: {self.hash}
Signature: {signature_display}"""

# --- Clase Blockchain ---
class Blockchain:
    def __init__(self, db_path):
        self.db_path = os.path.abspath(db_path) # Ruta absoluta para evitar confusiones
        self.private_key_path, self.public_key_path = self._get_key_paths(self.db_path)
        self.conn = None
        self.cursor = None
        self.connect_db() # Conectar al iniciar
        self.private_key = self.get_private_key()
        self.public_key = self.get_public_key()
        logging.info(f"Blockchain inicializada para: {self.db_path}")


    def _get_key_paths(self, db_path):
        """Genera las rutas de las claves en función de la ruta de la base de datos."""
        base_name = os.path.splitext(os.path.basename(db_path))[0]
        dir_name = os.path.dirname(db_path)
        private_key_path = os.path.join(dir_name, f"{base_name}_private_key.pem")
        public_key_path = os.path.join(dir_name, f"{base_name}_public_key.pem")
        return private_key_path, public_key_path

    def connect_db(self):
        """Intenta conectar a la base de datos y crear la tabla si es necesario."""
        try:
            # Asegura que el directorio exista
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Para acceder a las columnas por nombre
            self.cursor = self.conn.cursor()
            self.create_table()
            logging.info(f"Conexión a la base de datos establecida en: {self.db_path}")
        except sqlite3.Error as e:
            logging.critical(f"Error CRÍTICO al conectar a la base de datos: {e}", exc_info=True)
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudo conectar a la base de datos: {e}\nLa aplicación se cerrará o funcionará de forma limitada.")
            # No sys.exit(1) aquí, para permitir que la UI maneje esto si es posible.
            self.conn = None # Asegurarse de que la conexión esté nula si falla

    def create_table(self):
        """Crea la tabla 'blocks' si no existe."""
        if not self.conn:
            logging.error("No hay conexión a la base de datos para crear la tabla.")
            return
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    data TEXT,
                    previous_hash TEXT,
                    hash TEXT,
                    signature BLOB
                )
            ''')
            self.conn.commit()
            logging.info("Tabla 'blocks' creada o ya existente.")
        except sqlite3.Error as e:
            logging.error(f"Error al crear la tabla 'blocks': {e}", exc_info=True)
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudo crear la tabla: {e}")

    def add_block(self, data):
        """Añade un nuevo bloque a la blockchain."""
        if not self.conn or not self.private_key:
            logging.error("No se puede añadir un bloque: Conexión a DB o clave privada no disponible.")
            QMessageBox.critical(None, "Error", "No se pudo añadir el bloque: Conexión a DB o clave privada no disponible.")
            return None
        try:
            previous_block_db = self.get_latest_block()
            previous_hash = previous_block_db['hash'] if previous_block_db else "0"
            timestamp = datetime.datetime.now()
            new_block = Block(timestamp, data, previous_hash)
            new_block.sign_block(self.private_key)

            self.cursor.execute("INSERT INTO blocks (timestamp, data, previous_hash, hash, signature) VALUES (?, ?, ?, ?, ?)",
                                (new_block.timestamp.isoformat(), new_block.data, new_block.previous_hash, new_block.hash, new_block.signature))
            self.conn.commit()
            logging.info(f"Bloque ID {self.cursor.lastrowid} añadido a la blockchain: {new_block.hash[:10]}...")
            return new_block
        except sqlite3.Error as e:
            logging.error(f"Error al añadir bloque a la base de datos: {e}", exc_info=True)
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudo añadir el bloque: {e}")
            self.conn.rollback()
            return None
        except Exception as e:
            logging.exception("Error inesperado al agregar bloque.")
            QMessageBox.critical(None, "Error Inesperado", f"Ocurrió un error inesperado al añadir bloque: {e}")
            self.conn.rollback()
            return None

    def get_block(self, block_id):
        """Obtiene un bloque por su ID."""
        if not self.conn: return None
        try:
            self.cursor.execute("SELECT * FROM blocks WHERE id = ?", (block_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Error al obtener el bloque con id {block_id}: {e}", exc_info=True)
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudo obtener el bloque: {e}")
            return None

    def get_latest_block(self):
        """Obtiene el último bloque de la cadena."""
        if not self.conn: return None
        try:
            self.cursor.execute("SELECT * FROM blocks ORDER BY id DESC LIMIT 1")
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Error al obtener el ultimo bloque: {e}", exc_info=True)
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudo obtener el último bloque: {e}")
            return None

    def get_all_blocks(self):
        """Obtiene todos los bloques de la cadena."""
        if not self.conn: return []
        try:
            self.cursor.execute("SELECT * FROM blocks ORDER BY id ASC")
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error al obtener todos los bloques: {e}", exc_info=True)
            QMessageBox.critical(None, "Error de Base de Datos", f"No se pudieron obtener los bloques: {e}")
            return []

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            try:
                self.conn.close()
                logging.info(f"Conexión a la base de datos {self.db_path} cerrada.")
            except sqlite3.Error as e:
                logging.error(f"Error al cerrar la conexión a la base de datos: {e}", exc_info=True)

    def verify_blockchain(self):
        """Verifica la integridad de toda la blockchain."""
        if not self.conn or not self.public_key:
            logging.error("No se puede verificar la blockchain: Conexión a DB o clave pública no disponible.")
            QMessageBox.warning(None, "Advertencia de Verificación", "No se puede verificar la blockchain: Conexión a DB o clave pública no disponible.")
            return False

        blocks = self.get_all_blocks()
        if not blocks:
            logging.warning("Blockchain vacía, verificación omitida.")
            return True

        logging.info("Iniciando verificación de la blockchain...")
        for i in range(len(blocks)):
            current_block_data = blocks[i]
            block_id = current_block_data['id']
            
            # Reconstruir el objeto Block para verificar el hash y la firma
            try:
                timestamp_dt = datetime.datetime.fromisoformat(current_block_data['timestamp'])
            except ValueError as e:
                logging.error(f"VERIFICATION FAILED (TIMESTAMP PARSE ERROR) in block {block_id}: Error al parsear timestamp '{current_block_data['timestamp']}': {e}")
                return False

            block_obj = Block(
                timestamp_dt,
                current_block_data['data'],
                current_block_data['previous_hash'],
                current_block_data['hash'], # Pasar el hash almacenado para que Block lo use al verificar la firma
                current_block_data.get('signature')
            )

            # 1. Verificar la integridad del hash del bloque actual
            recalculated_hash = block_obj._calculate_hash_content()
            if current_block_data['hash'] != recalculated_hash:
                logging.error(f"VERIFICATION FAILED (HASH MISMATCH) in block {block_id}: "
                              f"Hash almacenado: {current_block_data['hash']}, Hash recalculado: {recalculated_hash}")
                logging.error(f"  Datos para cálculo de hash: Timestamp='{block_obj.timestamp.isoformat()}', Data='{block_obj.data[:50]}...', Previous Hash='{block_obj.previous_hash}'")
                return False
            logging.debug(f"Bloque {block_id}: Hash OK.")

            # 2. Verificar el enlace con el hash del bloque anterior (excepto para el primer bloque)
            if i > 0:
                previous_block_data = blocks[i - 1]
                if current_block_data['previous_hash'] != previous_block_data['hash']:
                    logging.error(f"VERIFICATION FAILED (CHAIN LINK) in block {block_id}: "
                                  f"'previous_hash' NO coincide con el hash del bloque anterior.")
                    logging.error(f"  Previous Hash (actual): {current_block_data['previous_hash']}, Hash del bloque anterior: {previous_block_data['hash']}")
                    return False
            elif current_block_data['previous_hash'] != "0": # El primer bloque debe tener "0" como previous_hash
                logging.error(f"VERIFICATION FAILED (GENESIS PREV HASH) in block {block_id}: El primer bloque no tiene '0' como previous_hash.")
                return False
            logging.debug(f"Bloque {block_id}: Enlace de cadena OK.")

            # 3. Verificar la firma del bloque actual
            if not block_obj.signature:
                logging.error(f"VERIFICATION FAILED (MISSING SIGNATURE) in block {block_id}: Falta la firma digital.")
                return False

            try:
                if not block_obj.verify_signature(self.public_key):
                    logging.error(f"VERIFICATION FAILED (INVALID SIGNATURE) in block {block_id}.")
                    logging.error(f"  Mensaje firmado/verificado (componentes Block): Timestamp='{block_obj.timestamp.isoformat()}', Data='{block_obj.data[:50]}...', Previous Hash='{block_obj.previous_hash}', Hash='{block_obj.hash}'")
                    return False
            except Exception as e: # Captura errores durante la verificación de la firma misma
                logging.error(f"VERIFICATION FAILED (SIGNATURE ERROR) in block {block_id}: Error inesperado durante la verificación de la firma: {e}", exc_info=True)
                return False
            logging.debug(f"Bloque {block_id}: Firma OK.")

        logging.info("Verificación de la blockchain exitosa. Todos los bloques son válidos. ✅")
        return True

    def generate_keys(self):
        """Genera un nuevo par de claves RSA y las guarda en disco."""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()

            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Asegurar que el directorio de claves exista
            os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)

            with open(self.private_key_path, "wb") as f:
                f.write(private_pem)

            with open(self.public_key_path, "wb") as f:
                f.write(public_pem)
            
            self.private_key = private_key
            self.public_key = public_key
            logging.info(f"Claves RSA generadas y guardadas en: {self.private_key_path} y {self.public_key_path}")
            return private_key, public_key
        except Exception as e:
            logging.error(f"Error al generar claves: {e}", exc_info=True)
            QMessageBox.critical(None, "Error al generar claves", f"No se pudieron generar las claves: {e}")
            return None, None

    def get_private_key(self):
        """Carga la clave privada del disco o la genera si no existe."""
        if not os.path.exists(self.private_key_path):
            logging.warning(f"Clave privada no encontrada en {self.private_key_path}. Generando un nuevo par de claves.")
            return self.generate_keys()[0] # [0] para obtener la clave privada
        try:
            with open(self.private_key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
            logging.debug(f"Clave privada cargada de: {self.private_key_path}")
            return private_key
        except Exception as e:
            logging.error(f"Error al obtener la clave privada de {self.private_key_path}: {e}", exc_info=True)
            QMessageBox.critical(None, "Error al obtener clave privada", f"No se pudo obtener la clave privada: {e}\nConsidere generar nuevas claves.")
            return None

    def get_public_key(self):
        """Carga la clave pública del disco o la genera si no existe."""
        if not os.path.exists(self.public_key_path):
            logging.warning(f"Clave pública no encontrada en {self.public_key_path}. Generando un nuevo par de claves (¡esto invalidará firmas antiguas!).")
            return self.generate_keys()[1] # [1] para obtener la clave pública
        try:
            with open(self.public_key_path, "rb") as key_file:
                public_key_pem = key_file.read()
            public_key = serialization.load_pem_public_key(public_key_pem)
            logging.debug(f"Clave pública cargada de: {self.public_key_path}")
            return public_key
        except Exception as e:
            logging.error(f"Error al obtener la clave pública de {self.public_key_path}: {e}", exc_info=True)
            QMessageBox.critical(None, "Error al obtener clave pública", f"No se pudo obtener la clave pública: {e}\nConsidere generar nuevas claves.")
            return None

# --- Clase BlockDetailsWindow ---
class BlockDetailsWindow(QWidget):
    def __init__(self, block_data):
        super().__init__()
        self.setWindowTitle(f"Detalles del Bloque #{block_data['id']}")
        self.block_data = block_data
        self.initUI()
        self.setFixedSize(400, 560) # Tamaño aumentado para más detalle

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        def create_detail_widget(label_text, content_text, max_height=80):
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #555;")
            text_edit = QTextEdit(content_text)
            text_edit.setReadOnly(True)
            text_edit.setMaximumHeight(max_height)
            text_edit.setMinimumHeight(30)
            text_edit.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 5px;")
            return label, text_edit

        timestamp_label, timestamp_text = create_detail_widget("Timestamp:", self.block_data['timestamp'])
        data_label, data_text = create_detail_widget("Data:", self.block_data['data'], max_height=180)

        previous_hash_label, previous_hash_text = create_detail_widget("Previous Hash:", self.block_data['previous_hash'])
        hash_label, hash_text = create_detail_widget("Hash:", self.block_data['hash'])

        signature = self.block_data.get('signature')
        signature_hex = signature.hex() if signature else "None (Bloque no firmado o firma corrupta)"
        signature_label, signature_text = create_detail_widget("Signature (HEX):", signature_hex, max_height=120)

        layout.addWidget(timestamp_label)
        layout.addWidget(timestamp_text)
        layout.addWidget(data_label)
        layout.addWidget(data_text)
        layout.addWidget(previous_hash_label)
        layout.addWidget(previous_hash_text)
        layout.addWidget(hash_label)
        layout.addWidget(hash_text)
        layout.addWidget(signature_label)
        layout.addWidget(signature_text)
        self.setLayout(layout)

# --- Clase BlockchainWindow (Interfaz Principal) ---
class BlockchainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_db_path = None
        self.blockchain = None # Se inicializará en _init_blockchain
        self.pending_blocks_data = []
        self.block_detail_windows = {} # Para gestionar ventanas de detalles abiertas
        
        self.create_menus()
        self.initUI()
        
        # Intentar cargar la blockchain predeterminada al inicio
        self.load_default_blockchain()

    def create_menus(self):
        """Crea la barra de menú de la aplicación."""
        self.menu_bar = QMenuBar(self)
        file_menu = self.menu_bar.addMenu("Archivo 📁")

        new_action = QAction("Nueva Blockchain... ✨", self)
        new_action.triggered.connect(self.new_blockchain_dialog)
        file_menu.addAction(new_action)

        load_action = QAction("Cargar Blockchain... 📦", self)
        load_action.triggered.connect(self.load_blockchain_dialog)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()

        exit_action = QAction("Salir 🚪", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Ubicar la barra de menú (normalmente se hace en el QMainWindow, pero se puede simular en QWidget)
        main_layout = QVBoxLayout(self)
        main_layout.setMenuBar(self.menu_bar)
        self.setLayout(main_layout) # Esto asegura que el layout principal tenga la menubar

    def initUI(self):
        """Inicializa los componentes de la interfaz de usuario."""
        # Si ya hay un layout, lo borramos para evitar duplicados al re-inicializar
        if hasattr(self, '_main_content_layout') and self._main_content_layout is not None:
            # Eliminar todos los widgets y layouts hijos del layout principal
            while self._main_content_layout.count():
                item = self._main_content_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())
        
        self._main_content_layout = QVBoxLayout()
        # Asegúrate de que el layout que contiene la menubar también contenga el resto de la UI
        # self.layout() devuelve el layout que creamos en create_menus (main_layout)
        self.layout().addLayout(self._main_content_layout) 

        # Section 1: Manual Block Addition
        manual_add_group = QVBoxLayout()
        manual_add_group.addWidget(QLabel("<h2 style='color: #4CAF50;'>✍️ Añadir Bloque Manualmente</h2>")) # Título con color

        self.data_input = QTextEdit()
        self.data_input.setPlaceholderText("Introduce datos para el bloque (permite múltiples líneas)... 📝")
        self.data_input.setMinimumHeight(60)
        self.data_input.setMaximumHeight(100)
        manual_add_group.addWidget(self.data_input)

        self.add_button = QPushButton("➕ Añadir Bloque Manualmente")
        self.add_button.clicked.connect(self.add_block_manual)
        self.add_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;") # Estilo al botón
        manual_add_group.addWidget(self.add_button)
        self._main_content_layout.addLayout(manual_add_group)

        self._main_content_layout.addWidget(QLabel("<hr style='border: 1px solid #ccc;'>")) # Separador

        # Section 2: JSON Block Processing
        json_process_group = QVBoxLayout()
        json_process_group.addWidget(QLabel("<h2 style='color: #2196F3;'>📦 Procesar Bloques desde JSON</h2>")) # Título con color

        json_buttons_layout = QHBoxLayout()
        self.load_json_button = QPushButton("📂 Cargar Bloques desde JSON")
        self.load_json_button.clicked.connect(self.load_blocks_from_json)
        self.load_json_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        json_buttons_layout.addWidget(self.load_json_button)

        self.mine_pending_button = QPushButton("⛏️ Minar Bloques Pendientes")
        self.mine_pending_button.clicked.connect(self.mine_pending_blocks)
        self.mine_pending_button.setEnabled(False)
        self.mine_pending_button.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;") # Naranja para minar
        json_buttons_layout.addWidget(self.mine_pending_button)
        json_process_group.addLayout(json_buttons_layout)

        json_process_group.addWidget(QLabel("<h3 style='color: #607D8B;'>Lista de Bloques Pendientes por Minar:</h3>"))
        self.pending_blocks_list_widget = QListWidget()
        self.pending_blocks_list_widget.setMinimumHeight(100)
        self.pending_blocks_list_widget.setMaximumHeight(200)
        self.pending_blocks_list_widget.setStyleSheet("border: 1px solid #ddd; padding: 5px;")
        json_process_group.addWidget(self.pending_blocks_list_widget)

        self._main_content_layout.addLayout(json_process_group)

        self._main_content_layout.addWidget(QLabel("<hr style='border: 1px solid #ccc;'>")) # Separador

        # Section 3: Blockchain Operations
        blockchain_ops_group = QVBoxLayout()
        blockchain_ops_group.addWidget(QLabel("<h2 style='color: #F44336;'>🛡️ Operaciones de la Blockchain</h2>"))

        self.verify_button = QPushButton("✅ Verificar Blockchain")
        self.verify_button.clicked.connect(self.verify_blockchain_action)
        self.verify_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        blockchain_ops_group.addWidget(self.verify_button)
        self._main_content_layout.addLayout(blockchain_ops_group)

        self._main_content_layout.addWidget(QLabel("<hr style='border: 1px solid #ccc;'>")) # Separador

        # Section 4: Display Blockchain
        self._main_content_layout.addWidget(QLabel("<h2 style='color: #9C27B0;'>📜 Visualización de la Blockchain</h2>"))

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QWidget()
        self.block_layout = QGridLayout(self.scroll_area_widget_contents)
        self.scroll_area_widget_contents.setLayout(self.block_layout)
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scroll_area.setMinimumHeight(200)
        self.scroll_area.setMaximumHeight(400)
        self.scroll_area.setStyleSheet("border: 1px solid #ddd;")
        self._main_content_layout.addWidget(self.scroll_area)

        self.output_text_label = QLabel("<h3 style='color: #607D8B;'>Detalles Completos de Bloques (Texto):</h3>")
        self._main_content_layout.addWidget(self.output_text_label)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        self.output_text.setStyleSheet("border: 1px solid #ddd; padding: 5px; background-color: #f9f9f9;")
        self._main_content_layout.addWidget(self.output_text)

        self.setGeometry(100, 100, 950, 800) # Tamaño inicial ajustado
        self.update_ui_state() # Inicializar el estado de los botones

    def _clear_layout(self, layout):
        """Helper to clear a layout and its widgets."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())

    def update_ui_state(self):
        """Actualiza el estado de los botones basándose en si una blockchain está cargada."""
        enabled = (self.blockchain is not None and self.blockchain.conn is not None)
        self.data_input.setEnabled(enabled)
        self.add_button.setEnabled(enabled)
        self.load_json_button.setEnabled(enabled)
        # El botón de minar se habilita solo si hay bloques pendientes Y hay blockchain
        self.mine_pending_button.setEnabled(enabled and bool(self.pending_blocks_data))
        self.verify_button.setEnabled(enabled)
        
        db_name = os.path.basename(self.current_db_path) if self.current_db_path else "Ninguna"
        self.setWindowTitle(f"Osiris Blockchain Manager 🔗 - ({db_name})")

    def _init_blockchain(self, db_path):
        """
        Inicializa o re-inicializa la instancia de Blockchain con la ruta especificada.
        Cierra la conexión anterior si existe.
        """
        if self.blockchain:
            self.blockchain.close()
        
        self.current_db_path = db_path
        # Asegurar que el directorio exista
        os.makedirs(os.path.dirname(self.current_db_path), exist_ok=True)

        try:
            self.blockchain = Blockchain(self.current_db_path)
            # Verificar si la conexión se estableció correctamente
            if self.blockchain.conn is None:
                QMessageBox.critical(self, "Error", "No se pudo establecer la conexión con la base de datos.")
                self.blockchain = None
                self.current_db_path = None
                self.update_ui_state()
                return False

            # Cargar o generar claves (se hace automáticamente en Blockchain.__init__)
            if self.blockchain.private_key is None or self.blockchain.public_key is None:
                QMessageBox.warning(self, "Advertencia", "No se pudieron cargar/generar las claves para la blockchain seleccionada. Algunas operaciones podrían fallar.")
                # Aunque las claves no se cargaran, la DB puede estar operativa para otras cosas.
                # Aquí decidimos si permitimos seguir o no. Por ahora, permitimos.

            self.update_output()
            self.update_pending_output()
            self.update_ui_state()
            logging.info(f"Blockchain cambiada a: {self.current_db_path}")
            return True
        except Exception as e:
            logging.critical(f"Error CRÍTICO al inicializar/cambiar blockchain a {db_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Error al Cargar Blockchain", f"No se pudo cargar/crear la blockchain: {e}")
            self.blockchain = None
            self.current_db_path = None
            self.update_ui_state()
            return False

    def load_default_blockchain(self):
        """Intenta cargar la blockchain predeterminada al inicio o solicita una acción."""
        default_db_path = os.path.join(BLOCKCHAIN_DATA_DIR, DEFAULT_DB_NAME)

        if not os.path.exists(default_db_path):
            response = QMessageBox.question(self, "Iniciar Blockchain",
                                            "No se encontró una blockchain predeterminada. ¿Deseas crear una nueva o cargar una existente? 🤔",
                                            QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                                            QMessageBox.Yes)
            if response == QMessageBox.Yes:
                self.new_blockchain_dialog()
            else:
                self.load_blockchain_dialog()
        else:
            logging.info(f"Cargando blockchain predeterminada: {default_db_path}")
            self._init_blockchain(default_db_path)


    def new_blockchain_dialog(self):
        """Diálogo para crear una nueva blockchain."""
        # CORRECCIÓN AQUÍ: Usar QInputDialog.getText
        db_name, ok = QInputDialog.getText(self, "Nueva Blockchain", "Introduce el nombre de la nueva blockchain (ej: mi_empresa):")
        if ok and db_name:
            if not db_name.endswith(".db"):
                db_name += ".db"
            new_db_path = os.path.join(BLOCKCHAIN_DATA_DIR, db_name)
            if os.path.exists(new_db_path):
                QMessageBox.warning(self, "Advertencia", "Ya existe una blockchain con ese nombre. Por favor, elige otro nombre o cárgala. ⚠️")
                return

            if self._init_blockchain(new_db_path):
                QMessageBox.information(self, "Nueva Blockchain", f"¡Blockchain '{db_name}' creada con éxito! 🎉")
            else:
                QMessageBox.critical(self, "Error", f"No se pudo crear la blockchain '{db_name}'. Consulta los logs. 💥")

    def load_blockchain_dialog(self):
        """Diálogo para cargar una blockchain existente."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Cargar Blockchain", BLOCKCHAIN_DATA_DIR,
                                                   "SQLite Databases (*.db);;All Files (*)", options=options)
        if file_name:
            if self._init_blockchain(file_name):
                QMessageBox.information(self, "Cargar Blockchain", f"¡Blockchain '{os.path.basename(file_name)}' cargada con éxito! 📦")
            else:
                QMessageBox.critical(self, "Error", f"No se pudo cargar la blockchain '{os.path.basename(file_name)}'. Consulta los logs. 💥")

    def add_block_manual(self):
        """Maneja la adición manual de un bloque."""
        if not self.blockchain:
            QMessageBox.warning(self, "Advertencia", "Primero carga o crea una blockchain. 💡")
            return
            
        data = self.data_input.toPlainText().strip()
        if data:
            try:
                new_block = self.blockchain.add_block(data)
                if new_block:
                    self.update_output()
                    self.data_input.clear()
                    # Simulando llamada a Osiris con los detalles del bloque
                    osiris_command("blockchain_add", new_block.timestamp.isoformat(), new_block.data, new_block.previous_hash, new_block.hash, new_block.signature.hex())
                    QMessageBox.information(self, "Bloque Añadido", "Bloque añadido manualmente con éxito. 🎉")
            except Exception as e:
                logging.exception("Error al agregar bloque manualmente")
                QMessageBox.critical(self, "Error", f"Error añadiendo bloque manualmente: {e}")
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce datos para el bloque en el campo manual. 💡")

    def load_blocks_from_json(self):
        """Carga bloques desde un archivo JSON para ser minados."""
        if not self.blockchain:
            QMessageBox.warning(self, "Advertencia", "Primero carga o crea una blockchain. 💡")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo JSON de bloques", "",
                                                   "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        QMessageBox.warning(self, "Formato Inválido", "El archivo JSON debe contener una lista de objetos. 🚫")
                        return

                    self.pending_blocks_data = [] # Limpiar bloques pendientes anteriores
                    for item in data:
                        if isinstance(item, dict) and "data" in item and isinstance(item["data"], str):
                            self.pending_blocks_data.append(item["data"])
                        else:
                            logging.warning(f"Ignorando item inválido en JSON (debe ser un objeto con clave 'data' string): {item}")

                    self.update_pending_output()
                    if self.pending_blocks_data:
                        QMessageBox.information(self, "Carga Exitosa", f"{len(self.pending_blocks_data)} bloques cargados y pendientes de minar. Ahora puedes minarlos. ⛏️")
                        self.mine_pending_button.setEnabled(True)
                    else:
                        QMessageBox.warning(self, "Sin Datos", "El archivo JSON no contenía bloques válidos para minar. 😔")
                        self.mine_pending_button.setEnabled(False)

            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Error de JSON", f"Error al parsear el archivo JSON. Asegúrate de que es un JSON válido: {e} 🐛")
                logging.error(f"Error de JSON al cargar {file_name}: {e}", exc_info=True)
            except Exception as e:
                QMessageBox.critical(self, "Error de Archivo", f"Error al leer el archivo: {e} 📁")
                logging.error(f"Error al cargar archivo {file_name}: {e}", exc_info=True)
        self.update_ui_state()

    def mine_pending_blocks(self):
        """Mina los bloques que están pendientes."""
        if not self.blockchain:
            QMessageBox.warning(self, "Advertencia", "Primero carga o crea una blockchain. 💡")
            return

        if not self.pending_blocks_data:
            QMessageBox.information(self, "Sin Bloques", "No hay bloques pendientes para minar. 🤷‍♂️")
            return

        mined_count = 0
        total_to_mine = len(self.pending_blocks_data)
        errors_occurred = False
        blocks_to_process = list(self.pending_blocks_data) # Copia para evitar problemas al modificar la lista

        QMessageBox.information(self, "Minando Bloques", f"Iniciando el minado de {total_to_mine} bloques pendientes... Por favor, espera. ⏳")

        for i, data in enumerate(blocks_to_process):
            logging.info(f"Minando bloque {i+1}/{total_to_mine}: {data[:50]}...")
            new_block = self.blockchain.add_block(data)
            if new_block:
                mined_count += 1
                osiris_command("blockchain_mine", new_block.timestamp.isoformat(), new_block.data, new_block.previous_hash, new_block.hash, new_block.signature.hex())
            else:
                errors_occurred = True
                logging.error(f"Fallo al minar el bloque con datos: {data[:50]}...")

        self.pending_blocks_data = [] # Limpiar la lista de pendientes
        self.update_output()
        self.update_pending_output()
        self.mine_pending_button.setEnabled(False) # Deshabilitar una vez minados

        if errors_occurred:
            QMessageBox.warning(self, "Minado Parcial", f"Se minaron {mined_count} de {total_to_mine} bloques. Hubo errores en algunos bloques. ⚠️")
        else:
            QMessageBox.information(self, "Minado Completo", f"¡Se minaron {mined_count} bloques con éxito! 🥳")
        self.update_ui_state()


    def update_pending_output(self):
        """Actualiza la lista de bloques pendientes en la interfaz."""
        self.pending_blocks_list_widget.clear()
        if not self.pending_blocks_data:
            self.pending_blocks_list_widget.addItem(QListWidgetItem("No hay bloques pendientes por minar. 😌"))
            return

        for i, data in enumerate(self.pending_blocks_data):
            display_data = data if len(data) <= 80 else data[:77] + "..."
            item = QListWidgetItem(f"Bloque #{i+1}: {display_data}")
            self.pending_blocks_list_widget.addItem(item)
        self.update_ui_state()


    def update_output(self):
        """Actualiza la visualización de todos los bloques minados en la interfaz."""
        # Limpiar el layout de botones de bloques
        for i in reversed(range(self.block_layout.count())):
            widget = self.block_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.output_text.clear()
        
        if not self.blockchain: # Si no hay blockchain cargada, no hay nada que mostrar
            self.output_text.setText("No hay una blockchain cargada. Usa el menú 'Archivo' para crear o cargar una. ☝️")
            return

        blocks = self.blockchain.get_all_blocks()
        row = 0
        col = 0
        output_text_buffer = []

        if not blocks:
            self.output_text.setText("La blockchain actual está vacía. ¡Añade tu primer bloque! 😄")
            return

        for block in blocks:
            # Recrear el objeto Block para una representación precisa (especialmente si es un BLOB)
            timestamp_dt = datetime.datetime.fromisoformat(block['timestamp'])
            # Asegurarse de pasar el hash y la firma tal cual están almacenados
            block_obj = Block(timestamp_dt, block['data'], block['previous_hash'], block['hash'], block.get('signature'))

            button = QPushButton(f"Bloque #{block['id']}")
            button.setToolTip(f"ID: {block['id']}\nHash: {block['hash'][:15]}...\nDatos: {block['data'][:50]}...")
            # Usar lambda para pasar argumentos al slot
            button.clicked.connect(lambda checked, block_id=block['id']: self.show_block_details(block_id))
            self.block_layout.addWidget(button, row, col)

            col += 1
            if col > 3: # 4 columnas por fila
                col = 0
                row += 1

            output_text_buffer.append(f"--- Bloque ID: {block['id']} ---")
            output_text_buffer.append(str(block_obj))
            output_text_buffer.append("\n\n")

        self.output_text.setText("".join(output_text_buffer))
        self.update_ui_state()


    def show_block_details(self, block_id):
        """Muestra una ventana con los detalles de un bloque específico."""
        if block_id in self.block_detail_windows and self.block_detail_windows[block_id].isVisible():
            window = self.block_detail_windows[block_id]
            window.activateWindow()
            window.raise_()
            return
        try:
            block_data = self.blockchain.get_block(block_id)
            if block_data:
                block_details_window = BlockDetailsWindow(block_data)
                self.block_detail_windows[block_id] = block_details_window
                block_details_window.show()
                block_details_window.destroyed.connect(lambda: self.block_detail_windows.pop(block_id, None))
            else:
                QMessageBox.warning(self, "Advertencia", f"No se encontró el bloque con ID {block_id}. 🔍")
        except Exception as e:
            logging.exception("Error al mostrar detalles del bloque")
            QMessageBox.critical(self, "Error", f"Error al mostrar detalles del bloque: {e} 💥")

    def verify_blockchain_action(self):
        """Ejecuta la verificación de la blockchain y muestra el resultado."""
        if not self.blockchain:
            QMessageBox.warning(self, "Advertencia", "Primero carga o crea una blockchain para verificar. 💡")
            return
        
        try:
            if self.blockchain.verify_blockchain():
                QMessageBox.information(self, "Verificación Exitosa", "La blockchain es válida. ¡Integridad Confirmada! ✅")
            else:
                QMessageBox.warning(self, "Verificación Fallida", "La blockchain es inválida. ¡ATENCIÓN! Posibles inconsistencias o manipulaciones detectadas. ❌\nConsulta los logs para más detalles.")

        except Exception as e:
            logging.exception("Error al verificar la blockchain")
            QMessageBox.critical(self, "Error", f"Error inesperado al verificar la blockchain: {e} 💣\nConsulta los logs para más detalles.")

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana para cerrar la conexión a la DB."""
        if self.blockchain:
            self.blockchain.close()
        for window in self.block_detail_windows.values():
            window.close() # Cierra las ventanas de detalles abiertas
        event.accept()

# --- Función Principal ---
def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    logging.info("Aplicación Qt inicializada.")
    try:
        # Asegurarse de que el directorio principal de datos exista
        os.makedirs(BLOCKCHAIN_DATA_DIR, exist_ok=True)
        
        window = BlockchainWindow()
        logging.info("Ventana Blockchain inicializada.")
        window.show()
        logging.info(f"Geometría de la ventana: x={window.geometry().x()}, y={window.geometry().y()}, ancho={window.geometry().width()}, alto={window.geometry().height()}")
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Error CRÍTICO al lanzar la ventana principal: {e}", exc_info=True)
        QMessageBox.critical(None, "Error de Aplicación", f"Ocurrió un error crítico al iniciar la aplicación: {e}\nConsulta los logs para más detalles.")
        sys.exit(1)

if __name__ == "__main__":
    main()
