#!/bin/env python3
import sys
import re
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QWidget, QLineEdit,
    QTabWidget, QLabel, QToolButton,
    QPlainTextEdit
)
from PyQt6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont, QSyntaxHighlighter,
    QTextDocument
)
from PyQt6.QtCore import ( # <-- ¡AQUÍ ESTÁ LA CORRECCIÓN CLAVE!
    Qt, QSize,
    QRegularExpression # Importamos QRegularExpression desde QtCore
)


# --- CLASES BASE PARA VENTANAS ASISTENTES ---

class BaseAssistantWindow(QDialog):
    """
    Clase base para ventanas asistentes de PyQt6.
    Configura propiedades comunes como "siempre encima" y tamaño mínimo.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Configurar la ventana para que esté siempre encima
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(QSize(800, 400)) # Tamaño mínimo para las ventanas
        self.resize(800, 600) # Tamaño inicial sugerido

        # Configuración de layout principal para todas las ventanas asistentes
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

    def _setup_text_widget_context_menu(self, text_widget):
        """
        Configura un menú contextual personalizado para un QTextEdit/QPlainTextEdit.
        Añade opciones básicas y "Copiar Todo".
        """
        text_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        text_widget.customContextMenuRequested.connect(
            lambda pos: self._show_text_context_menu(pos, text_widget)
        )

    def _show_text_context_menu(self, pos, text_widget):
        """
        Muestra el menú contextual para el widget de texto.
        """
        menu = text_widget.createStandardContextMenu() # Obtiene el menú por defecto (Copiar, Pegar, Cortar, Deshacer, Rehacer)

        # Añadir opción "Copiar Todo"
        copy_all_action = menu.addAction("Copiar Todo")
        copy_all_action.triggered.connect(text_widget.selectAll)
        copy_all_action.triggered.connect(text_widget.copy)

        menu.exec(text_widget.mapToGlobal(pos))


# --- CLASE PARA RESALTADO DE SINTAXIS (BÁSICO) ---

class CodeHighlighter(QSyntaxHighlighter):
    """
    Resaltador de sintaxis básico para QTextEdit.
    Soporta Python, JavaScript, Bash.
    """
    def __init__(self, document, language):
        super().__init__(document)
        self.highlightingRules = []

        # Formatos de color para diferentes elementos de sintaxis
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))  # Azul claro (como VS Code)
        keyword_format.setFontWeight(QFont.Weight.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))  # Naranja
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))  # Verde grisáceo
        comment_format.setFontItalic(True)

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8")) # Verde claro (números)

        # Palabras clave y patrones específicos por lenguaje
        keywords = []
        comment_pattern = ""

        if language.lower() in ["python", "py"]:
            keywords = ["def", "class", "import", "from", "as", "if", "elif", "else", 
                        "for", "while", "in", "is", "not", "and", "or", "return", 
                        "True", "False", "None", "try", "except", "finally", "with", "as", "lambda"]
            comment_pattern = r"#[^\n]*"
        elif language.lower() in ["javascript", "js", "json", "ts"]:
            keywords = ["function", "var", "let", "const", "if", "else", "for", "while", 
                        "return", "true", "false", "null", "class", "import", "export", 
                        "this", "new", "async", "await", "break", "continue", "debugger", 
                        "do", "enum", "extends", "super", "switch", "case", "default", "typeof", "void"]
            comment_pattern = r"//[^\n]*"
        elif language.lower() in ["bash", "sh"]:
            keywords = ["function", "if", "then", "else", "fi", "for", "do", "done", 
                        "while", "read", "echo", "return", "case", "esac", "select", 
                        "until", "local", "export", "set"]
            comment_pattern = r"#[^\n]*"
        elif language.lower() == "html":
            keywords = ["html", "head", "body", "div", "span", "p", "a", "img", "script", "style", "link", "meta", "title"]
            string_format.setForeground(QColor("#9cdcfe")) # Azul claro para atributos
            comment_pattern = r"<!--.*?-->" # Comentarios HTML
        elif language.lower() == "css":
            keywords = ["background", "color", "font-size", "margin", "padding", "border", "display", "position", "width", "height"]
            string_format.setForeground(QColor("#ffd700")) # Amarillo para valores css
            comment_pattern = r"/\*.*?\*/" # Comentarios CSS
        
        # Regla: Palabras clave
        for word in keywords:
            pattern = r"\b" + word + r"\b"
            self.highlightingRules.append((QRegularExpression(pattern), keyword_format)) # Usamos QRegularExpression

        # Regla: Cadenas (comillas simples y dobles)
        self.highlightingRules.append((QRegularExpression(r"\".*\""), string_format)) # Usamos QRegularExpression
        self.highlightingRules.append((QRegularExpression(r"\'.*\'"), string_format)) # Usamos QRegularExpression

        # Regla: Números
        self.highlightingRules.append((QRegularExpression(r"\b[0-9]+\b"), number_format)) # Usamos QRegularExpression
        self.highlightingRules.append((QRegularExpression(r"\b[0-9]*\.[0-9]+\b"), number_format)) # Usamos QRegularExpression

        # Regla: Comentarios (para un solo tipo de comentario, o adaptable si se puede)
        if comment_pattern:
            self.highlightingRules.append((QRegularExpression(comment_pattern), comment_format)) # Usamos QRegularExpression
        
        # Multi-line comments (simple approach, for full support need more complex block handling)
        if language.lower() in ["javascript", "js", "ts", "css"]:
            multi_comment_start_expression = QRegularExpression(r"/\*") # Usamos QRegularExpression
            multi_comment_end_expression = QRegularExpression(r"\*/") # Usamos QRegularExpression
            
            self.highlightingRules.append((multi_comment_start_expression, comment_format))
            self.highlightingRules.append((multi_comment_end_expression, comment_format))


    def highlightBlock(self, text):
        """
        Aplica el resaltado a un bloque de texto (una línea).
        """
        for expression, format in self.highlightingRules: # 'expression' es ahora QRegularExpression
            # Usamos QRegularExpressionMatchIterator para encontrar todas las coincidencias
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)
        
        # Reiniciar el estado del bloque (importante para comentarios multilínea si se implementan bien)
        self.setCurrentBlockState(0) 


# --- CLASE PARA LA VENTANA DE VISUALIZACIÓN DE CÓDIGO ---

class CodeViewerWindow(BaseAssistantWindow):
    """
    Ventana dedicada a la visualización de un bloque de código extraído.
    Incluye resaltado de sintaxis y opción de guardar.
    """
    def __init__(self, code_text, language, parent=None):
        super().__init__(parent)
        self.code_text = code_text
        self.language = language
        self.setWindowTitle(f"Código - {language.capitalize()}")
        self._init_ui()
        self._setup_text_widget_context_menu(self.code_widget) # Configura el menú contextual

    def _init_ui(self):
        # Widget para mostrar el código
        self.code_widget = QTextEdit(self)
        self.code_widget.setReadOnly(False) # Permitir edición del código extraído
        self.code_widget.setFont(QFont("Consolas", 12))
        self.code_widget.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap) # No word wrap para código
        self.code_widget.setText(self.code_text)
        self.main_layout.addWidget(self.code_widget)

        # Aplicar resaltado de sintaxis
        self.highlighter = CodeHighlighter(self.code_widget.document(), self.language)

        # Frame de botones
        button_frame_code = QHBoxLayout()
        
        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self._save_code)
        
        self.copy_all_button = QPushButton("Copiar Todo", self)
        self.copy_all_button.clicked.connect(self.code_widget.selectAll)
        self.copy_all_button.clicked.connect(self.code_widget.copy)

        self.close_button = QPushButton("Cerrar", self)
        self.close_button.clicked.connect(self.close)

        button_frame_code.addWidget(self.save_button)
        button_frame_code.addWidget(self.copy_all_button)
        button_frame_code.addStretch(1) # Empuja los botones a la izquierda
        button_frame_code.addWidget(self.close_button)
        self.main_layout.addLayout(button_frame_code)

    def _save_code(self):
        """
        Guarda el contenido del código en un archivo.
        Sugiere la extensión basada en el lenguaje.
        """
        # Obtenemos el texto actual del widget, por si el usuario lo editó
        current_code = self.code_widget.toPlainText()

        # Mapeo de lenguajes a extensiones para el diálogo de guardar
        extension_map = {
            "python": ".py", "py": ".py",
            "javascript": ".js", "js": ".js", "ts": ".ts", "json": ".json",
            "bash": ".sh", "sh": ".sh",
            "html": ".html", "css": ".css",
            # Añade más si lo necesitas
        }
        default_ext = extension_map.get(self.language.lower(), ".txt")
        file_filter = f"{self.language.capitalize()} files (*{default_ext});;All files (*.*)"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Código", "", file_filter
        )
        if filename:
            try:
                with open(filename, "w", encoding='utf-8') as f:
                    f.write(current_code)
                QMessageBox.information(self, "Guardado Exitoso", f"Código guardado en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo:\n{e}")


# --- CLASE PRINCIPAL DE VISUALIZACIÓN DE RESPUESTAS ---

class ResponseViewerWindow(BaseAssistantWindow):
    """
    Ventana principal para mostrar y procesar la respuesta de la IA.
    Incluye guardar, extraer código, modos de visualización y búsqueda.
    """
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contenido de la conversación")
        self.original_text = text # Almacenamos el texto original para los cambios de vista
        self._init_ui()
        self._setup_text_widget_context_menu(self.text_widget) # Configura el menú contextual

    def _init_ui(self):
        # Widget de texto principal
        self.text_widget = QTextEdit(self)
        self.text_widget.setReadOnly(False) # Permitir al usuario editar la respuesta
        self.text_widget.setFont(QFont("Consolas", 12))
        self.text_widget.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth) # Wrap de palabras
        self.main_layout.addWidget(self.text_widget)

        # Establecer el texto inicial como texto plano (por defecto)
        self._set_view_mode("plain")

        # Layout para los botones de modos de visualización
        self._add_view_mode_buttons()

        # Layout para la barra de búsqueda
        self._add_search_bar()

        # Layout de botones principal de la ventana
        self._add_main_buttons()

    def _add_view_mode_buttons(self):
        """Añade botones para cambiar el modo de visualización del texto."""
        view_mode_layout = QHBoxLayout()
        view_mode_layout.addWidget(QLabel("Ver como:"))

        self.plain_text_button = QPushButton("Texto Plano")
        self.plain_text_button.clicked.connect(lambda: self._set_view_mode("plain"))
        view_mode_layout.addWidget(self.plain_text_button)

        self.markdown_button = QPushButton("Markdown")
        self.markdown_button.clicked.connect(lambda: self._set_view_mode("markdown"))
        view_mode_layout.addWidget(self.markdown_button)

        self.html_button = QPushButton("HTML")
        self.html_button.clicked.connect(lambda: self._set_view_mode("html"))
        view_mode_layout.addWidget(self.html_button)

        view_mode_layout.addStretch(1) # Espacio para empujar los botones a la izquierda
        self.main_layout.addLayout(view_mode_layout)

    def _set_view_mode(self, mode):
        """Cambia el modo de visualización del QTextEdit."""
        # Se usa el texto original para evitar problemas de renderizado al cambiar entre modos.
        if mode == "plain":
            self.text_widget.setPlainText(self.original_text)
        elif mode == "markdown":
            self.text_widget.setMarkdown(self.original_text)
        elif mode == "html":
            self.text_widget.setHtml(self.original_text)
        
        # Desactivar edición en modos de visualización que no sean texto plano si es necesario
        # self.text_widget.setReadOnly(mode != "plain") 
        
        # Opcional: Podrías deshabilitar o habilitar resaltado si tienes un resaltador para la vista principal
        # Esto es más complejo y no lo implementaremos para "frugal" aquí.

    def _add_search_bar(self):
        """Añade una barra de búsqueda y botones de navegación."""
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Introduce texto a buscar...")
        self.search_input.returnPressed.connect(self._find_next_occurrence) # Buscar al presionar Enter
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Buscar", self)
        self.search_button.clicked.connect(self._find_next_occurrence)
        search_layout.addWidget(self.search_button)
        
        self.search_prev_button = QToolButton(self)
        self.search_prev_button.setText("▲")
        self.search_prev_button.setToolTip("Buscar anterior")
        self.search_prev_button.clicked.connect(lambda: self._find_next_occurrence(direction=False))
        search_layout.addWidget(self.search_prev_button)

        self.search_next_button = QToolButton(self)
        self.search_next_button.setText("▼")
        self.search_next_button.setToolTip("Buscar siguiente")
        self.search_next_button.clicked.connect(lambda: self._find_next_occurrence(direction=True))
        search_layout.addWidget(self.search_next_button)

        self.main_layout.addLayout(search_layout)

    def _find_next_occurrence(self, direction=True):
        """Busca la siguiente/anterior ocurrencia del texto."""
        query = self.search_input.text()
        if not query:
            return

        flags = QTextDocument.FindFlag(0)
        if not direction:
            flags |= QTextDocument.FindFlag.FindBackward

        # Reset cursor position if a new search starts
        if self.text_widget.textCursor().selectedText() != query:
            cursor = self.text_widget.textCursor()
            cursor.setPosition(0) # Start from beginning
            self.text_widget.setTextCursor(cursor)

        found = self.text_widget.find(query, flags)

        if not found:
            QMessageBox.information(self, "Buscar", f"No se encontró '{query}'.")
            # Opcional: volver al inicio/final para una búsqueda cíclica
            cursor = self.text_widget.textCursor()
            cursor.setPosition(0 if direction else self.text_widget.document().characterCount())
            self.text_widget.setTextCursor(cursor)
            if self.text_widget.find(query, flags): # Try again from start/end
                QMessageBox.information(self, "Buscar", f"Se ha reiniciado la búsqueda. Encontrado '{query}'.")


    def _add_main_buttons(self):
        """Añade los botones principales (Guardar, Extraer Código, Cerrar)."""
        main_button_frame = QHBoxLayout()
        
        self.save_button = QPushButton("Guardar como...", self)
        self.save_button.clicked.connect(self._save_text_to_file)
        main_button_frame.addWidget(self.save_button)

        self.extract_button = QPushButton("Extraer Código", self)
        self.extract_button.clicked.connect(self._handle_extract_code)
        main_button_frame.addWidget(self.extract_button)

        # Separador flexible para alinear "Cerrar" a la derecha
        main_button_frame.addStretch(1) 

        self.close_button = QPushButton("Cerrar", self)
        self.close_button.clicked.connect(self.close) # El método close() de QDialog cierra la ventana
        main_button_frame.addWidget(self.close_button)

        self.main_layout.addLayout(main_button_frame)

    def _save_text_to_file(self):
        """
        Guarda el contenido actual del widget de texto en un archivo.
        """
        # Obtenemos el texto actual del widget, por si el usuario lo editó
        current_text = self.text_widget.toPlainText()

        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Contenido", "", "Archivos de texto (*.txt);;Todos los archivos (*.*)"
        )
        if filename:
            try:
                with open(filename, "w", encoding='utf-8') as f:
                    f.write(current_text)
                QMessageBox.information(self, "Guardado Exitoso", f"Contenido guardado en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo:\n{e}")

    def _extract_code_blocks(self, text):
        """
        Extrae bloques de código del texto usando expresiones regulares.
        Soporta bloques Markdown con especificación de lenguaje (```python\n...\n```).
        """
        code_blocks = []
        # Patrón para Markdown de bloques de código: ```lang\ncode\n```
        pattern = r"```(\w+)\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        for language, code in matches:
            code_blocks.append({"language": language.strip(), "code": code.strip()})
        return code_blocks

    def _handle_extract_code(self):
        """
        Maneja la extracción de código y abre ventanas separadas para cada bloque.
        """
        # Usamos el texto actual del widget, por si el usuario lo editó
        current_text = self.text_widget.toPlainText()
        code_blocks = self._extract_code_blocks(current_text)

        if code_blocks:
            for block in code_blocks:
                # Pasa self como parent para que las ventanas de código se cierren con la principal
                code_window = CodeViewerWindow(block['code'], block['language'], parent=self)
                code_window.show()
        else:
            QMessageBox.information(self, "Información", "No se encontraron bloques de código en la respuesta.")

# --- FUNCIÓN DE ENTRADA (equivalente a tu `show_text_window`) ---

def show_ai_response_window(text: str):
    """
    Función de utilidad para mostrar la ventana de visualización de respuestas.
    Se asegura de que una QApplication exista.
    """
    app = QApplication.instance() # Intenta obtener una instancia existente
    if not app: # Si no hay ninguna, crea una nueva
        app = QApplication(sys.argv)
    # Crea y muestra la ventana
    viewer_window = ResponseViewerWindow(text)
    viewer_window.exec() # Usar exec() para que sea modal (bloquee hasta que se cierre)
                         # show() lo haría no-modal, pero podría cerrarse si la app principal sale.
    viewer_window.show()

# --- EJEMPLO DE USO ---
if __name__ == '__main__':
    show_ai_response_window(sample_ai_response)

