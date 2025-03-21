#!/bin/bash

# Vérifier si le dossier de l'environnement virtuel existe
if [ -d ".venv" ]; then
    echo "Activation de l'environnement Python"
    source .venv/bin/activate

    # Vérifiez si l'activation a réussi
    if [ $? -eq 0 ]; then
        echo "Vérification des dépendances..."
        if [ -f "dependence.txt" ]; then
            pip install -r dependence.txt
        else
            echo "Le fichier 'dependence.txt' n'existe pas. Aucune dépendance installée."
        fi

        echo "Démarrage du logiciel..."
        python3 -m source.lanceur

        # Vérifiez si le lancement du logiciel a réussi
        if [ $? -eq 0 ]; then
            echo "Le logiciel s'est arrêté correctement."
        else
            echo "Erreur lors du démarrage du logiciel."
        fi
    else
        echo "Échec de l'activation de l'environnement Python."
    fi
else
    echo "L'environnement virtuel n'existe pas. Installation des dépendances globalement..."
    
    # Vérifier si le fichier de dépendances existe
    if [ -f "dependence.txt" ]; then
        pip install -r dependence.txt
    else
        echo "Le fichier 'dependence.txt' n'existe pas. Aucune dépendance installée."
    fi

    echo "Démarrage du logiciel sans environnement virtuel..."
    python3 -m source.lanceur

    # Vérifiez si le lancement du logiciel a réussi
    if [ $? -eq 0 ]; then
        echo "Le logiciel s'est arrêté correctement."
    else
        echo "Erreur lors du démarrage du logiciel."
    fi
fi

echo "Fermeture Lanceur"
