#!/usr/bin/env python3
import sys
import os
import json
import glob
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QLabel, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit,
    QComboBox, QSpinBox, QFormLayout, QGridLayout, QFrame, QSpacerItem, QSizePolicy,
    QScrollArea
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal

# Directorio base para las operaciones de carga y guardado de archivos JSON.
# Se recomienda un directorio más robusto para producción, pero para este ejemplo, /tmp es funcional.
BASE_DIR = os.path.join(os.path.expanduser("~"), ".osiris_json_editor_data")
os.makedirs(BASE_DIR, exist_ok=True) # Asegura que el directorio exista


# --- Definición de Claves y sus Tipos para la GUI ---
# Basado en el análisis de load_osiris_context.py y insert.dev.ai
# Añadido 'picker_type' para campos de ruta individuales,
# y 'list_element_type' para los elementos dentro de las listas.
KEY_DEFINITIONS = {
    "human": {"type": "string", "multiline": True, "default": ""},
    "aiinstruction": {"type": "string", "multiline": True, "default": ""},
    "metadata": {"type": "object", "default": {}},
    "readfile": {"type": "list_string", "default": [], "list_element_type": "file"},
    # CORRECCIÓN v7: readdirectoryfiles ahora es un list_string
    "readdirectoryfiles": {"type": "list_string", "default": [], "list_element_type": "directory"},
    # CORRECCIÓN v7: readdirectoryfilesrecursive ahora es un list_string
    "readdirectoryfilesrecursive": {"type": "list_string", "default": [], "list_element_type": "directory"},
    "readdirectorypaths": {"type": "list_string", "default": [], "list_element_type": "directory"},
    "readdirectorypathrecursive": {"type": "list_string", "default": [], "list_element_type": "directory"},
    "filterincludeextensions": {"type": "list_string", "default": [], "list_element_type": "string"},
    "filterexcludepatterns": {"type": "list_string", "default": [], "list_element_type": "string"},
    "maxcontexttokens": {"type": "int", "default": 1000000},
    "responseformat": {"type": "string", "multiline": False, "default": ""},
    "fileencoding": {"type": "string", "multiline": False, "default": "utf-8"},
}

# Orden canónico de las claves, basado en load_osiris_context.py
CANONICAL_KEY_ORDER = [
    "maxcontexttokens",
    "fileencoding",
    "human",
    "aiinstruction",
    "metadata",
    "readfile",
    "readdirectoryfiles",
    "readdirectoryfilesrecursive",
    "readdirectorypaths",
    "readdirectorypathrecursive",
    "filterincludeextensions",
    "filterexcludepatterns",
    "responseformat"
]

# --- Nuevo Widget Personalizado para Seleccionar Rutas (Archivo/Directorio) ---
class PathLineEditWidget(QWidget):
    textChanged = pyqtSignal(str) # Señal personalizada

    def __init__(self, current_path, path_type="file", parent=None):
        super().__init__(parent)
        self.path_type = path_type
        self.current_path = current_path

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit(self.current_path)
        self.line_edit.textChanged.connect(self._on_line_edit_changed)
        layout.addWidget(self.line_edit)

        self.browse_button = QPushButton("Explorar...")
        self.browse_button.clicked.connect(self._browse_path)
        layout.addWidget(self.browse_button)

    def _on_line_edit_changed(self, text):
        self.current_path = text
        self.textChanged.emit(text)

    def _browse_path(self):
        try:
            if self.path_type == "file":
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Seleccionar Archivo",
                    os.path.dirname(self.current_path) if self.current_path and os.path.exists(self.current_path) else BASE_DIR,
                    "Todos los archivos (*.*)"
                )
                if file_path:
                    self.line_edit.setText(os.path.normpath(file_path)) # Normalizar la ruta al seleccionarla
            elif self.path_type == "directory":
                dir_path = QFileDialog.getExistingDirectory(
                    self,
                    "Seleccionar Directorio",
                    self.current_path if self.current_path and os.path.exists(self.current_path) else BASE_DIR
                )
                if dir_path:
                    self.line_edit.setText(os.path.normpath(dir_path)) # Normalizar la ruta al seleccionarla
        except Exception as e:
            QMessageBox.critical(self, "Error de Explorador", f"Error al abrir el explorador de archivos: {e} ❌")
            print(f"ERROR: Error al abrir el explorador de archivos: {e}")

    def text(self):
        return self.line_edit.text()

