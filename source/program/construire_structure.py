import pathlib
import json
import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

# variable
racine = pathlib.Path(__file__).parent.parent
config = pathlib.Path.home() / ".LanceurUpBGE"
source = racine / "data"
dos_moteur = source / "Moteur"
dos_linux = source / "Linux"
dos_windows = source / "Windows"
linux_json = "config_linux.json"
windows_json = "config_windows.json"
icon_json = "config_icon.json"
global_json = "config_global.json"

# Dictionnaires pour stocker les informations sur les projets et les exécutables
linux = {
    "projet":
        {
            "2x": {},
            "3x": {},
            "4x": {},
            "Range": {},
        },
    "executable":
        {
            "Linux-2x": "",
            "Linux-3x": "",
            "Linux-4x": "",
            "Linux-Range": "",
            "game-2x": "",
            "game-3x": "",
            "game-4x": "",
            "game-L-Range": "",
        },
}
windows = {
    "projet":
        {
            "2x": {},
            "3x": {},
            "4x": {},
            "Range": {},
        },
    "executable":
        {
            "Windows-2x": "",
            "Windows-3x": "",
            "Windows-4x": "",
            "Windows-Range": "",
            "game-2x": "",
            "game-3x": "",
            "game-4x": "",
            "game-W-Range": "",
        },
}
# Dictionnaire pour stocker les icônes
icon = {
    "linux": "",
    "windows": "",
    "upbge": "",
    "range": "",
}

def structure():
    # Construction du dossier de projet Linux et des répertoire de version
    if not source.exists(): source.mkdir(exist_ok=True)
    if not dos_linux.exists(): dos_linux.mkdir(exist_ok=True)
    for version_l in ["2x", "3x", "4x", "Range"]:
        chemin_l = dos_linux / version_l
        if not chemin_l.exists(): chemin_l.mkdir(exist_ok=True)
    if not dos_windows.exists(): dos_windows.mkdir(exist_ok=True)
    for version_w in ["2x", "3x", "4x", "Range"]:
        chemin_w = dos_windows / version_w
        if not chemin_w.exists(): chemin_w.mkdir(exist_ok=True)
    if not dos_moteur.exists(): dos_moteur.mkdir(exist_ok=True)
    for version_m in ["Linux-2x", "Linux-3x", "Linux-4x", "Linux-Range", "Windows-2x", "Windows-3x", "Windows-4x", "Windows-Range"]:
        chemin_m = dos_moteur / version_m
        if not chemin_m.exists(): chemin_m.mkdir(exist_ok=True)

    # Initialisation des fichiers de configuration
    if not config.exists(): config.mkdir(exist_ok=True)
    with open((config / linux_json), "w", encoding="utf-8") as f: json.dump(linux, f, indent=4)
    with open((config / windows_json), "w", encoding="utf-8") as f: json.dump(windows, f, indent=4)
    with open((config / icon_json), "w", encoding="utf-8") as f: json.dump(icon, f, indent=4)
    with open((config / global_json), "w", encoding="utf-8") as f: json.dump("", f, indent=4)


if __name__ == "__main__":
    structure()
