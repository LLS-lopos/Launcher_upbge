#!/bin/bash

# Configuration
SOURCE_DIR="source"
EXECUTABLE="lanceur.bin"

# Vérification des droits d'exécution
if [ ! -x "$SOURCE_DIR/$EXECUTABLE" ]; then
    echo "Erreur : $EXECUTABLE n'est pas exécutable"
    chmod +x "$SOURCE_DIR/$EXECUTABLE"
fi

# Démarrage du lanceur
echo "Démarrage du Lanceur..."
cd "$SOURCE_DIR" || { echo "Erreur : Impossible de changer de répertoire vers $SOURCE_DIR"; exit 1; }

./$EXECUTABLE

# Vérification du code de retour
if [ $? -eq 0 ]; then
    echo "Le Lanceur s'est arrêté correctement."
    exit 0
else
    echo "Erreur lors du démarrage du Lanceur. Code d'erreur: $?"
    exit 1
fi