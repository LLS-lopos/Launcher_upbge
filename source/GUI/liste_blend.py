from pathlib import Path
from subprocess import run
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

from source.program.manipuler_donner import charger

class Lblend(QWidget):
    def __init__(self):
        super().__init__()
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
            l_p = list(projet.glob('**/*.blend'))
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
                    base = parties.index('source')
                    moteur_linux = charger("linux")
                    moteur_windows = charger("windows")
                    if parties[base:base+3] == ['source', 'Linux', '2x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-2x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['source', 'Linux', '3x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-3x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['source', 'Linux', '4x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-4x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['source', 'Linux', 'Range']:
                        for cle in moteur_linux["executable"]:
                            if cle == "game-L-Range":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur) #################""
                    elif parties[base:base+3] == ['source', 'Windows', '2x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-2x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['source', 'Windows', '3x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-3x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['source', 'Windows', '4x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-4x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['source', 'Windows', 'Range']:
                        for cle in moteur_windows["executable"]:
                            if cle == "game-W-Range":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    commande.append(i)
            run(commande, check=True)

    def edition_projet(self):
        id_selectionner = self.p1.selectedIndexes()
        if id_selectionner:
            obj_selectionner = id_selectionner[0].data()
            commande = []
            for i in self.lister:
                if Path(i).name == obj_selectionner:
                    chemin = Path(i).resolve()
                    parties = list(chemin.parts)
                    base = parties.index('source')
                    moteur_linux = charger("linux")
                    moteur_windows = charger("windows")
                    if parties[base:base+3] == ['source', 'Linux', '2x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-2x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['source', 'Linux', '3x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-3x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['source', 'Linux', '4x']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-4x":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur)
                    elif parties[base:base+3] == ['source', 'Linux', 'Range']:
                        for cle in moteur_linux["executable"]:
                            if cle == "Linux-Range":
                                moteur = moteur_linux["executable"][cle]
                                commande.append(moteur) 
                    elif parties[base:base+3] == ['source', 'Windows', '2x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-2x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['source', 'Windows', '3x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-3x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['source', 'Windows', '4x']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-4x":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif parties[base:base+3] == ['source', 'Windows', 'Range']:
                        for cle in moteur_windows["executable"]:
                            if cle == "Windows-Range":
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())  # Chemin de l'exécutable
                                i = ("Z:" + str(Path(i)).replace("/", "\\"))  # Chemin du fichier .blend
                    commande.append(i)
            run(commande, check=True)

        