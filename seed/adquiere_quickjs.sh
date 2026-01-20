# 1. Descargar el tarball
wget https://bellard.org/quickjs/quickjs-2025-09-13-2.tar.xz

# 2. Descomprimirlo
tar xvf quickjs-2025-09-13-2.tar.xz
cd quickjs-2025-09-13


# Definimos la carpeta de origen para no escribir tanto
ORIGEN="/var/osiris2/seed/quickjs-2025-09-13"

# --- Mover Cabeceras (.h) a include ---
cp $ORIGEN/quickjs.h $ORIGEN/quickjs-atom.h $ORIGEN/quickjs-opcode.h \
   $ORIGEN/cutils.h $ORIGEN/list.h $ORIGEN/libregexp.h \
   $ORIGEN/libregexp-opcode.h $ORIGEN/libunicode.h \
   $ORIGEN/libunicode-table.h $ORIGEN/dtoa.h $ORIGEN/VERSION \
   /var/osiris2/seed/nodo_musculo/include/

# --- Mover Fuentes (.c) a drivers ---
# Nota: libbf.c no está en el tree porque Bellard a veces lo funde en quickjs.c,
# pero segun tu listado anterior, el dtoa.c y cutils.c son clave.
cp $ORIGEN/quickjs.c $ORIGEN/libregexp.c $ORIGEN/libunicode.c \
   $ORIGEN/cutils.c $ORIGEN/dtoa.c \
   /var/osiris2/seed/nodo_musculo/src/drivers/
