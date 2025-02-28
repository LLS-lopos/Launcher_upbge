import os
import platform
import subprocess
import sys

from PySide6.QtCore import (Slot, Qt)
from PySide6.QtGui import (QIcon, QAction, QFont)
from PySide6.QtWidgets import (QApplication, QMainWindow, QListWidgetItem, QListWidget, QTabWidget, QLabel, QWidget, QLineEdit,
                               QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, QCheckBox, QWidgetAction, QRadioButton)

from r_fonction import *


class Lanceur(QMainWindow):
    def __init__(self):
        super().__init__()
        structure()
        ic(linux, windows)
        self.setWindowTitle("Lanceur UPBGE")
        self.setGeometry(0, 0, 1200, 700)
        self.setWindowIcon(QIcon(str(icon.get("upbge"))))
        self.se = platform.system()

        self.base()
        self.connecter_signaux()

    def base(self):
        zone_central = QWidget()
        self.setCentralWidget(zone_central)
        self.barre_menu()
        self.barre_status()

        grille = QGridLayout(zone_central)

        grille.addWidget(self.logiciel(), 0, 0, 1, 3)
        grille.addWidget(self.liste_projet(), 1, 0, 10, 1)
        grille.addWidget(self.affichage(), 1, 1, 10, 2)

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

    def logiciel(self):
        widget = QWidget()
        widget.setFixedHeight(30)
        ligne = QHBoxLayout()
        choix_multiple = QRadioButton()
        saisie_nom_code = QLineEdit()
        saisie_nom_projet = QLineEdit()
        bouton_creer_projet = QPushButton()

        executables = linux.get("executable", {})
        for cle, executable in executables.items():
            if Path(executable).name == "blender" and Path(executable).exists() is True:
                nom = "upbge" + (Path(executable).parent.name).replace("Linux", "")
                bouton = QPushButton(QIcon(str(icon.get("linux"))), nom)
                bouton.setStatusTip(f"Logiciel {nom}")
                bouton.setFixedHeight(20)
                ligne.addWidget(bouton)
                choix_multiple.setLayout(ligne)
                bouton.clicked.connect(lambda checked, msg=[str(executable)]: self.lancer_editeur(msg))
            if Path(executable).name == "RangeEngine" and Path(executable).exists() is True:
                nom = "range" + (Path(executable).parent.name).replace("Linux", "")
                bouton = QPushButton(QIcon(str(icon.get("linux"))), nom)
                bouton.setStatusTip(f"Logiciel {nom}")
                bouton.setFixedHeight(20)
                ligne.addWidget(bouton)
                choix_multiple.setLayout(ligne)
                bouton.clicked.connect(lambda checked, msg=[str(executable)]: self.lancer_editeur(msg))

        executables = windows.get("executable", {})
        for cle, executable in executables.items():
            if Path(executable).name == "blender.exe" and Path(executable).exists() is True:
                nom = "upbge" + (Path(executable).parent.name).replace("Windows", "")
                bouton = QPushButton(QIcon(str(icon.get("windows"))), nom)
                bouton.setStatusTip(f"Logiciel {nom}")
                bouton.setFixedHeight(20)
                ligne.addWidget(bouton)
                choix_multiple.setLayout(ligne)
                bouton.clicked.connect(lambda checked, msg=["wine", str(executable)]: self.lancer_editeur(msg))
            if Path(executable).name == "RangeEngine.exe" and Path(executable).exists() is True:
                nom = "range" + (Path(executable).parent.name).replace("Windows", "")
                bouton = QPushButton(QIcon(str(icon.get("windows"))), nom)
                bouton.setStatusTip(f"Logiciel {nom}")
                bouton.setFixedHeight(20)
                ligne.addWidget(bouton)
                choix_multiple.setLayout(ligne)
                bouton.clicked.connect(lambda checked, msg=["wine", str(executable)]: self.lancer_editeur(msg))

        widget.setLayout(ligne)
        return widget

    def liste_projet(self):
        widget = QWidget()
        col_projet = QVBoxLayout()
        self.tableau = QTabWidget()

        self.page_l2 = QListWidget()
        self.page_l2.setFont(QFont("Arial", 14))
        for projet_l2 in linux["projet"]["2x"]:
            if projet_l2:
                self.page_l2.addItem(Path(projet_l2).name)
                self.tableau.addTab(self.page_l2, QIcon(str(icon.get("linux"))), "L2")
        self.page_l3 = QListWidget()
        self.page_l3.setFont(QFont("Arial", 14))
        for projet_l3 in linux["projet"]["3x"]:
            if projet_l3:
                self.page_l3.addItem(Path(projet_l3).name)
                self.tableau.addTab(self.page_l3, QIcon(str(icon.get("linux"))), "L3")
                self.page_l3.itemClicked.connect(lambda :self.affichage())
        self.page_l4 = QListWidget()
        self.page_l4.setFont(QFont("Arial", 14))
        for projet_l4 in linux["projet"]["4x"]:
            if projet_l4:
                self.page_l4.addItem(Path(projet_l4).name)
                self.tableau.addTab(self.page_l4, QIcon(str(icon.get("linux"))), "L4")
        self.page_lR = QListWidget()
        self.page_lR.setFont(QFont("Arial", 14))
        for projet_lR in linux["projet"]["Range"]:
            if projet_lR:
                self.page_lR.addItem(Path(projet_lR).name)
                self.tableau.addTab(self.page_lR, QIcon(str(icon.get("range"))), "LR")
        self.page_w2 = QListWidget()
        self.page_w2.setFont(QFont("Arial", 14))
        for projet_w2 in windows["projet"]["2x"]:
            if projet_w2:
                self.page_w2.addItem(Path(projet_w2).name)
                self.tableau.addTab(self.page_w2, QIcon(str(icon.get("windows"))), "W2")
        self.page_w3 = QListWidget()
        self.page_w3.setFont(QFont("Arial", 14))
        for projet_w3 in windows["projet"]["3x"]:
            if projet_w3:
                self.page_w3.addItem(Path(projet_w3).name)
                self.tableau.addTab(self.page_w3, QIcon(str(icon.get("windows"))), "W3")
        self.page_w4 = QListWidget()
        self.page_w4.setFont(QFont("Arial", 14))
        for projet_w4 in windows["projet"]["4x"]:
            if projet_w4:
                self.page_w4.addItem(Path(projet_w4).name)
                self.tableau.addTab(self.page_w4, QIcon(str(icon.get("windows"))), "W4")
        self.page_wR = QListWidget()
        self.page_wR.setFont(QFont("Arial", 14))
        for projet_wR in windows["projet"]["Range"]:
            if projet_wR:
                self.page_wR.addItem(Path(projet_wR).name)
                self.tableau.addTab(self.page_wR, QIcon(str(icon.get("range"))), "WR")

        col_projet.addWidget(self.tableau)
        widget.setLayout(col_projet)

        return widget

    def connecter_signaux(self):
        self.tableau.currentChanged.connect(self.affichage)

    def affichage(self):
        widget = QWidget()
        widget.setFixedWidth(900)
        col_affiche = QVBoxLayout()

        img_cadre = QLabel()
        img = QIcon(str(icon.get("upbge")))
        img_cadre.setPixmap(img.pixmap(20, 20))

        element = QLabel("UPBGE")
        # Récupérer le QTabWidget (assurez-vous d'avoir une référence à celui-ci)
        table = self.tableau
        id_page = table.currentIndex()
        nom_page = table.tabText(id_page)

        # Récupérer les projets sélectionnés
        self.page = None
        if nom_page == "L2":
            self.page = self.page_l2.selectedItems()
        elif nom_page == "L3":
            self.page = self.page_l3.selectedItems()
        elif nom_page == "L4":
            self.page = self.page_l4.selectedItems()
        elif nom_page == "LR":
            self.page = self.page_lR.selectedItems()
        elif nom_page == "W2":
            self.page = self.page_w2.selectedItems()
        elif nom_page == "W3":
            self.page = self.page_w3.selectedItems()
        elif nom_page == "W4":
            self.page = self.page_w4.selectedItems()
        elif nom_page == "WR":
            self.page = self.page_wR.selectedItems()

        # Afficher les projets sélectionnés
        if self.page:  # Vérifiez si des éléments sont sélectionnés
            projet_afficher = set()
            for projet in self.page:
                print(projet)
                projet_text = projet.text()
                if projet_text not in projet_afficher:
                    projet_afficher.add(projet_text)
            print(ic(projet_afficher))

        col_affiche.addWidget(img_cadre)
        col_affiche.addWidget(element)
        widget.setLayout(col_affiche)

        return widget

    @Slot()
    def fonc_Quitter(self):
        self.destroy()
        sys.exit()

    @Slot()
    def lancer_editeur(self, programme):
        if self.commande_secourre.checkState() == Qt.Unchecked:
            try:
                subprocess.run(programme, check=True)
            except:
                print("active commande de sauvetage dans le menu Option ;)")
        if self.commande_secourre.checkState() == Qt.Checked:
            try:
                env = os.environ.copy()
                env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                subprocess.run(programme, check=True, env=env)
            except:
                print("Dommage mais ne marche pas XD")

if __name__ == "__main__":
    aplis = QApplication(sys.argv)
    logiciel = Lanceur()
    logiciel.show()
    sys.exit(aplis.exec())
