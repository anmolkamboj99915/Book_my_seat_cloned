#!/bin/bash

# Exit on error
set -e

echo "▶ Installing dependencies..."
python3 -m pip install -r requirements.txt

# Satisfy settings.py STATICFILES_DIRS requirement
mkdir -p static

echo "▶ Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "▶ Build completed successfully!"