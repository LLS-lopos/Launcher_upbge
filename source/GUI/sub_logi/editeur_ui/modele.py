"""Modèle de données de l'éditeur UI BGUI.

Un fichier de conception est un arbre de nœuds — l'équivalent des widgets
BGUI (Screen, Frame, Label, Button, Image...). Chaque nœud possède un type,
un nom, des propriétés (dict) et une liste d'enfants.

Les coordonnées sont stockées **normalisées (0..1)**, relatives au parent,
comme BGUI l'attend : **l'origine (0,0) est en bas à gauche**, y croît vers le
haut, et `pos` désigne le coin bas-gauche du widget (il s'étend en x vers la
droite et en y vers le haut). L'affichage les convertit en pixels pour la
simulation (voir canvas.py).

La sérialisation se fait en JSON simple, compatible avec la structure des
fichiers de conception du lanceur.
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Types de widgets supportés par l'éditeur (sous-ensemble de BGUI)
# ---------------------------------------------------------------------------

TYPE_SCREEN = "Screen"
TYPE_LABEL = "Label"
TYPE_FRAME = "Frame"
TYPE_FRAME_BOUTON = "Button"
TYPE_IMAGE = "Image"
TYPE_BOUTON_IMAGE = "ImageButton"
TYPE_LISTE = "ListBox"
TYPE_BARRE_PROGRES = "ProgressBar"
TYPE_BLOC_TEXTE = "TextBlock"
TYPE_SAISIE_TEXTE = "TextInput"
TYPE_VIDEO = "Video"

# Nom du calque de base d'un écran : il existe toujours, en premier, et ne
# peut ni être renommé ni supprimé.
CALQUE_BASE = "start"

# Callbacks BGUI du widget de base (info_bgui_option.md → « callbacks »). Ce
# sont les déclencheurs d'événements proposés dans la section « Fonctions »
# de l'inspecteur (façon Godot : un déclencheur est relié à une fonction).
DECLENCHEURS_EVENEMENTS = (
    "on_click",
    "on_release",
    "on_hover",
    "on_mouse_enter",
    "on_mouse_exit",
    "on_active",
)

# Types de propriétés custom d'un écran (source : Scripts/proprieter_screen.md).
# Les types bpy.type.* désignent des références Blender/UPBGE.
TYPES_PROPRIETE = [
    "float()", "int()", "str()", "bool()",
    "vector 2D", "vector 3D", "vector 4D",
    "list",
    "RGBA", "tuple image",
    "bpy.type.Action", "bpy.type.Armature", "bpy.type.Camera",
    "bpy.type.Collection", "bpy.type.Curve", "bpy.type.Image",
    "bpy.type.Key", "bpy.type.Library", "bpy.type.Light",
    "bpy.type.Material", "bpy.type.Mesh", "bpy.type.MovieClip",
    "bpy.type.NodeTree", "bpy.type.Object", "bpy.type.ParticleSettings",
    "bpy.type.Sound", "bpy.type.Speaker", "bpy.type.Text",
    "bpy.type.Texture", "bpy.type.VectorFont", "bpy.type.Volume",
    "bpy.type.World",
]


def valeur_defaut_propriete(type_propriete):
    """Valeur par défaut d'une propriété en fonction de son type."""
    if type_propriete == "float()":
        return 0.0
    if type_propriete == "int()":
        return 0
    if type_propriete == "str()":
        return ""
    if type_propriete == "bool()":
        return False
    if type_propriete == "vector 2D":
        return [0.0, 0.0]
    if type_propriete == "vector 3D":
        return [0.0, 0.0, 0.0]
    if type_propriete == "vector 4D":
        return [0.0, 0.0, 0.0, 0.0]
    if type_propriete == "list":
        return ""
    if type_propriete == "RGBA":
        return (1.0, 1.0, 1.0, 1.0)
    if type_propriete == "tuple image":
        return (None, 0, 0, 1, 1)
    return ""  # bpy.type.* -> référence encore non définie


