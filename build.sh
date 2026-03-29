#!/usr/bin/env bash
# exit on error
set -o errexit

# Installer les dépendances backend
pip install -r requirements.txt

# Construire le frontend
cd frontend
npm install
npm run build
cd ..

# Retour au root et peuplement de la DB si nécessaire (SQLite local seulement)
# En production Render, on utilisera une DB externe ou un Disk
python backend/populate_demo.py
