import sys
import signal
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QPainter, QMouseEvent


class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurar la ventana sin bordes, siempre encima y redimensionable
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)

        # Habilitar fondo transparente
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Permitir el redimensionamiento
        self.setMouseTracking(True)
        self.setMinimumSize(200, 150)  # Tamaño mínimo

        # Establecer geometría inicial de la ventana
        self.setGeometry(100, 100, 400, 300)

        # Variables para el estado de pantalla completa y el arrastre
        self.fullscreen = False
        self.is_moving = False
        self.is_resizing = False  # Definir la variable para redimensionar
        self.offset = QPoint()

    # Pintar contenido personalizado
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(0, 0, 0, 150))  # Negro semi-transparente
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

    # Mover ventana con el ratón
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Detectar si está redimensionando desde las esquinas
            if self.cursor().shape() == Qt.SizeFDiagCursor:
                self.is_resizing = True
                self.offset = event.globalPos() - self.geometry().bottomRight()
            else:
                # Mover la ventana
                self.is_moving = True
                self.offset = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_moving and not self.fullscreen:
            # Mover la ventana al arrastrarla
            self.move(self.pos() + event.pos() - self.offset)
        elif self.is_resizing:
            # Redimensionar la ventana
            self.resize(event.globalX() - self.x(), event.globalY() - self.y())
        else:
            # Cambiar el cursor en las esquinas para redimensionar
            x, y, w, h = self.geometry().getRect()
            right = x + w
            bottom = y + h

            if event.x() >= right - 10 and event.y() >= bottom - 10:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.is_moving = False
        self.is_resizing = False

    # Doble clic para alternar pantalla completa
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.fullscreen:
                self.showNormal()
            else:
                self.showFullScreen()
            self.fullscreen = not self.fullscreen

    # Detectar teclas para mover la ventana
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.move(self.x(), self.y() - 10)
        elif event.key() == Qt.Key_Down:
            self.move(self.x(), self.y() + 10)
        elif event.key() == Qt.Key_Left:
            self.move(self.x() - 10, self.y())
        elif event.key() == Qt.Key_Right:
            self.move(self.x() + 10, self.y())

        # Detectar Ctrl + C para cerrar
        if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            print("Cerrando ventana con Ctrl + C")
            QApplication.instance().quit()


# Manejar Ctrl + C para cerrar la ventana desde la terminal
def handle_sigint(sig, frame):
    print("Cerrando aplicación...")
    QApplication.instance().quit()


if __name__ == "__main__":
    # Manejar la señal SIGINT (Ctrl + C) para cerrar la ventana
    signal.signal(signal.SIGINT, handle_sigint)

    app = QApplication(sys.argv)

    # Crear una ventana con fondo transparente
    window = TransparentWindow()
    window.show()

    # Ejecutar la aplicación
    sys.exit(app.exec_())
