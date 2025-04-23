import sys
import datetime
import hashlib
# No necesitamos json ni sqlite3 para este demo de claves específicas
# import json
# import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
                             QTextEdit, QMessageBox, QHBoxLayout, QMainWindow, QAction,
                             QFileDialog, QMenuBar, QMenu)
from PyQt5.QtCore import Qt, QSize # QSize tampoco se usa directamente, pero lo mantenemos.
import os
import traceback
import logging
# Importaciones específicas de cryptography
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# Configuración de Logging (útil para ver lo que pasa "por detrás")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Rutas de los archivos de clave (usamos la ruta relativa al script para simplificar el demo)
# ¡NUEVAMENTE: Esto es MUY INSEGURO en un contexto real!
KEY_DIR = os.path.join(os.path.dirname(__file__), "crypto_demo_keys")
PRIVATE_KEY_FILE = os.path.join(KEY_DIR, "private_key_demo.pem")
PUBLIC_KEY_FILE = os.path.join(KEY_DIR, "public_key_demo.pem")

# --- Funciones Criptográficas de Utilidad (nombres ligeramente acortados) ---

def gen_k(): # generar_claves
    """Genera un par de claves privada y pública RSA y las guarda en archivos PEM."""
    logging.info("[*] Gen. Par de Claves...")
    try:
        # Generación de la clave privada
        # Se basa en seleccionar dos números primos muy grandes y realizar operaciones matemáticas complejas
        # La seguridad proviene de la dificultad computacional de factorizar el producto de esos primos.
        pk = rsa.generate_private_key(
            public_exponent=65537, # Exponente estándar (un número primo pequeño)
            key_size=2048          # Tamaño de la clave en bits (seguridad, 2048 es un estándar actual)
        )
        # Derivación de la clave pública desde la privada
        # La clave pública se deriva de la clave privada usando operaciones matemáticas.
        # Es fácil ir de privada a pública, pero extremadamente difícil ir de pública a privada.
        pubk = pk.public_key()

        # Serialización (codificación) de las claves a formato PEM
        # PEM (Privacy Enhanced Mail) es un formato de texto que representa datos binarios (las claves)
        # utilizando Base64, encerrados entre cabeceras como "-----BEGIN PRIVATE KEY-----" y "-----END PRIVATE KEY-----".
        # No es encriptación por sí solo, sino un formato de empaquetado para transportar claves.
        # ¡OJO! encryption_algorithm=serialization.NoEncryption() es INSEGURO para claves privadas reales
        private_pem = pk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8, # Formato PKCS8 común para claves privadas
            encryption_algorithm=serialization.NoEncryption() # ¡SIN ENCRIPTACIÓN para el demo!
        )

        public_pem = pubk.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo # Formato estándar para claves públicas
        )

        # Asegurar que el directorio de claves existe
        os.makedirs(KEY_DIR, exist_ok=True)

        # Guardar en archivos
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_pem)
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_pem)

        logging.info("[+] Par de claves generado y guardado.")
        # Retornamos como strings decodificadas para mostrarlas fácilmente
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')

    except Exception as e:
        logging.error(f"[!] ERROR gen. claves: {e}", exc_info=True)
        QMessageBox.critical(None, "Error Cripto", f"No se pudieron generar las claves:\n{e}")
        return None, None

def c_pk(): # cargar_clave_privada
    """Carga la clave privada desde el archivo PEM."""
    try:
        with open(PRIVATE_KEY_FILE, "rb") as kf:
            # Para cargar una clave privada encriptada, pasaríamos la contraseña al parámetro password.
            pk = serialization.load_pem_private_key(
                kf.read(),
                password=None # No hay contraseña en este demo, es texto plano
            )
        return pk
    except FileNotFoundError:
        logging.warning(f"[!] Archivo clave privada no encontrado: {PRIVATE_KEY_FILE}")
        # La ventana principal gestionará la falta del archivo
        return None
    except Exception as e:
        logging.error(f"[!] ERROR cargando clave privada: {e}", exc_info=True)
        QMessageBox.critical(None, "Error Cripto", f"No se pudo cargar la clave privada:\n{e}")
        return None

def c_pubk(): # cargar_clave_publica
    """Carga la clave pública desde el archivo PEM."""
    try:
        with open(PUBLIC_KEY_FILE, "rb") as kf:
            # Las claves públicas no se encriptan, por lo que no se necesita contraseña aquí.
            pubk = serialization.load_pem_public_key(kf.read())
        return pubk
    except FileNotFoundError:
         logging.warning(f"[!] Archivo clave pública no encontrado: {PUBLIC_KEY_FILE}")
         # La ventana principal gestionará la falta del archivo
         return None
    except Exception as e:
        logging.error(f"[!] ERROR cargando clave pública: {e}", exc_info=True)
        QMessageBox.critical(None, "Error Cripto", f"No se pudo cargar la clave pública:\n{e}")
        return None

def der_addr(pubk_pem_bytes): # derivar_direccion
    """Deriva una dirección de wallet simple a partir de bytes PEM de clave pública."""
    # Proceso simplificado: En criptomonedas reales se aplican varias funciones hash y codificaciones.
    # Ejemplo Bitcoin: SHA256(public_key) -> RIPEMD160() -> Prefijo de red -> Checksum -> Base58Check
    # Ejemplo Ethereum: Keccak256(public_key_bytes[1:])[-20:] (últimos 20 bytes del hash)
    logging.info("[*] Derivando Dirección...")
    try:
        # Aplicar un hash a la clave pública PEM para obtener una huella digital
        hashed_pubk = hashlib.sha256(pubk_pem_bytes).digest() # Obtenemos bytes del hash SHA256
        # Tomar una parte del hash y convertir a hexadecimal para una "dirección" legible de ejemplo
        direccion_base = hashed_pubk.hex()
        direccion_corta = direccion_base[:40] # Tomamos los primeros 40 caracteres como "dirección" de ejemplo

        logging.info("[+] Dirección derivada.")
        return direccion_corta
    except Exception as e:
        logging.error(f"[!] ERROR derivando dirección: {e}", exc_info=True)
        QMessageBox.critical(None, "Error Cripto", f"No se pudo derivar la dirección:\n{e}")
        return "ERROR_DERIVACION"


