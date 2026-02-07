import os
import sys
import platform

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton, QMessageBox, QHBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot
from pathlib import Path
import json

from Fonction.manipuler_donner import charger, config, global_json, sauvegarder

class Lprojet(QWidget):
    def __init__(self):
        super().__init__()
        self.projets = {}  # Dictionnaire pour stocker les projets par onglet
        layout = QVBoxLayout()
        self.tableau = QTabWidget(self)

        # Charger les projets dès l'initialisation
        if platform.system() == "Linux": self.charger_tableau(charger("config_launcher")["linux"], "linux")
        self.charger_tableau(charger("config_launcher")["windows"], "windows")
        
        # Ajouter le bouton "Recharger la liste"
        self.b_recharger = QPushButton("Recharger la liste")
        self.b_recharger.clicked.connect(self.recharger_liste)
        # Ajouter le bouton "supprimer projet"
        self.b_del_projet = QPushButton("Supprimer Projet")
        self.b_del_projet.clicked.connect(self.supprimer_projet)

        # ligne
        ligne1 = QHBoxLayout()
        ligne1.addWidget(self.b_recharger)
        ligne1.addWidget(self.b_del_projet)
        # colone
        layout.addWidget(self.tableau)
        layout.addLayout(ligne1)
        self.setLayout(layout)

    def charger_tableau(self, tabeau, district):
        try:
            projets = tabeau  # Charger les projets pour l'onglet spécifié
        except Exception as e:
            print(f"Erreur lors du chargement des projets : {e}")
            return

        # Créer un QListWidget pour chaque version
        for version in projets["projet"]:
            page = QListWidget()
            self.projets[version] = []  # Initialiser la liste des projets pour cette version
            
            # Ajouter les projets existants de cette version
            for projet in projets["projet"][version]:
                if os.path.exists(projet):
                    if projet:
                        self.projets[version].append(projet)  # Ajouter le projet à la liste
                        item = page.addItem(Path(projet).name)  # Ajouter le nom du projet au QListWidget
                        chemin_projet = Path(projet).parent
                        page.itemClicked.connect(lambda item=item, chemin=chemin_projet: self.projet_selectionner(item, chemin))
                    # Ajouter l'onglet avec le nom de la version
                    self.tableau.addTab(page, QIcon(charger("config_launcher")["icon"][district]), f"{version} {district}")

    @Slot()
    def projet_selectionner(self, item, chemin):
        projet_nom = item.text()
        dos = Path(chemin) / projet_nom
        info = {"p_actif": str(dos)}
        with open((config / global_json), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)

    @Slot()
    def recharger_liste(self):
        self.tableau.clear()  # Effacer les onglets existants
        self.projets.clear()  # Réinitialiser le dictionnaire des projets
        sauvegarder()
        # Recharger les projets
        if platform.system() == "Linux": self.charger_tableau(charger("config_launcher")["linux"], "linux")
        self.charger_tableau(charger("config_launcher")["windows"], "windows")

    @Slot()
    def supprimer_projet(self):
        selection = charger("global")
        if selection["p_actif"]:
            # Demander confirmation à l'utilisateur
            reponse = QMessageBox.question(
                self,
                "Confirmation de suppression",
                f"Êtes-vous sûr de vouloir supprimer définitivement le projet\n{selection['p_actif']} ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reponse == QMessageBox.Yes:
                try:
                    import shutil
                    shutil.rmtree(selection["p_actif"])
                    sauvegarder()
                    QMessageBox.information(self, "Succès", "Le projet a été supprimé avec succès.")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le projet {selection["p_actif"]}: {str(e)}")
                    return
            else:
                return
        
        index_courant = self.tableau.currentIndex()  # Sauvegarder l'index de l'onglet actif avant le rechargement
        self.recharger_liste()  # Recharger tous les projets
        # Rétablir l'index de l'onglet actif
        if index_courant != -1:
            self.tableau.setCurrentIndex(index_courant)
