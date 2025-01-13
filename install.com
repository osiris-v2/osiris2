


#instalamos aplicaciones necesarias


osiris-env-sys-vars  ./bin/install/osiris_env_sys_vars.sh

python-pack  ./bin/install/python_pack_install.sh




date				apt install date

py3				apt install python3.11
py3full				apt install python3.11-full
py3pip			 	apt install python3-pip 
py3env				apt install python3.11-venv
pip				apt install pip pip3
php				apt install php php-fpm php-mysqli php-all-dev
apache2 			apt install apache2 libapache2-mod-php libapache2-mod-fcgid 

#rustc-update        rustup update

mariadb 			apt install mariadb 
ffmpeg				apt install ffmpeg 
transmission-cli	apt install transmission-cli 
docker				apt install docker docker.io
tcptrack			apt install tcptrack
nodejs   			apt install nodejs
certbot 			apt install certbot
tor 				apt install tor

port-audio          apt install portaudio19-dev

xcblib    apt install libxcb-xinerama0 libxcb1 libx11-xcb1 libxcb-glx0 libxcb-shape0 libxcb-render0 libxcb-render-util0 libxcb-xfixes0 libxcb-sync1 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-util1 libxcb-xkb1


yt-dlp 				pip install yt-dlp


# source tutorial-env/bin/activate


#etc.. si no se chekea desde install.sh, se ignora

#NUEVA-app	apt install NUEVA-app

depend pip install python-bitcoinlib Flask
depend /usr/sbin/a2enmod ssl rewrite
depend apt install whois

#Osiris packs

pip.requeriments.install . bin/install/installpip.sh 

pip.requeriments.upgrade . bin/install/upgradepip.sh 

install.rust . bin/install/rust.sh

node-Opack eval . bin/install/node_install.sh
terminator-Opack  . bin/install/terminator_install.sh
ffmpeg-pack . bin/install/ffmpeg_install.sh
tmux-pack . bin/install/tmux_install.sh

#END
