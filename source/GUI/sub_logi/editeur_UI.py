import sys
import os

# Add the source directory to Python path
source_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          '..', '..'))
sys.path.insert(0, source_dir)

#: Chemin du thème BGUI chargé par défaut dans l'onglet « CODE ».
CHEMIN_THEME = os.path.join(source_dir, "Scripts", "theme.cfg")

#: Drapeaux « Widget options » d'un widget (constantes bgui/widget.py).
#: ``BGUI_CENTERED`` est un méta-drapeau = CENTERX | CENTERY.
DRAPEAUX_OPTIONS = [
    (1, "BGUI_CENTERX", "Centrer horizontalement"),
    (2, "BGUI_CENTERY", "Centrer verticalement"),
    (4, "BGUI_NO_NORMALIZE", "Pas de normalisation des coordonnées"),
    (8, "BGUI_NO_THEME", "Ignorer le thème du widget"),
    (16, "BGUI_NO_FOCUS", "Ne pas accepter le focus clavier/souris"),
    (32, "BGUI_CACHE", "Mettre le rendu du widget en cache"),
]
BIT_CENTERED = 1 | 2  # BGUI_CENTERED = BGUI_CENTERX | BGUI_CENTERY

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QColorDialog, QComboBox, QDialog,
                               QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMenu, QMessageBox, QPlainTextEdit, QPushButton,
                               QSplitter, QSpinBox, QTabWidget, QToolBar, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget, QScrollArea)

from GUI.sub_logi.editeur_ui import theme_bgui as bgui_theme
from GUI.sub_logi.editeur_ui.canvas import CanvasBGUI
from GUI.sub_logi.editeur_ui.generateur_script import sauvegarder_script
from GUI.sub_logi.editeur_ui.syntaxe_cfg import SyntaxeCfgCfg
from GUI.sub_logi.editeur_ui.theme_bgui import (THEME_BGUI, THEME_BGUI_DEFAUT, appliquer_theme,
                                                charger_theme_fichier, definir_base_projet, lire_cfg_texte,
                                                proprietes_depuis_donnees, reinitialiser_theme,
                                                resoudre_proprietes, sauvegarder_theme_fichier,
                                                sous_themes_disponibles, theme_defaut_en_texte,
                                                taille_label, valeur_rendu)
from GUI.sub_logi.editeur_ui.modele import (CALQUE_BASE, CATALOGUE, CHAMPS_DEDIES,
                                            DECLENCHEURS_EVENEMENTS, OPTIONS_PAR_TYPE,
                                            TYPE_BARRE_PROGRES, TYPE_BLOC_TEXTE, TYPE_BOUTON_IMAGE,
                                            TYPE_FRAME_BOUTON, TYPE_FRAME, TYPE_IMAGE,
                                            TYPE_LABEL, TYPE_LISTE, TYPE_SAISIE_TEXTE,
                                            TYPE_SCREEN, TYPE_VIDEO, TYPES_PROPRIETE,
                                            NoeudUI, ajouter_calque, calque_de,
                                            calques_ecran, description_type_propriete,
                                            enfants_calque, libelle_type_propriete,
                                            nouveau_noeud, prochain_nom, renommer_calque,
                                            retirer_calque, sauvegarder_fichier,
                                            charger_fichier, scene_vide, px_vers_normalise,
                                            reparenter, valeur_defaut_propriete,
                                            valeur_depuis_texte, valeur_typee_propriete)

#: Types de widgets proposés à l'ajout (barre d'outils + menus contextuels).
#: `(Type, Libellé de création)`.
TYPES_AJOUTABLES = [
    (TYPE_LABEL, "Label"),
    (TYPE_FRAME_BOUTON, "Bouton"),
    (TYPE_FRAME, "Cadre"),
    (TYPE_IMAGE, "Image"),
    (TYPE_BOUTON_IMAGE, "ImageButton"),
    (TYPE_LISTE, "ListBox"),
    (TYPE_BARRE_PROGRES, "ProgressBar"),
    (TYPE_BLOC_TEXTE, "TextBlock"),
    (TYPE_SAISIE_TEXTE, "TextInput"),
]


class ProprietesSource:
    """Cible d'édition des propriétés nom/valeur.

    Porte la liste à éditer et les deux rappels :
    - ``maj``   : léger, après chaque édition d'une valeur (redessin...) ;
    - ``apres`` : après ajout/suppression (reconstruit la zone).
    """

    def __init__(self, liste, maj=None, apres=None, proprietaire="cet écran"):
        self.liste = liste
        self.maj = maj or (lambda: None)
        self.apres = apres or self.maj
        self.proprietaire = proprietaire


_MARQUEUR_CALQUE = "calque"


class ArbreWidgets(QTreeWidget):
    """Arbre des widgets avec glisser-déposer entre calques.

    Déposer un enfant direct du Screen sur un dossier « Calque : … »
    change son calque d'appartenance (l'affichage du widget).
    """

    def __init__(self, editeur):
        super().__init__()
        self._editeur = editeur
        self._source_glissee = None
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)

    def startDrag(self, actions):
        self._source_glissee = self.currentItem()
        super().startDrag(actions)

    def dragEnterEvent(self, event):
        """Refuse les dépôts de fichiers externes.

        Ils remontent ainsi à la fenêtre principale qui les ouvre dans leur
        éditeur respectif ; seuls les glisser-déposer internes sont gardés.
        """
        if event.mimeData().hasUrls():
            event.ignore()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        editeur = self._editeur
        source = self._source_glissee
        self._source_glissee = None
        cible = self.itemAt(event.position().toPoint())
        if cible is None or source is None:
            event.ignore()
            return
        cible_data = cible.data(0, Qt.UserRole)
        if not (isinstance(cible_data, tuple) and cible_data[0] == _MARQUEUR_CALQUE):
            event.ignore()
            return
        noeud = source.data(0, Qt.UserRole)
        if noeud is None or not isinstance(noeud, NoeudUI):
            event.ignore()
            return
        if noeud.type == TYPE_SCREEN:
            event.ignore()
            return
        if editeur.canvas.parent_de(editeur.scene, noeud) is not editeur.scene:
            event.ignore()
            return
        calque = cible_data[1]
        if calque_de(noeud) == calque:
            event.accept()
            return
        noeud.prop["calque"] = calque
        editeur.canvas.rafraichir()
        editeur.rafraichir_arbre()
        event.accept()


class EditeurThemeDepot(QPlainTextEdit):
    """Éditeur de thème acceptant les dépôts de fichiers.

    Un dépôt de fichier (``.cfg``) est refusé ici pour remonter jusqu'à la
    fenêtre principale, qui l'ouvre dans l'éditeur de thème ; le dépôt de
    texte garde le comportement standard.
    """

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.ignore()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.ignore()
            return
        super().dropEvent(event)


