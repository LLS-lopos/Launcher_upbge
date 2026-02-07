import json
from pprint import pprint
from PySide6.QtCore import Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QGridLayout, QLabel, QLineEdit, \
    QPushButton, QFileDialog, QSizePolicy, QSpinBox, QCheckBox
from Fonction.manipuler_donner import charger, config, config_launcher_json, preference_launcher_json

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
            "Interface",
            "Système"
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
        if page is None:
            self.affiche.addWidget(self.general())
        if page == "gen":
            self.affiche.addWidget(self.general())
        elif page == "ui":
            self.affiche.addWidget(self.interface())
        elif page == "sys":
            self.affiche.addWidget(self.systeme())

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
        widget = QWidget(self)
        grille = QGridLayout()
        
        ########## code ###########
        self.LE_dossier_export = QLineEdit()
        self.LE_dossier_export.setText(charger("preference")["dossier_export"])
        B_dossier_export = QPushButton("+")
        B_dossier_export.clicked.connect(lambda: self.selection_dossier_fichier(self.LE_dossier_export, 0))
        #------
        self.Flargeur = QSpinBox()
        self.Flargeur.setMaximum(1900)
        self.Flargeur.setValue(charger("preference").get("taille")[0])
        self.Fhauteur = QSpinBox()
        self.Fhauteur.setMaximum(1900)
        self.Fhauteur.setValue(charger("preference").get("taille")[1])
        #------
        self.plein_ecran: QCheckBox = QCheckBox("Plein écran")
        self.plein_ecran.setChecked(charger("preference").get("fullscreen", False))
        self.moteur_commun: QCheckBox = QCheckBox("Moteur Commun")
        self.moteur_commun.setChecked(charger("preference").get("moteur_commun", False))
        #------
        # Label LineEditte BoutonSelectDossier
        ligne1 = QHBoxLayout()
        ligne1.addWidget(QLabel("Taille ecran: "))
        ligne1.addWidget(self.Flargeur)
        ligne1.addWidget(QLabel("x"))
        ligne1.addWidget(self.Fhauteur)
        ########## Grille Layout ##########
        grille.addWidget(QLabel("dossier d'export: "), 0, 0, 1, 1)
        grille.addWidget(self.LE_dossier_export, 0, 1, 1, 3)
        grille.addWidget(B_dossier_export, 0, 4, 1, 1)
        grille.addLayout(ligne1, 1, 0, 1, 2)
        grille.addWidget(self.plein_ecran, 2, 0, 1, 1)
        grille.addWidget(self.moteur_commun, 2, 1, 1, 1)

        #widget.setLayout(col)
        widget.setLayout(grille)
        return widget

    def interface(self):
        widget = QWidget(self)
        grille = QGridLayout()

        b_custom_theme = QCheckBox("Thème Custom")
        ##### élément #####

        ##### Grille #####
        grille.addWidget(b_custom_theme, 0, 0, 1, 1)
        grille.addWidget(QLabel("Couleur Base"), 1, 0, 1, 1)
        grille.addWidget(QLabel("Couleur terminal"), 2, 0, 1, 1)
        grille.addWidget(QLabel("Couleur affichage projet"), 3, 0, 1, 1)
        grille.addWidget(QLabel("Couleur Liste Projet"), 4, 0, 1, 1)
        grille.addWidget(QLabel("Couleur Liste Fichier"), 5, 0, 1, 1)
        grille.addWidget(QLabel("Couleur Arborescence Projet"), 6, 0, 1, 1)
        grille.addWidget(QLabel("Couleur Barre status"), 7, 0, 1, 1)
        grille.addWidget(QLabel("Couleur Barre outils"), 8, 0, 1, 1)
        grille.addWidget(QLabel("Couleur app menu"), 9, 0, 1, 1)

        widget.setLayout(grille)
        return widget

    def systeme(self):
        widget = QWidget(self)
        grille = QGridLayout()

        ##### élément #####
        check_code = QCheckBox("code")
        check_image = QCheckBox("image")
        check_video = QCheckBox("vidéo")
        self.edit_code = QLineEdit()
        self.vue_image = QLineEdit()
        self.vue_video = QLineEdit()
        b_code = QPushButton("*")
        b_image = QPushButton("/")
        b_video = QPushButton("-")
        ##### Ligne #####
        ligne1 = QHBoxLayout()
        ligne1.addWidget(check_code)
        ligne1.addWidget(self.edit_code)
        ligne1.addWidget(b_code)
        ligne2 = QHBoxLayout()
        ligne2.addWidget(check_image)
        ligne2.addWidget(self.vue_image)
        ligne2.addWidget(b_image)
        ligne3 = QHBoxLayout()
        ligne3.addWidget(check_video)
        ligne3.addWidget(self.vue_video)
        ligne3.addWidget(b_video)
        ##### Grille #####
        grille.addWidget(QLabel("Editeur Code"), 0, 0, 1, 1)
        grille.addLayout(ligne1, 1, 0, 1, 1)
        grille.addWidget(QLabel("Visioneur Image"), 2, 0, 1, 1)
        grille.addLayout(ligne2, 3, 0, 1, 1)
        grille.addWidget(QLabel("Visioneur Vidéo"), 4, 0, 1, 1)
        grille.addLayout(ligne3, 5, 0, 1, 1)

        widget.setLayout(grille)
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
        # page est la fenêtre active
        # la fonction ne doit être actif que pour la page active
        # différencier chaque application via sa propre fenêtre
        with open((config / preference_launcher_json), 'r') as f:
            r_data = json.load(f)
            pprint(r_data)

        data = r_data
        if self.LE_dossier_export.text() != "":
            data["dossier_export"] = self.LE_dossier_export.text()
        data["taille"] = [self.Flargeur.value(), self.Fhauteur.value()]
        if self.plein_ecran.isChecked(): data["fullscreen"] = True
        else: data["fullscreen"] = False
        if self.moteur_commun.isChecked(): data["moteur_commun"] = True
        else: data["moteur_commun"] = False
        with open((config / preference_launcher_json), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        pprint(data)


    def impri(self, obj):
        new_page = obj.text()
        if new_page != self.page_courante:
            self.page_courante = new_page
            self.conteneur.removeWidget(self.zone_config)
            self.zone_config.deleteLater()
            if new_page == "Général":
                self.zone_config = self.affiche_page("gen")
            elif new_page == "Interface":
                self.zone_config = self.affiche_page("ui")
            elif new_page == "Système":
                self.zone_config = self.affiche_page("sys")
            self.conteneur.addWidget(self.zone_config, 0, 1, 1, 3)