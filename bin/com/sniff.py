from scapy.all import *
import signal


print('Creado módulo-comando sniff y fecha y hora: 2023-10-02 12:00:26.017185')

ctrl_c = False

def stop_filter(packet):
    global ctrl_c
    return ctrl_c

def main(args):
    global ctrl_c
    ctrl_c = False
#    signal.signal(signal.SIGINT,ch_sign)
    print('Args dentro de sniff', args)

    # Verificar si hay argumentos
    if len(args) < 1:
        print("Requiere un argumento ")
        # se sale
        return

    if args[0] == "--interfaces":
        # Obtener interfaces de red disponibles
        interfaces = ifaces
        if not interfaces:
            print("No hay interfaces de red disponibles")
            return

        print("Interfaces disponibles:")
        for iface, details in interfaces.items():
            print(f"Nombre: {iface}, Descripción: {details.description}")
        return

    iface = args[0] 


    if len(args) == 2 and args[1] == "--guardian":
        try:
            try:
                alert_on_suspicious_activity(iface)
                return
            except Exception as e:
                print("Error:",e)
                return
        except Exception as e:
            print("Error leyendo guardian:",e)
            return


    print(f"Monitoreando la red en la interfaz {iface}...\n")
    try:
        sniff(iface=iface, prn=packet_handler, stop_filter = stop_filter)
        return
    except Exception as e:
        print("Exit sniff")
        return



def packet_handler(packet):

    if packet.haslayer(IP):
        ip_packet = packet[IP]
        print(f"IP Source: {ip_packet.src}, IP Destination: {ip_packet.dst}")

        if packet.haslayer(TCP):
            tcp_packet = packet[TCP]
            print(f"TCP Source Port: {tcp_packet.sport}, TCP Destination Port: {tcp_packet.dport}")
            print("TCP Headers:")
            print(tcp_packet.show())
            print("\n" + "=" * 50 + "\n")




def ch_sign(signal,frame):
    global ctrl_c
    ctrl_c = True
#    signal.signal(signal.SIGINT,signal.SIG_DFL)
    return








def alert_on_suspicious_activity(iface):

    print("Detectando actividad sospechosa en:",iface)
    print("En obras")












if __name__ == "__main__":
    main(sys.argv[1:])
