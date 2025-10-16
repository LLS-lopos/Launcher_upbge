import os, sys, platform

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from pathlib import Path
from subprocess import run, Popen, PIPE
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, Qt

from program.manipuler_donner import charger
from GUI.EditeurDeTexte import LoposEditor
from GUI.creerNouveauFichier import CreerFichier

class Lblend(QWidget):
    def __init__(self, save):
        super().__init__()
        self.save = save
        self.old_global = None
        self.lister_blend_range = [] # Gère les fichiers Blender et range (ok)
        self.lister_texte = [] # Gère les fichiers texte
        self.lister_script = [] # Gère les fichiers Python
        self.lister_son = [] # Gère les fichiers audio
        self.lister_images = [] # Gère les images/textures
        self.lister_video = [] # Gère les vidéos
        self.lister_font = [] # Gère les chaînes de caractères
        
        # Réintroduire la liste des éditeurs ouverts
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
        
        # Bouton Éditer Fichier
        b_edition = QPushButton("Édition Fichier")
        b_edition.clicked.connect(self.edition_projet)
        # Bouton Tester Fichier
        b_test = QPushButton("Tester Fichier")
        b_test.clicked.connect(self.tester_fichier)
        # Bouton création de fichier
        b_nouveau_fichier = QPushButton("Créer Fichier")
        b_nouveau_fichier.clicked.connect(self.creer_fichier)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(b_nouveau_fichier)
        layout.addWidget(self.tableau)
        layout.addWidget(b_edition)
        layout.addWidget(b_test)
        self.setLayout(layout)

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
        # Définir les informations des onglets et leurs données
        self.tab_info = [
            (self.lister_blend_range, self.p_blend_range, "Blend/Range"),
            (self.lister_texte, self.p_texte, "Texte"),
            (self.lister_script, self.p_script, "Script"),
            (self.lister_son, self.p_son, "Son"),
            (self.lister_images, self.p_image, "Image"),
            (self.lister_video, self.p_video, "Vidéo"),
            (self.lister_font, self.p_font, "Font"),
        ]
        
        # Stocker les onglets existants avant modification
        existing_tabs = {}
        for i in range(self.tableau.count()):
            existing_tabs[self.tableau.tabText(i)] = self.tableau.widget(i)
        
        # Supprimer tous les onglets existants
        while self.tableau.count() > 0:
            self.tableau.removeTab(0)
        
        # Ajouter dynamiquement les onglets pour les listes non vides
        pages_creees = []
        for (liste, page, tableau) in self.tab_info:
            if liste:
                # Utiliser l'onglet existant si possible, sinon créer un nouveau
                if tableau in [text for text in existing_tabs.keys()]:
                    self.tableau.addTab(existing_tabs[tableau], QIcon(""), tableau)
                    pages_creees.append((liste, existing_tabs[tableau], tableau, "existant"))
                else:
                    self.tableau.addTab(page, QIcon(""), tableau)
                    pages_creees.append((liste, page, tableau, "nouveau"))
        
        # Afficher les pages créées
        #print("Pages créées :", [(p[2], p[3]) for p in pages_creees])
        # Créer l'index à partir de pages_creees
        index_page = 0
        for i, page in enumerate(pages_creees):
            if page[3] == "existant":
                index_page = i
                break
        
        # Sélectionner l'index trouvé ou le premier onglet
        if self.tableau.count() > 0:
            self.tableau.setCurrentIndex(index_page)

        # Stocker pages_creees comme attribut de l'instance
        self.pages_creees = pages_creees

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
            l_p += list(projet.glob('**/*.blend@'))
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
                base = Path(t)
                script = base / "data" / "donné" / "actifs" / "Scripts"
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
                base = Path(t)
                son = base / "data" / "donné" / "Audio"
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
                    moteur_windows = charger("config_launcher")["windows"]
                    if platform.system() == "Linux":
                        moteur_linux = charger("config_launcher")["linux"]
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
                    elif platform.system() == "Windows":
                        if parties[base:base+3] == ['data', 'Windows', '2x']:
                            for cle in moteur_windows["executable"]:
                                if cle == "game-2x":
                                    moteur = moteur_windows["executable"][cle]
                                    commande.append(moteur)
                        elif parties[base:base+3] == ['data', 'Windows', '3x']:
                            for cle in moteur_windows["executable"]:
                                if cle == "game-3x":
                                    moteur = moteur_windows["executable"][cle]
                                    commande.append(moteur)
                        elif parties[base:base+3] == ['data', 'Windows', '4x']:
                            for cle in moteur_windows["executable"]:
                                if cle == "game-4x":
                                    moteur = moteur_windows["executable"][cle]
                                    commande.append(moteur)
                    commande.append(str(i))
        if self.save.checkState() == Qt.Unchecked:
            try:
                Popen(
                    commande,
                    stdin=PIPE,
                    stdout=PIPE,
                    stderr=PIPE,
                    start_new_session=True,
                    )
            except: 
                print("Activez la commande de sauvegarde dans le menu Options ;)")
        if self.save.checkState() == Qt.Checked:
            try:
                # avec un environnement os.system ne fonctionne pas
                env = os.environ.copy()
                env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                run(commande, check=True, env=env)
            except: print("Dommage mais ne marche pas XD")

    def edition_projet(self):
        onglet = self.tableau.currentIndex() # Récupérer l'index de l'onglet actuel
        
        # Utilisation pages_creees
        if 0 <= onglet < len(self.pages_creees):
            type_onglet = self.pages_creees[onglet][2]
            liste_fichiers = self.pages_creees[onglet][0]
            page_widget = self.pages_creees[onglet][1]
        else:
            type_onglet = None
            liste_fichiers = []
            page_widget = None

        # Vérifier si des fichiers sont disponibles
        if liste_fichiers and page_widget:
            index_selectionne = page_widget.currentRow() # Récupérer l'index de l'élément sélectionné
            
            if 0 <= index_selectionne < len(liste_fichiers):
                fichier_selectionne = liste_fichiers[index_selectionne]
                
                if type_onglet == "Blend/Range":
                    # Traitement blend/range
                    commande = []
                    chemin = Path(fichier_selectionne).resolve()
                    parties = list(chemin.parts)
                    base = parties.index('data')
                    if platform.system() == "Linux": moteur_linux = charger("config_launcher")["linux"]
                    moteur_windows = charger("config_launcher")["windows"]
                    
                    # Déterminer le système d'exploitation et la version
                    systeme = parties[base+1]  # Linux ou Windows
                    version = parties[base+2]  # 2x, 3x, 4x, ou Range
                    
                    # Clé de recherche pour le moteur
                    cle_moteur = f"{systeme}-{version}"
                    
                    # Sélectionner le bon moteur
                    if platform.system() == "Linux":
                        if systeme == "Linux":
                            moteur = moteur_linux["executable"].get(cle_moteur)
                            if moteur:
                                commande.append(moteur)
                        
                        elif systeme == "Windows":
                            moteur = moteur_windows["executable"].get(cle_moteur)
                            if moteur:
                                commande.append("wine")
                                commande.append("Z:" + Path(moteur).as_posix())  # Chemin de l'exécutable
                                fichier_selectionne = ("Z:" + str(Path(fichier_selectionne)).replace("/", "\\"))  # Chemin du fichier .blend
                    elif platform.system() == "Windows":
                        moteur = moteur_windows["executable"].get(cle_moteur)
                        if moteur:
                            commande.append(moteur)  # Chemin de l'exécutable
                    commande.append(fichier_selectionne)
                    
                    # Gestion de l'exécution avec ou sans commande de vauvetage
                    if self.save.checkState() == Qt.Unchecked:
                        try: 
                            Popen(
                                commande,
                                stdin=PIPE,
                                stdout=PIPE,
                                stderr=PIPE,
                                start_new_session=True,
                                )
                        except: 
                            print("Activez la commande de sauvegarde dans le menu Options ;)")
                    
                    if self.save.checkState() == Qt.Checked:
                        try:
                            env = os.environ.copy()
                            env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                            run(commande, check=True, env=env)
                        except: 
                            print("Dommage mais ne marche pas XD")
                # Ouvrir l'éditeur texte
                elif type_onglet in ["Texte", "Script"]:
                    chemin = Path(fichier_selectionne).resolve()
                    print(chemin)
                    editor = LoposEditor.ouvrir_fichier(str(chemin))
                    self.editors_ouverts.append(editor)
        else:
            print("Aucune sélection ou onglet inconnu")
    
    def creer_fichier(self):
        self.new_fichier = CreerFichier()
        self.new_fichier.show()
