import sys
import datetime
import hashlib
import os
import traceback
import logging
import json  # Import for saving/loading wallets
import secrets
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QMessageBox, QHBoxLayout,
                             QMainWindow, QAction, QFileDialog, QMenuBar, QMenu, QInputDialog,
                             QComboBox, QListWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hmac
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import binascii  # Import for converting bytes to hex strings
import qrcode  # Import for QR code generation
from PyQt5.QtGui import QPixmap, QImage
from io import BytesIO  # For QR code image


# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directorio y archivos de claves (ruta relativa al script)
KEY_DIR = os.path.join(os.path.dirname(__file__), "crypto_demo_keys")
WALLET_FILE = os.path.join(KEY_DIR, "wallets.json")  # File to save wallet data


# --- Funciones criptográficas ---

def generar_claves(contraseña):
    """Genera un par de claves RSA, encripta la privada y guarda ambas."""
    try:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        salt = secrets.token_bytes(16) # Use secrets for secure randomness
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # Increase iterations for better security
            backend=default_backend()
        )
        key = kdf.derive(contraseña.encode('utf-8'))
        iv = secrets.token_bytes(16) # Use secrets for secure randomness
        cipher = Cipher(algorithms.AES(key), modes.CFB8(iv), backend=default_backend()) # CFB8 mode is more resilient to padding issues
        encryptor = cipher.encryptor()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        encrypted_private_key = encryptor.update(private_pem.encode('utf-8')) + encryptor.finalize()

        os.makedirs(KEY_DIR, exist_ok=True) # Create KEY_DIR if it doesn't exist
        return public_pem, encrypted_private_key.hex(), salt.hex(), iv.hex()  # Return hex-encoded encrypted key, salt and iv

    except Exception as e:
        logging.error(f"Error generando claves: {e}", exc_info=True)
        return None, None, None, None

