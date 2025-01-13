import configparser

def read_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)

    config_data = {}
    for section in config.sections():
        config_data[section] = {}
        for key, value in config.items(section):
            config_data[section][key] = value

    return config_data

def get_config_variable(config, variable):
    # Si no se encontró la configuración, devolver None
    if config is None:
        return None

    return config.get(variable)

def config_module(module_name):
    # Obtener la configuración desde get_config.py
    config_all = read_config('com.ini')

    # Obtener la configuración específica para el módulo actual (module_name)
    try:
        config = config_all.get(module_name)
    except KeyError:
        print("Advertencia: Configuración para este módulo no encontrada.")
        config = None

    def config_function(var):
        value = get_config_variable(config, var)
        if value is not None:
            return value
        else:
            print(f"La variable '{var}' no está configurada o no se encontró la configuración para este módulo.")
    
    return config_function
