#!/usr/bin/env bash
# Salir si ocurre un error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Empaquetar el CSS
python manage.py collectstatic --no-input

# Aplicar las migraciones a la base de datos de Render
python manage.py migrate