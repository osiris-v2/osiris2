#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import datetime # Para timestamps en logging y mensajes
import shutil # Para copiar archivos en la creación de ejemplo

from jinja2 import Environment, FileSystemLoader
import markdown # Para convertir Markdown a HTML para la visualización en Qt

# Importar los módulos de PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QTextBrowser, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QLineEdit, QSplitter, QInputDialog, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QUrl # QUrl es útil para abrir enlaces o anclas
from PyQt5.QtGui import QDesktopServices # Para abrir archivos con el programa por defecto

# --- Configuración global y rutas ---
# Path relativo al directorio de ejecución del script
BASE_DOCS_DIR = 'documentation'
TEMPLATES_DIR = os.path.join(BASE_DOCS_DIR, 'templates')
CONFIG_FILE = 'doc_config.json' # Este archivo estará en la raíz del proyecto
OUTPUT_FILE = os.path.join(BASE_DOCS_DIR, 'osiris_documentation.html') # Cambiado a HTML para QTextBrowser
EDITOR_COMMAND = "gedit" # Por defecto a VS Code (con espera), ajusta para tu OS/editor (ej: "gedit", "nano", "subl -w", "notepad.exe")

# Asegurarse de que los directorios base existan
if not os.path.exists(BASE_DOCS_DIR):
    os.makedirs(BASE_DOCS_DIR)
    print(f"Directorio base de documentación '{BASE_DOCS_DIR}' creado. 📂")
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)
    print(f"Directorio de plantillas '{TEMPLATES_DIR}' creado. 📂")

