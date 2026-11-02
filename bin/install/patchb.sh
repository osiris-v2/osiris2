#!/usr/bin/bash


echo "USER: ${SUDO_USER:-}"


SDIR=$(dirname "$(readlink -f "$0")")

echo "El parche beta completa y corrige bugs que se puedan dar durante el desarrollo de la versión Beta"

read -p "Instalar el parche Beta Y/N:   " resp

if [[ "${resp^^}" == "Y" ]]; then

echo "Se instalarán los Parches Beta...  "

echo "cambiando a $SDIR"
cd $SDIR
echo "cambiando a ../../DEBIAN/usr/bin"
cd ../../DEBIAN/usr/bin
 
usr_bin_f=("o2load" "com") 
printf '%s\n' "${usr_bin_f[@]}" | while IFS= read -r archivo; do 
  if sudo cp ./$archivo /usr/bin/$archivo ; then
   sudo chmod +x /usr/bin/$archivo
   echo "Copia a /usr/bin/$archivo efectuada "
  else
   echo "Error al copiar de DEBIAN a /usr/bin/$archivo "
  fi 
done

else
echo "Optaste por no instalar el Parche Beta \n"
echo "El sistema podría no funcionar correctamente."
fi

#volvemos al directorio del script
cd $SDIR