def libelle_type_propriete(type_propriete):
    """Étiquette courte affichée pour un type de propriété.

    - ``list``      -> ``enum()`` (enum BGUI généré depuis la liste)
    - ``bpy.type.X`` -> ``objet · type: X`` (référence vers un objet UPBGE)
    - autres types  -> le type tel quel (``str()``, ``float()``...)
    """
    if type_propriete == "list":
        return "enum()"
    if type_propriete.startswith("bpy.type."):
        return "objet · type: " + type_propriete.split(".", 2)[2]
    return type_propriete


def description_type_propriete(type_propriete):
    """Description complète d'un type (affichée en infobulle)."""
    if type_propriete == "list":
        return ("enum() : éléments séparés par des virgules en édition ;\n"
                "génère une propriété enum {\"a\", \"b\", ...} à l'écran.")
    if type_propriete == "RGBA":
        return ("RGBA : couleur r, g, b, a (floats 0..1).\n"
                "Ex. : 1, 0.7, 0.1, 1")
    if type_propriete == "tuple image":
        return ("tuple image : None, x, y, w, h\n"
                "(None, 0, 0, 1, 1) = image entière.")
    if type_propriete.startswith("bpy.type."):
        return "objet · type: " + type_propriete.split(".", 2)[2]
    return f"{type_propriete} : propriété {type_propriete}"

# Propriétés communes à tous les widgets (hors racine Screen).
# Coordonnées BGUI : origine (0,0) en bas à gauche, y croît vers le haut.
PROP_BASE = {
    "pos": [0.0, 0.0],          # coin bas-gauche, normalisé 0..1 relatif au parent
    "size": [1.0, 1.0],         # taille normalisée 0..1 relative au parent
    "visible": True,            # widget affiché ou non
    "z_index": 0,               # ordre de dessin (plus haut = au-dessus)
    "sub_theme": "",            # sous-thème BGUI (classe CSS équivalente)
    "frozen": False,            # le widget accepte ou non les événements
    "options": 0,               # drapeaux BGUI (BGUI_CENTERX, BGUI_CACHE…)
}

# Options disponibles des widgets (source : Scripts/info_bgui_option.md,
# sections « option code »). ``sub_theme`` en est volontairement exclu : il
# se définit via le champ dédié de l'inspecteur (voir _champ_sub_theme).
# ``aspect`` (contrainte de ratio) : présent sur tous les widgets SAUF le
# Label (BGUI n'en accepte pas dans sa signature). Défaut 0.0 = aucune
# contrainte ; sinon la largeur est dérivée de la hauteur : largeur = hauteur
# × aspect (formule BGUI, cf. bgui/widget.py).
OPTIONS_PAR_TYPE = {
    TYPE_FRAME: {
        "border": 0,                       # bordure (0 = thème)
        "aspect": 0.0,                     # contrainte de ratio
        "border_color": [0.0, 0.0, 0.0, 1.0],
    },
    TYPE_FRAME_BOUTON: {
        "font": "",
        "aspect": 0.0,
        "color": [1.0, 1.0, 1.0, 1.0],     # couleur du texte
    },
    TYPE_IMAGE: {
        "img": "",
        "aspect": 0.0,
        "texco": [0.0, 0.0, 1.0, 1.0],     # coordonnées UV
        "color": [1.0, 1.0, 1.0, 1.0],     # teinte du plan
    },
    TYPE_BOUTON_IMAGE: {
        "aspect": 0.0,
        "default2_image": "",
        "hover_image": "",
        "click_image": "",
    },
    TYPE_LABEL: {
        "font": "",
        "outline_color": [0.0, 0.0, 0.0, 1.0],
        "outline_size": 0,
        "outline_smoothing": False,
    },
    TYPE_LISTE: {
        "padding": 0,
        "aspect": 0.0,
    },
    TYPE_BARRE_PROGRES: {
        "aspect": 0.0,
    },
    TYPE_BLOC_TEXTE: {
        "font": "",
        "overflow": 0,                     # BGUI_OVERFLOW_*
        "aspect": 0.0,
    },
    TYPE_SAISIE_TEXTE: {
        "font": "",
        "aspect": 0.0,
    },
    TYPE_VIDEO: {
        "play_audio": True,
        "repeat": -1,                      # -1 = boucle infinie
        "aspect": 0.0,
        "start": 0.0,                      # début de lecture (s ou image)
        "end": 100.0,                      # fin de lecture (s ou image)
        "use_frames": True,                # start/end exprimés en images
        "fps": 30,                         # utilisé si use_frames
    },
    TYPE_SCREEN: {},
}

