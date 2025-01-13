import socket
import dns.resolver
import nmap
import time
import sys
import requests
import json
import signal
import subprocess

print('Creado módulo-comando scanip y fecha y hora: 2023-10-02 15:48:20.085867')



def detectar_servicio_desconocido(ip, puerto):
    protocolos = {
        'http': {
            'solicitud': b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n',
            'respuesta': b'HTTP/1.1',
        },
        'ssh': {
            'solicitud': b'SSH-2.0-OpenSSH_7.9p1 Debian-10+deb10u2\r\n',
            'respuesta': b'SSH',
        },
        # Agrega más protocolos aquí si es necesario
    }

    for protocolo, datos in protocolos.items():
        solicitud = datos['solicitud']
        respuesta_esperada = datos['respuesta']
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                sock.connect((ip, puerto))
                sock.sendall(solicitud)
                respuesta = sock.recv(1024)
                if respuesta and respuesta_esperada in respuesta:
                    return protocolo
        except (socket.timeout, socket.error):
            continue

    return 'Desconocido'


def resolve_ip_or_domain(input_str):
    try:
        # Intenta resolver el input como dominio
        answers = dns.resolver.resolve(input_str, 'A')
        ip = answers[0].address
        return ip
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        # Si no se puede resolver como dominio, asume que es una IP
        return input_str

def check_port(ip, puerto):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            resultado = sock.connect_ex((ip, puerto))
            
            if resultado == 0:
                return True
            else:
                return False
    except (socket.timeout, socket.error):
        return False

def get_service_info(ip, puerto):
    try:
        servicio = socket.getservbyport(puerto)
        return servicio
    except (OSError, socket.error):
        try:
            scanner = nmap.PortScanner()
            scanner.scan(ip, f"{puerto}")
            service = scanner[ip]['tcp'][puerto]['name']
            return service
        except nmap.PortScannerError:
            servicio_desconocido = detectar_servicio_desconocido(ip, puerto)
            return servicio_desconocido



def extraer_y_vaciar(array):
    # Creamos un nuevo array vacío para almacenar los valores extraídos
    array_extraido = []

    # Iteramos sobre el array original
    for valor in array:
        # Comprobamos si el valor empieza por --
        if valor.startswith("--"):
            # Añadimos el valor al nuevo array
            array_extraido.append(valor)
            # Eliminamos el valor del array original
            array.pop(array.index(valor))

    # Devolvemos el array extraido
    return array_extraido



def netapp(args):
    try:
        subprocess.Popen(args)
        print(args)
    except Exception as e:
        print("PIPE ERROR :",e)

netapps = ["nmap","telnet"]

def main(args):
    global netmapps

    if args[0] in netapps:
        netapp(args)
        print("--- END APP ---- :",args[0])
        return

    if len(args) == 1:
        print("Scanip: Es necesario más de un parametro")
        return


    try:
        param = extraer_y_vaciar(args)
    except Exception as e:
        print("Error:",e)
        return



    if len(args) == 2 and len(param) == 0:
        try:
            print("scanip:",args[1])
            scan_1(args[0],args[1])
            print("scanip:",args[1])
        except Exception as e:
            print("Error:",e)
            return
    elif len(args) == 1 and param[0] == "--all":
        print("scaneo")
        scan_all(args[0])
        return
    elif len(args) == 1 and param[0] == "--info":
        print("info")
        try:
            info_ip(args[0])
        except Exception as e:
            print("Error:",e)            
            return
        return
    else:
        print("comando inválido")
        return



def scan_1(xip,xpuerto):

    input_str = xip  # Cambia el dominio o la IP aquí


    if xpuerto == "":
        print("Es necesario un puerto")
        return

    try:
        puerto =  int(xpuerto) 
    except ValueError:
        print("El puerto debe de ser un número válido")
        return

    try:
        ip = resolve_ip_or_domain(input_str)
    except Exception as e:
        print("Error:",e)
        return

    if ip is None:
        print(f"No se puede resolver el dominio o la IP {input_str}.")
        return

    if not check_port(ip, puerto):
        print(f"El puerto {puerto} en {ip} está cerrado o no responde.")
        return

    servicio = get_service_info(ip, puerto)
    print(f"El puerto {puerto} en {ip} usa el servicio {servicio}.")


ctrl_c = False



def return_scall(signum,frame):
    global ctrl_c
    print("EXIT Scan All:",signum)
    ctrl_c = True
    return

def scan_all(xip):

    global ctrl_c
    input_str = xip  # Cambia el dominio o la IP aquí

    ip = resolve_ip_or_domain(input_str)
    try:
        signal.signal(signal.SIGINT,return_scall)
    except Exception as e:
        print("ERROR SIGNAL:",e)
        return

    for d in range(0,35635):
        if ctrl_c == True:
            ctrl_c = False
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            break
        i = d
        if not check_port(ip, i):
            print(f"El puerto {i} en {ip} está cerrado o no responde.")
            #sys.stdout.write("clear")
            continue
        servicio = get_service_info(ip, i)
        print("SERVICIO DESCUBIERTO")
        print(f"El puerto {i} en {ip} usa el servicio {servicio}")
        print("\n Pause 3seg\n")
        time.sleep(3)
    #time.sleep(1)


def info_ip(location):

    subprocess.run("whois "+str(location),shell=True)

    url = "https://dns.google.com/resolve?name="+location+"&type=A"

    print("SearchIn:",url)

    response = requests.get(url)

# Verifica el código de estado de la respuesta
    if response.status_code == 200:
    # Convierte la respuesta en un objeto JSON
        json_data = json.loads(response.content)

    # Recorre el objeto JSON con un bucle for in
        for key, value in json_data.items():
        # Imprime la clave y el valor
            print(f"{key}: {value}")
    else:
        print(f"Error al obtener la respuesta: {response.status_code}")


