import sys
import signal
import cv2
import tkinter as tk
from tkinter import messagebox
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QImage
from moviepy.editor import VideoFileClip
import argparse
import time  # Importar el módulo time

def show_error_message(message):
    # Crear una ventana de error usando Tkinter
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal de Tkinter
    messagebox.showerror("Error", message)
    root.destroy()  # Destruir la ventana después de mostrar el mensaje


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, source):
        super().__init__()
        self._run_flag = True
        self.source = source
        self.video_clip = None

        # Inicializar frame_rate a un valor predeterminado
        self.frame_rate = 30  # Valor por defecto (puedes cambiarlo según sea necesario)

    def run(self):
        try:
            if self.source == "--webcam":
                # Abrir la cámara web
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise Exception("Error al abrir la cámara web")
            else:
                # Cargar el video con MoviePy
                self.video_clip = VideoFileClip(self.source)
                self.frame_rate = self.video_clip.fps
                current_time = 0

            while self._run_flag:
                if self.source == "--webcam":
                    # Obtener frame de la cámara
                    ret, frame = cap.read()
                    if not ret:
                        break
                else:
                    # Obtener frame del video clip
                    frame = self.video_clip.get_frame(current_time)
                    current_time += 1 / self.frame_rate  # Incrementar el tiempo según la tasa de fotogramas

                # Convertir el frame de BGR a RGB
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convierte el frame a QImage
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                # Emite la señal con la imagen actualizada
                self.change_pixmap_signal.emit(q_image)

                if self.source != "--webcam" and current_time >= self.video_clip.duration:
                    break
                
                # Añadir un retraso para controlar la velocidad de reproducción
                time.sleep(1 / self.frame_rate)

            if self.source == "--webcam":
                cap.release()
            else:
                self.video_clip.close()

        except Exception as e:
            show_error_message(str(e))

    def stop(self):
        self._run_flag = False
        self.wait()


class TransparentWindow(QWidget):
    def __init__(self, source):
        super().__init__()

        # Configurar la ventana sin bordes, siempre encima y redimensionable
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(420, 360)
        self.setGeometry(100, 100, 640, 520)

        # Variables para el estado de pantalla completa y el arrastre
        self.fullscreen = False
        self.is_moving = False
        self.offset = QPoint()

        # Crear un label para mostrar el video
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.width(), self.height())
        self.label.setAlignment(Qt.AlignCenter)

        # Iniciar el thread del video
        self.thread = VideoThread(source)
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.move(self.pos() - QPoint(10, 0))  # Mover a la izquierda
        elif event.key() == Qt.Key_Right:
            self.move(self.pos() + QPoint(10, 0))  # Mover a la derecha
        elif event.key() == Qt.Key_Up:
            self.move(self.pos() - QPoint(0, 10))  # Mover hacia arriba
        elif event.key() == Qt.Key_Down:
            self.move(self.pos() + QPoint(0, 10))  # Mover hacia abajo
        elif event.key() == Qt.Key_Shift:
            # Redimensionar la ventana con Shift + flechas (agregar lógica aquí si lo deseas)
            pass

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

    # Parser de argumentos
    parser = argparse.ArgumentParser()
    parser.add_argument("--webcam", action="store_true", help="Utilizar la cámara web")
    parser.add_argument("video_path", nargs="?", default=None, help="Ruta al archivo de video")
    args = parser.parse_args()

    app = QApplication(sys.argv)

    try:
        # Validar los argumentos
        if args.webcam and args.video_path:
            show_error_message("Solo se puede especificar --webcam o una ruta al archivo de video")
            sys.exit(1)
        elif args.webcam:
            source = "--webcam"
        elif args.video_path:
            source = args.video_path
        else:
            show_error_message("Debe especificar --webcam o una ruta al archivo de video")
            sys.exit(1)

        # Crear una ventana con fondo transparente
        window = TransparentWindow(source)
        window.show()

        # Ejecutar la aplicación
        sys.exit(app.exec_())
    except Exception as e:
        show_error_message(str(e))
