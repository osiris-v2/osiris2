import os
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext

class ConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Conversor de Video")

        # Configuración de la ventana
        master.geometry("600x500")
        
        # Directorios de entrada y salida
        self.input_dir = ""
        self.output_dir = ""

        # Panel de selección de directorios
        self.create_directory_selection_panel()

        # Botón para iniciar la conversión
        self.convert_button = tk.Button(master, text="Iniciar Conversión", command=self.start_conversion, bg='green', fg='white')
        self.convert_button.pack(pady=10)

        # Área de texto para mostrar la salida
        self.output_text = scrolledtext.ScrolledText(master, width=70, height=20, state='normal', wrap=tk.WORD)
        self.output_text.pack(pady=10)

    def create_directory_selection_panel(self):
        """Crea el panel de selección de directorios."""
        dir_frame = tk.Frame(self.master)
        dir_frame.pack(pady=10)

        self.input_button = tk.Button(dir_frame, text="Seleccionar Directorio de Entrada", command=self.select_input_dir, bg='blue', fg='white')
        self.input_button.grid(row=0, column=0, padx=5)

        self.output_button = tk.Button(dir_frame, text="Seleccionar Directorio de Salida", command=self.select_output_dir, bg='blue', fg='white')
        self.output_button.grid(row=0, column=1, padx=5)

    def select_input_dir(self):
        self.input_dir = filedialog.askdirectory()
        if self.input_dir:
            self.output_text.insert(tk.END, f"Directorio de entrada: {self.input_dir}\n")

    def select_output_dir(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            self.output_text.insert(tk.END, f"Directorio de salida: {self.output_dir}\n")

    def start_conversion(self):
        if not self.input_dir or not self.output_dir:
            self.output_text.insert(tk.END, "Por favor, seleccione ambos directorios.\n")
            return

        ffmpeg_options = "-af aresample=async=1,loudnorm=I=-16:TP=-1.5:LRA=11 -vf scale=-2:580 -c:v h264 -preset ultrafast -c:a aac -ac 2 -bsf:v h264_mp4toannexb -b:v 3000k -b:a 128k -maxrate 5000k -f mpegts"

        # Recorrer todos los archivos en el directorio de entrada
        for input_file in os.listdir(self.input_dir):
            input_path = os.path.join(self.input_dir, input_file)
            if os.path.isfile(input_path):
                base_name = os.path.splitext(input_file)[0]
                output_file = f"{base_name}.580p.optimo.ts"
                output_path = os.path.join(self.output_dir, output_file)

                self.output_text.insert(tk.END, f"Convirtiendo {input_path} a {output_path}...\n")
                command = f"ffmpeg -y -i \"{input_path}\" {ffmpeg_options} \"{output_path}\""

                # Ejecutar el comando y obtener la salida en tiempo real
                self.run_ffmpeg(command)

        self.output_text.insert(tk.END, "Conversión completa.\n")

    def run_ffmpeg(self, command):
        """Ejecuta FFmpeg y muestra la salida en tiempo real."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            self.output_text.insert(tk.END, line)
            self.output_text.yview(tk.END)  # Desplazar hacia abajo la vista del texto
            self.master.update()  # Actualizar la interfaz

        process.stdout.close()
        process.wait()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()

