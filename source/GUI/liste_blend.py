from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton
from PySide6.QtGui import QIcon

from source.program.manipuler_donner import charger

class Lblend(QWidget):
    def __init__(self):
        super().__init__()

        tableau = QTabWidget(self)

        #page
        p1 = QListWidget()
        p1.addItem("test")
        #tableau
        tableau.addTab(p1, QIcon(""), "P1")

        # Bouton Editer Fichier
        b_edition = QPushButton("Edition Fichier")
        # Bouton Tester Fichier
        b_test = QPushButton("Tester Fichier")

        layout = QVBoxLayout()
        layout.addWidget(tableau)
        layout.addWidget(b_edition)
        layout.addWidget(b_test)
        self.setLayout(layout)
        self.setFixedWidth((1280*0.2))