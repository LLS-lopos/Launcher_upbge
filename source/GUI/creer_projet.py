import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from pathlib import Path
from subprocess import run

from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QGridLayout)
from PySide6.QtCore import (Slot, Qt)
from PySide6.QtGui import (QIcon)
from PIL import Image

from program.manipuler_donner import charger, sauvegarder

class Creer(QWidget):
    """
    Widget pour créer de nouveaux projets de jeux dans le Lanceur UPBGE.

    Cette classe fournit une interface utilisateur pour créer de nouveaux projets de jeux,
    permettant aux utilisateurs de spécifier les noms de projet et de jeu, 
    et de sélectionner un moteur de jeu.

    Attributs:
        nom_projet (QLineEdit): Champ de saisie pour le nom du projet
        nom_jeu (QLineEdit): Champ de saisie pour le nom du jeu
        liste_moteur (QComboBox): Liste déroulante pour sélectionner le moteur de jeu
        save (callable): Fonction de rappel pour sauvegarder les informations du projet
    """

    def __init__(self, save):
        """
        Initialiser le widget de création de projet.

        Args:
            save (callable): Une fonction de rappel pour sauvegarder les informations du projet
        """
        super().__init__()
        # Charger les icônes
        icone = charger("icon")
        self.save = save

        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(2)

        # Titre
        widget_titre = QLabel("Création de Projet")

        # Créer les champs de saisie
        self.nom_projet = QLineEdit()
        self.nom_jeu = QLineEdit()

        # Configurer la liste des moteurs de jeu
        self.liste_moteur = QComboBox()
        # Charger les moteurs Linux
        self.linux = charger("linux")
        for cle in self.linux:
            if cle == "executable":
                for p in self.linux[cle]:
                    if Path(self.linux[cle][p]).exists():
                        if p.startswith("Linux"):
                            self.liste_moteur.addItem(QIcon(icone.get("linux")), p)
        
        # Charger les moteurs Windows
        self.windows = charger("windows")
        for cle in self.windows:
            if cle == "executable":
                for p in self.windows[cle]:
                    if Path(self.windows[cle][p]).exists():
                        if p.startswith("Windows"):
                            self.liste_moteur.addItem(QIcon(icone.get("windows")), p)

        # Créer le bouton de création de projet
        b_creer_projet = QPushButton("créer")
        b_creer_projet.clicked.connect(lambda: self.lancer_projet())

        # Créer les labels
        texte_projet = QLabel("nom du projet")
        texte_jeu = QLabel("nom du jeu")
        texte_moteur = QLabel("moteur disponible")

        # Disposition des widgets dans la grille
        conteneur.addWidget(widget_titre, 0, 0, 1, 3)
        conteneur.addWidget(texte_projet, 1, 0, 2, 1)
        conteneur.addWidget(self.nom_projet, 1, 1, 2, 2)
        conteneur.addWidget(texte_jeu, 3, 0, 2, 1)
        conteneur.addWidget(self.nom_jeu, 3, 1, 2, 2)
        conteneur.addWidget(texte_moteur, 5, 0, 2, 1)
        conteneur.addWidget(self.liste_moteur, 5, 1, 2, 2)
        conteneur.addWidget(b_creer_projet, 7, 0, 1, 3)

        # Définir la disposition
        self.setLayout(conteneur)

    def projet_structure(self):
        """
        Créer la structure du projet.

        Cette méthode crée les répertoires et fichiers nécessaires pour un nouveau projet.
        """
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
        """
        Créer un nouveau projet basé sur la saisie de l'utilisateur.

        Valide la saisie, sauvegarde les informations du projet et ferme la boîte de dialogue.
        Appelle la méthode de sauvegarde de rappel pour conserver les détails du projet.
        """
        # Récupérer les valeurs saisies
        projet = self.nom_projet.text()
        jeu = self.nom_jeu.text()
        moteur = self.liste_moteur.currentText()
        n_moteur = moteur.rsplit("-", 1)[0].lower()
        if projet and jeu:
            self.dos_p = Path(f"data/{moteur.replace('-', '/')}/{projet}")
            self.dos_p.mkdir(parents=True, exist_ok=True)
            self.projet_structure()
            if "Range" in moteur:
                fichier = self.dos_p / f"{jeu}.range"
            else:
                fichier = self.dos_p / f"{jeu}.blend"

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
        sauvegarder() # Sauvegarder la configuration
        self.destroy() # Fermer la fenêtre
