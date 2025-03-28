import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from pathlib import Path
from subprocess import run

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, QComboBox)
from PySide6.QtCore import (Slot, Qt)
from PySide6.QtGui import (QIcon)
from PIL import Image

from program.manipuler_donner import charger, sauvegarder

class Creer(QWidget):
    def __init__(self, save):
        super().__init__()
        icone = charger("icon")
        self.save = save

        conteneur = QHBoxLayout()

        self.nom_projet = QLineEdit()
        self.nom_projet.setStatusTip("nom du projet")

        self.nom_jeu = QLineEdit()
        self.nom_jeu.setStatusTip("nom du jeu")

        self.liste_moteur = QComboBox()
        self.liste_moteur.setStatusTip("Liste des moteurs disponible")
        self.linux = charger("linux")
        for cle in self.linux:
            if cle == "executable":
                for p in self.linux[cle]:
                    if p.startswith("Linux"):
                        self.liste_moteur.addItem(QIcon(icone.get("linux")), p)
        self.windows = charger("windows")
        for cle in self.windows:
            if cle == "executable":
                for p in self.windows[cle]:
                    if p.startswith("Windows"):
                        self.liste_moteur.addItem(QIcon(icone.get("windows")), p)

        b_creer_projet = QPushButton("créer")
        b_creer_projet.setStatusTip("Création du projet")
        b_creer_projet.clicked.connect(lambda: self.lancer_projet())

        conteneur.addWidget(self.nom_projet)
        conteneur.addWidget(self.nom_jeu)
        conteneur.addWidget(self.liste_moteur)
        conteneur.addWidget(b_creer_projet)

        self.setLayout(conteneur)

    def projet_structure(self):
        # créer la structure de donné
        description = self.dos_p / "description.txt"
        description.touch(exist_ok=True)
        img = Image.new("RGB", (1280, 720), "white")
        img.save(self.dos_p / "image.png")
        d_1 = self.dos_p / "donné"
        d_1.mkdir(exist_ok=True)
        d_2 = ["actifs", "scènes"]
        for i in d_2:
            dos = d_1 / i
            dos.mkdir(exist_ok=True)
        d_3 = ["Modèle3D", "Scripts", "Textures", "Audio", "Police d'écriture", "Licences"]
        for i in d_3:
            dos = d_1 / d_2[0] / i
            dos.mkdir(exist_ok=True)
        d_model = ["Personnages", "Map", "C-Objets", "G-Objets"]
        for i in d_model:
            dos = d_1 / d_2[0] / d_3[0] / i
            dos.mkdir(exist_ok=True)
        d_audio = ["sfx", "musique"]
        for i in d_audio:
            dos = d_1 / d_2[0] / d_3[3] / i
            dos.mkdir(exist_ok=True)
        credit = d_1 / d_2[0] / d_3[-1] / "crédits.txt"
        credit.touch(exist_ok=True)
        return

    @Slot()
    def lancer_projet(self):
        projet = self.nom_projet.text()
        nom = self.nom_jeu.text()
        moteur = self.liste_moteur.currentText()
        n_moteur = moteur.rsplit("-", 1)[0].lower()
        if projet and nom:
            self.dos_p = Path(f"source/{moteur.replace('-', '/')}/{projet}")
            self.dos_p.mkdir(parents=True, exist_ok=True)
            self.projet_structure()
            fichier = self.dos_p / f"{nom}.blend"

            if n_moteur == "linux": command = [self.linux["executable"].get(moteur), str(fichier)]
            elif n_moteur == "windows": command = ["wine", self.windows["executable"].get(moteur), str(fichier)]

            if self.save.checkState() == Qt.Unchecked:
                try: run(command, check=True)
                except: print("active commande de sauvetage dans le menu Option ;)")
            if self.save.checkState() == Qt.Checked:
                try:
                    env = os.environ.copy()
                    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                    run(command, check=True, env=env)
                except: print("Dommage mais ne marche pas XD")
            self.nom_projet.setText("")
            self.nom_jeu.setText("")
            sauvegarder()
