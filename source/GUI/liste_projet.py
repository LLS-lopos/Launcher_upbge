from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot

from pathlib import Path

from source.program.manipuler_donner import charger

class Lprojet(QWidget):
    def __init__(self, table=None):
        super().__init__()
        self.projets = {}  # Dictionnaire pour stocker les projets par onglet
        self.table = table
        self.icone = charger("icon")
        layout = QVBoxLayout()
        self.tableau = QTabWidget(self)
        self.tableau.setMaximumWidth(300)

        self.charger_tableau("linux")
        self.charger_tableau("windows")
        
        # Ajouter le bouton "Recharger la liste"
        self.b_recharger = QPushButton("Recharger la liste")
        self.b_recharger.clicked.connect(lambda: self.recharger_liste())
        self.b_recharger.setMaximumWidth(300)

        layout.addWidget(self.tableau)
        layout.addWidget(self.b_recharger)
        self.setLayout(layout)
        self.setFixedWidth((1280*0.3))

        self.tableau.currentChanged.connect(self.tab_actif)
        self.table = self.tableau.tabText(self.tableau.currentIndex())
        
    def charger_tableau(self, tabeau):
        projets = charger(tabeau)
        for v_projet in projets["projet"]:
            page = QListWidget() # page (élément de tableau)
            self.projets[v_projet] = []  # Initialiser la liste des projets pour cet onglet
            for projet in projets["projet"][v_projet]:
                if projet:
                    self.projets[v_projet].append(projet)  # Ajouter le projet à la liste
                    page.addItem(Path(projet).name)
                self.tableau.addTab(page, QIcon(self.icone.get(tabeau)), str(v_projet)) # ajouter page au tableau

    def tab_actif(self, index):
        self.table = self.tableau.tabText(index)
        print(f"Onglet sélectionné : {self.table}")
        if self.table in self.projets:
            print(f"Projets pour l'onglet '{self.table}': {self.projets[self.table]}")
            for projet in self.projets[self.table]:
                print(projet)
    
    @Slot()
    def recharger_liste(self):
        # Effacer les onglets existants
        self.tableau.clear()
        self.projets.clear()  # Réinitialiser le dictionnaire des projets

        # Recharger les projets
        self.charger_tableau("linux")
        self.charger_tableau("windows")