# --- Diálogo para Editar Listas de Strings o Rutas ---
class ListStringPathEditorDialog(QDialog):
    def __init__(self, current_list, list_element_type="string", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Lista de Elementos")
        self.setGeometry(200, 200, 500, 400) # Tamaño ampliado

        self.list_data = list(current_list) # Copia para no modificar el original directamente
        self.list_element_type = list_element_type
        
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.addItems(self.list_data)
        layout.addWidget(self.list_widget)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"Nuevo elemento ({self.list_element_type}) o elemento a editar")
        input_layout.addWidget(self.input_field)

        self.add_button = QPushButton("Añadir Texto")
        self.add_button.clicked.connect(self._add_item)
        input_layout.addWidget(self.add_button)

        # Botones de exploración de rutas si aplica
        if self.list_element_type == "file":
            self.add_file_button = QPushButton("Añadir Archivo...")
            self.add_file_button.clicked.connect(self._add_file_item)
            input_layout.addWidget(self.add_file_button)
        elif self.list_element_type == "directory":
            self.add_dir_button = QPushButton("Añadir Directorio...")
            self.add_dir_button.clicked.connect(self._add_directory_item)
            input_layout.addWidget(self.add_dir_button)
        
        layout.addLayout(input_layout)

        edit_delete_layout = QHBoxLayout()
        self.edit_button = QPushButton("Editar Seleccionado")
        self.edit_button.clicked.connect(self._edit_item)
        edit_delete_layout.addWidget(self.edit_button)
        
        self.remove_button = QPushButton("Eliminar Seleccionado")
        self.remove_button.clicked.connect(self._remove_item)
        edit_delete_layout.addWidget(self.remove_button)

        layout.addLayout(edit_delete_layout)
        
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("Aceptar")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        self.list_widget.itemDoubleClicked.connect(lambda item: self.input_field.setText(item.text()))
        self.list_widget.currentRowChanged.connect(self._update_button_states)
        self._update_button_states() # Estado inicial de los botones

    def _add_item_to_list(self, text):
        if text:
            # Normalizar la ruta si es de tipo archivo o directorio
            if self.list_element_type in ["file", "directory"]:
                text = os.path.normpath(text) 
            
            if text not in self.list_data:
                self.list_data.append(text)
                self.list_widget.addItem(text)
                self.input_field.clear()
                self._update_button_states()
            else:
                QMessageBox.warning(self, "Duplicado", f"El elemento \'{text}\' ya existe en la lista. ⚠️")
                print(f"ADVERTENCIA: Intento de añadir elemento duplicado: \'{text}\'.")
        else:
            QMessageBox.warning(self, "Entrada Vacía", "El texto a añadir no puede estar vacío. 😕")
            print("ADVERTENCIA: Intento de añadir texto vacío a la lista.")

    def _add_item(self):
        try:
            text = self.input_field.text().strip()
            self._add_item_to_list(text)
        except Exception as e:
            QMessageBox.critical(self, "Error al Añadir", f"Error inesperado al añadir elemento: {e} 💥")
            print(f"ERROR: Error inesperado al añadir elemento a la lista: {e}")

    def _add_file_item(self):
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Seleccionar Archivos",
                BASE_DIR,
                "Todos los archivos (*.*)"
            )
            for file_path in file_paths:
                self._add_item_to_list(file_path)
            self.input_field.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error de Archivo", f"Error al seleccionar archivo: {e} ❌")
            print(f"ERROR: Error al seleccionar archivo en ListStringPathEditorDialog: {e}")

    def _add_directory_item(self):
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar Directorio",
                BASE_DIR
            )
            if dir_path:
                self._add_item_to_list(dir_path)
            self.input_field.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error de Directorio", f"Error al seleccionar directorio: {e} ❌")
            print(f"ERROR: Error al seleccionar directorio en ListStringPathEditorDialog: {e}")

    def _edit_item(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            new_text = self.input_field.text().strip()
            if not new_text:
                QMessageBox.warning(self, "Edición", "El elemento no puede estar vacío. ⚠️")
                print("ADVERTENCIA: Intento de editar con texto vacío.")
                return

            # Check for duplication AFTER removing the old item from consideration for comparison
            temp_list_data = list(self.list_data)
            del temp_list_data[current_row] # Remove old item for unique check

            if new_text in temp_list_data:
                QMessageBox.warning(self, "Duplicado", f"El elemento \'{new_text}\' ya existe en la lista. ⚠️")
                print(f"ADVERTENCIA: Intento de editar a un elemento duplicado: \'{new_text}\'.")
                return
            
            try:
                self.list_data[current_row] = new_text
                self.list_widget.item(current_row).setText(new_text)
                self.input_field.clear()
                self._update_button_states()
            except Exception as e:
                QMessageBox.critical(self, "Error al Editar", f"Error inesperado al editar elemento: {e} 💥")
                print(f"ERROR: Error inesperado al editar elemento en la lista: {e}")
        else:
            QMessageBox.warning(self, "Edición", "Selecciona un elemento para editar. ⚠️")
            print("ADVERTENCIA: Intento de editar sin selección.")


    def _remove_item(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            try:
                item_text = self.list_widget.item(current_row).text()
                reply = QMessageBox.question(self, "Eliminar Elemento",
                                             f"¿Estás seguro de que quieres eliminar \'{item_text}\'? 🗑️",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.list_widget.takeItem(current_row) # Elimina el widget
                    del self.list_data[current_row]        # Elimina del modelo de datos
                    self._update_button_states()
                    self.input_field.clear() # Limpiar el campo de entrada al eliminar
            except Exception as e:
                QMessageBox.critical(self, "Error al Eliminar", f"Error inesperado al eliminar elemento: {e} 💥")
                print(f"ERROR: Error inesperado al eliminar elemento de la lista: {e}")
        else:
            QMessageBox.warning(self, "Eliminar", "Selecciona un elemento para eliminar. ⚠️")
            print("ADVERTENCIA: Intento de eliminar sin selección.")

    def _update_button_states(self):
        is_selected = self.list_widget.currentRow() >= 0
        self.edit_button.setEnabled(is_selected)
        self.remove_button.setEnabled(is_selected)
        # El botón de añadir texto siempre está activo.

    def get_list(self):
        return self.list_data

# --- Diálogo para Editar Objetos JSON (Metadata) ---
class JsonEditorDialog(QDialog):
    def __init__(self, current_json_obj, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Objeto JSON (Metadata)")
        self.setGeometry(200, 200, 600, 400)

        self.json_obj = current_json_obj # No copia, edita directamente para simplificar
        
        layout = QVBoxLayout(self)

        self.json_text_edit = QTextEdit()
        self.json_text_edit.setFont(QFont("Consolas", 9))
        self.json_text_edit.setPlaceholderText("Introduce tu objeto JSON aquí...")
        try:
            self.json_text_edit.setPlainText(json.dumps(self.json_obj, indent=2, ensure_ascii=False))
        except Exception as e:
            self.json_text_edit.setPlainText("{}") # Fallback a objeto vacío en caso de error inicial
            QMessageBox.warning(self, "Error de JSON", f"El objeto JSON inicial no pudo ser formateado. Se usará un objeto vacío: {e} ⚠️")
            print(f"ADVERTENCIA: Error al formatear JSON inicial en JsonEditorDialog: {e}")
        layout.addWidget(self.json_text_edit)

        buttons_layout = QHBoxLayout()
        self.validate_button = QPushButton("Validar JSON")
        self.validate_button.clicked.connect(self._validate_json)
        buttons_layout.addWidget(self.validate_button)
        
        ok_button = QPushButton("Aceptar")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)

    def _validate_json(self):
        content = self.json_text_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Validación", "El editor está vacío. No hay JSON para validar. 😕")
            print("ADVERTENCIA: Intento de validar JSON vacío.")
            return False
        try:
            json.loads(content)
            QMessageBox.information(self, "Validación Exitosa", "El JSON es válido. ✅")
            return True
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error de Validación", "El JSON es inválido:\n" + str(e) + " ❌")
            print(f"ERROR: JSON inválido en JsonEditorDialog: {e}")
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error de Validación", f"Error inesperado durante la validación del JSON: {e} 💥")
            print(f"ERROR: Error inesperado en la validación del JSON en JsonEditorDialog: {e}")
            return False

    def accept(self):
        if self._validate_json():
            try:
                self.json_obj = json.loads(self.json_text_edit.toPlainText())
                super().accept()
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Error de Guardado", f"El JSON no pudo ser parseado al aceptar: {e} ❌")
                print(f"ERROR: JSON no pudo ser parseado al aceptar en JsonEditorDialog: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error de Guardado", f"Error inesperado al guardar JSON: {e} 💥")
                print(f"ERROR: Error inesperado al guardar JSON en JsonEditorDialog: {e}")

    def get_json_object(self):
        return self.json_obj

# --- Diálogo para Seleccionar Clave a Añadir ---
class AddKeyDialog(QDialog):
    def __init__(self, existing_keys, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Nueva Clave")
        self.setGeometry(300, 300, 350, 150)

        self.selected_key = None

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.key_combo = QComboBox()
        available_keys = [k for k in CANONICAL_KEY_ORDER if k.lower() not in [ek.lower() for ek in existing_keys]]
        if not available_keys:
            QMessageBox.warning(self, "No hay Claves", "Todas las claves predefinidas ya están en este bloque. 🙁")
            self.reject() # Cerrar el diálogo si no hay claves disponibles
            return
        self.key_combo.addItems(available_keys)
        form_layout.addRow("Selecciona una clave:", self.key_combo)
        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("Añadir")
        ok_button.clicked.connect(self._accept_selection)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

    def _accept_selection(self):
        self.selected_key = self.key_combo.currentText()
        self.accept()

    def get_selected_key(self):
        return self.selected_key

# --- Clase Principal de la GUI ---
class OsirisJsonBuilderQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Osiris Context JSON Builder (PyQt6) v7") # Título actualizado
        self.setGeometry(100, 100, 1500, 900) # Tamaño ampliado

        self.current_file_path = None
        self.default_dir = BASE_DIR
        os.makedirs(self.default_dir, exist_ok=True)

        self.json_data = [] # Representación interna como lista de diccionarios Python

        self._create_widgets()
        self._create_layouts()
        self._connect_signals()
        self._update_path_label()
        self.statusBar().showMessage("Listo. Crea un nuevo JSON o abre uno existente. 🚀")

        # Añadir un bloque inicial vacío por defecto
        self.add_new_block()
        self.update_json_preview()

    def _create_widgets(self):
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # --- Top Buttons ---
        self.new_button = QPushButton("Nuevo JSON")
        self.open_button = QPushButton("Abrir JSON")
        self.save_button = QPushButton("Guardar JSON")
        self.save_as_button = QPushButton("Guardar Como...")
        self.validate_button = QPushButton("Validar Documento JSON")
        self.insert_template_button = QPushButton("Insertar Plantilla")

        # --- Left Panel: Block Management ---
        self.block_list_widget = QListWidget()
        self.block_list_widget.setMinimumWidth(200)
        self.block_list_widget.setMaximumWidth(300)
        self.add_block_button = QPushButton("Añadir Bloque")
        self.remove_block_button = QPushButton("Eliminar Bloque")

        # --- Center Panel: Key-Value Editor for Current Block ---
        self.key_value_table = QTableWidget()
        self.key_value_table.setColumnCount(2)
        self.key_value_table.setHorizontalHeaderLabels(["Clave", "Valor"])
        self.key_value_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.key_value_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # CORRECCIÓN V5: Habilitar redimensionamiento vertical interactivo para los encabezados de fila
        self.key_value_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.add_key_button = QPushButton("Añadir Clave")
        self.remove_key_button = QPushButton("Eliminar Clave")

        # --- Bottom Panel: JSON Preview ---
        self.json_preview_text = QTextEdit()
        self.json_preview_text.setReadOnly(True)
        self.json_preview_text.setFont(QFont("Consolas", 9))
        self.json_preview_text.setMinimumHeight(150)

        # --- Path Label in Status Bar ---
        self.path_label = QLabel("Archivo Actual: Ninguno")
        self.statusBar().addPermanentWidget(self.path_label)

    def _create_layouts(self):
        # Top buttons layout
        top_button_layout = QHBoxLayout()
        top_button_layout.addWidget(self.new_button)
        top_button_layout.addWidget(self.open_button)
        top_button_layout.addWidget(self.save_button)
        top_button_layout.addWidget(self.save_as_button)
        
        # Add a visual separator (QFrame) instead of addSeparator()
        h_splitter_top = QFrame()
        h_splitter_top.setFrameShape(QFrame.Shape.HLine)
        h_splitter_top.setFrameShadow(QFrame.Shadow.Sunken)
        # Wrap the separator in a layout to give it proper space in QHBoxLayout
        splitter_layout_wrapper = QVBoxLayout()
        splitter_layout_wrapper.addWidget(h_splitter_top)
        top_button_layout.addLayout(splitter_layout_wrapper) # Add the wrapper layout

        top_button_layout.addWidget(self.validate_button)
        top_button_layout.addWidget(self.insert_template_button)
        top_button_layout.addStretch(1)

        # Left panel layout (Blocks)
        left_panel_layout = QVBoxLayout()
        left_panel_layout.addWidget(QLabel("<h2>Bloques de Contexto</h2>"))
        left_panel_layout.addWidget(self.block_list_widget)
        left_panel_layout.addWidget(self.add_block_button)
        left_panel_layout.addWidget(self.remove_block_button)

        # Separator for visual clarity
        v_splitter = QFrame()
        v_splitter.setFrameShape(QFrame.Shape.VLine)
        v_splitter.setFrameShadow(QFrame.Shadow.Sunken)

        # Center panel layout (Key-Value Editor)
        center_panel_layout = QVBoxLayout()
        center_panel_layout.addWidget(QLabel("<h2>Editar Claves del Bloque Actual</h2>"))
        
        # Wrap key_value_table in a QScrollArea for better handling of many rows
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_content = QWidget()
        self.table_layout = QVBoxLayout(scroll_area_content)
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.table_layout.addWidget(self.key_value_table)
        scroll_area.setWidget(scroll_area_content)
        center_panel_layout.addWidget(scroll_area)


        key_button_layout = QHBoxLayout()
        key_button_layout.addWidget(self.add_key_button)
        key_button_layout.addWidget(self.remove_key_button)
        key_button_layout.addStretch(1)
        center_panel_layout.addLayout(key_button_layout)

        # Main horizontal layout for left and center panels
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.addLayout(left_panel_layout)
        main_horizontal_layout.addWidget(v_splitter)
        main_horizontal_layout.addLayout(center_panel_layout, 1) # Center panel expands

        # Overall main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addLayout(top_button_layout)
        main_layout.addLayout(main_horizontal_layout, 1) # Horizontal layout expands
        main_layout.addWidget(QLabel("<h3>Vista Previa del JSON Completo</h3>"))
        main_layout.addWidget(self.json_preview_text)

    def _connect_signals(self):
        self.new_button.clicked.connect(self.new_json_file)
        self.open_button.clicked.connect(self.load_json_file)
        self.save_button.clicked.connect(self.save_json_file)
        self.save_as_button.clicked.connect(self.save_json_file_as)
        self.validate_button.clicked.connect(self.validate_full_json)
        self.insert_template_button.clicked.connect(self.insert_template)

        self.add_block_button.clicked.connect(self.add_new_block)
        self.remove_block_button.clicked.connect(self.remove_selected_block)
        self.block_list_widget.currentRowChanged.connect(self.display_selected_block)

        self.add_key_button.clicked.connect(self.add_new_key_to_block)
        self.remove_key_button.clicked.connect(self.remove_selected_key_from_block)
        # No es necesario conectar key_value_table.cellChanged porque los QCellWidgets manejan sus propias señales
        # self.key_value_table.cellChanged.connect(self._handle_cell_changed) 

    def _update_path_label(self):
        try:
            if self.current_file_path:
                self.path_label.setText("Archivo Actual: " + os.path.basename(self.current_file_path))
                self.setToolTip(f"Ruta completa: {self.current_file_path}") # Tooltip para la ruta completa
            else:
                self.path_label.setText("Archivo Actual: Ninguno")
                self.setToolTip("")
        except Exception as e:
            print(f"ERROR: Error al actualizar la etiqueta de ruta: {e}")
            self.path_label.setText("Archivo Actual: Error ❌")
            self.setToolTip(f"Error: {e}")

    def _show_status_message(self, message):
        try:
            self.statusBar().showMessage(message)
        except Exception as e:
            print(f"ERROR: Error al mostrar mensaje en la barra de estado: {e}")

    def update_json_preview(self):
        """Actualiza el QTextEdit de la parte inferior con la representación JSON actual."""
        try:
            # Ordenar las claves de cada bloque antes de serializar para una vista previa consistente
            ordered_json_data = []
            for block in self.json_data:
                ordered_block = {}
                sorted_keys = sorted(block.keys(), key=lambda k: CANONICAL_KEY_ORDER.index(k.lower()) if k.lower() in CANONICAL_KEY_ORDER else len(CANONICAL_KEY_ORDER))
                for key in sorted_keys:
                    ordered_block[key] = block[key]
                ordered_json_data.append(ordered_block)

            formatted_json = json.dumps(ordered_json_data, indent=2, ensure_ascii=False)
            self.json_preview_text.setPlainText(formatted_json)
        except Exception as e:
            self.json_preview_text.setPlainText(f"Error al generar la vista previa JSON: {e} ❌")
            print(f"ERROR: Error al generar la vista previa JSON: {e}")

    def get_current_block_index(self):
        return self.block_list_widget.currentRow()

    def add_new_block(self):
        try:
            self.json_data.append({})
            block_name = f"Bloque {len(self.json_data)} " # Espacio añadido para mejor audición
            self.block_list_widget.addItem(block_name)
            self.block_list_widget.setCurrentRow(len(self.json_data) - 1)
            self.update_json_preview()
            self._show_status_message(f"Bloque \'{block_name}\' añadido. ➕")
        except Exception as e:
            QMessageBox.critical(self, "Error al Añadir Bloque", f"Error inesperado al añadir un nuevo bloque: {e} 💥")
            print(f"ERROR: Error al añadir nuevo bloque: {e}")


    def remove_selected_block(self):
        current_row = self.get_current_block_index()
        if current_row >= 0:
            try:
                reply = QMessageBox.question(self, "Eliminar Bloque",
                                             f"¿Estás seguro de que quieres eliminar \'Bloque {current_row + 1}\'? 🗑️",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.json_data.pop(current_row)
                    self.block_list_widget.takeItem(current_row)
                    # Renombrar los bloques restantes
                    for i in range(self.block_list_widget.count()):
                        self.block_list_widget.item(i).setText(f"Bloque {i + 1}")
                    
                    if self.block_list_widget.count() > 0:
                        new_row = min(current_row, self.block_list_widget.count() - 1)
                        self.block_list_widget.setCurrentRow(new_row)
                    else:
                        self.key_value_table.setRowCount(0) # Limpiar tabla si no quedan bloques
                    self.update_json_preview()
                    self._show_status_message("Bloque eliminado. ✔️")
            except Exception as e:
                QMessageBox.critical(self, "Error al Eliminar Bloque", f"Error inesperado al eliminar el bloque seleccionado: {e} 💥")
                print(f"ERROR: Error al eliminar bloque seleccionado: {e}")
        else:
            QMessageBox.warning(self, "Eliminar Bloque", "Selecciona un bloque para eliminar. ⚠️")
            print("ADVERTENCIA: Intento de eliminar bloque sin selección.")

    def display_selected_block(self, row):
        # Almacenar la clave y columna enfocadas actualmente antes de borrar para restaurar el foco
        focused_key = None
        focused_column = -1
        if self.key_value_table.rowCount() > 0 and self.key_value_table.currentColumn() >= 0:
            try:
                focused_column = self.key_value_table.currentColumn()
                current_row_in_table = self.key_value_table.currentRow()
                if current_row_in_table >= 0:
                    key_widget = self.key_value_table.cellWidget(current_row_in_table, 0)
                    if isinstance(key_widget, QComboBox):
                        focused_key = key_widget.currentText()
            except Exception as e:
                print(f"ADVERTENCIA: Error al obtener el foco actual antes de redibujar la tabla: {e}")

        # Limpiar la tabla actual
        self.key_value_table.clearContents()
        self.key_value_table.setRowCount(0)
        
        if row < 0 or row >= len(self.json_data):
            return

        current_block_data = self.json_data[row]
        
        # Ordenar las claves del bloque actual según el orden canónico
        sorted_keys = sorted(current_block_data.keys(), key=lambda k: CANONICAL_KEY_ORDER.index(k.lower()) if k.lower() in CANONICAL_KEY_ORDER else len(CANONICAL_KEY_ORDER))
        
        self.key_value_table.setRowCount(len(sorted_keys))

        for i, key in enumerate(sorted_keys):
            try:
                value = current_block_data[key]

                # Key ComboBox
                key_combo = QComboBox()
                # Asegurarse de que el ComboBox tenga todas las claves posibles para que el usuario pueda cambiar
                # Y que se muestre la clave actual, ya sea canónica o una no-canónica temporalmente
                key_combo.addItems(CANONICAL_KEY_ORDER)
                
                # Bloquear señales temporalmente al establecer el texto para evitar disparar el evento durante la inicialización
                key_combo.blockSignals(True) 
                key_combo.setCurrentText(key)
                key_combo.blockSignals(False) # Desbloquear después de establecer el texto
                
                # Conectar la señal *después* de la configuración inicial
                # Usamos una lambda para capturar los valores correctos de 'i' y 'key'
                key_combo.currentTextChanged.connect(lambda text, r=i, old_k=key: self._rename_key_in_block(r, old_k, text))
                self.key_value_table.setCellWidget(i, 0, key_combo)

                # Value Editor
                self._set_value_editor(i, key.lower(), value) # Usar key.lower() para la definición
            except Exception as e:
                print(f"ERROR: Error al procesar clave \'{key}\' en bloque {row + 1}: {e}")
                self.key_value_table.setCellWidget(i, 0, QTableWidgetItem(f"Error: {key}"))
                self.key_value_table.setCellWidget(i, 1, QTableWidgetItem(f"Error: {e}"))
                QMessageBox.critical(self, "Error de Bloque", f"Error al cargar la clave \'{key}\' en el bloque {row + 1}. Consulte la consola para más detalles. 💥")

        # CORRECCIÓN V5: NO llamar a resizeRowsToContents() para permitir el redimensionamiento manual de filas
        # por el usuario, especialmente para QTextEdit.
        # self.key_value_table.resizeRowsToContents() 
        self.update_json_preview()

        # Restaurar el foco si se pudo determinar
        if focused_key and focused_column != -1:
            for r in range(self.key_value_table.rowCount()):
                key_widget = self.key_value_table.cellWidget(r, 0)
                if isinstance(key_widget, QComboBox) and key_widget.currentText() == focused_key:
                    self.key_value_table.setCurrentCell(r, focused_column)
                    break

    def _set_value_editor(self, row, key, value):
        key_def = KEY_DEFINITIONS.get(key, {"type": "string", "multiline": False, "default": ""}) # Fallback, importante que sea False por defecto.
        
        try:
            if key_def["type"] == "string":
                # Verificar si es una ruta (file o directory)
                picker_type = key_def.get("picker_type")
                if picker_type in ["file", "directory"]:
                    path_widget = PathLineEditWidget(str(value), picker_type, self)
                    # Conectar la señal personalizada textChanged
                    path_widget.textChanged.connect(lambda text, r=row, k=key: self._update_value_from_line_edit(r, k, text))
                    self.key_value_table.setCellWidget(row, 1, path_widget)
                    self.key_value_table.setRowHeight(row, 30) # Altura estándar
                elif key_def["multiline"]:
                    text_edit = QTextEdit()
                    text_edit.setPlainText(str(value)) # Asegurarse de que el valor sea una cadena
                    text_edit.textChanged.connect(lambda r=row, k=key: self._update_value_from_text_edit(r, k, text_edit))
                    # CORRECCIÓN V5: Establecer altura mínima y política de tamaño para redimensionamiento interactivo
                    text_edit.setMinimumHeight(60) # Altura mínima para varias líneas de texto
                    text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Permitir que se expanda y sea redimensionable
                    self.key_value_table.setCellWidget(row, 1, text_edit)
                    self.key_value_table.setRowHeight(row, 80) # Altura inicial razonable para multilínea
                else:
                    line_edit = QLineEdit(str(value)) # Asegurarse de que el valor sea una cadena
                    line_edit.textChanged.connect(lambda text, r=row, k=key: self._update_value_from_line_edit(r, k, text))
                    self.key_value_table.setCellWidget(row, 1, line_edit)
                    self.key_value_table.setRowHeight(row, 30) # Altura estándar para línea simple
            elif key_def["type"] == "list_string":
                list_element_type = key_def.get("list_element_type", "string")
                btn = QPushButton("Editar Lista")
                btn.clicked.connect(lambda _, r=row, k=key, v=value, let=list_element_type: self._open_list_editor(r, k, v, let))
                self.key_value_table.setCellWidget(row, 1, btn)
                self.key_value_table.setRowHeight(row, 30)
            elif key_def["type"] == "object":
                btn = QPushButton("Editar Objeto JSON")
                btn.clicked.connect(lambda _, r=row, k=key, v=value: self._open_json_editor(r, k, v))
                self.key_value_table.setCellWidget(row, 1, btn)
                self.key_value_table.setRowHeight(row, 30)
            elif key_def["type"] == "int":
                spin_box = QSpinBox()
                spin_box.setRange(0, 20000000) # Rango sensible para tokens
                try:
                    spin_box.setValue(int(value))
                except (ValueError, TypeError):
                    spin_box.setValue(key_def["default"]) # Fallback a valor por defecto
                    QMessageBox.warning(self, "Tipo de Dato Incorrecto", f"El valor para \'{key}\' debería ser un número entero. Se ha restablecido al valor por defecto \'{key_def['default']}\'. ⚠️")
                    print(f"ADVERTENCIA: Valor incorrecto para \'{key}\', esperando entero, se encontró \'{value}\'. Establecido a defecto.")
                spin_box.valueChanged.connect(lambda val, r=row, k=key: self._update_value_from_spinbox(r, k, val))
                self.key_value_table.setCellWidget(row, 1, spin_box)
                self.key_value_table.setRowHeight(row, 30)
            else:
                # Fallback para tipos no definidos o desconocidos
                line_edit = QLineEdit(str(value))
                line_edit.setPlaceholderText("Tipo de clave desconocido o no soportado por la GUI.")
                line_edit.setReadOnly(True) # Hacerlo de solo lectura si no sabemos cómo manejarlo
                self.key_value_table.setCellWidget(row, 1, line_edit)
                self.key_value_table.setRowHeight(row, 30)
                QMessageBox.warning(self, "Tipo de Clave Desconocido", f"La clave \'{key}\' tiene un tipo \'{key_def['type']}\' no reconocido por la GUI. Se mostrará como texto plano y de solo lectura. 🚫")
                print(f"ADVERTENCIA: Tipo de clave \'{key_def['type']}\' para \'{key}\' no reconocido. Se usará QLineEdit de solo lectura.")
        except Exception as e:
            # Fallback general si falla la creación del widget
            error_text_edit = QTextEdit(f"ERROR al crear widget para \'{key}\': {e}")
            error_text_edit.setReadOnly(True)
            self.key_value_table.setCellWidget(row, 1, error_text_edit)
            self.key_value_table.setRowHeight(row, 50)
            QMessageBox.critical(self, "Error de GUI", f"Ocurrió un error al intentar crear el widget para la clave \'{key}\': {e} 💥")
            print(f"ERROR: Error al crear widget para la clave \'{key}\': {e}")


    def _update_value_from_text_edit(self, row, key, text_edit):
        current_block_idx = self.get_current_block_index()
        if current_block_idx >= 0 and current_block_idx < len(self.json_data):
            try:
                self.json_data[current_block_idx][key] = text_edit.toPlainText()
                self.update_json_preview()
                # CORRECCIÓN V5: Se ha quitado la actualización de altura de fila aquí para evitar el flickering
                # Ahora la altura la gestiona el usuario con el redimensionamiento vertical interactivo.
            except Exception as e:
                print(f"ERROR: Error al actualizar valor de QTextEdit para clave \'{key}\': {e}")
                self._show_status_message(f"Error al actualizar valor de \'{key}\'. Consulte la consola. ❌")


    def _update_value_from_line_edit(self, row, key, text):
        current_block_idx = self.get_current_block_index()
        if current_block_idx >= 0 and current_block_idx < len(self.json_data):
            try:
                self.json_data[current_block_idx][key] = text
                self.update_json_preview()
            except Exception as e:
                print(f"ERROR: Error al actualizar valor de QLineEdit para clave \'{key}\': {e}")
                self._show_status_message(f"Error al actualizar valor de \'{key}\'. Consulte la consola. ❌")


    def _update_value_from_spinbox(self, row, key, value):
        current_block_idx = self.get_current_block_index()
        if current_block_idx >= 0 and current_block_idx < len(self.json_data):
            try:
                self.json_data[current_block_idx][key] = value
                self.update_json_preview()
            except Exception as e:
                print(f"ERROR: Error al actualizar valor de QSpinBox para clave \'{key}\': {e}")
                self._show_status_message(f"Error al actualizar valor de \'{key}\'. Consulte la consola. ❌")


    def _open_list_editor(self, row, key, value, list_element_type):
        try:
            dialog = ListStringPathEditorDialog(value, list_element_type, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_list = dialog.get_list()
                current_block_idx = self.get_current_block_index()
                if current_block_idx >= 0:
                    self.json_data[current_block_idx][key] = new_list
                    self.update_json_preview()
                    self._show_status_message(f"Lista para \'{key}\' actualizada. 📝")
        except Exception as e:
            QMessageBox.critical(self, "Error al Editar Lista", f"Error inesperado al abrir o procesar el editor de lista: {e} 💥")
            print(f"ERROR: Error al abrir/procesar ListStringPathEditorDialog para clave \'{key}\': {e}")

    def _open_json_editor(self, row, key, value):
        try:
            dialog = JsonEditorDialog(value, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_json_obj = dialog.get_json_object()
                current_block_idx = self.get_current_block_index()
                if current_block_idx >= 0:
                    self.json_data[current_block_idx][key] = new_json_obj
                    self.update_json_preview()
                    self._show_status_message(f"Objeto JSON para \'{key}\' actualizado. ⚙️")
        except Exception as e:
            QMessageBox.critical(self, "Error al Editar JSON", f"Error inesperado al abrir o procesar el editor JSON: {e} 💥")
            print(f"ERROR: Error al abrir/procesar JsonEditorDialog para clave \'{key}\': {e}")

    def add_new_key_to_block(self):
        current_block_idx = self.get_current_block_index()
        if current_block_idx < 0:
            QMessageBox.warning(self, "Añadir Clave", "Selecciona un bloque primero. ⚠️")
            print("ADVERTENCIA: Intento de añadir clave sin bloque seleccionado.")
            return

        current_block = self.json_data[current_block_idx]
        
        try:
            # Abrir diálogo para que el usuario seleccione la clave
            add_key_dialog = AddKeyDialog(current_block.keys(), self)
            if add_key_dialog.exec() == QDialog.DialogCode.Accepted:
                new_key = add_key_dialog.get_selected_key()
                if new_key:
                    # La validación de duplicados ya la hace el AddKeyDialog
                    key_def = KEY_DEFINITIONS.get(new_key.lower())
                    new_value = key_def["default"] if key_def else ""

                    current_block[new_key] = new_value
                    
                    # Actualizar la visualización del bloque actual para mostrar la nueva clave en el orden correcto
                    self.display_selected_block(current_block_idx)
                    
                    # Encontrar la nueva fila para la clave añadida y seleccionarla
                    for r in range(self.key_value_table.rowCount()):
                        key_widget = self.key_value_table.cellWidget(r, 0)
                        if isinstance(key_widget, QComboBox) and key_widget.currentText() == new_key:
                            self.key_value_table.setCurrentCell(r, 0) # Seleccionar la nueva fila
                            break

                    self.update_json_preview()
                    self._show_status_message(f"Clave \'{new_key}\' añadida al bloque {current_block_idx + 1}. ✨")
                else:
                    self._show_status_message("No se seleccionó ninguna clave para añadir. 🤔")
            else:
                self._show_status_message("Operación \'Añadir Clave\' cancelada. 🚫")
        except Exception as e:
            QMessageBox.critical(self, "Error al Añadir Clave", f"Error inesperado al añadir una nueva clave al bloque: {e} 💥")
            print(f"ERROR: Error al añadir nueva clave al bloque: {e}")

    def remove_selected_key_from_block(self):
        current_block_idx = self.get_current_block_index()
        if current_block_idx < 0:
            QMessageBox.warning(self, "Eliminar Clave", "Selecciona un bloque primero. ⚠️")
            print("ADVERTENCIA: Intento de eliminar clave sin bloque seleccionado.")
            return

        selected_row = self.key_value_table.currentRow()
        if selected_row >= 0:
            try:
                key_combo = self.key_value_table.cellWidget(selected_row, 0)
                if isinstance(key_combo, QComboBox):
                    key_to_remove = key_combo.currentText()
                    reply = QMessageBox.question(self, "Eliminar Clave",
                                                 f"¿Estás seguro de que quieres eliminar la clave \'{key_to_remove}\'? 🗑️",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        del self.json_data[current_block_idx][key_to_remove]
                        # Después de modificar los datos, actualizar la visualización del bloque actual
                        self.display_selected_block(current_block_idx) 
                        self.update_json_preview()
                        self._show_status_message(f"Clave \'{key_to_remove}\' eliminada. ✔️")
                else:
                    QMessageBox.warning(self, "Eliminar Clave", "La celda seleccionada no contiene una clave válida. 🚫")
                    print("ADVERTENCIA: Intento de eliminar clave de una celda no válida.")
            except Exception as e:
                QMessageBox.critical(self, "Error al Eliminar Clave", f"Error inesperado al eliminar la clave seleccionada: {e} 💥")
                print(f"ERROR: Error al eliminar clave seleccionada: {e}")
        else:
            QMessageBox.warning(self, "Eliminar Clave", "Selecciona una fila para eliminar. ⚠️")
            print("ADVERTENCIA: Intento de eliminar clave sin selección.")

    def _rename_key_in_block(self, row_in_table, old_key, new_key):
        current_block_idx = self.get_current_block_index()
        if current_block_idx < 0:
            print(f"ADVERTENCIA: Intento de renombrar clave sin bloque seleccionado. Ignorado. (Old: {old_key}, New: {new_key})")
            return

        current_block = self.json_data[current_block_idx]
        
        combo = self.key_value_table.cellWidget(row_in_table, 0)
        if not isinstance(combo, QComboBox):
            print(f"ERROR: Widget de clave inesperado en la fila {row_in_table}. Se esperaba QComboBox. 🐞")
            self._show_status_message(f"Error interno: Widget de clave inesperado en la fila {row_in_table}. 🐞")
            return

        # Bloquear señales para evitar recursión al establecer el texto programáticamente
        combo.blockSignals(True)

        if old_key == new_key: # No hay cambio real en el texto de la clave
            combo.blockSignals(False) # Desbloquear
            self._show_status_message(f"No hay cambio de clave \'{old_key}\'. 🤔")
            return

        normalized_new_key = new_key.lower() # Asegurarse de comparar con la versión normalizada
        normalized_old_key = old_key.lower()

        # Comprobar si la nueva clave (normalizada) ya existe y no es la misma que la antigua (normalizada)
        if normalized_new_key in [k.lower() for k in current_block.keys()] and normalized_new_key != normalized_old_key:
            QMessageBox.warning(self, "Cambiar Clave", f"La clave \'{new_key}\' ya existe en este bloque. No se puede renombrar. ⚠️")
            combo.setCurrentText(old_key) # Revertir al texto original en el ComboBox
            combo.blockSignals(False) # Desbloquear
            self._show_status_message(f"Error: La clave \'{new_key}\' ya existe. No se pudo renombrar. ❌")
            print(f"ERROR: Intento de renombrar clave a \'{new_key}\', que ya existe.")
            return

        try:
            value = current_block.pop(old_key)
            
            # --- CORRECCIÓN V5: INTENTO DE CONVERSIÓN DE TIPO AL RENOMBRAR CLAVE ---
            new_key_def = KEY_DEFINITIONS.get(normalized_new_key)
            if new_key_def:
                target_type = new_key_def["type"]
                default_value = new_key_def["default"]

                converted_value = value
                conversion_needed = False

                if target_type == "int":
                    if not isinstance(value, int):
                        try:
                            converted_value = int(value)
                            conversion_needed = True
                        except (ValueError, TypeError):
                            converted_value = default_value
                            conversion_needed = True
                            print(f"ADVERTENCIA: Fallo en conversión de tipo para '{new_key}'. Valor '{value}' no compatible con entero. Usando por defecto: {default_value}.")
                elif target_type == "list_string":
                    if not isinstance(value, list):
                        # Si el valor anterior no era una lista, intentar convertirlo a una lista con un solo elemento o usar el valor por defecto
                        converted_value = [str(value)] if value not in (None, "", []) else list(default_value) 
                        conversion_needed = True
                        print(f"ADVERTENCIA: Fallo en conversión de tipo para '{new_key}'. Valor '{value}' no compatible con lista. Inicializado como: {converted_value}.")
                    else: # Asegurarse de que todos los elementos de la lista sean strings
                        if not all(isinstance(item, str) for item in value):
                            converted_value = [str(item) for item in value]
                            conversion_needed = True
                            print(f"ADVERTENCIA: Algunos elementos de la lista de '{old_key}' no eran strings. Convertidos para '{new_key}'.")
                elif target_type == "object":
                    if not isinstance(value, dict):
                        try:
                            # Si es un string que parece JSON, intentar cargarlo
                            if isinstance(value, str):
                                temp_obj = json.loads(value)
                                if isinstance(temp_obj, dict):
                                    converted_value = temp_obj
                                    conversion_needed = True
                                else:
                                    raise ValueError("String no es un objeto JSON.")
                            else:
                                raise TypeError("No es un diccionario o string JSON.")
                        except (json.JSONDecodeError, ValueError, TypeError):
                            converted_value = default_value
                            conversion_needed = True
                            print(f"ADVERTENCIA: Fallo en conversión de tipo para '{new_key}'. Valor '{value}' no compatible con objeto JSON. Usando por defecto: {default_value}.")
                elif target_type == "string":
                    converted_value = str(value) # Siempre es convertible a string
                    if not isinstance(value, str): # Solo marcar si hubo una conversión real
                        conversion_needed = True

                if conversion_needed:
                    QMessageBox.warning(self, "Conversión de Tipo", 
                                        f"El valor de la clave \'{old_key}\' fue convertido o restablecido al renombrar a \'{new_key}\' para coincidir con el tipo esperado ({target_type}). Detalles en la consola. 🔄")
                    self._show_status_message(f"Conversión de tipo para \'{new_key}\' realizada. 🔄")

                current_block[new_key] = converted_value
            else: # Si no se encuentra la definición de la nueva clave, mantener el valor tal cual.
                current_block[new_key] = value

            # IMPORANTE: Después de modificar los datos subyacentes, refrescar completamente la visualización del bloque actual.
            self.display_selected_block(current_block_idx) 
            
            found_new_key_row = -1
            for r in range(self.key_value_table.rowCount()):
                key_widget = self.key_value_table.cellWidget(r, 0)
                if isinstance(key_widget, QComboBox) and key_widget.currentText() == new_key:
                    found_new_key_row = r
                    break
            
            if found_new_key_row != -1:
                self.key_value_table.setCurrentCell(found_new_key_row, 0)
            else:
                self._show_status_message(f"Advertencia: No se pudo localizar la clave \'{new_key}\' después de renombrar para seleccionar. 🧐")
                print(f"ADVERTENCIA: No se pudo localizar \'{new_key}\' después de renombrar.")

            self.update_json_preview()
            self._show_status_message(f"Clave renombrada de \'{old_key}\' a \'{new_key}\'. ✔️")
        except Exception as e:
            QMessageBox.critical(self, "Error al Renombrar Clave", f"Error inesperado al renombrar la clave \'{old_key}\' a \'{new_key}\': {e} 💥")
            print(f"ERROR: Error inesperado al renombrar clave \'{old_key}\' a \'{new_key}\': {e}")
            combo.setCurrentText(old_key) # Intentar revertir en caso de error
        finally:
            combo.blockSignals(False) # Asegurarse de desbloquear las señales


    def new_json_file(self):
        try:
            if self.json_data and not QMessageBox.question(self, "Nuevo JSON",
                                                          "¿Deseas crear un nuevo archivo JSON? Se borrarán todos los bloques y el contenido actual. 🧹",
                                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self._show_status_message("Operación \'Nuevo JSON\' cancelada. 🚫")
                print("INFO: Creación de nuevo JSON cancelada por el usuario.")
                return
            
            self.json_data = []
            self.block_list_widget.clear()
            self.key_value_table.clearContents()
            self.key_value_table.setRowCount(0)
            self.current_file_path = None
            self._update_path_label()
            self.add_new_block() # Iniciar con un bloque vacío
            self.update_json_preview()
            self._show_status_message("Nuevo archivo JSON listo para editar. ✨")
        except Exception as e:
            QMessageBox.critical(self, "Error al Crear Nuevo JSON", f"Error inesperado al iniciar un nuevo archivo JSON: {e} 💥")
            print(f"ERROR: Error al iniciar nuevo archivo JSON: {e}")


    def load_json_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo JSON de Osiris",
                self.default_dir,
                "Archivos JSON de Osiris (*.dev.ai.json);;Archivos JSON (*.json);;Todos los archivos (*.*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        loaded_data = json.loads(content)
                        
                        if not isinstance(loaded_data, list):
                            QMessageBox.critical(self, "Error de Formato", "El archivo JSON debe ser un arreglo (list) de objetos. Formato inválido. ❌")
                            self._show_status_message("Error: Formato JSON inválido. ❌")
                            print(f"ERROR: Archivo \'{os.path.basename(file_path)}\' tiene formato JSON raíz inválido (no es lista).")
                            return
                        
                        normalized_loaded_data = []
                        for block in loaded_data:
                            if not isinstance(block, dict):
                                QMessageBox.critical(self, "Error de Formato", "Cada elemento del arreglo JSON debe ser un objeto (dict). Formato inválido. ❌")
                                self._show_status_message("Error: Formato JSON de bloque inválido. ❌")
                                print(f"ERROR: Archivo \'{os.path.basename(file_path)}\' contiene un bloque con formato JSON inválido (no es diccionario).")
                                return
                            # CORRECCIÓN V5: Normalizar las claves a minúsculas al cargar
                            normalized_block = {k.lower(): v for k, v in block.items()}
                            normalized_loaded_data.append(normalized_block)

                        self.json_data = normalized_loaded_data
                        self.block_list_widget.clear()
                        for i, _ in enumerate(self.json_data):
                            self.block_list_widget.addItem(f"Bloque {i + 1}")
                        
                        if self.json_data:
                            self.block_list_widget.setCurrentRow(0)
                        else:
                            self.key_value_table.setRowCount(0) # Limpiar tabla si no hay bloques
                            self.add_new_block() # Añadir un bloque vacío si el JSON cargado estaba vacío
                        
                        self.current_file_path = file_path
                        self._update_path_label()
                        self.update_json_preview()
                        self._show_status_message(f"Archivo \'{os.path.basename(file_path)}\' cargado correctamente. ✔️")
                except FileNotFoundError:
                    QMessageBox.critical(self, "Error", "Archivo no encontrado. 📂❌")
                    self._show_status_message("Error: Archivo no encontrado. ❌")
                    print(f"ERROR: Archivo no encontrado al cargar: \'{file_path}\'.")
                except json.JSONDecodeError as e:
                    QMessageBox.critical(self, "Error de JSON", f"El archivo \'{os.path.basename(file_path)}\' no es un JSON válido:\\\n" + str(e) + " ❌")
                    self._show_status_message(f"Error: JSON mal formado en \'{os.path.basename(file_path)}\'. ❌")
                    print(f"ERROR: JSON mal formado al cargar \'{file_path}\': {e}.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", "Ocurrió un error inesperado al cargar el archivo: " + str(e) + " 💥")
                    self._show_status_message(f"Error al cargar archivo: {e} 💥")
                    print(f"ERROR: Error inesperado al cargar archivo \'{file_path}\': {e}.")
            else:
                self._show_status_message("Carga de archivo JSON cancelada. 🚫")
                print("INFO: Carga de archivo JSON cancelada por el usuario.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Diálogo", f"Error al abrir el diálogo de carga de archivo: {e} 💥")
            print(f"ERROR: Error al abrir diálogo de carga de archivo: {e}.")


    def save_json_file(self):
        try:
            if self.current_file_path:
                self._do_save(self.current_file_path)
            else:
                self.save_json_file_as()
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"Error inesperado al guardar el archivo: {e} 💥")
            print(f"ERROR: Error inesperado en save_json_file: {e}.")

    def save_json_file_as(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar archivo JSON Como",
                os.path.join(self.default_dir, "new_context.dev.ai.json"),
                "Archivos JSON de Osiris (*.dev.ai.json);;Archivos JSON (*.json);;Todos los archivos (*.*)"
            )
            if file_path:
                self._do_save(file_path)
            else:
                self._show_status_message("Guardar como... cancelado. 🚫")
                print("INFO: Guardar como... cancelado por el usuario.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Diálogo", f"Error al abrir el diálogo \'Guardar Como\': {e} 💥")
            print(f"ERROR: Error al abrir diálogo \'Guardar Como\': {e}.")

    def _do_save(self, file_path):
        if not self.json_data:
            QMessageBox.warning(self, "Advertencia", "No hay bloques de contexto para guardar. 🚫")
            self._show_status_message("Advertencia: No se guardó un archivo vacío. 🚫")
            print("ADVERTENCIA: Intento de guardar archivo vacío.")
            return

        try:
            # Ordenar las claves de cada bloque antes de serializar para una salida consistente
            ordered_json_data = []
            for block in self.json_data:
                ordered_block = {}
                sorted_keys = sorted(block.keys(), key=lambda k: CANONICAL_KEY_ORDER.index(k.lower()) if k.lower() in CANONICAL_KEY_ORDER else len(CANONICAL_KEY_ORDER))
                for key in sorted_keys:
                    ordered_block[key] = block[key]
                ordered_json_data.append(ordered_block)

            formatted_content = json.dumps(ordered_json_data, indent=2, ensure_ascii=False)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            self.current_file_path = file_path
            self._update_path_label()
            self._show_status_message("Archivo \'" + os.path.basename(file_path) + "\' guardado correctamente. ✅")
            QMessageBox.information(self, "Éxito", "Archivo guardado en:\n" + file_path + " ✨")
            print(f"INFO: Archivo \'{file_path}\' guardado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", "Ocurrió un error inesperado al guardar el archivo: " + str(e) + " 💥")
            self._show_status_message("Error al guardar archivo: " + str(e) + " 💥")
            print(f"ERROR: Error inesperado al guardar archivo \'{file_path}\': {e}.")


    def validate_full_json(self):
        """Valida si el contenido JSON actual es bien formado."""
        if not self.json_data:
            self._show_status_message("No hay JSON para validar (lista de bloques vacía). 😕")
            print("INFO: Intento de validar JSON vacío.")
            return
        
        try:
            # Intentar serializar y luego deserializar para una validación completa
            # Ordenar las claves de cada bloque antes de serializar para una validación consistente
            ordered_json_data = []
            for block in self.json_data:
                ordered_block = {}
                sorted_keys = sorted(block.keys(), key=lambda k: CANONICAL_KEY_ORDER.index(k.lower()) if k.lower() in CANONICAL_KEY_ORDER else len(CANONICAL_KEY_ORDER))
                for key in sorted_keys:
                    ordered_block[key] = block[key]
                ordered_json_data.append(ordered_block)

            temp_json_str = json.dumps(ordered_json_data, ensure_ascii=False)
            json.loads(temp_json_str)
            self._show_status_message("JSON válido. ✅")
            QMessageBox.information(self, "Validación Exitosa", "El documento JSON completo es válido. ✨")
            print("INFO: Validación de JSON completa exitosa.")
        except json.JSONDecodeError as e:
            self._show_status_message("JSON mal formado: " + str(e) + " ❌")
            QMessageBox.critical(self, "Error de Validación", "El documento JSON completo no es válido:\n" + str(e) + " ❌")
            print(f"ERROR: Validación de JSON fallida: {e}.")
        except Exception as e:
            self._show_status_message("Error inesperado durante la validación: " + str(e) + " 💥")
            QMessageBox.critical(self, "Error de Validación", "Error inesperado durante la validación:\n" + str(e) + " 💥")
            print(f"ERROR: Error inesperado durante la validación de JSON: {e}.")

    def insert_template(self):
        try:
            if self.json_data and not QMessageBox.question(self, "Insertar Plantilla",
                                                          "¿Deseas insertar la plantilla? Esto reemplazará todos los bloques y el contenido actual. 🔄",
                                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self._show_status_message("Inserción de plantilla cancelada. 🚫")
                print("INFO: Inserción de plantilla cancelada por el usuario.")
                return

            now_utc = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
            template_data = [
                {
                    "human": "Este es un bloque de instrucciones humanas para la IA, describiendo la tarea o el contexto general. Por ejemplo: 'Analiza el código Python proporcionado y sugiereme mejoras de rendimiento.'",
                    "aiinstruction": "Procesar la información de los archivos adjuntos y generar un resumen técnico detallado, resaltando las dependencias, funcionalidades clave y posibles vulnerabilidades.",
                    "metadata": {
                        "project_name": "EjemploOsirisProject",
                        "version": "1.0.0",
                        "author": "UsuarioOsiris",
                        "date": now_utc,
                        "description": "Plantilla de configuración para el análisis de un proyecto de software con Osiris AI."
                    },
                    "readfile": [
                        "ruta/al/archivo_principal.py",
                        "ruta/al/config.ini"
                    ],
                    # CORRECCIÓN v7: readDirectoryFiles ahora es una lista de rutas
                    "readdirectoryfiles": ["ruta/al/directorio_de_configuracion_1/", "ruta/al/otro_directorio_de_configuracion/"], 
                    # CORRECCIÓN v7: readdirectoryfilesRecursive ahora es una lista de rutas
                    "readdirectoryfilesrecursive": ["ruta/al/directorio_de_codigo_fuente_1/", "ruta/al/otro_directorio_de_codigo_fuente/"],
                    "readdirectorypaths": ["ruta/al/directorio_de_documentos/"],
                    "readdirectorypathrecursive": ["ruta/al/directorio_de_assets_o_librerias/"],
                    "filterincludeextensions": [".py", ".json", ".md", ".txt"],
                    "filterexcludepatterns": ["*/__pycache__/*", "*.log", "node_modules/**"]
                },
                {
                    "maxcontexttokens": 500000,
                    "responseformat": "Markdown",
                    "fileencoding": "utf-8"
                }
            ]
            self.json_data = template_data
            self.block_list_widget.clear()
            for i, _ in enumerate(self.json_data):
                self.block_list_widget.addItem(f"Bloque {i + 1}")
            self.block_list_widget.setCurrentRow(0)
            self.update_json_preview()
            self._show_status_message("Plantilla de contexto Osiris insertada. Modifícala a tu gusto. 🎨")
            print("INFO: Plantilla de contexto Osiris insertada.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Insertar Plantilla", f"Error inesperado al insertar la plantilla: {e} 💥")
            print(f"ERROR: Error al insertar plantilla: {e}.")


def main():
    app = QApplication(sys.argv)
    editor = OsirisJsonBuilderQt()
    editor.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()