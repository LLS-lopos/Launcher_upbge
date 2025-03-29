import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QCheckBox, QWidgetAction
from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QIcon

# élément graphique
from GUI.creer_projet import Creer
from GUI.liste_projet import Lprojet
from GUI.affichage_projet import Affichage_projet
from GUI.liste_blend import Lblend
# fonction backend
from program.construire_structure import structure
from program.manipuler_donner import sauvegarder, charger

class Lanceur(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        structure()
        sauvegarder()
        img = charger("icon")
        self.setWindowTitle("Lanceur UPBGE")
        self.setWindowIcon(QIcon(img["upbge"]))
        self.setGeometry(0, 0, 1280, 720)
        self.centre()

    def centre(self):
        zone_centre = QWidget()
        self.setCentralWidget(zone_centre)
        self.barre_menu()
        self.barre_status()

        grille = QGridLayout(zone_centre)
        grille.setSpacing(2)
        grille.setContentsMargins(2, 2, 2, 2)

        grille.addWidget(Creer(self.commande_secourre), 0, 0, 1, 3)
        grille.addWidget(Lprojet(), 1, 0, 1, 1)
        grille.addWidget(Affichage_projet(), 1, 1, 1, 1)
        grille.addWidget(Lblend(self.commande_secourre), 1, 2, 1, 1)

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
