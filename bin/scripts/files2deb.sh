#/usr/bin/bash
script_dir=$(dirname "$(readlink -f "$0")")
cd $script_dir

#este script incorpora a la carpeta DEBIAN 
#los archivos de entorno global de osiris


DIST="osiris2"
USRBIN="/usr/bin"
USRBIO="/usr/local/${DIST}/bio"
DEBIAN="../../DEBIAN"
BASEBIO="${DEBIAN}${USRBIO}"

cp $USRBIN/osiris2tmux  ${BASEBIO}/osiris2tmux
cp $USRBIN/o2load  ${BASEBIO}/o2load

