#!/usr/bin/bash

type check_command_installed >/dev/null 2>&1 || . osiris.sh

# Comprobación de aplicaciones instaladas.


check_command_installed /usr/bin/date -R 

sleep 2

echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"

#echo "Esta opción instala  python venv y pip"
#check_command_installed /usr/bin/python3.9-venv --version



echo "Esta opción instala  python "
check_command_installed /usr/bin/py3 --version

echo "Esta opción instala  python "
check_command_installed /usr/bin/py3full --version


echo "Esta opción instala  python "
check_command_installed /usr/bin/py3env --version
check_command_installed /usr/bin/py3Virtualenv --version


echo "Esta opción instala  python "
check_command_installed /usr/bin/py3pip --version

echo "Esta opción instala  xcblib librerias necesarias para usar Qt con python y otras"

check_command_installed /usr/bin/QtCppLib
check_command_installed /usr/bin/xcblib 
check_command_installed /usr/bin/port-audio 
check_command_installed /usr/bin/cdevlibs 



echo "Esta opción instala  pip "
check_command_installed /usr/bin/pip --version


check_command_installed osiris-env-sys-vars

#activamos directorio virtual
. ./bin/venv.sh


echo "Esta opción instala los paquetes pip instalados en el sistema"
check_command_installed /usr/bin/pip.requeriments.install


echo "Esta opción actualiza los paquetes pip instalados en el sistema"
check_command_installed /usr/bin/pip.requeriments.upgrade

check_command_installed /usr/bin/python-pack
#check_command_installed node-Opack --version
check_command_installed terminator-Opack 
check_command_installed tmux-pack 

check_command_installed ffmpeg-pack

check_command_installed install.rust













#check_command_installed /usr/bin/pip
#check_command_installed /usr/bin/nodejs
check_command_installed /usr/bin/certbot

#check_command_installed /usr/bin/Osiris-python3.9-venv

#. bin/venv.sh


#check_command_installed /usr/bin/Osiris-venv-activate
#check_command_installed /usr/bin/Osiris-venv-export

#check_command_installed /usr/bin/depend

#check_command_installed /usr/bin/tor --version

check_command_installed /usr/bin/apache2 -v
check_command_installed /usr/bin/apache2.enmod -v


check_command_installed /usr/bin/php --version 
check_command_installed /usr/bin/mariadb 
#check_command_installed /usr/bin/ffmpeg -version
#check_command_installed /usr/bin/transmission-cli --version 

check_command_installed /usr/bin/tcptrack -v 
#check_command_installed /usr/bin/yt-dlp --version
#check_command_installed /usr/bin/rustc "--version -v"
#check_command_installed /usr/bin/docker 



