from pathlib import Path
from icecream import ic

racine = Path(__file__).parent
linux = {
    "projet":
        {
            "2x": {},
            "3x": {},
            "4x": {},
        },
    "executable":
        {
            "Linux-2x": "",
            "Linux-3x": "",
            "Linux-4x": "",
            "game-2x": "",
            "game-3x": "",
            "game-4x": "",
        },
}
windows = {
    "projet":
        {
            "2x": {},
            "3x": {},
            "4x": {},
        },
    "executable":
        {
            "Windows-2x": "",
            "Windows-3x": "",
            "Windows-4x": "",
            "game-2x": "",
            "game-3x": "",
            "game-4x": "",
        },
}
icon = {
    "linux": "",
    "windows": "",
    "upbge": "",
}


def structure():
    dos_moteur = racine / "Moteur"
    dos_linux = racine / "Linux"
    dos_windows = racine / "Windows"

    if not dos_linux.exists(): dos_linux.mkdir(exist_ok=True)
    for version_l in ["2x", "3x", "4x"]:
        chemin_l = dos_linux / version_l
        if not chemin_l.exists(): chemin_l.mkdir(exist_ok=True)

    if not dos_windows.exists(): dos_windows.mkdir(exist_ok=True)
    for version_w in ["2x", "3x", "4x"]:
        chemin_w = dos_windows / version_w
        if not chemin_w.exists(): chemin_w.mkdir(exist_ok=True)

    if not dos_moteur.exists(): dos_moteur.mkdir(exist_ok=True)
    for version_m in ["Linux-2x", "Linux-3x", "Linux-4x", "Windows-2x", "Windows-3x", "Windows-4x"]:
        chemin_m = dos_moteur / version_m
        if not chemin_m.exists(): chemin_m.mkdir(exist_ok=True)

    for dos_l in dos_linux.iterdir():
        if dos_l.name == "2x":
            for projet in dos_l.iterdir():
                linux["projet"]["2x"][projet] = []
                for fichier in projet.iterdir():
                    if fichier.is_file():
                        linux["projet"]["2x"][projet].append(fichier)
        if dos_l.name == "3x":
            for projet in dos_l.iterdir():
                linux["projet"]["3x"][projet] = []
                for fichier in projet.iterdir():
                    if fichier.is_file():
                        linux["projet"]["3x"][projet].append(fichier)
        if dos_l.name == "4x":
            for projet in dos_l.iterdir():
                linux["projet"]["4x"][projet] = []
                for fichier in projet.iterdir():
                    if fichier.is_file():
                        linux["projet"]["4x"][projet].append(fichier)
    for dos_w in dos_windows.iterdir():
        if dos_w.name == "2x":
            for projet in dos_w.iterdir():
                windows["projet"]["2x"][projet] = []
                for fichier in projet.iterdir():
                    if fichier.is_file():
                        windows["projet"]["2x"][projet].append(fichier)
        if dos_w.name == "3x":
            for projet in dos_w.iterdir():
                windows["projet"]["3x"][projet] = []
                for fichier in projet.iterdir():
                    if fichier.is_file():
                        windows["projet"]["3x"][projet].append(fichier)
        if dos_w.name == "4x":
            for projet in dos_w.iterdir():
                windows["projet"]["4x"][projet] = []
                for fichier in projet.iterdir():
                    if fichier.is_file():
                        windows["projet"]["4x"][projet].append(fichier)
    for dos_m in dos_moteur.iterdir():
        if dos_m.is_file():
            if dos_m.name == "linux-svgrepo-com.svg": icon["linux"] = dos_m
            if dos_m.name == "microsoft.svg": icon["windows"] = dos_m
            if dos_m.name == "upbge.svg": icon["upbge"] = dos_m
        if dos_m.is_dir():
            if dos_m.name == "Windows-2x": windows["executable"]["Windows-2x"] = dos_m / "blender.exe"
            if dos_m.name == "Windows-3x": windows["executable"]["Windows-3x"] = dos_m / "blender.exe"
            if dos_m.name == "Windows-4x": windows["executable"]["Windows-4x"] = dos_m / "blender.exe"
            if dos_m.name == "Windows-2x": windows["executable"]["game-2x"] = dos_m / "blenderplayer.exe"
            if dos_m.name == "Windows-3x": windows["executable"]["game-3x"] = dos_m / "blenderplayer.exe"
            if dos_m.name == "Windows-4x": windows["executable"]["game-4x"] = dos_m / "blenderplayer.exe"
            if dos_m.name == "Linux-2x": linux["executable"]["Linux-2x"] = dos_m / "blender"
            if dos_m.name == "Linux-3x": linux["executable"]["Linux-3x"] = dos_m / "blender"
            if dos_m.name == "Linux-4x": linux["executable"]["Linux-4x"] = dos_m / "blender"
            if dos_m.name == "Linux-2x": linux["executable"]["game-2x"] = dos_m / "blenderplayer"
            if dos_m.name == "Linux-3x": linux["executable"]["game-3x"] = dos_m / "blenderplayer"
            if dos_m.name == "Linux-4x": linux["executable"]["game-4x"] = dos_m / "blenderplayer"


if __name__ == "__main__":
    structure()
