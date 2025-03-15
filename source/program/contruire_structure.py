import pathlib
import json

# variable
racine = pathlib.Path(__file__).parent.parent
config = pathlib.Path.home() / ".LanceurUpBGE"
dos_moteur = racine / "Moteur"
dos_linux = racine / "Linux"
dos_windows = racine / "Windows"
linux_json = "config_linux.json"
windows_json = "config_windows.json"
icon_json = "config_icon.json"

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
    if not (config / linux_json).exists():
        with open((config / linux_json), "w", encoding="utf-8") as f: json.dump(linux, f, indent=4)
    if not (config / windows_json).exists():
        with open((config / windows_json), "w", encoding="utf-8") as f: json.dump(windows, f, indent=4)
    if not (config / icon_json).exists():
        with open((config / icon_json), "w", encoding="utf-8") as f: json.dump(icon, f, indent=4)


if __name__ == "__main__":
    structure()
