import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, Toplevel
from threading import Thread, Event
import requests

class DownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Downloader Mejorado")
        master.geometry("750x600")

        self.output_dir = ""
        self.is_running = False
        self.stop_event = Event()
        self.download_mode = tk.StringVar(value="sequential")

        self.create_directory_selection_panel()
        self.create_options_panel()

        self.download_button = tk.Button(master, text="Iniciar Descarga", command=self.start_download, bg='green', fg='white')
        self.download_button.pack(pady=10)

        self.stop_button = tk.Button(master, text="Detener Descarga", command=self.stop_download, bg='red', state="disabled")
        self.stop_button.pack(pady=5)

        self.show_command_button = tk.Button(master, text="Mostrar Comando en Ejecución", command=self.show_command_window, state="disabled")
        self.show_command_button.pack(pady=5)

        self.output_text = scrolledtext.ScrolledText(master, width=85, height=20, wrap=tk.WORD)
        self.output_text.pack(pady=10, fill=tk.BOTH, expand=True)

        master.grid_rowconfigure(3, weight=1)
        master.grid_columnconfigure(0, weight=1)

    def create_directory_selection_panel(self):
        dir_frame = tk.Frame(self.master)
        dir_frame.pack(pady=10)

        self.output_button = tk.Button(dir_frame, text="Seleccionar Directorio de Salida", command=self.select_output_dir, bg='blue', fg='white')
        self.output_button.grid(row=0, column=0, padx=5)

    def create_options_panel(self):
        options_frame = tk.Frame(self.master)
        options_frame.pack(pady=10)

        tk.Label(options_frame, text="URLs para descargar (una por línea):").grid(row=0, column=0, padx=5)
        self.urls_entry = scrolledtext.ScrolledText(options_frame, width=50, height=5)
        self.urls_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        self.parallel_button = tk.Radiobutton(options_frame, text="Descarga en Paralelo", variable=self.download_mode, value="parallel")
        self.parallel_button.grid(row=2, column=0)

        self.sequential_button = tk.Radiobutton(options_frame, text="Descarga Secuencial", variable=self.download_mode, value="sequential")
        self.sequential_button.grid(row=2, column=1)

    def select_output_dir(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            self.output_text.insert(tk.END, f"Directorio de salida: {self.output_dir}\n")

    def start_download(self):
        if not self.output_dir:
            self.output_text.insert(tk.END, "Por favor, selecciona un directorio de salida.\n")
            return

        if self.is_running:
            return  # Prevenir doble descarga si ya está en progreso

        self.is_running = True
        self.stop_event.clear()
        self.stop_button.config(state="normal")
        self.download_button.config(state="disabled")
        self.show_command_button.config(state="normal")

        urls = self.urls_entry.get("1.0", tk.END).strip().splitlines()
        if self.download_mode.get() == "parallel":
            self.download_parallel(urls)
        else:
            Thread(target=self.download_sequential, args=(urls,)).start()

    def stop_download(self):
        self.stop_event.set()
        self.output_text.insert(tk.END, "Descarga detenida.\n")
        self.is_running = False
        self.download_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.show_command_button.config(state="disabled")

    def download_file(self, url):
        file_name = os.path.join(self.output_dir, os.path.basename(url))
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if self.stop_event.is_set():
                            self.output_text.insert(tk.END, f"Descarga detenida para {url}.\n")
                            return
                        f.write(chunk)
            self.output_text.insert(tk.END, f"Descargado: {file_name}\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error descargando {url}: {e}\n")

    def download_sequential(self, urls):
        for url in urls:
            if self.stop_event.is_set():
                break
            self.output_text.insert(tk.END, f"Iniciando descarga: {url}\n")
            self.download_file(url)
        self.download_complete()

    def download_parallel(self, urls):
        threads = []
        for url in urls:
            if self.stop_event.is_set():
                break
            thread = Thread(target=self.download_file, args=(url,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.download_complete()

    def download_complete(self):
        self.output_text.insert(tk.END, "Todas las descargas completadas.\n")
        self.is_running = False
        self.download_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.show_command_button.config(state="disabled")

    def show_command_window(self):
        command_window = Toplevel(self.master)
        command_window.title("Comando en Ejecución")
        command_window.geometry("600x200")
        command_label = tk.Label(command_window, text="Descargando archivos de las URLs especificadas...", wraplength=500)
        command_label.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()

