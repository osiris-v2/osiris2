import sys
import signal
import cv2
import tkinter as tk
from tkinter import messagebox
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QImage


def show_error_message(message):
    # Crear una ventana de error usando Tkinter
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal de Tkinter
    messagebox.showerror("Error", message)
    root.destroy()  # Destruir la ventana después de mostrar el mensaje


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        try:
            # Intentar abrir la cámara o el archivo de video
#            cap = cv2.VideoCapture(0)  # 0 para la cámara web predeterminada
            cap = cv2.VideoCapture("/var/www/osiris000/bin/com/datas/ffmpeg/así-es-la-vida-gatillazo.mp4")
            if not cap.isOpened():
                raise Exception("Error al abrir la cámara o el video")

            while self._run_flag:
                ret, frame = cap.read()
                if ret:
                    # Convierte el frame de BGR a RGB
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convierte el frame a QImage
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    # Emite la señal con la imagen actualizada
                    self.change_pixmap_signal.emit(q_image)
                else:
                    break

            cap.release()
        except Exception as e:
            show_error_message(str(e))

    def stop(self):
        self._run_flag = False
        self.wait()


class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Configurar la ventana sin bordes, siempre encima y redimensionable
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(200, 150)
        self.setGeometry(100, 100, 400, 300)

        # Variables para el estado de pantalla completa y el arrastre
        self.fullscreen = False
        self.is_moving = False
        self.is_resizing = False
        self.offset = QPoint()
        self.resize_corner = None

        # Crear un label para mostrar el video
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.width(), self.height())
        self.label.setAlignment(Qt.AlignCenter)

        # Iniciar el thread del video
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def update_image(self, q_image):
        try:
            self.label.setPixmap(QPixmap.fromImage(q_image))
        except Exception as e:
            show_error_message(str(e))

    # Mover la ventana con el mouse
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_moving = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.is_moving:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.is_moving = False

    # Redimensionar la ventana desde las esquinas
    def mouseDoubleClickEvent(self, event):
        if not self.fullscreen:
            self.showFullScreen()
            self.fullscreen = True
        else:
            self.showNormal()
            self.fullscreen = False

    def closeEvent(self, event):
        # Detener el thread del video al cerrar la ventana
        self.thread.stop()
        super().closeEvent(event)


# Manejar Ctrl + C para cerrar la ventana desde la terminal
def handle_sigint(sig, frame):
    print("Cerrando aplicación...")
    QApplication.instance().quit()


if __name__ == "__main__":
    # Manejar la señal SIGINT (Ctrl + C) para cerrar la ventana
    signal.signal(signal.SIGINT, handle_sigint)

    app = QApplication(sys.argv)

    try:
        # Crear una ventana con fondo transparente
        window = TransparentWindow()
        window.show()

        # Ejecutar la aplicación
        sys.exit(app.exec_())
    except Exception as e:
        show_error_message(str(e))
