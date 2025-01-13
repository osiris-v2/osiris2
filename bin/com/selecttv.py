import tkinter as tk

class ResizableRectangle(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Resizable Rectangle")
        self.geometry("400x300+100+100")  # Tamaño inicial y posición de la ventana
        self.overrideredirect(True)  # Elimina las decoraciones de la ventana
        self.attributes("-topmost", True)  # Mantiene la ventana al frente
        self.attributes("-alpha", 0.5)  # Hace la ventana semi-transparente

        self.border_thickness = 5
        self.start_x = self.start_y = None
        self.is_resizing = False

        self.border_frame = tk.Frame(self, bg='red', bd=0, highlightthickness=self.border_thickness, highlightbackground="black")
        self.border_frame.pack(fill=tk.BOTH, expand=True)
        self.border_frame.bind("<B1-Motion>", self.move_window)  # Mover la ventana
        self.border_frame.bind("<ButtonPress-1>", self.start_move)  # Iniciar el movimiento

        self.resize_handle = tk.Frame(self.border_frame, bg='black', cursor='bottom_right_corner', width=10, height=10)
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.resize_handle.bind("<ButtonPress-1>", self.start_resize)  # Iniciar redimensionamiento
        self.resize_handle.bind("<B1-Motion>", self.perform_resize)  # Redimensionar la ventana

        self.done_button = tk.Button(self.border_frame, text="Done", command=self.on_done)
        self.done_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.close_button = tk.Button(self.border_frame, text="Close", command=self.on_close)
        self.close_button.pack(side=tk.LEFT, padx=5, pady=5)

    def start_move(self, event):
        self.start_x, self.start_y = event.x_root, event.y_root

    def move_window(self, event):
        x, y = event.x_root, event.y_root
        dx, dy = x - self.start_x, y - self.start_y
        new_x = self.winfo_x() + dx
        new_y = self.winfo_y() + dy
        self.geometry(f"+{new_x}+{new_y}")
        self.start_x, self.start_y = x, y

    def start_resize(self, event):
        self.start_x, self.start_y = event.x_root, event.y_root
        self.is_resizing = True

    def perform_resize(self, event):
        if not self.is_resizing:
            return
        
        x, y = event.x_root, event.y_root
        dx, dy = x - self.start_x, y - self.start_y
        new_width = self.winfo_width() + dx
        new_height = self.winfo_height() + dy
        self.geometry(f"{new_width}x{new_height}")
        self.start_x, self.start_y = x, y

    def on_done(self):
        self.result = (self.winfo_x(), self.winfo_y(), self.winfo_width(), self.winfo_height())
        self.destroy()

    def on_close(self):
        self.result = None
        self.destroy()

    def get_rectangle(self):
        self.mainloop()
        return self.result

def main(args):
#    print(args)
    try:
        app = ResizableRectangle()
        rect = app.get_rectangle()
        if rect:
            print(f"{rect[0]},{rect[1]},{rect[2]},{rect[3]}")
        else:
            print("Closed without selection")
    except Exception as e:
        print("Error:",e)



main("start")
