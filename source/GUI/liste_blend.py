import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from pathlib import Path
from subprocess import run
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, Qt

from program.manipuler_donner import charger

class Lblend(QWidget):
    def __init__(self, save):
        super().__init__()
        self.save = save
        self.old_global = None
        self.lister = []
        tableau = QTabWidget(self)
        #page
        self.p1 = QListWidget()
                
        #tableau
        tableau.addTab(self.p1, QIcon(""), "Fichier.blend")
        # charger le tableau des que charger_blend est mis à jour
        tableau.currentChanged.connect(self.charger_blend)
        
        # Bouton Editer Fichier
        b_edition = QPushButton("Edition Fichier")
        b_edition.clicked.connect(self.edition_projet)
        # Bouton Tester Fichier
        b_test = QPushButton("Tester Fichier")
        b_test.clicked.connect(self.tester_fichier)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(tableau)
        layout.addWidget(b_edition)
        layout.addWidget(b_test)
        self.setLayout(layout)
        self.setFixedWidth((1280*0.2))

        # Configurer le timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_global)  # Connecter le signal timeout à la méthode check_global
        self.timer.start(60)  # Vérifier toutes les secondes (1000 ms)
    
    def check_global(self):
        self.f_global = charger("global")  # Charger la valeur actuelle de f_global
        if self.f_global != self.old_global:  # Vérifier si f_global a changé
            self.old_global = self.f_global  # Mettre à jour la valeur précédente
            self.charger_blend()  # Recharger l'affichage complet
    
    def charger_blend(self):
        self.lister.clear()
        self.f_global = charger("global")
        projet = None
        for p in self.f_global:
            if self.f_global["p_actif"]:
                p = self.f_global["p_actif"]
                projet = Path(p)
                break
        if projet:
            l_p = []
            l_p += list(projet.glob('**/*.blend'))
            l_p += list(projet.glob('**/*.range'))
            self.lister = l_p
            self.update_list_widget()

    def update_list_widget(self):
        self.p1.clear()  # Clear the current items
        for item in self.lister:
            self.p1.addItem(Path(item).name)  # Add the new items
    
    def tester_fichier(self):
        id_selectionner = self.p1.selectedIndexes()
        if id_selectionner:
            obj_selectionner = id_selectionner[0].data()
            commande = []
            for i in self.lister:
                if Path(i).name == obj_selectionner:
                    chemin = Path(i).resolve()
                    parties = list(chemin.parts)
                    base = parties.index('data')
                    moteur_linux = charger("linux")
                    moteur_windows = charger("windows")
                    if parties[base:base+3] == ['data', 'Linux', '2x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-2x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['data', 'Linux', '3x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-3x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['data', 'Linux', '4x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-4x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['data', 'Linux', 'Range']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-L-Range":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur) 
                    elif parties[base:base+3] == ['data', 'Windows', '2x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-2x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['data', 'Windows', '3x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-3x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['data', 'Windows', '4x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-4x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['data', 'Windows', 'Range']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-W-Range":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    commande.append(str(i))
            if self.save.checkState() == Qt.Unchecked:
                try:
                    os.system(f"nohup '{commande[0]}' '{commande[-1]}' > /dev/null 2>&1 &")
                except: 
                    print("active commande de sauvetage dans le menu Option ;)")
            if self.save.checkState() == Qt.Checked:
                try:
                    # avec un environement os.system ne fonctionne pas
                    env = os.environ.copy()
                    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                    run(commande, check=True, env=env)
                except: print("Dommage mais ne marche pas XD")

    def edition_projet(self):
        id_selectionner = self.p1.selectedIndexes()
        if id_selectionner:
            obj_selectionner = id_selectionner[0].data()
            commande = []
            for i in self.lister:
                if Path(i).name == obj_selectionner:
                    chemin = Path(i).resolve()
                    parties = list(chemin.parts)
                    base = parties.index('data')
                    moteur_linux = charger("linux")
                    moteur_windows = charger("windows")
                    if parties[base:base+3] == ['data', 'Linux', '2x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-2x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['data', 'Linux', '3x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-3x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['data', 'Linux', '4x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-4x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['data', 'Linux', 'Range']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-Range":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur) 
                    elif parties[base:base+3] == ['data', 'Windows', '2x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-2x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['data', 'Windows', '3x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-3x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['data', 'Windows', '4x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-4x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['data', 'Windows', 'Range']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-Range":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    commande.append(i)
            if self.save.checkState() == Qt.Unchecked:
                try: run(commande, check=True)
                except: print("active commande de sauvetage dans le menu Option ;)")
            if self.save.checkState() == Qt.Checked:
                try:
                    env = os.environ.copy()
                    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                    run(commande, check=True, env=env)
                except: print("Dommage mais ne marche pas XD")