# Champs déjà édités par un contrôle dédié de l'inspecteur : ils ne sont
# pas répétés dans la section « Options BGUI ».
CHAMPS_DEDIES = {
    TYPE_FRAME: {"color"},
    TYPE_FRAME_BOUTON: {"text", "pt_size", "base_color", "color"},
    TYPE_IMAGE: {"fichier"},
    TYPE_BOUTON_IMAGE: {"fichier", "default2_image", "hover_image",
                        "click_image"},
    TYPE_LABEL: {"text", "pt_size", "color"},
    TYPE_LISTE: {"items", "selected"},
    TYPE_BARRE_PROGRES: {"percent"},
    TYPE_BLOC_TEXTE: {"text", "color"},
    TYPE_SAISIE_TEXTE: {"text", "pt_size", "prefix", "color"},
    TYPE_VIDEO: {"fichier"},
    TYPE_SCREEN: set(),
}

# Catalogue des types : propriétés par défaut, préfixe d'auto-nommage et
# taille "raisonnable" proposée à la création.
CATALOGUE = {
    TYPE_SCREEN: {
        "prefixe": "ecran",
        "defaut": {"res": [1280, 720]},
    },
    TYPE_LABEL: {
        "prefixe": "label",
        "defaut": {
            "text": "Label",
            "pt_size": 30,
        },
        "taille": [0.2, 0.06],
    },
    TYPE_FRAME: {
        "prefixe": "cadre",
        "defaut": {},
        "taille": [0.5, 0.5],
    },
    TYPE_FRAME_BOUTON: {
        "prefixe": "bouton",
        "defaut": {
            "text": "Bouton",
            "pt_size": 30,
        },
        "taille": [0.25, 0.09],
    },
    TYPE_IMAGE: {
        "prefixe": "image",
        "defaut": {"fichier": ""},
        "taille": [0.3, 0.2],
    },
    TYPE_BOUTON_IMAGE: {
        "prefixe": "bouton_image",
        "defaut": {"fichier": ""},
        "taille": [0.3, 0.2],
    },
    TYPE_LISTE: {
        "prefixe": "liste",
        "defaut": {
            "items": ["élément 1", "élément 2", "élément 3"],
            "selected": 0,
            "pt_size": 22,
        },
        "taille": [0.3, 0.4],
    },
    TYPE_BARRE_PROGRES: {
        "prefixe": "barre_progres",
        "defaut": {"percent": 0.5},
        "taille": [0.4, 0.06],
    },
    TYPE_BLOC_TEXTE: {
        "prefixe": "bloc_texte",
        "defaut": {"text": "Bloc de texte", "pt_size": 24},
        "taille": [0.5, 0.3],
    },
    TYPE_SAISIE_TEXTE: {
        "prefixe": "saisie",
        "defaut": {"text": "", "prefix": "» ", "pt_size": 24},
        "taille": [0.4, 0.08],
    },
    TYPE_VIDEO: {
        "prefixe": "video",
        "defaut": {"fichier": ""},
        "taille": [0.5, 0.3],
    },
}


class NoeudUI:
    """Un nœud de l'arbre de conception (équivalent d'un widget BGUI)."""

    def __init__(self, type, nom=None, prop=None, enfants=None, proprietes=None):
        self.type = type
        self.nom = nom or type.lower()
        self.parent = None
        self.prop = dict(PROP_BASE)
        self.prop.update(OPTIONS_PAR_TYPE.get(type, {}))
        self.prop.update(CATALOGUE.get(type, {}).get("defaut", {}))
        if prop:
            self.prop.update(prop)
        #: Snapshot des valeurs à la création. Le cfg fournit la base : une
        #: clé n'est « définie par le code » que si elle diffère de ce snapshot
        #: et de la valeur cfg courante (cf. noeud_defini).
        self.init_prop = dict(self.prop)
        self.enfants = list(enfants) if enfants is not None else []
        for enfant in self.enfants:
            enfant.parent = self
        self.proprietes = proprietes if proprietes is not None else []
        self.calques = [CALQUE_BASE]    # nom des calques (Significatif sur Screen)
        #: Événements déclencheurs du widget (section « Fonctions » de
        #: l'inspecteur) : liste de ``{"declencheur", "fonction"}``.
        self.evenements = []
        #: Corps de la « Mise à jour » du widget : lignes de code injectées
        #: dans ``Layout.update()`` (exécutées à chaque frame).
        self.update_code = []

    def __repr__(self):
        return f"NoeudUI(type={self.type!r}, nom={self.nom!r}, enfants={len(self.enfants)})"


