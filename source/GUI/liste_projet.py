import os, sys, platform, pprint, pathlib, json, subprocess

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton,
    QListWidgetItem, QMessageBox, QHBoxLayout, QTreeWidget,
    QSizePolicy, QLabel, QListView, QScrollArea
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Slot, Qt
from pathlib import Path

from Fonction.manipuler_donner import charger, config, global_json, sauvegarder_config

class Lprojet(QWidget):
    def __init__(self):
        super().__init__()
        self.projets = {}  # Dictionnaire pour stocker les projets par onglet
        layout = QVBoxLayout()
        self.tableau = QTabWidget(self)

        # Charger les projets dès l'initialisation
        if platform.system() == "Linux": self.charger_tableau(charger("config_launcher")["linux"], "linux")
        self.charger_tableau(charger("config_launcher")["windows"], "windows")
        
        # Ajouter le bouton "Recharger la liste"
        self.b_recharger = QPushButton("Recharger la liste")
        self.b_recharger.clicked.connect(self.recharger_liste)
        # Ajouter le bouton "supprimer projet"
        self.b_del_projet = QPushButton("Supprimer Projet")
        self.b_del_projet.clicked.connect(self.supprimer_projet)

        # ligne
        ligne1 = QHBoxLayout()
        ligne1.addWidget(self.b_recharger)
        ligne1.addWidget(self.b_del_projet)
        # colone
        layout.addWidget(self.tableau)
        layout.addLayout(ligne1)
        self.setLayout(layout)

    def charger_tableau(self, tabeau, district):
        try:
            projets = tabeau  # Charger les projets pour l'onglet spécifié
        except Exception as e:
            print(f"Erreur lors du chargement des projets : {e}")
            return

        # Créer un QListWidget pour chaque version
        for version in projets["projet"]:
            page = QListWidget()
            self.projets[version] = []  # Initialiser la liste des projets pour cette version
            
            # Ajouter les projets existants de cette version
            for projet in projets["projet"][version]:
                if os.path.exists(projet):
                    if projet:
                        self.projets[version].append(projet)  # Ajouter le projet à la liste
                        item = page.addItem(Path(projet).name)  # Ajouter le nom du projet au QListWidget
                        chemin_projet = Path(projet).parent
                        page.itemClicked.connect(lambda item=item, chemin=chemin_projet: self.projet_selectionner(item, chemin))
                    # Ajouter l'onglet avec le nom de la version
                    self.tableau.addTab(page, QIcon(charger("config_launcher")["icon"][district]), f"{version} {district}")

    @Slot()
    def projet_selectionner(self, item, chemin):
        projet_nom = item.text()
        dos = Path(chemin) / projet_nom
        info = {"p_actif": str(dos)}
        with open((config / global_json), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)

    @Slot()
    def recharger_liste(self):
        self.tableau.clear()  # Effacer les onglets existants
        self.projets.clear()  # Réinitialiser le dictionnaire des projets
        sauvegarder_config()
        # Recharger les projets
        if platform.system() == "Linux": self.charger_tableau(charger("config_launcher")["linux"], "linux")
        self.charger_tableau(charger("config_launcher")["windows"], "windows")

    @Slot()
    def supprimer_projet(self):
        selection = charger("global")
        if selection["p_actif"]:
            # Demander confirmation à l'utilisateur
            reponse = QMessageBox.question(
                self,
                "Confirmation de suppression",
                f"Êtes-vous sûr de vouloir supprimer définitivement le projet\n{selection['p_actif']} ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reponse == QMessageBox.Yes:
                try:
                    import shutil
                    shutil.rmtree(selection["p_actif"])
                    sauvegarder_config()
                    QMessageBox.information(self, "Succès", "Le projet a été supprimé avec succès.")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le projet {selection["p_actif"]}: {str(e)}")
                    return
            else:
                return
        
        index_courant = self.tableau.currentIndex()  # Sauvegarder l'index de l'onglet actif avant le rechargement
        self.recharger_liste()  # Recharger tous les projets
        # Rétablir l'index de l'onglet actif
        if index_courant != -1:
            self.tableau.setCurrentIndex(index_courant)


class Projet(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.data = None
        self.projets = None
        self.h_layout = QHBoxLayout()

        self.layout = QVBoxLayout()
        self.tableau = QTabWidget()

        self.h_layout.addLayout(self.layout)

        self.v_layout_tab = QVBoxLayout()
        edition_bouton = QHBoxLayout()

        b_creer_fichier = QPushButton("+Fichier")
        b_2 = QPushButton("ok")
        edition_bouton.addWidget(b_creer_fichier)
        edition_bouton.addWidget(b_2)

        self.v_layout_tab.addLayout(edition_bouton)
        self.v_layout_tab.addWidget(self.tableau)

        self.h_layout.addLayout(self.v_layout_tab)
        self.recharger_projet()

        self.setLayout(self.h_layout)

    def recharger_projet(self):
        self.data = charger("config_launcher")
        self.projets = []
        self.recup_donner()

    def recup_donner(self):
        data = []
        new_data = []
        if platform.system() == "Linux": data.append(("Linux", self.data.get("linux", None)))
        data.append(("Windows", self.data.get("windows", None)))
        # (os/logi-icon/version-logi/icone/nom-projet/titre-projet/version-projet/tester-le-projet/bouton-supprimer)
        donner = [None, None, None, None, None, None, None]
        for i in data:
            if i[0] in ["Linux", "Windows"]:
                for p in i[1]["projet"]:
                    for nom_projet in i[1]["projet"][p]:
                        donner = [
                            i[0].lower(), #0
                            None, #1
                            p, #2
                            self.data["icon"].get(p.lower()), #3
                            nom_projet, #4
                            None, #5
                            None, #6
                        ]
                        new_data.append(donner)
        self.projets = new_data
        self.afficher()
        self.page_tableau()

    def afficher(self):
        # Nettoyer les anciens widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        b_recharge = QPushButton("Recharger")
        b_recharge.clicked.connect(lambda: self.recharger_projet())
        self.layout.addWidget(b_recharge)

        scrol = QScrollArea()
        scrol.setWidgetResizable(True)
        conteneur = QWidget()
        v_layout = QVBoxLayout(conteneur)

        for i in self.projets:
            ligne_rang = QHBoxLayout()
            icone = QLabel()
            icone.setFixedSize(25, 25)
            if i[2] == "Range":
                pixmap = QPixmap(self.data.get("icon")["range"]).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = QPixmap(self.data.get("icon")[i[0]]).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icone.setPixmap(pixmap)
            bouton_actif = QPushButton(pathlib.Path(i[4]).name)
            bouton_actif.setStatusTip(f"Rendre Actif Projet {pathlib.Path(i[4]).name} !!!")
            bouton_actif.clicked.connect(lambda checked, actif=pathlib.Path(i[4]): self.defini_actif(valeur=actif))
            bouton_supprimer = QPushButton("X")
            bouton_supprimer.setStatusTip(f"Supprimer {pathlib.Path(i[4]).name} !!!")
            bouton_supprimer.setFixedWidth(20)
            bouton_supprimer.clicked.connect(lambda checked, texte=pathlib.Path(i[4]): self.supprimer_projet(valeur=texte))
            bouton_test = QPushButton("Test")
            bouton_test.setStatusTip(f"Tester le Projet {pathlib.Path(i[4]).name} !!!")
            bouton_test.clicked.connect(lambda checked, chemin=pathlib.Path(i[4]): self.test_le_projet(valeur=chemin))

            ligne_rang.addWidget(bouton_actif)
            ligne_rang.addWidget(QLabel(i[0].capitalize()))
            ligne_rang.addWidget(icone)
            ligne_rang.addWidget(QLabel(i[2]))
            ligne_rang.addWidget(bouton_test)
            ligne_rang.addWidget(bouton_supprimer)
            v_layout.addLayout(ligne_rang)
        v_layout.addStretch()
        scrol.setWidget(conteneur)
        self.layout.addWidget(scrol)

    def page_tableau(self):
        self.tableau.clear()
        """
        tab = [
            ("Fichier", QListWidget()),
            ("Arboressence", QListWidget()),
        ]

        for (categorie, page) in tab:
            self.tableau.addTab(page, categorie)
        self.donner_fichier()
        self.donner_arboressence()"""
        # Page Fichier reste un QListWidget
        self.page_fichier = QTabWidget()
        self.tableau.addTab(self.page_fichier, "Fichier")

        # Page Arborescence devient un QTabWidget imbriqué
        self.page_arbo = QTabWidget()
        self.tableau.addTab(self.page_arbo, "Arborescence")

        self.donner_fichier()
        self.donner_arboressence()

    def donner_fichier(self):
        try:
            projet_actif = pathlib.Path(charger("global").get("p_actif"))
        except:
            return
        self.page_fichier.clear()
        #####
        categories = [
            ("Blend/Range", ['**/*.blend', '**/*.blend@', '**/*.range']), # récupérer fichier blend
            ("Polices", ['**/*.ttf', '**/*.otf']), # récupérer fichier police (font)
            ("Images", ['**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.svg']), # récupérer fichier image
            ("Scripts", ['**/*.py', '**/*.txt']), # récupérer fichier script et texte
            ("Audio", ['**/*.mp3', '**/*.wav', '**/*.ogg']), # récupérer fichier son, audio et video
        ]
        #####
        for nom_cat, patterns in categories:
             page = QListWidget()
             fichiers_trouves = []
             for pattern in patterns:
                 fichiers_trouves += projet_actif.glob(pattern)

             for fiche in sorted(fichiers_trouves, key=lambda f: f.name):
                 page.addItem(fiche.name)

             if fichiers_trouves:
                 self.page_fichier.addTab(page, nom_cat)

    def donner_arboressence(self):
        #self.tableau.tabText(1)
        f_global = charger("global").get("p_actif")
        if not f_global or not Path(f_global).exists():
            return

        self.page_arbo.clear()  # Nettoyer les onglets imbriqués

        dossier_projet = Path(f_global) / "data"
        self._construire_onglets_arbo(self.page_arbo, dossier_projet)

    def _construire_onglets_arbo(self, tab_imbrique, dossier):
        """Crée un onglet par sous-répertoire dans le QTabWidget imbriqué."""
        for sous_dossier in sorted(dossier.iterdir()):
            if sous_dossier.is_dir():
                # Créer une QListWidget pour chaque sous-dossier
                page = QListWidget()
                for fichier in sorted(sous_dossier.iterdir()):
                    page.addItem(fichier.name)
                tab_imbrique.addTab(page, sous_dossier.name)

    @Slot()
    def supprimer_projet(self, valeur):
        reponse = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer définitivement le projet\n{pathlib.Path(valeur).name}\n{valeur} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reponse == QMessageBox.Yes:
            try:
                import shutil
                shutil.rmtree(valeur)
                sauvegarder_config()
                QMessageBox.information(self, "Succès", "Le projet a été supprimé avec succès.")
                self.recharger_projet()
            except Exception as e:
                QMessageBox.critical(self, "Erreur",
                                     f"Impossible de supprimer le projet {valeur}: {str(e)}")
                return
        else:
            return

    @Slot()
    def defini_actif(self, valeur):
        info = {"p_actif": str(valeur)}
        with open((config / global_json), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)
        self.page_tableau()

    @Slot()
    def test_le_projet(self, valeur):
        os = ["Windows", "Linux"]
        version = ["2x", "3x", "4x", "5x", "Range"]
        os_util = None
        version_utils = None
        fichier_main = None
        base_cle = None
        commande = []
        use_wine = False

        for i in os:
            if i in str(valeur).split("/"): os_util = i
        for i in version:
            if i in str(valeur).split("/"): version_utils = i

        if blend_principal := list(valeur.glob("**/*.blend")):
            fichier_main = blend_principal[0]
        elif range_principal := list(valeur.glob("**/*.range")):
            fichier_main = range_principal[0]
        else: return fichier_main

        config_moteur = charger("config_launcher")[os_util.lower()]
        if version_utils == "Range":
            if os_util == "Windows":
                use_wine = True
                base_cle = f"game-W-{version_utils}"
            if os_util == "Linux":
                use_wine = False
                base_cle = f"game-L-{version_utils}"
        else:
            if os_util == "Windows":
                use_wine = True
            else:
                use_wine = False
            base_cle = f"game-{version_utils}"

        if use_wine:
            commande.append("wine")
            fichier_main = "Z:" + str(fichier_main).replace("/", "\\")

        commande.append(config_moteur['executable'][base_cle])
        commande.append(fichier_main)

        subprocess.Popen(args=commande)
