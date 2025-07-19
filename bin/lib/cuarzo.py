import sys
import re
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QWidget, QLineEdit,
    QTabWidget, QLabel, QToolButton, QInputDialog, QGridLayout
)
from PyQt6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont, QSyntaxHighlighter,
    QTextDocument
)
from PyQt6.QtCore import (
    Qt, QSize,
    QRegularExpression
)


# --- CLASES BASE PARA VENTANAS ASISTENTES ---

class BaseAssistantWindow(QDialog):
    '''
    Clase base para ventanas asistentes de PyQt6.
    Configura propiedades comunes y tamaño mínimo.
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint) # REMOVED: Now toggleable
        self.setMinimumSize(QSize(800, 400))
        self.resize(800, 600) # Tamaño inicial sugerido

        # Configuración de layout principal para todas las ventanas asistentes
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # Apply modern stylesheet
        self.setStyleSheet('''
            QDialog {
                background-color: #2e2e2e; /* Dark background */
                color: #e0e0e0; /* Light text */
                border: 1px solid #4a4a4a;
            }
            QPushButton {
                background-color: #569cd6; /* VS Code blue */
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #61a9ed;
            }
            QPushButton:pressed {
                background-color: #4a8cd0;
            }
            QLineEdit, QTextEdit {
                background-color: #3e3e3e;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit[readOnly="true"] {
                background-color: #333333; /* Slightly darker for read-only */
                border: 1px solid #444444;
            }
            QLabel {
                color: #b0b0b0;
            }
            QTabWidget::pane { /* The tab widget frame */
                border-top: 2px solid #569cd6;
            }
            QTabBar::tab {
                background: #3e3e3e;
                color: #b0b0b0;
                padding: 8px 15px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #5a5a5a;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: #2e2e2e;
                color: white;
                border-color: #569cd6;
                border-bottom: none;
            }
            QToolButton {
                background-color: #4a4a4a;
                color: #e0e0e0;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #5a5a5a;
            }
        ''')

    def _setup_text_widget_context_menu(self, text_widget):
        '''
        Configura un menú contextual personalizado para un QTextEdit/QPlainTextEdit.
        Añade opciones básicas y "Copiar Todo".
        '''
        text_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        text_widget.customContextMenuRequested.connect(
            lambda pos: self._show_text_context_menu(pos, text_widget)
        )

    def _show_text_context_menu(self, pos, text_widget):
        '''
        Muestra el menú contextual para el widget de texto.
        '''
        menu = text_widget.createStandardContextMenu()

        # Añadir opción "Copiar Todo"
        copy_all_action = menu.addAction("Copiar Todo")
        copy_all_action.triggered.connect(text_widget.selectAll)
        copy_all_action.triggered.connect(text_widget.copy)

        menu.exec(text_widget.mapToGlobal(pos))


# --- CLASE PARA RESALTADO DE SINTAXIS (BÁSICO) ---
class CodeHighlighter(QSyntaxHighlighter):
    '''
    Resaltador de sintaxis básico para QTextEdit.
    Soporta Python, JavaScript, Bash, HTML, CSS.
    '''
    def __init__(self, document, language):
        super().__init__(document)
        self.highlightingRules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        comment_format.setFontItalic(True)

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))

        keywords = []
        comment_pattern = ""
        self.multi_comment_start_expression = None
        self.multi_comment_end_expression = None


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
            self.multi_comment_start_expression = QRegularExpression(r"/\*")
            self.multi_comment_end_expression = QRegularExpression(r"\*/")
        elif language.lower() in ["bash", "sh"]:
            keywords = ["function", "if", "then", "else", "fi", "for", "do", "done", 
                        "while", "read", "echo", "return", "case", "esac", "select", 
                        "until", "local", "export", "set"]
            comment_pattern = r"#[^\n]*"
        elif language.lower() == "html":
            keywords = ["html", "head", "body", "div", "span", "p", "a", "img", "script", "style", "link", "meta", "title"]
            string_format.setForeground(QColor("#9cdcfe"))
            comment_pattern = r"<!--.*?-->"
        elif language.lower() == "css":
            keywords = ["background", "color", "font-size", "margin", "padding", "border", "display", "position", "width", "height"]
            string_format.setForeground(QColor("#ffd700"))
            self.multi_comment_start_expression = QRegularExpression(r"/\*")
            self.multi_comment_end_expression = QRegularExpression(r"\*/")
        
        for word in keywords:
            pattern = r"\b" + word + r"\b"
            self.highlightingRules.append((QRegularExpression(pattern), keyword_format))

        self.highlightingRules.append((QRegularExpression(r"\".*\""), string_format))
        self.highlightingRules.append((QRegularExpression(r"\'.*\'"), string_format))

        self.highlightingRules.append((QRegularExpression(r"\b[0-9]+\b"), number_format))
        self.highlightingRules.append((QRegularExpression(r"\b[0-9]*\.[0-9]+\b"), number_format))

        if comment_pattern:
            self.highlightingRules.append((QRegularExpression(comment_pattern), comment_format))
        
        if self.multi_comment_start_expression:
            self.highlightingRules.append((self.multi_comment_start_expression, comment_format))
        if self.multi_comment_end_expression:
            self.highlightingRules.append((self.multi_comment_end_expression, comment_format))


    def highlightBlock(self, text):
        self.setCurrentBlockState(0)

        for expression, format in self.highlightingRules:
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)
        
        if self.previousBlockState() == 1:
            comment_format = QTextCharFormat()
            comment_format.setForeground(QColor("#6a9955"))
            comment_format.setFontItalic(True)
            self.setFormat(0, len(text), comment_format)

        if self.multi_comment_start_expression and self.multi_comment_end_expression:
            comment_start_index = text.indexOf(self.multi_comment_start_expression)
            while comment_start_index >= 0:
                comment_end_index = text.indexOf(self.multi_comment_end_expression, comment_start_index + self.multi_comment_start_expression.pattern().length())
                comment_format = QTextCharFormat()
                comment_format.setForeground(QColor("#6a9955"))
                comment_format.setFontItalic(True)

                if comment_end_index == -1:
                    self.setCurrentBlockState(1)
                    self.setFormat(comment_start_index, len(text) - comment_start_index, comment_format)
                else:
                    self.setFormat(comment_start_index, comment_end_index - comment_start_index + self.multi_comment_end_expression.pattern().length(), comment_format)
                
                comment_start_index = text.indexOf(self.multi_comment_start_expression, comment_start_index + 1)


# --- CLASE PARA LA VENTANA DE VISUALIZACIÓN DE CÓDIGO ---

class CodeViewerWindow(BaseAssistantWindow):
    '''
    Ventana dedicada a la visualización de un bloque de código extraído.
    Incluye resaltado de sintaxis, opción de guardar y alternar resaltado.
    '''
    def __init__(self, code_text, language, parent=None):
        super().__init__(parent)
        self.code_text = code_text
        self.language = language
        self.setWindowTitle(f"Código - {language.capitalize()}")
        self._highlighting_enabled = True
        self._is_always_on_top = False # New state for "always on top"
        self._init_ui()
        self._setup_text_widget_context_menu(self.code_widget)

    def _init_ui(self):
        self.code_widget = QTextEdit(self)
        self.code_widget.setReadOnly(False)
        self.code_widget.setFont(QFont("Consolas", 12))
        self.code_widget.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.code_widget.setText(self.code_text)
        self.main_layout.addWidget(self.code_widget)

        self.highlighter = CodeHighlighter(self.code_widget.document(), self.language)

        button_frame_code = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Guardar", self)
        self.save_button.clicked.connect(self._save_code)
        
        self.copy_all_button = QPushButton("📄 Copiar Todo", self)
        self.copy_all_button.clicked.connect(self.code_widget.selectAll)
        self.copy_all_button.clicked.connect(self.code_widget.copy)

        self.toggle_highlight_button = QPushButton("✨ Alternar Resaltado", self)
        self.toggle_highlight_button.clicked.connect(self._toggle_highlighting)

        self.toggle_ontop_button = QPushButton("📌 Mantener Siempre Visible", self) # New button
        self.toggle_ontop_button.clicked.connect(self._toggle_always_on_top)

        # NEW: Font size controls for code viewer
        self.font_increase_code_button = QPushButton("A+", self)
        self.font_increase_code_button.setToolTip("Aumentar tamaño de fuente del código")
        self.font_increase_code_button.clicked.connect(lambda: self._change_code_font_size(1))
        button_frame_code.addWidget(self.font_increase_code_button)

        self.font_decrease_code_button = QPushButton("A-", self)
        self.font_decrease_code_button.setToolTip("Disminuir tamaño de fuente del código")
        self.font_decrease_code_button.clicked.connect(lambda: self._change_code_font_size(-1))
        button_frame_code.addWidget(self.font_decrease_code_button)
        # END NEW

        self.close_button = QPushButton("❌ Cerrar", self)
        self.close_button.clicked.connect(self.close)

        button_frame_code.addWidget(self.save_button)
        button_frame_code.addWidget(self.copy_all_button)
        button_frame_code.addWidget(self.toggle_highlight_button)
        button_frame_code.addWidget(self.toggle_ontop_button) # Add the new button
        button_frame_code.addStretch(1)
        button_frame_code.addWidget(self.close_button)
        self.main_layout.addLayout(button_frame_code)

    # NEW: Method to change font size for code viewer
    def _change_code_font_size(self, delta):
        font = self.code_widget.font()
        font.setPointSize(font.pointSize() + delta)
        self.code_widget.setFont(font)
    # END NEW

    def _toggle_highlighting(self):
        if self._highlighting_enabled:
            self.highlighter.setDocument(None)
            self._highlighting_enabled = False
            self.toggle_highlight_button.setText("🌈 Activar Resaltado")
        else:
            self.highlighter.setDocument(self.code_widget.document())
            self._highlighting_enabled = True
            self.toggle_highlight_button.setText("✨ Alternar Resaltado")
            self.highlighter.rehighlight()

    def _toggle_always_on_top(self):
        '''Toggles the 'always on top' window flag.'''
        if self._is_always_on_top:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self._is_always_on_top = False
            self.toggle_ontop_button.setText("📌 Mantener Siempre Visible")
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self._is_always_on_top = True
            self.toggle_ontop_button.setText("📍 No Mantener Siempre Visible")
        self.show() # Apply the flag change

    def _save_code(self):
        current_code = self.code_widget.toPlainText()
        extension_map = {
            "python": ".py", "py": ".py",
            "javascript": ".js", "js": ".js", "ts": ".ts", "json": ".json",
            "bash": ".sh", "sh": ".sh",
            "html": ".html", "css": ".css",
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
    '''
    Ventana principal para mostrar y procesar la respuesta de la IA.
    Incluye guardar, extraer código, modos de visualización, búsqueda,
    y ahora entrada de texto y gestión de permisos.
    '''
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contenido de la conversación 💬")
        self.original_text = text
        self._is_always_on_top = False # State for "always on top"
        self._init_ui()
        self._setup_text_widget_context_menu(self.text_widget)

    def _init_ui(self):
        self.text_widget = QTextEdit(self)
        self.text_widget.setReadOnly(False)
        self.text_widget.setFont(QFont("Consolas", 12))
        self.text_widget.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.main_layout.addWidget(self.text_widget)

        self._set_view_mode("plain")

        self._add_view_mode_buttons()
        self._add_search_bar()
        self._add_input_and_send_bar() # NEW: Input text area and send button
        self._add_permissions_button() # NEW: Permissions button
        self._add_main_buttons()
        self._add_window_options_buttons() # NEW: Toggle Always on Top

    def _add_view_mode_buttons(self):
        view_mode_layout = QHBoxLayout()
        view_mode_layout.addWidget(QLabel("Ver como:"))

        self.plain_text_button = QPushButton("📝 Texto Plano")
        self.plain_text_button.clicked.connect(lambda: self._set_view_mode("plain"))
        view_mode_layout.addWidget(self.plain_text_button)

        self.markdown_button = QPushButton("📜 Markdown")
        self.markdown_button.clicked.connect(lambda: self._set_view_mode("markdown"))
        view_mode_layout.addWidget(self.markdown_button)

        self.html_button = QPushButton("🌐 HTML")
        self.html_button.clicked.connect(lambda: self._set_view_mode("html"))
        view_mode_layout.addWidget(self.html_button)

        view_mode_layout.addStretch(1)
        self.main_layout.addLayout(view_mode_layout)

    def _set_view_mode(self, mode):
        if mode == "plain":
            self.text_widget.setPlainText(self.original_text)
        elif mode == "markdown":
            self.text_widget.setMarkdown(self.original_text)
        elif mode == "html":
            self.text_widget.setHtml(self.original_text)
        
    def _add_search_bar(self):
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔎 Buscar:"))

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Introduce texto a buscar...")
        self.search_input.returnPressed.connect(self._find_next_occurrence)
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
        query = self.search_input.text()
        if not query:
            return

        flags = QTextDocument.FindFlag(0)
        if not direction:
            flags |= QTextDocument.FindFlag.FindBackward
        
        cursor = self.text_widget.textCursor()
        
        if cursor.selectedText() != query:
             cursor.setPosition(0 if direction else self.text_widget.document().characterCount())
             self.text_widget.setTextCursor(cursor)

        found = self.text_widget.find(query, flags)

        if not found:
            cursor = self.text_widget.textCursor()
            cursor.setPosition(0 if direction else self.text_widget.document().characterCount())
            self.text_widget.setTextCursor(cursor)
            
            found_again = self.text_widget.find(query, flags)
            
            if found_again:
                QMessageBox.information(self, "Buscar", f"Se ha reiniciado la búsqueda. Encontrado '{query}'.")
            else:
                QMessageBox.information(self, "Buscar", f"No se encontró '{query}'.")

    def _add_input_and_send_bar(self):
        '''Adds an input text area and a 'Send' button. MODIFIED for QTextEdit.'''
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("📥 Enviar a la IA:"))

        # MODIFIED: Changed QLineEdit to QTextEdit for multiline input
        self.user_input_field = QTextEdit(self)
        self.user_input_field.setPlaceholderText("Escribe tu mensaje o comando para la IA aquí...")
        self.user_input_field.setAcceptRichText(False) # Ensure plain text input
        self.user_input_field.setFixedHeight(80) # Fixed height to make it look like a textarea
        self.user_input_field.setFont(QFont("Consolas", 10)) # Smaller font for input area
        input_layout.addWidget(self.user_input_field)

        self.send_input_button = QPushButton("🚀 Enviar", self)
        self.send_input_button.clicked.connect(self._send_input_to_ai)
        input_layout.addWidget(self.send_input_button)

        # NEW: Clear input button
        self.clear_input_button = QPushButton("🗑️ Limpiar Input", self)
        self.clear_input_button.setToolTip("Limpiar el contenido del área de entrada")
        self.clear_input_button.clicked.connect(self.user_input_field.clear)
        input_layout.addWidget(self.clear_input_button)
        # END NEW

        self.main_layout.addLayout(input_layout)

    def _send_input_to_ai(self):
        '''Sends the user input to stdout with a special prefix for the AI to pick up. MODIFIED for QTextEdit.'''
        # MODIFIED: Use toPlainText() for QTextEdit
        user_text = self.user_input_field.toPlainText().strip()
        if user_text:
            # Print to stdout with a unique prefix. The main Osiris script must be
            # configured to read and interpret this output.
            sys.stdout.write(f"{user_text}\n")
            sys.stdout.flush() # Ensure it's written immediately

            QMessageBox.information(self, "Envío Confirmado", "Tu mensaje ha sido enviado al sistema Osiris. El sistema lo procesará.")
            self.user_input_field.clear() # Clear the input field after sending
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce texto antes de enviar.")

    def _add_permissions_button(self):
        '''Adds a button to manage file permissions (user/root concept).'''
        permissions_layout = QHBoxLayout()
        self.manage_permissions_button = QPushButton("🔑 Gestión de Permisos", self)
        self.manage_permissions_button.clicked.connect(self._show_permissions_dialog)
        permissions_layout.addWidget(self.manage_permissions_button)
        permissions_layout.addStretch(1) # Push to left
        self.main_layout.addLayout(permissions_layout)

    def _show_permissions_dialog(self):
        '''Shows a dialog to get file path and new permissions, then generates CRO.'''
        dialog = QDialog(self)
        dialog.setWindowTitle("Gestión de Permisos (CRO)")
        dialog.setFixedSize(400, 200) # Fixed size for simplicity

        layout = QGridLayout(dialog)

        layout.addWidget(QLabel("Ruta del archivo:"), 0, 0)
        path_input = QLineEdit(dialog)
        path_input.setPlaceholderText("/ruta/al/archivo")
        layout.addWidget(path_input, 0, 1)

        layout.addWidget(QLabel("Permisos (ej. 755):"), 1, 0)
        perms_input = QLineEdit(dialog)
        perms_input.setPlaceholderText("755")
        layout.addWidget(perms_input, 1, 1)

        generate_button = QPushButton("Generar CRO", dialog)
        generate_button.clicked.connect(lambda: self._generate_chmod_cro(path_input.text(), perms_input.text(), dialog))
        layout.addWidget(generate_button, 2, 1)

        dialog.exec()

    def _generate_chmod_cro(self, path, permissions, dialog_instance):
        '''Generates and displays the CRO for chmod.'''
        if not path or not permissions:
            QMessageBox.warning(dialog_instance, "Error", "Por favor, introduce la ruta y los permisos.")
            return

        # Basic validation for permissions (3 digits, 0-7)
        if not re.fullmatch(r"[0-7]{3}", permissions):
             QMessageBox.warning(dialog_instance, "Error de Formato", "Los permisos deben ser 3 dígitos octales (ej. 755).")
             return

        # Generate CRO command
        cro_command = f'''```CRO
EXECUTE_SYSTEM_ACTION_* RUN_COMMAND
COMMAND="sudo chmod {permissions} {path}"
```

