#!/usr/bin/bash
source /etc/environment
echo $OSIRIS000_BIN
pip install --upgrade pip
pip install --upgrade -r $OSIRIS000_VENV_PATH/osiris.pip.requeriments 