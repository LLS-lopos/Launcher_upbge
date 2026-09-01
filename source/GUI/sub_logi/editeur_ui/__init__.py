"""Package de l'éditeur UI BGUI : simulation d'écran et conception.

Modules :
- modele     : données (nœuds de widgets), catalogue BGUI, JSON
- theme_bgui : thème par défaut et rendu fidèle des widgets
- canvas     : simulation de l'écran (rendu, sélection, drag, resize)
"""

from .modele import (
    CATALOGUE, CHAMPS_DEDIES, OPTIONS_PAR_TYPE, TYPE_FRAME_BOUTON, TYPE_FRAME,
    TYPE_IMAGE, TYPE_LABEL, TYPE_SCREEN,
    NoeudUI, charger_fichier, nouveau_noeud, noeud_a_json, noeud_depuis_json,
    normalise_vers_px, prochain_nom, px_vers_normalise, sauvegarder_fichier,
    scene_exemple,
)
from .theme_bgui import (appliquer_theme, charger_theme_fichier,
                         definir_base_projet, lire_cfg_texte, lire_valeur,
                         peindre_widget, proprietes_depuis_donnees,
                         reinitialiser_theme, resoudre_proprietes,
                         resoudre_chemin_fichier, sauvegarder_theme_fichier,
                         sous_themes_disponibles, theme_defaut_en_texte,
                         theme_en_texte)
from .canvas import CanvasBGUI
from .generateur_script import (classe_calque, etat_calque, nom_python,
                                sauvegarder_script, script_ui_en_texte)

__all__ = [
    "CATALOGUE", "CHAMPS_DEDIES", "OPTIONS_PAR_TYPE", "TYPE_FRAME_BOUTON",
    "TYPE_FRAME", "TYPE_IMAGE", "TYPE_LABEL",
    "TYPE_SCREEN", "NoeudUI", "CanvasBGUI", "appliquer_theme",
    "charger_fichier", "charger_theme_fichier", "definir_base_projet",
    "lire_cfg_texte", "lire_valeur", "noeud_a_json", "noeud_depuis_json",
    "normalise_vers_px", "peindre_widget", "prochain_nom",
    "proprietes_depuis_donnees", "px_vers_normalise", "reinitialiser_theme",
    "resoudre_proprietes", "resoudre_chemin_fichier",
    "sauvegarder_fichier", "sauvegarder_theme_fichier", "scene_exemple",
    "sous_themes_disponibles", "theme_defaut_en_texte", "theme_en_texte",
    "classe_calque", "etat_calque", "nom_python", "sauvegarder_script",
    "script_ui_en_texte",
]