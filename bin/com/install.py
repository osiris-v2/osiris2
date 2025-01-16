import os, get_config, shutil



# Obtener la función para acceder a las variables de configuración para el módulo actual
config = get_config.config_module(__name__)




def main(args):
    print("Args dentro de install.py:", args)
    
    if args:
        parse(args)
    else:
        print("No se proporcionaron argumentos.")

def parse(args):
    command = args[0]
    arguments = args[1:]

    # Filtrar los argumentos que empiezan con "--" y separarlos de los demás
    arg_with_dash = [arg for arg in arguments if arg.startswith("--")]
    arg_without_dash = [arg for arg in arguments if not arg.startswith("--")]

    if command == "auto-install":
        print("Simulando ejecución de auto-install con argumentos:", arguments)
        # Llamar a la función correspondiente para el comando auto-install con los argumentos
        # Ejemplo: auto_install_function(arguments)
    elif command == "webapp":
        if len(arg_without_dash) > 1:
            print("Error: Solo se permite pasar un argumento como nombre de webapp.")
            return
        elif len(arg_without_dash) == 1:

            webapp_install = config("webapp_install")
            webapp_dir = config("webapp_dir")
            
            
            if not webapp_install:

                print("No existe variable webapp_install")
                return

            elif not webapp_dir:

                print("No existe webapp_dir wn com.ini")
                return

            else:

                print("webapp_install VALOR:",webapp_install)
                print("webapp_dir VALOR:",webapp_dir)

                webapp_install = webapp_install + "/" +arg_without_dash[0]
                webapp_dir = webapp_dir + "/" +arg_without_dash[0]


                if "--create-default" in arg_with_dash and len(arg_with_dash) < 2:


                    if not os.path.exists(webapp_install):
    
                        copy_path = config("--create-default")
                        print("SE CREA EL POR DEFECTO en")

                        try:
                            shutil.copytree(copy_path, webapp_install)
                            print(f"Se ha copiado el contenido de '{copy_path}' a '{webapp_install}'.")
                        except shutil.Error as e:
                            print(f"Error al copiar el contenido: {e}")
                        except Exception as e:
                            print(f"Error desconocido: {e}")
                
   
                    else:
                        
                        print("Error: El directorio para webapp ya existe.",webapp_install)
                        print("Use --update para actualizar")
                    
                        return
                

                elif "--update" in arg_with_dash and len(arg_with_dash) < 2:

                    print("Update App: ",arg_without_dash[0])

                    if not os.path.exists(webapp_install):
                        print("no existe la aplicación a actualizar en: ",webapp_install)
                        return

                    elif not os.path.exists(webapp_dir):
                        print("no existe la aplicacion a instalar en:",webapp_dir)
                        print("""
                    Sin embargo, sí existe en la carpeta de instalación
                    use --update para copiarla o actualizarla al directorio
                    web. 
                    Se va a crear el proyecto nuevo. 
                            """)

                        try:
                            shutil.copytree(webapp_install,webapp_dir)
                            print(f"Se ha copiado el contenido de '{webapp_install}' en '{webapp_dir}'")
                        except shutil.Error as e:
                            print(f"Error al copiar el contenido: {e}")
                        except Exception as e:
                            print(f"Error desconocido al copiar en --update: {e}")



                    else:
                        #existe origen y destino se hace el update
                        print("Realizando UPDATE AQUI de app: ",arg_without_dash[0])
                        shutil.rmtree(webapp_dir)
                        shutil.copytree(webapp_install, webapp_dir)
                        print(f"Se ha copiado y actualizado la carpeta {webapp_install} a {webapp_dir} correctamente.")
                    
                else:
                    
                    print("""
                        --Argumento dash no reconocido--
                        Use --create-default para crear un proyecto nuevo
                        Use --update para actualizar uno existente
                        """)












            print("Argumentos con '--':", arg_with_dash)
            print("Argumento sin '--':", arg_without_dash[0] if arg_without_dash else None)
            print("Simulando ejecución de webapp con argumentos:", arguments)

        else:
            print("Es necesario pasar un argumento como webapp")

    else:
        print("Comando no reconocido para install.py:", command)




if __name__ == "__main__":
    import sys
    main(sys.argv[1:])  # Pasamos los argumentos sin el primer elemento que es el nombre del script