class LoposUIeditor(QMainWindow):
    """Éditeur de conception d'interface BGUI (simulation type Godot).

    Trois zones autour du canvas de simulation :
    - à gauche  : l'outliner (arborescence des widgets)
    - au centre : l'écran simulé (rendu BGUI, clic/drag/resize)
    - à droite  : l'inspecteur de propriétés du widget sélectionné
    """

    def __init__(self, titre="LPS UI éditeur", largeur=1400, hauteur=900):
        super().__init__()
        self.setWindowTitle(titre)

        moniteur = QGuiApplication.primaryScreen()
        taille_moniteur = moniteur.size()
        calcul_l = (taille_moniteur.width() * 0.5) - (largeur * 0.5)
        calcul_h = (taille_moniteur.height() * 0.5) - (hauteur * 0.5)
        self.setGeometry(int(calcul_l), int(calcul_h), largeur, hauteur)

        self.scene = scene_vide()
        self.chemin_projet = None
        self._verrou_arbre = False
        self._noeud_vers_item = {}
        self.champ = {}                     # champs de l'inspecteur en cours
        self.setAcceptDrops(True)
        self._initialiser_interface()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _initialiser_interface(self):
        self.creer_barre_outils()

        self.canvas = CanvasBGUI()
        self.canvas.definir_scene(self.scene)
        self.canvas.selection_changee.connect(self._selection_changee)
        self.canvas.geo_changee.connect(self._geo_changee)
        self.canvas.souris_changee.connect(self._survol)
        self.canvas.modele_change.connect(self.rafraichir_calques)
        self.canvas.menu_demande.connect(self._menu_contextuel_canvas)

        self.onglets = QTabWidget()
        self.onglets.addTab(self.creer_onglet_ui(), "UI")
        self.onglets.addTab(self.creer_onglet_code(), "CODE")
        self.setCentralWidget(self.onglets)

        self.barre_status()
        self.rafraichir_arbre()
        self.initialiser_theme_generer()

    # ------------------------------------------------------------------
    # Glisser-déposer de fichiers (projet JSON / thème *.cfg)
    # ------------------------------------------------------------------

    #: Extension des fichiers ouverts au dépôt, vers l'onglet cible.
    FICHIERS_DEPOSES = {".json": "projet", ".cfg": "theme"}

    def dragEnterEvent(self, event):
        """Accepte le dépôt si l'un des fichiers est un projet ou un thème."""
        if self._fichiers_deposes(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Ouvre les fichiers déposés dans leur éditeur respectif."""
        for chemin in self._fichiers_deposes(event):
            try:
                self._ouvrir_fichier_depose(chemin)
            except Exception as e:
                self.statusBar().showMessage(
                    f"Impossible d'ouvrir {chemin}: {e}", 6000)
        event.acceptProposedAction()

    def _fichiers_deposes(self, event):
        """Chemins locaux des fichiers déposés dont l'extension est connue."""
        if not event.mimeData().hasUrls():
            return []
        acceptable = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            chemin = url.toLocalFile()
            if (os.path.isfile(chemin)
                    and os.path.splitext(chemin)[1].lower()
                    in self.FICHIERS_DEPOSES):
                acceptable.append(chemin)
        return acceptable

    def _ouvrir_fichier_depose(self, chemin):
        """Route un fichier déposé vers l'éditeur adapté, onglet ouvert."""
        cible = self.FICHIERS_DEPOSES.get(
            os.path.splitext(chemin)[1].lower())
        if cible == "projet":
            self._ouvrir_projet(chemin)
            self.onglets.setCurrentIndex(0)
        elif cible == "theme":
            self._ouvrir_theme(chemin)
            self.onglets.setCurrentIndex(1)

    def creer_onglet_ui(self):
        outliner = self.creer_outliner()
        inspecteur = self.creer_inspecteur()

        separateur = QSplitter(Qt.Horizontal)
        separateur.addWidget(outliner)
        separateur.addWidget(self._zone_canvas())
        separateur.addWidget(inspecteur)
        separateur.setStretchFactor(0, 1)
        separateur.setStretchFactor(1, 4)
        separateur.setStretchFactor(2, 1)
        separateur.setSizes([270, 680, 260])
        return separateur

    def _zone_canvas(self):
        """Canvas précédé d'une barre de choix du calque affiché."""
        zone = QWidget()
        calque = QWidget()
        barre = QHBoxLayout(calque)
        barre.setContentsMargins(6, 4, 6, 2)
        barre.addWidget(QLabel("Calque :"))
        self.combo_calque = QComboBox()
        self.combo_calque.setMinimumWidth(160)
        self.combo_calque.currentIndexChanged.connect(self._changer_calque)
        barre.addWidget(self.combo_calque)
        barre.addStretch(1)
        disposition = QVBoxLayout(zone)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(0)
        disposition.addWidget(calque)
        disposition.addWidget(self.canvas, 1)
        return zone

    def creer_onglet_code(self):
        """Onglet « CODE » : base du projet, thème BGUI et propriétés.

        Permet de choisir le dossier de base du projet (utilisé pour résoudre
        les chemins ``//`` et pour localiser le fichier de thème), d'éditer
        une version générée du thème et de définir des propriétés
        nom/valeur au format de theme.cfg (ou en str()).

        Le fichier ``<base>/Scripts/theme.cfg`` n'est pas chargé au départ :
        on part d'une version générée (codée en dur) puisque le fichier est
        à créer. Il peut ensuite être ouvert ou enregistré (« Ouvrir » /
        « Enregistrer sous »).
        """
        self.chemin_theme = None
        onglet = QWidget()
        disposition = QVBoxLayout(onglet)
        disposition.setContentsMargins(4, 4, 4, 4)

        # --- Dossier de base du projet --------------------------------
        barre_base = QHBoxLayout()
        barre_base.addWidget(QLabel("<b>Source projet :</b>"))
        self.edt_base_projet = QLineEdit(bgui_theme.CHEMIN_BASE_PROJET)
        self.edt_base_projet.setReadOnly(True)
        self.edt_base_projet.setToolTip(
            "Dossier de base du projet. Il sert à résoudre les chemins "
            "relatifs « // » des images/vidéos et à localiser le fichier de "
            "thème (<base>/Scripts/theme.cfg).")
        barre_base.addWidget(self.edt_base_projet, 1)
        b_base = QPushButton("Parcourir…")
        b_base.setToolTip("Choisir le dossier de base du projet")
        b_base.clicked.connect(self._choisir_base_projet)
        barre_base.addWidget(b_base)
        disposition.addLayout(barre_base)

        # --- Éditeur du thème -----------------------------------------
        barre = QHBoxLayout()
        self.lbl_theme = QLabel(self.chemin_theme or "généré (non enregistré)")
        self.lbl_theme.setToolTip(
            "Fichier de thème chargé dans l'éditeur. Le rendu de l'onglet "
            "« UI » utilise ses valeurs.")
        barre.addWidget(self.lbl_theme, 1)

        b_ouvrir = QPushButton("Ouvrir")
        b_ouvrir.clicked.connect(self.ouvrir_theme)
        barre.addWidget(b_ouvrir)
        b_save = QPushButton("Enregistrer")
        b_save.clicked.connect(self.enregistrer_theme)
        barre.addWidget(b_save)
        b_save_sous = QPushButton("Enregistrer sous")
        b_save_sous.setToolTip("Sauvegarder le thème sous un autre nom")
        b_save_sous.clicked.connect(self.enregistrer_theme_sous)
        barre.addWidget(b_save_sous)
        b_appliquer = QPushButton("Appliquer")
        b_appliquer.clicked.connect(self.appliquer_theme_editeur)
        barre.addWidget(b_appliquer)
        b_defaut = QPushButton("Défaut")
        b_defaut.setToolTip("Revenir aux valeurs de thème par défaut intégrées")
        b_defaut.clicked.connect(self.reinitialiser_theme_editeur)
        barre.addWidget(b_defaut)
        disposition.addLayout(barre)

        # --- Éditeur + propriétés du projet côte à côte ---------------
        self.proprietes_projet = []     # listes {nom, type, valeur}
        corps = QHBoxLayout()
        disposition.addLayout(corps, 1)

        self.texte_theme = EditeurThemeDepot()
        self.texte_theme.setFont(QFont("monospace"))
        self.texte_theme.setStyleSheet(
            "QPlainTextEdit { background-color: #1e1e1e; color: #e6e6e6;"
            " border: 1px solid #3e3e3e; }")
        self.texte_theme.setToolTip(
            "Format BGUI : sections [Widget] et clés Nom=valeur.\n"
            "Couleurs : r, g, b, a (0..1) · entiers, booléens, tuples image.\n"
            "Une valeur peut référencer une propriété : prop.<nom>.")
        self.syntaxe_theme = SyntaxeCfgCfg(self.texte_theme.document())
        corps.addWidget(self.texte_theme, 7)

        panneau_code = QWidget()
        disposition_panneau = QVBoxLayout(panneau_code)
        disposition_panneau.setContentsMargins(0, 0, 0, 0)
        disposition_panneau.addWidget(QLabel(
            "<b>Propriétés du projet</b> "
            "<span style='color:#8a8a8a;'>(fichier theme.cfg)</span>"))
        aide_prop = QLabel(
            "Utilisables dans theme.cfg avec "
            "<span style='color:#c9a227;'>prop.nom</span>\n"
            "pour en récupérer la valeur typée.")
        aide_prop.setWordWrap(True)
        aide_prop.setStyleSheet("color:#8a8a8a;")
        disposition_panneau.addWidget(aide_prop)

        zone_defil = QScrollArea()
        zone_defil.setWidgetResizable(True)
        interieur = QWidget()
        self.form_code_prop = QGridLayout(interieur)
        self.form_code_prop.setContentsMargins(2, 2, 2, 2)
        self.form_code_prop.setColumnStretch(1, 1)
        zone_defil.setWidget(interieur)
        disposition_panneau.addWidget(zone_defil, 1)

        self.source_code = ProprietesSource(
            self.proprietes_projet,
            maj=lambda: None,
            apres=self._reconstruire_code_proprietes,
            proprietaire="le projet (theme.cfg)")
        self._ligne_prop_code = 0
        disposition_panneau.addWidget(QLabel(
            "Sélectionnez « + Properties » pour définir une propriété.\n"
            "Les types acceptés sont ceux de l'écran (float(), int(), str(),\n"
            "bool(), vecteurs, enum(), RGBA, tuple image, objet bpy.*)."))
        corps.addWidget(panneau_code, 3)
        return onglet

    # ------------------------------------------------------------------
    # Onglet CODE : gestion du thème
    # ------------------------------------------------------------------

    def lire_theme_editeur(self):
        """Analyse le texte de l'éditeur de thème ; None si invalide."""
        try:
            return lire_cfg_texte(self.texte_theme.toPlainText())
        except Exception:
            return None

    @Slot()
    def appliquer_theme_editeur(self):
        """Analyse le texte puis l'applique au rendu.

        Les propriétés du panneau sont la source de vérité : elles ne sont
        jamais réécrites dans le texte (aucune section `[Properties]` n'est
        générée — on référence directement ``prop.<nom>``). La résolution se
        fait depuis le panneau au moment de l'application.
        """
        donnees = self.lire_theme_editeur()
        if donnees is None:
            self.statusBar().showMessage(
                "Thème invalide : le texte n'a pas pu être analysé", 4000)
            return
        appliquer_theme(resoudre_proprietes(donnees, self.proprietes_projet))
        self.canvas.rafraichir()
        n = len(self.proprietes_projet)
        self.statusBar().showMessage(
            f"Thème appliqué au rendu (propriétés : {n} · prop.nom résolus)",
            4000)

    @Slot()
    def ouvrir_theme(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un thème BGUI", "",
            "Fichier de thème (*.cfg);;Tous les fichiers (*)")
        if not chemin:
            return
        self._ouvrir_theme(chemin)

    def _ouvrir_theme(self, chemin):
        """Charge un fichier de thème dans l'éditeur (dialogue ou dépôt)."""
        self.chemin_theme = chemin
        self.lbl_theme.setText(chemin)
        self.charger_theme_dans_editeur(chemin)
        self.statusBar().showMessage(f"Thème chargé: {chemin}", 4000)

    @Slot()
    def enregistrer_theme(self):
        if self.chemin_theme is None:
            self.enregistrer_theme_sous()
            return
        self._ecrire_theme(self.chemin_theme)

    @Slot()
    def enregistrer_theme_sous(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le thème sous",
            self.chemin_theme or "theme.cfg",
            "Fichier de thème (*.cfg)")
        if not chemin:
            return
        self.chemin_theme = chemin
        self.lbl_theme.setText(chemin)
        self._ecrire_theme(chemin)
        self.charger_theme_dans_editeur(self.chemin_theme)

    def _ecrire_theme(self, chemin):
        """Sauvegarde le texte de l'éditeur tel quel (aucune section générée).

        Les références ``prop.<nom>`` sont conservées telles quelles : les
        valeurs vivent dans le panneau « Propriétés » du projet, pas dans le
        fichier de thème."""
        try:
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(self.texte_theme.toPlainText())
        except OSError as e:
            self.statusBar().showMessage(f"Impossible d'écrire le thème: {e}", 4000)
            return
        self.statusBar().showMessage(f"Thème enregistré: {chemin}", 4000)

    @Slot()
    def reinitialiser_theme_editeur(self):
        self.initialiser_theme_generer()
        self.statusBar().showMessage(
            "Thème réinitialisé aux valeurs par défaut intégrées", 4000)

    def initialiser_theme_generer(self):
        """Base de l'éditeur : version générée (codée en dur), sans fichier.

        Le fichier de thème étant à créer par l'utilisateur, on ne lit aucun
        fichier à l'ouverture : on part toujours d'une version générée.
        Un fichier existant peut ensuite être ouvert via « Ouvrir ».
        """
        reinitialiser_theme()
        self.texte_theme.setPlainText(theme_defaut_en_texte())
        self.proprietes_projet = []
        self._reconstruire_code_proprietes()
        self.canvas.rafraichir()

    def charger_theme_dans_editeur(self, chemin=None):
        """Charge le theme.cfg par défaut dans l'éditeur (à l'ouverture)."""
        chemin = chemin or self.chemin_theme
        try:
            charger_theme_fichier(chemin)
        except OSError as e:
            self.statusBar().showMessage(
                f"Thème par défaut introuvable: {e}", 6000)
            return
        self.texte_theme.setPlainText(
            open(chemin, encoding="utf-8").read())
        self.proprietes_projet = proprietes_depuis_donnees(
            lire_cfg_texte(self.texte_theme.toPlainText()))
        self._reconstruire_code_proprietes()
        self.canvas.rafraichir()

    @Slot()
    def _choisir_base_projet(self):
        """Choisit le dossier de base du projet (résolution des chemins //)."""
        depart = bgui_theme.CHEMIN_BASE_PROJET or os.getcwd()
        dossier = QFileDialog.getExistingDirectory(
            self, "Dossier de base du projet", depart)
        if not dossier:
            return
        definir_base_projet(dossier)
        self.edt_base_projet.setText(bgui_theme.CHEMIN_BASE_PROJET)
        self.canvas.def_base_projet(bgui_theme.CHEMIN_BASE_PROJET)
        self.canvas.rafraichir()
        self.statusBar().showMessage(
            f"Base du projet: {bgui_theme.CHEMIN_BASE_PROJET}", 4000)

    def lire_proprietes_projet(self):
        """Renvoie le dict {nom: valeur} des propriétés du tableau.

        Les valeurs sont analysées comme dans theme.cfg (booléens, entiers,
        flottants, couleurs, tuples image) puis, à défaut, lues en texte.
        """
        return {p["nom"]: valeur_typee_propriete(p)
                for p in self.proprietes_projet if p.get("nom")}

    def _ligne_suivante_code(self):
        """Ligne courante du panneau « Propriétés » de l'onglet CODE."""
        ligne = self._ligne_prop_code
        self._ligne_prop_code += 1
        return ligne

    def _reconstruire_code_proprietes(self):
        """Reconstruit le panneau « Propriétés » depuis proprietes_projet."""
        self.source_code.liste = self.proprietes_projet
        while self.form_code_prop.count():
            item = self.form_code_prop.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._ligne_prop_code = 0
        self._champ_proprietes(self.source_code, self.form_code_prop,
                               self._ligne_suivante_code)

    def creer_barre_outils(self):
        self.tool_barre = QToolBar("barre d'outil UI")
        self.tool_barre.setMovable(False)
        self.addToolBar(self.tool_barre)

        self.tool_barre.addWidget(QLabel("Écran: "))
        self.spin_largeur = QSpinBox()
        self.spin_largeur.setRange(1, 3840)
        self.spin_largeur.setValue(1280)
        self.spin_largeur.setSuffix("px")
        self.spin_largeur.valueChanged.connect(self._maj_ecran)
        self.tool_barre.addWidget(self.spin_largeur)
        self.tool_barre.addWidget(QLabel(" x "))
        self.spin_hauteur = QSpinBox()
        self.spin_hauteur.setRange(1, 3840)
        self.spin_hauteur.setValue(720)
        self.spin_hauteur.setSuffix("px")
        self.spin_hauteur.valueChanged.connect(self._maj_ecran)
        self.tool_barre.addWidget(self.spin_hauteur)
        self.tool_barre.addSeparator()

        b_ouvrir = QPushButton("Ouvrir")
        b_ouvrir.clicked.connect(self.open_projet)
        self.tool_barre.addWidget(b_ouvrir)
        b_save = QPushButton("Enregistrer")
        b_save.clicked.connect(self.save_projet)
        self.tool_barre.addWidget(b_save)
        b_save_sous = QPushButton("Enregistrer sous")
        b_save_sous.setToolTip("Sauvegarder le projet sous un autre nom")
        b_save_sous.clicked.connect(self.save_projet_sous)
        self.tool_barre.addWidget(b_save_sous)
        b_gen = QPushButton("Générer code")
        b_gen.clicked.connect(self.generer_fichier)
        self.tool_barre.addWidget(b_gen)
        self.tool_barre.addSeparator()

        b_nouveau = QPushButton("Nouveau fichier")
        b_nouveau.setToolTip("Créer une nouvelle interface vierge")
        b_nouveau.clicked.connect(self.nouveau_projet)
        self.tool_barre.addWidget(b_nouveau)
        b_quitter = QPushButton("Quitter")
        b_quitter.setToolTip("Quitter l'éditeur UI")
        b_quitter.clicked.connect(self.quitter)
        self.tool_barre.addWidget(b_quitter)

    def creer_outliner(self):
        boite = QWidget()
        disposition = QVBoxLayout(boite)
        disposition.setContentsMargins(4, 4, 4, 4)
        disposition.addWidget(QLabel("Outliner"))
        grille = QGridLayout()
        for i, (type_w, libelle) in enumerate(TYPES_AJOUTABLES):
            bouton = QPushButton(f"+ {libelle}")
            bouton.clicked.connect(
                lambda _, t=type_w: self.ajouter_widget_sous(self.scene, t))
            grille.addWidget(bouton, i // 2, i % 2)
        disposition.addLayout(grille)
        self.arbre = ArbreWidgets(self)
        # Une seule colonne : le nom occupe toute la largeur du panneau
        # (avec deux colonnes, la 1re était figée à 100 px et les noms
        # longs étaient tronqués par « … »).
        self.arbre.setColumnCount(1)
        self.arbre.setHeaderHidden(True)
        self.arbre.itemClicked.connect(self._arbre_clic)
        self.arbre.setContextMenuPolicy(Qt.CustomContextMenu)
        self.arbre.customContextMenuRequested.connect(
            self._menu_contextuel_outliner)
        disposition.addWidget(self.arbre)
        return boite

    def creer_inspecteur(self):
        boite = QWidget()
        disposition = QVBoxLayout(boite)
        disposition.setContentsMargins(4, 4, 4, 4)
        disposition.addWidget(QLabel("Inspecteur"))

        defile = QScrollArea()
        defile.setWidgetResizable(True)
        self.zone_inspe = QWidget()
        self.form_inspe = QGridLayout(self.zone_inspe)
        self.form_inspe.setContentsMargins(4, 4, 4, 4)
        defile.setWidget(self.zone_inspe)
        disposition.addWidget(defile)
        return boite

    def barre_status(self):
        self.StatuBarre = self.statusBar()
        self.lbl_selection = QLabel("aucun widget sélectionné")
        self.StatuBarre.addPermanentWidget(self.lbl_selection)

    # ------------------------------------------------------------------
    # Outliner (arborescence)
    # ------------------------------------------------------------------

    def rafraichir_arbre(self):
        self._verrou_arbre = True
        self.arbre.clear()
        self._noeud_vers_item = {}
        if self.scene is not None:
            self._inserer_item_arbre(self.scene, None)
        selection = self.canvas.selection_actuelle()
        item = self._noeud_vers_item.get(id(selection))
        if item is not None:
            self.arbre.setCurrentItem(item)
            self.arbre.scrollToItem(item)
        # L'outliner reste toujours déplié : une reconstruction le replierait.
        self.arbre.expandAll()
        self._verrou_arbre = False
        self.rafraichir_calques()

    def _inserer_item_arbre(self, noeud, parent_item):
        libelle = f"{noeud.nom} ({noeud.type})"
        item = QTreeWidgetItem([libelle])
        item.setData(0, Qt.UserRole, noeud)
        item.setToolTip(0, libelle)
        if parent_item is not None:
            parent_item.addChild(item)
        else:
            self.arbre.addTopLevelItem(item)
        self._noeud_vers_item[id(noeud)] = item
        if noeud.type == TYPE_SCREEN:
            # Les enfants directs du Screen sont groupés par calque.
            base = calques_ecran(noeud)[0]
            for nom_calque in calques_ecran(noeud):
                dossier = QTreeWidgetItem([f"Calque : {nom_calque}"])
                dossier.setData(0, Qt.UserRole, (_MARQUEUR_CALQUE, nom_calque))
                item.addChild(dossier)
                for enfant in noeud.enfants:
                    if enfant.prop.get("calque", base) == nom_calque:
                        self._inserer_item_arbre(enfant, dossier)
        else:
            for enfant in noeud.enfants:
                self._inserer_item_arbre(enfant, item)

    def rafraichir_calques(self):
        """Re-synchronise la liste du combobox avec les calques du Screen."""
        if not hasattr(self, "combo_calque") or self.scene is None:
            return
        noms = calques_ecran(self.scene)
        actif = self.canvas.calque_actif
        if actif not in noms:
            actif = noms[0]
            self.canvas.calque_actif = actif
        self.combo_calque.blockSignals(True)
        self.combo_calque.clear()
        self.combo_calque.addItems(noms)
        self.combo_calque.setCurrentText(actif)
        self.combo_calque.blockSignals(False)

    @Slot(int)
    def _changer_calque(self, _indice):
        self.definir_calque_actif(self.combo_calque.currentText())

    def definir_calque_actif(self, nom):
        """Affiche le calque nommé (canvas + combobox).

        Ne reconstruit pas l'arbre : la sélection en cours (un dossier
        « Calque : x », qui désigne la cible des nouveaux widgets) est
        conservée.
        """
        if nom and self.canvas.set_calque_actif(nom):
            self.rafraichir_calques()

    @Slot()
    def _arbre_clic(self, item, colonne):
        if self._verrou_arbre:
            return
        donnee = item.data(0, Qt.UserRole)
        if isinstance(donnee, tuple) and donnee[0] == _MARQUEUR_CALQUE:
            # Cliquer sur un dossier « Calque : x » le rend actif : le
            # canvas l'affiche et les nouveaux widgets y sont ajoutés.
            self.definir_calque_actif(donnee[1])
            return
        self.canvas.definir_selection(donnee)

    @Slot(object, object)
    def _menu_contextuel_canvas(self, noeud, pos_globale):
        # Clic droit sur le canvas : cible le widget sous le curseur,
        # sinon l'écran (celui-ci est re-sélectionné par le canvas).
        self._ouvrir_menu_contextuel(noeud, pos_globale)

    @Slot(object)
    def _menu_contextuel_outliner(self, pos):
        item = self.arbre.itemAt(pos)
        if item is None:
            return
        donnee = item.data(0, Qt.UserRole)
        if isinstance(donnee, tuple) and donnee[0] == _MARQUEUR_CALQUE:
            noeud = self.scene
        else:
            noeud = donnee
        if noeud is None:
            return
        self.arbre.setCurrentItem(item)
        self.canvas.definir_selection(noeud)
        self._ouvrir_menu_contextuel(
            noeud, self.arbre.viewport().mapToGlobal(pos))

    def _ouvrir_menu_contextuel(self, noeud, pos_globale):
        """Ouvre le menu contextuel pour le nœud ciblé à l'écran.

        Propose « Ajouter un enfant » pour tout nœud (tous les widgets
        acceptent des enfants) ainsi que la suppression pour un widget.
        """
        if noeud is None:
            noeud = self.scene
        if noeud is None:
            return
        menu = QMenu(self)
        titre = menu.addAction(f"{noeud.nom}")
        titre.setEnabled(False)
        menu.addSeparator()
        sous = menu.addMenu("Ajouter un enfant")
        for type_w, libelle in TYPES_AJOUTABLES:
            action = sous.addAction(libelle)
            action.triggered.connect(
                lambda _=False, t=type_w, p=noeud:
                self.ajouter_widget_sous(p, t))
        if noeud.type != TYPE_SCREEN:
            menu.addSeparator()
            act_suppr = menu.addAction("Supprimer")
            act_suppr.triggered.connect(self.supprimer_selection)
        menu.exec(pos_globale)

    @Slot(object)
    def _selection_changee(self, noeud):
        self._verrou_arbre = True
        item = self._noeud_vers_item.get(id(noeud))
        if item is not None:
            self.arbre.setCurrentItem(item)
            self.arbre.scrollToItem(item)
        self._verrou_arbre = False
        self.rafraichir_inspecteur()
        self._maj_status()

    # ------------------------------------------------------------------
    # Ajout / suppression de widgets
    # ------------------------------------------------------------------

    def ajouter_widget_sous(self, domaine, type_w):
        """Crée un widget du type donné et le rattache sous ``domaine``.

        ``domaine`` peut être n'importe quel widget (tout type reçoit des
        enfants) ou le Screen. Si le parent est le Screen, le nouveau widget
        entre dans le calque actif.
        """
        if domaine is None or self.scene is None:
            return
        noeud = nouveau_noeud(type_w, prochain_nom(self.scene, type_w))
        taille = CATALOGUE.get(type_w, {}).get("taille", [0.2, 0.1])
        noeud.prop["pos"] = [0.1, 0.1]
        noeud.prop["size"] = list(taille)
        if domaine is self.scene:
            # Toute création directement sous le Screen entre dans le calque
            # actif (celui du combobox ou du dossier sélectionné).
            noeud.prop["calque"] = self.canvas.calque_actif
        domaine.enfants.append(noeud)
        noeud.parent = domaine

        self.canvas.rafraichir()
        self.rafraichir_arbre()
        self.canvas.definir_selection(noeud)
        self.statusBar().showMessage(
            f"Widget « {noeud.nom} » ({type_w}) ajouté sous {domaine.nom}", 4000)

    def supprimer_selection(self):
        noeud = self.canvas.selection_actuelle()
        if noeud is None or noeud.type == TYPE_SCREEN:
            return
        parent = self.canvas.parent_de(self.scene, noeud)
        if parent is None:
            return
        parent.enfants.remove(noeud)
        noeud.parent = None
        self.canvas.definir_selection(parent)
        self.canvas.rafraichir()
        self.rafraichir_arbre()
        self.statusBar().showMessage(f"Widget « {noeud.nom} » supprimé", 4000)

    # ------------------------------------------------------------------
    # Inspecteur de propriétés
    # ------------------------------------------------------------------

    def _vider_inspecteur(self):
        while self.form_inspe.count():
            item = self.form_inspe.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self.champ = {}
        self._ligne = 0

    def _ligne_suivante(self):
        """Renvoie la ligne courante du formulaire puis l'incrémente."""
        ligne = self._ligne
        self._ligne += 1
        return ligne

    def rafraichir_inspecteur(self):
        self._vider_inspecteur()
        noeud = self.canvas.selection_actuelle()
        if noeud is None:
            self.form_inspe.addWidget(
                QLabel("Sélectionnez un widget\ndans l'outliner ou sur l'écran."),
                0, 0)
            return

        parent_px = self.canvas.rect_parent_scene(noeud)
        p_l, p_h = parent_px.width(), parent_px.height()
        pos = noeud.prop.get("pos", [0.0, 0.0])
        size = noeud.prop.get("size", [1.0, 1.0])

        self.form_inspe.addWidget(
            QLabel(f"<b>{noeud.nom}</b> <i>({noeud.type})</i>"),
            self._ligne_suivante(), 0, 1, 3)

        self.champ_nom = QLineEdit(noeud.nom)
        self.champ_nom.textChanged.connect(
            lambda t, n=noeud: self._renommer(n, t))
        self.form_inspe.addWidget(QLabel("Nom"), self._ligne_suivante(), 0)
        self.form_inspe.addWidget(self.champ_nom, self._ligne - 1, 1, 1, 2)

        self.champ["px"] = self._spin(pos[0], p_l, 0.0, p_l,
                                      lambda v: self._modifier_prop(noeud, "pos", 0, v, p_l))
        self.champ["py"] = self._spin(pos[1], p_h, 0.0, p_h,
                                      lambda v: self._modifier_prop(noeud, "pos", 1, v, p_h))
        if noeud.type == TYPE_LABEL:
            # Le Label BGUI calcule sa taille depuis le texte + pt_size :
            # le size stocké ne sert à rien, on affiche la taille réelle
            # (calculée) sans permettre de la modifier à la main.
            w_px, h_px = taille_label(noeud, parent_px)
            self.champ["pw"] = self._spin(w_px / (p_l or 1.0), p_l, 1.0, p_l,
                                          lambda v: None)
            self.champ["ph"] = self._spin(h_px / (p_h or 1.0), p_h, 1.0, p_h,
                                          lambda v: None)
            self.champ["pw"].setEnabled(False)
            self.champ["ph"].setEnabled(False)
            self.champ["pw"].setToolTip(
                "Taille calculée depuis le texte et la police (pt) : "
                "le redimensionnement direct n'a pas d'effet sur un Label.")
            self.champ["ph"].setToolTip(
                self.champ["pw"].toolTip())
        else:
            self.champ["pw"] = self._spin(size[0], p_l, 1.0, p_l,
                                          lambda v: self._modifier_prop(noeud, "size", 0, v, p_l))
            self.champ["ph"] = self._spin(size[1], p_h, 1.0, p_h,
                                          lambda v: self._modifier_prop(noeud, "size", 1, v, p_h))
        ligne_geo = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Position"), ligne_geo, 0)
        self.form_inspe.addWidget(self.champ["px"], ligne_geo, 1)
        self.form_inspe.addWidget(self.champ["py"], ligne_geo, 2)
        ligne_geo = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Taille"), ligne_geo, 0)
        self.form_inspe.addWidget(self.champ["pw"], ligne_geo, 1)
        self.form_inspe.addWidget(self.champ["ph"], ligne_geo, 2)

        if noeud.type == TYPE_SCREEN:
            self._champ_calques(noeud)
            self._champ_resolution(noeud)
            self._champ_couleur(noeud, "color", "Couleur de fond")
            self.source_inspe = ProprietesSource(
                noeud.proprietes,
                maj=lambda: self.canvas.update(),
                apres=(lambda n=noeud: (
                    self.canvas.rafraichir(), self.rafraichir_inspecteur(),
                    self._maj_status())),
                proprietaire="cet écran")
            self._champ_proprietes(self.source_inspe, self.form_inspe,
                                   self._ligne_suivante)
            self._champ_visible(noeud)
            return

        # --- Section « Code » : propriétés du widget (non liées au thème) ---
        self._en_tete_section("Code")
        self._champ_parent(noeud)
        self._champs_code(noeud)
        self._champ_options(noeud)
        self._champ_visible(noeud)

        # --- Section « Thème » : sous-thème + couleurs résolues du thème ---
        self._en_tete_section("Thème")
        self._champ_sub_theme(noeud)
        self._champs_couleurs(noeud)

        # --- Section « Fonctions » : déclencheurs d'événements (Godot) ---
        self._champ_fonctions(noeud)

        # --- Section « Mise à jour » : code exécuté à chaque frame ---
        self._champ_mise_a_jour(noeud)

        b_suppr = QPushButton("Supprimer")
        b_suppr.clicked.connect(self.supprimer_selection)
        self.form_inspe.addWidget(b_suppr, self._ligne_suivante(), 0, 1, 3)

    def _en_tete_section(self, libelle):
        """En-tête d'une section de l'inspecteur (Code, Thème...)."""
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel(f"<b>{libelle}</b>"), ligne, 0, 1, 3)

    def _champ_parent(self, noeud):
        """Sélecteur du parent d'un widget (tout type peut être parent).

        Le déplacement se fait via :func:`modele.reparenter` : si le nouveau
        parent est le Screen, le widget est rattaché au calque actif ; sinon
        la clé ``calque`` est retirée (seuls les enfants directs d'un Screen
        sont regroupés par calque).
        """
        if noeud.type == TYPE_SCREEN:
            return
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Parent"), ligne, 0)

        interdits = set()

        def marquer(n):
            interdits.add(id(n))
            for e in n.enfants:
                marquer(e)
        marquer(noeud)   # soi + descendants (interdit : créer un cycle)

        candidats = []

        def parcourir(n, prof):
            if id(n) not in interdits:
                candidats.append(("  " * prof, n, f"  {n.nom} ({n.type})"))
            for e in n.enfants:
                parcourir(e, prof + 1)
        parcourir(self.scene, 0)

        combo = QComboBox()
        parent_actuel = noeud.parent
        index_courant = -1
        for i, (indent, n, _) in enumerate(candidats):
            combo.addItem(indent + n.nom, n)
            if n is parent_actuel:
                index_courant = i
        if index_courant < 0:
            combo.insertItem(0, "", None)
            index_courant = 0
        combo.setCurrentIndex(index_courant)
        combo.setToolTip(
            "Choisir le widget parent de cet élément.\n"
            "Tout type de widget peut recevoir des enfants.")

        def changer(index):
            cible = combo.itemData(index)
            if cible is None or cible is noeud or cible is parent_actuel:
                return
            calque = (self.canvas.calque_actif
                      if cible.type == TYPE_SCREEN else None)
            if reparenter(noeud, cible, calque):
                self.canvas.rafraichir()
                self.rafraichir_arbre()
                self.rafraichir_inspecteur()

        combo.currentIndexChanged.connect(changer)
        self.form_inspe.addWidget(combo, ligne, 1, 1, 2)

    def _champs_code(self, noeud):
        """Champs propres au type du widget, rangés dans la section « Code »."""
        if noeud.type in (TYPE_LABEL, TYPE_FRAME_BOUTON, TYPE_SAISIE_TEXTE):
            self._champ_texte(noeud)
        elif noeud.type == TYPE_BLOC_TEXTE:
            self._champ_texte_libre(noeud)
        if noeud.type == TYPE_SAISIE_TEXTE:
            self._champ_prefixe(noeud)
        if noeud.type == TYPE_LISTE:
            self._champ_items(noeud)
        if noeud.type == TYPE_BARRE_PROGRES:
            self._champ_pourcentage(noeud)
        if noeud.type == TYPE_BOUTON_IMAGE:
            self._champ_bouton_images(noeud)
        elif noeud.type in (TYPE_IMAGE, TYPE_VIDEO):
            self._champ_chemin_image(
                noeud, "Vidéo" if noeud.type == TYPE_VIDEO else "Image")

    def _champs_couleurs(self, noeud):
        """Couleurs du widget (résolues depuis le thème) : section « Thème »."""
        if noeud.type == TYPE_FRAME_BOUTON:
            for i in range(1, 5):
                self._champ_couleur(noeud, f"base_color{i}", f"Fond coin {i}")
            self._champ_couleur(noeud, "color", "Couleur texte")
        elif noeud.type in (TYPE_FRAME, TYPE_LABEL, TYPE_BLOC_TEXTE,
                            TYPE_SAISIE_TEXTE):
            self._champ_couleur(noeud, "color", "Couleur")

    def _champ_calques(self, noeud):
        """Section « Calques » de l'inspecteur, réservée à la sélection Screen.

        La création d'un calque ne se fait qu'ici (sélection du Screen). Le
        premier calque (la base, nommée ``start`` au départ) peut être
        renommé mais jamais supprimé.
        """
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Calques"), ligne, 0)
        for i, nom in enumerate(calques_ecran(noeud)):
            ligne = self._ligne_suivante()
            champ = QLineEdit(nom)
            nom_actuel = [nom]        # mutable : suit le nom après renommage
            champ.editingFinished.connect(
                lambda c=champ, n=nom_actuel: self._renommer_calque(c, n))
            self.form_inspe.addWidget(champ, ligne, 0, 1, 2)
            if i > 0:
                b_suppr = QPushButton("✕")
                b_suppr.setMaximumWidth(28)
                b_suppr.setToolTip(
                    "Supprimer ce calque et tous les éléments qu'il contient")
                b_suppr.clicked.connect(
                    lambda _, n=nom_actuel: self._supprimer_calque(n[0]))
                self.form_inspe.addWidget(b_suppr, ligne, 2)
        ligne = self._ligne_suivante()
        b_ajout = QPushButton("+ Ajouter un calque")
        b_ajout.setToolTip("Ajoute un calque d'affichage à cet écran")
        b_ajout.clicked.connect(self._ajouter_calque_ecran)
        self.form_inspe.addWidget(b_ajout, ligne, 0, 1, 3)

    @Slot()
    def _ajouter_calque_ecran(self):
        if self.scene is None:
            return
        ajouter_calque(self.scene)
        self.canvas.rafraichir()
        self.rafraichir_arbre()
        self.rafraichir_inspecteur()

    @Slot(object, object)
    def _renommer_calque(self, champ, nom_actuel):
        """Renomme le calque désigné par ``champ`` à la validation.

        Le renommage n'a lieu qu'en fin d'édition (Entrée / perte de focus)
        : le champ n'est jamais détruit en cours de frappe. ``nom_actuel``
        suit le nom réel du calque après chaque renommage.
        """
        ancien = nom_actuel[0]
        nouveau = champ.text()
        if self.scene is None or not nouveau.strip():
            return
        if not renommer_calque(self.scene, ancien, nouveau.strip()):
            self._revenir_nom(champ, ancien)
            return
        nom_actuel[0] = nouveau.strip()
        self.canvas.rafraichir()
        self.rafraichir_arbre()

    def _revenir_nom(self, champ, nom):
        champ.blockSignals(True)
        champ.setText(nom)
        champ.blockSignals(False)

    @Slot(str)
    def _supprimer_calque(self, nom):
        if self.scene is None:
            return
        if retirer_calque(self.scene, nom):
            self.canvas.rafraichir()
            self.rafraichir_arbre()
            self.rafraichir_inspecteur()

    def _spin(self, valeur_norm, parent_px, defaut_px, max_px, callback):
        spin = QDoubleSpinBox()
        spin.setRange(0.0, max(1.0, max_px))
        spin.setMaximumWidth(90)
        spin.setDecimals(1)
        spin.setValue(valeur_norm * parent_px)
        spin.setSingleStep(max(1.0, parent_px / 200.0))
        spin.valueChanged.connect(callback)
        return spin

    def _modifier_prop(self, noeud, cle, index, valeur_px, parent_px):
        valeurs = list(noeud.prop.get(cle, [0, 0]))
        valeurs[index] = px_vers_normalise(valeur_px, parent_px)
        noeud.prop[cle] = valeurs
        self.canvas.rafraichir()
        self._maj_status()

    def _champ_resolution(self, noeud):
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Résolution"), ligne, 0)
        for index in (0, 1):
            spin = QSpinBox()
            spin.setRange(1, 3840)
            spin.setValue(int(noeud.prop.get("res", [1280, 720])[index]))
            spin.valueChanged.connect(
                lambda v, i=index: self._modifier_res(noeud, i, v))
            self.form_inspe.addWidget(spin, ligne, index + 1)

    def _modifier_res(self, noeud, index, valeur):
        res = list(noeud.prop.get("res", [1280, 720]))
        res[index] = int(valeur)
        noeud.prop["res"] = res
        self.canvas.maj_taille_ecran(res[0], res[1])

    def _champ_texte(self, noeud):
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Texte"), ligne, 0)
        champ_texte = QLineEdit(str(noeud.prop.get("text", "")))
        champ_texte.textChanged.connect(
            lambda t, n=noeud: (n.prop.__setitem__("text", t),
                                self.canvas.rafraichir(),
                                self._maj_champs_geo(n)))
        self.form_inspe.addWidget(champ_texte, ligne, 1, 1, 2)

        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Font (pt)"), ligne, 0)
        spin_pt = QSpinBox()
        spin_pt.setRange(6, 200)
        spin_pt.setValue(int(valeur_rendu(noeud, "pt_size", TYPE_LABEL, "Size",
                                          THEME_BGUI_DEFAUT[TYPE_LABEL]["Size"])))
        spin_pt.valueChanged.connect(
            lambda v, n=noeud: (n.prop.__setitem__("pt_size", v),
                                self.canvas.rafraichir(),
                                self._maj_champs_geo(n)))
        self.form_inspe.addWidget(spin_pt, ligne, 1, 1, 2)

    def _champ_texte_libre(self, noeud):
        """Champ texte multi-lignes (TextBlock)."""
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Texte"), ligne, 0)
        texte = QPlainTextEdit(str(noeud.prop.get("text", "")))
        texte.setFixedHeight(70)
        texte.textChanged.connect(
            lambda n=noeud, t=texte: self._ecrire_texte_bloc(n, t))
        self.form_inspe.addWidget(texte, ligne, 1, 1, 2)

        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Font (pt)"), ligne, 0)
        spin_pt = QSpinBox()
        spin_pt.setRange(6, 200)
        spin_pt.setValue(int(valeur_rendu(noeud, "pt_size", TYPE_LABEL, "Size",
                                          THEME_BGUI_DEFAUT[TYPE_LABEL]["Size"])))
        spin_pt.valueChanged.connect(
            lambda v, n=noeud: (n.prop.__setitem__("pt_size", v),
                                self.canvas.update()))
        self.form_inspe.addWidget(spin_pt, ligne, 1, 1, 2)

    def _ecrire_texte_bloc(self, noeud, editeur):
        """Stocke le texte du TextBlock depuis son éditeur multi-lignes."""
        noeud.prop["text"] = editeur.toPlainText()
        self.canvas.update()

    def _champ_prefixe(self, noeud):
        """Champ préfixe non éditable (TextInput)."""
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Préfixe"), ligne, 0)
        champ_prefixe = QLineEdit(str(noeud.prop.get("prefix", "")))
        champ_prefixe.setToolTip(
            "Texte affiché avant la saisie de l'utilisateur, non éditable "
            "(propriété TextInput.prefix)")
        champ_prefixe.textChanged.connect(
            lambda t, n=noeud: (n.prop.__setitem__("prefix", t),
                                self.canvas.update()))
        self.form_inspe.addWidget(champ_prefixe, ligne, 1, 1, 2)

    def _champ_items(self, noeud):
        """Champ éléments de la ListBox (un par ligne) + index sélectionné."""
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Éléments"), ligne, 0)
        editeur = QPlainTextEdit()
        items = noeud.prop.get("items", [])
        if isinstance(items, list):
            editeur.setPlainText("\n".join(str(i) for i in items))
        else:
            editeur.setPlainText(str(items))
        editeur.setFixedHeight(70)
        editeur.setToolTip("Un élément par ligne (ListBox.items)")
        editeur.textChanged.connect(
            lambda n=noeud, t=editeur: self._ecrire_items(n, t))
        self.form_inspe.addWidget(editeur, ligne, 1, 1, 2)

        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Sélection"), ligne, 0)
        spin_sel = QSpinBox()
        spin_sel.setRange(0, max(0, len(items) - 1))
        spin_sel.setValue(int(noeud.prop.get("selected", 0)))
        spin_sel.valueChanged.connect(
            lambda v, n=noeud: (n.prop.__setitem__("selected", v),
                                self.canvas.update()))
        self.form_inspe.addWidget(spin_sel, ligne, 1, 1, 2)

    def _ecrire_items(self, noeud, editeur):
        noeud.prop["items"] = [l for l in editeur.toPlainText().splitlines()]
        self.canvas.update()

    def _champ_pourcentage(self, noeud):
        """Champ pourcentage de la ProgressBar (0 à 100 %)."""
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Pourcentage"), ligne, 0)
        spin_pct = QDoubleSpinBox()
        spin_pct.setRange(0.0, 100.0)
        spin_pct.setSuffix(" %")
        spin_pct.setSingleStep(1.0)
        spin_pct.setDecimals(1)
        spin_pct.setValue(float(noeud.prop.get("percent", 0.5)) * 100.0)
        spin_pct.valueChanged.connect(
            lambda v, n=noeud: self._modifier_pourcentage(n, v))
        self.form_inspe.addWidget(spin_pct, ligne, 1, 1, 2)

    def _modifier_pourcentage(self, noeud, pourcentage):
        noeud.prop["percent"] = max(0.0, min(100.0, pourcentage)) / 100.0
        self.canvas.update()

    def _champ_couleur(self, noeud, cle, libelle):
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel(libelle), ligne, 0)

        spin_alpha = QDoubleSpinBox()
        spin_alpha.setRange(0.0, 1.0)
        spin_alpha.setDecimals(2)
        spin_alpha.setSingleStep(0.05)
        spin_alpha.setToolTip(
            f"Opacité (alpha) de « {libelle.lower()} » : "
            "0.0 = transparent, 1.0 = opaque")
        spin_alpha.valueChanged.connect(
            lambda a, n=noeud, c=cle: self._modifier_couleur(n, c, alpha=a))
        rgba = self._couleur_effective(noeud, cle)
        spin_alpha.setValue(float(rgba[3]) if len(rgba) > 3 else 1.0)

        bouton = self._bouton_couleur(noeud, cle, spin_alpha)
        self.form_inspe.addWidget(bouton, ligne, 1)
        self.form_inspe.addWidget(spin_alpha, ligne, 2)

    def _modifier_couleur(self, noeud, cle, alpha=None):
        """Met à jour une couleur : alpha optionnel (0..1), RGB conservé."""
        valeurs = list(noeud.prop.get(cle, self._couleur_effective(noeud, cle)))
        if len(valeurs) < 3:
            valeurs = [1.0, 1.0, 1.0, 1.0]
        if len(valeurs) < 4:
            valeurs.append(1.0)
        if alpha is not None:
            valeurs[3] = float(alpha)
        noeud.prop[cle] = [float(v) for v in valeurs[:4]]
        self.canvas.update()

    # --- Propriétés custom (écran / projet theme.cfg) ---------------------

    def _champ_proprietes(self, source, grille, ligne_suivante):
        """Section « Propriétés » : bouton « + Properties » + liste existante.

        ``source`` est une :class:`ProprietesSource` (celle de l'écran
        sélectionné ou celle du projet de l'onglet CODE). Le rendu se fait
        dans la grille fournie, sur la ligne renvoyée par ``ligne_suivante``.
        """
        ligne = ligne_suivante()
        grille.addWidget(QLabel("<b>Propriétés</b>"), ligne, 0)
        b_plus = QPushButton("+ Properties")
        b_plus.setToolTip(
            f"Ajouter une propriété custom à {source.proprietaire}.\n"
            "Types : str(), float(), int(), bool(), vecteurs 2D/3D/4D,\n"
            "RGBA, tuple image, enum() (liste), objet (bpy.types.*).\n"
            "Dans theme.cfg, sa valeur se récupère avec prop.<nom>.")
        b_plus.clicked.connect(
            lambda _=False, s=source: self._ajouter_propriete(s))
        grille.addWidget(b_plus, ligne, 1, 1, 2)

        for index, propriete in enumerate(source.liste):
            ligne = ligne_suivante()
            type_propriete = propriete["type"]
            libelle = libelle_type_propriete(type_propriete)
            etiquette = QLabel(
                f"<b>{propriete['nom']}</b> "
                f"<span style='color:#8a8a8a;'>{libelle}</span>")
            etiquette.setToolTip(description_type_propriete(type_propriete))
            grille.addWidget(etiquette, ligne, 0)
            editeur = self._editeur_propriete(source, index)
            grille.addWidget(editeur, ligne, 1)
            b_suppr = QPushButton("✕")
            b_suppr.setFixedWidth(26)
            b_suppr.setToolTip("Supprimer cette propriété")
            b_suppr.clicked.connect(
                lambda _=False, s=source, i=index:
                self._supprimer_propriete(s, i))
            grille.addWidget(b_suppr, ligne, 2)

    def _ajouter_propriete(self, source):
        """Ouvre un petit formulaire pour définir une nouvelle propriété."""
        formule = QDialog(self)
        formule.setWindowTitle("Ajouter une propriété")
        formulaire = QFormLayout(formule)
        noms_existants = {p["nom"] for p in source.liste}
        numero = 1
        while f"propriete_{numero}" in noms_existants:
            numero += 1
        champ_nom = QLineEdit(f"propriete_{numero}")
        liste_types = QComboBox()
        for type_propriete in TYPES_PROPRIETE:
            liste_types.addItem(libelle_type_propriete(type_propriete),
                                userData=type_propriete)
        formulaire.addRow("Nom :", champ_nom)
        formulaire.addRow("Type :", liste_types)
        ligne_type = QLabel(
            "\n— enum() : liste d'éléments séparés par des virgules ;\n"
            "  génère une propriété d'énumération.\n"
            "— objet · type: X : référence vers un objet bpy.type.X (UPBGE).\n"
            "— Dans theme.cfg, prop.<nom> renvoie la valeur typée.")
        ligne_type.setWordWrap(True)
        formulaire.addRow("", ligne_type)
        boutons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        boutons.accepted.connect(formule.accept)
        boutons.rejected.connect(formule.reject)
        formulaire.addRow(boutons)
        if formule.exec() != QDialog.Accepted:
            return
        nom = champ_nom.text().strip()
        if not nom:
            return
        type_propriete = liste_types.currentData()
        for p in source.liste:
            if p["nom"] == nom:
                QMessageBox.warning(
                    self, "Propriété existante",
                    f"Une propriété « {nom} » existe déjà "
                    f"sur {source.proprietaire}.")
                return
        source.liste.append({
            "nom": nom,
            "type": type_propriete,
            "valeur": valeur_defaut_propriete(type_propriete),
        })
        source.apres()

    def _supprimer_propriete(self, source, index):
        propriete = source.liste.pop(index)
        self._maj_status()
        source.apres()
        self.lbl_selection.setText(
            f"{source.proprietaire} · propriété "
            f"« {propriete['nom']} » supprimée")

    def _editeur_propriete(self, source, index):
        """Widget d'édition de la valeur selon le type de la propriété."""
        propriete = source.liste[index]
        type_propriete = propriete["type"]
        valeur = propriete.get("valeur", valeur_defaut_propriete(type_propriete))

        def ecrire(nouvelle):
            source.liste[index]["valeur"] = nouvelle
            source.maj()

        if type_propriete == "bool()":
            case = QCheckBox()
            case.setChecked(bool(valeur))
            case.toggled.connect(ecrire)
            return case
        if type_propriete == "int()":
            spin = QSpinBox()
            spin.setRange(-2**31, 2**31 - 1)
            spin.setValue(int(valeur))
            spin.valueChanged.connect(ecrire)
            return spin
        if type_propriete == "float()":
            spin = QDoubleSpinBox()
            spin.setRange(-1e9, 1e9)
            spin.setDecimals(3)
            spin.setValue(float(valeur))
            spin.valueChanged.connect(ecrire)
            return spin

        if type_propriete.startswith("vector "):
            return self._editeur_vecteur(source, index, type_propriete)

        if type_propriete == "bpy.type.VectorFont":
            return self._editeur_font_propriete(source, index)

        description = {
            "list": "Éléments séparés par des virgules :\n"
                    "ex. epee, bouclier, casque  →  "
                    "{\"epee\", \"bouclier\", \"casque\"}",
            "RGBA": "Couleur r, g, b, a (floats 0..1).\n"
                    "Ex. : 1, 0.7, 0.1, 1",
            "tuple image": "Image : None, x, y, w, h\n"
                           "(None, 0, 0, 1, 1) = image entière",
        }.get(type_propriete,
              f"Référence UPBGE de type {type_propriete}.")
        champ_texte = QLineEdit(str(valeur))
        champ_texte.setToolTip(description)
        champ_texte.textChanged.connect(
            lambda t, i=index, s=source: self._ecrire_texte_propriete(s, i, t))
        return champ_texte

    def _editeur_vecteur(self, source, index, type_propriete):
        """Édition d'un vecteur 2D/3D/4D par des float() individuels."""
        dimension = {
            "vector 2D": 2, "vector 3D": 3, "vector 4D": 4,
        }.get(type_propriete, 2)
        prefixe_composantes = ("x", "y", "z", "w")[:dimension]
        valeurs = source.liste[index].get(
            "valeur", [0.0] * dimension)
        if not isinstance(valeurs, (list, tuple)):
            valeurs = [0.0] * dimension

        boite = QWidget()
        disposition = QVBoxLayout(boite)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(2)

        def ecrire():
            source.liste[index]["valeur"] = [s.value() for s in spins]
            source.maj()

        spins = []
        for i in range(dimension):
            spin = QDoubleSpinBox()
            spin.setRange(-1e9, 1e9)
            spin.setDecimals(3)
            spin.setValue(float(valeurs[i]) if len(valeurs) > i else 0.0)
            spin.setPrefix(prefixe_composantes[i] + ": ")
            spin.setFixedWidth(110)
            spin.setToolTip(f"Composante {prefixe_composantes[i]}")
            spin.valueChanged.connect(ecrire)
            disposition.addWidget(spin)
            spins.append(spin)
        return boite

    def _ecrire_texte_propriete(self, source, index, texte):
        source.liste[index]["valeur"] = texte
        source.maj()

    def _editeur_font_propriete(self, source, index):
        """Éditeur d'une propriété écran de type VectorFont : choix du fichier.

        La valeur stockée est le **chemin du fichier de police** (.ttf/.otf)
        utilisé uniquement pour l'aperçu dans l'éditeur. L'export, lui,
        continue de passer par ``data["font"][i].filepath`` (référence UPBGE
        résolue au runtime) — le chemin ici n'a donc aucun effet sur le code
        généré.
        """
        propriete = source.liste[index]
        valeur = str(propriete.get("valeur") or "")

        boite = QWidget()
        disposition = QHBoxLayout(boite)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.setSpacing(2)

        champ = QLineEdit(valeur)
        champ.setPlaceholderText("Fichier de police (aperçu éditeur)")
        champ.setToolTip(
            "Chemin du fichier de police (.ttf/.otf) à afficher dans\n"
            "l'éditeur. Sans effet sur l'export : celui-ci utilise\n"
            "data['font'][i].filepath (référence UPBGE).\n"
            "Une fois le fichier choisi, sélectionnez cette propriété dans\n"
            "le champ « font » du widget pour voir le texte avec cette fonte.")
        champ.textEdited.connect(
            lambda t, s=source, i=index: self._ecrire_texte_propriete(s, i, t))
        disposition.addWidget(champ, 1)

        def parcourir():
            chemin, _ = QFileDialog.getOpenFileName(
                self, "Choisir une police (aperçu éditeur)",
                champ.text(), "Polices (*.ttf *.otf)")
            if chemin:
                champ.setText(chemin)
                self._ecrire_texte_propriete(source, index, chemin)

        b_fichier = QPushButton("…")
        b_fichier.setFixedWidth(28)
        b_fichier.setToolTip("Parcourir le disque pour choisir le fichier de police")
        b_fichier.clicked.connect(parcourir)
        disposition.addWidget(b_fichier)
        return boite

    def _couleur_effective(self, noeud, cle):
        """Couleur réellement affichée : propriété du nœud, sinon thème actif
        (section du type, ou du sous-thème du widget si ``sub_theme``)."""
        if noeud.type == TYPE_FRAME_BOUTON:
            if cle in ("base_color1", "base_color2", "base_color3",
                       "base_color4"):
                coin = cle[-1]
                return valeur_rendu(
                    noeud, cle, TYPE_FRAME_BOUTON, f"Color{coin}",
                    THEME_BGUI_DEFAUT[TYPE_FRAME_BOUTON][f"Color{coin}"])
            return valeur_rendu(
                noeud, cle, TYPE_FRAME_BOUTON, "Color",
                THEME_BGUI_DEFAUT[TYPE_FRAME_BOUTON]["Color"])
        if noeud.type == TYPE_SCREEN and cle == "color":
            return valeur_rendu(
                noeud, cle, TYPE_SCREEN, "fond",
                THEME_BGUI_DEFAUT[TYPE_SCREEN]["fond"])
        if noeud.type == TYPE_SAISIE_TEXTE:
            return valeur_rendu(
                noeud, cle, TYPE_SAISIE_TEXTE, "TextColor",
                THEME_BGUI_DEFAUT[TYPE_SAISIE_TEXTE]["TextColor"])
        if noeud.type in (TYPE_LABEL, TYPE_BLOC_TEXTE):
            return valeur_rendu(
                noeud, cle, TYPE_LABEL, "Color",
                THEME_BGUI_DEFAUT[TYPE_LABEL]["Color"])
        return valeur_rendu(
            noeud, cle, TYPE_FRAME, "Color1",
            THEME_BGUI_DEFAUT[TYPE_FRAME]["Color1"])

    def _bouton_couleur(self, noeud, cle, spin_alpha=None):
        bouton = QPushButton()
        bouton.setFixedHeight(24)

        def actualiser():
            rgba = self._couleur_effective(noeud, cle)
            couleur = QColor(int(rgba[0] * 255), int(rgba[1] * 255),
                             int(rgba[2] * 255))
            bouton.setStyleSheet(
                f"background-color: {couleur.name()}; border: 1px solid #777;")
            bouton.setToolTip(
                f"RGBA : {rgba[0]:.2f}, {rgba[1]:.2f}, {rgba[2]:.2f}, "
                f"{float(rgba[3]) if len(rgba) > 3 else 1.0:.2f}  "
                f"(cliquer pour ouvrir le sélecteur de couleur)")
            if spin_alpha is not None and len(rgba) > 3:
                spin_alpha.blockSignals(True)
                spin_alpha.setValue(float(rgba[3]))
                spin_alpha.blockSignals(False)

        def choisir():
            rgba = self._couleur_effective(noeud, cle)
            courante = QColor(int(rgba[0] * 255), int(rgba[1] * 255),
                              int(rgba[2] * 255),
                              int(rgba[3] * 255) if len(rgba) > 3 else 255)
            boite = QColorDialog(courante, self)
            boite.setOption(QColorDialog.ShowAlphaChannel, True)
            boite.setWindowTitle("Choisir une couleur")
            if boite.exec():
                choix = boite.selectedColor()
                noeud.prop[cle] = [choix.red() / 255.0, choix.green() / 255.0,
                                   choix.blue() / 255.0, choix.alphaF()]
                actualiser()
                self.canvas.update()

        bouton.clicked.connect(choisir)
        actualiser()
        return bouton

    def _champ_bouton_images(self, noeud):
        """Champs image du ImageButton : chaque état a son sélecteur.

        L'image principale (``fichier``) et les états alternatifs
        (``default2_image``, ``hover_image``, ``click_image``) sont
        sélectionnables comme une image simple.
        """
        for libelle, cle in [("Image", "fichier"),
                             ("Défaut 2", "default2_image"),
                             ("Survol", "hover_image"),
                             ("Clic", "click_image")]:
            self._champ_chemin_image(noeud, libelle, cle)

    def _champ_chemin_image(self, noeud, libelle="Image", cle="fichier"):
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel(libelle), ligne, 0)
        champ = QLineEdit(str(noeud.prop.get(cle, "")))
        champ.setToolTip(
            "Chemins acceptés :\n"
            "//data/logo.png  relatif au projet (UPBGE)\n"
            "~/Images/logo.png  relatif au répertoire personnel\n"
            "/home/user/logo.png  ou chemin absolu")
        champ.textChanged.connect(
            lambda t, n=noeud, k=cle: (n.prop.__setitem__(k, t),
                                       self.canvas.update()))
        self.form_inspe.addWidget(champ, ligne, 1, 1, 2)

        b_parcourir = QPushButton("Parcourir...")
        b_parcourir.setToolTip(
            f"Choisir un fichier {libelle.lower()}. Le chemin saisi peut être "
            "relatif (// ou ~/) ou absolu.")
        b_parcourir.clicked.connect(
            lambda _=False, n=noeud, c=champ, l=libelle, k=cle:
            self._choisir_fichier(n, c, l, k))
        self.form_inspe.addWidget(b_parcourir, self._ligne_suivante(), 1, 1, 2)

    def _choisir_fichier(self, noeud, champ, libelle, cle="fichier"):
        if libelle == "Vidéo":
            filtre = ("Vidéos (*.ogg *.ogv *.webm *.mp4 *.avi *.mpeg "
                      "*.mpg *.wmv)")
            titre = "Choisir une vidéo"
        else:
            filtre = "Images (*.png *.jpg *.jpeg *.bmp *.tga)"
            titre = "Choisir une image"
        chemin, _ = QFileDialog.getOpenFileName(self, titre, "", filtre)
        if chemin:
            stocke = self._chemin_relatif_projet(chemin)
            noeud.prop[cle] = stocke
            champ.setText(stocke)
            self.canvas.update()

    def _chemin_relatif_projet(self, chemin):
        """Convertit un chemin absolu en chemin relatif « // » au projet.

        Le résultat est stocké au format ``//data/logo.png`` (relatif au
        répertoire de base du projet) et résolu au runtime par
        ``bge.logic.expandPath``/``bpy.path.abspath``. Si le fichier n'est
        pas sous la base du projet, le chemin absolu est conservé.
        """
        base = bgui_theme.CHEMIN_BASE_PROJET
        if not base or not chemin:
            return chemin
        absolu = os.path.abspath(chemin)
        base_abs = os.path.abspath(base)
        try:
            relatif = os.path.relpath(absolu, base_abs)
        except ValueError:
            return chemin
        if relatif.startswith(".."):
            return chemin
        relatif = relatif.replace(os.sep, "/")
        if os.altsep:
            relatif = relatif.replace(os.altsep, "/")
        return "//" + relatif

    def _champ_options(self, noeud):
        """Options « code » génériques du widget, rangées dans la section « Code ».

        Rendu : `z_index`, `frozen`, `options` (drapeaux BGUI) puis les
        options propres au type (OPTIONS_PAR_TYPE) qui ne sont pas éditées
        par un champ dédié.
        « sub_theme » et les couleurs, eux, vivent dans la section « Thème ».
        """
        if noeud.type == TYPE_SCREEN:
            return
        for cle in ("z_index", "frozen", "options"):
            valeur = noeud.prop.get(cle)
            if valeur is None:
                continue
            ligne = self._ligne_suivante()
            self.form_inspe.addWidget(
                QLabel("Widget options" if cle == "options" else cle),
                ligne, 0)
            editeur = (self._editeur_options(noeud) if cle == "options"
                       else self._editeur_option(noeud, cle, valeur))
            self.form_inspe.addWidget(editeur, ligne, 1, 1, 2)

        dedies = CHAMPS_DEDIES.get(noeud.type, set())
        for cle, valeur in OPTIONS_PAR_TYPE.get(noeud.type, {}).items():
            if cle in dedies:
                continue
            ligne = self._ligne_suivante()
            self.form_inspe.addWidget(QLabel(cle), ligne, 0)
            self.form_inspe.addWidget(
                self._editeur_option(noeud, cle, valeur), ligne, 1, 1, 2)

    def _editeur_options(self, noeud):
        """Éditeur des drapeaux « Widget options » du widget.

        Un menu déroulant (QComboBox) listant les constantes BGUI
        utilisables, ``BGUI_DEFAULT`` (0) étant la valeur proposée par
        défaut. La valeur choisie est stockée telle quelle dans
        ``noeud.prop["options"]``.
        """
        choix = [(0, "BGUI_DEFAULT (0)"),
                 (BIT_CENTERED, "BGUI_CENTERED (CENTERX|CENTERY)")]
        docs = {bit: doc for bit, _, doc in DRAPEAUX_OPTIONS}
        choix += [(bit, f"{nom} ({bit})") for bit, nom, _ in DRAPEAUX_OPTIONS]

        combo = QComboBox()
        for bit, libelle in choix:
            combo.addItem(libelle, bit)
            combo.setItemData(combo.count() - 1, docs.get(bit, ""),
                              Qt.ToolTipRole)

        courant = int(noeud.prop.get("options") or 0)
        indice = next((i for i, (bit, _) in enumerate(choix)
                       if bit == courant), 0)
        combo.setCurrentIndex(indice)

        def maj(_indice):
            noeud.prop["options"] = int(choix[combo.currentIndex()][0])
            self.canvas.rafraichir()

        combo.currentIndexChanged.connect(maj)
        return combo

    def _champ_fonctions(self, noeud):
        """Section « Fonctions » : événements déclencheurs, façon Godot.

        Chaque événement relie un déclencheur BGUI (ex. ``on_click``) à la
        fonction à appeler (nom de méthode, à définir dans le code UPBGE).
        Le corps de la fonction est éditable directement dans le champ
        multiline sous le nom.
        """
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("<b>Fonctions</b>"), ligne, 0, 1, 3)

        for index, evenement in enumerate(list(noeud.evenements)):
            if str(evenement.get("declencheur", "")) == "on_update":
                continue
            ligne = self._ligne_suivante()
            champ = QComboBox()
            champ.addItems(DECLENCHEURS_EVENEMENTS)
            champ.setCurrentText(str(evenement.get(
                "declencheur", DECLENCHEURS_EVENEMENTS[0])))
            champ.setToolTip(
                "Déclencheur BGUI du widget (callback raccordé).\n"
                "Ex. : on_click = clic sur le bouton.")
            champ.currentTextChanged.connect(
                lambda t, n=noeud, i=index:
                self._modifier_evenement(n, i, "declencheur", t))
            self.form_inspe.addWidget(champ, ligne, 0)

            champ_fonction = QLineEdit(str(evenement.get("fonction", "")))
            champ_fonction.setPlaceholderText("fonction")
            champ_fonction.setToolTip(
                "Nom de la fonction appelée quand le déclencheur se produit.\n"
                "À définir dans le code Python de l'UPBGE.")
            champ_fonction.textChanged.connect(
                lambda t, n=noeud, i=index:
                self._modifier_evenement(n, i, "fonction", t))
            self.form_inspe.addWidget(champ_fonction, ligne, 1)

            b_suppr = QPushButton("✕")
            b_suppr.setFixedWidth(26)
            b_suppr.setToolTip("Supprimer cet événement")
            b_suppr.clicked.connect(
                lambda _=False, n=noeud, i=index:
                self._supprimer_evenement(n, i))
            self.form_inspe.addWidget(b_suppr, ligne, 2)

            corps = "\n".join(evenement.get("code", []))
            champ_code = QPlainTextEdit(corps)
            champ_code.setPlaceholderText("pass")
            champ_code.setTabChangesFocus(True)
            champ_code.setToolTip(
                "Corps de la fonction à écrire.\n"
                "Le code sera indenté sous le ``def`` dans le script généré.")
            champ_code.setMaximumHeight(96)
            champ_code.setPlainText(corps)
            champ_code.textChanged.connect(
                lambda _=False, n=noeud, i=index, w=champ_code:
                self._modifier_evenement(
                    n, i, "code", w.toPlainText().splitlines()))
            ligne_code = self._ligne_suivante()
            self.form_inspe.addWidget(champ_code, ligne_code, 0, 1, 3)

            ligne = self._ligne_suivante()
            chk_lambda = QCheckBox("Lambda (widget, *args)")
            chk_lambda.setChecked(bool(evenement.get("lambda")))
            chk_lambda.setToolTip(
                "Coché : raccord via ``lambda widget, *args: ...``.\n"
                "Décoché : raccord direct ``self.<fonction>`` (actuel).")
            chk_lambda.toggled.connect(
                lambda v, n=noeud, i=index:
                self._modifier_evenement(n, i, "lambda", v))
            self.form_inspe.addWidget(chk_lambda, ligne, 0, 1, 3)

            ligne = self._ligne_suivante()
            self.form_inspe.addWidget(QLabel("Arguments"), ligne, 0)
            b_arg = QPushButton("+ Argument")
            b_arg.setFixedWidth(96)
            b_arg.setToolTip(
                "Ajouter un nom d'argument passé à la fonction.\n"
                "Le stub généré accepte alors ``*args``.")
            b_arg.clicked.connect(
                lambda _=False, n=noeud, i=index:
                self._ajouter_argument(n, i))
            self.form_inspe.addWidget(b_arg, ligne, 1, 1, 2)

            for idx_arg, nom_arg in enumerate(
                    evenement.get("args", []) or []):
                ligne_arg = self._ligne_suivante()
                champ_arg = QLineEdit(str(nom_arg))
                champ_arg.setPlaceholderText("nom")
                champ_arg.setToolTip(
                    "Nom de l'argument reçu dans la fonction (``*args``).\n"
                    "Donnez-lui une valeur par défaut dans le corps.")
                champ_arg.textChanged.connect(
                    lambda t, n=noeud, i=index, a=idx_arg:
                    self._modifier_argument(n, i, a, "nom", t))
                self.form_inspe.addWidget(champ_arg, ligne_arg, 0, 1, 2)

                b_suppr_arg = QPushButton("✕")
                b_suppr_arg.setFixedWidth(26)
                b_suppr_arg.setToolTip("Retirer cet argument")
                b_suppr_arg.clicked.connect(
                    lambda _=False, n=noeud, i=index, a=idx_arg:
                    self._supprimer_argument(n, i, a))
                self.form_inspe.addWidget(b_suppr_arg, ligne_arg, 2)

        ligne = self._ligne_suivante()
        b_ajout = QPushButton("+ Ajouter un événement")
        b_ajout.setToolTip(
            "Raccorder un déclencheur à une fonction (façon Godot).")
        b_ajout.clicked.connect(
            lambda _=False, n=noeud: self._ajouter_evenement(n))
        self.form_inspe.addWidget(b_ajout, ligne, 0, 1, 3)

    def _ajouter_evenement(self, noeud):
        """Ajoute un événement déclencheur vide au widget et réaffiche."""
        noeud.evenements.append(
            {"declencheur": DECLENCHEURS_EVENEMENTS[0], "fonction": "",
             "code": [], "lambda": False, "args": []})
        self.canvas.rafraichir()
        self.rafraichir_inspecteur()

    def _modifier_evenement(self, noeud, index, cle, valeur):
        """Met à jour une partie d'un événement, sans reconstruire l'inspecteur."""
        if 0 <= index < len(noeud.evenements):
            noeud.evenements[index][cle] = valeur

    def _supprimer_evenement(self, noeud, index):
        """Retire l'événement d'index `index` et réaffiche l'inspecteur."""
        if 0 <= index < len(noeud.evenements):
            del noeud.evenements[index]
        self.canvas.rafraichir()
        self.rafraichir_inspecteur()

    def _ajouter_argument(self, noeud, index):
        """Ajoute un argument vide à l'événement d'index `index`."""
        if 0 <= index < len(noeud.evenements):
            evenement = noeud.evenements[index]
            evenement.setdefault("args", []).append("")
            # Un argument n'a de sens qu'avec le lambda : on le coche.
            evenement["lambda"] = True
            self.canvas.update()
        self.rafraichir_inspecteur()

    def _modifier_argument(self, noeud, index, idx_arg, cle, valeur):
        """Met à jour un champ d'un argument sans reconstruire l'inspecteur."""
        try:
            evenement = noeud.evenements[index]
            evenement.setdefault("args", [])
            if 0 <= idx_arg < len(evenement["args"]):
                evenement["args"][idx_arg] = valeur
        except (IndexError, KeyError):
            pass

    def _supprimer_argument(self, noeud, index, idx_arg):
        """Retire un argument d'un événement et réaffiche l'inspecteur."""
        try:
            evenement = noeud.evenements[index]
            if 0 <= idx_arg < len(evenement.get("args", [])):
                del evenement["args"][idx_arg]
            self.canvas.update()
        except IndexError:
            pass
        self.rafraichir_inspecteur()

    def _champ_mise_a_jour(self, noeud):
        """Section « Mise à jour » : code exécuté à chaque frame.

        Le corps est injecté dans ``Layout.update()`` du calque contenant
        le widget. Les lignes référencent le widget par son attribut
        (ex. ``self.image_1.color = [1, 0, 0, 1]``).
        """
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(
            QLabel("<b>+ Mise à jour</b>"), ligne, 0, 1, 3)

        corps = "\n".join(getattr(noeud, "update_code", None) or [])
        champ_code = QPlainTextEdit(corps)
        champ_code.setPlaceholderText(
            "Code exécuté à chaque frame dans Layout.update() du calque.\n"
            "Référez le widget par self.<attribut>\n"
            "(ex. self.image_1.color = [1, 0, 0, 1])")
        champ_code.setTabChangesFocus(True)
        champ_code.setToolTip(
            "Ces lignes sont injectées dans la méthode update() du Layout.\n"
            "Utilisez self.<nom_du_widget>.<propriété> pour le modifier.")
        champ_code.setMaximumHeight(96)
        champ_code.setPlainText(corps)
        champ_code.textChanged.connect(
            lambda _=False, n=noeud, w=champ_code:
            self._modifier_mise_a_jour(n, w.toPlainText().splitlines()))
        ligne_code = self._ligne_suivante()
        self.form_inspe.addWidget(champ_code, ligne_code, 0, 1, 3)

    def _modifier_mise_a_jour(self, noeud, lignes):
        """Stocke le corps « mise à jour » du widget sans reconstruire."""
        noeud.update_code = lignes

    def _champ_sub_theme(self, noeud):
        """Champ « sub_theme » : sous-thème du widget (section « Type:Nom »).

        Éditable : liste les sous-thèmes déjà définis dans le thème actif
        pour le type du widget (ex. ``[Label:Titre]``), et permet d'en saisir
        un nouveau, à définir ensuite dans l'onglet CODE. L'option « None »
        (par défaut) laisse la valeur vide = thème de base du type
        (ex. ``[Label]``).
        """
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("sub_theme"), ligne, 0)
        champ = QComboBox()
        champ.setEditable(True)
        courant = str(noeud.prop.get("sub_theme", ""))
        champ.blockSignals(True)
        champ.addItem("None", userData="")
        champ.addItems(sous_themes_disponibles(noeud.type))
        if courant and champ.findData(courant) < 0:
            champ.addItem(courant)
        champ.setCurrentText(courant)
        champ.blockSignals(False)
        champ.setToolTip(
            "Nom d'un sous-thème défini dans le fichier de thème, équivalent "
            "d'une classe CSS.\nEx. : « Titre » pour utiliser la section "
            "[Label:Titre] ;\n« None » (défaut) = thème de base [Label].\n"
            "Définissez la section dans l'onglet CODE puis « Appliquer ».")
        champ.lineEdit().setPlaceholderText("None")
        champ.lineEdit().textEdited.connect(
            lambda t, n=noeud: self._ecrire_sub_theme(n, t))
        champ.currentTextChanged.connect(
            lambda t, n=noeud: self._ecrire_sub_theme(n, t))
        self.form_inspe.addWidget(champ, ligne, 1, 1, 2)

    def _ecrire_sub_theme(self, noeud, texte):
        """Écrit la propriété sub_theme, « None »/vide étant traité comme absent."""
        valeur = "" if not texte or texte.strip() in ("", "None") else texte.strip()
        noeud.prop["sub_theme"] = valeur
        self.canvas.rafraichir()

    def _editeur_option(self, noeud, cle, valeur):
        """Éditeur générique d'une option BGUI (selon son type de valeur)."""

        if cle == "font":
            return self._champ_option_font(noeud)

        def ecrire(nouvelle):
            noeud.prop[cle] = nouvelle
            self.canvas.rafraichir()

        if isinstance(valeur, bool):
            case = QCheckBox()
            case.setChecked(bool(noeud.prop.get(cle, valeur)))
            case.toggled.connect(ecrire)
            return case
        if isinstance(valeur, int):
            spin = QSpinBox()
            spin.setRange(-1_000_000, 1_000_000)
            spin.setValue(int(noeud.prop.get(cle, valeur)))
            spin.valueChanged.connect(ecrire)
            return spin
        if isinstance(valeur, float):
            spin = QDoubleSpinBox()
            spin.setRange(-1e9, 1e9)
            spin.setDecimals(3)
            spin.setValue(float(noeud.prop.get(cle, valeur)))
            spin.valueChanged.connect(ecrire)
            return spin
        if isinstance(valeur, (list, tuple)) and len(valeur) >= 2:
            champ = QLineEdit(", ".join(str(m) for m in
                                        noeud.prop.get(cle, valeur)))
            champ.setToolTip(
                "Valeurs séparées par des virgules"
                " (couleur : r, g, b, a).")
            if len(valeur) == 4:
                champ.setPlaceholderText("r, g, b, a")
            champ.textChanged.connect(
                lambda t, n=noeud, c=cle:
                self._ecrire_option_liste(n, c, t))
            return champ
        champ = QLineEdit(str(noeud.prop.get(cle, valeur)))
        champ.textChanged.connect(ecrire)
        return champ

    def _ecrire_option_liste(self, noeud, cle, texte):
        parsed = valeur_depuis_texte(texte)
        if isinstance(parsed, tuple):
            noeud.prop[cle] = [float(m) for m in parsed]
        else:
            noeud.prop[cle] = texte
        self.canvas.rafraichir()

    def _champ_option_font(self, noeud):
        """Champ « font » d'un widget : référence à une propriété police.

        La police est chargée dans UPBGE comme propriété de l'écran ; ce
        champ attend le **nom** d'une propriété du Screen (déclaré dans le
        panneau « Propriétés » de l'écran). Le code généré fera
        ``font=bge.logic.expandPath(data["font"][i].filepath)``.

        L'option « None » (par défaut) laisse la police non modifiée : aucun
        ``font=`` n'est alors émis dans le script.
        """
        noms = set()
        for racine in (self.scene,):
            noms.update(str(p.get("nom", "")).strip()
                        for p in getattr(racine, "proprietes", [])
                        if p.get("nom"))
        champ = QComboBox()
        champ.setEditable(True)
        champ.addItem("None", userData="")
        noms = sorted(n for n in noms if n)
        champ.addItems(noms)
        courant = str(noeud.prop.get("font", "") or "")
        if courant:
            champ.setCurrentText(courant)
        else:
            champ.setCurrentIndex(champ.findData(""))
        champ.lineEdit().setPlaceholderText("None")
        champ.setToolTip(
            "Nom d'une propriété police de l'écran, ou « None » pour ne pas\n"
            "modifier la police (aucun font= émis dans le code généré).\n"
            "La police est chargée dans UPBGE et récupérée via\n"
            "data[\"font\"][i] dans le code généré.")
        champ.lineEdit().textEdited.connect(
            lambda t, n=noeud: self._ecrire_font(n, t))
        champ.currentTextChanged.connect(
            lambda t, n=noeud: self._ecrire_font(n, t))
        return champ

    def _ecrire_font(self, noeud, texte):
        """Écrit la propriété font, « None »/vide étant traité comme absent."""
        valeur = "" if not texte or texte.strip() in ("", "None") else texte.strip()
        noeud.prop["font"] = valeur
        self.canvas.rafraichir()

    def _champ_visible(self, noeud):
        ligne = self._ligne_suivante()
        self.form_inspe.addWidget(QLabel("Visible"), ligne, 0)
        case = QCheckBox()
        case.setChecked(bool(noeud.prop.get("visible", True)))
        case.toggled.connect(
            lambda v, n=noeud: (n.prop.__setitem__("visible", v),
                                self.canvas.rafraichir()))
        self.form_inspe.addWidget(case, ligne, 1, 1, 2)

    def _renommer(self, noeud, texte):
        noeud.nom = texte
        item = self._noeud_vers_item.get(id(noeud))
        if item is not None:
            item.setText(0, texte)
        self._maj_status()

    # ------------------------------------------------------------------
    # Synchronisation écran / inspecteur / barre d'état
    # ------------------------------------------------------------------

    @Slot(object)
    def _geo_changee(self, noeud):
        if noeud is not None and noeud is self.canvas.selection_actuelle():
            self._maj_champs_geo(noeud)
            self._maj_status()

    def _taille_affichage(self, noeud, parent_px):
        """Taille affichée (px) d'un widget dans son parent.

        Pour un Label, la taille réelle est calculée depuis le texte +
        pt_size (le ``size`` stocké n'ayant aucun effet BGUI) ; les autres
        widgets utilisent leur ``size`` normalisé.
        """
        p_l = parent_px.width() or 1.0
        p_h = parent_px.height() or 1.0
        if noeud.type == TYPE_LABEL:
            w_px, h_px = taille_label(noeud, parent_px)
            return w_px, h_px
        size = noeud.prop.get("size", [1.0, 1.0])
        return size[0] * p_l, size[1] * p_h

    def _maj_champs_geo(self, noeud):
        parent_px = self.canvas.rect_parent_scene(noeud)
        p_l, p_h = parent_px.width(), parent_px.height()
        pos = noeud.prop.get("pos", [0.0, 0.0])
        w_px, h_px = self._taille_affichage(noeud, parent_px)
        for cle, valeur in (("px", pos[0] * p_l), ("py", pos[1] * p_h),
                            ("pw", w_px), ("ph", h_px)):
            champ = self.champ.get(cle)
            if champ is not None:
                champ.blockSignals(True)
                champ.setValue(valeur)
                champ.blockSignals(False)

    def _maj_status(self):
        noeud = self.canvas.selection_actuelle()
        if noeud is None:
            self.lbl_selection.setText("aucun widget sélectionné")
            return
        parent_px = self.canvas.rect_parent_scene(noeud)
        p_l, p_h = parent_px.width(), parent_px.height()
        pos = noeud.prop.get("pos", [0.0, 0.0])
        w_px, h_px = self._taille_affichage(noeud, parent_px)
        self.lbl_selection.setText(
            f"{noeud.nom} ({noeud.type})  ·  position: "
            f"{pos[0] * p_l:.0f}, {pos[1] * p_h:.0f}px  "
            f"({pos[0]:.3f}, {pos[1]:.3f})  ·  taille: "
            f"{w_px:.0f} × {h_px:.0f}px  "
            f"({w_px / p_l:.3f} × {h_px / p_h:.3f})")

    @Slot(float, float, float, float)
    def _survol(self, px_x, px_y, norm_x, norm_y):
        self.statusBar().showMessage(
            f"Souris: {int(px_x)}, {int(px_y)} px   ·   "
            f"normalisé: {norm_x:.3f}, {norm_y:.3f}")

    # ------------------------------------------------------------------
    # Écran simulé (résolution)
    # ------------------------------------------------------------------

    @Slot()
    def _maj_ecran(self):
        self.canvas.maj_taille_ecran(self.spin_largeur.value(),
                                     self.spin_hauteur.value())
        self.rafraichir_arbre()

    # ------------------------------------------------------------------
    # Sauvegarde / ouverture / génération de code
    # ------------------------------------------------------------------

    def _synchroniser_spins_ecran(self):
        l, h = self.canvas.taille_ecran()
        self.spin_largeur.blockSignals(True)
        self.spin_largeur.setValue(l)
        self.spin_largeur.blockSignals(False)
        self.spin_hauteur.blockSignals(True)
        self.spin_hauteur.setValue(h)
        self.spin_hauteur.blockSignals(False)

    @Slot()
    def save_projet(self):
        if self.scene is None:
            return
        if self.chemin_projet is None:
            self.save_projet_sous()
            return
        definir_base_projet(self.chemin_projet)
        sauvegarder_fichier(self.scene, self.chemin_projet)
        self.statusBar().showMessage(
            f"Projet enregistré: {self.chemin_projet}", 4000)

    @Slot()
    def save_projet_sous(self):
        if self.scene is None:
            return
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le projet UI sous",
            self.chemin_projet or "interface.json",
            "Projet UI (*.json)")
        if not chemin:
            return
        self.chemin_projet = chemin
        definir_base_projet(chemin)
        sauvegarder_fichier(self.scene, chemin)
        self.statusBar().showMessage(
            f"Projet enregistré sous: {self.chemin_projet}", 4000)

    @Slot()
    def open_projet(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un projet UI", "", "Projet UI (*.json)")
        if not chemin:
            return
        self._ouvrir_projet(chemin)

    def _ouvrir_projet(self, chemin):
        """Ouvre un projet UI depuis un fichier (dialogue ou dépôt)."""
        try:
            self.scene = charger_fichier(chemin)
        except (OSError, ValueError) as e:
            self.statusBar().showMessage(
                f"Impossible d'ouvrir le projet {chemin}: {e}", 6000)
            return
        self.chemin_projet = chemin
        definir_base_projet(chemin)
        self.canvas.definir_scene(self.scene)
        self._synchroniser_spins_ecran()
        self.rafraichir_arbre()
        self.rafraichir_inspecteur()
        self._maj_status()
        self.statusBar().showMessage(f"Projet ouvert: {chemin}", 4000)

    @Slot()
    def generer_fichier(self):
        if self.scene is None:
            return
        defaut = ("interface.py"
                  if not self.chemin_projet
                  else os.path.splitext(
                      os.path.basename(self.chemin_projet))[0] + ".py")
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Générer le script BGUI sous", defaut,
            "Script Python (*.py)")
        if not chemin:
            return
        sauvegarder_script(self.scene, chemin)
        self.statusBar().showMessage(
            f"Script généré: {chemin}", 4000)

    def _confirmer_perte(self, action):
        """Demande de sauvegarder avant de perdre le projet courant.

        Retourne ``True`` pour continuer, ``False`` pour annuler. Propose
        trois choix : Enregistrer (puis continuer), Ne pas enregistrer,
        Annuler.
        """
        if self.scene is None or self.scene_vierge_non_modifie():
            return True
        reponse = QMessageBox.question(
            self, "Projet non enregistré",
            f"Voulez-vous enregistrer le projet courant avant de {action} ?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save)
        if reponse == QMessageBox.Cancel:
            return False
        if reponse == QMessageBox.Save:
            self.save_projet()
            if self.chemin_projet is None:
                # Annulé à l'enregistrement sous
                return False
        return True

    def scene_vierge_non_modifie(self):
        """Le projet n'a rien à perdre (vierge et non modifié)."""
        return (self.scene is not None
                and not self.scene.enfants
                and self.chemin_projet is None)

    @Slot()
    def nouveau_projet(self):
        """Crée une interface vierge, après confirmation si besoin."""
        if not self._confirmer_perte("créer un nouveau fichier"):
            return
        self.scene = scene_vide()
        self.chemin_projet = None
        self.canvas.definir_scene(self.scene)
        self.canvas.definir_selection(None)
        self._synchroniser_spins_ecran()
        self.rafraichir_arbre()
        self.rafraichir_inspecteur()
        self._maj_status()
        self.statusBar().showMessage("Nouveau fichier créé", 4000)

    @Slot()
    def quitter(self):
        """Quitte l'éditeur, après confirmation si le projet est modifié."""
        if not self._confirmer_perte("quitter l'éditeur"):
            return
        self.close()

    # ------------------------------------------------------------------
    # Alias conservés pour compatibilité (panneaux de l'éditeur)
    # ------------------------------------------------------------------

    def bgui_widget(self):
        self.statusBar().showMessage("Palette de widgets: barre d'outils", 3000)

    def bgui_outliner(self):
        self.rafraichir_arbre()

    def bgui_scrren(self):
        self.canvas.rafraichir()

    def bgui_proprieter(self):
        self.rafraichir_inspecteur()

    def bgui_info(self):
        self.rafraichir_inspecteur()
        self.rafraichir_arbre()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    fenetre = LoposUIeditor()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()