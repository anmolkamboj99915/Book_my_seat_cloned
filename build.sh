#!/bin/bash

echo "▶ Building Project..."
# Install dependencies
python3 -m pip install -r requirements.txt

# Create the missing static folder to satisfy settings.py
mkdir -p static

# Collect static files into 'staticfiles/'
echo "▶ Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "▶ Build Finished!"