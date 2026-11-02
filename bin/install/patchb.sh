#!/usr/bin/bash



SDIR=$(dirname "$(readlink -f "$0")")

echo "El parche beta completa y corrige bugs que se puedan dar durante el desarrollo de la versión Beta"

read -p "Instalar el parche Beta Y/N:   " resp

if [[ "${resp^^}" == "Y" ]]; then

echo "Se instalarán los Parches Beta... \n "

cd $SDIR
cd ../../DEBIAN/usr/bin
 
  if cp -r . /usr/bin ; then
   echo "Copia a /usr/bin efectuada \n"
  else
   echo "Error al copiar de DEBIAN a /usr/bin \n"
  fi

else
echo "Optaste por no instalar el Parche Beta \n"
echo "El sistema podría no funcionar correctamente."
fi

#volvemos al directorio del script
cd $SDIR
