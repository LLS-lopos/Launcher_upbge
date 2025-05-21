import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from pathlib import Path
from subprocess import run
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, Qt

from program.manipuler_donner import charger
from GUI.EditeurDeTexte import LoposEditor

class Lblend(QWidget):
    def __init__(self, save):
        super().__init__()
        self.save = save
        self.old_global = None
        self.lister_blend_range = [] # gère les fichier blender et range (ok)
        self.lister_texte = [] # gère les fichier texte
        self.lister_script = [] # gère les fichier python
        self.lister_son = [] # gère les fichier audio
        self.lister_images = [] # gère les images/texture
        self.lister_video = [] # gère les vidéos
        self.lister_font = [] # gère les chaine de caractère
        self.editors_ouverts = []

        self.tableau = QTabWidget(self)
        #page
        self.p_blend_range = QListWidget()
        self.p_texte = QListWidget()
        self.p_script = QListWidget()
        self.p_son = QListWidget()
        self.p_image = QListWidget()
        self.p_video = QListWidget()
        self.p_font = QListWidget()
        
        # charger le tableau des que charger_blend est mis à jour
        self.tableau.currentChanged.connect(self.charger_blend)
        
        # Bouton Editer Fichier
        b_edition = QPushButton("Edition Fichier")
        b_edition.clicked.connect(self.edition_projet)
        # Bouton Tester Fichier
        b_test = QPushButton("Tester Fichier")
        b_test.clicked.connect(self.tester_fichier)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tableau)
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
            self.charger_blend()  # Recharger l'affichage fichier blend/range
            self.charger_font()
            self.charger_image()
            self.charger_script()
            self.charger_texte()
            self.charger_son()
            self.charger_video()
            self.charger_tableau()
    
    def charger_tableau(self):
        self.tab_info = [
        (self.lister_blend_range, self.p_blend_range, "Blend/Range"),
        (self.lister_texte, self.p_texte, "Texte"),
        (self.lister_script, self.p_script, "Script"),
        (self.lister_son, self.p_son, "Son"),
        (self.lister_images, self.p_image, "Image"),
        (self.lister_video, self.p_video, "Video"),
        (self.lister_font, self.p_font, "Font"),
    ]
        for (liste, page, tableau) in self.tab_info:
            if liste:
                if self.tableau.indexOf(page) == -1:  # Check if tab is already added
                    self.tableau.addTab(page, QIcon(""), tableau)
            else:
                index = self.tableau.indexOf(page)
                if index != -1:  # Check if tab exists
                    self.tableau.removeTab(index)

    def charger_blend(self):
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
            self.lister_blend_range = l_p
            self.p_blend_range.clear()
            for e in self.lister_blend_range:
                self.p_blend_range.addItem(Path(e).name)
        
    def charger_texte(self):
        texte = None
        for t in self.f_global:
            if self.f_global["p_actif"]:
                t = self.f_global["p_actif"]
                texte = Path(t)
                break
        if texte:
            fichier = []
            fichier += list(texte.glob('**/*.txt'))
            self.lister_texte = fichier
            self.p_texte.clear()
            for texte in self.lister_texte:
                self.p_texte.addItem(Path(texte).name)

    def charger_script(self):
        script = None
        for t in self.f_global:
            if self.f_global["p_actif"]:
                t = self.f_global["p_actif"]
                script = Path(t)
                break
        if script:
            fichier = []
            fichier += list(script.glob('**/*.py'))
            self.lister_script = fichier
            self.p_script.clear()
            for e in self.lister_script:
                self.p_script.addItem(Path(e).name)

    def charger_son(self):
        son = None
        for t in self.f_global:
            if self.f_global["p_actif"]:
                t = self.f_global["p_actif"]
                son = Path(t)
                break
        if son:
            fichier = []
            fichier += list(son.glob('**/*.ogg'))
            fichier += list(son.glob('**/*.mp3'))
            self.lister_son = fichier
            self.p_son.clear()
            for e in self.lister_son:
                self.p_son.addItem(Path(e).name)

    def charger_image(self):
        img = None
        for t in self.f_global:
            if self.f_global["p_actif"]:
                t = self.f_global["p_actif"]
                img = Path(t)
                break
        if img:
            fichier = []
            fichier += list(img.glob('**/*.png'))
            fichier += list(img.glob('**/*.jpg'))
            fichier += list(img.glob('**/*.jpeg'))
            self.lister_images = fichier
            self.p_image.clear()
            for e in self.lister_images:
                self.p_image.addItem(Path(e).name)
                
    def charger_video(self):
        video = None
        for t in self.f_global:
            if self.f_global["p_actif"]:
                t = self.f_global["p_actif"]
                video = Path(t)
                break
        if video:
            fichier = []
            fichier += list(video.glob('**/*.mkv'))
            fichier += list(video.glob('**/*.mp4'))
            fichier += list(video.glob('**/*.avi'))
            self.lister_video = fichier
            self.p_video.clear()
            for e in self.lister_video:
                self.p_video.addItem(Path(e).name)

    def charger_font(self):
        font = None
        for t in self.f_global:
            if self.f_global["p_actif"]:
                t = self.f_global["p_actif"]
                font = Path(t)
                break
        if font:
            fichier = []
            fichier += list(font.glob('**/*.ttf'))
            fichier += list(font.glob('**/*.otf'))
            self.lister_font = fichier
            self.p_font.clear()
            for e in self.lister_font:
                self.p_font.addItem(Path(e).name)

    def tester_fichier(self):
        id_blend_range = self.p_blend_range.selectedIndexes()
        commande = []
        if id_blend_range:
            obj_selectionner = id_blend_range[0].data()
            for i in self.lister_blend_range:
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
        id_blend_range = self.p_blend_range.selectedIndexes()
        id_texte = self.p_texte.selectedIndexes()
        id_script = self.p_script.selectedIndexes()

        onglet = self.tableau.currentIndex()
        if onglet < len(self.tab_info):
            type_onglet = self.tab_info[onglet][2]
        else:
            type_onglet = None
        print(type_onglet)

        if type_onglet == "Blend/Range" and id_blend_range:
            # Traitement blend
            commande = []
            obj_selectionner = id_blend_range[0].data()
            for i in self.lister_blend_range:
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
        elif type_onglet == "Texte" and id_texte:
            obj_selectionner = id_texte[0].data()
            for i in self.lister_texte:
                if Path(i).name == obj_selectionner:
                    chemin = Path(i).resolve()
                    print(chemin)
                    editor = LoposEditor.ouvrir_fichier(str(chemin))
                    self.editors_ouverts.append(editor)
        elif type_onglet == "Script" and id_script:
            obj_selectionner = id_script[0].data()
            for i in self.lister_script:
                if Path(i).name == obj_selectionner:
                    chemin = Path(i).resolve()
                    print(chemin)
                    editor = LoposEditor.ouvrir_fichier(str(chemin))
                    self.editors_ouverts.append(editor)
        else:
            print("Aucune sélection ou onglet inconnu")
