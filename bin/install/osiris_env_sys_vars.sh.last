#!/usr/bin/bash
echo " Este script establece las variables del entorno global"
echo "  Virtual environment G-Osiris"
VENV_NAME="osiris_env"
# Función para agregar o actualizar variables de entorno
add_env_variables() {
    # Recibir las variables como argumentos
    for var in "$@"; do
        # Separar nombre y valor de la variable
        VARIABLE_NAME=$(echo "$var" | cut -d '=' -f 1)
        VARIABLE_VALUE=$(echo "$var" | cut -d '=' -f 2)

        # Verificar si la variable ya está definida en /etc/environment
        if grep -q "^$VARIABLE_NAME=" /etc/environment; then
            # Obtener el valor actual de la variable en /etc/environment
            CURRENT_VALUE=$(grep "^$VARIABLE_NAME=" /etc/environment | cut -d '=' -f 2- | tr -d '"')

            # Comparar el valor actual con el nuevo valor
            if [ "$CURRENT_VALUE" != "$VARIABLE_VALUE" ]; then
                echo "La variable '$VARIABLE_NAME' está definida con un valor diferente. Actualizando..."
                sudo sed -i "s|^$VARIABLE_NAME=.*|$VARIABLE_NAME=\"$VARIABLE_VALUE\"|" /etc/environment
                echo "Variable '$VARIABLE_NAME' actualizada a '$VARIABLE_VALUE'."
            else
                echo "La variable '$VARIABLE_NAME' ya está definida con el valor correcto."
            fi
        else
            # Añadir la variable a /etc/environment si no existe
            echo "Añadiendo la variable '$VARIABLE_NAME' a /etc/environment..."
            echo "$VARIABLE_NAME=\"$VARIABLE_VALUE\"" | sudo tee -a /etc/environment > /dev/null
            echo "Variable '$VARIABLE_NAME' añadida exitosamente a /etc/environment."
        fi
    done

    # Recargar las variables de entorno
    source /etc/environment
}

# Ejemplo de uso de la función
add_env_variables  "OSIRIS000_VENV_PYTHONPATH=/var/www/osiris000/bin/com/osiris_env/lib/python3.9/site-packages" \
"OSIRIS000_BIN=/var/www/osiris000/bin" \
"OSIRIS000_BASEPATH=/var/www/osiris000" \
"OSIRIS000_VENV_NAME=${VENV_NAME}" \
"OSIRIS000_VENV_PATH=/var/www/osiris000/bin/com/osiris_env" \
"VENV_ACTIVATE_PATH=/var/www/osiris000/bin/com/osiris_env/bin/activate" \
"AME_VENV=${VENV_NAME}" \
"OSIRIS_PUBLIC_WWW_DIR=/var/www/osiris000/html/app/freedirectory/osiris" 
