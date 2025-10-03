"""
Module de construction et de gestion de la structure du projet pour le Lanceur UPBGE.

Ce module définit la structure des répertoires et de configuration de l'application,
en configurant les chemins pour différents moteurs de jeu, types de projets et fichiers de configuration.
"""

import pathlib, platform, json, os, sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

# Définir les chemins de base pour la structure du projet
racine = pathlib.Path(__file__).parent.parent
config = pathlib.Path.home() / ".LanceurUpBGE"
source = racine / "data"
dos_moteur = source / "Moteur"
dos_linux = source / "Linux"
dos_windows = source / "Windows"
dos_icon = source / "icone"

# Noms des fichiers de configuration
global_json = "config_global.json"
config_launcher_json = "config_launcher.json"

# Dictionnaire de configuration logiciel
config_launcher = {
    "icon": {
        "linux": "",
        "windows": "",
        "upbge": "",
        "range": "",
        "blender": "",
        "nouveau_projet": "",
        "export_projet": "",
        "config_logiciel": "",
        "game": "",
    },
    "theme": "",
    "windows": {
        "projet": {
            "2x": {},
            "3x": {},
            "4x": {},
            "Range": {},
        },
        "executable": {
            "Windows-2x": "",
            "Windows-3x": "",
            "Windows-4x": "",
            "Windows-Range": "",
            "game-2x": "",
            "game-3x": "",
            "game-4x": "",
            "game-W-Range": "",
        },
    },
    "linux": {
        "projet": {
            "2x": {},
            "3x": {},
            "4x": {},
            "Range": {},
        },
        "executable": {
            "Linux-2x": "",
            "Linux-3x": "",
            "Linux-4x": "",
            "Linux-Range": "",
            "game-2x": "",
            "game-3x": "",
            "game-4x": "",
            "game-L-Range": "",
        },
    },
    "configuration": {
        "dossier_export": "",
    },
}
if platform.system() == "Windows": 
    config_launcher.pop("linux")
    config_launcher["icon"].pop("linux")
# vérifier si les éléments de "configuration" existe déjà
if (config / config_launcher_json).exists():
    try:
        with open((config / config_launcher_json), 'r') as f: data = json.load(f)
        config_launcher["configuration"]["dossier_export"] = data["configuration"]["dossier_export"]
    except: pass

def structure():
    """
    Créer la structure de base des répertoires et des fichiers de configuration pour le Lanceur UPBGE.

    Cette fonction garantit que tous les répertoires et fichiers de configuration 
    nécessaires existent pour le bon fonctionnement de l'application. Elle crée :
    - Le répertoire de configuration dans le dossier personnel de l'utilisateur
    - Les répertoires de données pour différents moteurs de jeu et types de projets
    - Les fichiers de configuration JSON initiaux
    """
    # Créer le répertoire de configuration
    if not config.exists(): config.mkdir(exist_ok=True)

    # Créer les répertoires de données
    if not source.exists(): source.mkdir(exist_ok=True)
    if platform.system() == "Linux":
        if not dos_linux.exists(): dos_linux.mkdir(exist_ok=True)
        for version_l in ["2x", "3x", "4x", "Range"]:
            chemin_l = dos_linux / version_l
            if not chemin_l.exists(): chemin_l.mkdir(exist_ok=True)
    if not dos_windows.exists(): dos_windows.mkdir(exist_ok=True)
    for version_w in ["2x", "3x", "4x", "Range"]:
        chemin_w = dos_windows / version_w
        if not chemin_w.exists(): chemin_w.mkdir(exist_ok=True)
    if not dos_moteur.exists(): dos_moteur.mkdir(exist_ok=True)
    mt_list = []
    if platform.system() == "Linux": mt_list = ["Linux-2x", "Linux-3x", "Linux-4x", "Linux-Range", "Windows-2x", "Windows-3x", "Windows-4x", "Windows-Range"]
    elif platform.system() == "Windows": mt_list = ["Windows-2x", "Windows-3x", "Windows-4x", "Windows-Range"]
    for version_m in mt_list:
        chemin_m = dos_moteur / version_m
        if not chemin_m.exists(): chemin_m.mkdir(exist_ok=True)
    if not dos_icon.exists(): dos_icon.mkdir(exist_ok=True)

    # Initialisation des fichiers de configuration
    if not config.exists(): config.mkdir(exist_ok=True)
    with open((config / global_json), "w", encoding="utf-8") as f: json.dump("", f, indent=4)
    with open((config / config_launcher_json), 'w', encoding="utf-8") as f: json.dump(config_launcher, f, indent=4)

if __name__ == "__main__":
    structure()