El siguiente comando CRO propone cambiar los permisos del archivo '{path}' a '{permissions}'. Esto requiere permisos de superusuario (sudo).

¿Deseas que el sistema ejecute este comando? Si confirmas, el sistema te pedirá la contraseña de sudo si es necesario.
'''
        QMessageBox.information(dialog_instance, "CRO Generado", cro_command)
        dialog_instance.accept() # Close the permissions dialog

    def _add_main_buttons(self):
        main_button_frame = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Guardar como...", self)
        self.save_button.clicked.connect(self._save_text_to_file)
        main_button_frame.addWidget(self.save_button)

        self.extract_button = QPushButton("✂️ Extraer Código", self)
        self.extract_button.clicked.connect(self._handle_extract_code)
        main_button_frame.addWidget(self.extract_button)

        # NEW: Font size controls for main text display
        self.font_increase_button = QPushButton("A+", self)
        self.font_increase_button.setToolTip("Aumentar tamaño de fuente del texto")
        self.font_increase_button.clicked.connect(lambda: self._change_text_font_size(1))
        main_button_frame.addWidget(self.font_increase_button)

        self.font_decrease_button = QPushButton("A-", self)
        self.font_decrease_button.setToolTip("Disminuir tamaño de fuente del texto")
        self.font_decrease_button.clicked.connect(lambda: self._change_text_font_size(-1))
        main_button_frame.addWidget(self.font_decrease_button)
        # END NEW

        main_button_frame.addStretch(1)

        self.close_button = QPushButton("❌ Cerrar", self)
        self.close_button.clicked.connect(self.close)
        main_button_frame.addWidget(self.close_button)

        self.main_layout.addLayout(main_button_frame)

    # NEW: Method to change font size for response viewer
    def _change_text_font_size(self, delta):
        font = self.text_widget.font()
        font.setPointSize(font.pointSize() + delta)
        self.text_widget.setFont(font)
    # END NEW

    def _add_window_options_buttons(self):
        '''Adds buttons for window options like 'Always on Top'.'''
        window_options_layout = QHBoxLayout()
        self.toggle_ontop_button = QPushButton("📌 Mantener Siempre Visible", self)
        self.toggle_ontop_button.clicked.connect(self._toggle_always_on_top)
        window_options_layout.addWidget(self.toggle_ontop_button)
        window_options_layout.addStretch(1)
        self.main_layout.addLayout(window_options_layout)

    def _toggle_always_on_top(self):
        '''Toggles the 'always on top' window flag.'''
        if self._is_always_on_top:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self._is_always_on_top = False
            self.toggle_ontop_button.setText("📌 Mantener Siempre Visible")
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self._is_always_on_top = True
            self.toggle_ontop_button.setText("📍 No Mantener Siempre Visible")
        self.show() # Apply the flag change

    def _save_text_to_file(self):
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
        code_blocks = []
        pattern = r"```(\w+)\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        for language, code in matches:
            code_blocks.append({"language": language.strip(), "code": code.strip()})
        return code_blocks

    def _handle_extract_code(self):
        current_text = self.text_widget.toPlainText()
        code_blocks = self._extract_code_blocks(current_text)

        if code_blocks:
            for block in code_blocks:
                code_window = CodeViewerWindow(block['code'], block['language'], parent=self)
                code_window.show()
        else:
            QMessageBox.information(self, "Información", "No se encontraron bloques de código en la respuesta. Asegúrate de que estén en formato Markdown (```lenguaje\\ncódigo\\n```).")

# --- FUNCIÓN DE ENTRADA (equivalente a tu `show_text_window`) ---

def show_ai_response_window(text: str):
    '''
    Función de utilidad para mostrar la ventana de visualización de respuestas.
    Se asegura de que una QApplication exista.
    '''
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    viewer_window = ResponseViewerWindow(text)
    viewer_window.show() # Use .show() for non-modal behavior
    
    # If this script (aluminium.py) is meant to run as a standalone GUI app
    # then app.exec() is needed here to start the event loop and keep the window open.
    # If it's part of a larger QApplication managed by gemini.py, then exec() should not be called here.
    # Given the previous context, it seems it runs standalone sometimes for "debugging" or "inspection".
    # So, we'll keep app.exec() for standalone execution.
    if QApplication.instance() == app: # Only call exec if this app instance is the main one
        app.exec() # Keep the application running and handle events

def main(args):
    # This is an example text that the AI could return.
    sample_ai_response = ''' ¡Hola! 😊 Soy Gemini AI, tu asistente aquí en Osiris. ¿En qué puedo ayudarte hoy? '''
    sample_ai_response+=str(args)
    show_ai_response_window(sample_ai_response)

if __name__ == "__main__":
    main(sys.argv[1:])