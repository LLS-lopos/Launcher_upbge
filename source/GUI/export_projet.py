# exporter le projet
# le moteur
# encoder les données de projets
# créer un lanceur avec décodeur
# choisir l'enplacement de l'export des porjets
from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit
                               , QFileDialog, QPushButton, QComboBox, QGridLayout)
from PySide6.QtCore import (Slot, Qt)
from PySide6.QtGui import (QIcon)
import pathlib
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
        widget_titre = QLabel("Exporter")
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
        self.b_export.clicked.connect(self.exportation_projet)

        # Configurer la liste des moteurs de jeu
        self.liste_moteur = QComboBox()
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
        conteneur.addWidget(widget_titre, 0, 0, 1, 2)
        conteneur.addWidget(T_sortie_jeu, 1, 0, 1, 1)
        conteneur.addWidget(self.sortie_jeu, 1, 1, 1, 1)
        conteneur.addWidget(self.select_sortie_jeu, 1, 2, 1, 1)
        conteneur.addWidget(T_dos_projet, 2, 0, 1, 1)
        conteneur.addWidget(self.projet_jeu, 2, 1, 1, 1)
        conteneur.addWidget(self.select_projet_jeu, 2, 2, 1, 1)

        conteneur.addWidget(self.liste_moteur, 3, 0, 1, 3)
        conteneur.addWidget(self.b_export, 4, 0, 1, 3)
        # Définir la disposition
        self.setLayout(conteneur)
        self.setFixedSize(300, (30*5))

    @Slot()
    def exportation_projet(self):
        dossier_moteur = ""
        projet = pathlib.PosixPath(self.projet_jeu.text())
        destination = pathlib.PosixPath(self.sortie_jeu.text())
        moteur = self.liste_moteur.currentText()
        for i in self.dos_moteur:
            if moteur == i.name:
                dossier_moteur = i
        print(destination)
        print(projet)
        print(moteur)
        self.copi_element(projet, dossier_moteur, destination)

    @Slot()
    def selection_dossier(self, valeur=None):
        # Ouvrir la boîte de dialogue pour sélectionner un dossier
        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if dossier:
            if valeur == 0:
                self.sortie_jeu.setText(dossier)  # Afficher le chemin du dossier sélectionné
            elif valeur == 1:
                self.projet_jeu.setText(dossier)  # Afficher le chemin du dossier sélectionné

    def copi_element(self, projet, moteur, sortie):
        dos_projet = (sortie / projet.name)
        if not (sortie/projet.name).exists(): (sortie/projet.name).mkdir(exist_ok=True)

        run(["cp", "-r", projet, dos_projet], check=True)

        if (dos_projet / "data").exists():
            run(["rm", "-rf", (dos_projet / "data")], check=True)
        run(["mv", (dos_projet / projet.name), (dos_projet / "data")], check=True)

        run(["cp", "-r", moteur, dos_projet], check=True)
        new_dossier = (dos_projet / moteur.name)
        for i in new_dossier.iterdir():
            if i.is_file():
                if i.name != "blenderplayer":
                    run(["rm", i], check=True)
        addons = list(new_dossier.glob('**/scripts'))
        print(addons)
        for i in addons[0].iterdir():
            if i.is_dir():
                if i.name not in ["bge", "freestyle", "modules"]:
                    run(["rm", "-rf", i], check=True)
        if (dos_projet / "engine").exists():
            run(["rm", "-rf", (dos_projet / "engine")], check=True)
        run(["mv", new_dossier, (new_dossier.parent / "engine")], check=True)