# --- CSS Básico para la Documentación Generada ---
DEFAULT_CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 20px; background-color: #f8f8f8; }
    h1, h2, h3, h4, h5, h6 { color: #2c3e50; margin-top: 1.5em; margin-bottom: 0.5em; }
    h1 { font-size: 2.2em; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { font-size: 1.8em; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
    h3 { font-size: 1.4em; }
    p { margin-bottom: 1em; }
    a { color: #3498db; text-decoration: none; }
    a:hover { text-decoration: underline; }
    code { font-family: 'Consolas', 'Menlo', 'Courier New', monospace; background-color: #eef; padding: 2px 4px; border-radius: 3px; }
    pre { background-color: #eee; border: 1px solid #ddd; padding: 10px; border-radius: 5px; overflow-x: auto; }
    pre code { background-color: transparent; padding: 0; }
    blockquote { border-left: 4px solid #ccc; margin: 1.5em 0; padding: 0.5em 10px; color: #666; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 1em; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    ul, ol { margin-bottom: 1em; padding-left: 20px; }
    hr { border: 0; border-top: 1px solid #eee; margin: 2em 0; }
</style>
"""

# --- Diálogo para Añadir/Editar un Capítulo ---
class ChapterEditDialog(QDialog):
    def __init__(self, parent=None, chapter_data=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Capítulo de Documentación")
        self.setModal(True)
        self.chapter_data = chapter_data if chapter_data is not None else {}
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.title_input = QLineEdit(self.chapter_data.get('titulo', ''))
        layout.addRow("Título del Capítulo:", self.title_input)

        self.id_input = QLineEdit(self.chapter_data.get('id', ''))
        self.id_input.setPlaceholderText("ID único (ej: intro_chapter). Usado para enlaces internos.")
        layout.addRow("ID (para anclas HTML):", self.id_input)

        # Sugerir ruta de plantilla dentro del directorio de plantillas
        default_template_path = self.chapter_data.get('plantilla', os.path.join(TEMPLATES_DIR, "nuevo_capitulo.md"))
        self.template_input = QLineEdit(default_template_path)
        self.template_input.setPlaceholderText(f"Ruta al archivo de plantilla (ej: {TEMPLATES_DIR}/mi_capitulo.md)")
        layout.addRow("Ruta de Plantilla (.md):", self.template_input)

        # Para datos_extra, se podría usar un QTextEdit para JSON, pero lo haremos simple por ahora
        # Si 'datos_extra' es un diccionario, convertirlo a una cadena JSON para mostrar
        extra_data_str = json.dumps(self.chapter_data.get('datos_extra', {}), indent=2)
        self.extra_data_input = QTextEdit(extra_data_str)
        self.extra_data_input.setPlaceholderText("Datos extra para Jinja2 (formato JSON). Ej: {\"version\": \"1.0\"}")
        self.extra_data_input.setMinimumHeight(80)
        layout.addRow("Datos Extra (JSON):", self.extra_data_input)


        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_chapter_data(self):
        try:
            title = self.title_input.text().strip()
            chapter_id = self.id_input.text().strip()
            template_path = self.template_input.text().strip()
            
            # Validar ID: debe ser un identificador HTML válido
            if not chapter_id:
                raise ValueError("El ID del capítulo no puede estar vacío.")
            # Simple validación: solo alfanuméricos, guiones y guiones bajos
            if not all(c.isalnum() or c in ['-', '_'] for c in chapter_id):
                raise ValueError("El ID del capítulo solo puede contener letras, números, guiones y guiones bajos.")
            
            # Validar plantilla: puede ser vacía si no hay contenido, pero si hay, que sea una ruta relativa
            if template_path and not os.path.isabs(template_path) and not template_path.startswith(BASE_DOCS_DIR):
                # Sugerir que la ruta debe ser dentro de BASE_DOCS_DIR si no es absoluta
                # Considera que el usuario puede escribirla como relative_to_TEMPLATES_DIR, o full path
                # Simplificamos: si no es absoluta, la hacemos relativa a BASE_DOCS_DIR
                if not template_path.startswith(TEMPLATES_DIR + os.sep) and not template_path.startswith(os.path.basename(TEMPLATES_DIR) + os.sep):
                    QMessageBox.warning(self, "Ruta de Plantilla",
                                        f"La ruta de la plantilla '{template_path}' parece estar fuera de '{TEMPLATES_DIR}' o no es absoluta. Se recomienda usar rutas relativas a la raíz del script o absolutas. Asegúrate de que Jinja2 pueda encontrarla.")
                
            extra_data_text = self.extra_data_input.toPlainText().strip()
            extra_data = {}
            if extra_data_text:
                try:
                    extra_data = json.loads(extra_data_text)
                    if not isinstance(extra_data, dict):
                        raise ValueError("Los datos extra deben ser un objeto JSON (diccionario).")
                except json.JSONDecodeError:
                    raise ValueError("Los 'Datos Extra' no son un JSON válido.")
                except Exception as e:
                    raise ValueError(f"Error al procesar 'Datos Extra': {e}")

            return {
                "titulo": title,
                "id": chapter_id,
                "plantilla": template_path,
                "datos_extra": extra_data
            }
        except ValueError as e:
            QMessageBox.warning(self, "Error de Entrada", f"Error de validación: {e}")
            return None

# --- Diálogo para Gestionar la Estructura de Capítulos ---
class ChapterManagerDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Gestionar Capítulos de Documentación")
        self.setModal(True)
        self.config = config.copy() # Trabajar con una copia para no modificar la original hasta 'Aceptar'
        self.chapters_list = self.config.get('capitulos', [])
        self.parent_app = parent # Referencia a la ventana principal para log y editor
        self.init_ui()
        self._populate_list()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Input para Título y Autor del Documento Global
        form_layout = QFormLayout()
        self.doc_title_input = QLineEdit(self.config.get('titulo_documento', ''))
        form_layout.addRow("Título del Documento:", self.doc_title_input)
        self.doc_author_input = QLineEdit(self.config.get('autor', ''))
        form_layout.addRow("Autor del Documento:", self.doc_author_input)
        main_layout.addLayout(form_layout)

        main_layout.addWidget(QLabel("<h3>Lista de Capítulos:</h3>"))
        self.chapter_list_widget = QListWidget()
        main_layout.addWidget(self.chapter_list_widget)

        # Botones de acción para capítulos
        chapter_buttons_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Añadir")
        btn_add.clicked.connect(self._add_chapter)
        btn_edit = QPushButton("✏️ Editar")
        btn_edit.clicked.connect(self._edit_chapter)
        btn_remove = QPushButton("🗑️ Eliminar")
        btn_remove.clicked.connect(self._remove_chapter)
        btn_move_up = QPushButton("🔼 Subir")
        btn_move_up.clicked.connect(self._move_chapter_up)
        btn_move_down = QPushButton("🔽 Bajar")
        btn_move_down.clicked.connect(self._move_chapter_down)
        btn_open_template = QPushButton("📂 Abrir Plantilla")
        btn_open_template.clicked.connect(self._open_template_file)

        chapter_buttons_layout.addWidget(btn_add)
        chapter_buttons_layout.addWidget(btn_edit)
        chapter_buttons_layout.addWidget(btn_remove)
        chapter_buttons_layout.addStretch(1) # Espacio flexible
        chapter_buttons_layout.addWidget(btn_move_up)
        chapter_buttons_layout.addWidget(btn_move_down)
        chapter_buttons_layout.addWidget(btn_open_template)
        main_layout.addLayout(chapter_buttons_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)
        self.resize(800, 600) # Tamaño inicial del diálogo

    def _populate_list(self):
        self.chapter_list_widget.clear()
        for chapter in self.chapters_list:
            display_text = f"{chapter.get('titulo', 'Sin Título')} (ID: {chapter.get('id', 'N/A')})"
            item = QListWidgetItem(display_text)
            # Guardar los datos completos del capítulo en el ítem
            item.setData(Qt.UserRole, chapter)
            self.chapter_list_widget.addItem(item)

    def _add_chapter(self):
        dialog = ChapterEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_chapter_data = dialog.get_chapter_data()
            if new_chapter_data:
                # Validar ID único antes de añadir
                if any(c.get('id') == new_chapter_data['id'] for c in self.chapters_list):
                    QMessageBox.warning(self, "ID Duplicado",
                                        f"Ya existe un capítulo con el ID '{new_chapter_data['id']}'. Por favor, usa un ID único.")
                    return
                self.chapters_list.append(new_chapter_data)
                self._populate_list()
                self.parent_app.statusBar().showMessage(f"Capítulo '{new_chapter_data['titulo']}' añadido. ✔️")

    def _edit_chapter(self):
        selected_item = self.chapter_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Advertencia", "Selecciona un capítulo para editar. ☝️")
            return

        current_chapter_data = selected_item.data(Qt.UserRole).copy() # Editar una copia
        dialog = ChapterEditDialog(self, chapter_data=current_chapter_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_chapter_data = dialog.get_chapter_data()
            if updated_chapter_data:
                # Validar ID único, pero permitiendo que el ID del propio capítulo no cause duplicado
                original_id = current_chapter_data.get('id')
                if any(c.get('id') == updated_chapter_data['id'] and c.get('id') != original_id for c in self.chapters_list):
                    QMessageBox.warning(self, "ID Duplicado",
                                        f"Ya existe otro capítulo con el ID '{updated_chapter_data['id']}'. Por favor, usa un ID único.")
                    return

                idx = self.chapter_list_widget.currentRow()
                if idx != -1:
                    self.chapters_list[idx] = updated_chapter_data
                    self._populate_list()
                    self.chapter_list_widget.setCurrentRow(idx) # Mantener selección
                    self.parent_app.statusBar().showMessage(f"Capítulo '{updated_chapter_data['titulo']}' actualizado. ✏️")

    def _remove_chapter(self):
        selected_item = self.chapter_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Advertencia", "Selecciona un capítulo para eliminar. ☝️")
            return

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar el capítulo '{selected_item.text()}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            idx = self.chapter_list_widget.currentRow()
            if idx != -1:
                removed_chapter = self.chapters_list.pop(idx)
                self._populate_list()
                self.parent_app.statusBar().showMessage(f"Capítulo '{removed_chapter.get('titulo', 'Sin Título')}' eliminado. 🗑️")

    def _move_chapter_up(self):
        idx = self.chapter_list_widget.currentRow()
        if idx > 0:
            chapter = self.chapters_list.pop(idx)
            self.chapters_list.insert(idx - 1, chapter)
            self._populate_list()
            self.chapter_list_widget.setCurrentRow(idx - 1)
            self.parent_app.statusBar().showMessage("Capítulo movido arriba. ⬆️")

    def _move_chapter_down(self):
        idx = self.chapter_list_widget.currentRow()
        if idx < len(self.chapters_list) - 1 and idx != -1:
            chapter = self.chapters_list.pop(idx)
            self.chapters_list.insert(idx + 1, chapter)
            self._populate_list()
            self.chapter_list_widget.setCurrentRow(idx + 1)
            self.parent_app.statusBar().showMessage("Capítulo movido abajo. ⬇️")

    def _open_template_file(self):
        selected_item = self.chapter_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Advertencia", "Selecciona un capítulo para abrir su plantilla. ☝️")
            return
        
        chapter_data = selected_item.data(Qt.UserRole)
        template_path = chapter_data.get('plantilla')

        if not template_path:
            QMessageBox.information(self, "Sin Plantilla", "Este capítulo no tiene una ruta de plantilla especificada. Por favor, edítalo y añade una.")
            return

        abs_template_path = os.path.abspath(template_path)

        # Crear el archivo si no existe
        if not os.path.exists(abs_template_path):
            reply = QMessageBox.question(self, "Crear Plantilla",
                                         f"El archivo '{abs_template_path}' no existe. ¿Quieres crearlo?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(os.path.dirname(abs_template_path), exist_ok=True)
                    with open(abs_template_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {chapter_data.get('titulo', 'Nuevo Capítulo')}\n\n")
                        f.write("<!--\n")
                        f.write("Este es el contenido de tu capítulo. Puedes usar Markdown aquí.\n")
                        f.write("Para inyectar datos del JSON, usa la sintaxis de Jinja2:\n")
                        f.write("Por ejemplo: {{ chapter.id }} o {{ datos_extra.version }}\n")
                        f.write("-->\n\n")
                        f.write("¡Empieza a escribir aquí! 😉")
                    QMessageBox.information(self, "Plantilla Creada",
                                            f"Archivo '{abs_template_path}' creado con contenido básico. 🎉")
                    self.parent_app.statusBar().showMessage(f"Archivo '{abs_template_path}' creado. 🎉")
                except Exception as e:
                    QMessageBox.critical(self, "Error al Crear Archivo",
                                         f"No se pudo crear el archivo '{abs_template_path}': {e}")
                    self.parent_app.statusBar().showMessage(f"❌ Error al crear '{abs_template_path}'.")
                    return
            else:
                self.parent_app.statusBar().showMessage("Operación cancelada. ❌")
                return
        
        self.parent_app.statusBar().showMessage(f"Abriendo '{abs_template_path}' con '{EDITOR_COMMAND}'... 🚀")
        try:
            command = [EDITOR_COMMAND] + [abs_template_path]
            subprocess.run(command, check=True, shell=False) 
            self.parent_app.statusBar().showMessage(f"Editor cerrado para '{abs_template_path}'.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Editor no encontrado",
                                 f"Error: El comando '{EDITOR_COMMAND}' no fue encontrado.\nPor favor, asegúrate de que el editor esté instalado y en tu PATH, o configura otro en el script.")
            self.parent_app.statusBar().showMessage(f"❌ Editor '{EDITOR_COMMAND}' no encontrado.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error de Editor",
                                 f"El editor '{EDITOR_COMMAND}' no pudo abrir el archivo o terminó con un error.\nError: {e}")
            self.parent_app.statusBar().showMessage(f"❌ Error al abrir el editor.")
        except Exception as e:
            QMessageBox.critical(self, "Error Inesperado",
                                 f"Ocurrió un error inesperado al intentar abrir el editor: {e}")
            self.parent_app.statusBar().showMessage(f"⚠️ Error inesperado al abrir editor.")
        
        # Después de editar, preguntar si desea regenerar la documentación
        reply_refresh = QMessageBox.question(self, "Plantilla Editada",
                                             "¿Deseas regenerar la documentación ahora para ver los cambios?",
                                             QMessageBox.Yes | QMessageBox.No)
        if reply_refresh == QMessageBox.Yes:
            # Si el editor se cerró y el usuario quiere refrescar, se pasa la señal a la app principal
            # NOTA: Esto hará que la app principal recargue la config *de nuevo* y regenere
            # Por eso es importante que este diálogo guarde antes de salir si cambia algo.
            self.parent_app.generate_documentation_and_display()

    def get_updated_config(self):
        # Actualiza los valores de título y autor del documento global
        self.config['titulo_documento'] = self.doc_title_input.text().strip()
        self.config['autor'] = self.doc_author_input.text().strip()
        self.config['capitulos'] = self.chapters_list
        return self.config

# --- Interfaz de Usuario Principal ---
class OsirisDocApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Osiris Documentador ✨")
        # Establece un tamaño inicial de la ventana
        self.setGeometry(100, 100, 1200, 800) 

        self.config = self.load_config() # Carga la configuración al inicio
        self.create_initial_templates_if_needed() # Asegura que las plantillas de ejemplo existan

        self.init_ui()
        self.generate_documentation_and_display() # Genera y muestra la doc. al iniciar

    def init_ui(self):
        # Widget y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Barra Superior con Botones y Búsqueda ---
        top_bar_layout = QHBoxLayout()
        
        btn_generate = QPushButton("Generar Documentación 📖")
        btn_generate.clicked.connect(self.generate_documentation_and_display)
        top_bar_layout.addWidget(btn_generate)

        btn_manage = QPushButton("Gestionar Documentación 📊") # Texto cambiado
        btn_manage.clicked.connect(self.manage_documentation_structure) # Función cambiada
        top_bar_layout.addWidget(btn_manage)

        # Barra de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en la documentación...")
        # Conectar la tecla Enter para iniciar la búsqueda
        self.search_input.returnPressed.connect(lambda: self.search_documentation(forward=True)) 
        top_bar_layout.addWidget(self.search_input)

        btn_search = QPushButton("Buscar 🔍")
        btn_search.clicked.connect(lambda: self.search_documentation(forward=True))
        top_bar_layout.addWidget(btn_search)

        btn_next_match = QPushButton("Siguiente ▶️")
        btn_next_match.clicked.connect(lambda: self.search_documentation(forward=True))
        top_bar_layout.addWidget(btn_next_match)

        btn_prev_match = QPushButton("Anterior ◀️")
        btn_prev_match.clicked.connect(lambda: self.search_documentation(forward=False))
        top_bar_layout.addWidget(btn_prev_match)

        main_layout.addLayout(top_bar_layout)

        # --- Contenido Principal (Navegación | Visor de Documentos) ---
        # QSplitter permite redimensionar los paneles arrastrando
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Panel Izquierdo: Tabla de Contenidos (Navegación)
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabels(["Capítulos"])
        # Conectar el clic de un elemento del árbol para navegar
        self.toc_tree.itemClicked.connect(self.on_toc_item_clicked)
        splitter.addWidget(self.toc_tree)

        # Panel Derecho: Visor de Documentos
        self.doc_viewer = QTextBrowser()
        # Permite que los enlaces externos se abran en el navegador por defecto
        self.doc_viewer.setOpenExternalLinks(True) 
        # Evita que los enlaces internos sean manejados como enlaces externos
        self.doc_viewer.setOpenLinks(False) 
        # Conecta el clic de un ancla (interno) para que el visor salte a ella
        self.doc_viewer.anchorClicked.connect(self.doc_viewer.scrollToAnchor) 
        splitter.addWidget(self.doc_viewer)

        # Establecer tamaños iniciales para los paneles del splitter
        splitter.setSizes([250, 950]) # 250px para el TOC, 950px para el visor

        # Barra de estado para mensajes de información
        self.statusBar().showMessage("Osiris Documentador listo. ✨")

    def load_config(self):
        """Carga la configuración del archivo JSON."""
        if not os.path.exists(CONFIG_FILE):
            QMessageBox.warning(self, "Configuración no encontrada",
                                f"El archivo de configuración '{CONFIG_FILE}' no existe.\n"
                                "Creando un archivo de configuración de ejemplo...")
            # Crear un JSON de ejemplo si no existe
            example_config = {
                "titulo_documento": "Manual de Osiris",
                "autor": "Osiris AI",
                "capitulos": [
                    {
                        "id": "bienvenida",
                        "titulo": "Bienvenida a Osiris Docs",
                        "plantilla": os.path.join(TEMPLATES_DIR, "bienvenida.md"),
                        "datos_extra": {"creado_el": datetime.date.today().isoformat()}
                    },
                    {
                        "id": "primeros_pasos",
                        "titulo": "Primeros Pasos",
                        "plantilla": os.path.join(TEMPLATES_DIR, "primeros_pasos.md")
                    },
                    {
                        "id": "uso_avanzado",
                        "titulo": "Uso Avanzado",
                        "plantilla": os.path.join(TEMPLATES_DIR, "uso_avanzado.md"),
                        "datos_extra": {"version": "2.0"}
                    }
                ]
            }
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(example_config, f, indent=2)
                QMessageBox.information(self, "Configuración creada",
                                        f"Archivo '{CONFIG_FILE}' creado con un ejemplo.\n"
                                        "Puedes gestionarlo desde 'Gestionar Documentación'.")
                self.statusBar().showMessage(f"Archivo '{CONFIG_FILE}' creado con un ejemplo. 😉")
                return example_config
            except Exception as e:
                QMessageBox.critical(self, "Error de Guardado",
                                     f"No se pudo crear el archivo de configuración de ejemplo: {e}")
                self.statusBar().showMessage(f"❌ Error al crear '{CONFIG_FILE}'.")
                return {"capitulos": []} # Devuelve config vacía para evitar fallos

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error de JSON",
                                 f"Error al leer el archivo '{CONFIG_FILE}'. Asegúrate de que es un JSON válido.\nError: {e}")
            self.statusBar().showMessage(f"❌ Error al leer '{CONFIG_FILE}'.")
            return {"capitulos": []} # Devuelve config vacía para evitar fallos
        except Exception as e:
            QMessageBox.critical(self, "Error de Lectura",
                                 f"No se pudo cargar el archivo de configuración '{CONFIG_FILE}': {e}")
            self.statusBar().showMessage(f"❌ Error al cargar '{CONFIG_FILE}'.")
            return {"capitulos": []} # Devuelve config vacía para evitar fallos

    def save_config(self):
        """Guarda la configuración actual en el archivo JSON."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            self.statusBar().showMessage(f"Configuración guardada en '{CONFIG_FILE}'. 💾")
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar Configuración",
                                 f"No se pudo guardar la configuración en '{CONFIG_FILE}': {e}")
            self.statusBar().showMessage(f"❌ Error al guardar configuración.")

    def create_initial_templates_if_needed(self):
        """Crea archivos de plantilla de ejemplo si no existen y están referenciados en la configuración."""
        for chapter in self.config.get('capitulos', []):
            template_path = chapter.get('plantilla')
            if template_path and not os.path.exists(template_path):
                try:
                    # Asegurar que el directorio de la plantilla exista
                    os.makedirs(os.path.dirname(template_path), exist_ok=True)
                    with open(template_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {chapter.get('titulo', 'Nuevo Capítulo')}\n\n")
                        f.write(f"Contenido de ejemplo para el capítulo '{chapter.get('titulo')}'.\n\n")
                        f.write("Puedes usar Jinja2 para inyectar datos:\n")
                        f.write(f"- ID: `{{{{ chapter.id }}}}` (actual: {chapter.get('id', 'N/A')})\n")
                        if chapter.get('datos_extra'):
                            f.write(f"- Datos extra: `{{{{ datos_extra }}}}` (actual: {json.dumps(chapter.get('datos_extra'))})\n")
                        f.write("\n```python\n# Ejemplo de código\nprint('Hola, Osiris!')\n```\n")
                    self.statusBar().showMessage(f"Plantilla de ejemplo creada: '{template_path}'. 📄")
                except Exception as e:
                    self.statusBar().showMessage(f"❌ Error al crear plantilla '{template_path}': {e}")
                    QMessageBox.warning(self, "Error al Crear Plantilla",
                                        f"No se pudo crear la plantilla de ejemplo '{template_path}': {e}")

    def generate_documentation_and_display(self):
        """Genera la documentación completa y la muestra en el visor."""
        self.statusBar().showMessage("🚀 Iniciando la generación de la documentación...")
        self.config = self.load_config() # Recarga la configuración por si ha cambiado

        # Limpiar el TOC existente
        self.toc_tree.clear()

        # Configurar Jinja2 para cargar plantillas desde el directorio 'templates'
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

        document_html_content = []
        document_html_content.append("<!DOCTYPE html>\n<html>\n<head>\n<meta charset='utf-8'>\n")
        document_html_content.append(DEFAULT_CSS) # Añadir el CSS básico
        document_html_content.append(f"<title>{self.config.get('titulo_documento', 'Documentación')}</title>\n</head>\n<body>\n")

        document_html_content.append(f"<h1>{self.config.get('titulo_documento', 'Documentación')}</h1>\n")
        document_html_content.append(f"<p><strong>Autor:</strong> {self.config.get('autor', 'Desconocido')}</p>\n")
        document_html_content.append("<hr>\n\n")

        for i, chapter_data in enumerate(self.config.get('capitulos', [])):
            title = chapter_data.get('titulo', 'Sin Título')
            template_path = chapter_data.get('plantilla') 
            extra_data = chapter_data.get('datos_extra', {})
            
            # Usar el ID del JSON si está presente, sino generar uno para la ancla
            chapter_id = chapter_data.get('id', f"chap_{i+1}") 
            # Asegurar que el ID sea un ID HTML válido (sin espacios, caracteres especiales)
            # Ya debería estar validado en ChapterEditDialog, pero precaución extra
            chapter_id = "".join(c for c in chapter_id if c.isalnum() or c in ['-', '_']).replace(" ", "_")
            if not chapter_id: chapter_id = f"generated_chap_{i+1}" # Fallback si después de limpiar queda vacío

            # Añadir capítulo a la Tabla de Contenidos (TOC)
            toc_item = QTreeWidgetItem(self.toc_tree, [title])
            toc_item.setData(0, Qt.UserRole, chapter_id) # Almacenar el ID del ancla en los datos de usuario del ítem
            
            # Añadir título al documento HTML con un ancla
            document_html_content.append(f"<h2 id='{chapter_id}'>{title}</h2>\n")

            if template_path:
                # La ruta de la plantilla debe ser relativa a TEMPLATES_DIR para Jinja2
                # Convertimos cualquier ruta a relativa a TEMPLATES_DIR
                if os.path.isabs(template_path):
                    relative_template_path_for_jinja = os.path.relpath(template_path, start=TEMPLATES_DIR)
                else:
                    # Si ya es relativa, asumimos que es relativa a BASE_DOCS_DIR (como en el JSON original)
                    # Y luego la hacemos relativa a TEMPLATES_DIR para Jinja2
                    full_path = os.path.join(os.path.dirname(CONFIG_FILE), template_path)
                    relative_template_path_for_jinja = os.path.relpath(full_path, start=TEMPLATES_DIR)

                try:
                    template = env.get_template(relative_template_path_for_jinja)
                    rendered_chapter_md = template.render(chapter=chapter_data, datos_extra=extra_data)
                    
                    chapter_html = markdown.markdown(rendered_chapter_md, extensions=['extra', 'codehilite', 'fenced_code'])
                    document_html_content.append(chapter_html + "\n\n")
                    self.statusBar().showMessage(f"✔️ Capítulo '{title}' procesado.")
                except Exception as e:
                    error_msg = f"<p style='color:red;'>⚠️ <strong>Error al cargar o renderizar la plantilla '{template_path}':</strong> {e}</p>\n\n"
                    document_html_content.append(error_msg)
                    self.statusBar().showMessage(f"❌ Error en '{title}': {e}")
            else:
                document_html_content.append("<p><i>(Sin contenido de plantilla especificado para este capítulo.)</i></p>\n\n")
                self.statusBar().showMessage(f"❗ Capítulo '{title}' no tiene plantilla especificada.")

        document_html_content.append("\n</body>\n</html>")
        full_html_doc = "".join(document_html_content)

        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(full_html_doc)
            self.statusBar().showMessage(f"🎉 Documentación generada con éxito en '{OUTPUT_FILE}' y mostrada en el visor. ✨")
        except Exception as e:
            QMessageBox.critical(self, "Error de Guardado",
                                 f"No se pudo guardar el archivo de documentación en '{OUTPUT_FILE}': {e}")
            self.statusBar().showMessage(f"❌ Error al guardar '{OUTPUT_FILE}'.")

        self.doc_viewer.setHtml(full_html_doc)


    def on_toc_item_clicked(self, item, column):
        """Desplaza el visor de documentos al capítulo/sección seleccionada."""
        anchor_id = item.data(0, Qt.UserRole)
        if anchor_id:
            self.doc_viewer.scrollToAnchor(anchor_id)
            self.statusBar().showMessage(f"Navegando a: {item.text(0)} 🧭")

    def search_documentation(self, forward=True):
        """Busca texto en el visor de documentación y resalta."""
        query = self.search_input.text()
        if not query:
            self.statusBar().showMessage("Por favor, introduce texto para buscar. 🤔")
            return

        flags = QTextBrowser.FindFlags()
        if not forward:
            flags |= QTextBrowser.FindBackward # Si es hacia atrás, añade la bandera

        found = self.doc_viewer.find(query, flags)
        if found:
            self.statusBar().showMessage(f"Encontrado: '{query}'")
        else:
            self.statusBar().showMessage(f"No se encontraron más coincidencias para '{query}'. 🤷‍♂️")
            # Si no se encuentra más, intenta desde el principio/final para "envolver" la búsqueda
            if forward:
                self.doc_viewer.moveCursor(self.doc_viewer.document().textCursor().Start)
            else:
                self.doc_viewer.moveCursor(self.doc_viewer.document().textCursor().End)
            # Intenta buscar de nuevo desde el nuevo cursor
            found_again = self.doc_viewer.find(query, flags)
            if found_again:
                self.statusBar().showMessage(f"Encontrado: '{query}' (continuando búsqueda desde el principio/final).")
            else:
                self.statusBar().showMessage(f"No se encontró '{query}' en la documentación. 😔")


    def manage_documentation_structure(self):
        """Abre un diálogo para gestionar la estructura de la documentación (capítulos)."""
        self.statusBar().showMessage("Abriendo gestor de documentación... 📊")
        
        # Recargar configuración para obtener el estado más reciente
        self.config = self.load_config()

        dialog = ChapterManagerDialog(self, config=self.config)
        if dialog.exec_() == QDialog.Accepted:
            updated_config = dialog.get_updated_config()
            if updated_config:
                self.config = updated_config
                self.save_config() # Guardar los cambios inmediatamente
                self.generate_documentation_and_display() # Regenerar la documentación con la nueva estructura
                self.statusBar().showMessage("Estructura de documentación actualizada y regenerada. ✅")
            else:
                self.statusBar().showMessage("No se aplicaron cambios a la estructura. 🚫")
        else:
            self.statusBar().showMessage("Gestión de documentación cancelada. 👋")

def main():
    app = QApplication(sys.argv)
    window = OsirisDocApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
