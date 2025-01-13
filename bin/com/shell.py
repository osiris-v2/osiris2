import subprocess


def main(args):

    try:
        subprocess.call(args,cwd="com/osiris_env")
    except Exception as e:
        print("ERROR:",e)
    return



print('Creado módulo-comando shell y fecha y hora: 2023-11-28 12:12:24.596228')
