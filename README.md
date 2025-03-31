# Lanceur_upbge
un lanceur et gestionnaire de projet UP(BGE)

- dépendence pip :
    - requis :
        - PySide6
    - pour la documentation:
        - sphinx
        - furo
    - pour créer un exécutable:
        - nuitka

utilisez la commande suivante:
```
pip install -r dependence.txt
```

## Utilisation

```
python3 source/lanceur.py
```
---
# Linux
utilisation de wine pour les projets sous Windows

```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine64 wine32 wine winetricks
```
---
# Construction du projet
```bash
# cloner le projet
git clone https://github.com/LLS-lopos/Launcher_upbge.git
# naviguer dans le projet
cd Launcher_upbge
mkdir nuitka_build && cd nuitka_build
# construction
nuitka3 --standalone --plugin-enable=pyside6 ../source/lanceur.py --include-data-dir=../source/style=./style --include-data-files=../source/data/Moteur/*.svg=./data/Moteur/ --include-package=GUI --include-package=program
```
---
## interface && Style
[Feuille de style](https://qss-stock.devsecstudio.com/index.php) sous licences MIT
- fusion
![](./info/img-1.jpg)
- windows
![](./info/theme-windows.jpeg)
- standard
![](./info/theme-standard.jpeg)
- combinear
![](./info/theme-combinear.jpeg)
- diffnes
![](./info/theme-diffnes.jpeg)
- genetive
![](./info/theme-genetive.jpeg)
---
# TODO

- ajouter un support blender
- rendre plus efficace la reconnaissance des exécutable logiciel
---
Projet en cours de conception