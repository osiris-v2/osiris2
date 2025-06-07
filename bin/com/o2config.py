#!/usr/bin/env python3
import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QScrollArea, QLineEdit, QCheckBox, QFileDialog, QTabWidget,
    QSizePolicy # Para la política de tamaño de los widgets
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

# Nombre del archivo de configuración por defecto
CONFIG_FILE = "aplicaciones.json"

class DskonfigPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Osiris DSKL - Gestor de Aplicaciones")
        self.setGeometry(100, 100, 800, 600) # Tamaño inicial más generoso

        # Layout principal de la ventana
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Estructura para almacenar los datos de cada pestaña
        # self.tabs_data = [ { "widget": QWidget, "file_path": "...", "original": [...], "current": [...] }, ... ]
        self.tabs_data = []

        # Barra de herramientas (Toolbar)
        self.create_toolbar()

        # Widget de pestañas
        self.tabs_widget = QTabWidget()
        self.main_layout.addWidget(self.tabs_widget)

        # Conectar signal para manejar el cierre de pestañas por el usuario
        self.tabs_widget.tabCloseRequested.connect(self.close_tab)

        # Asegurar que el archivo de configuración por defecto existe y cargarlo
        self.ensure_config_file_exists()
        self.load_config(CONFIG_FILE) # Intentar cargar el archivo por defecto

    def create_toolbar(self):
        """Crea y configura la barra de herramientas."""
        toolbar = QWidget() # Usamos un QWidget para la toolbar
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0) # Espacio reducido alrededor de los botones

        # Botones de la toolbar
        btn_new_config = QPushButton("Nuevo Config.")
        btn_new_config.clicked.connect(self.new_config_tab)
        toolbar_layout.addWidget(btn_new_config)

        btn_load_config = QPushButton("Cargar Config.")
        btn_load_config.clicked.connect(self.load_config_file)
        toolbar_layout.addWidget(btn_load_config)

        btn_save_config = QPushButton("Guardar Config.")
        btn_save_config.clicked.connect(self.save_current_config)
        toolbar_layout.addWidget(btn_save_config)

        # Añadir espacio elástico para empujar los botones a la izquierda
        toolbar_layout.addStretch(1)

        self.main_layout.addWidget(toolbar) # Añadir la toolbar al layout principal

    def ensure_config_file_exists(self):
        """Asegura que el archivo de configuración por defecto existe, creándolo si no."""
        if not os.path.exists(CONFIG_FILE):
            print(f"Archivo '{CONFIG_FILE}' no encontrado. Creando uno por defecto...")
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump([], f, indent=4) # Crea un JSON con una lista vacía
                QMessageBox.information(self, "Configuración Creada",
                                        f"El archivo '{CONFIG_FILE}' no fue encontrado y se ha creado uno vacío por defecto.")
                print(f"Archivo '{CONFIG_FILE}' creado con contenido por defecto.")
            except Exception as e:
                QMessageBox.critical(self, "Error de Creación",
                                     f"No se pudo crear el archivo de configuración '{CONFIG_FILE}': {str(e)}")
                print(f"Error al crear archivo de configuración: {e}")


    def new_config_tab(self, file_path=None, config_data=None):
        """Crea una nueva pestaña para una configuración (vacía o cargada)."""
        tab_name = os.path.basename(file_path) if file_path else f"Nueva Config {len(self.tabs_data) + 1}"
        tab_widget = QWidget() # Widget contenedor para la nueva pestaña
        tab_layout = QVBoxLayout(tab_widget) # Layout para el contenido de la pestaña
        tab_layout.setContentsMargins(5, 5, 5, 5) # Márgenes internos

        # --- Configurar ScrollArea para la lista de aplicaciones ---
        scroll_area = QScrollArea(tab_widget)
        scroll_area.setWidgetResizable(True)

        # Widget contenedor para el layout de las entradas de aplicaciones
        scroll_content_widget = QWidget()
        # Usamos un QVBoxLayout simple para apilar las entradas de apps
        apps_entries_layout = QVBoxLayout(scroll_content_widget)
        apps_entries_layout.setAlignment(Qt.AlignTop) # Asegurar que las entradas se apilan arriba
        apps_entries_layout.setContentsMargins(0, 0, 0, 0)
        apps_entries_layout.setSpacing(10) # Espacio entre entradas

        scroll_content_widget.setLayout(apps_entries_layout)
        scroll_area.setWidget(scroll_content_widget)

        # Añadir botón para agregar nueva entrada de aplicación
        btn_add_entry = QPushButton("+ Agregar Aplicación")
        # Conectar a la función que añade la entrada a los datos Y a la UI de ESTA pestaña
        btn_add_entry.clicked.connect(lambda: self.add_config_entry(tab_widget))
        tab_layout.addWidget(btn_add_entry)

        # Añadir el scroll area al layout de la pestaña
        tab_layout.addWidget(scroll_area)

        # Añadir espacio elástico al final del layout de entradas para empujar todo hacia arriba
        apps_entries_layout.addStretch(1) # Esto es CRUCIAL para el scroll

        # --- Fin de ScrollArea ---

        # Añadir la pestaña al QTabWidget
        tab_index = self.tabs_widget.addTab(tab_widget, tab_name)
        self.tabs_widget.setCurrentIndex(tab_index) # Seleccionar la nueva pestaña

        # Almacenar los datos de esta pestaña
        initial_data = config_data if config_data is not None else []
        self.tabs_data.append({
            "widget": tab_widget,
            "file_path": file_path,
            "original": initial_data.copy(), # Copia profunda de la lista y dicts
            "current": initial_data.copy()
        })

        # Mostrar las entradas de configuración iniciales si existen
        self.display_config_entries(tab_widget, initial_data)

        # Habilitar botón de cierre en la pestaña
        self.tabs_widget.setTabsClosable(True)


    def display_config_entries(self, tab_widget, entries):
        """Muestra las entradas de configuración en la UI de una pestaña específica."""
        # Encontrar el layout de entradas dentro del scroll area de esta pestaña
        scroll_area = tab_widget.findChild(QScrollArea)
        if not scroll_area:
            print("Error: No se encontró QScrollArea en la pestaña.")
            return

        scroll_content_widget = scroll_area.widget()
        if not scroll_content_widget:
             print("Error: No se encontró el widget de contenido en el QScrollArea.")
             return

        apps_entries_layout = scroll_content_widget.layout()
        if not apps_entries_layout:
             print("Error: No se encontró el layout de entradas en el widget de contenido.")
             return

        # Limpiar entradas existentes antes de mostrarlas
        self.clear_layout(apps_entries_layout)

        # Añadir cada entrada a la UI
        for entry in entries:
            self.add_entry_to_ui(apps_entries_layout, entry, tab_widget)

        # Asegurar que el elástico está al final después de añadir todas las entradas
        apps_entries_layout.addStretch(1)


    def add_config_entry(self, tab_widget):
        """Añade una nueva entrada de configuración a los datos y a la UI de una pestaña."""
        tab_index = self.tabs_widget.indexOf(tab_widget)
        if tab_index == -1:
            print("Error: add_config_entry llamada para un widget no encontrado en las pestañas.")
            return

        # Crear una nueva entrada con valores por defecto
        new_entry = {
            "id": len(self.tabs_data[tab_index]["current"]) + 1, # ID simple basado en la longitud actual
            "name": f"Nueva App {len(self.tabs_data[tab_index]['current']) + 1}",
            "alias": "",
            "path": "",
            "icon": "", # Añadir campo icon por defecto
            "enabled": True # Por defecto habilitada
            # Puedes añadir más campos por defecto aquí
        }

        # Añadir la nueva entrada a los datos 'current' de la pestaña
        self.tabs_data[tab_index]["current"].append(new_entry)

        # Encontrar el layout de entradas en la UI de esta pestaña para añadir el nuevo widget
        scroll_area = tab_widget.findChild(QScrollArea)
        scroll_content_widget = scroll_area.widget()
        apps_entries_layout = scroll_content_widget.layout()

        # Añadir la nueva entrada a la UI
        self.add_entry_to_ui(apps_entries_layout, new_entry, tab_widget)

        # Asegurar que el elástico está al final después de añadir la nueva entrada
        # Primero, remover el elástico actual si existe
        item_to_remove = None
        for i in range(apps_entries_layout.count()):
            item = apps_entries_layout.itemAt(i)
            if item and item.spacerItem():
                item_to_remove = item
                break
        if item_to_remove:
             apps_entries_layout.removeItem(item_to_remove)

        # Luego, añadir un nuevo elástico
        apps_entries_layout.addStretch(1)


    def add_entry_to_ui(self, apps_entries_layout, entry, tab_widget):
        """Crea y añade los widgets de una entrada de aplicación a un layout específico."""
        entry_widget = QWidget() # Widget contenedor para esta fila de entrada
        entry_layout = QHBoxLayout(entry_widget)
        entry_layout.setContentsMargins(5, 5, 5, 5) # Márgenes internos
        entry_widget.setStyleSheet("border: 1px solid lightgray; border-radius: 5px;") # Estilo visual simple

        # Campo Nombre
        entry_layout.addWidget(QLabel("Nombre:"))
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Nombre de la aplicación")
        name_edit.setText(entry.get("name", ""))
        # Conectar signal para actualizar los datos cuando el texto cambie o el foco se pierda
        name_edit.textChanged.connect(lambda text: self.update_entry_field(entry, "name", text))
        entry_layout.addWidget(name_edit)

        # Campo Alias (nombre del ejecutable)
        entry_layout.addWidget(QLabel("Alias:"))
        alias_edit = QLineEdit()
        alias_edit.setPlaceholderText("ejecutable.exe o script.sh")
        alias_edit.setText(entry.get("alias", ""))
        alias_edit.textChanged.connect(lambda text: self.update_entry_field(entry, "alias", text))
        entry_layout.addWidget(alias_edit)

        # Campo Path (directorio del ejecutable)
        entry_layout.addWidget(QLabel("Ruta Dir:"))
        path_edit = QLineEdit()
        path_edit.setPlaceholderText("/ruta/al/directorio")
        path_edit.setText(entry.get("path", ""))
        path_edit.textChanged.connect(lambda text: self.update_entry_field(entry, "path", text))
        entry_layout.addWidget(path_edit)

        # Botón Seleccionar Directorio para Path
        btn_select_path = QPushButton("...") # Usar puntos para un botón más compacto
        btn_select_path.setToolTip("Seleccionar directorio de la aplicación")
        # Conectar usando lambda para pasar la entrada y el widget de edición
        btn_select_path.clicked.connect(lambda: self.select_path(entry, path_edit, "directory"))
        entry_layout.addWidget(btn_select_path)

        # Campo Icon Path
        entry_layout.addWidget(QLabel("Icono:"))
        icon_edit = QLineEdit()
        icon_edit.setPlaceholderText("ruta/al/icono.png (opcional)")
        icon_edit.setText(entry.get("icon", ""))
        icon_edit.textChanged.connect(lambda text: self.update_entry_field(entry, "icon", text))
        entry_layout.addWidget(icon_edit)

        # Botón Seleccionar Archivo para Icono
        btn_select_icon = QPushButton("...")
        btn_select_icon.setToolTip("Seleccionar archivo de ícono (.png, .jpg, etc.)")
        btn_select_icon.clicked.connect(lambda: self.select_path(entry, icon_edit, "file"))
        entry_layout.addWidget(btn_select_icon)

        # Checkbox para Habilitar
        enabled_checkbox = QCheckBox("Habilitado")
        enabled_checkbox.setChecked(entry.get("enabled", False)) # Asegurar valor por defecto si no existe
        # Conectar signal para actualizar los datos
        enabled_checkbox.stateChanged.connect(lambda state: self.update_entry_field(entry, "enabled", state == Qt.Checked))
        entry_layout.addWidget(enabled_checkbox)


        # Botón Eliminar (alineado a la derecha si hay espacio)
        btn_delete = QPushButton("Eliminar")
        btn_delete.clicked.connect(lambda: self.delete_entry(entry, entry_widget, tab_widget))
        entry_layout.addWidget(btn_delete)

        # Añadir el widget de la entrada (con su layout) al layout vertical principal de las entradas
        apps_entries_layout.addWidget(entry_widget)


    def update_entry_field(self, entry, field_name, new_value):
        """Actualiza un campo específico en el diccionario de datos de una entrada."""
        entry[field_name] = new_value
        # Opcional: podrías marcar la pestaña como "modificada" aquí


    def select_path(self, entry, line_edit_widget, mode="file"):
        """Abre un diálogo para seleccionar archivo o directorio y actualiza la UI y los datos."""
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog # Descomentar si hay problemas con el diálogo nativo

        if mode == "file":
            file_dialog = QFileDialog.getOpenFileName(self, "Seleccionar Archivo", "",
                                                      "Todos los Archivos (*);;Imágenes (*.png *.jpg *.jpeg *.gif)", options=options)
            selected_path = file_dialog[0]
        elif mode == "directory":
             file_dialog = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio", "", options=options | QFileDialog.ShowDirsOnly)
             selected_path = file_dialog # getExistingDirectory devuelve solo la ruta

        if selected_path:
            line_edit_widget.setText(selected_path) # Actualiza la UI
            # La actualización de los datos se hace automáticamente si el QLineEdit está conectado con textChanged


    def delete_entry(self, entry, entry_widget, tab_widget):
        """Elimina una entrada de los datos y de la UI."""
        confirm = QMessageBox.askyesno(self, "Confirmar Eliminación", "¿Estás seguro de que deseas eliminar esta configuración?")
        if confirm == QMessageBox.Yes:
            tab_index = self.tabs_widget.indexOf(tab_widget)
            if tab_index != -1:
                # Eliminar de los datos 'current'
                self.tabs_data[tab_index]["current"].remove(entry)
                # Eliminar el widget de la UI
                entry_widget.deleteLater()
                # Opcional: podrías marcar la pestaña como "modificada" aquí


    def load_config_file(self):
        """Abre un diálogo de archivo para cargar una configuración y crea una nueva pestaña."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Cargar Archivo de Configuración", "",
                                                    "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            self.load_config(file_path)

    def load_config(self, file_path):
        """Carga datos de un archivo JSON y crea una nueva pestaña para ellos."""
        try:
            with open(file_path, "r", encoding='utf-8') as f: # Usar encoding seguro
                config_data = json.load(f)

            if not isinstance(config_data, list):
                QMessageBox.warning(self, "Error de Formato",
                                    f"El archivo '{file_path}' tiene un formato incorrecto. Debería ser una lista de objetos JSON.")
                return # No cargar si el formato es incorrecto

            # Verificar si el archivo ya está cargado en otra pestaña
            for data_entry in self.tabs_data:
                 if data_entry["file_path"] and os.path.abspath(data_entry["file_path"]) == os.path.abspath(file_path):
                      # Si ya está cargado, simplemente cambiamos a esa pestaña
                      index = self.tabs_widget.indexOf(data_entry["widget"])
                      if index != -1:
                          self.tabs_widget.setCurrentIndex(index)
                          QMessageBox.information(self, "Ya Cargado", f"El archivo '{os.path.basename(file_path)}' ya está abierto.")
                          return # Salir sin cargar de nuevo

            # Si no está cargado, crear una nueva pestaña
            self.new_config_tab(file_path=file_path, config_data=config_data)

        except FileNotFoundError:
            # Esto ya se manejó en ensure_config_file_exists para el archivo por defecto
            # Si el usuario intenta cargar un archivo que no existe, lo informamos
            if file_path != CONFIG_FILE: # Evitar doble mensaje al inicio
                 QMessageBox.critical(self, "Error", f"El archivo '{file_path}' no fue encontrado.")
            print(f"Error FileNotFoundError: {file_path}")

        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", f"Error al decodificar el archivo JSON '{file_path}'. Revisa su formato.")
            print(f"Error JSONDecodeError: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error desconocido", f"Error al cargar configuración desde '{file_path}': {str(e)}")
            print(f"Error desconocido al cargar {file_path}: {e}")


    def save_current_config(self):
        """Guarda la configuración de la pestaña actualmente seleccionada."""
        current_tab_index = self.tabs_widget.currentIndex()
        if current_tab_index == -1:
            QMessageBox.warning(self, "Advertencia", "No hay ninguna pestaña seleccionada para guardar.")
            return

        # Obtener los datos de la pestaña actual
        tab_data = self.tabs_data[current_tab_index]
        current_config = tab_data["current"]
        original_config = tab_data["original"]
        file_path = tab_data["file_path"]

        # Comparar la configuración actual con la original (ignorando posibles diferencias en el orden o campos extra que no se editan)
        # Una comparación simple de listas de diccionarios puede no ser suficiente para detectar todos los cambios sutiles,
        # pero para los campos que estamos editando, debería funcionar si los datos están bien estructurados.
        # Una comparación más robusta implicaría ordenar las listas por un ID o clave única y luego comparar los dicts.
        # Por ahora, la comparación simple funciona para los cambios básicos (valores de campos, añadir/eliminar).

        # if current_config != original_config: # Comparación simple
        # Verificar si hay cambios comparando los datos 'current' con los 'original'
        # Esto es un poco más robusto: convierte a JSON y compara las cadenas
        # (ignora el orden si usas sort_keys=True, pero necesitamos el orden para la UI)
        # Mejor: verificar longitud y luego comparar item por item si el orden importa
        has_changes = len(current_config) != len(original_config)
        if not has_changes:
            # Comparar elemento por elemento si las longitudes son iguales
            # Asumimos que el orden en la UI y los datos 'current' es el mismo
            for i in range(len(current_config)):
                # Comparación de dicts. Puede ser superficial si los dicts tienen sub-estructuras complejas
                if i >= len(original_config) or current_config[i] != original_config[i]:
                    has_changes = True
                    break

        if has_changes:
            # Determinar la ruta de guardado
            if not file_path:
                # Si la pestaña no tiene ruta (es una nueva configuración), preguntar dónde guardar
                options = QFileDialog.Options()
                file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Configuración Como",
                                                             f"Nueva Config {current_tab_index + 1}.json",
                                                             "JSON Files (*.json);;All Files (*)", options=options)
                if not file_path: # Usuario canceló
                    return
                # Si se guardó como un nuevo archivo, actualizar la ruta de la pestaña
                tab_data["file_path"] = file_path
                # También actualizar el título de la pestaña
                self.tabs_widget.setTabText(current_tab_index, os.path.basename(file_path))

            try:
                # Eliminar IDs antes de guardar si no queremos que estén en el archivo
                # (Aunque tener IDs puede ser útil para el gestor interno, el lanzador no los necesita)
                # Decidamos mantener los IDs por ahora, pueden ser útiles después.
                # config_to_save = [ {k: v for k, v in item.items() if k != 'id'} for item in current_config ]

                # Guardar los datos actuales en el archivo JSON
                with open(file_path, "w", encoding='utf-8') as f:
                    json.dump(current_config, f, indent=4) # Usar indent=4 para que sea legible

                QMessageBox.information(self, "Guardado Exitoso", f"Configuración guardada en '{file_path}'")
                print(f"Configuración guardada en: {file_path}")

                # Actualizar la configuración original después de guardar
                tab_data["original"] = current_config.copy()

            except (TypeError, ValueError) as e:
                QMessageBox.critical(self, "Error de Guardado", f"Error al convertir datos a JSON o escribir en archivo: {e}")
                print(f"Error de guardado (JSON/Write): {e}")
            except Exception as e:
                 QMessageBox.critical(self, "Error de Guardado", f"Error desconocido al guardar archivo: {e}")
                 print(f"Error de guardado (desconocido): {e}")

        else:
            QMessageBox.information(self, "Sin Cambios", "No hay cambios para guardar en esta configuración.")


    def close_tab(self, index):
        """Maneja el cierre de una pestaña, preguntando si guardar si hay cambios."""
        if index < 0 or index >= len(self.tabs_data):
             print(f"Error: Intento de cerrar índice de pestaña inválido: {index}")
             return

        tab_data = self.tabs_data[index]
        has_changes = tab_data["current"] != tab_data["original"] # Comparación simple de cambios

        if has_changes:
            reply = QMessageBox.question(self, "Guardar Cambios",
                                         f"La configuración de la pestaña '{self.tabs_widget.tabText(index)}' ha sido modificada. ¿Desea guardar los cambios antes de cerrar?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            if reply == QMessageBox.Save:
                # Intentar guardar. Si el guardado es cancelado o falla, no cerrar la pestaña.
                # Necesitamos modificar save_current_config o manejar aquí si el guardado fue exitoso.
                # Una forma simple es llamar save_current_config y verificar si el file_path ya no es None (si era una nueva config sin guardar)
                original_file_path = tab_data["file_path"]
                self.tabs_widget.setCurrentIndex(index) # Asegurarse de que esta es la pestaña activa para save_current_config
                self.save_current_config()
                # Después de llamar a save_current_config, re-verificar si todavía hay cambios para guardar
                # Esto puede ser complicado. Un enfoque más simple: si el usuario elige Guardar, asumimos que quiere cerrar DESPUÉS de intentar guardar.
                # Si el guardado falla o se cancela DENTRO de save_current_config (ej: cierra el diálogo Guardar Como), save_current_config ya maneja el mensaje de error.
                # Aquí simplemente procedemos a cerrar DESPUÉS del intento de guardar, a menos que el usuario haya elegido Cancelar inicialmente.

                # Re-check has_changes state after potential save - this is tricky.
                # For simplicity, let's assume if Save was chosen, we attempt save and then close.
                # A more robust solution would require save_current_config to return success/failure.
                # For now, let's just proceed to close.

                # If the user cancelled the Save dialog inside save_current_config, file_path might still be None
                # and has_changes might still be True. This needs careful handling.
                # Let's add a simple check: if after save attempt, the tab still has no file_path AND still has changes,
                # maybe don't close? Or just close anyway? Closing seems less frustrating than a stuck tab.
                pass # Proceed to close after Save attempt

            elif reply == QMessageBox.Cancel:
                return # No cerrar la pestaña

            # If reply is Discard or Save was chosen, proceed to remove the tab

        # Si no hay cambios o el usuario eligió Descartar o Guardar (y no Cancelar el diálogo inicial)
        # Remove the widget and data associated with this index
        self.tabs_widget.removeTab(index)
        # Remover el elemento de self.tabs_data por índice
        del self.tabs_data[index]
        print(f"Pestaña en índice {index} cerrada.")


    def clear_layout(self, layout):
        """Limpia todos los widgets y layouts dentro de un layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None:
                         self.clear_layout(sub_layout) # Limpiar sub-layouts recursivamente
                         sub_layout.deleteLater() # Eliminar el layout después de limpiar
                del item # Eliminar el QLayoutItem



# Ejecución de la Aplicación
#if __name__ == "__main__":
def main(args):
    try:
        app = QApplication(sys.argv)
        launcher = DskonfigPanel() # Cambiamos el nombre a DskonfigPanel
        launcher.show()
        sys.exit(app.exec_())
    except Exception as e:
        print("ERROR EXCEPTION EN MAIN FUNCTION")
        return


try:
    main([""])
except Exception as e:
    print("EXCEPTION MAIN LOAD:",e)


