# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QCheckBox, QWidgetAction
from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QIcon

# élément graphique
from GUI.liste_projet import Lprojet
from GUI.affichage_projet import Affichage_projet
# fonction backend
from program.contruire_structure import structure

class Lanceur(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        structure()
        self.setWindowTitle("Lanceur UPBGE")
        self.setGeometry(0, 0, 1280, 720)
        self.centre()

    def centre(self):
        zone_centre = QWidget()
        self.setCentralWidget(zone_centre)
        self.barre_menu()
        self.barre_status()

        grille = QGridLayout(zone_centre)
        grille.setSpacing(10)
        grille.setContentsMargins(10, 10, 10, 10)

        grille.addWidget(Lprojet(), 0, 0, 1, 1)
        grille.addWidget(Affichage_projet(), 0, 1, 1, 1)

    def barre_menu(self):
        self.barreMenu = self.menuBar()  # créer la barre de menu
        # sous menu
        Menu_fichier = self.barreMenu.addMenu("&Fichier")
        Menu_option = self.barreMenu.addMenu("&Option")
        # bouton quitter
        act_quitter = QAction(QIcon(""), "&Quitter", self)
        act_quitter.setStatusTip("Fermer le lanceur")
        act_quitter.setShortcut("Ctrl+Q")
        act_quitter.triggered.connect(self.fonc_Quitter)
        # Checbox Commande de secours
        self.commande_secourre = QCheckBox("Commande de secours")
        act_commande_secourre = QWidgetAction(self)
        act_commande_secourre.setDefaultWidget(self.commande_secourre)
        # associer les actions au menu
        Menu_fichier.addAction(act_quitter)
        Menu_option.addAction(act_commande_secourre)
        # lier
        self.setMenuBar(self.barreMenu)  # instancier la barre de menu

    def barre_status(self):
        self.StatuBarre = self.statusBar()
        self.StatuBarre.showMessage("Statu Bar")

    @Slot()
    def fonc_Quitter(self):  # Ferme Le Logiciel
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = QApplication([])
    window = Lanceur()
    window.show()
    sys.exit(app.exec())
