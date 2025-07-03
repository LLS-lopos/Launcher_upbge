import json
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import (Slot)
from PySide6.QtGui import QIcon
from program.manipuler_donner import config_launcher_json, config, charger

class CreerFichier(QWidget):
    def __init__(self):
        super().__init__()
        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(2)

        #### code ####
        bouton_appliquer = QPushButton("Appliquer")
        bouton_appliquer.clicked.connect(lambda: self.appliquer())
        conteneur.addWidget(bouton_appliquer, 0, 0, 1, 1)
        #### code ####

        self.setLayout(conteneur)
        self.setFixedSize(400, (30*2))
        self.setWindowTitle("Création de Fichier")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["config_logiciel"]))

    def lister_dossier(self):
        base = charger("global")["p_actif"]
        if base != None:
            print(str(base))
        else:
            print("aucun projet sélectionner")

    def creer_fichier(self):
        print("vide")

    @Slot()
    def appliquer(self):
        self.lister_dossier()
        self.creer_fichier()