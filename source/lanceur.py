import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QGridLayout, QCheckBox, QWidgetAction
from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QIcon

# élément graphique
from GUI.creer_projet import Creer
from GUI.liste_projet import Lprojet
from GUI.affichage_projet import Affichage_projet
from GUI.liste_blend import Lblend
from GUI.theme import Theme
# fonction backend
from program.construire_structure import structure
from program.manipuler_donner import sauvegarder, charger

class Lanceur(QMainWindow):
    """
    Fenêtre principale de l'application Lanceur UPBGE.

    Cette classe gère l'interface principale du lanceur, incluant 
    les barres de menu, les barres d'outils et la disposition du widget central.

    Attributs:
        tool_barre (QToolBar): Barre d'outils pour les actions de l'application
        barreMenu (QMenuBar): Barre de menu principale de l'application
    """

    def __init__(self, parent=None):
        """
        Initialiser la fenêtre principale du Lanceur.

        Configure les propriétés de base de la fenêtre, crée la structure du projet,
        sauvegarde la configuration initiale et définit l'icône de la fenêtre.

        Args:
            parent (QWidget, optional): Widget parent. Par défaut à None.
        """
        super().__init__(parent)
        # Créer la structure de projet initiale
        structure()
        # Sauvegarder la configuration initiale
        sauvegarder()
        # Charger les icônes
        img = charger("icon")
        self.setWindowTitle("Lanceur UPBGE")
        self.setWindowIcon(QIcon(img["upbge"]))
        self.setGeometry(0, 0, 1280, 720)
        self.centre()

    def centre(self):
        """
        Configurer le widget central et la disposition de la fenêtre principale.

        Configure le widget central, la barre de menu, la barre de statut et la barre d'outils.
        Organise les widgets liés aux projets dans une disposition en grille.
        """
        # Créer un widget central
        zone_centre = QWidget()
        self.setCentralWidget(zone_centre)
        
        # Configurer les différents éléments de l'interface
        self.barre_menu()
        self.barre_status()
        self.barre_outils()

        # Créer une disposition en grille pour les widgets
        grille = QGridLayout(zone_centre)

        # Ajouter les widgets de projet à la grille
        grille.addWidget(Lprojet(), 1, 0, 1, 1)
        grille.addWidget(Affichage_projet(), 1, 1, 1, 1)
        grille.addWidget(Lblend(self.commande_secourre), 1, 2, 1, 1)

    def barre_outils(self):
        """
        Créer et configurer la barre d'outils de la fenêtre principale.

        Ajoute un bouton '+' pour créer de nouveaux projets, connecté à la 
        fonction de création de projet.
        """
        # Créer un bouton pour ajouter un nouveau projet
        b_creer_p = QPushButton("+")
        b_creer_p.setStatusTip("créer nouveau projet")
        b_creer_p.clicked.connect(self.fonc_creer_p)
        
        # Ajouter la barre d'outils à la fenêtre principale
        self.tool_barre = self.addToolBar("barre d'outil")
        self.tool_barre.addWidget(b_creer_p)

    def barre_menu(self):
        """
        Configurer la barre de menu principale avec les menus Fichier, Option et Thème.

        Crée des éléments de menu et configure la navigation de base de l'application.
        """
        # Créer la barre de menu
        self.barreMenu = self.menuBar()
        
        # Ajouter les sous-menus principaux
        Menu_fichier = self.barreMenu.addMenu("&Fichier")
        Menu_option = self.barreMenu.addMenu("&Option")
        
        # Ajouter le menu de thème réutilisable
        menu_theme = Theme()
        self.barreMenu.addMenu(menu_theme)
        
        # Créer l'action de quitter
        act_quitter = QAction(QIcon(""), "&Quitter", self)
        act_quitter.setStatusTip("Fermer le lanceur")
        act_quitter.setShortcut("Ctrl+Q")
        act_quitter.triggered.connect(self.fonc_Quitter)
        
        # Checbox Commande de secours
        self.commande_secourre = QCheckBox("Commande de secours")
        act_commande_secourre = QWidgetAction(self)
        act_commande_secourre.setDefaultWidget(self.commande_secourre)
        
        # Associer les actions au menu
        Menu_fichier.addAction(act_quitter)
        Menu_option.addAction(act_commande_secourre)
        
        # Lier
        self.setMenuBar(self.barreMenu)  # instancier la barre de menu

    def barre_status(self):
        """
        Configurer la barre de statut de la fenêtre principale.

        Actuellement une méthode de réserve pour une personnalisation potentielle 
        de la barre de statut.
        """
        # Méthode pour configurer la barre de status si nécessaire
        self.StatuBarre = self.statusBar()
        self.StatuBarre.showMessage("Statu Bar")

    @Slot()
    def fonc_creer_p(self):
        """
        Ouvrir la boîte de dialogue de création de projet.

        Crée et affiche le widget Creer pour créer un nouveau projet,
        en passant la méthode commande_secourre comme rappel de sauvegarde.
        """
        creer_projet_dialog = Creer(self.commande_secourre)
        creer_projet_dialog.show()

    @Slot()
    def fonc_Quitter(self):  
        """
        Fermer l'application.

        Détruit la fenêtre principale et quitte l'application.
        """
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = QApplication([])
    window = Lanceur()
    window.show()
    sys.exit(app.exec())
