import datetime
import subprocess
import os


def main(args):
    print('Args dentro de create', args)
    if len(args) == 2 and args[1] == "--create":
    	#create_module_file(args[0])
    	create_module_file(args[0])
    	#comprobar que se haya creado el archivo
    	#posibilidad de editarlo
    elif args[0] == "--edit":
        subprocess.call(["nano", "-w","-i","com/"+os.path.basename(__file__)])
    else:
        print("Use \"nombre_de_comando --create\" para crear en nuevo archivo del comando  ")
        return


def create_module_file(module_name):

    global IN_MAIN
    global IMPORTS
    
	#comprobar si existe ruta
	#si no existe se crea el módulo por defecto
    try:
        with open(f"com/{module_name}.py", "x") as file:
            file.write(f"{IMPORTS}")
            file.write(f"{IN_MAIN}")
            file.write(f"print('Creado módulo-comando {module_name} y fecha y hora: {datetime.datetime.now()}')\n")
            print('Creado módulo-comando')
    except FileExistsError:
        print("El archivo del comando ya existe com/"+module_name+".py")


IMPORTS = """

import datetime
import subprocess
import os

"""

IN_MAIN = """


def main(args):
    print('Args dentro de {module_name}', args)


    try:
        if args[0] == "--edit":
            subprocess.call(["nano", "-w","-i","com/"+os.path.basename(__file__)])

    except Exception as e:
        print("Se ha producido un error:",e)


"""













print('Creado módulo-comando create y fecha y hora: 2023-09-26 08:34:08.790010')
