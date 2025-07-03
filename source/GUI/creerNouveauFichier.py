import json
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import (Slot)
from PySide6.QtGui import QIcon
import pathlib
from pathlib import Path
from program.manipuler_donner import config_launcher_json, config, charger


class CreerFichier(QWidget):
    def __init__(self):
        super().__init__()
        # Créer la disposition de la fenêtre
        conteneur = QGridLayout()
        conteneur.setContentsMargins(2, 2, 2, 2)
        conteneur.setSpacing(2)

        #### code ####
        text_info = self.lister_dossier()
        self.l_niveau = []
        texte = QLabel(text_info["N0"][0])
        position = text_info["N0"][-1]
        self.l_niveau.append([texte, position, QLineEdit()])
        for n1 in text_info["N1"]:
            texte = QLabel(n1[0])
            position = n1[-1]
            self.l_niveau.append([texte, position, QLineEdit()])
        for n2 in text_info["N2"]:
            texte = QLabel(n2[0])
            position = n2[-1]
            self.l_niveau.append([texte, position, QLineEdit()])
        for n3 in text_info["N3"]:
            texte = QLabel(n3[0])
            position = n3[-1]
            self.l_niveau.append([texte, position, QLineEdit()])

        for b, i in enumerate(self.l_niveau):
            conteneur.addWidget(i[0], b, 0, 1, 1)
            conteneur.addWidget(i[-1], b, 1, 1, 1)

        bouton_appliquer = QPushButton("Appliquer")
        bouton_appliquer.clicked.connect(lambda: self.appliquer())
        conteneur.addWidget(bouton_appliquer, len(self.l_niveau)+1, 0, 1, 2)
        #### code ####

        self.setLayout(conteneur)
        self.setFixedSize(400, (30*(len(self.l_niveau)+1)))
        self.setWindowTitle("Création de Fichier")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["config_logiciel"]))

    def lister_dossier(self):
        nom = {
            "N0": [],
            "N1": [],
            "N2": [],
            "N3": [],
        }
        base = Path(charger("global")["p_actif"])
        if base is not None:
            print(base)
        else:
            return
        
        for dos in base.iterdir():
            if dos.is_dir():
                nom["N0"] = [dos.name, dos]
                for n_1 in dos.iterdir():
                    if n_1.is_dir():
                        nom["N1"].append([n_1.name, n_1])
                    else: continue
                    for n_2 in n_1.iterdir():
                        if n_2.is_dir():
                            nom["N2"].append([n_2.name, n_2])
                        else: continue
                        for n_3 in n_2.iterdir():
                            if n_3.is_dir():
                                nom["N3"].append([n_3.name, n_3])
                            else: continue
        return nom

    def creer_fichier(self):
        for b, i in enumerate(self.l_niveau):
            if i[1].exists():
                liste_i = (i[-1].text()).split(", ")
                if liste_i != None:
                    for n in liste_i:
                        val = i[1] / n
                        if "/" in str(val):
                            remix = str(val).split("/")
                            remix.pop(-1)
                            n_val = "/".join(remix)
                            Path(n_val).mkdir(parents=True, exist_ok=True)
                        val.touch(exist_ok=True)
        self.l_niveau = []

    @Slot()
    def appliquer(self):
        self.creer_fichier()