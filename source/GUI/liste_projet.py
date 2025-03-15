from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget
from PySide6.QtGui import QIcon


class Lprojet(QWidget):
    def __init__(self):
        super().__init__()

        tableau = QTabWidget(self)
        tableau.setMaximumWidth(300)

        #page
        p1 = QListWidget()
        p1.addItem("test")

        #tableau
        tableau.addTab(p1, QIcon(""), "P1")

        layout = QVBoxLayout()
        layout.addWidget(tableau)
        self.setLayout(layout)


