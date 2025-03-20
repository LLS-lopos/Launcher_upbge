from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget
from PySide6.QtGui import QIcon

from pathlib import Path

from source.program.manipuler_donner import charger

class Lprojet(QWidget):
    def __init__(self):
        super().__init__()
        icone = charger("icon")
        print(icone)
        layout = QVBoxLayout()
        tableau = QTabWidget(self)
        tableau.setMaximumWidth(300)

        linux = charger("linux")
        for v_projet in linux["projet"]:
            page = QListWidget() # page (élément de tableau)
            for projet in linux["projet"][v_projet]:
                if projet:
                    page.addItem(Path(projet).name)
                tableau.addTab(page, QIcon(icone.get("linux")), str(v_projet)) # ajouter page au tableau
        
        windows = charger("windows")
        for v_projet in windows["projet"]:
            page = QListWidget() # page (élément de tableau)
            for projet in windows["projet"][v_projet]:
                if projet:
                    page.addItem(Path(projet).name)
                tableau.addTab(page, QIcon(icone.get("windows")), str(v_projet)) # ajouter page au tableau

        layout.addWidget(tableau)
        self.setLayout(layout)
