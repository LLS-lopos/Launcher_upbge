import os, sys, platform, pprint, pathlib, json, subprocess

from GUI.Biblio.export_projet import Exportation

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
from PySide6.QtCore import QSize, Slot, Qt
from pathlib import Path

from Fonction.manipuler_donner import charger, config, global_json, sauvegarder_config
from GUI.liste_blend import Lblend
from GUI.struct_dossier import DosStructure

class Projet(QWidget):
    def __init__(self, parent=None, save=None):
        super().__init__()
        self.save = save
        self.lblend = None
        self.data = None
        self.projets = None
        self.h_layout = QHBoxLayout()

        self.layout = QVBoxLayout()
        self.tableau = QTabWidget()

        self.h_layout.addLayout(self.layout)

        self.v_layout_tab = QVBoxLayout()
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
            bouton_actif.setFixedWidth(40)
            bouton_actif.setStatusTip(f"Rendre Actif Projet {pathlib.Path(i[4]).name} !!!")
            bouton_actif.clicked.connect(lambda checked, actif=pathlib.Path(i[4]): self.defini_actif(valeur=actif))
            bouton_supprimer = QPushButton()
            bouton_supprimer.setFixedSize(30,30)
            bouton_supprimer.setIcon(QIcon(charger("config_launcher")["icon"]["Trash"]))
            bouton_supprimer.setIconSize(QSize(25,25))
            bouton_supprimer.setStatusTip(f"Supprimer {pathlib.Path(i[4]).name} !!!")
            bouton_supprimer.clicked.connect(lambda checked, texte=pathlib.Path(i[4]): self.supprimer_projet(valeur=texte))
            bouton_test = QPushButton()
            bouton_test.setFixedSize(30,30)
            bouton_test.setIcon(QIcon(charger("config_launcher")["icon"]["game"]))
            bouton_test.setIconSize(QSize(25,25))
            bouton_test.setStatusTip(f"Tester le Projet {pathlib.Path(i[4]).name} !!!")
            bouton_test.clicked.connect(lambda checked, chemin=pathlib.Path(i[4]): self.test_le_projet(valeur=chemin))
            bouton_export = QPushButton()
            bouton_export.setFixedSize(30,30)
            bouton_export.setIcon(QIcon(charger("config_launcher")["icon"]["export_projet"]))
            bouton_export.setIconSize(QSize(25,25))
            bouton_export.setStatusTip(f"Exporter projet {pathlib.Path(i[4]).name} !!!")
            bouton_export.clicked.connect(lambda checked, chemin=pathlib.Path(i[4]), os_util=i[0], ver=i[2]: self.exporter_projet(valeur=chemin, os_util=os_util, version_utils=ver))

            ligne_rang.addWidget(bouton_actif)
            ligne_rang.addWidget(QLabel(i[0].capitalize()))
            ligne_rang.addWidget(icone)
            ligne_rang.addWidget(QLabel(i[2]))
            ligne_rang.addWidget(bouton_test)
            ligne_rang.addWidget(bouton_supprimer)
            ligne_rang.addWidget(bouton_export)
            v_layout.addLayout(ligne_rang)
        v_layout.addStretch()
        scrol.setWidget(conteneur)
        self.layout.addWidget(scrol)

    def page_tableau(self):
        self.tableau.clear()

        if self.lblend is None:
            self.lblend = Lblend(self.save)
        self.tableau.addTab(self.lblend, "Fichier")

        self.page_arbo = DosStructure()
        self.tableau.addTab(self.page_arbo, "Arborescence")

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

    def exporter_projet(self, valeur, os_util, version_utils):
        config_moteur = charger("config_launcher")[os_util]
        chemin_mot = config_moteur['executable'].get(f"{os_util.capitalize()}-{version_utils}")
        if not chemin_mot:
            QMessageBox.critical(self, "Erreur", f"Chemin du moteur introuvable pour {os_util}-{version_utils}")
            return
        chemin_mot = str(pathlib.Path(chemin_mot).parent)

        self.export_projet = Exportation(projet=valeur, moteur=chemin_mot)
        if not self.export_projet._auto_exported:
            self.export_projet.show()