import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QScrollArea
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap
from pathlib import Path
from program.manipuler_donner import charger

class Affichage_projet(QWidget):
    def __init__(self):
        super().__init__()
        self.list_img = []
        self.old_global = None  # Pour stocker la valeur précédente de f_global

        # Créer un QVBoxLayout pour contenir la mise en page
        self.affiche = QVBoxLayout()

        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.area.setLayout(self.affiche)

        # Créer un widget conteneur pour le QScrollArea
        container_widget = QWidget()
        container_widget.setLayout(self.affiche)  # Appliquer le layout au widget conteneur
        self.area.setWidget(container_widget)  # Définir le widget conteneur comme le widget du QScrollArea
        # Ajouter le QScrollArea au layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.area)  # Ajouter le QScrollArea au layout principal

        self.setLayout(layout)  # Définir la mise en page principale pour le widget
        
        # Configurer le timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_global)  # Connecter le signal timeout à la méthode check_global
        self.timer.start(60)  # Vérifier toutes les secondes (1000 ms)
        self.recharger()  # Charger initialement le contenu

    def recharger(self):
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
        
        # Recharger le contenu
        self.affiche.addLayout(self.titre())  # Ajouter le titre
        self.affiche.addWidget(self.illustration())  # Ajouter les images
        self.affiche.addLayout(self.description())  # Ajouter la description

    def clear_layout(self, layout):
        # Méthode pour supprimer récursivement tous les widgets et layouts
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            else:
                nested_layout = item.layout()
                if nested_layout is not None:
                    self.clear_layout(nested_layout)

    def check_global(self):
        current_global = charger("global")  # Charger la valeur actuelle de f_global
        if current_global != self.old_global:  # Vérifier si f_global a changé
            self.old_global = current_global  # Mettre à jour la valeur précédente
            self.recharger()  # Recharger l'affichage complet
    
    def titre(self):
        widget = QHBoxLayout()
        # Créer un QLabel et définir son texte
        logo = charger("config_launcher")["icon"]
        f_global = charger("global")
        
        titre = QLabel("Aucun Projet Sélectionné")  # Créer le QLabel sans argument
        icone = QLabel()
        icone.setFixedSize(50, 50)
        if f_global:
            for cle, valeur in f_global.items():  # itération sur les éléments
                project_path = Path(valeur)
                # Déterminer l'icône
                if "Range" in project_path.parts:
                    pixmap = QPixmap(logo.get("range")).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    prefix = "Range"
                else:
                    pixmap = QPixmap(logo.get("upbge")).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    prefix = "UPBGE"
                
                icone.setPixmap(pixmap)
                
                # Trouver le fichier .blend
                blend_files = list(project_path.glob("*.blend"))
                range_files = list(project_path.glob("*.range"))
                project_name = project_path.name  # Nom par défaut
                
                if blend_files:
                    # Prendre le premier fichier blend trouvé
                    project_name = blend_files[0].stem  # Nom sans extension
                elif range_files:
                    project_name = range_files[0].stem  # Nom sans extension
                
                titre.setText(f"{prefix} | Projet : {project_path.name} | Jeu : {project_name}")
                break  # Sortir après le premier projet valide

        widget.addWidget(icone)
        widget.addWidget(titre)
        return widget

    def illustration(self):  # afficher les images d'illustration de projet
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        widget.setFixedHeight(300)

        conteneur = QWidget()
        boite_h = QHBoxLayout(conteneur)
        boite_h.setContentsMargins(0, 0, 0, 0)
        boite_h.setSpacing(10)

        f_global = charger("global")
        if f_global:
            for cle, valeur in f_global.items():
                if cle == "p_actif":
                    dos = Path(valeur) / "data"
                    png = list(dos.glob("*.png"))
                    jpg = list(dos.glob("*.jpg"))
                    for i in png + jpg:
                        icone = QLabel()
                        png_pixmap = QPixmap(str(i)).scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        icone.setPixmap(png_pixmap)
                        icone.setAlignment(Qt.AlignCenter)
                        boite_h.addWidget(icone)
        conteneur.setLayout(boite_h)
        widget.setWidget(conteneur)
        return widget

    def description(self):  # afficher les information du fichier de description.txt et Crédits.txt si il existe
        widget = QVBoxLayout()  # Utiliser un QVBoxLayout pour empiler les descriptions
        f_global = charger("global")
        if f_global:
            for cle, valeur in f_global.items():
                if cle == "p_actif":
                    dos = Path(valeur) / "data"
                    # description.txt et Crédits.txt
                    txt = list(dos.glob("**/*.txt"))
                    for fichier in txt:
                        if fichier.name == "description.txt":
                            titre = QLabel("Description\n==========")
                            titre.setStyleSheet("font-size: 20px;")
                            widget.addWidget(titre)
                            with open(str(fichier), "r") as f:
                                id_text = f.readlines()
                                for ligne in id_text:
                                    if len(ligne) > 1:
                                        text = QLabel(ligne)
                                        text.setFixedHeight(16)
                                        widget.addWidget(text)
                                    else:
                                        text = QLabel(ligne)
                                        text.setFixedHeight(6)
                                        widget.addWidget(text)

                        if fichier.name == "crédits.txt":
                            titre = QLabel("Credits\n========")
                            titre.setStyleSheet("font-size: 20px;")
                            widget.addWidget(titre)
                            with open(str(fichier), "r") as f:
                                id_text = f.readlines()
                                for ligne in id_text:
                                    if len(ligne) > 1:
                                        text = QLabel(ligne)
                                        text.setFixedHeight(16)
                                        widget.addWidget(text)
                                    else:
                                        text = QLabel(ligne)
                                        text.setFixedHeight(6)
                                        widget.addWidget(text)
        return widget