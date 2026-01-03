# Compilation mode, standalone everywhere, except on macOS there app bundle
# nuitka-project: --mode=app
#
# Debugging options, controlled via environment variable at compile time.
# nuitka-project-if: {OS} == "Windows" and os.getenv("DEBUG_COMPILATION", "no") == "yes":
#     nuitka-project: --windows-console-mode=hide
# nuitka-project-else:
#     nuitka-project-if: {OS} == "Windows":
#         nuitka-project: --windows-console-mode=disable
#     nuitka-project-else:
#         # Ignore console options on non-Windows platforms
#         pass

import sys, os, platform
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QGridLayout, QCheckBox, QWidgetAction, QMessageBox, QSizePolicy
from PySide6.QtCore import Slot, QSize
from PySide6.QtGui import QAction, QIcon, QGuiApplication

# élément graphique

from GUI.liste_projet import Lprojet
from GUI.affichage_projet import Affichage_projet
from GUI.liste_blend import Lblend
from GUI.pybash import PyBash
from GUI.struct_dossier import DosStructure
# autre fonction
from Fonction.creer_projet import Creer
from Fonction.export_projet import Exportation
from Fonction.theme import Theme
# app
from Biblio.librairie_jeux import Jeu
from Biblio.preference import Preference
# fonction backend
from program.construire_structure import structure
from program.manipuler_donner import sauvegarder, charger

class Lanceur(QMainWindow):
    def __init__(self, parent=None, largeur=1280, hauteur=720):
        super().__init__(parent)
        # Créer la structure de projet initiale
        structure()
        pref = charger("preference")
        if pref["fullscreen"]: self.showFullScreen()
        else: self.showNormal()
        if charger("preference")["taille"][0]: self.largeur = charger("preference")["taille"][0]
        else: self.largeur = largeur
        if charger("preference")["taille"][1]: self.hauteur = charger("preference")["taille"][1]
        else: self.hauteur = hauteur

        moniteur = QGuiApplication.primaryScreen()
        taille_moniteur = moniteur.size()
        calcul_l = (taille_moniteur.width()//2) - (self.largeur//2)
        calcul_h = (taille_moniteur.height()//2) - (self.hauteur//2)
        # Sauvegarder la configuration initiale
        sauvegarder()
        # Charger les icônes
        self.setWindowTitle("Lanceur UPBGE")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["upbge"]))
        self.setGeometry(int(calcul_l), int(calcul_h), self.largeur, self.hauteur)
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

        # Configurer l'espacement et les marges de la grille
        grille.setSpacing(2)  # Espacement entre les cellules
        grille.setContentsMargins(2, 2, 2, 2)  # Marges autour de la grille

        # Créer les widgets avec leurs politiques de taille
        projet_widget = Lprojet()
        projet_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        blend_widget = Lblend(self.commande_secourre)
        blend_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        affichage_widget = Affichage_projet()
        affichage_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        structure_widget = DosStructure()
        structure_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Ajout du terminal avec politique de taille
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pybash = PyBash(start_dir=app_dir)
        self.pybash.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Ajouter les widgets de projet à la grille
        grille.addWidget(projet_widget, 0, 0, 1, 1)
        grille.addWidget(blend_widget, 1, 0, 1, 1)

        grille.addWidget(affichage_widget, 0, 1, 1, 2)
        grille.addWidget(structure_widget, 0, 3, 1, 1)

        # Ajout du terminal
        grille.addWidget(self.pybash, 1, 1, 1, 3)

        # Configurer les facteurs d'étirement des colonnes pour équilibrer l'espace
        grille.setColumnStretch(0, 1)  # Colonne 0 : Lprojet et Lblend
        grille.setColumnStretch(1, 3)  # Colonne 1 : Affichage_projet (span 2 colonnes)
        grille.setColumnStretch(2, 0)  # Colonne 2 : partie droite d'Affichage_projet
        grille.setColumnStretch(3, 1)  # Colonne 3 : DosStructure

    def barre_outils(self):
        """
        Créer et configurer la barre d'outils de la fenêtre principale.

        Ajoute un bouton '+' pour créer de nouveaux projets, connecté à la 
        fonction de création de projet.
        """
        # Créer un bouton pour ajouter un nouveau projet
        b_creer_p = QPushButton()
        b_creer_p.setFixedSize(40, 40)
        b_creer_p.setIcon(QIcon(charger("config_launcher")["icon"]["nouveau_projet"]))
        b_creer_p.setIconSize(QSize(35, 35))
        b_creer_p.setStatusTip("créer nouveau projet")
        b_creer_p.clicked.connect(self.fonc_creer_p)

        # Créer un bouton pour exporter un projet
        b_export_p = QPushButton()
        b_export_p.setFixedSize(40, 40)
        b_export_p.setIcon(QIcon(charger("config_launcher")["icon"]["export_projet"]))
        b_export_p.setIconSize(QSize(35, 35))
        b_export_p.setStatusTip("exporter le projet")
        b_export_p.clicked.connect(self.fonc_export_p)

        # Créer un bouton pour lancer les jeu exporter
        b_lib_jeu = QPushButton()
        b_lib_jeu.setFixedSize(40, 40)
        b_lib_jeu.setIcon(QIcon(charger("config_launcher")["icon"]["game"]))
        b_lib_jeu.setIconSize(QSize(35, 35))
        b_lib_jeu.setStatusTip("Bibliothèque de jeux")
        b_lib_jeu.clicked.connect(self.lib_jeu_biblio)
        
        # Ajouter la barre d'outils à la fenêtre principale
        self.tool_barre = self.addToolBar("barre d'outil")
        self.tool_barre.addWidget(b_creer_p)
        self.tool_barre.addWidget(b_export_p)
        self.tool_barre.addWidget(b_lib_jeu)

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

        # Créer l'action de Configuration des préférences
        act_preference = QAction(QIcon(""), "&Préférence", self)
        act_preference.setStatusTip("Configuration des préférence")
        act_preference.setShortcut("Ctrl+P")
        act_preference.triggered.connect(self.fonc_Preference)
        
        # Checbox Commande de secours
        self.commande_secourre = QCheckBox("Commande de secours")
        act_commande_secourre = QWidgetAction(self)
        act_commande_secourre.setDefaultWidget(self.commande_secourre)
        
        # Associer les actions au menu
        Menu_fichier.addAction(act_preference)
        Menu_fichier.addSeparator()
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
        self.creer_projet_dialog = Creer(self.commande_secourre)
        self.creer_projet_dialog.show()

    @Slot()
    def lib_jeu_biblio(self):
        self.game = Jeu()
        self.game.show()
    
    @Slot()
    def fonc_export_p(self):
        """
        Ouvrir la boîte de dialogue d'exportation de projet.

        Crée et affiche le widget Exporter un projet,
        en passant la méthode commande_secourre comme rappel de sauvegarde.
        """
        self.exporter_projet_dialogue = Exportation()
        self.exporter_projet_dialogue.show()
        """if platform.system() == "Linux":
            self.exporter_projet_dialogue = Exportation()
            self.exporter_projet_dialogue.show()
        else:
            # Créer une boîte de message d'avertissement
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Avertissement")
            msg_box.setInformativeText("Cette fonctionnalité est uniquement disponible sur Linux.")
            msg_box.setWindowTitle("Avertissement")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()  # Afficher la boîte de message"""

    @Slot()
    def fonc_Preference(self):
        self.run_preference = Preference()
        self.run_preference.show()

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
