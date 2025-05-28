#!/usr/bin/env python3
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
import markdown # Para convertir Markdown a HTML para la visualización en Qt

# Importar los módulos de PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextBrowser, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QLineEdit, QSplitter, QInputDialog, QLabel
)
from PyQt5.QtCore import Qt, QUrl # QUrl es útil para abrir enlaces o anclas
from PyQt5.QtGui import QDesktopServices # Para abrir archivos con el programa por defecto

# --- Configuración global ---
# Path relativo al directorio de ejecución del script
BASE_DOCS_DIR = 'documentation'
TEMPLATES_DIR = os.path.join(BASE_DOCS_DIR, 'templates')
CONFIG_FILE = 'doc_config.json' # Este archivo estará en la raíz del proyecto
OUTPUT_FILE = os.path.join(BASE_DOCS_DIR, 'osiris_documentation.html') # Cambiado a HTML para QTextBrowser
EDITOR_COMMAND = os.getenv('EDITOR', 'code --wait') # Por defecto a VS Code (con espera), ajusta para tu OS/editor

# Asegurarse de que los directorios base existan
if not os.path.exists(BASE_DOCS_DIR):
    os.makedirs(BASE_DOCS_DIR)
    print(f"Directorio base de documentación '{BASE_DOCS_DIR}' creado. 📂")
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)
    print(f"Directorio de plantillas '{TEMPLATES_DIR}' creado. 📂")

class OsirisDocApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Osiris Documentador ✨")
        # Establece un tamaño inicial de la ventana
        self.setGeometry(100, 100, 1200, 800) 

        self.config = self.load_config() # Carga la configuración al inicio

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

        btn_manage = QPushButton("Gestionar Plantillas 📝")
        btn_manage.clicked.connect(self.manage_templates_dialog)
        top_bar_layout.addWidget(btn_manage)

        # Barra de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en la documentación...")
        # Conectar la tecla Enter para iniciar la búsqueda
        self.search_input.returnPressed.connect(self.search_documentation) 
        top_bar_layout.addWidget(self.search_input)

        btn_search = QPushButton("Buscar 🔍")
        btn_search.clicked.connect(self.search_documentation)
        top_bar_layout.addWidget(btn_search)

        btn_next_match = QPushButton("Siguiente ▶️")
        # Usar lambda para pasar argumentos a la función conectada
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
        self.statusBar().showMessage("Osiris listo para documentar. ✨")

    def load_config(self):
        """Carga la configuración del archivo JSON."""
        if not os.path.exists(CONFIG_FILE):
            QMessageBox.warning(self, "Configuración no encontrada",
                                f"El archivo de configuración '{CONFIG_FILE}' no existe.\n"
                                "Creando un archivo de configuración de ejemplo...")
            # Crear un JSON de ejemplo si no existe
            example_config = {
                "titulo_documento": "Manual de Osiris (Ejemplo)",
                "autor": "Osiris AI",
                "capitulos": [
                    {
                        "id": "bienvenida",
                        "titulo": "Bienvenida a Osiris Docs",
                        # La ruta de la plantilla debe ser relativa a la raíz del script
                        "plantilla": os.path.join(TEMPLATES_DIR, "bienvenida.md"),
                        "datos_extra": {"creado_el": "hoy"}
                    },
                    {
                        "id": "primeros_pasos",
                        "titulo": "Primeros Pasos",
                        "plantilla": os.path.join(TEMPLATES_DIR, "primeros_pasos.md")
                    }
                ]
            }
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(example_config, f, indent=2)
                QMessageBox.information(self, "Configuración creada",
                                        f"Archivo '{CONFIG_FILE}' creado con un ejemplo.\n"
                                        "Por favor, edítalo desde el gestor de plantillas.")
                self.statusBar().showMessage(f"Archivo '{CONFIG_FILE}' creado con un ejemplo. 😉")
            except Exception as e:
                QMessageBox.critical(self, "Error de Guardado",
                                     f"No se pudo crear el archivo de configuración de ejemplo: {e}")
                self.statusBar().showMessage(f"❌ Error al crear '{CONFIG_FILE}'.")
            return example_config

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

    def generate_documentation_and_display(self):
        """Genera la documentación completa y la muestra en el visor."""
        self.statusBar().showMessage("🚀 Iniciando la generación de la documentación...")
        self.config = self.load_config() # Recarga la configuración por si ha cambiado

        # Limpiar el TOC existente
        self.toc_tree.clear()

        # Configurar Jinja2 para cargar plantillas desde el directorio 'templates'
        # El FileSystemLoader espera rutas relativas a TEMPLATES_DIR
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

        document_html_content = []
        document_html_content.append(f"<h1>{self.config.get('titulo_documento', 'Documentación')}</h1>\n")
        document_html_content.append(f"<p><strong>Autor:</strong> {self.config.get('autor', 'Desconocido')}</p>\n")
        document_html_content.append("<hr>\n\n")

        for i, chapter_data in enumerate(self.config.get('capitulos', [])):
            title = chapter_data.get('titulo', 'Sin Título')
            template_path = chapter_data.get('plantilla') # Esta ruta es relativa a la raíz del script (e.g. 'documentation/templates/...')
            extra_data = chapter_data.get('datos_extra', {})
            
            # Crear un ID para el ancla HTML, limpiando el título
            # Este ID se usará tanto para el ancla HTML como para los datos del ítem del TOC
            chapter_id = chapter_data.get('id', f"chap_{i+1}") # Usa 'id' del JSON si está, sino genera uno
            # Limpiar chapter_id para que sea un ID HTML válido (sin espacios, caracteres especiales)
            chapter_id = "".join(c for c in chapter_id if c.isalnum() or c in ['-', '_']).replace(" ", "_")
            if not chapter_id: chapter_id = f"chap_{i+1}" # Fallback si después de limpiar queda vacío

            # Añadir capítulo a la Tabla de Contenidos (TOC)
            toc_item = QTreeWidgetItem(self.toc_tree, [title])
            # Almacenar el ID del ancla en los datos de usuario del ítem
            toc_item.setData(0, Qt.UserRole, chapter_id) 
            
            # Añadir título al documento HTML con un ancla
            document_html_content.append(f"<h2 id='{chapter_id}'>{title}</h2>\n")

            if template_path:
                # Asegurarse de que la ruta de la plantilla sea relativa al FileSystemLoader de Jinja2
                # Si TEMPLATES_DIR es 'documentation/templates' y template_path es 'documentation/templates/intro.md'
                # Jinja2 necesita solo 'intro.md'. os.path.relpath hace esto.
                relative_template_path_for_jinja = os.path.relpath(template_path, start=TEMPLATES_DIR)

                try:
                    template = env.get_template(relative_template_path_for_jinja)
                    # Renderizar la plantilla, pasando tanto chapter_data como extra_data
                    rendered_chapter_md = template.render(chapter=chapter_data, datos_extra=extra_data)
                    
                    # Convertir el Markdown renderizado a HTML
                    # Usamos extensiones para mejor formato (tablas, resaltado de código)
                    chapter_html = markdown.markdown(rendered_chapter_md, extensions=['extra', 'codehilite', 'fenced_code'])
                    document_html_content.append(chapter_html + "\n\n")
                    self.statusBar().showMessage(f"✔️ Capítulo '{title}' procesado desde '{template_path}'.")
                except Exception as e:
                    error_msg = f"<p style='color:red;'>⚠️ <strong>Error al cargar o renderizar la plantilla '{template_path}':</strong> {e}</p>\n\n"
                    document_html_content.append(error_msg)
                    self.statusBar().showMessage(f"❌ Error en '{title}': {e}")
            else:
                document_html_content.append("<p><i>(Sin contenido de plantilla especificado)</i></p>\n\n")
                self.statusBar().showMessage(f"❗ Capítulo '{title}' no tiene plantilla especificada.")

        full_html_doc = "".join(document_html_content)

        try:
            # Guardar el HTML generado (útil para ver la documentación en un navegador externo)
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(full_html_doc)
            self.statusBar().showMessage(f"🎉 Documentación generada con éxito en '{OUTPUT_FILE}' y mostrada en el visor. ✨")
        except Exception as e:
            QMessageBox.critical(self, "Error de Guardado",
                                 f"No se pudo guardar el archivo de documentación en '{OUTPUT_FILE}': {e}")
            self.statusBar().showMessage(f"❌ Error al guardar '{OUTPUT_FILE}'.")

        # Mostrar el HTML generado en el QTextBrowser
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
                self.statusBar().showMessage(f"Encontrado: '{query}' (continuando búsqueda).")
            else:
                self.statusBar().showMessage(f"No se encontró '{query}' en la documentación. 😔")


    def manage_templates_dialog(self):
        """Abre un diálogo para gestionar (crear/editar) las plantillas."""
        self.statusBar().showMessage("Abriendo gestor de plantillas... 📝")
        
        # Recargar configuración para obtener el estado más reciente de las plantillas
        self.config = self.load_config()

        templates_info = []
        for chapter_data in self.config.get('capitulos', []):
            template_path = chapter_data.get('plantilla')
            # Asegurarse de que la ruta sea absoluta para os.path.exists y el lanzamiento del editor
            if template_path:
                abs_template_path = os.path.abspath(template_path)
                # Evitar duplicados si varios capítulos usan la misma plantilla
                if abs_template_path not in [info['path'] for info in templates_info]:
                    templates_info.append({
                        "titulo_capitulo": chapter_data.get('titulo', 'Sin Título'),
                        "path": abs_template_path,
                        # Guardar la ruta relativa original para el JSON, si fuera necesario guardar la config.
                        "relative_path_for_json": template_path 
                    })

        # Preparar la lista de ítems para el QInputDialog (texto a mostrar)
        items_display = []
        for i, info in enumerate(templates_info):
            exists_status = "✅ Existe" if os.path.exists(info['path']) else "❌ NO existe"
            items_display.append(f"{info['titulo_capitulo']} ({os.path.basename(info['path'])}) - {exists_status}")
            
        # Añadir una opción explícita para crear una nueva plantilla
        items_display.append("-- CREAR NUEVA PLANTILLA --")

        templates_dialog = QInputDialog(self)
        templates_dialog.setWindowTitle("Gestionar Plantillas de Documentación")
        templates_dialog.setLabelText("Selecciona una plantilla para editar o escribe una nueva ruta:")
        templates_dialog.setComboBoxItems(items_display)
        templates_dialog.setComboBoxEditable(True) # Permite al usuario escribir una ruta personalizada

        # Sugerir una ruta de plantilla dentro del directorio de plantillas
        templates_dialog.setTextValue(os.path.join(TEMPLATES_DIR, "nueva_plantilla.md"))

        ok = templates_dialog.exec_() # Mostrar el diálogo y esperar la interacción del usuario
        if ok:
            selected_input = templates_dialog.textValue() # Obtener el texto seleccionado/introducido
            
            template_file_path = ""
            selected_info_data = None # Para almacenar los datos de la plantilla seleccionada/creada

            if selected_input == "-- CREAR NUEVA PLANTILLA --":
                # Si el usuario eligió crear una nueva plantilla, pedir el nombre del archivo
                new_filename, ok_filename = QInputDialog.getText(self, "Nueva Plantilla",
                                                                  "Introduce el nombre del archivo de la nueva plantilla (ej. mi_capitulo.md):",
                                                                  text="nueva_plantilla.md")
                if not ok_filename or not new_filename:
                    self.statusBar().showMessage("Creación de plantilla cancelada. ❌")
                    return
                
                # Construir la ruta completa dentro de TEMPLATES_DIR
                template_file_path = os.path.abspath(os.path.join(TEMPLATES_DIR, new_filename))
                # Guardar la ruta relativa para el JSON si se fuera a añadir
                relative_path_for_json = os.path.join(TEMPLATES_DIR, new_filename)
                
                # Crear datos para la nueva plantilla
                selected_info_data = {
                    "path": template_file_path,
                    "relative_path_for_json": relative_path_for_json,
                    "titulo_capitulo": os.path.splitext(new_filename)[0].replace('_', ' ').title()
                }

            elif selected_input in items_display: # El usuario seleccionó una plantilla existente de la lista
                idx = items_display.index(selected_input)
                selected_info_data = templates_info[idx]
                template_file_path = selected_info_data['path'] # Ya es una ruta absoluta

            else: # El usuario introdujo una ruta personalizada
                template_file_path = selected_input
                # Resolver a ruta absoluta para operaciones de archivo y lanzamiento del editor
                abs_typed_path = os.path.abspath(template_file_path)
                selected_info_data = {
                    "path": abs_typed_path,
                    "relative_path_for_json": template_file_path, # Mantener la ruta tal como la introdujo el usuario para referencia
                    "titulo_capitulo": os.path.basename(template_file_path)
                }
                template_file_path = abs_typed_path # Usar la ruta absoluta final

            if not template_file_path:
                self.statusBar().showMessage("Ruta de plantilla inválida o vacía. ❌")
                return

            # Crear el archivo si no existe
            if not os.path.exists(template_file_path):
                reply = QMessageBox.question(self, "Crear Plantilla",
                                             f"El archivo '{template_file_path}' no existe. ¿Quieres crearlo?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    try:
                        # Crear el directorio si no existe antes de crear el archivo
                        os.makedirs(os.path.dirname(template_file_path), exist_ok=True)
                        with open(template_file_path, 'w', encoding='utf-8') as f:
                            f.write(f"# {selected_info_data.get('titulo_capitulo', 'Nuevo Capítulo')}\n\n")
                            f.write("<!--\n")
                            f.write("Este es el contenido de tu capítulo. Puedes usar Markdown aquí.\n")
                            f.write("Para inyectar datos del JSON, usa la sintaxis de Jinja2:\n")
                            f.write("Por ejemplo: {{ chapter.id }} o {{ datos_extra.version }}\n")
                            f.write("-->\n\n")
                            f.write("¡Empieza a escribir aquí! 😉")
                        QMessageBox.information(self, "Plantilla Creada",
                                                f"Archivo '{template_file_path}' creado con contenido básico. 🎉")
                        self.statusBar().showMessage(f"Archivo '{template_file_path}' creado. 🎉")
                    except Exception as e:
                        QMessageBox.critical(self, "Error al Crear Archivo",
                                             f"No se pudo crear el archivo '{template_file_path}': {e}")
                        self.statusBar().showMessage(f"❌ Error al crear '{template_file_path}'.")
                        return
                else:
                    self.statusBar().showMessage("Operación cancelada. ❌")
                    return
            
            # Abrir el archivo con el editor externo
            self.statusBar().showMessage(f"Abriendo '{template_file_path}' con '{EDITOR_COMMAND}'... 🚀")
            try:
                # Usar shlex.split no es necesario si el comando no contiene espacios
                # Si el comando tiene espacios (ej: 'C:\\Program Files\\Editor\\editor.exe'), entonces shlex.split sí es útil.
                # Para comandos simples como 'code --wait' o 'nano', una lista simple funciona.
                command = [EDITOR_COMMAND] + [template_file_path]
                # shell=False es más seguro, evita problemas de inyección de comandos
                subprocess.run(command, check=True, shell=False) 
                self.statusBar().showMessage(f"Editor cerrado para '{template_file_path}'.")
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Error de Editor",
                                     f"Error al abrir el editor. Asegúrate de que '{EDITOR_COMMAND}' esté en tu PATH o sea el comando correcto.\nError: {e}")
                self.statusBar().showMessage(f"❌ Error al abrir el editor.")
            except FileNotFoundError:
                QMessageBox.critical(self, "Editor no encontrado",
                                     f"Error: El comando '{EDITOR_COMMAND}' no fue encontrado.\nPor favor, asegúrate de que el editor esté instalado y en tu PATH.")
                self.statusBar().showMessage(f"❌ Editor '{EDITOR_COMMAND}' no encontrado.")
            except Exception as e:
                QMessageBox.critical(self, "Error Inesperado",
                                     f"Ocurrió un error inesperado al intentar abrir el editor: {e}")
                self.statusBar().showMessage(f"⚠️ Error inesperado al abrir editor.")
            
            # Después de editar, preguntar si desea regenerar la documentación
            reply_refresh = QMessageBox.question(self, "Plantilla Editada",
                                                 "¿Deseas regenerar la documentación ahora para ver los cambios?",
                                                 QMessageBox.Yes | QMessageBox.No)
            if reply_refresh == QMessageBox.Yes:
                self.generate_documentation_and_display()
        else:
            self.statusBar().showMessage("Gestión de plantillas cancelada. 👋")


def main():
    app = QApplication(sys.argv)
    window = OsirisDocApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()