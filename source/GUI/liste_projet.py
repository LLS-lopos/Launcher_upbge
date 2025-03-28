import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot
from pathlib import Path
import json

from program.manipuler_donner import charger, config, global_json

class Lprojet(QWidget):
    def __init__(self):
        super().__init__()
        self.projets = {}  # Dictionnaire pour stocker les projets par onglet
        self.icone = charger("icon")
        layout = QVBoxLayout()
        self.tableau = QTabWidget(self)
        self.tableau.setMaximumWidth(300)

        # Charger les projets dès l'initialisation
        self.charger_tableau("linux")
        self.charger_tableau("windows")
        
        # Ajouter le bouton "Recharger la liste"
        self.b_recharger = QPushButton("Recharger la liste")
        self.b_recharger.clicked.connect(self.recharger_liste)
        self.b_recharger.setMaximumWidth(300)

        layout.addWidget(self.tableau)
        layout.addWidget(self.b_recharger)
        self.setLayout(layout)
        self.setFixedWidth((1280 * 0.3))

    def charger_tableau(self, tabeau):
        projet = None
        try: projets = charger(tabeau)  # Charger les projets pour l'onglet spécifié # ... (le reste de votre code)
        except Exception as e: print(f"Erreur lors du chargement des projets : {e}")
        for v_projet in projets["projet"]:
            page = QListWidget()  # Créer un nouveau QListWidget pour l'onglet
            self.projets[v_projet] = []  # Initialiser la liste des projets pour cet onglet
            for projet in projets["projet"][v_projet]:
                if projet:
                    self.projets[v_projet].append(projet)  # Ajouter le projet à la liste
                    item = page.addItem(Path(projet).name)  # Ajouter le nom du projet au QListWidget
                    chemin_projet = Path(projet).parent
                    page.itemClicked.connect(lambda item=item, chemin=chemin_projet: self.projet_selectionner(item, chemin))  # Connecter le signal de clic sur l'élément
            self.tableau.addTab(page, QIcon(self.icone.get(tabeau)), str(v_projet))  # Ajouter la page au widget d'onglets

    @Slot()
    def projet_selectionner(self, item, chemin):
        projet_nom = item.text()
        dos = Path(chemin) / projet_nom
        info = {"p_actif": str(dos)}
        # print(f"Élément cliqué : {projet_nom}\n {type(projet_nom)}\n{dos}\n {type(dos)}")
        with open((config / global_json), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)

    @Slot()
    def recharger_liste(self):
        # Effacer les onglets existants
        self.tableau.clear()
        self.projets.clear()  # Réinitialiser le dictionnaire des projets

        # Recharger les projets
        self.charger_tableau("linux")
        self.charger_tableau("windows")