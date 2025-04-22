# Asegúrate de tener la biblioteca cryptography instalada:
# pip install cryptography
import datetime
import sys
import hashlib # Lo usaremos para simular una "dirección" corta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import os

# --- Parte 1: Explicación Teórica (para el usuario al inicio) ---
def explicar_claves():
    print("======================================================")
    print("      DEMO EDUCATIVA: Claves Pública y Privada        ")
    print("======================================================")
    print("\nImagina tu wallet de criptomoneda como una caja fuerte.")
    print("Necesitas dos tipos de llaves:")
    print("\n1.  LA LLAVE PRIVADA (Private Key):")
    print("    - Es SECRETA. ¡Debes guardarla muy bien!")
    print("    - La usas para 'abrir' la caja fuerte, es decir, para firmar")
    print("      transacciones y poder gastar tus criptomonedas.")
    print("    - Es tu prueba de que eres el dueño de los fondos.")

    print("\n2.  LA LLAVE PÚBLICA (Public Key):")
    print("    - NO es secreta. ¡Puedes compartirla libremente!")
    print("    - Se deriva de la clave privada, pero NO puedes obtener la")
    print("      clave privada a partir de la pública.")
    print("    - La usas para que otros te envíen criptomonedas (a menudo")
    print("      se convierte en una 'dirección' más corta y legible).")
    print("    - Sirve para que otros verifiquen que una transacción firmada")
    print("      con la clave privada correspondiente es auténtica.")

    print("\nEn este demo, simularemos:")
    print("1. Generar un par de claves.")
    print("2. Firmar un 'mensaje' (como una transacción) con la clave PRIVADA.")
    print("3. Verificar esa firma con la clave PÚBLICA (debería funcionar).")
    print("4. Intentar verificar con un mensaje ALTERADO (debería fallar).")
    print("5. Intentar verificar con una clave PÚBLICA INCORRECTA (debería fallar).")
    print("======================================================")
    input("Presiona Enter para comenzar la demostración...")

# --- Parte 2: Funciones Criptográficas ---

def generar_par_claves():
    """Genera un par de claves privada y pública RSA."""
    print("\n[*] Generando par de claves...")
    # Usamos RSA para la demostración, aunque las criptomonedas suelen usar ECDSA
    # Key size 2048 es razonable para demostración
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    # Serializar (convertir a formato estándar) para poder mostrar y guardar
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption() # Sin encriptación para simplificar, ¡NO HACER EN PRODUCCIÓN REAL!
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    print("[+] Par de claves generado.")
    return private_pem, public_pem # Retornamos las claves serializadas para mostrarlas

def simular_mensaje(mensaje_str):
    """Convierte un string a bytes (necesario para criptografía)."""
    return mensaje_str.encode('utf-8')

def firmar_mensaje(private_key_pem, mensaje_bytes):
    """Firma un mensaje en bytes usando la clave privada PEM."""
    print("[*] Firmando mensaje con la clave PRIVADA...")
    try:
        # Cargar la clave privada desde el formato PEM
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None # No hay contraseña en este demo
        )

        # Firmar el mensaje
        signature = private_key.sign(
            mensaje_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH # Usamos el máximo salt length recomendado
            ),
            hashes.SHA256() # Usamos SHA256 para el hashing
        )
        print("[+] Mensaje firmado exitosamente.")
        return signature # La firma también es en bytes

    except Exception as e:
        print(f"[!] ERROR al firmar el mensaje: {e}")
        return None

