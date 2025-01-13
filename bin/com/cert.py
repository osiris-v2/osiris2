

import datetime
import subprocess
import os




def main(args):
#    print('Args dentro de {module_name}', args)


    if args[0] == "new":
    	print("New Cert")

    # Solicitar los nombres de dominio
    print("Introduzca los nombres de dominio para el certificado (separados por comas):")
    domains = input().split(",")

    # Solicitar el tamaño de la clave RSA
    while True:
        try:
            key_size = int(input("Introduzca el tamaño de la clave RSA (por defecto 2048): ") or 2048)
            if key_size <= 0:
                raise ValueError
            break
        except ValueError:
            print("El tamaño de la clave debe ser un número entero positivo.")

    # Solicitar el nombre del archivo de la clave RSA (opcional)
    key_file = None
    while True:
        key_file = input("Introduzca el nombre del archivo de la clave RSA (o pulse Enter para generar una nueva): ")
        if not key_file or os.path.exists(key_file):
            break
        print(f"El archivo '{key_file}' no existe.")

    # Solicitar el nombre del archivo del certificado (opcional)
    cert_file = None
    while True:
        cert_file = input("Introduzca el nombre del archivo del certificado (o pulse Enter para usar 'cert.pem'): ") or "cert.pem"
        if os.path.exists(cert_file):
            print(f"El archivo '{cert_file}' ya existe. ¿Desea sobrescribirlo? (s/n)")
            answer = input().lower()
            if answer not in ("s", "si"):
                continue
        break

    # Generar el certificado
    create_cert(domains, key_size, key_file, cert_file)

if __name__ == '__main__':
    main()





















print('Creado módulo-comando cert y fecha y hora: 2024-03-22 09:09:52.670395')
