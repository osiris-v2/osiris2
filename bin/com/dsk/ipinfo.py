import sys
import signal
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QScrollArea
)

class IPInfoWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Herramienta de Información de IP")
        self.setGeometry(100, 100, 500, 300)  # Tamaño inicial de la ventana

        # Crear los widgets
        self.ip_label = QLabel("Ingrese una dirección IP:")
        self.ip_entry = QLineEdit()
        self.search_button = QPushButton("Buscar")

        # Área de información con ScrollArea
        self.info_widget = QWidget()  # Contenedor para el QLabel
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)  # Ajustar texto al ancho
        self.info_layout = QVBoxLayout(self.info_widget)
        self.info_layout.addWidget(self.info_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Permite que el scroll se ajuste al contenido
        self.scroll_area.setWidget(self.info_widget)

        # Añadir los widgets a un layout
        layout = QVBoxLayout()
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_entry)
        layout.addWidget(self.search_button)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        # Conectar señales y slots
        self.search_button.clicked.connect(self.on_search)

    def on_search(self):
        ip_address = self.ip_entry.text()

        if not ip_address:
            QMessageBox.warning(self, "Error", "Por favor, ingrese una dirección IP válida.")
            return

        try:
            # Obtener información en cascada
            info_data = self.get_ip_info(ip_address)
            self.info_label.setText(info_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al obtener información: {e}")

    def get_ip_info(self, ip_address):
        info_data = f"**Información de la dirección IP: {ip_address}**\n\n"

        # 1. Ping
        ping_result = self.run_command(["ping", "-c", "4", ip_address])
        info_data += f"**Ping:**\n{ping_result}\n\n"

        # 2. Traceroute
        traceroute_result = self.run_command(["traceroute", ip_address])
        info_data += f"**Traceroute:**\n{traceroute_result}\n\n"

        # 3. Dig para información DNS
        dig_result = self.run_command(["dig", "+short", ip_address])
        info_data += f"**DNS:**\n{dig_result}\n\n"

        # 4. Whois
        whois_result = self.run_command(["whois", ip_address])
        info_data += f"**Whois:**\n{whois_result}\n\n"

        # 5. Información del router (si es posible)
        # Obtener la dirección MAC del dispositivo objetivo (si el ping fue exitoso)
        if "TTL=" in ping_result:
            mac_address = self.get_mac_address_from_ping(ping_result)
            if mac_address:
                info_data += f"**Dirección MAC:** {mac_address}\n\n"
                router_info = self.get_router_info(mac_address)
                if router_info:
                    info_data += f"**Información del Router:**\n{router_info}\n\n"

        return info_data

    def run_command(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True).stdout
            return result
        except Exception as e:
            return f"Error al ejecutar el comando: {e}\n"

    def get_mac_address_from_ping(self, ping_result):
        # Buscar la dirección MAC en la salida del ping
        lines = ping_result.splitlines()
        for line in lines:
            if "from " in line and " [0x" in line:
                parts = line.split(" ")
                mac_address = parts[2]
                return mac_address.replace("[", "").replace("]", "")
        return None

    def get_router_info(self, mac_address):
        # Buscar la dirección IP del router usando la dirección MAC
        netstat_result = self.run_command(["netstat", "-a"])
        ifconfig_result = self.run_command(["ifconfig"])

        # Buscar la dirección IP en la salida de netstat o ifconfig
        for line in netstat_result.splitlines():
            if mac_address in line:
                parts = line.split(" ")
                ip_address = parts[4]
                return f"Dirección IP: {ip_address}"
        for line in ifconfig_result.splitlines():
            if mac_address in line:
                parts = line.split(" ")
                ip_address = parts[1]
                return f"Dirección IP: {ip_address}"
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IPInfoWindow()
    window.show()
    sys.exit(app.exec_())
