# sera une fenêtre de bibliothèque de jeu créer avec le Lanceur

import json
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import (Slot)
from PySide6.QtGui import QIcon
from program.manipuler_donner import config_launcher_json, config, charger

class Jeu(QWidget):
    def __init__(self):
        super().__init__()
        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(2)

        ### code ###
        texte1 = QLabel("Toto")
        conteneur.addWidget(texte1, 0, 0, 1, 1)
        ### code ###

        self.setLayout(conteneur)
        self.setFixedSize(400, (30*2))
        self.setWindowTitle("Biblihothèque de Jeu")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["config_logiciel"]))
