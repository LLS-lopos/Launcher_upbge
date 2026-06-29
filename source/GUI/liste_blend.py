import os, sys, platform

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from pathlib import Path
from subprocess import run, Popen, PIPE
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QScrollArea, QPushButton, QHBoxLayout, QCheckBox, QComboBox, QLabel, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, Qt

from Fonction.manipuler_donner import charger
from GUI.Biblio.EditeurDeTexte import LoposEditor
from GUI.Biblio.creerNouveauFichier import CreerFichier

class Lblend(QWidget):
    def __init__(self, save):
        super().__init__()
        self.save = save
        self.old_global = None
        self.lister_blend_range = []
        self.lister_texte = []
        self.lister_script = []
        self.lister_son = []
        self.lister_images = []
        self.lister_video = []
        self.lister_font = []

        self.editors_ouverts = []

        self.tableau = QTabWidget(self)

        # Pages avec scroll
        self.p_blend_range, self.blend_range_layout = self._creer_page_vide()
        self.p_texte, self.texte_layout = self._creer_page_vide()
        self.p_script, self.script_layout = self._creer_page_vide()
        self.p_son, self.son_layout = self._creer_page_vide()
        self.p_image, self.image_layout = self._creer_page_vide()
        self.p_video, self.video_layout = self._creer_page_vide()
        self.p_font, self.font_layout = self._creer_page_vide()

        self.tableau.currentChanged.connect(self.charger_blend)

        b_nouveau_fichier = QPushButton("Créer Fichier")
        b_nouveau_fichier.clicked.connect(self.creer_fichier)

        self.op_custom = QCheckBox("EXE custom")
        self.liste_custom = QComboBox()
        custom_l = charger("config_launcher").get("custom")
        self.exe_custom = {}
        for i in custom_l:
            if Path(custom_l[i]).exists() and custom_l[i] != "":
                self.liste_custom.addItem(QIcon(charger("config_launcher")["icon"].get("upbge.svg")), i)
                self.exe_custom[i] = custom_l[i]

        ligne1 = QHBoxLayout()
        ligne1.addWidget(b_nouveau_fichier)
        ligne2 = QHBoxLayout()
        ligne2.addWidget(self.op_custom)
        ligne2.addWidget(self.liste_custom)

        layout = QVBoxLayout()
        layout.addWidget(self.tableau)
        layout.addLayout(ligne2)
        layout.addLayout(ligne1)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_global)
        self.timer.start(60)

    def _creer_page_vide(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        conteneur = QWidget()
        layout = QVBoxLayout(conteneur)
        scroll.setWidget(conteneur)
        return scroll, layout

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            else:
                sub = item.layout()
                if sub is not None:
                    self._clear_layout(sub)

    def _ajouter_ligne_fichier(self, layout, fichier, type_fichier):
        row = QHBoxLayout()
        nom = QLabel(Path(fichier).name)
        b_test = QPushButton("Tester")
        b_edit = QPushButton("Éditer")
        b_del = QPushButton("Supprimer")

        b_test.clicked.connect(lambda checked, f=fichier: self._tester_fichier(f, type_fichier))
        b_edit.clicked.connect(lambda checked, f=fichier: self._editer_fichier(f, type_fichier))
        b_del.clicked.connect(lambda checked, f=fichier: self._supprimer_fichier(f))

        row.addWidget(nom)
        row.addStretch()
        row.addWidget(b_test)
        row.addWidget(b_edit)
        row.addWidget(b_del)
        layout.addLayout(row)

    def check_global(self):
        try:
            self.f_global = charger("global")
            if self.f_global != self.old_global:
                self.old_global = self.f_global
                self.charger_blend()
                self.charger_font()
                self.charger_image()
                self.charger_script()
                self.charger_texte()
                self.charger_son()
                self.charger_video()
                self.charger_tableau()
        except:
            pass

    def charger_tableau(self):
        while self.tableau.count() > 0:
            self.tableau.removeTab(0)

        for (liste, page, nom) in [
            (self.lister_blend_range, self.p_blend_range, "Blend/Range"),
            (self.lister_texte, self.p_texte, "Texte"),
            (self.lister_script, self.p_script, "Script"),
            (self.lister_son, self.p_son, "Son"),
            (self.lister_images, self.p_image, "Image"),
            (self.lister_video, self.p_video, "Vidéo"),
            (self.lister_font, self.p_font, "Font"),
        ]:
            if liste:
                self.tableau.addTab(page, QIcon(""), nom)

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
            self._clear_layout(self.blend_range_layout)
            for e in self.lister_blend_range:
                self._ajouter_ligne_fichier(self.blend_range_layout, e, "Blend/Range")
            self.blend_range_layout.addStretch()

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
            self._clear_layout(self.texte_layout)
            for e in self.lister_texte:
                self._ajouter_ligne_fichier(self.texte_layout, e, "Texte")
            self.texte_layout.addStretch()

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
            self._clear_layout(self.script_layout)
            for e in self.lister_script:
                self._ajouter_ligne_fichier(self.script_layout, e, "Script")
            self.script_layout.addStretch()

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
            self._clear_layout(self.son_layout)
            for e in self.lister_son:
                self._ajouter_ligne_fichier(self.son_layout, e, "Son")
            self.son_layout.addStretch()

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
            self._clear_layout(self.image_layout)
            for e in self.lister_images:
                self._ajouter_ligne_fichier(self.image_layout, e, "Image")
            self.image_layout.addStretch()

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
            self._clear_layout(self.video_layout)
            for e in self.lister_video:
                self._ajouter_ligne_fichier(self.video_layout, e, "Vidéo")
            self.video_layout.addStretch()

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
            self._clear_layout(self.font_layout)
            for e in self.lister_font:
                self._ajouter_ligne_fichier(self.font_layout, e, "Font")
            self.font_layout.addStretch()

    # --- Actions par fichier ---

    def _tester_fichier(self, fichier, type_fichier):
        if type_fichier == "Blend/Range":
            self._tester_blend(fichier)
        elif type_fichier in ("Texte", "Script"):
            self._editer_texte(fichier)
        else:
            self._ouvrir_systeme(fichier)

    def _editer_fichier(self, fichier, type_fichier):
        if type_fichier == "Blend/Range":
            self._editer_blend(fichier)
        elif type_fichier in ("Texte", "Script"):
            self._editer_texte(fichier)
        else:
            self._ouvrir_systeme(fichier)

    def _tester_blend(self, fichier):
        commande = []
        chemin = Path(fichier).resolve()
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
            elif parties[base:base+3] == ['data', 'Linux', '5x']:
                for cle in moteur_linux["executable"]:
                    if cle == "game-5x":
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
                        commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())
                        fichier = ("Z:" + str(Path(fichier)).replace("/", "\\"))
            elif parties[base:base+3] == ['data', 'Windows', '3x']:
                for cle in moteur_windows["executable"]:
                    if cle == "game-3x":
                        commande.append("wine")
                        commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())
                        fichier = ("Z:" + str(Path(fichier)).replace("/", "\\"))
            elif parties[base:base+3] == ['data', 'Windows', '4x']:
                for cle in moteur_windows["executable"]:
                    if cle == "game-4x":
                        commande.append("wine")
                        commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())
                        fichier = ("Z:" + str(Path(fichier)).replace("/", "\\"))
            elif parties[base:base+3] == ['data', 'Windows', '5x']:
                for cle in moteur_windows["executable"]:
                    if cle == "game-5x":
                        commande.append("wine")
                        commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())
                        fichier = ("Z:" + str(Path(fichier)).replace("/", "\\"))
            elif parties[base:base+3] == ['data', 'Windows', 'Range']:
                for cle in moteur_windows["executable"]:
                    if cle == "game-W-Range":
                        commande.append("wine")
                        commande.append("Z:" + Path(moteur_windows["executable"][cle]).as_posix())
                        fichier = ("Z:" + str(Path(fichier)).replace("/", "\\"))
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
            elif parties[base:base+3] == ['data', 'Windows', '5x']:
                for cle in moteur_windows["executable"]:
                    if cle == "game-5x":
                        moteur = moteur_windows["executable"][cle]
                        commande.append(moteur)
            elif parties[base:base+3] == ['data', 'Windows', 'Range']:
                for cle in moteur_windows["executable"]:
                    if cle == "game-W-Range":
                        moteur = moteur_windows["executable"][cle]
                        commande.append(moteur)
        commande.append(str(fichier))
        self.run_command(commande, self.op_custom, self.save)

    def _editer_blend(self, fichier):
        commande = []
        chemin = Path(fichier).resolve()
        parties = list(chemin.parts)
        base = parties.index('data')
        moteur_windows = charger("config_launcher")["windows"]

        if platform.system() == "Linux":
            moteur_linux = charger("config_launcher")["linux"]
            systeme = parties[base+1]
            version = parties[base+2]
            cle_moteur = f"{systeme}-{version}"

            if systeme == "Linux":
                moteur = moteur_linux["executable"].get(cle_moteur)
                if moteur:
                    commande.append(moteur)
            elif systeme == "Windows":
                moteur = moteur_windows["executable"].get(cle_moteur)
                if moteur:
                    commande.append("wine")
                    commande.append("Z:" + Path(moteur).as_posix())
                    fichier = ("Z:" + str(Path(fichier)).replace("/", "\\"))
        elif platform.system() == "Windows":
            systeme = parties[base+1]
            version = parties[base+2]
            cle_moteur = f"{systeme}-{version}"
            moteur = moteur_windows["executable"].get(cle_moteur)
            if moteur:
                commande.append(moteur)

        commande.append(str(fichier))
        self.run_command(commande, self.op_custom, self.save)

    def _editer_texte(self, fichier):
        chemin = Path(fichier).resolve()
        editor = LoposEditor.ouvrir_fichier(str(chemin))
        self.editors_ouverts.append(editor)

    def _ouvrir_systeme(self, fichier):
        if platform.system() == "Linux":
            Popen(['xdg-open', str(fichier)])
        elif platform.system() == "Windows":
            os.startfile(str(fichier))
        elif platform.system() == "Darwin":
            Popen(['open', str(fichier)])

    def _supprimer_fichier(self, fichier):
        reponse = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Supprimer définitivement {Path(fichier).name} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            try:
                Path(fichier).unlink()
                self.charger_blend()
                self.charger_font()
                self.charger_image()
                self.charger_script()
                self.charger_texte()
                self.charger_son()
                self.charger_video()
                self.charger_tableau()
            except Exception as e:
                print(f"Erreur lors de la suppression : {e}")

    def creer_fichier(self):
        self.new_fichier = CreerFichier()
        self.new_fichier.show()

    def run_command(self, commande, option, sauvetage):
        if option.isChecked():
            for i in self.exe_custom:
                if i == self.liste_custom.currentText():
                    commande[0] = self.exe_custom[i]

        try:
            Popen(commande, stdin=PIPE, stdout=PIPE, stderr=PIPE, start_new_session=True)
        except:
            print("tentative de secour")

        if sauvetage.checkState() == Qt.Checked:
            try:
                env = os.environ.copy()
                env["LIBGL_ALWAYS_SOFTWARE"] = "1"
                run(commande, check=True, env=env)
            except:
                print("Dommage mais ne marche pas XD")
