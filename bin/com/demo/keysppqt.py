import sys
import datetime
import hashlib
import json # Aunque no lo usamos para transacciones aquí, se podría usar para serializar/deserializar otros datos.
import sqlite3 # No se usa en este demo, pero estaba en el código anterior, lo quitamos.
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
                             QTextEdit, QMessageBox, QHBoxLayout, QMainWindow, QAction,
                             QFileDialog, QMenuBar, QMenu) # Quitamos QScrollArea, QGridLayout, QDialog si no se usan
from PyQt5.QtCore import Qt, QSize
import os
import traceback
import logging
# Importaciones específicas de cryptography
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
# No necesitamos load_pem_private_key/public_key aquí ya que cargamos desde PEM en bytes directamente

# Configuración de Logging (opcional, pero útil para depuración)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Rutas de los archivos de clave (usamos la ruta relativa al script)
# NOTA: Guardar claves privadas en archivos sin encriptación es MUY INSEGURO
# En un programa real, NUNCA se guardaría la clave privada así.
# Esto es solo para el demo educativo.
KEY_DIR = os.path.join(os.path.dirname(__file__), "keys_demo")
PRIVATE_KEY_FILE = os.path.join(KEY_DIR, "private_key_demo.pem")
PUBLIC_KEY_FILE = os.path.join(KEY_DIR, "public_key_demo.pem")

# --- Funciones Criptográficas Básicas (con nombres cortos para 'ofuscación') ---

# Generar Par de Claves
def gp_c(): # generar_par_claves
    """Genera un par de claves privada y pública RSA y las guarda en archivos."""
    logging.info("[*] Generando par de claves...")
    try:
        pk = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        pubk = pk.public_key()

        private_pem = pk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption() # SIN ENCRIPTACIÓN (solo para demo)
        )

        public_pem = pubk.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Asegurar que el directorio de claves existe
        os.makedirs(KEY_DIR, exist_ok=True)

        # Guardar en archivos
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_pem)
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_pem)

        logging.info("[+] Par de claves generado y guardado.")
        return private_pem.decode('utf-8'), public_pem.decode('utf-8') # Retornar como strings

    except Exception as e:
        logging.error(f"[!] ERROR al generar claves: {e}")
        QMessageBox.critical(None, "Error de Criptografía", f"No se pudieron generar las claves:\n{e}")
        return None, None

# Cargar Clave Privada (desde archivo PEM)
def c_pk(): # cargar_clave_privada
    """Carga la clave privada desde el archivo PEM."""
    try:
        with open(PRIVATE_KEY_FILE, "rb") as kf:
            pk = serialization.load_pem_private_key(
                kf.read(),
                password=None # No hay contraseña en este demo
            )
        return pk
    except FileNotFoundError:
        logging.warning(f"[!] Archivo de clave privada no encontrado: {PRIVATE_KEY_FILE}")
        # No mostramos QMessageBox aquí, la ventana principal lo manejará si es necesario
        return None
    except Exception as e:
        logging.error(f"[!] ERROR al cargar clave privada: {e}")
        QMessageBox.critical(None, "Error de Criptografía", f"No se pudo cargar la clave privada:\n{e}")
        return None

# Cargar Clave Pública (desde archivo PEM)
def c_pubk(): # cargar_clave_publica
    """Carga la clave pública desde el archivo PEM."""
    try:
        with open(PUBLIC_KEY_FILE, "rb") as kf:
            pubk = serialization.load_pem_public_key(kf.read())
        return pubk
    except FileNotFoundError:
         logging.warning(f"[!] Archivo de clave pública no encontrado: {PUBLIC_KEY_FILE}")
         # No mostramos QMessageBox aquí
         return None
    except Exception as e:
        logging.error(f"[!] ERROR al cargar clave pública: {e}")
        QMessageBox.critical(None, "Error de Criptografía", f"No se pudo cargar la clave pública:\n{e}")
        return None

# Simular Mensaje (string a bytes)
def s_m(m_str): # simular_mensaje
    """Convierte un string a bytes."""
    return m_str.encode('utf-8')

