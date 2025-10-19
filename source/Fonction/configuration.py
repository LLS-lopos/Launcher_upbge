# paramètre de configuration du programme
#
# élément suivant à ajouter:
##############################################################################################################
#                                     Paramètres d'affichage                                                 #
# Choix de la langue de l'interface.                                                                         #
# Taille de la police ou style de police.                                                                    #
#------------------------------------------------------------------------------------------------------------#
#                                     Paramètres de sauvegarde                                               #
# Fréquence de sauvegarde automatique.                                                                       #
# Format de sauvegarde (par exemple, JSON, XML).                                                             #
#------------------------------------------------------------------------------------------------------------#
#                                  Paramètres de personnalisation                                            #
# Options pour personnaliser l'interface utilisateur (par exemple, disposition des fenêtres, couleurs).      #
#------------------------------------------------------------------------------------------------------------#
#                                   Paramètres de journalisation                                             #
# Niveau de détail des journaux (debug, info, warning, error).                                               #
# Emplacement du fichier de journalisation.                                                                  #
##############################################################################################################

import json
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import (Slot)
from PySide6.QtGui import QIcon
from program.manipuler_donner import config_launcher_json, config, charger
class Configuration(QWidget):
    def __init__(self):
        super().__init__()
        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(2)

        # dossier d'export
        T_sortie_jeu = QLabel("dossier d'export: ")
        self.sortie_jeu = QLineEdit()
        self.select_sortie_jeu = QPushButton("++")
        self.select_sortie_jeu.clicked.connect(lambda: self.selection_dossier(0))
        conteneur.addWidget(T_sortie_jeu, 0, 0, 1, 1)
        conteneur.addWidget(self.sortie_jeu, 0, 1, 1, 1)
        conteneur.addWidget(self.select_sortie_jeu, 0, 2, 1, 1)

        # Bouton de sauvegarde
        self.b_save = QPushButton("appliqué")
        self.b_save.clicked.connect(self.appliquer_config)
        conteneur.addWidget(self.b_save, 1, 0, 1, 3)

        self.setLayout(conteneur)
        self.setFixedSize(400, (30*2))
        self.setWindowTitle("Configuration")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["config_logiciel"]))

    @Slot()
    def selection_dossier(self, valeur=None):
        # Ouvrir la boîte de dialogue pour sélectionner un dossier
        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if dossier:
            if valeur == 0:
                self.sortie_jeu.setText(dossier)  # Afficher le chemin du dossier sélectionné

    @Slot()
    def appliquer_config(self):
        if self.sortie_jeu.text() != "":
            with open((config / config_launcher_json), 'r') as f:
                data = json.load(f)
            data["configuration"]["dossier_export"] = self.sortie_jeu.text()
            with open((config / config_launcher_json), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        self.destroy() # Fermer la fenêtre