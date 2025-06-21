# devra être un QWidget dans lequel ce trouvera tous les paramètre de configuration du programme
# chemin de dossier d'exportation
# chemin de dossier de projet
# autre
import json
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import (Slot)
from program.manipuler_donner import config_launcher_json, config
class Configuration(QWidget):
    def __init__(self):
        super().__init__()
        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(2)

        conteneur.addWidget(QLabel("Configuration"), 0, 0, 1, 1)

        # dossier d'export
        T_sortie_jeu = QLabel("dossier d'export: ")
        self.sortie_jeu = QLineEdit()
        self.select_sortie_jeu = QPushButton("++")
        self.select_sortie_jeu.clicked.connect(lambda: self.selection_dossier(0))
        conteneur.addWidget(T_sortie_jeu, 1, 0, 1, 1)
        conteneur.addWidget(self.sortie_jeu, 1, 1, 1, 1)
        conteneur.addWidget(self.select_sortie_jeu, 1, 2, 1, 1)

        # Bouton de sauvegarde
        self.b_save = QPushButton("appliqué")
        self.b_save.clicked.connect(self.appliquer_config)
        conteneur.addWidget(self.b_save, 2, 2, 1, 1)

        self.setLayout(conteneur)
        self.setFixedSize(400, (30*3))

    @Slot()
    def selection_dossier(self, valeur=None):
        # Ouvrir la boîte de dialogue pour sélectionner un dossier
        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if dossier:
            if valeur == 0:
                self.sortie_jeu.setText(dossier)  # Afficher le chemin du dossier sélectionné

    @Slot()
    def appliquer_config(self):
        with open((config / config_launcher_json), 'r') as f:
            data = json.load(f)
        data["configuration"]["dossier_export"] = self.sortie_jeu.text()
        with open((config / config_launcher_json), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)