def sim_msg(m_str): # simular_mensaje
    """Convierte un string a bytes (necesario para operaciones criptográficas)."""
    return m_str.encode('utf-8')

def sign_msg(pk_obj, m_bytes): # firmar_mensaje
    """
    Firma un mensaje en bytes usando un objeto clave privada.
    Proceso: Se calcula un hash del mensaje y se "encripta" (firma) ese hash
    usando la clave privada y operaciones matemáticas (basadas en modular exponentiation para RSA).
    """
    logging.info("[*] Firmando mensaje...")
    try:
        # El padding PSS y el hash SHA256 son parte del estándar recomendado para firmar con RSA.
        # La firma es el resultado de aplicar la función de firma con la clave privada sobre el hash del mensaje.
        sig = pk_obj.sign(
            m_bytes, # Los datos a firmar (en realidad se hashea internamente si no lo has hecho tú)
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), # Mask Generation Function usando SHA256
                salt_length=padding.PSS.MAX_LENGTH # Usamos el máximo salt length recomendado
            ),
            hashes.SHA256() # Especificamos el algoritmo de hash usado para la firma (o MGF)
        )
        logging.info("[+] Mensaje firmado exitosamente.")
        return sig # La firma resultante es en bytes

    except Exception as e:
        logging.error(f"[!] ERROR firmando mensaje: {e}", exc_info=True)
        QMessageBox.critical(None, "Error Cripto", f"No se pudo firmar el mensaje:\n{e}")
        return None

def verify_sig(pubk_obj, m_bytes, sig_bytes): # verificar_firma
    """
    Verifica una firma usando un objeto clave pública y el mensaje original.
    Proceso: Se aplica la función de verificación con la clave pública sobre la firma.
    Esto "desencripta" la firma para recuperar el hash original. Se compara este hash
    recuperado con el hash calculado independientemente del mensaje original. Si coinciden, la firma es válida.
    """
    logging.info("[*] Verificando firma...")
    try:
        # La función verify realiza las operaciones matemáticas inversas a sign usando la clave pública.
        # Comprueba si la firma es válida para el mensaje dado y la clave pública.
        pubk_obj.verify(
            sig_bytes, # La firma a verificar
            m_bytes, # El mensaje original (se hashea internamente para comparar)
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), # Debe coincidir con el usado para firmar
                salt_length=padding.PSS.MAX_LENGTH # Debe coincidir con el usado para firmar
            ),
            hashes.SHA256() # Debe coincidir con el usado para firmar
        )
        # Si la función verify no lanza una excepción, la verificación es exitosa.
        logging.info("[+] ¡VERIFICACIÓN EXITOSA! La firma es válida.")
        return True

    except InvalidSignature:
        # Esta excepción se lanza si la firma no coincide con el mensaje y la clave pública.
        logging.warning("[!] ¡VERIFICACIÓN FALLIDA! La firma NO es válida.")
        return False

    except Exception as e:
        logging.error(f"[!] ERROR durante verificación: {e}", exc_info=True)
        # No siempre mostrar un critical aquí, a veces es un resultado esperado de la demo
        return False

# --- Clase Principal de la Ventana PyQt5 ---

class CryptoDemoWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.setWindowTitle("Demo Educativa: Criptografía de Clave Pública/Privada")
        self.setGeometry(100, 100, 750, 700) # Aumentamos un poco más el tamaño

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.layout.addWidget(self.output_text)

        self.button_layout = QHBoxLayout()
        self.start_button = QPushButton("Comenzar Demo")
        self.next_button = QPushButton("Siguiente Paso")
        self.exit_button = QPushButton("Salir")

        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.exit_button)
        self.layout.addLayout(self.button_layout)

        # Conectar botones
        self.start_button.clicked.connect(self.start_demo)
        self.next_button.clicked.connect(self.advance_demo_step)
        self.exit_button.clicked.connect(self.close)

        # Estado de la demo
        self.current_step = 0
        self.private_key_pem_str = None
        self.public_key_pem_str = None
        self.direccion_wallet = None
        self.mensaje_original_bytes = None
        self.firma_bytes = None

        self.create_menu()
        self.show_explanation() # Mostrar la explicación inicial al abrir

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('&Archivo')
        restart_action = QAction('&Reiniciar Demo', self)
        restart_action.triggered.connect(self.restart_demo)
        file_menu.addAction(restart_action)

        show_keys_dir_action = QAction('Mostrar Ubicación de Archivos', self)
        show_keys_dir_action.triggered.connect(self.show_keys_directory)
        file_menu.addAction(show_keys_dir_action)

        exit_action = QAction('&Salir', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def show_explanation(self):
        """Muestra la explicación inicial y resetea el estado."""
        self.output_text.clear()
        explanation = """<h1>Demo Educativa: Criptografía de Clave Pública/Privada en Wallets</h1>

<p>Imagina tu wallet de criptomoneda como una caja fuerte con un par de "llaves" matemáticas:</p>

<h2>1. La Clave Privada (Private Key):</h2>
<ul>
    <li>Es <strong>TU SECRETO ABSOLUTO</strong>. ¡NUNCA la compartas!</li>
    <li>Es una cadena larga de caracteres aleatorios (un número muy grande).</li>
    <li>La usas para <strong>firmar transacciones</strong>, demostrando que autorizas el gasto de fondos asociados a tu clave pública.</li>
    <li>Es tu prueba de propiedad de los fondos.</li>
</ul>

<h2>2. La Clave Pública (Public Key):</h2>
<ul>
    <li><strong>NO es secreta</strong>. ¡Puedes compartirla libremente!</li>
    <li>Se genera matemáticamente a partir de la clave privada, pero es prácticamente imposible obtener la privada desde la pública.</li>
    <li>Se usa para <strong>verificar firmas</strong> creadas con la clave privada correspondiente.</li>
</ul>

<h2>La Dirección de Wallet:</h2>
<ul>
    <li>Es una representación más corta y legible de tu clave pública (obtenida aplicando funciones hash a la pública y otras transformaciones).</li>
    <li>Es lo que le das a otros para que te <strong>envíen fondos</strong>.</li>
    <li>Es pública y segura para compartir.</li>
</ul>

<h2>Cómo Funciona la Demostración:</h2>
<ol>
    <li><strong>Generación y Mate:</strong> Creamos un par de claves (privada y pública) y vemos cómo se relacionan matemáticamente.</li>
    <li><strong>Dirección:</strong> Derivamos una dirección a partir de la pública (usando hashes).</li>
    <li><strong>Almacenamiento y Codificación:</strong> Vemos cómo se codifican (formato PEM) y discutimos la <strong>seguridad crítica</strong> de su almacenamiento.</li>
    <li><strong>Recuperación Simulada:</strong> Cargamos las claves desde los archivos (simulando acceder a tu wallet).</li>
    <li><strong>Firma:</strong> Usamos la clave privada (cargada) para firmar un "mensaje" (como una transacción).</li>
    <li><strong>Verificación (Éxito):</strong> Usamos la clave pública (cargada) para verificar la firma con el mensaje original (vemos que coincide).</li>
    <li><strong>Verificación (Mensaje Alterado):</strong> Intentamos verificar la firma con un mensaje modificado (debería fallar, mostrando que la integridad está protegida).</li>
    <li><strong>Verificación (Clave Incorrecta):</strong> Intentamos verificar la firma con una clave pública diferente (debería fallar, mostrando que la autenticidad está protegida).</li>
</ol>
"""
        self.output_text.setHtml(explanation) # Usamos setHtml para formato básico
        self.current_step = 0
        # Resetear variables de estado para una nueva demo
        self.private_key_pem_str = None
        self.public_key_pem_str = None
        self.direccion_wallet = None
        self.mensaje_original_bytes = None
        self.firma_bytes = None

        self.start_button.setEnabled(True)
        self.next_button.setEnabled(False)
        self.setWindowTitle("Demo Educativa: Claves Pública/Privada") # Resetear título si se cambió

    def start_demo(self):
        """Inicia el primer paso de la demo."""
        self.output_text.clear()
        self.output_text.append("--- COMENZANDO DEMOSTRACIÓN ---")
        self.start_button.setEnabled(False)
        self.next_button.setEnabled(True)
        self.advance_demo_step() # Ir directamente al primer paso

    def advance_demo_step(self):
        """Avanza al siguiente paso de la demo."""
        self.current_step += 1
        self.output_text.append(f"<hr><h2>--- PASO {self.current_step} ---</h2>") # Separador visual

        step_failed = False # Bandera para saber si un paso falló y deshabilitar el siguiente

        try:
            if self.current_step == 1:
                # Paso 1: Generar Claves y Guardar (Incluyendo la base Matemática)
                self.output_text.append("<strong>Paso 1: Generación de Claves y Base Matemática</strong>")
                self.output_text.append("<p>Estamos creando un nuevo par de llaves criptográficas (Privada y Pública).</p>")
                self.output_text.append("<p>La relación entre ellas se basa en problemas matemáticos difíciles. Para RSA (el algoritmo usado en este demo):</p>")
                self.output_text.append("<ul>")
                self.output_text.append("<li>Se eligen dos números primos muy grandes al azar.</li>")
                self.output_text.append("<li>Se multiplican para obtener un número N.</li>")
                self.output_text.append("<li>La <strong>clave pública</strong> se deriva de N y otro número público.</li>")
                self.output_text.append("<li>La <strong>clave privada</strong> se deriva de los dos números primos originales (que son secretos).</li>")
                self.output_text.append("<li>La seguridad radica en que es fácil multiplicar dos primos, pero extremadamente difícil hacer el camino inverso (factorizar N) si N es muy grande. Solo con la clave privada (que conoce los primos originales) se pueden realizar ciertas operaciones matemáticas que la clave pública no puede.</li>")
                self.output_text.append("</ul>")
                self.output_text.append("<p>El par generado tiene esta propiedad clave: algo 'cerrado' (firmado) con la clave privada solo puede ser 'abierto' (verificado) con la clave pública correspondiente.</p>")
                self.output_text.append("<p>Ahora, generamos y guardamos las claves:</p>")

                private_pem, public_pem = gen_k() # Llama a la función de generación y guardado
                if private_pem and public_pem:
                    self.private_key_pem_str = private_pem
                    self.public_key_pem_str = public_pem

                    self.output_text.append("\nTu Clave PRIVADA (El secreto):")
                    self.output_text.append(f"<pre>{private_pem}</pre>") # Usar <pre> para formato

                    self.output_text.append("\nTu Clave PÚBLICA (Para verificar):")
                    self.output_text.append(f"<pre>{public_pem}</pre>")
                    self.output_text.append("Puedes compartir esto para que otros verifiquen firmas creadas por ti.")

                    QMessageBox.information(self, "Paso 1 Completo", "Claves generadas, guardadas y explicación matemática.")
                else:
                    self.output_text.append("[!] Falló la generación de claves.")
                    step_failed = True
                    QMessageBox.critical(self, "Error", "Falló la generación de claves.")


            elif self.current_step == 2:
                # Paso 2: Derivación de Dirección (Usando Hashes)
                if not self.public_key_pem_str:
                    self.output_text.append("[!] Error: Clave pública no disponible para derivar dirección.")
                    step_failed = True
                else:
                    self.output_text.append("<strong>Paso 2: Derivación de Dirección (usando Funciones Hash)</strong>")
                    self.output_text.append("<p>La clave pública es larga y compleja. Para facilitar su uso, se deriva una 'dirección de wallet' más corta y legible.</p>")
                    self.output_text.append("<p>Esto se hace aplicando una o más <strong>funciones hash criptográficas</strong> a la clave pública. Una función hash toma cualquier entrada de tamaño y produce una salida de tamaño fijo (como una huella digital única).</p>")
                    self.output_text.append("<p>Propiedades clave de un buen hash:</p><ul><li><strong>Determinista:</strong> La misma entrada siempre produce la misma salida.</li><li><strong>Una sola vía:</strong> Es imposible (computacionalmente) obtener la entrada a partir de la salida (hash).</li><li><strong>Resistencia a colisiones:</strong> Es extremadamente difícil encontrar dos entradas diferentes que produzcan el mismo hash.</li><li><strong>Efecto avalancha:</strong> Un pequeño cambio en la entrada cambia drásticamente la salida.</li></ul>")
                    self.output_text.append("<p>Las direcciones de wallet son el hash (o una combinación de hashes y otras codificaciones) de tu clave pública. Son públicas y seguras para compartir porque no se puede derivar la clave pública (y mucho menos la privada) a partir de la dirección.</p>")
                    self.output_text.append("<p>Ahora, generamos tu dirección de ejemplo:</p>")

                    # Necesitamos los bytes de la clave pública PEM para el hashing
                    self.direccion_wallet = der_addr(self.public_key_pem_str.encode('utf-8'))
                    if self.direccion_wallet:
                        self.output_text.append(f"\nSimulación de tu Dirección de Wallet:")
                        self.output_text.append(f"<code>{self.direccion_wallet}</code>") # Usar <code> para código/dirección
                        self.output_text.append("<br>Esta dirección es lo que le das a otros para recibir fondos. Es pública y segura para compartir.")
                        QMessageBox.information(self, "Paso 2 Completo", "Dirección de wallet derivada y explicación de hashes.")
                    else:
                        self.output_text.append("[!] Falló la derivación de dirección.")
                        step_failed = True
                        QMessageBox.critical(self, "Error", "Falló la derivación de dirección.")

            elif self.current_step == 3:
                 # Paso 3: Almacenamiento y Codificación (Incluyendo la Seguridad)
                 self.output_text.append("<strong>Paso 3: Almacenamiento, Codificación (PEM) y Seguridad Crítica</strong>")
                 self.output_text.append("<p>Hemos generado tus claves y las hemos guardado en archivos.</p>")
                 self.output_text.append("<p>El formato utilizado es <strong>PEM (Privacy Enhanced Mail)</strong>. Es una forma estándar de codificar datos binarios (como claves criptográficas, certificados) en un formato de texto legible por humanos (usando Base64).</p>")
                 self.output_text.append("<p>Un archivo PEM típico se ve así (con tu clave privada dentro):</p><pre>-----BEGIN PRIVATE KEY-----\n[Mucho texto Base64 aquí...]\n-----END PRIVATE KEY-----</pre>")
                 self.output_text.append("<p>La codificación Base64 simplemente convierte los bytes de la clave en caracteres ASCII imprimibles. Para usar la clave, se necesita <strong>descodificar</strong> de Base64 primero.</p>")
                 self.output_text.append("<p>En este demo, los archivos PEM se guardaron (inseguramente) en:\n<code>{}</code></p>".format(KEY_DIR))

                 self.output_text.append("\n<span style='color: red;'><h2>--- ¡ADVERTENCIA DE SEGURIDAD CRÍTICA! ---</h2></span>")
                 self.output_text.append("<p>Guardar tu Clave Privada en un archivo SIN ENCRIPTACIÓN (como en este demo, donde usamos <code>serialization.NoEncryption()</code> al serializar) es <strong>EXTREMADAMENTE INSEGURO</strong> en un contexto global real.</p>")
                 self.output_text.append("<p><strong>¿Por qué es inseguro a nivel global?</strong></p>")
                 self.output_text.append("<ul>")
                 self.output_text.append("<li>Tu clave privada es el control total de tus fondos. Si alguien la obtiene, pueden robarlos al instante, sin necesidad de contraseñas o autenticación adicional.</li>")
                 self.output_text.append("<li>En la era de internet, tu computadora o dispositivo puede ser objetivo de hackers, malware (virus, troyanos, keyloggers), o accesos no autorizados (incluso físicos si te roban el dispositivo).</li>")
                 self.output_text.append("<li>Un archivo PEM sin encriptar es trivial de encontrar y leer para un atacante una vez que accede a tu sistema. Es como encontrar la llave maestra de tu caja fuerte en una nota adhesiva.</li>")
                 self.output_text.append("<li>Una vez robada y utilizada, es casi imposible recuperar tus fondos.</li>")
                 self.output_text.append("</ul>")
                 self.output_text.append("<p><strong>¿Cómo se protege la Clave Privada de forma segura en la vida real?</strong></p>")
                 self.output_text.append("<ul>")
                 self.output_text.append("<li><strong>Encriptación del Archivo de Clave:</strong> El archivo PEM *mismo* se encripta con una contraseña FUERTE (usando un algoritmo como AES, por ejemplo, especificado en <code>encryption_algorithm</code> al serializar). Para cargar la clave, DEBES proporcionar la contraseña correcta.</li>")
                 self.output_text.append("<li><strong>Frases de Semilla (Mnemonic Phrases):</strong> La mayoría de las wallets modernas no guardan el archivo de clave privada directamente. En su lugar, generan una lista de 12 o 24 palabras (la frase de semilla) que, usando estándares como BIP39, genera <strong>determinísticamente</strong> tu clave privada y todas tus direcciones. <strong>Debes guardar esta frase de forma SEGURA OFFLINE (escrita en papel, metal, etc.)</strong>. Si pierdes tu dispositivo o wallet, puedes 'recuperar' tus fondos importando la frase de semilla en otra wallet compatible. La frase de semilla es tu backup maestro, y también debe mantenerse secreta.</li>")
                 self.output_text.append("<li><strong>Hardware Wallets:</strong> Dispositivos físicos dedicados que almacenan la clave privada en un chip seguro y aislado, OFFLINE. La clave privada nunca sale del dispositivo. Las transacciones se firman DENTRO del hardware wallet.</li>")
                 self.output_text.append("<li><strong>Multi-Signature Wallets:</strong> Wallets que requieren múltiples firmas (de diferentes claves privadas, posiblemente en diferentes dispositivos o controladas por diferentes personas) para autorizar una transacción. Esto añade una capa de seguridad al requerir cooperación.</li>")
                 self.output_text.append("</ul>")
                 self.output_text.append("<p>En resumen: la seguridad de tu Clave Privada (y/o tu frase de semilla) es la seguridad de tus fondos.</p>")
                 self.output_text.append("<span style='color: red;'><h2>--- FIN ADVERTENCIA DE SEGURIDAD ---</h2></span>")

                 self.output_text.append("\nUsa el menú Archivo -> Mostrar Ubicación de Archivos para ver dónde se guardaron (inseguramente) en este demo.")

                 QMessageBox.information(self, "Paso 3 Completo", "Explicación de almacenamiento, codificación (PEM) y SEGURIDAD.")


            elif self.current_step == 4:
                 # Paso 4: Recuperación Simulada (Cargar desde archivo)
                 self.output_text.append("<strong>Paso 4: Recuperación Simulada (Cargar desde Archivo)</strong>")
                 self.output_text.append("<p>Simulamos lo que hace una wallet de software simple: cargar las claves desde los archivos guardados.</p>")
                 self.output_text.append("<p>Internamente, la wallet lee los archivos PEM, <strong>descodifica</strong> el contenido Base64 y, si la clave privada estaba encriptada (no en este demo), pide la contraseña para <strong>desencriptarla</strong> y obtener el objeto clave usable.</p>")

                 # Intentamos cargar para ver si los archivos están ahí y son válidos
                 pk_obj_rec = c_pk()
                 pubk_obj_rec = c_pubk()

                 if pk_obj_rec and pubk_obj_rec:
                     self.output_text.append("[+] Claves cargadas exitosamente desde archivos PEM.")
                     self.output_text.append("<br>Como mencionamos, en wallets reales, la 'recuperación' de la clave privada operativa suele ser desde una <strong>frase de semilla</strong> (que generas al configurar) o un archivo de wallet <strong>encriptado</strong>, que requieren una acción adicional (ingresar palabras, contraseña) para obtener la clave privada operativa y lista para firmar.")
                     QMessageBox.information(self, "Paso 4 Completo", "Recuperación simulada (carga de archivos).")
                 else:
                      self.output_text.append("[!] Falló la carga de claves desde archivos. Asegúrate de haber generado claves en el Paso 1 y que los archivos existan y no estén corruptos.")
                      step_failed = True
                      QMessageBox.warning(self, "Advertencia", "Falló la carga de claves. Asegúrate de haberlas generado en el paso 1.")

            elif self.current_step == 5:
                 # Paso 5: Firma de Mensaje con Clave Privada
                pk_obj_sign = c_pk() # Cargar la clave privada desde el archivo para firmar
                if pk_obj_sign:
                    self.output_text.append("<strong>Paso 5: Firma (con la Clave Privada)</strong>")
                    self.output_text.append("<p>Ahora que tenemos la clave privada (cargada/recuperada), la usamos para firmar un mensaje. Este mensaje representa una transacción (por ejemplo, 'Enviar 50 monedas a X dirección').</p>")
                    self.output_text.append("<p><strong>Proceso de Firma:</strong></p><ul><li>La wallet toma los detalles exactos del mensaje/transacción.</li><li>Calcula el <strong>hash</strong> de ese mensaje.</li><li>Usa la <strong>clave privada</strong> para realizar una operación matemática (basada en la relación con la clave pública) sobre este hash, produciendo la <strong>firma digital</strong>.</li><li>La firma es única para ese mensaje Y esa clave privada.</li></ul>")

                    # Definimos el mensaje a firmar
                    # Incluimos elementos variables para asegurar que el mensaje cambia cada vez si se reinicia
                    mensaje_original_str = f"Transferir 50 monedas a otra_direccion_{hashlib.sha256(os.urandom(8)).hexdigest()[:6]}. ID Tx: {hashlib.sha256(os.urandom(16)).hexdigest()[:8]}. Hora: {datetime.datetime.now().isoformat()}"
                    self.mensaje_original_bytes = sim_msg(mensaje_original_str)
                    self.output_text.append(f"\nMensaje a firmar: <i>'{mensaje_original_str}'</i>")
                    self.output_text.append("Esta firma prueba que tú autorizas exactamente este mensaje, y solo tú puedes crearla con tu clave privada.")

                    self.firma_bytes = sign_msg(pk_obj_sign, self.mensaje_original_bytes) # Llama a la función de firma

                    if self.firma_bytes:
                        self.output_text.append("\nFirma Digital generada:")
                        self.output_text.append(f"<code>{self.firma_bytes.hex()}</code>") # Mostrar en hex
                        self.output_text.append("<br>Esta es la prueba criptográfica de tu autorización para este mensaje específico.")
                        QMessageBox.information(self, "Paso 5 Completo", "Mensaje firmado con clave privada.")
                    else:
                        self.output_text.append("[!] Falló la firma del mensaje.")
                        step_failed = True
                        QMessageBox.critical(self, "Error", "Falló la firma del mensaje.")
                else:
                    self.output_text.append("[!] Error: Clave privada no disponible para firmar.")
                    step_failed = True
                    QMessageBox.warning(self, "Advertencia", "Clave privada no encontrada para firmar.")

            elif self.current_step == 6:
                 # Paso 6: Verificar Firma (Correctamente)
                pubk_obj_verify = c_pubk() # Cargar la clave pública desde el archivo
                if pubk_obj_verify and self.mensaje_original_bytes is not None and self.firma_bytes is not None: # Verificar si los datos existen
                    self.output_text.append("<strong>Paso 6: Verificación (con Éxito)</strong>")
                    self.output_text.append("<p>Cualquiera que tenga el mensaje original, la firma y tu clave pública puede verificar si la firma es auténtica y si el mensaje no fue alterado.</p>")
                    self.output_text.append("<p><strong>Proceso de Verificación:</strong></p><ul><li>El verificador (ej: otro nodo de la red) recibe el mensaje Y la firma.</li><li>Calcula el <strong>hash</strong> del mensaje recibido (exactamente como se hizo al firmar).</li><li>Usa la <strong>clave pública</strong> para realizar una operación matemática inversa sobre la <strong>firma</strong>. Esto 'desencripta' la firma para obtener el hash que se usó al firmar.</li><li>Compara el hash calculado del mensaje recibido con el hash obtenido de la firma.</li><li>Si ambos hashes <strong>COINCIDEN</strong>, la verificación es exitosa. Esto prueba que la firma fue creada por el dueño de la clave privada correspondiente a esa clave pública Y que el mensaje no ha sido modificado desde que se firmó.</li></ul>")

                    self.output_text.append("\nVerificando la Firma (con la Clave PÚBLICA Correcta)...")
                    self.output_text.append("\nMensaje utilizado para verificar: <i>(el original del paso 5)</i>")
                    self.output_text.append("Firma utilizada para verificar: <i>(la original del paso 5)</i>")
                    self.output_text.append("Clave Pública utilizada para verificar: <i>(la tuya del paso 1)</i>")

                    verificacion_exitosa = verify_sig(pubk_obj_verify, self.mensaje_original_bytes, self.firma_bytes) # Llama a la función de verificación

                    if verificacion_exitosa:
                        self.output_text.append("\n<span style='color: green;'><strong>¡VERIFICACIÓN EXITOSA!</strong></span>")
                        self.output_text.append("Esto confirma que la firma es auténtica (viene del dueño de la clave privada) <strong>Y</strong> que el mensaje no ha sido alterado desde que se firmó.")
                        QMessageBox.information(self, "Paso 6 Completo", "Verificación correcta exitosa.")
                    else:
                         self.output_text.append("\n<span style='color: red;'><strong>¡VERIFICACIÓN FALLIDA!</strong></span> (¡Inesperado si todo es correcto!)")
                         self.output_text.append("Esto indica un problema en la demo o que los archivos de clave/el mensaje han sido modificados externamente.")
                         step_failed = True
                         QMessageBox.critical(self, "Error", "La verificación correcta falló (¡Problema en el código o archivos!).")
                else:
                    self.output_text.append("[!] Error: Clave pública, mensaje original o firma no disponibles para verificar.")
                    step_failed = True
                    QMessageBox.warning(self, "Advertencia", "Faltan datos para la verificación.")


            elif self.current_step == 7:
                 # Paso 7: Demostración de Verificación Fallida (Mensaje Alterado)
                if self.firma_bytes is None or self.public_key_pem_str is None or self.mensaje_original_bytes is None:
                    self.output_text.append("[!] Error: Firma, clave pública o mensaje original no disponibles.")
                    step_failed = True
                    return

                self.output_text.append("<strong>Paso 7: Verificación con Mensaje Alterado (Debería Fallar)</strong>")
                self.output_text.append("<p>Veamos qué pasa si alguien intenta modificar el mensaje ORIGINAL después de que ha sido firmado, pero usa la firma original.</p>")
                self.output_text.append("<p>Cualquier cambio, por mínimo que sea, en el mensaje original hará que su hash cambie. Cuando el verificador calcule el hash del mensaje *alterado* y lo compare con el hash 'desencriptado' de la firma ORIGINAL, NO coincidirán.</p>")

                mensaje_alterado_str = self.mensaje_original_bytes.decode('utf-8') + " - <strong>MENSAJE ALTERADO!</strong>" # Añadimos algo al mensaje original
                mensaje_alterado_bytes = sim_msg(mensaje_alterado_str)
                self.output_text.append(f"\nMensaje Alterado: <i>'{mensaje_alterado_str}'</i>")
                self.output_text.append("Usando la firma ORIGINAL pero con este mensaje ALTERADO.")

                pubk_obj_verify = c_pubk() # Cargar la clave pública de nuevo
                if pubk_obj_verify:
                    verificacion_fallida_mensaje = verify_sig(pubk_obj_verify, mensaje_alterado_bytes, self.firma_bytes) # Llama a la función de verificación

                    if not verificacion_fallida_mensaje:
                        self.output_text.append("\n<span style='color: green;'><strong>¡VERIFICACIÓN FALLIDA, como se esperaba!</strong></span>")
                        self.output_text.append("Esto demuestra que cualquier pequeño cambio en el mensaje (incluso un espacio o una letra) invalida la firma.")
                        self.output_text.append("La firma digital <strong>protege la integridad</strong> del mensaje.")
                        QMessageBox.information(self, "Paso 7 Completo", "Verificación con mensaje alterado falló (correcto).")
                    else:
                        self.output_text.append("\n<span style='color: red;'><strong>¡ALERTA! ¡VERIFICACIÓN EXITOSA con mensaje alterado!</strong></span> (Esto indica un problema grave)")
                        self.output_text.append("Esto NO debería pasar con criptografía correcta. El mensaje ha sido alterado pero la firma parece válida.")
                        step_failed = True
                        QMessageBox.critical(self, "Error", "La verificación con mensaje alterado tuvo éxito (¡Problema en el código!).")
                else:
                    self.output_text.append("[!] Error: Clave pública no disponible para verificación.")
                    step_failed = True
                    QMessageBox.warning(self, "Advertencia", "Faltan datos para la verificación (mensaje alterado).")

            elif self.current_step == 8:
                 # Paso 8: Demostración de Verificación Fallida (Clave Pública Incorrecta)
                if self.firma_bytes is None or self.mensaje_original_bytes is None:
                    self.output_text.append("[!] Error: Firma o mensaje original no disponibles.")
                    step_failed = True
                    return

                self.output_text.append("<strong>Paso 8: Verificación con Clave Pública Incorrecta (Debería Fallar)</strong>")
                self.output_text.append("<p>Ahora veamos qué pasa si alguien intenta verificar la firma usando una clave pública que NO es la que corresponde al par con el que se firmó.</p>")
                self.output_text.append("<p>Aunque la clave pública esté matemáticamente ligada a una *privada*, esa relación es única para *ese par específico*. La clave pública de Pepito no puede verificar una firma creada con la clave privada de Juanito.</p>")
                self.output_text.append("<p>Generando un par de claves COMPLETAMENTE NUEVO solo para obtener una clave pública diferente para la prueba...</p>")

                try:
                    # Generamos un nuevo par solo para obtener una clave pública diferente.
                    private_key_otra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                    public_key_otra = private_key_otra.public_key()
                    # No necesitamos serializarla, solo el objeto clave para verificar.

                    self.output_text.append("[+] Clave pública incorrecta generada para la prueba.")
                    self.output_text.append("\nUsando la firma ORIGINAL, el mensaje ORIGINAL, pero una clave PÚBLICA DIFERENTE (del par recién creado).")

                    verificacion_fallida_clave = verify_sig(public_key_otra, self.mensaje_original_bytes, self.firma_bytes) # Llama a la función de verificación

                    if not verificacion_fallida_clave:
                        self.output_text.append("\n<span style='color: green;'><strong>¡VERIFICACIÓN FALLIDA, como se esperaba!</strong></span>")
                        self.output_text.append("Esto demuestra que solo la clave pública que corresponde al par original (el dueño de la clave privada que firmó) puede verificar la firma.")
                        self.output_text.append("La firma digital <strong>protege la autenticidad</strong> del firmante.")
                        QMessageBox.information(self, "Paso 8 Completo", "Verificación con clave incorrecta falló (correcto).")
                    else:
                        self.output_text.append("\n<span style='color: red;'><strong>¡ALERTA! ¡VERIFICACIÓN EXITOSA con clave pública incorrecta!</strong></span> (Esto indica un problema grave)")
                        self.output_text.append("Esto NO debería pasar. La firma parece válida incluso con la clave pública equivocada.")
                        step_failed = True
                        QMessageBox.critical(self, "Error", "La verificación con clave incorrecta tuvo éxito (¡Problema en el código!).")

                except Exception as e:
                     self.output_text.append(f"[!] ERROR al generar clave incorrecta para la demostración: {e}", exc_info=True)
                     QMessageBox.critical(self, "Error", f"Error al generar clave incorrecta para la demostración:\n{e}")
                     step_failed = True


            elif self.current_step > 8:
                # Fin de la demo
                self.output_text.append("\n======================================================")
                self.output_text.append("             FIN DE LA DEMOSTRACIÓN                  ")
                self.output_text.append("======================================================")
                self.output_text.append("<p>Has completado la demo educativa sobre Claves Pública y Privada.</p>")
                self.output_text.append("<p><strong>Principales puntos a recordar:</strong></p>")
                self.output_text.append("<ul>")
                self.output_text.append("<li>Tu Clave PRIVADA es el control total de tus fondos. ¡Mantenla SECRETA y muy bien protegida!</li>")
                self.output_text.append("<li>Tu Clave PÚBLICA (o tu dirección derivada) es tu 'número de cuenta'. ¡Compártela para recibir fondos!</li>")
                self.output_text.append("<li>Las firmas digitales, creadas con la Clave Privada y verificadas con la Pública, garantizan la autenticidad (quién firmó) y la integridad (que el mensaje no cambió) de las transacciones.</li>")
                self.output_text.append("<li>Guardar claves privadas sin encriptación es muy inseguro. Las wallets reales usan encriptación, frases de semilla, o hardware seguro para proteger tu secreto.</li>")
                self.output_text.append("</ul>")
                self.output_text.append("======================================================")
                self.next_button.setEnabled(False) # Deshabilitar el botón "Siguiente Paso"
                QMessageBox.information(self, "Demo Finalizada", "La demostración ha concluido.")
                self.setWindowTitle("Demo Educativa: Claves Pública/Privada - Finalizada")

        except Exception as e:
            # Captura cualquier error inesperado en los pasos de la demo
            logging.exception("Error inesperado durante un paso de la demo")
            self.output_text.append(f"\n<span style='color: red;'><strong>[!] ERROR INESPERADO DURANTE EL PASO {self.current_step}:</strong></span>")
            self.output_text.append(f"<pre>{traceback.format_exc()}</pre>") # Mostrar el traceback completo
            QMessageBox.critical(self, f"Error Inesperado Paso {self.current_step}", f"Ocurrió un error inesperado:\n{e}\n\nVerifique el log para más detalles.")
            step_failed = True

        # Si algún paso falló (intencionalmente - verificaciones negativas - o por error),
        # deshabilitar el botón "Siguiente Paso" solo si fue un error no esperado.
        # Las fallas intencionales (pasos 7 y 8) no deberían detener la demo,
        # pero si ocurre un error *durante* esos pasos, sí deberíamos detenernos.
        # Mejor aún: si verify_sig regresa False, es el resultado esperado de los pasos 7 y 8.
        # Si regresa True inesperadamente en 7/8, o lanza una excepción, es un fallo real.

        # Reevaluamos la bandera step_failed basándonos en los resultados de los pasos 7 y 8.
        if self.current_step == 7 and not verificacion_fallida_mensaje: # Si paso 7 falló como debe (retornó False)
             step_failed = False # No es un fallo que deba detener la demo
        if self.current_step == 8 and not verificacion_fallida_clave: # Si paso 8 falló como debe (retornó False)
             step_failed = False # No es un fallo que deba detener la demo

        if step_failed: # Si hubo un fallo que NO fue la verificación esperada en pasos 7 u 8
             self.next_button.setEnabled(False)
             self.output_text.append("\n<span style='color: red;'><strong>Demo detenida debido a un error. Reinicia para intentarlo de nuevo.</strong></span>")
        elif self.current_step > 8: # Si la demo terminó
             self.next_button.setEnabled(False) # Asegurarse de que el botón Siguiente esté deshabilitado al final


    def restart_demo(self):
        """Reinicia la demostración."""
        logging.info("[*] Reiniciando demostración...")
        self.show_explanation() # Mostrar la explicación de nuevo y resetear estado
        self.output_text.append("<hr><h2>--- DEMOSTRACIÓN REINICIADA ---</h2>")
        QMessageBox.information(self, "Demo Reiniciada", "La demostración se ha reiniciado. Presiona 'Comenzar Demo' para empezar de nuevo.")

    def show_keys_directory(self):
        """Abre el directorio donde se guardan los archivos (claves)."""
        logging.info(f"[*] Intentando abrir directorio de archivos: {KEY_DIR}")
        if not os.path.exists(KEY_DIR):
             # Si el directorio no existe, lo creamos y avisamos
             try:
                 os.makedirs(KEY_DIR, exist_ok=True)
                 QMessageBox.warning(self, "Directorio no Encontrado",
                                     f"El directorio de archivos no existía, se ha creado:\n{KEY_DIR}\n\n"
                                     "Los archivos de clave (.pem) se guardarán aquí después de generar las claves.")
                 logging.info(f"[+] Directorio creado: {KEY_DIR}")
             except Exception as e:
                  logging.error(f"[!] ERROR creando directorio: {e}", exc_info=True)
                  QMessageBox.critical(self, "Error", f"No se pudo crear el directorio:\n{KEY_DIR}\n\nError: {e}")
                  return # Salir si falla la creación

        # Intentar abrir el directorio en el explorador de archivos del sistema operativo
        try:
            if sys.platform == "win32":
                os.startfile(KEY_DIR)
            elif sys.platform == "darwin": # macOS
                os.system(f'open "{KEY_DIR}"')
            else: # linux variants
                os.system(f'xdg-open "{KEY_DIR}"')
            logging.info(f"[+] Directorio abierto exitosamente: {KEY_DIR}")
        except Exception as e:
            logging.error(f"[!] ERROR al abrir directorio: {e}", exc_info=True)
            QMessageBox.critical(self, "Error al abrir directorio", f"No se pudo abrir el directorio:\n{KEY_DIR}\n\nError: {e}")


# --- Función Principal para Ejecutar la Aplicación ---
def main(args):
    # args contendrá los argumentos de la línea de comandos si se pasan
    # print("Argumentos recibidos:", args) # Puedes usar esto para depurar argumentos si los necesitas

    app = QApplication(sys.argv) # sys.argv permite que Qt procese argumentos estándar de línea de comandos

    window = CryptoDemoWindow(args)
    window.show()

    sys.exit(app.exec_()) # Ejecutar el bucle de eventos principal

if __name__ == "__main__":
    # Pasamos sys.argv a main para que la ventana principal tenga acceso si es necesario.
    main(sys.argv)
