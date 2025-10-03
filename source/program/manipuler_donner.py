"""
Module de gestion et de manipulation des configurations de données du Lanceur UPBGE.

Ce module fournit des fonctions pour sauvegarder et charger des données de configuration 
pour les projets de jeux Linux et Windows, en gérant les informations de fichiers et de projets.
"""

import json, os, sys, platform

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from .construire_structure import (
    config, dos_linux, dos_icon,
    dos_moteur, dos_windows,
    global_json, config_launcher_json,
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
    # Fichier de configuration unique
    with open((config / config_launcher_json), 'r') as f:
        config_launcher: dict = json.load(f)
    
    # Parcourir les projets Linux
    if platform.system() == "Linux":
        for dossier in dos_linux.iterdir():
            for projet in dossier.iterdir():
                if dossier.name in ["2x", "3x", "4x", "Range"]:
                    config_launcher["linux"]["projet"][dossier.name][str(projet)] = []
                    # Ajouter les fichiers du dossier projet/data s'il existe
                    data_dir = projet / "data"
                    if data_dir.exists() and data_dir.is_dir():
                        for fichier in data_dir.iterdir():
                            if fichier.is_file():
                                config_launcher["linux"]["projet"][dossier.name][str(projet)].append(str(fichier))

    # Parcourir les projets Windows
    for dossier in dos_windows.iterdir():
        for projet in dossier.iterdir():
            if dossier.name in ["2x", "3x", "4x", "Range"]:
                config_launcher["windows"]["projet"][dossier.name][str(projet)] = []
                # Ajouter les fichiers du dossier projet/data s'il existe
                data_dir = projet / "data"
                if data_dir.exists() and data_dir.is_dir():
                    for fichier in data_dir.iterdir():
                        if fichier.is_file():
                            config_launcher["windows"]["projet"][dossier.name][str(projet)].append(str(fichier))
            
    # Icone / Exécutable
    for dossier in dos_icon.iterdir():
        if dossier.is_file():
            if platform.system() == "Linux":
                if dossier.name == "linux-svgrepo-com.svg": config_launcher["icon"]["linux"] = str(dossier)
            if dossier.name == "microsoft.svg": config_launcher["icon"]["windows"] = str(dossier)
            if dossier.name == "upbge.svg": config_launcher["icon"]["upbge"] = str(dossier)
            if dossier.name == "range.svg": config_launcher["icon"]["range"] = str(dossier)
            if dossier.name == "blender.svg": config_launcher["icon"]["blender"] = str(dossier)
            if dossier.name == "nouveau_projet.svg": config_launcher["icon"]["nouveau_projet"] = str(dossier)
            if dossier.name == "export_projet.svg": config_launcher["icon"]["export_projet"] = str(dossier)
            if dossier.name == "config_logiciel.svg": config_launcher["icon"]["config_logiciel"] = str(dossier)
            if dossier.name == "game.svg": config_launcher["icon"]["game"] = str(dossier)
    for dossier in dos_moteur.iterdir():
        if dossier.is_dir():
            if dossier.name == "Windows-2x": config_launcher["windows"]["executable"]["Windows-2x"] = str(dossier / "blender.exe")
            if dossier.name == "Windows-3x": config_launcher["windows"]["executable"]["Windows-3x"] = str(dossier / "blender.exe")
            if dossier.name == "Windows-4x": config_launcher["windows"]["executable"]["Windows-4x"] = str(dossier / "blender.exe")
            if dossier.name == "Windows-Range": config_launcher["windows"]["executable"]["Windows-Range"] = str(dossier / "RangeEngine.exe")
            if dossier.name == "Windows-2x": config_launcher["windows"]["executable"]["game-2x"] = str(dossier / "blenderplayer.exe")
            if dossier.name == "Windows-3x": config_launcher["windows"]["executable"]["game-3x"] = str(dossier / "blenderplayer.exe")
            if dossier.name == "Windows-4x": config_launcher["windows"]["executable"]["game-4x"] = str(dossier / "blenderplayer.exe")
            if dossier.name == "Windows-Range": config_launcher["windows"]["executable"]["game-W-Range"] = str(dossier / "RangeRuntime.exe")
            if platform.system() == "Linux":
                if dossier.name == "Linux-2x": config_launcher["linux"]["executable"]["Linux-2x"] = str(dossier / "blender")
                if dossier.name == "Linux-3x": config_launcher["linux"]["executable"]["Linux-3x"] = str(dossier / "blender")
                if dossier.name == "Linux-4x": config_launcher["linux"]["executable"]["Linux-4x"] = str(dossier / "blender")
                if dossier.name == "Linux-Range": config_launcher["linux"]["executable"]["Linux-Range"] = str(dossier / "RangeEngine")
                if dossier.name == "Linux-2x": config_launcher["linux"]["executable"]["game-2x"] = str(dossier / "blenderplayer")
                if dossier.name == "Linux-3x": config_launcher["linux"]["executable"]["game-3x"] = str(dossier / "blenderplayer")
                if dossier.name == "Linux-4x": config_launcher["linux"]["executable"]["game-4x"] = str(dossier / "blenderplayer")
                if dossier.name == "Linux-Range": config_launcher["linux"]["executable"]["game-L-Range"] = str(dossier / "RangeRuntime")

    with open((config / config_launcher_json), 'w', encoding="utf-8") as f: json.dump(config_launcher, f, indent=4)

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
        if element == "global":
            with open((config / global_json), "r") as f:
                glob = json.load(f)
            return glob
        elif element == "config_launcher":
            with open((config / config_launcher_json), 'r') as f:
                launcher: dict = json.load(f)
            return launcher
        else:
            print(f"Erreur: élément '{element}' non reconnu. Choix possible: [linux, windows, icon, global, config]")
        return None
    except FileNotFoundError:
        print(f"Erreur: Le fichier de configuration pour '{element}' n'existe pas")
        return None
    except json.JSONDecodeError:
        print(f"Erreur: Le fichier de configuration pour '{element}' est invalide")
        return None