# Firmar Mensaje
def f_m(pk, m_bytes): # firmar_mensaje
    """Firma un mensaje en bytes usando un objeto clave privada."""
    logging.info("[*] Firmando mensaje con la clave PRIVADA...")
    try:
        sig = pk.sign(
            m_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        logging.info("[+] Mensaje firmado exitosamente.")
        return sig # La firma es en bytes

    except Exception as e:
        logging.error(f"[!] ERROR al firmar el mensaje: {e}")
        QMessageBox.critical(None, "Error de Criptografía", f"No se pudo firmar el mensaje:\n{e}")
        return None

# Verificar Firma
def v_f(pubk, m_bytes, sig_bytes): # verificar_firma
    """Verifica una firma usando un objeto clave pública y el mensaje original."""
    logging.info("[*] Verificando firma con la clave PÚBLICA...")
    try:
        pubk.verify(
            sig_bytes,
            m_bytes, # ¡Debe ser el mensaje ORIGINAL exacto!
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        logging.info("[+] ¡VERIFICACIÓN EXITOSA! La firma es válida.")
        return True # La verificación fue exitosa

    except InvalidSignature:
        logging.warning("[!] ¡VERIFICACIÓN FALLIDA! La firma NO es válida para este mensaje y clave pública.")
        return False # La firma no coincide

    except Exception as e:
        logging.error(f"[!] ERROR durante la verificación: {e}")
        QMessageBox.critical(None, "Error de Criptografía", f"Error durante la verificación:\n{e}")
        return False

# --- Clase Principal de la Ventana PyQt5 ---

class KeyDemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo Claves Pública/Privada")
        self.setGeometry(100, 100, 600, 500)

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
        self.private_key_pem = None
        self.public_key_pem = None
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

        show_keys_dir_action = QAction('Mostrar Ubicación de Claves', self)
        show_keys_dir_action.triggered.connect(self.show_keys_directory)
        file_menu.addAction(show_keys_dir_action)

        exit_action = QAction('&Salir', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def show_explanation(self):
        """Muestra la explicación inicial y resetea el estado."""
        self.output_text.clear()
        explanation = """======================================================
      DEMO EDUCATIVA: Claves Pública y Privada
======================================================

Imagina tu wallet de criptomoneda como una caja fuerte.
Necesitas dos tipos de llaves:

1.  LA LLAVE PRIVADA (Private Key):
    - Es SECRETA. ¡Debes guardarla muy bien!
    - La usas para 'abrir' la caja fuerte, es decir, para firmar
      transacciones y poder gastar tus criptomonedas.
    - Es tu prueba de que eres el dueño de los fondos.

2.  LA LLAVE PÚBLICA (Public Key):
    - NO es secreta. ¡Puedes compartirla libremente!
    - Se deriva de la clave privada, pero NO puedes obtener la
      clave privada a partir de la pública.
    - La usas para que otros te envíen criptomonedas (a menudo
      se convierte en una 'dirección' más corta y legible).
    - Sirve para que otros verifiquen que una transacción firmada
      con la clave privada correspondiente es auténtica.

En este demo, simularemos:
1. Generar un par de claves.
2. Firmar un 'mensaje' (como una transacción) con la clave PRIVADA.
3. Verificar esa firma con la clave PÚBLICA (debería funcionar).
4. Intentar verificar con un mensaje ALTERADO (debería fallar).
5. Intentar verificar con una clave PÚBLICA INCORRECTA (debería fallar).

"""
        self.output_text.append(explanation)
        self.current_step = 0
        self.private_key_pem = None
        self.public_key_pem = None
        self.mensaje_original_bytes = None
        self.firma_bytes = None
        self.start_button.setEnabled(True)
        self.next_button.setEnabled(False)


    def start_demo(self):
        """Inicia el primer paso de la demo."""
        self.output_text.clear() # Limpiar la explicación al iniciar
        self.output_text.append("--- COMENZANDO DEMOSTRACIÓN ---")
        self.start_button.setEnabled(False)
        self.next_button.setEnabled(True)
        self.advance_demo_step() # Ir directamente al primer paso

    def advance_demo_step(self):
        """Avanza al siguiente paso de la demo."""
        self.current_step += 1
        self.output_text.append(f"\n--- PASO {self.current_step} ---")

        if self.current_step == 1:
            # Paso 1: Generar Claves
            private_pem, public_pem = gp_c()
            if private_pem and public_pem:
                self.private_key_pem = private_pem
                self.public_key_pem = public_pem

                self.output_text.append("\nTu Clave PRIVADA (SECRETA):")
                self.output_text.append(private_pem)
                self.output_text.append("\n==============================================================")
                self.output_text.append("!!! GUARDA ESTO MUY SEGURO. PERDERLA = PERDER TUS FONDOS. !!!")
                self.output_text.append("!!! NUNCA LA COMPARTAS.                             !!!")
                self.output_text.append("==============================================================")

                self.output_text.append("\nTu Clave PÚBLICA (para compartir):")
                self.output_text.append(public_pem)
                self.output_text.append("\nPuedes compartir esto con cualquiera que quiera enviarte criptomonedas.")

                # Simulación de dirección de wallet
                direccion_base = hashlib.sha256(public_pem.encode('utf-8')).hexdigest()
                self.direccion_corta = direccion_base[:40] # Guardamos la dirección
                self.output_text.append(f"\nSimulación de tu Dirección de Wallet (derivada de la pública):")
                self.output_text.append(self.direccion_corta)
                self.output_text.append("==============================================================")
                self.output_text.append("Comparte esta dirección corta para recibir fondos.")
                self.output_text.append("==============================================================")
                QMessageBox.information(self, "Paso 1 Completo", "Claves generadas y mostradas.")
            else:
                 self.output_text.append("[!] Falló la generación de claves.")
                 self.next_button.setEnabled(False) # Deshabilitar siguiente paso si falla
                 QMessageBox.critical(self, "Error", "Falló la generación de claves.")


        elif self.current_step == 2:
            # Paso 2: Preparar Mensaje a Firmar
            if not self.direccion_corta:
                 self.output_text.append("[!] Error: No se generó una dirección.")
                 self.next_button.setEnabled(False)
                 return

            mensaje_original_str = f"Enviar 10 monedas a la dirección {self.direccion_corta}. Fecha: {datetime.datetime.now().isoformat()}"
            self.mensaje_original_bytes = s_m(mensaje_original_str)
            self.output_text.append(f"\nMensaje a firmar: '{mensaje_original_str}'")
            self.output_text.append("Este mensaje representa los detalles de la acción que quieres autorizar (gastar fondos).")
            QMessageBox.information(self, "Paso 2 Completo", "Mensaje de transacción preparado.")

        elif self.current_step == 3:
             # Paso 3: Firmar Mensaje con Clave Privada
            pk_obj = c_pk() # Cargar la clave privada desde el archivo
            if pk_obj and self.mensaje_original_bytes:
                self.firma_bytes = f_m(pk_obj, self.mensaje_original_bytes)
                if self.firma_bytes:
                    self.output_text.append("\nFirma Digital generada:")
                    self.output_text.append(self.firma_bytes.hex())
                    self.output_text.append("\nEsta firma prueba que tú (el dueño de la clave privada) autorizaste este mensaje específico.")
                    QMessageBox.information(self, "Paso 3 Completo", "Mensaje firmado con clave privada.")
                else:
                    self.output_text.append("[!] Falló la firma del mensaje.")
                    self.next_button.setEnabled(False)
                    QMessageBox.critical(self, "Error", "Falló la firma del mensaje.")
            else:
                self.output_text.append("[!] Error: Clave privada o mensaje no disponibles para firmar.")
                self.next_button.setEnabled(False)
                QMessageBox.critical(self, "Error", "Error al preparar para firmar.")


        elif self.current_step == 4:
             # Paso 4: Verificar Firma (Correctamente)
            pubk_obj = c_pubk() # Cargar la clave pública desde el archivo
            if pubk_obj and self.mensaje_original_bytes and self.firma_bytes:
                self.output_text.append("\nVerificando la Firma (con la Clave PÚBLICA Correcta)...")
                self.output_text.append("Cualquiera que tenga el mensaje original, la firma y tu clave pública puede hacer esto.")
                verificacion_exitosa = v_f(pubk_obj, self.mensaje_original_bytes, self.firma_bytes)

                if verificacion_exitosa:
                    self.output_text.append("\nLa verificación tuvo éxito. Esto significa que la firma fue creada por el dueño de la clave privada correspondiente a esta clave pública, y el mensaje no fue alterado.")
                    QMessageBox.information(self, "Paso 4 Completo", "Verificación correcta exitosa.")
                else:
                    self.output_text.append("\nLa verificación falló (inesperado si el mensaje y la clave son correctos).")
                    self.next_button.setEnabled(False)
                    QMessageBox.critical(self, "Error", "La verificación correcta falló (¡Problema en el código!).")
            else:
                self.output_text.append("[!] Error: Clave pública, mensaje o firma no disponibles para verificar.")
                self.next_button.setEnabled(False)
                QMessageBox.critical(self, "Error", "Error al preparar para verificar.")


        elif self.current_step == 5:
             # Paso 5: Demostración de Verificación Fallida (Mensaje Alterado)
            if not self.firma_bytes or not self.public_key_pem:
                 self.output_text.append("[!] Error: Firma o clave pública no disponibles.")
                 self.next_button.setEnabled(False)
                 return

            mensaje_alterado_str = f"Enviar 10000 monedas a la dirección {self.direccion_corta}. Fecha: {datetime.datetime.now().isoformat()} - ALTERADO" # Cambiamos el monto y añadimos texto
            mensaje_alterado_bytes = s_m(mensaje_alterado_str)
            self.output_text.append("\nIntentar Verificar con un Mensaje ALTERADO...")
            self.output_text.append(f"Mensaje Alterado: '{mensaje_alterado_str}'")
            self.output_text.append("Usando la firma ORIGINAL pero con el mensaje ALTERADO.")

            pubk_obj = c_pubk() # Cargar la clave pública de nuevo
            if pubk_obj:
                verificacion_fallida_mensaje = v_f(pubk_obj, mensaje_alterado_bytes, self.firma_bytes)

                if not verificacion_fallida_mensaje:
                    self.output_text.append("\nLa verificación falló, como se esperaba. Esto demuestra que cualquier pequeño cambio en el mensaje invalida la firma.")
                    QMessageBox.information(self, "Paso 5 Completo", "Verificación con mensaje alterado falló (correcto).")
                else:
                    self.output_text.append("\n¡ALERTA! La verificación tuvo éxito con un mensaje alterado. Esto indica un problema.")
                    self.next_button.setEnabled(False)
                    QMessageBox.critical(self, "Error", "La verificación con mensaje alterado tuvo éxito (¡Problema en el código!).")
            else:
                self.output_text.append("[!] Error: Clave pública no disponible para verificación.")
                self.next_button.setEnabled(False)
                QMessageBox.critical(self, "Error", "Error al preparar para verificar (mensaje alterado).")

        elif self.current_step == 6:
             # Paso 6: Demostración de Verificación Fallida (Clave Pública Incorrecta)
            if not self.firma_bytes or not self.mensaje_original_bytes:
                 self.output_text.append("[!] Error: Firma o mensaje original no disponibles.")
                 self.next_button.setEnabled(False)
                 return

            self.output_text.append("\nIntentar Verificar con una Clave PÚBLICA INCORRECTA...")
            self.output_text.append("Generando un par de claves COMPLETAMENTE NUEVO para obtener una clave pública diferente...")

            try:
                # Generamos un nuevo par solo para obtener una clave pública diferente.
                private_key_otra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                public_key_otra = private_key_otra.public_key()
                # No necesitamos serializarla para este paso, solo el objeto clave.

                self.output_text.append("[+] Clave pública incorrecta generada.")
                self.output_text.append("\nUsando la firma ORIGINAL, el mensaje ORIGINAL, pero una clave PÚBLICA DIFERENTE.")
                verificacion_fallida_clave = v_f(public_key_otra, self.mensaje_original_bytes, self.firma_bytes)

                if not verificacion_fallida_clave:
                    self.output_text.append("\nLa verificación falló, como se esperaba. Esto demuestra que solo la clave pública que corresponde al par original puede verificar la firma.")
                    QMessageBox.information(self, "Paso 6 Completo", "Verificación con clave incorrecta falló (correcto).")
                else:
                    self.output_text.append("\n¡ALERTA! La verificación tuvo éxito con una clave pública incorrecta. Esto indica un problema.")
                    self.next_button.setEnabled(False)
                    QMessageBox.critical(self, "Error", "La verificación con clave incorrecta tuvo éxito (¡Problema en el código!).")

            except Exception as e:
                 self.output_text.append(f"[!] ERROR al generar clave incorrecta para la demostración: {e}")
                 QMessageBox.critical(self, "Error", f"Error al generar clave incorrecta para la demostración:\n{e}")
                 self.next_button.setEnabled(False)


        elif self.current_step > 6:
            # Fin de la demo
            self.output_text.append("\n======================================================")
            self.output_text.append("             FIN DE LA DEMOSTRACIÓN                  ")
            self.output_text.append("======================================================")
            self.output_text.append("Recuerda:")
            self.output_text.append("  - Tu Clave PRIVADA es tu control de los fondos (¡Mantenla secreta!).")
            self.output_text.append("  - Tu Clave PÚBLICA (o tu dirección derivada de ella) es para que te envíen fondos (¡Comparte!).")
            self.output_text.append("  - La firma digital conecta un mensaje específico con el dueño de la clave privada.")
            self.output_text.append("======================================================")
            self.next_button.setEnabled(False) # Deshabilitar el botón "Siguiente Paso"
            QMessageBox.information(self, "Demo Finalizada", "La demostración ha concluido.")

    def restart_demo(self):
        """Reinicia la demostración."""
        logging.info("[*] Reiniciando demostración...")
        self.show_explanation() # Mostrar la explicación de nuevo
        self.output_text.append("--- DEMOSTRACIÓN REINICIADA ---")
        QMessageBox.information(self, "Demo Reiniciada", "La demostración se ha reiniciado. Presiona 'Comenzar Demo' para empezar de nuevo.")

    def show_keys_directory(self):
        """Abre el directorio donde se guardan las claves."""
        logging.info(f"[*] Intentando abrir directorio de claves: {KEY_DIR}")
        if not os.path.exists(KEY_DIR):
             os.makedirs(KEY_DIR, exist_ok=True) # Asegurar que existe
             QMessageBox.warning(self, "Directorio no Encontrado", f"El directorio de claves no existía, se ha creado:\n{KEY_DIR}\n\nLas claves se generarán al iniciar la demo.")
             return

        # Verificar si los archivos existen
        if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
             reply = QMessageBox.question(self, "Archivos de Clave No Encontrados",
                                         f"Los archivos de clave no se encontraron en:\n{KEY_DIR}\n\n"
                                         "¿Deseas generar un nuevo par de claves ahora?\n"
                                         "(Nota: Esto sobrescribirá cualquier clave existente)",
                                         QMessageBox.Yes | QMessageBox.No)
             if reply == QMessageBox.Yes:
                 self.gen_keys_and_show() # Generar y luego intentar mostrar el directorio
                 return # Salir después de intentar generar

        try:
            # Abrir el directorio en el explorador de archivos del sistema operativo
            if sys.platform == "win32":
                os.startfile(KEY_DIR)
            elif sys.platform == "darwin": # macOS
                os.system(f'open "{KEY_DIR}"')
            else: # linux variants
                os.system(f'xdg-open "{KEY_DIR}"')
            logging.info(f"[+] Directorio abierto exitosamente: {KEY_DIR}")
        except Exception as e:
            logging.error(f"[!] ERROR al abrir directorio: {e}")
            QMessageBox.critical(self, "Error al abrir directorio", f"No se pudo abrir el directorio:\n{KEY_DIR}\n\nError: {e}")

    def gen_keys_and_show(self):
        """Genera claves y luego muestra la ubicación."""
        private_pem, public_pem = gp_c()
        if private_pem and public_pem:
             self.private_key_pem = private_pem
             self.public_key_pem = public_pem
             QMessageBox.information(self, "Claves Generadas", "Un nuevo par de claves se ha generado y guardado.")
             self.show_keys_directory() # Ahora intenta mostrar el directorio
        else:
             QMessageBox.warning(self, "Generación Fallida", "La generación de claves falló.")


# --- Función Principal para Ejecutar la Aplicación ---
def main(args):
    # args contendrá los argumentos de la línea de comandos si se pasan
    # print("Argumentos recibidos:", args) # Puedes usar esto para depurar argumentos si los necesitas

    app = QApplication(sys.argv) # sys.argv permite que Qt procese argumentos estándar de línea de comandos

    window = KeyDemoWindow()
    # No necesitamos setGeometry o showMaximized si queremos un tamaño inicial manejable
    # Puedes descomentar si prefieres iniciar maximizado:
    # window.setGeometry(0, 0, 800, 600)
    # window.showMaximized()
    window.show()

    sys.exit(app.exec_()) # Ejecutar el bucle de eventos principal

if __name__ == "__main__":
    # Pasamos sys.argv[1:] a main si quieres procesar argumentos
    # Si solo necesitas que Qt procese sys.argv, puedes llamar a main() directamente.
    # Aquí, pasamos sys.argv para que la función main tenga acceso si se necesita en el futuro.
    main(sys.argv)
