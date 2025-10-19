# exporter le projet
# le moteur
# encoder les données de projets
# créer un lanceur avec décodeur
# choisir l'enplacement de l'export des porjets
from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit
                               , QFileDialog, QPushButton, QComboBox, QGridLayout)
from PySide6.QtCore import (Slot, Qt)
from PySide6.QtGui import (QIcon)
import pathlib, platform
from subprocess import run
from program.manipuler_donner import charger

class Exportation(QWidget):
    def __init__(self):
        super().__init__()
        self.data_launcher = charger("config_launcher")
        icone = self.data_launcher['icon']
        self.dos_moteur = []
        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(2)

        # Titre & Texte
        T_sortie_jeu = QLabel("dossier d'export: ")
        T_dos_projet = QLabel("dossier projet: ")

        # chemin d'exportation
        self.sortie_jeu = QLineEdit()
        self.select_sortie_jeu = QPushButton("++")
        self.select_sortie_jeu.clicked.connect(lambda: self.selection_dossier(0))

        # chemin de projet
        self.projet_jeu = QLineEdit()
        self.select_projet_jeu = QPushButton("+-")
        self.select_projet_jeu.clicked.connect(lambda: self.selection_dossier(1))

        # bouton exportation
        self.b_export = QPushButton("Export")
        self.b_export.clicked.connect(lambda: self.exportation_projet())

        # Configurer la liste des moteurs de jeu
        self.liste_moteur = QComboBox()
        if platform.system() == "Linux":
            self.linux = self.data_launcher["linux"]
            for cle in self.linux:
                if cle == "executable":
                    for p in self.linux[cle]:
                        if pathlib.Path(self.linux[cle][p]).exists():
                            if p.startswith("Linux"):
                                self.liste_moteur.addItem(QIcon(icone.get("linux")), p)
                                self.dos_moteur.append(pathlib.Path(self.linux[cle][p]).parent)
        self.windows = self.data_launcher["windows"]
        for cle in self.windows:
            if cle == "executable":
                for p in self.windows[cle]:
                    if pathlib.Path(self.windows[cle][p]).exists():
                        if p.startswith("Windows"):
                            self.liste_moteur.addItem(QIcon(icone.get("windows")), p)
                            self.dos_moteur.append(pathlib.Path(self.windows[cle][p]).parent)

        # Disposition des widgets dans la grille
        conteneur.addWidget(T_dos_projet, 0, 0, 1, 1)
        conteneur.addWidget(self.projet_jeu, 0, 1, 1, 1)
        conteneur.addWidget(self.select_projet_jeu, 0, 2, 1, 1)

        conteneur.addWidget(self.liste_moteur, 1, 0, 1, 3)
        conteneur.addWidget(self.b_export, 2, 0, 1, 3)
        # Définir la disposition
        self.setLayout(conteneur)
        self.setFixedSize(400, (30*3))
        self.setWindowTitle("Exporter")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["export_projet"]))

    @Slot()
    def exportation_projet(self):
        dossier_moteur = ""
        projet = pathlib.Path(self.projet_jeu.text())
        destination = pathlib.Path(charger("config_launcher")["configuration"]["dossier_export"])
        moteur = self.liste_moteur.currentText()
        for i in self.dos_moteur:
            if moteur == i.name:
                dossier_moteur = i
        #print(f"{destination}\n{projet}\n{moteur}")
        lanceur = ""
        if platform.system() == "Linux":
            if moteur in ["Linux-2x", "Linux-3x", "Linux-4x"]:
                lanceur = "blenderplayer"
            elif moteur in ["Linux-Range"]:
                lanceur = "RangeRuntime"
        if moteur in ["Windows-2x", "Windows-3x", "Windows-4x"]:
            lanceur = "blenderplayer.exe"
        elif moteur in ["Windows-Range"]:
            lanceur = "RangeRuntime.exe"
        self.copi_element(projet, dossier_moteur, destination, lanceur)
        self.lanceurDeJeuSimple(projet, destination, lanceur)
        self.destroy() # Fermer la fenêtre

    @Slot()
    def selection_dossier(self, valeur=None):
        # Ouvrir la boîte de dialogue pour sélectionner un dossier
        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if dossier:
            if valeur == 0:
                self.sortie_jeu.setText(dossier)  # Afficher le chemin du dossier sélectionné
            elif valeur == 1:
                self.projet_jeu.setText(dossier)  # Afficher le chemin du dossier sélectionné

    def copi_element(self, projet, moteur, sortie: pathlib.Path, executable):
        """
        Copie et organise les éléments nécessaires pour l'exportation d'un projet UPBGE.
        
        Args:
            projet (Path): Chemin vers le dossier du projet à exporter
            moteur (str): Chemin vers le dossier du moteur de jeu (UPBGE)
            sortie (Path): Dossier de destination pour l'export
            executable (str): Nom du fichier exécutable du moteur (ex: 'blenderplayer' ou 'RangeRuntime')
        """
        # Créer le dossier de destination pour le projet exporté
        dos_projet = (sortie / projet.name)
        if not (sortie/projet.name).exists(): (sortie/projet.name).mkdir(exist_ok=True)

        # 1. Copier tout le contenu du projet vers le dossier de destination
        if platform.system() == "Windows": run(["xcopy", (projet / "data"), dos_projet], check=True)
        else: run(["cp", "-r", (projet / "data"), dos_projet], check=True)
            

        # 2. Réorganiser la structure du projet:
        #    - Supprimer l'ancien dossier 'data' s'il existe
        #    - Renommer le dossier du projet en 'data' pour la structure standard UPBGE
        """if (dos_projet / "data").exists():
            run(["rm", "-rf", (dos_projet / "data")], check=True)
        run(["mv", (dos_projet / projet.name), (dos_projet / "data")], check=True)"""

        # 3. Copier le moteur de jeu dans le dossier du projet
        if platform.system() == "Windows": run(["xcopy", moteur, dos_projet], check=True)
        else: run(["cp", "-r", moteur, dos_projet], check=True)
        new_dossier = (dos_projet / moteur.name)
        
        # 4. Nettoyer les fichiers inutiles du moteur:
        #    - Garder uniquement l'exécutable spécifié
        #    - Pour Windows, conserver les .dll nécessaires
        for i in new_dossier.iterdir():
            if i.is_file():
                if i.name != executable:
                    if executable in ["RangeRuntime", "RangeRuntime.exe"]: print("tous concerver")
                    elif executable in ["blenderplayer.exe"]:
                        if not i.name.endswith(".dll"):
                            if platform.system() == "Windows": run(["del", i], check=True)     
                            else: run(["rm", i], check=True)                        
                    else: 
                        try:
                            run(["rm", i], check=True)
                        except: pass
        addons = list(new_dossier.glob('**/scripts'))
        if addons:  # Vérifier si le dossier scripts existe
            for i in addons[0].iterdir():
                if i.is_dir():
                    if i.name not in ["bge", "freestyle", "modules"]:
                        if platform.system() == "Windows": run(["rmdir", "/s", "/q", i], check=True)
                        else: run(["rm", "-rf", i], check=True)
        
        # 6. Renommer le dossier du moteur en 'engine' pour la structure standard
        if (dos_projet / "engine").exists():
            if platform.system() == "Windows": run(["rmdir", "/s", "/q", (dos_projet / "engine")], check=True)
            else: run(["rm", "-rf", (dos_projet / "engine")], check=True)
        if platform.system() == "Windows": run(["MOVE", new_dossier, (new_dossier.parent / "engine")], check=True)
        else: run(["mv", new_dossier, (new_dossier.parent / "engine")], check=True)

    def lanceurDeJeuSimple(self, jeu, sortie, executable):
        """
        Crée un script shell pour lancer le jeu exporté.
        
        Args:
            jeu (Path): Chemin vers le dossier du projet source
            sortie (Path): Dossier de destination de l'export
            executable (str): Nom du fichier exécutable du moteur
        """
        # Trouver le fichier .blend ou .range dans le dossier data
        data_dir = sortie / jeu.name / "data"
        f_blend = []
        
        if 'blenderplayer' in executable.lower():
            f_blend = list(data_dir.glob('*.blend'))
        elif 'rangeruntime' in executable.lower():
            f_blend = list(data_dir.glob('*.range'))
        
        if not f_blend:
            print("Aucun fichier .blend ou .range trouvé dans le dossier data du projet")
            return
        
        if platform.system() == "Linux":
            data_path = f"./data/{f_blend[0].name}"
            script_path = (sortie / jeu.name / f"{jeu.name}.sh").resolve()
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n\n")
                f.write("# Obtenir le chemin absolu du script\n")
                f.write('DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"\n\n')
                
                f.write("# Se déplacer dans le répertoire du script\n")
                f.write('cd "$DIR" || exit 1\n\n')
                
                f.write("# Chemins des fichiers\n")
                f.write('MOTEUR="$DIR/engine/' + executable + '"\n')
                f.write('FICHIER="$DIR/' + data_path + '"\n')
                f.write('DOSSIER_DONNEES="$DIR/data"\n\n')
                
                f.write("# Vérifier que les fichiers existent\n")
                f.write('if [ ! -f "$MOTEUR" ]; then\n')
                f.write('    echo "Erreur: $MOTEUR introuvable" >&2\n')
                f.write('    echo "Recherche dans: $MOTEUR" >&2\n')
                f.write('fi\n\n')
                
                f.write('echo "Démarrage du jeu depuis: $DIR"\n')
                f.write('echo "Exécution de: $MOTEUR $FICHIER"\n\n')
                
                f.write('# Définir le chemin des bibliothèques\n')
                f.write('export LD_LIBRARY_PATH="$DIR/engine/lib:$LD_LIBRARY_PATH"\n\n')
                
                f.write('# Fonction pour convertir les chemins Linux en chemins Windows pour Wine\n')
                f.write('wine_path() {\n')
                f.write('    local path="$1"\n')
                f.write('    # Convertir le chemin en chemin Windows\n')
                f.write('    if command -v winepath >/dev/null 2>&1; then\n')
                f.write('        path=$(winepath -w "$path" 2>/dev/null)\n')
                f.write('    else\n')
                f.write('        # Fallback si winepath n\'est pas disponible\n')
                f.write('        path=$(echo "$path" | sed \'s|^/mnt/\([a-zA-Z]\+\)|\1:|\' | sed \'s|/|\\\\|g\')\n')
                f.write('    fi\n')
                f.write('    echo "$path"\n}\n')
                f.write('\n# Exécuter le jeu avec Wine pour les .exe, sinon directement\n')
                f.write('if [[ "' + executable + '" == *".exe" ]]; then\n')
                f.write('    echo "Lancement avec Wine..."\n')
                f.write('    # Convertir les chemins pour Wine\n')
                f.write('    WIN_MOTEUR=$(wine_path "$MOTEUR")\n')
                f.write('    WIN_FICHIER=$(wine_path "$FICHIER")\n')
                f.write('    # Démarrer en mode fenêtré avec des dimensions fixes\n')
                f.write('    wine "$WIN_MOTEUR" "$WIN_FICHIER"\n')
                f.write('else\n')
                f.write('    # Mode natif\n')
                f.write('    exec "$MOTEUR" "$FICHIER"\n')
                f.write('fi\n\n')
                
                f.write('# Garder la fenêtre ouverte en cas d\'erreur\n')
                f.write('if [ $? -ne 0 ]; then\n')
                f.write('    echo -e "\\nLe jeu s\'est arrêté avec une erreur. Appuyez sur Entrée pour quitter..."\n')
                f.write('    read -r\n')
                f.write('fi\n')
                
                f.write('# Vérifier si Wine est installé (uniquement pour les .exe)\n')
                f.write('if [[ "' + executable + '" == *".exe" ]]; then\n')
                f.write('    if ! command -v wine >/dev/null 2>&1; then\n')
                f.write('        echo "Erreur: Wine n\'est pas installé. Impossible de lancer les exécutables Windows." >&2\n')
                f.write('        echo "Installez Wine avec: sudo apt install wine" >&2\n')
                f.write('        read -p "Appuyez sur Entrée pour quitter..."\n')
                f.write('        exit 1\n')
                f.write('    fi\n')
                f.write('fi\n')
            try:
                run(["chmod", "+x", (sortie / jeu.name / (str(jeu.name)+".sh"))], check=True)
            except: pass
        elif platform.system() == "Windows":
            data_path = f"\data\{f_blend[0].name}"
            script_path = (sortie / jeu.name / f"{jeu.name}.bat").resolve()
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(f"@echo off\n")
                f.write(f"setlocal enabledelayedexpansion\n\n")
                f.write(f":: Configuration\n")
                f.write(f"set DIR=%~dp0\n")
                f.write(f"set MOTEUR=%DIR%engine\\{executable}\n")
                f.write(f"set FICHIER=%DIR%{data_path}\n\n")
                f.write(f":: Vérifier que les fichiers existent\n")
                f.write(f'if not exist "%MOTEUR%" (\n')
                f.write(f'    echo Erreur: "%MOTEUR%" introuvable\n')
                f.write(f'    echo Recherche dans: "%MOTEUR%"\n')
                f.write(f'    pause\n')
                f.write(f'    exit /b 1\n')
                f.write(f')\n\n')
                f.write(f'echo Démarrage du jeu depuis: %DIR%\n')
                f.write(f'echo Exécution de: "%MOTEUR%" "%FICHIER%"\n\n')
                f.write(f'"%MOTEUR%" "%FICHIER%"\n\n')
                f.write(f':: Garder la fenêtre ouverte en cas d\'erreur\n')
                f.write(f'if %errorlevel% neq 0 (\n')
                f.write(f'    echo.\n')
                f.write(f'    echo Le jeu s\'est arrêté avec une erreur. Appuyez sur Entrée pour quitter...\n')
                f.write(f'    pause\n')
                f.write(f')\n')
            try:
                run(["chmod", "+x", (sortie / jeu.name / (str(jeu.name)+".bat"))], check=True)
            except: pass
