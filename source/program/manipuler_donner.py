"""
Module de gestion et de manipulation des configurations de données du Lanceur UPBGE.

Ce module fournit des fonctions pour sauvegarder et charger des données de configuration 
pour les projets de jeux Linux et Windows, en gérant les informations de fichiers et de projets.
"""

import json
import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from .construire_structure import (
    config, linux_json, windows_json, 
    icon_json, dos_linux, 
    dos_moteur, dos_windows,
    global_json, config_json,
    )

def sauvegarder():
    """
    Sauvegarde les informations des projets pour les jeux Linux et Windows.

    Cette fonction met à jour les fichiers de configuration JSON avec l'état actuel 
    des projets dans les répertoires de données Linux et Windows. Elle analyse 
    les répertoires de projets et enregistre les fichiers de chaque projet.

    La fonction met à jour deux fichiers de configuration principaux :
    - config_linux.json : Contient les informations des projets Linux
    - config_windows.json : Contient les informations des projets Windows
    """
    # Charger et mettre à jour la configuration Linux
    with open((config / linux_json), "r") as f:
        linux: dict = json.load(f)

    # Parcourir les projets Linux
    for dossier in dos_linux.iterdir():
        for projet in dossier.iterdir():
            if dossier.name == "2x":
                linux["projet"]["2x"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): linux["projet"]["2x"][str(projet)].append(str(fichier))
            elif dossier.name == "3x":
                linux["projet"]["3x"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): linux["projet"]["3x"][str(projet)].append(str(fichier))
            elif dossier.name == "4x":
                linux["projet"]["4x"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): linux["projet"]["4x"][str(projet)].append(str(fichier))
            elif dossier.name == "Range":
                linux["projet"]["Range"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): linux["projet"]["Range"][str(projet)].append(str(fichier))
    
    with open((config / windows_json), "r") as f:
        windows: dict = json.load(f)

    # Parcourir les projets Windows
    for dossier in dos_windows.iterdir():
        for projet in dossier.iterdir():
            if dossier.name == "2x":
                windows["projet"]["2x"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): windows["projet"]["2x"][str(projet)].append(str(fichier))
            elif dossier.name == "3x":
                windows["projet"]["3x"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): windows["projet"]["3x"][str(projet)].append(str(fichier))
            elif dossier.name == "4x":
                windows["projet"]["4x"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): windows["projet"]["4x"][str(projet)].append(str(fichier))
            elif dossier.name == "Range":
                windows["projet"]["Range"][str(projet)] = []
                for fichier in projet.iterdir():
                    if fichier.is_file(): windows["projet"]["Range"][str(projet)].append(str(fichier))

    with open((config / icon_json), "r") as f:
        icon: dict = json.load(f)
    for dossier in dos_moteur.iterdir():
        if dossier.is_file():
            if dossier.name == "linux-svgrepo-com.svg": icon["linux"] = str(dossier)
            if dossier.name == "microsoft.svg": icon["windows"] = str(dossier)
            if dossier.name == "upbge.svg": icon["upbge"] = str(dossier)
            if dossier.name == "range.svg": icon["range"] = str(dossier)
        if dossier.is_dir():
            if dossier.name == "Windows-2x": windows["executable"]["Windows-2x"] = str(dossier / "blender.exe")
            if dossier.name == "Windows-3x": windows["executable"]["Windows-3x"] = str(dossier / "blender.exe")
            if dossier.name == "Windows-4x": windows["executable"]["Windows-4x"] = str(dossier / "blender.exe")
            if dossier.name == "Windows-Range": windows["executable"]["Windows-Range"] = str(dossier / "RangeEngine.exe")
            if dossier.name == "Windows-2x": windows["executable"]["game-2x"] = str(dossier / "blenderplayer.exe")
            if dossier.name == "Windows-3x": windows["executable"]["game-3x"] = str(dossier / "blenderplayer.exe")
            if dossier.name == "Windows-4x": windows["executable"]["game-4x"] = str(dossier / "blenderplayer.exe")
            if dossier.name == "Windows-Range": windows["executable"]["game-W-Range"] = str(dossier / "RangeRuntime.exe")
            if dossier.name == "Linux-2x": linux["executable"]["Linux-2x"] = str(dossier / "blender")
            if dossier.name == "Linux-3x": linux["executable"]["Linux-3x"] = str(dossier / "blender")
            if dossier.name == "Linux-4x": linux["executable"]["Linux-4x"] = str(dossier / "blender")
            if dossier.name == "Linux-Range": linux["executable"]["Linux-Range"] = str(dossier / "RangeEngine")
            if dossier.name == "Linux-2x": linux["executable"]["game-2x"] = str(dossier / "blenderplayer")
            if dossier.name == "Linux-3x": linux["executable"]["game-3x"] = str(dossier / "blenderplayer")
            if dossier.name == "Linux-4x": linux["executable"]["game-4x"] = str(dossier / "blenderplayer")
            if dossier.name == "Linux-Range": linux["executable"]["game-L-Range"] = str(dossier / "RangeRuntime")
    
    with open((config / linux_json), "w", encoding="utf-8") as f: json.dump(linux, f, indent=4)
    with open((config / windows_json), "w", encoding="utf-8") as f: json.dump(windows, f, indent=4)
    with open((config / icon_json), "w", encoding="utf-8") as f: json.dump(icon, f, indent=4)

def charger(element):
    """
    Charge les données de configuration pour un élément spécifique.

    Args:
        element (str): Le type de configuration à charger. 
                       Valeurs possibles : 'linux', 'windows', 'icon', etc.

    Returns:
        dict: Les données de configuration pour l'élément spécifié.
              Retourne un dictionnaire vide si l'élément n'est pas trouvé.

    Raises:
        FileNotFoundError: Si le fichier de configuration ne peut pas être trouvé.
        json.JSONDecodeError: Si le fichier de configuration n'est pas un JSON valide.
    """
    try:
        if element == "linux":
            with open((config / linux_json), "r") as f:
                linux: dict = json.load(f)
            return linux
        elif element == "windows":
            with open((config / windows_json), "r") as f:
                windows: dict = json.load(f)
            return windows
        elif element == "icon":
            with open((config / icon_json), "r") as f:
                icon: dict = json.load(f)
            return icon
        elif element == "global":
            with open((config / global_json), "r") as f:
                glob = json.load(f)
            return glob
        elif element == "config":
            with open((config / config_json), "r") as f:
                conf = json.load(f)
            return conf
        else:
            print(f"Erreur: élément '{element}' non reconnu. Choix possible: [linux, windows, icon, global, config]")
        return None
    except FileNotFoundError:
        print(f"Erreur: Le fichier de configuration pour '{element}' n'existe pas")
        return None
    except json.JSONDecodeError:
        print(f"Erreur: Le fichier de configuration pour '{element}' est invalide")
        return None
