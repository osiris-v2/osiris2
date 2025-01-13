import os,cnf



def fhelp(prcs):
	fpath = cnf.PATH["PATH_HELP"]+"/"+prcs+".hlp"
	if not os.path.isfile(fpath):
		r = open(fpath,"x+")
		r.write("***** "+prcs+" *****")
		read = r.read()
		r.close()
		return "\n NO HAY INFORMACION PARA "+prcs\
		+"\n Se ha creado el archivo "+fpath\
		+"\n "+read+" \n"
	else:
		with open(fpath,"r") as r:
			read = r.read()
			r.close()
			return read