def cargar_claves(contraseña, encrypted_private_key_hex, salt_hex, iv_hex):
    """Carga claves y devuelve objetos clave."""
    try:
        salt = binascii.unhexlify(salt_hex)
        iv = binascii.unhexlify(iv_hex)
        encrypted_key = binascii.unhexlify(encrypted_private_key_hex)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # Match iterations used in key generation
            backend=default_backend()
        )
        key = kdf.derive(contraseña.encode('utf-8'))
        cipher = Cipher(algorithms.AES(key), modes.CFB8(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        private_pem = decryptor.update(encrypted_key) + decryptor.finalize()
        private_key = serialization.load_pem_private_key(private_pem, password=None, backend=default_backend())
        public_key = private_key.public_key()  # Derive public key from the loaded private key
        return private_key, public_key

    except FileNotFoundError:
        logging.error("Archivo de clave no encontrado.")
        return None, None
    except Exception as e:
        logging.error(f"Error cargando claves: {e}", exc_info=True)
        return None, None

def derivar_direccion(public_key):
    """Deriva una dirección de wallet simplificada."""
    try:
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,  # Use DER format
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        hashed_pubkey = hashlib.sha256(public_key_bytes).digest()
        direccion = hashed_pubkey.hex()[:40] # Increase address length
        return direccion

    except Exception as e:
        logging.error(f"Error derivando dirección: {e}", exc_info=True)
        return None

def firmar_mensaje(private_key, mensaje):
    """Firma un mensaje usando la clave privada."""
    try:
        signature = private_key.sign(
            mensaje,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return binascii.hexlify(signature).decode('ascii')  # Return hex string

    except Exception as e:
        logging.error(f"Error firmando mensaje: {e}", exc_info=True)
        return None

def verificar_firma(public_key, mensaje, firma):
    """Verifica una firma contra un mensaje y clave pública."""
    try:
        signature = binascii.unhexlify(firma)  # Convert hex string to bytes
        public_key.verify(
            signature,
            mensaje,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256())
        return True

    except InvalidSignature:
        return False
    except Exception as e:
        logging.error(f"Error verificando firma: {e}", exc_info=True)
        return False

def generar_qr_code(data):
    """Genera un código QR como QPixmap."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, "PNG")
    image = QImage.fromData(bio.getvalue())
    return QPixmap.fromImage(image)

# Clase Wallet
class Wallet:  # Clase para representar una wallet
    def __init__(self, name, address, encrypted_private_key_hex, public_key_pem, salt_hex, iv_hex, balance=0):  # Store public key as PEM string
        self.name = name
        self.address = address
        self.encrypted_private_key_hex = encrypted_private_key_hex
        self.public_key_pem = public_key_pem
        self.salt_hex = salt_hex
        self.iv_hex = iv_hex
        self.balance = balance
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
# Clase CryptoDemoWindow
class CryptoDemoWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.setWindowTitle("Demo Educativa: Criptografía Avanzada")
        self.setGeometry(100, 100, 900, 800) # Increased window size

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Output Text Area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.layout.addWidget(self.output_text)

        # Password Input
        self.password_label = QLabel("Contraseña Maestra:")
        self.layout.addWidget(self.password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_input)

        # Wallet Management
        self.wallet_label = QLabel("Wallet Activa:")
        self.layout.addWidget(self.wallet_label)
        self.wallet_combo = QComboBox()
        self.layout.addWidget(self.wallet_combo)
        self.wallets = {} # Dictionary to store wallet objects {wallet_name: Wallet object}
        self.active_wallet = None

        self.create_wallet_button = QPushButton("Crear Nueva Wallet")
        self.layout.addWidget(self.create_wallet_button)
        self.create_wallet_button.clicked.connect(self.create_wallet)

        # QR Code Display
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.qr_label)

        # Transaction UI
        self.destination_label = QLabel("Wallet Destino:")
        self.layout.addWidget(self.destination_label)
        self.destination_input = QLineEdit()
        self.layout.addWidget(self.destination_input)

        self.amount_label = QLabel("Monto a Enviar:")
        self.layout.addWidget(self.amount_label)
        self.amount_input = QLineEdit()
        self.layout.addWidget(self.amount_input)

        self.send_button = QPushButton("Enviar")
        self.layout.addWidget(self.send_button)
        self.send_button.clicked.connect(self.send_transaction)

        # Transaction History
        self.transaction_label = QLabel("Historial de Transacciones:")
        self.layout.addWidget(self.transaction_label)
        self.transaction_list = QListWidget()
        self.layout.addWidget(self.transaction_list)

        # Message Signing UI
        self.message_label = QLabel("Mensaje a firmar:")
        self.layout.addWidget(self.message_label)
        self.message_input = QLineEdit()
        self.layout.addWidget(self.message_input)

        self.signature_label = QLabel("Firma:")
        self.layout.addWidget(self.signature_label)
        self.signature_output = QLineEdit()
        self.signature_output.setReadOnly(True)
        self.layout.addWidget(self.signature_output)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generar Claves")  # Only generates, doesn't auto-create wallet
        self.sign_button = QPushButton("Firmar Mensaje")
        self.verify_button = QPushButton("Verificar Firma")
        self.show_keys_button = QPushButton("Mostrar Claves") #Fix: Added Show Keys
        self.exit_button = QPushButton("Salir")

        self.button_layout.addWidget(self.generate_button)
        self.button_layout.addWidget(self.sign_button)
        self.button_layout.addWidget(self.verify_button)
        self.button_layout.addWidget(self.show_keys_button) #Fix: Added Show Keys
        self.button_layout.addWidget(self.exit_button)
        self.layout.addLayout(self.button_layout)

        self.generate_button.clicked.connect(self.generate_keys)
        self.sign_button.clicked.connect(self.sign_message)
        self.verify_button.clicked.connect(self.verify_signature)
        self.show_keys_button.clicked.connect(self.show_keys) #Fix: Added Show Keys
        self.exit_button.clicked.connect(self.close)
        self.wallet_combo.currentIndexChanged.connect(self.wallet_changed)

        self.timer = QTimer()  # Timer for updating QR code
        self.timer.timeout.connect(self.update_qr_code)
        self.timer.start(5000)  # Update every 5 seconds

        self.public_key_pem_str = None
        self.encrypted_private_key_hex = None
        self.salt_hex = None
        self.iv_hex = None
        self.contraseña = None

        self.create_menu()
        self.load_wallets() # Load wallets on startup
        self.show_explanation()

    # Menu creation function
    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&Archivo')

        save_action = QAction('&Guardar Wallets', self)
        save_action.triggered.connect(self.save_wallets)
        file_menu.addAction(save_action)

        load_action = QAction('&Cargar Wallets', self)
        load_action.triggered.connect(self.load_wallets)
        file_menu.addAction(load_action)

        show_keys_dir_action = QAction('Mostrar Ubicación de Archivo Wallets', self)
        show_keys_dir_action.triggered.connect(self.show_keys_directory)
        file_menu.addAction(show_keys_dir_action)

        exit_action = QAction('&Salir', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    # Function to display information on the text output area
    def show_explanation(self):
        self.output_text.clear()
        explanation = """<h1>Demo Educativa: Criptografía Avanzada</h1>
<p>Genera claves RSA seguras, gestiona múltiples wallets y simula transacciones. Explora la firma digital y la verificación.</p>
<p>Este software es una demostración simplificada. La seguridad del mundo real requiere medidas más robustas.</p>"""
        self.output_text.setHtml(explanation)

    # Generates the Keys and store them PEM
    def generate_keys(self):
        self.contraseña = self.password_input.text()
        if not self.contraseña:
            QMessageBox.critical(self, "Error", "Ingresa una contraseña maestra")
            return

        try:
            os.makedirs(KEY_DIR, exist_ok=True) # Ensure key directory exists
            public_pem, encrypted_private_key_hex, salt_hex, iv_hex = generar_claves(self.contraseña)
            if public_pem and encrypted_private_key_hex and salt_hex and iv_hex:
                self.public_key_pem_str = public_pem
                self.encrypted_private_key_hex = encrypted_private_key_hex
                self.salt_hex = salt_hex
                self.iv_hex = iv_hex

                QMessageBox.information(self, "Claves Generadas", "Claves generadas. Crea una wallet ahora.")
            else:
                QMessageBox.critical(self, "Error", "Error al generar las claves.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar claves: {e}")

    # Show a form to create new wallet
    def create_wallet(self):
        wallet_name, ok = QInputDialog.getText(self, "Crear Wallet", "Nombre de la Wallet:")
        if ok and wallet_name:
            if wallet_name in self.wallets:
                QMessageBox.critical(self, "Error", "Este nombre de wallet ya existe.")
                return

            if not self.public_key_pem_str or not self.encrypted_private_key_hex or not self.salt_hex or not self.iv_hex:
                QMessageBox.warning(self, "Advertencia", "Genera las claves primero.")
                return

            #Create the wallet and insert into wallets and update de combobox
            private_key, public_key = cargar_claves(self.contraseña, self.encrypted_private_key_hex, self.salt_hex, self.iv_hex)
            address = derivar_direccion(public_key)
            wallet = Wallet(wallet_name, address, self.encrypted_private_key_hex, self.public_key_pem_str, self.salt_hex, self.iv_hex)
            self.wallets[wallet_name] = wallet
            self.wallet_combo.addItem(wallet_name)

            self.output_text.append(f"Wallet '{wallet_name}' creada con dirección: {wallet.address} y balance: {wallet.balance}")
            self.save_wallets() # Save wallets on create
            self.update_qr_code() # Update QR code with the new wallet address
            self.password_input.clear() # Clear password input field

    # Update the transactions of selected wallet
    def wallet_changed(self, index):
        wallet_name = self.wallet_combo.itemText(index)
        if wallet_name in self.wallets:
            self.active_wallet = self.wallets[wallet_name]
            self.output_text.append(f"Wallet activa cambiada a: {wallet_name}")
            self.update_transaction_list()
            self.update_qr_code()
        else:
            self.active_wallet = None
            self.transaction_list.clear()
            self.qr_label.clear()

    # Realize and sign the transactions
    def send_transaction(self):
        if not self.active_wallet:
            QMessageBox.warning(self, "Advertencia", "Selecciona una wallet de origen.")
            return

        destination_address = self.destination_input.text()
        amount_str = self.amount_input.text()

        if not destination_address or not amount_str:
            QMessageBox.warning(self, "Advertencia", "Ingresa la dirección de destino y el monto.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                QMessageBox.warning(self, "Advertencia", "El monto debe ser mayor a cero.")
                return
            if amount > self.active_wallet.balance:
                QMessageBox.warning(self, "Advertencia", "Saldo insuficiente.")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Monto inválido.")
            return

        # Find destination wallet (if it exists in our managed wallets)
        destination_wallet = None
        for wallet_name, wallet in self.wallets.items():
            if wallet.address == destination_address:
                destination_wallet = wallet
                break

        # Sign the transaction
        transaction = {
            "sender": self.active_wallet.address,
            "receiver": destination_address,
            "amount": amount,
            "timestamp": datetime.datetime.now().isoformat()
        }

        private_key, public_key = cargar_claves(self.contraseña, self.active_wallet.encrypted_private_key_hex, self.active_wallet.salt_hex, self.active_wallet.iv_hex)
        message = json.dumps(transaction, sort_keys=True).encode('utf-8')
        signature = firmar_mensaje(private_key, message)
        if not signature:
            QMessageBox.critical(self, "Error", "Error al firmar la transacción.")
            return

        transaction["signature"] = signature  # Add signature to transaction
        # Update balances
        self.active_wallet.balance -= amount
        self.active_wallet.add_transaction(transaction)

        if destination_wallet: # If we know the destination wallet, update its balance
            destination_wallet.balance += amount
            destination_wallet.add_transaction(transaction)  # Add to destination wallet too

        self.output_text.append(f"Transacción enviada: {amount} a {destination_address} firmada con {signature}")
        self.output_text.append(f"Nuevo balance de {self.active_wallet.name}: {self.active_wallet.balance}")
        self.update_transaction_list() # Update transaction view
        self.save_wallets() # Save wallets
        self.password_input.clear() # Clear password input field

    # Function that sign messages, requires message to be non null
    def sign_message(self):
        if not self.active_wallet:
            QMessageBox.warning(self, "Advertencia", "Selecciona una wallet primero.")
            return

        message = self.message_input.text()
        if not message:
            QMessageBox.warning(self, "Advertencia", "Ingresa un mensaje a firmar.")
            return
        try:
            private_key, public_key = cargar_claves(self.contraseña, self.active_wallet.encrypted_private_key_hex, self.active_wallet.salt_hex, self.active_wallet.iv_hex)
            signature = firmar_mensaje(private_key, message.encode('utf-8'))
            if signature:
                self.signature_output.setText(signature)
            else:
                QMessageBox.critical(self, "Error", "Firma fallida.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al firmar mensaje: {e}")

    #Verify Signatures
    def verify_signature(self):
        if not self.active_wallet:
            QMessageBox.warning(self, "Advertencia", "Selecciona una wallet primero.")
            return

        message = self.message_input.text()
        signature = self.signature_output.text()

        if not message or not signature:
            QMessageBox.warning(self, "Advertencia", "Mensaje o firma faltantes.")
            return

        try:
            private_key, public_key = cargar_claves(self.contraseña, self.active_wallet.encrypted_private_key_hex, self.active_wallet.salt_hex, self.active_wallet.iv_hex)
            is_valid = verificar_firma(public_key, message.encode('utf-8'), signature)
            if is_valid:
                QMessageBox.information(self, "Firma", "Firma verificada correctamente.")
            else:
                QMessageBox.warning(self, "Firma", "Firma inválida.")
            self.output_text.append(f"Firma válida: {is_valid}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al verificar la firma: {e}")

    def show_keys(self):
        """Shows the keys for the active wallet."""
        if not self.active_wallet:
            QMessageBox.warning(self, "Advertencia", "Selecciona una wallet primero.")
            return

        try:
            password, ok = QInputDialog.getText(self, "Introduce la contraseña", "Contraseña:", QLineEdit.Password)
            if ok and password:
                private_key, public_key = cargar_claves(password, self.active_wallet.encrypted_private_key_hex, self.active_wallet.salt_hex, self.active_wallet.iv_hex)
                if private_key and public_key:
                    private_pem = private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ).decode('utf-8')
                    public_pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ).decode('utf-8')

                    keys_message = (f"Clave Privada (Desencriptada):\n{private_pem}\n\n"
                                    f"Clave Pública:\n{public_pem}")
                    QMessageBox.information(self, "Claves Generadas", keys_message)
                else:
                    QMessageBox.critical(self, "Error", "Error al cargar claves.")
            else:
                QMessageBox.critical(self, "Error", "Debes ingresar la contraseña.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al mostrar claves: {e}")
            
    #Save wallets data to local
    def save_wallets(self):
        try:
            wallet_data = {}
            for wallet_name, wallet in self.wallets.items():
                wallet_data[wallet_name] = {
                    "name": wallet.name,
                    "address": wallet.address,
                    "encrypted_private_key_hex": wallet.encrypted_private_key_hex,
                    "public_key_pem": wallet.public_key_pem,
                    "salt_hex": wallet.salt_hex,
                    "iv_hex": wallet.iv_hex,
                    "balance": wallet.balance,
                    "transactions": wallet.transactions
                }

            with open(WALLET_FILE, "w") as f:
                json.dump(wallet_data, f)
            QMessageBox.information(self, "Guardado", "Wallets guardadas correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar wallets: {e}")

    #Load wallets data from local
    def load_wallets(self):
        try:
            if not os.path.exists(WALLET_FILE):
                return  # No file to load

            with open(WALLET_FILE, "r") as f:
                wallet_data = json.load(f)

            self.wallets = {}  # Clear existing wallets
            self.wallet_combo.clear()  # Clear the combo box

            for wallet_name, data in wallet_data.items():
                wallet = Wallet(
                    data["name"],
                    data["address"],
                    data["encrypted_private_key_hex"],
                    data["public_key_pem"],
                    data["salt_hex"],
                    data["iv_hex"],
                    data["balance"],
                )

                self.wallets[wallet_name] = wallet
                self.wallet_combo.addItem(wallet_name) # Add to dropdown

            QMessageBox.information(self, "Cargado", "Wallets cargadas correctamente.")

        except FileNotFoundError:
            QMessageBox.information(self, "Cargado", "No se encontro archivo de wallets.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar wallets: {e}")

    #Opens file explorer to the location of the wallet file
    def show_keys_directory(self):
        if not os.path.exists(KEY_DIR):
            os.makedirs(KEY_DIR, exist_ok=True)
            QMessageBox.warning(self, "Directorio no encontrado", f"Se creó el directorio {KEY_DIR}. Genera claves para ver los archivos.")
            return

        try:
            if sys.platform == "win32":
                os.startfile(KEY_DIR)
            elif sys.platform == "darwin":
                os.system(f'open "{KEY_DIR}"')
            else:
                os.system(f'xdg-open "{KEY_DIR}"')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al abrir directorio: {e}")

    #Function to update transactions of the selected wallet in a view area
    def update_transaction_list(self):
        self.transaction_list.clear()
        if self.active_wallet:
            for transaction in self.active_wallet.transactions:
                self.transaction_list.addItem(str(transaction))

    #Function to update qr code
    def update_qr_code(self):
        if self.active_wallet:
            qr_data = self.active_wallet.address
            pixmap = generar_qr_code(qr_data)
            self.qr_label.setPixmap(pixmap.scaledToWidth(200))
        else:
            self.qr_label.clear()

# Start aplication
def main(args):
    app = QApplication(sys.argv)
    window = CryptoDemoWindow(args)
    window.show()
    sys.exit(app.exec_())

#Init
if __name__ == "__main__":
    main(sys.argv)
