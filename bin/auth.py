import hashlib, base64 , os, cnf, com, getpass



def run():
	print("Verificación de Acceso Osiris App\n")
	if os.path.isfile(cnf.FileAuth) :
		access()
	else :
 		makeauth()



def makeauth():
	passin = pcp = input("Crear password: ")
	if len(passin) < 6 :
		print("\nEl password ha de tener una longitud mínima de 6 caracteres\n")
		makeauth()
	else :
		with open(cnf.FileAuth,"w") as f :
			passin = hashlib.sha512(bytes(passin,"utf-8"))
			passin = passin.hexdigest()
			f.write(str(passin))
			f.close()
			print("Password Nuevo creado \n",pcp, passin)
		access()

def get_psw():
	with open(cnf.FileAuth,"r") as f :
		psw = f.read(512)
	return psw


def access():
	psw = get_psw()
	pswin = getpass.getpass("Insert Osiris Password:")
	hashpass = hashlib.sha512(bytes(pswin,"utf-8"))
	hashpass = hashpass.hexdigest()
	if psw == str(hashpass):
		print("Acceso Permitido\n",hashpass)
		com.command_line()
	elif pswin == "Reset Password Key "+psw+"."+cnf.Reset_Password_Key:
		print("Reset password ")
		makeauth()
	else:
		print("Acceso Denegado")
		access()