import os, sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from pathlib import Path
from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from program.manipuler_donner import charger

class DosStructure(QWidget):
    def __init__(self):
        super().__init__()
        self.old_actif = None
        layout = QVBoxLayout(self)  # Créer le layout principal

        # Créer l'arbre avec ses propriétés
        self.arbre = QTreeWidget(self)
        self.arbre.setColumnCount(1) # 2
        self.arbre.setHeaderLabels(["Nom"]) # ["Nom", "Type"]

        # Ajouter l'arbre au layout
        layout.addWidget(self.arbre)

        # Configurer le timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_global)  # Connecter le signal timeout à la méthode check_global
        self.timer.start(60)  # Vérifier toutes les secondes (1000 ms)

    def check_global(self):
        self.actif = charger("global").get("p_actif")
        if self.actif != self.old_actif:
            self.old_actif = self.actif
            self.arbre.clear()
            self.trie_donner(self.old_actif)
    
    def trie_donner(self, base):
        l_donner = {}
        if Path(base):
            l_file = list(Path(base).glob('**/*'))
            for i in l_file:
                sep = str(i).split("/")
                for e in range(len(base.split("/"))):
                    sep.pop(0)
                n_sep = "/".join(sep)
                l_donner[Path(i)] = n_sep
        self.organiser_donner(l_donner)

    def organiser_donner(self, donner):
        # Créer une structure d'arbre imbriquée à partir des chemins plats
        tree_structure = {}
        
        for dos, min_dos in donner.items():
            path_parts = min_dos.split("/")
            current_level = tree_structure
            # Naviguer à travers le chemin, en créant des dictionnaires imbriqués
            for i, part in enumerate(path_parts):
                if part not in current_level:  # Déterminer si c'est la dernière partie (peut être un fichier ou un dossier)
                    if i == len(path_parts) - 1:  # C'est l'élément final - vérifier si c'est un fichier
                        is_file = '.' in part
                        current_level[part] = None if is_file else {}
                    else:   # C'est un dossier intermédiaire
                        current_level[part] = {}

                if i < len(path_parts) - 1:  # Passer au niveau suivant (si pas à la fin)
                    current_level = current_level[part]

        self.construire_arbre(tree_structure)  # Construire l'arbre depuis la structure imbriquée
        
    def construire_arbre(self, tree_structure, parent_item=None):
        """Construit récursivement les éléments QTreeWidget depuis la structure de dictionnaire imbriquée"""
        if parent_item is None:  # Effacer les éléments existants et commencer depuis la racine
            self.arbre.clear()
            parent_item = self.arbre.invisibleRootItem()
        
        for name, content in tree_structure.items():  # Déterminer si c'est un fichier ou un dossier
            if content is None:
                # C'est un fichier
                # extension = name.split('.')[-1].upper() if '.' in name else ""
                item = QTreeWidgetItem([name]) # [name, extension]
                item.setData(0, Qt.UserRole, "file")  # Marquer comme fichier
                parent_item.addChild(item)
            else:
                # C'est un dossier
                item = QTreeWidgetItem([name]) # [name, "Dossier"]
                item.setData(0, Qt.UserRole, "folder")  # Marquer comme dossier
                parent_item.addChild(item)

                self.construire_arbre(content, item)  # Construire récursivement les enfants
        
        # Déplier tous les éléments pour une meilleure visibilité
        self.arbre.expandAll()