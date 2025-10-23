import json
from PySide6.QtCore import Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSizePolicy
from program.manipuler_donner import charger, config, config_launcher_json

class Preference(QWidget):
    def __init__(self):
        super().__init__()
        # Créer la disposition de la fenêtre
        self.conteneur = QGridLayout()
        self.conteneur.setContentsMargins(2, 2, 2, 2)
        self.conteneur.setSpacing(4)

        ##########Appel de fonction###########
        type_param = self.liste_page()
        self.zone_config = self.affiche_page()
        self.b_save = QPushButton("appliqué")
        self.b_save.clicked.connect(self.appliquer_config)
        self.page_courante = None  # Variable pour tracker la page actuelle

        type_param.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.zone_config.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.b_save.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.conteneur.addWidget(type_param, 0, 0, 1, 1)
        self.conteneur.addWidget(self.b_save, 1, 0, 1, 1)
        self.conteneur.addWidget(self.zone_config, 0, 1, 2, 3)

        self.conteneur.setColumnStretch(0, 1)
        self.conteneur.setColumnStretch(1, 3)
        self.conteneur.setRowStretch(0, 18)
        self.conteneur.setRowStretch(1, 1)
        ##########Appel de fonction###########

        self.setLayout(self.conteneur)
        self.setFixedSize(800, 600)
        self.setWindowTitle("Préférence")
        self.setWindowIcon(QIcon(charger("config_launcher")["icon"]["config_logiciel"]))

    def liste_page(self):
        self.list_obj = QListWidget()
        Liste_option = [
            "Général",
            "Aff-Fichier",
            "Aff-Tree-Projet",
            "Aff-Projet",
            "Terminal",
            "Thème"
        ]
        for i in Liste_option:
            nom = self.list_obj.addItem(i)
        self.list_obj.itemClicked.connect(self.impri)

        self.list_obj.setSpacing(5)
        return self.list_obj

    def affiche_page(self, page=None):
        widget = QWidget(self)
        self.affiche = QVBoxLayout()
        self.nettoyer_affichage()
        if page == "gen":
            self.affiche.addWidget(self.general())

        widget.setLayout(self.affiche)
        return widget
    
    def nettoyer_affichage(self):
        # Effacer le contenu actuel
        while self.affiche.count():  # Tant qu'il y a des items dans le layout
            item = self.affiche.takeAt(0)  # Prendre le premier item
            widget = item.widget()  # Récupérer le widget associé
            if widget is not None:
                widget.setParent(None)  # Supprimer le widget du layout
                widget.deleteLater()  # Marquer le widget pour suppression
            else:
                layout = item.layout()  # Si c'est un layout, le supprimer récursivement
                if layout is not None:
                    self.clear_layout(layout)

    def general(self):
        print("general activé")
        widget = QWidget(self)
        col = QVBoxLayout()
        
        ########## code ###########
        L_dossier_export = QLabel("dossier d'export: ")
        self.LE_dossier_export = QLineEdit()
        B_dossier_export = QPushButton("++")
        B_dossier_export.clicked.connect(lambda: self.selection_dossier_fichier(self.LE_dossier_export, 0))
        # Label LineEditte BoutonSelectDossier
        ligne1 = QHBoxLayout()
        ligne1.addWidget(L_dossier_export)
        ligne1.addWidget(self.LE_dossier_export)
        ligne1.addWidget(B_dossier_export)
        ########## code ###########
        col.addLayout(ligne1)

        widget.setLayout(col)
        return widget
    
    @Slot()
    def selection_dossier_fichier(self, bouton, valeur=None):
        # Ouvrir la boîte de dialogue pour sélectionner un dossier
        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if dossier:
            if valeur == 0:
                bouton.setText(dossier)  # Afficher le chemin du dossier sélectionné
            elif valeur == 1:
                return
    
    @Slot()
    def appliquer_config(self, page=None):
        if self.sortie_jeu.text() != "":
            with open((config / config_launcher_json), 'r') as f:
                data = json.load(f)
            data["configuration"]["dossier_export"] = self.sortie_jeu.text()
            with open((config / config_launcher_json), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def impri(self, obj):
        print(f"test GG {obj.text()}")
        new_page = obj.text()
        if new_page != self.page_courante:
            self.page_courante = new_page
            if new_page == "Général":
                # Remplacer le widget de configuration
                self.conteneur.removeWidget(self.zone_config)
                self.zone_config.deleteLater()
                self.zone_config = self.affiche_page("gen")
                self.conteneur.addWidget(self.zone_config, 0, 1, 1, 3)
            else:
                # Placeholder pour autres pages
                self.conteneur.removeWidget(self.zone_config)
                self.zone_config.deleteLater()
                self.zone_config = self.affiche_page()  # Page vide par défaut
                self.conteneur.addWidget(self.zone_config, 0, 1, 1, 3)