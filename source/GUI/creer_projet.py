import os

from pathlib import Path
from subprocess import run

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, QComboBox)
from PySide6.QtCore import (Slot, Qt)

from source.program.manipuler_donner import charger

class Creer(QWidget):
    def __init__(self, save):
        super().__init__()
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
                        self.liste_moteur.addItem(p)
        self.windows = charger("windows")
        for cle in self.windows:
            if cle == "executable":
                for p in self.windows[cle]:
                    if p.startswith("Windows"):
                        self.liste_moteur.addItem(p)

        b_creer_projet = QPushButton("créer")
        b_creer_projet.setStatusTip("Création du projet")
        b_creer_projet.clicked.connect(lambda: self.lancer_projet())

        conteneur.addWidget(self.nom_projet)
        conteneur.addWidget(self.nom_jeu)
        conteneur.addWidget(self.liste_moteur)
        conteneur.addWidget(b_creer_projet)

        self.setLayout(conteneur)

    @Slot()
    def lancer_projet(self):
        projet = self.nom_projet.text()
        nom = self.nom_jeu.text()
        moteur = self.liste_moteur.currentText()
        n_moteur = moteur.rsplit("-")[0].lower()
        print(f"moteur: {n_moteur}")
        print(projet, nom, moteur)
        if projet and nom:
            dos_p = Path(f"source/{moteur.replace('-', '/')}/{projet}")
            dos_p.mkdir(parents=True, exist_ok=True)
            fichier = dos_p / f"{nom}.blend"

            if n_moteur == "linux": command = [self.linux["executable"].get(moteur), str(fichier)]
            elif n_moteur == "windows": command = ["wine", self.windows["executable"].get(moteur), str(fichier)]

            if self.save.checkState() == Qt.Unchecked:
                try:
                    run(command, check=True)
                except:
                    print("active commande de sauvetage dans le menu Option ;)")
            if self.save.checkState() == Qt.Checked:
                try:
                    env = os.environ.copy()
                    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                    run(command, check=True, env=env)
                except:
                    print("Dommage mais ne marche pas XD")
            self.nom_projet.setText("")
            self.nom_jeu.setText("")