def verificar_firma(public_key_pem, mensaje_bytes, signature_bytes):
    """Verifica una firma usando la clave pública PEM y el mensaje original."""
    print("[*] Verificando firma con la clave PÚBLICA...")
    try:
        # Cargar la clave pública desde el formato PEM
        public_key = serialization.load_pem_public_key(public_key_pem)

        # Verificar la firma
        public_key.verify(
            signature_bytes,
            mensaje_bytes, # ¡Debe ser el mensaje ORIGINAL exacto!
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print("[+] ¡VERIFICACIÓN EXITOSA! La firma es válida.")
        return True # La verificación fue exitosa

    except InvalidSignature:
        print("[!] ¡VERIFICACIÓN FALLIDA! La firma NO es válida para este mensaje y clave pública.")
        return False # La firma no coincide

    except Exception as e:
        print(f"[!] ERROR durante la verificación: {e}")
        return False

# --- Parte 3: Flujo de la Demostración ---

def ejecutar_demo():
    explicar_claves()

    # --- Paso 1: Generar Claves ---
    print("\n--- PASO 1: Generación de Claves ---")
    private_pem, public_pem = generar_par_claves()

    print("\nTu Clave PRIVADA (SECRETA):")
    print(private_pem.decode('utf-8')) # Decodificar para imprimir como texto legible
    print("\n==============================================================")
    print("!!! GUARDA ESTO MUY SEGURO. PERDERLA = PERDER TUS FONDOS. !!!")
    print("!!! NUNCA LA COMPARTAS.                             !!!")
    print("==============================================================")

    print("\nTu Clave PÚBLICA (para compartir):")
    print(public_pem.decode('utf-8'))
    print("\nPuedes compartir esto con cualquiera que quiera enviarte criptomonedas.")

    # Simulación de dirección de wallet
    # Una dirección real de Bitcoin/Ethereum es más compleja, pero esto da la idea.
    direccion_base = hashlib.sha256(public_pem).hexdigest()
    direccion_corta = direccion_base[:40] # Tomamos los primeros 40 caracteres como "dirección"
    print(f"\nSimulación de tu Dirección de Wallet (derivada de la pública):")
    print(direccion_corta)
    print("==============================================================")
    print("Comparte esta dirección corta para recibir fondos.")
    print("==============================================================")


    input("\nPresiona Enter para simular la firma de una transacción...")

    # --- Paso 2: Simular Mensaje a Firmar ---
    print("\n--- PASO 2: Preparar Mensaje para Firmar (como una Transacción) ---")
    mensaje_original_str = f"Enviar 10 monedas a la dirección {direccion_corta}. Fecha: {datetime.datetime.now().isoformat()}"
    mensaje_original_bytes = simular_mensaje(mensaje_original_str)
    print(f"\nMensaje a firmar: '{mensaje_original_str}'")
    print("Este mensaje representa los detalles de la acción que quieres autorizar (gastar fondos).")
    input("Presiona Enter para firmar el mensaje con tu clave privada...")

    # --- Paso 3: Firmar Mensaje ---
    print("\n--- PASO 3: Firmar el Mensaje con la Clave PRIVADA ---")
    # Solo tú, con tu clave privada, puedes hacer esto de forma válida.
    firma_bytes = firmar_mensaje(private_pem, mensaje_original_bytes)

    if firma_bytes:
        print("\nFirma Digital generada:")
        print(firma_bytes.hex()) # Mostrar la firma en formato hexadecimal para que sea legible
        print("\nEsta firma prueba que tú (el dueño de la clave privada) autorizaste este mensaje específico.")
    else:
        print("\nLa firma falló. Terminando demostración.")
        sys.exit(1) # Salir si no se pudo firmar

    input("\nPresiona Enter para verificar la firma con la clave pública...")

    # --- Paso 4: Verificar Firma (Correctamente) ---
    print("\n--- PASO 4: Verificar la Firma con la Clave PÚBLICA Correcta ---")
    print("Cualquiera que tenga el mensaje original, la firma y tu clave pública puede hacer esto.")
    verificacion_exitosa = verificar_firma(public_pem, mensaje_original_bytes, firma_bytes)

    if verificacion_exitosa:
        print("\nLa verificación tuvo éxito. Esto significa que la firma fue creada por el dueño de la clave privada correspondiente a esta clave pública, y el mensaje no fue alterado.")
    else:
         print("\nLa verificación falló (inesperado si el mensaje y la clave son correctos). Terminando demostración.")
         sys.exit(1)


    input("\nPresiona Enter para ver qué pasa si el mensaje cambia...")

    # --- Paso 5: Demostración de Verificación Fallida (Mensaje Alterado) ---
    print("\n--- PASO 5: Intentar Verificar con un Mensaje ALTERADO ---")
    mensaje_alterado_str = f"Enviar 10000 monedas a la dirección {direccion_corta}. Fecha: {datetime.datetime.now().isoformat()}" # Cambiamos el monto drasticamente
    mensaje_alterado_bytes = simular_mensaje(mensaje_alterado_str)
    print(f"\nMensaje Alterado: '{mensaje_alterado_str}'")
    print("\nUsando la firma ORIGINAL pero con el mensaje ALTERADO.")

    verificacion_fallida_mensaje = verificar_firma(public_pem, mensaje_alterado_bytes, firma_bytes)

    if not verificacion_fallida_mensaje:
        print("\nLa verificación falló, como se esperaba. Esto demuestra que cualquier pequeño cambio en el mensaje invalida la firma.")
    else:
        print("\n¡ALERTA! La verificación tuvo éxito con un mensaje alterado. Esto indica un problema.") # Esto no debería pasar con criptografía correcta

    input("\nPresiona Enter para ver qué pasa si la clave pública es incorrecta...")

    # --- Paso 6: Demostración de Verificación Fallida (Clave Pública Incorrecta) ---
    print("\n--- PASO 6: Intentar Verificar con una Clave PÚBLICA INCORRECTA ---")
    print("Generando un par de claves COMPLETAMENTE NUEVO para obtener una clave pública diferente...")
    # Generamos un nuevo par solo para obtener una clave pública diferente.
    try:
        private_key_otra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key_otra = private_key_otra.public_key()
        public_pem_otra = public_key_otra.public_bytes(
             encoding=serialization.Encoding.PEM,
             format=serialization.PublicFormat.SubjectPublicKeyInfo
         )
        print("[+] Clave pública incorrecta generada.")
        print("\nUsando la firma ORIGINAL, el mensaje ORIGINAL, pero una clave PÚBLICA DIFERENTE.")
        verificacion_fallida_clave = verificar_firma(public_pem_otra, mensaje_original_bytes, firma_bytes)

        if not verificacion_fallida_clave:
            print("\nLa verificación falló, como se esperaba. Esto demuestra que solo la clave pública que corresponde al par original puede verificar la firma.")
        else:
            print("\n¡ALERTA! La verificación tuvo éxito con una clave pública incorrecta. Esto indica un problema.") # Esto no debería pasar

    except Exception as e:
         print(f"[!] ERROR al generar clave incorrecta para la demostración: {e}")


    print("\n======================================================")
    print("             FIN DE LA DEMOSTRACIÓN                  ")
    print("======================================================")
    print("Recuerda:")
    print("  - Tu Clave PRIVADA es tu control de los fondos (¡Mantenla secreta!).")
    print("  - Tu Clave PÚBLICA (o tu dirección derivada de ella) es para que te envíen fondos (¡Comparte!).")
    print("  - La firma digital conecta un mensaje específico con el dueño de la clave privada.")
    print("======================================================")

# --- Ejecutar el programa ---
def main(args):
    print(args,"\nExecuting Demo\n")
    ejecutar_demo()
main("EXEC DEMO")   