def attacher(noeud, parent):
    """Attache ``noeud`` comme enfant de ``parent`` (met à jour ``parent``).

    Équivalent à ``parent.enfants.append(noeud)`` en conservant la
    référence `parent` du nœud — utilisée par le générateur de code.
    """
    noeud.parent = parent
    parent.enfants.append(noeud)


def detacher(noeud):
    """Détache ``noeud`` de son parent (retire de ``enfants``)."""
    if noeud.parent is not None:
        noeud.parent.enfants.remove(noeud)
    noeud.parent = None


def reparenter(noeud, nouveau_parent, calque=None):
    """Change le parent d'un widget (le déplace dans l'arbre).

    ``calque`` : nom du calque à assigner si le nouveau parent est le Screen
    (sinon la clé ``calque`` est retirée : seuls les enfants directs d'un
    Screen sont regroupés par calque). Retourne ``True`` si le déplacement a
    réellement eu lieu (parents différents).
    """
    if noeud.parent is nouveau_parent:
        return False
    detacher(noeud)
    if nouveau_parent.type == TYPE_SCREEN:
        if calque:
            noeud.prop["calque"] = calque
        else:
            noeud.prop.pop("calque", None)
    else:
        noeud.prop.pop("calque", None)
    attacher(noeud, nouveau_parent)
    return True


