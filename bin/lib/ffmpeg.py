print("Import ffpmeg lib")

import os

class ConcatenadorFFmpeg:
    def __init__(self, extension, archivo_concat, directorio_origen, directorio_destino):
        self.extension = extension
        self.archivo_concat = archivo_concat
        self.directorio_origen = directorio_origen
        self.directorio_destino = directorio_destino

    def encontrar_archivos(self):
        archivos_mp4 = []
        for archivo in os.listdir(self.directorio_origen):
            if archivo.endswith(self.extension):
                archivos_mp4.append(archivo)
        return archivos_mp4

    def escribir_archivo_concat(self, archivos):
        with open(os.path.join(self.directorio_destino, self.archivo_concat), 'w') as f:
            for archivo_mp4 in archivos:
                f.write(f"file '{self.directorio_origen}/{archivo_mp4}'\n")

    def concatenar_archivos(self):
        archivos = self.encontrar_archivos()
        if archivos:
            self.escribir_archivo_concat(archivos)
            print("Se ha creado el archivo de concatenación:", self.archivo_concat)
        else:
            print("No se encontraron archivos con la extensión especificada.")

