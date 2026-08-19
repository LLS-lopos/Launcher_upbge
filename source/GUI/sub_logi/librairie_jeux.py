# sera une fenêtre de bibliothèque de jeu créer avec le Lanceur

import json, platform
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import (Slot)
from PySide6.QtGui import QIcon
from Fonction.manipuler_donner import config_launcher_json, config, charger
from pathlib import Path
from subprocess import Popen, PIPE

class Jeu(QWidget):
    def __init__(self):
        super().__init__()
        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(4)

        ### code ###
        lib = Path(charger("preference")["dossier_export"])
        dossier = []
        for i in lib.iterdir():
            if i.is_dir():
                dossier.append(i)
        bouton_lib = self.creation_bouton(dossier)
        
        for b, i in enumerate(bouton_lib):
            ligne = b // 4
            col = b % 4
            conteneur.addWidget(i[0], ligne, col, 1, 1)
        ### code ###

        self.setLayout(conteneur)
        self.setFixedSize((400+4*conteneur.spacing()), ((60*(len(bouton_lib)//4)+60 if len(bouton_lib)%4 else 60*(len(bouton_lib)//4))+4*conteneur.spacing()))
        self.setWindowTitle("Biblihothèque de Jeu")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["game"]))

    def creation_bouton(self, bouton):
        lib_bibli = []
        for dossier in bouton:
            for fichier in dossier.iterdir():
                if fichier.is_file():
                    if fichier.name.endswith(".sh"):
                        b = QPushButton(fichier.name.replace(".sh", ""))
                        b.setFixedSize(100, 60)
                        b.clicked.connect(lambda checked, f=fichier: self.lancer_jeu(f))
                        lib_bibli.append([b, fichier])
                    elif fichier.name.endswith(".bat"):
                        b = QPushButton(fichier.name.replace(".bat", ""))
                        b.setFixedSize(100, 60)
                        b.clicked.connect(lambda checked, f=fichier: self.lancer_jeu(f))
                        lib_bibli.append([b, fichier])
        return lib_bibli
    
    @Slot()
    def lancer_jeu(self, exe):
        """print(exe)
        run(["/bin/bash", str(exe)], check=True)
        """
        print(f"Tentative de lancement: {exe}")
        try:
            # Vérifier si le fichier existe et est exécutable
            if not exe.exists():
                print(f"Erreur: Le fichier {exe} n'existe pas")
                return
                
            # Rendre le fichier exécutable
            exe.chmod(0o755)
            
            # Lancer le script en spécifiant explicitement le shell
            if platform.system() == "Windows":
                Popen([str(exe)])
            else:
                Popen(
                    ['/bin/bash', str(exe)],
                    stdin=PIPE,
                    stdout=PIPE,
                    stderr=PIPE,
                    start_new_session=True,
                    )
            
        except Exception as e:
            print(f"Erreur lors du lancement du jeu: {e}")
            print("Assurez-vous que le fichier est un script shell valide et qu'il a les permissions d'exécution.")
            # Essayer d'ouvrir le fichier avec l'application par défaut
            import os
            os.system(f'xdg-open "{exe}"')