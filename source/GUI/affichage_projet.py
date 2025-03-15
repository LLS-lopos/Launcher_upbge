from PySide6.QtWidgets import QWidget, QFrame, QLabel, QGridLayout

class Affichage_projet(QWidget):
    def __init__(self):
        super().__init__()

        # Créer un QFrame pour contenir la mise en page
        affiche = QFrame()
        affiche.setMaximumWidth(600)  # Définir la largeur maximale du QFrame

        # Créer une QGridLayout
        grille = QGridLayout()

        # Créer un QLabel et définir son texte
        titre = QLabel()  # Créer le QLabel sans argument
        titre.setText("UP-BGE")  # Définir le texte du QLabel

        # Ajouter le QLabel à la mise en page de la grille
        grille.addWidget(titre, 0, 0, 1, 1)  # Ajouter le QLabel à la position (0, 0) dans la grille

        # Définir la mise en page pour le QFrame
        affiche.setLayout(grille)

        # Créer une mise en page principale pour le widget
        main_layout = QGridLayout(self)  # Créer une mise en page pour le widget principal
        main_layout.addWidget(affiche)  # Ajouter le QFrame à la mise en page principale
        self.setLayout(main_layout)  # Définir la mise en page principale pour le widget