def _valeur_egale(a, b):
    """Égalité « sémantique » entre valeurs de propriété (listes/tuples/floats).

    Compare les contenus plutôt que les types : ``(1, 1, 1, 1)`` ==
    ``[1, 1, 1, 1]``, et tolère les écarts flottants infimes.
    """
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)):
            return False
        if len(a) != len(b):
            return False
        return all(_valeur_egale(x, y) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 1e-6
        except (TypeError, ValueError):
            return False
    return a == b


def noeud_defini(noeud, cle, cfg=None):
    """Une valeur a-t-elle été explicitement définie par le code (widget) ?

    Le cfg généré sert de base. Une valeur de widget n'est donc « définie par
    le code » que si elle diffère **à la fois** de sa valeur d'initialisation
    (valeur égale à l'initiale ⇒ jamais modifiée ⇒ cfg gouverne) **et** de la
    valeur cfg courante du paramètre équivalent (si ``cfg`` est fourni :
    valeur égale au cfg ⇒ cfg gouverne).

    Une valeur modifiée puis remise à la valeur initiale ou à la valeur cfg
    redevient ainsi gouvernée par le thème. Sans ``cfg`` (clé sans équivalent
    de thème), seule l'initialisation sert de référence ; une clé absente du
    snapshot d'initialisation (ex. une couleur posée après création) est
    considérée définie.
    """
    if cle not in noeud.prop:
        return False
    if (cle in noeud.init_prop
            and _valeur_egale(noeud.prop[cle], noeud.init_prop[cle])):
        return False
    if cfg is not None and _valeur_egale(noeud.prop[cle], cfg):
        return False
    return True


def nouveau_noeud(type, nom=None):
    """Crée un nœud du type donné avec ses propriétés par défaut."""
    return NoeudUI(type, nom)


def est_conteneur(noeud):
    """Tout widget (et le Screen) peut contenir d'autres widgets."""
    return True


def prochain_nom(racine, type):
    """Trouve un nom unique pour un nouveau widget du type donné.

    Exemple : bouton_1, bouton_2... en comptant les nœuds existants qui
    utilisent déjà le même préfixe.
    """
    prefixe = CATALOGUE.get(type, {}).get("prefixe", type.lower())

    def compter(n):
        total = 0
        for e in n.enfants:
            if e.type == type and e.nom.startswith(f"{prefixe}_"):
                suffixe = e.nom[len(prefixe) + 1 :]
                if suffixe.isdigit():
                    total = max(total, int(suffixe))
        for e in n.enfants:
            total = max(total, compter(e))
        return total

    return f"{prefixe}_{compter(racine) + 1}"


# ---------------------------------------------------------------------------
# Calques d'affichage (screens/menus d'un Screen)
# ---------------------------------------------------------------------------

def calques_ecran(noeud):
    """Noms des calques d'un Screen, dans l'ordre ; le premier est la base.

    Un Screen peut définir plusieurs affichages (menus) : chaque affichage
    est un « calque » nommé qui regroupe une partie des enfants directs de
    l'écran. Le calque de base s'appelle ``start`` au départ (et le premier
    calque ne peut pas être supprimé), mais il peut être renommé.
    """
    calques = list(getattr(noeud, "calques", None) or [])
    if not calques:
        calques = [CALQUE_BASE]
    return calques


def calque_de(noeud, base=None):
    """Nom du calque d'un widget (``base`` par défaut si non précisé).

    ``base`` : nom du calque de base — utilisé pour les widgets non
    assignés (aucune propriété ``calque``) ; vaut ``start`` si omis.
    """
    return noeud.prop.get("calque", base if base is not None else CALQUE_BASE)


def enfants_calque(noeud, calque):
    """Enfants directs d'un Screen appartenant au calque donné."""
    base = calques_ecran(noeud)[0]
    return [e for e in noeud.enfants if calque_de(e, base) == calque]


def prochain_calque(calques):
    """Trouve un nom de calque libre : calque_1, calque_2..."""
    rang = 1
    while f"calque_{rang}" in calques:
        rang += 1
    return f"calque_{rang}"


def ajouter_calque(noeud, nom=None):
    """Crée un calque sur un écran et retourne son nom (unique).

    Sans ``nom``, un nom automatique ``calque_N`` est choisi. Aucun nom
    n'est réservé : « start » peut même être créé si le calque de base a
    été renommé.
    """
    calques = calques_ecran(noeud)
    if nom is not None:
        nom = nom.strip()
    nom = nom or prochain_calque(calques)
    if nom not in calques:
        calques.append(nom)
        noeud.calques = list(calques)
    return nom


def renommer_calque(noeud, ancien, nouveau):
    """Renomme un calque (y compris le calque de base) ; ses widgets suivent.

    Retourne ``True`` si le renommage a eu lieu (nom unique, non vide).
    """
    nouveau = nouveau.strip()
    calques = calques_ecran(noeud)
    if (nouveau == ancien or not nouveau
            or ancien not in calques or nouveau in calques):
        return False
    base = calques[0]
    noeud.calques = [nouveau if c == ancien else c for c in calques]
    for enfant in noeud.enfants:
        if calque_de(enfant, base) == ancien:
            enfant.prop["calque"] = nouveau
    return True


def retirer_calque(noeud, nom):
    """Supprime un calque autre que le calque de base (le premier).

    Tous les widgets du calque sont supprimés avec lui.
    Retourne ``True`` si la suppression a eu lieu.
    """
    calques = calques_ecran(noeud)
    if (nom not in calques or len(calques) <= 1
            or nom == calques[0]):
        return False
    base = calques[0]
    noeud.calques = [c for c in calques if c != nom]
    noeud.enfants = [e for e in noeud.enfants
                     if calque_de(e, base) != nom]
    return True


# ---------------------------------------------------------------------------
# Conversions pixels <-> normalisé (par rapport à la taille d'un parent)
# ---------------------------------------------------------------------------

def px_vers_normalise(valeur_px, taille_parent_px):
    """Convertit une grandeur en pixels vers la valeur normalisée 0..1."""
    if taille_parent_px and taille_parent_px > 0:
        return valeur_px / taille_parent_px
    return 0.0


def normalise_vers_px(valeur, taille_parent_px):
    """Convertit une valeur normalisée 0..1 vers des pixels."""
    return valeur * taille_parent_px


# ---------------------------------------------------------------------------
# Sérialisation JSON
# ---------------------------------------------------------------------------

def noeud_a_json(noeud):
    """Sérialise un nœud (et ses descendants) en dictionnaire JSON."""
    donnees = {
        "type": noeud.type,
        "nom": noeud.nom,
        "prop": dict(noeud.prop),
        "proprietes": [dict(p) for p in noeud.proprietes],
        "enfants": [noeud_a_json(e) for e in noeud.enfants],
    }
    if noeud.evenements:
        donnees["evenements"] = [dict(e) for e in noeud.evenements]
    if getattr(noeud, "update_code", None):
        donnees["update_code"] = list(noeud.update_code)
    if noeud.type == TYPE_SCREEN:
        donnees["calques"] = list(calques_ecran(noeud))
    return donnees


def noeud_depuis_json(donnees):
    """Reconstruit un nœud depuis un dictionnaire JSON."""
    noeud = NoeudUI(donnees.get("type", TYPE_LABEL),
                    donnees.get("nom"),
                    donnees.get("prop"))
    # Données chargées = décisions du concepteur, mais une valeur égale à la
    # valeur cfg courante reste gouvernée par le thème (règle « base == cfg ») ;
    # init_prop vide = toutes les clés comparées au cfg fourni par le rendu.
    noeud.init_prop = {}
    calques = donnees.get("calques")
    if calques:
        noeud.calques = [str(c) for c in calques]
    noeud.enfants = [noeud_depuis_json(e) for e in donnees.get("enfants", [])]
    for enfant in noeud.enfants:
        enfant.parent = noeud
    noeud.proprietes = [dict(p) for p in donnees.get("proprietes", [])]
    noeud.evenements = [dict(e) for e in donnees.get("evenements", [])]
    noeud.update_code = [str(l) for l in donnees.get("update_code", [])]
    return noeud


# ---------------------------------------------------------------------------
# Scène d'exemple : permet de valider la simulation immédiatement
# ---------------------------------------------------------------------------

def scene_vide():
    """Construit un écran vierge : un Screen avec le seul calque ``start``,
    sans aucun widget. Sert de scène initiale à l'ouverture du programme.

    Définit par défaut la propriété écran ``cfg`` (objet ``bpy.types.Text``,
    chemine vers le dossier du theme.cfg) utilisée par le script généré.
    """
    racine = nouveau_noeud(TYPE_SCREEN, "ecran")
    racine.prop["res"] = [1280, 720]
    racine.proprietes = [{"nom": "cfg", "type": "bpy.type.Text",
                          "valeur": ""}]
    return racine


def scene_exemple():
    """Construit une petite interface type « menu de jeu » prête à simuler.

    Coordonnées BGUI : l'origine (0,0) est en bas à gauche et y croît vers le
    haut — une valeur y élevée place donc le widget vers le haut de l'écran.
    """
    racine = nouveau_noeud(TYPE_SCREEN, "ecran")
    racine.prop["res"] = [1280, 720]

    score = nouveau_noeud(TYPE_LABEL, "score")
    score.prop["pos"] = [0.04, 0.91]
    score.prop["size"] = [0.18, 0.05]
    score.prop["text"] = "Score: 0"
    score.prop["pt_size"] = 24
    attacher(score, racine)

    cadre = nouveau_noeud(TYPE_FRAME, "menu_principal")
    cadre.prop["pos"] = [0.3, 0.35]
    cadre.prop["size"] = [0.4, 0.3]
    cadre.prop["color"] = [0.25, 0.28, 0.34, 1.0]
    attacher(cadre, racine)

    titre = nouveau_noeud(TYPE_LABEL, "titre")
    titre.prop["pos"] = [0.1, 0.72]
    titre.prop["size"] = [0.8, 0.2]
    titre.prop["text"] = "Mon interface"
    titre.prop["pt_size"] = 34
    attacher(titre, cadre)

    for nom, texte, y in [("jouer", "Jouer", 0.46),
                          ("options", "Options", 0.28),
                          ("quitter", "Quitter", 0.10)]:
        bouton = nouveau_noeud(TYPE_FRAME_BOUTON, nom)
        bouton.prop["pos"] = [0.25, y]
        bouton.prop["size"] = [0.5, 0.16]
        bouton.prop["text"] = texte
        attacher(bouton, cadre)

    return racine


def sauvegarder_fichier(racine, chemin):
    """Sauvegarde une scène au format JSON de conception."""
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(noeud_a_json(racine), f, indent=2)


def charger_fichier(chemin):
    """Charge une scène depuis un fichier JSON de conception."""
    with open(chemin, encoding="utf-8") as f:
        return noeud_depuis_json(json.load(f))


# ----------------------------------------------------------------------
# Valeurs de propriétés au format theme.cfg
# ----------------------------------------------------------------------

def valeur_depuis_texte(texte):
    """Convertit le texte d'une valeur cfg en type Python.

    - ``r, g, b, a``          -> tuple de floats (couleur RGBA)
    - ``None, x, y, w, h``    -> tuple débutant par None (image/uv)
    - ``(r, g, b, a)``        -> parenthèses tolérées, ignorées
    - ``True``/``False``      -> booléen
    - valeur numérique        -> int ou float
    - chaine vide             -> ``""``
    - sinon                   -> texte tel quel (séparateurs conservés)
    """
    texte = texte.strip()
    if texte.startswith("(") and texte.endswith(")"):
        texte = texte[1:-1].strip()
    morceaux = [m.strip() for m in texte.split(",")] if texte else []
    if len(morceaux) > 1:
        if morceaux[0].lower() == "none":
            try:
                return (None,) + tuple(float(m) for m in morceaux[1:])
            except ValueError:
                return ", ".join(morceaux)
        try:
            return tuple(float(m) for m in morceaux)
        except ValueError:
            return ", ".join(morceaux)
    if len(morceaux) == 1 and morceaux[0].lower() in ("true", "false"):
        return morceaux[0].lower() == "true"
    if len(morceaux) == 1:
        try:
            return int(morceaux[0])
        except ValueError:
            try:
                return float(morceaux[0])
            except ValueError:
                return texte
    return texte


def valeur_vers_texte(valeur):
    """Convertit une valeur Python en texte de clé cfg."""
    if isinstance(valeur, bool):
        return "True" if valeur else "False"
    if isinstance(valeur, (tuple, list)):
        return ", ".join(
            "None" if m is None else f"{m:g}" if isinstance(m, float)
            else str(m) for m in valeur)
    if isinstance(valeur, float):
        return f"{valeur:g}"
    return str(valeur)


def inferer_type_propriete(valeur):
    """Déduit un type de propriété (clé de TYPES_PROPRIETE) depuis une
    valeur analysée par :func:`valeur_depuis_texte`."""
    if isinstance(valeur, bool):
        return "bool()"
    if isinstance(valeur, int):
        return "int()"
    if isinstance(valeur, float):
        return "float()"
    if isinstance(valeur, (tuple, list)) and valeur:
        if isinstance(valeur[0], (int, float)):
            if isinstance(valeur[0], bool):
                return "list"
            if len(valeur) == 2:
                return "vector 2D"
            if len(valeur) == 3:
                return "vector 3D"
            if len(valeur) == 4:
                return "RGBA"
        if len(valeur) == 5 and valeur[0] is None:
            return "tuple image"
        return "list"
    return "str()"


def valeur_typee_propriete(propriete):
    """Valeur d'une propriété convertie selon son type.

    Les types texte (str(), list, RGBA, tuple image, bpy.type.*) sont
    analysés comme dans theme.cfg ; les types numériques/vecteurs sont
    convertis directement.
    """
    type_propriete = propriete["type"]
    valeur = propriete.get("valeur")
    if type_propriete == "bool()":
        return bool(valeur)
    if type_propriete == "int()":
        try:
            return int(valeur)
        except (TypeError, ValueError):
            return valeur
    if type_propriete == "float()":
        try:
            return float(valeur)
        except (TypeError, ValueError):
            return valeur
    if type_propriete.startswith("vector "):
        if isinstance(valeur, str):
            return valeur_depuis_texte(valeur)
        if isinstance(valeur, (list, tuple)):
            return [float(x) for x in valeur]
        return valeur
    if type_propriete in ("RGBA", "tuple image"):
        if isinstance(valeur, (list, tuple)):
            return tuple(valeur)
        if valeur not in (None, ""):
            return valeur_depuis_texte(str(valeur))
        return valeur
    if type_propriete == "list":
        return valeur
    return str(valeur) if valeur is not None else ""