#!/usr/bin/env python3.9
import sys
import random
import string
import os
import subprocess
import osiris2

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor

# Variable global para almacenar los mensajes de estado
hecho = ""

class ResizableRectangle(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 300)

        self.start_pos = None
        self.is_resizing = False

        # Main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Text area
        self.text_area = QTextEdit(self)
        self.text_area.setPlaceholderText("Write here...")
        self.main_layout.addWidget(self.text_area)

        # Button layout
        self.button_layout = QHBoxLayout()
        self.done_button = QPushButton("Capturar", self)
        self.done_button.clicked.connect(self.on_done)
        self.button_layout.addWidget(self.done_button)

        self.close_button = QPushButton("Hecho", self)
        self.close_button.clicked.connect(self.close)
        self.button_layout.addWidget(self.close_button)

        self.main_layout.addLayout(self.button_layout)

        # Set background color
        self.setStyleSheet("background-color: rgba(255, 255, 255, 200);")
        self.text_area.setStyleSheet("background-color: lightgray;")

        # Mouse events for moving and resizing
        self.main_widget.mousePressEvent = self.start_move
        self.main_widget.mouseMoveEvent = self.move_window
        self.main_widget.mouseReleaseEvent = self.stop_move

        # Resize handle
        self.resize_handle = QFrame(self)
        self.resize_handle.setGeometry(self.width() - 10, self.height() - 10, 10, 10)
        self.resize_handle.setStyleSheet("background-color: black;")
        self.resize_handle.mousePressEvent = self.start_resize
        self.resize_handle.mouseMoveEvent = self.perform_resize

        # Focus on text area
        self.text_area.setFocus()

    def start_move(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPos() - self.frameGeometry().topLeft()

    def move_window(self, event):
        if self.start_pos is not None:
            self.move(event.globalPos() - self.start_pos)

    def stop_move(self, event):
        self.start_pos = None

    def start_resize(self, event):
        if event.button() == Qt.LeftButton:
            self.is_resizing = True
            self.start_pos = event.globalPos()

    def perform_resize(self, event):
        if self.is_resizing:
            new_width = max(event.globalPos().x() - self.x(), 200)
            new_height = max(event.globalPos().y() - self.y(), 200)
            self.setFixedSize(new_width, new_height)
            self.resize_handle.move(self.width() - 10, self.height() - 10)  # Move the resize handle

    def on_done(self):
        global hecho
        # Get the current geometry before hiding the window
        geometry = self.geometry()

        # Hide the window and disable mouse interaction
        self.hide()
        QApplication.setOverrideCursor(Qt.BlankCursor)  # Disable mouse interaction

        # Use a timer to delay the capture until the window is hidden
        QTimer.singleShot(200, lambda: self.capture(geometry))

    def capture(self, geometry):
        global hecho  # Declarar hecho como global
        try:
            # Calculate the area to capture (the specific area of this window)
            x = geometry.x()
            y = geometry.y()
            width = geometry.width()
            height = geometry.height()

            # Print coordinates for debugging
            hecho += f"Coordinates: ({x}, {y}), Width: {width}, Height: {height}\n"

            # Create a unique filename for the screenshot
            image_path = os.path.join(os.getcwd() , "com/tmp", f"{self.generate_filename()}.png")


            display = os.environ.get("DISPLAY")

            if display:
                display = display
                #print(f"El valor de $DISPLAY es: {display}")
            else:
                display=":0"
                #print("La variable $DISPLAY no está configurada.")


            # Use ffmpeg to capture the area
            command = [
                "o2ffmpeg",
                "-video_size", f"{width}x{height}",
                "-f", "x11grab",
                "-i", f"{display}.0+{x},{y}",
                "-frames:v", "1",
                image_path
            ]

            # Run the ffmpeg command and capture the output
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check if the command was successful
            if result.returncode == 0:
                hecho += f"ImagePath: {image_path}\n"
            else:
                hecho += f"Failed to capture image. Error: {result.stderr.decode().strip()}\n"

            # Show the window again and restore cursor
            self.show()  # Show the window again
            QApplication.restoreOverrideCursor()  # Restore mouse interaction
            self.activateWindow()  # Activate the window again
            self.setFocus()  # Set focus back to the window

            # Get the text content
            text_content = self.text_area.toPlainText().strip()
            hecho += f"Text: {text_content}\n"  # Corregido para usar +=
            print(hecho)

        except Exception as e:
            # Show an error message if capturing fails
            QMessageBox.critical(self, "Capture Error", f"Failed to capture the image: {str(e)}")
            self.show()  # Restore the window in case of error
            QApplication.restoreOverrideCursor()  # Restore mouse interaction

    def generate_filename(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    def paintEvent(self, event):
        # Custom painting for rounded corners
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(255, 255, 255, 200))  # Semi-transparent background
        painter.drawRoundedRect(self.rect(), 10, 10)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResizableRectangle()
    window.show()
    sys.exit(app.exec_())

