#!/usr/bin/env python3
import sys
import json
import os
import subprocess # Mejor que os.system para lanzar procesos externos
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout,
    QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

class AppLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Osiris App Launcher 🚀")
        self.setGeometry(100, 100, 800, 500) # Tamaño inicial ajustado

        # Layout principal en cuadrícula y alineado a la parte superior izquierda
        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.grid_layout.setContentsMargins(15, 15, 15, 15) # Márgenes alrededor de la cuadrícula
        self.grid_layout.setSpacing(15) # Espacio entre los elementos de la cuadrícula
        self.setLayout(self.grid_layout)

        # Cargar aplicaciones desde JSON y crear botones
        self.load_and_create_buttons()

    def load_and_create_buttons(self):
        # Limpiar widgets existentes si la función se llama varias veces (ej. para refrescar)
        for i in reversed(range(self.grid_layout.count())):
            widget_item = self.grid_layout.itemAt(i)
            if widget_item is not None:
                if widget_item.widget():
                    widget_item.widget().deleteLater()
                elif widget_item.layout():
                    # Eliminar layouts anidados si los hubiera, aunque aquí no se usan directamente
                    self._clear_layout(widget_item.layout())

        cols = 3 # Número deseado de columnas en la cuadrícula
        row = 0
        col = 0

        try:
            # Intentar abrir el archivo de configuración
            if not os.path.exists("aplicaciones.json"):
                QMessageBox.critical(self, "Error", "Archivo 'aplicaciones.json' no encontrado. Asegúrate de que está en el mismo directorio que el script. 📄❌")
                return

            with open("aplicaciones.json", "r", encoding='utf-8') as file:
                applications = json.load(file)

            if not isinstance(applications, list):
                QMessageBox.critical(self, "Error de Formato", "El archivo 'aplicaciones.json' debe contener una lista de objetos. 🚫")
                return

            for app_data in applications:
                try:
                    # Omitir si la aplicación no está habilitada
                    if not app_data.get("enabled", False):
                        continue

                    name = app_data.get("name", "Aplicación desconocida")
                    alias = app_data.get("alias", "")
                    path = app_data.get("path", "")
                    icon_path = app_data.get("icon") # Obtener la ruta del icono directamente
                    # Construir la ruta completa al ejecutable
                    # Si path es vacío, se asume que alias ya es una ruta completa o un comando en el PATH.
                    full_command = os.path.join(path, alias) if path and alias else alias

                    # Crear un QWidget para cada "tarjeta" de aplicación
                    app_card = QWidget()
                    # Estilo CSS para la tarjeta (borde, padding, esquinas redondeadas)
                    app_card.setStyleSheet("""
                        QWidget {
                            border: 1px solid #ddd;
                            border-radius: 8px;
                            background-color: #fcfcfc;
                            padding: 10px;
                        }
                        QWidget:hover {
                            border: 1px solid #aaddff; /* Cambia el color del borde al pasar el ratón */
                            background-color: #f0f8ff; /* Color de fondo al pasar el ratón */
                        }
                    """)
                    
                    app_card_layout = QVBoxLayout(app_card)
                    app_card_layout.setContentsMargins(10, 10, 10, 10) # Padding interno de la tarjeta
                    app_card_layout.setSpacing(8) # Espacio entre elementos dentro de la tarjeta

                    # Sección superior: Icono y Nombre
                    icon_name_layout = QHBoxLayout()
                    icon_label = QLabel()
                    
                    # Cargar icono si existe y es válido
                    if icon_path and os.path.exists(icon_path):
                        pixmap = QPixmap(icon_path)
                        if not pixmap.isNull(): # Verificar si la carga del pixmap fue exitosa
                            icon_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        else:
                            print(f"Advertencia: No se pudo cargar el icono para '{name}' en '{icon_path}'. Archivo corrupto o formato no soportado. 🖼️❌")
                    # Si icon_path es vacío o el archivo no existe, icon_label permanece vacío (cumple "sino ninguno")
                    
                    icon_name_layout.addWidget(icon_label)
                    
                    name_label = QLabel(name)
                    name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
                    icon_name_layout.addWidget(name_label)
                    icon_name_layout.addStretch(1) # Empuja icono y nombre a la izquierda
                    app_card_layout.addLayout(icon_name_layout)

                    # Sección de botones
                    buttons_layout = QHBoxLayout()
                    
                    launch_button = QPushButton("Lanzar 🚀")
                    launch_button.setFixedSize(QSize(90, 32)) # Tamaño fijo para el botón Lanzar
                    launch_button.setToolTip(f"Ejecutar: {full_command}")
                    # Conectar el botón a la función de lanzamiento con el comando completo
                    launch_button.clicked.connect(lambda _, cmd=full_command, app_name=name: self.launch_application(cmd, app_name))
                    launch_button.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50; /* Verde */
                            color: white;
                            border: none;
                            border-radius: 5px;
                            padding: 8px 12px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                    """)
                    buttons_layout.addWidget(launch_button)

                    info_button = QPushButton("Info ℹ️")
                    info_button.setFixedSize(QSize(70, 32)) # Tamaño fijo para el botón Info
                    info_button.setToolTip(f"Mostrar detalles de {name}")
                    # Conectar el botón de info a la función show_info con los datos de la aplicación
                    info_button.clicked.connect(lambda _, a=app_data: self.show_info(a))
                    info_button.setStyleSheet("""
                        QPushButton {
                            background-color: #2196F3; /* Azul */
                            color: white;
                            border: none;
                            border-radius: 5px;
                            padding: 8px 12px;
                        }
                        QPushButton:hover {
                            background-color: #1a7bb9;
                        }
                    """)
                    buttons_layout.addWidget(info_button)
                    
                    buttons_layout.addStretch(1) # Empuja los botones a la izquierda
                    app_card_layout.addLayout(buttons_layout)

                    # Añadir la tarjeta de la aplicación a la cuadrícula principal
                    self.grid_layout.addWidget(app_card, row, col)

                    col += 1
                    if col >= cols: # Si la columna actual excede el número de columnas deseado
                        col = 0
                        row += 1

                except Exception as e:
                    # Capturar errores específicos para una aplicación y continuar con la siguiente
                    QMessageBox.warning(self, "Error al cargar aplicación", f"No se pudo cargar la aplicación '{name}': {str(e)} ⚠️")

        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error de JSON", "Error al decodificar el archivo 'aplicaciones.json'. Verifica su formato JSON. 🛠️❌")
        except Exception as e:
            QMessageBox.critical(self, "Error desconocido", f"Ocurrió un error inesperado al cargar las aplicaciones: {str(e)} 💥")

        # Añadir un "stretch" al final para empujar el contenido hacia arriba y a la izquierda
        # Esto asegura que las columnas y filas no ocupen todo el espacio si hay pocos elementos.
        self.grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), row + 1, 0, 1, cols)
        self.grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, col + 1, row + 1, 1)

    def _clear_layout(self, layout):
        """Función auxiliar para limpiar un layout y sus widgets."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())

    def launch_application(self, command, app_name):
        """Lanza la aplicación especificada usando subprocess."""
        if not command:
            QMessageBox.warning(self, "Error de Lanzamiento", f"La ruta o comando para '{app_name}' está vacío. No se puede lanzar. 🚫")
            return

        try:
            # Usar subprocess.Popen para lanzar la aplicación en segundo plano
            # shell=True permite ejecutar comandos complejos o con variables de entorno
            # stdout y stderr a devnull para evitar que la salida inunde la consola del lanzador
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            QMessageBox.information(self, "Lanzado", f"Aplicación '{app_name}' lanzada. ¡Disfruta! 🎉")
        except FileNotFoundError:
            QMessageBox.warning(self, "Error de Ejecución", f"El comando '{command}' no se encontró. Asegúrate de que la aplicación está instalada y en tu PATH o la ruta es correcta. 📁❌")
        except Exception as e:
            QMessageBox.critical(self, "Error Inesperado", f"No se pudo iniciar la aplicación '{app_name}': {str(e)} 💥")

    def show_info(self, app):
        """Muestra una ventana de mensaje con la información detallada de la aplicación."""
        try:
            # Obtener información detallada del JSON
            name = app.get("name", "Sin nombre")
            alias = app.get("alias", "Sin alias")
            path = app.get("path", "Sin ruta")
            icon = app.get("icon", "Sin icono")
            enabled = app.get("enabled", False)

            # Formatear el mensaje
            info_message = (
                f"Nombre: {name}\n"
                f"Alias (comando): {alias}\n"
                f"Ruta del directorio: {path}\n"
                f"Ruta del icono: {icon if icon else 'Ninguno especificado'}\n"
                f"Habilitado: {'Sí' if enabled else 'No'}"
            )

            # Mostrar mensaje de información
            QMessageBox.information(self, f"Información de {name}", info_message)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo mostrar la información: {str(e)} 💥")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = AppLauncher()
    launcher.show()
    sys.exit(app.exec_())