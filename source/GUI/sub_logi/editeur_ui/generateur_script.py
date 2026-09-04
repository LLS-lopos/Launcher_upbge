"""Génération du script Python BGUI (component UPBGE) depuis une scène.

Le gabarit de référence est ``source/Scripts/minimum_bgui_component.py`` :
un component ``ui`` (bge.types.KX_PythonComponent) par écran, et une
classe ``bgui_utils.Layout`` par calque d'affichage. L'état d'un calque est
le nom slugifié en minuscules ; sa classe est le slug en CamelCase.

Règles de génération :

- chaque calque devient une classe Layout ; les widgets sont créés dans
  ``__init__`` avec pour parent le bon widget (l'écran est le component,
  `Layout` lui-même sert de widget racine) ;
- seules les valeurs « définies par le code » sont écrites (pos, size,
  text, sub_theme, images... et couleurs/bordure/police explicitement
  réglées par le concepteur après la création) : le look reste piloté par
  le theme.cfg au runtime (principe « base == cfg », cf. theme_bgui) ;
- les propriétés de l'écran remplissent ``args`` du component (list ->
  enum ``{"a", "b"}``, ``bpy.type.*`` -> pointeur ``bpy.types.*``) ;
- les événements (déclencheur -> fonction) lient le callback du widget et
  un stub vide est généré pour chaque fonction référencée.
"""

from __future__ import annotations

import os
import re

from .modele import (TYPE_BARRE_PROGRES, TYPE_BLOC_TEXTE,
                     TYPE_BOUTON_IMAGE, TYPE_FRAME, TYPE_FRAME_BOUTON,
                     TYPE_IMAGE, TYPE_LABEL, TYPE_LISTE, TYPE_SAISIE_TEXTE,
                     TYPE_VIDEO, calque_de, calques_ecran, noeud_defini,
                     valeur_defaut_propriete, valeur_typee_propriete)
from .theme_bgui import (THEME_BGUI, THEME_BGUI_DEFAUT,
                         TYPE_PAR_SECTION, _valeur_sous_theme)

# ---------------------------------------------------------------------------
# Nommage des identifiants Python
# ---------------------------------------------------------------------------

_MOTIF_IDENTIFIANT = re.compile(r"[a-zA-Z0-9]+")


def nom_python(nom, prefixe="", minuscules=True):
    """Identifiant Python valide depuis un nom quelconque (slug minuscules).

    Les caractères hors alphanumériques sont remplacés par des
    soulignés ; un nom commençant par un chiffre est préfixé.
    Si ``minuscules`` est ``False``, la casse du nom d'origine est
    conservée (utile pour les noms de fonction écrits tels quels).
    """
    base = "_".join(_MOTIF_IDENTIFIANT.findall(str(nom or "")))
    if minuscules:
        base = base.lower()
    if not base:
        base = "widget"
    if base[0].isdigit():
        base = "_" + base
    return prefixe + base


def classe_calque(nom):
    """Nom de la classe Layout d'un calque : slug en CamelCase.

    ``"start"`` -> ``Start``, ``"menu principal"`` -> ``MenuPrincipal``.
    """
    return "".join(part.capitalize()
                   for part in nom_python(nom).split("_"))


def etat_calque(nom):
    """État d'un calque dans le component ``ui`` : slug minuscules."""
    return nom_python(nom)


# ---------------------------------------------------------------------------
# Formatage des littéraux Python
# ---------------------------------------------------------------------------

class _CodeArgs:
    """Marqueur d'une référence ``args['...']`` (code brut, non littéral)."""

    __slots__ = ("code",)

    def __init__(self, code):
        self.code = code


def _litteral_python(valeur):
    """Littéral Python (listes/tuples/bool/... ) très lisible."""
    if isinstance(valeur, _CodeArgs):
        return valeur.code
    if isinstance(valeur, bool):
        return "True" if valeur else "False"
    if isinstance(valeur, (tuple, list)):
        return "[" + ", ".join(_litteral_python(v) for v in valeur) + "]"
    return repr(valeur)


#: Drapeaux BGUI (vallées dans bgui/widget.py, cf. info_bgui_option.md).
_FLAGS_OPTIONS = {
    1: "BGUI_CENTERX",
    2: "BGUI_CENTERY",
    4: "BGUI_NO_NORMALIZE",
    8: "BGUI_NO_THEME",
    16: "BGUI_NO_FOCUS",
    32: "BGUI_CACHE",
}
#: Alias BGUI_CENTERED = BGUI_CENTERX | BGUI_CENTERY (bit 1|2).
_BIT_CENTERED = 1 | 2


def _expression_options(valeur):
    """Expression Python noms nus des drapeaux options d'un widget.

    ``BGUI_CENTERX | BGUI_CENTERY`` est raccourci en ``BGUI_CENTERED``
    (défini par BGUI comme l'alias des deux bits), les autres drapeaux
    étant combinés par ``|``. Retourne ``(expression, noms_a_importer)``.
    """
    valeur = int(valeur or 0)
    if not valeur:
        return None, []
    noms = []
    if valeur & _BIT_CENTERED == _BIT_CENTERED:
        noms.append("BGUI_CENTERED")
    else:
        if valeur & 1:
            noms.append("BGUI_CENTERX")
        if valeur & 2:
            noms.append("BGUI_CENTERY")
    for bit in (4, 8, 16, 32):
        if valeur & bit:
            noms.append(_FLAGS_OPTIONS[bit])
    if not noms:
        return repr(valeur), []
    return " | ".join(noms), noms


# ---------------------------------------------------------------------------
# Valeurs « définies par le code »
# ---------------------------------------------------------------------------

def _defini_par_code(noeud, cle, type_widget, cle_theme, defaut,
                     seulement_positif=False):
    """Une clé à équivalent thème est-elle écrite par le code ?

    Reproduit la règle du rendu (theme_bgui._pc_err) : un sous-thème
    appliqué la gouverne, et une valeur n'est « définie » que si elle
    diffère à la fois de sa valeur d'initialisation et de la valeur cfg
    courante. ``seulement_positif`` : une bordure/taille à 0 (« non
    précisée ») n'est jamais émise (le thème fournit la valeur).
    """
    if _valeur_sous_theme(noeud, type_widget, cle_theme) is not None:
        return False
    if not noeud_defini(noeud, cle, None):
        return False
    cfg = THEME_BGUI.get(type_widget, {}).get(cle_theme, defaut)
    if not noeud_defini(noeud, cle, cfg):
        return False
    valeur = noeud.prop[cle]
    if seulement_positif and cle_theme in ("BorderSize", "Size") and not valeur:
        return False
    return True


# ---------------------------------------------------------------------------
# Correspondance type de nœud -> constructeur BGUI + paramètres
# ---------------------------------------------------------------------------

BGUI_CLASSE_PAR_TYPE = {
    TYPE_FRAME: "Frame",
    TYPE_FRAME_BOUTON: "FrameButton",
    TYPE_LABEL: "Label",
    TYPE_IMAGE: "Image",
    TYPE_BOUTON_IMAGE: "ImageButton",
    TYPE_LISTE: "ListBox",
    TYPE_BARRE_PROGRES: "ProgressBar",
    TYPE_BLOC_TEXTE: "TextBlock",
    TYPE_SAISIE_TEXTE: "TextInput",
    TYPE_VIDEO: "Video",
}


def _active(noeud, cle):
    """Propriété « règlée » par le code (valeur différente de l'initiale)."""
    return noeud_defini(noeud, cle, None)


def _pt_size_defini(noeud, type_widget):
    """Un ``pt_size`` explicite doit-il être émis dans le script ?

    Reproduit la règle de rendu de :func:`theme_bgui._pc_err` : un
    ``pt_size`` explicitement réglé (c.-à-d. différent du ``Size`` de base
    du thème) PRIME sur le ``Size`` du sous-thème ou du thème. Sinon, on
    n'émet rien pour laisser le thème/sous-thème fournir la taille — c'est
    ainsi que l'éditeur affiche 80 (``[Label:Titre2] Size=80``) alors qu'un
    ``pt_size`` non réglé valait 30.
    """
    defaut = _theme_defaut(type_widget, "Size", 0)
    cfg = THEME_BGUI.get(type_widget, {}).get("Size", defaut)
    return noeud_defini(noeud, "pt_size", cfg)


def _theme_defaut(type_widget, cle_theme, defaut):
    return THEME_BGUI_DEFAUT.get(type_widget, {}).get(cle_theme, defaut)


def _font_args(nom, fonts):
    """Expression du paramètre font d'un widget.

    Les polices sont transmises au layout via ``data["font"]`` (propriétés
    écran de type ``bpy.types.VectorFont``). Si ``nom`` correspond au nom
    d'une telle propriété, on génère
    ``bge.logic.expandPath(data["font"][<index>].filepath)`` référençant la
    police au bon rang ; sinon on garde ``nom`` tel quel (chemin littéral).
    """
    nom = (nom or "").strip()
    if nom in (fonts or []):
        index = list(fonts).index(nom)
        return _CodeArgs(
            f'bge.logic.expandPath(data["font"][{index}].filepath)')
    return nom


def _params_constructeur(noeud, noms_proprietes=None, fonts=None,
                         imports=None):
    """Paramètres et propriétés du widget.

    Retourne ``(params, apres)`` :
    - ``params`` : paramètres du constructeur BGUI (hors parent/name) ;
    - ``apres``  : propriétés à régler après la création (ex. ``colors``
      d'un Frame, ``color`` d'un texte) — jamais acceptées en kwarg.

    Les coordonnées sont toujours émises ; les clés d'apparence (couleurs,
    bordure, police) seulement quand le concepteur les a explicitement
    définies (règle « base == cfg », cf. theme_bgui).  Le ``size`` n'est
    pas émis pour les ``Label`` : leur taille est déduite du thème.
    """
    params = [("pos", noeud.prop["pos"])]
    if noeud.type != TYPE_LABEL:
        params.insert(0, ("size", noeud.prop["size"]))
    apres = []
    sous = str(noeud.prop.get("sub_theme", "") or "").strip()
    if sous:
        params.append(("sub_theme", sous))
    # ``aspect`` (contrainte de ratio) : valable pour tout widget sauf le
    # Label — le Screen ne passe pas ici (absent de BGUI_CLASSE_PAR_TYPE).
    if noeud.type != TYPE_LABEL and _active(noeud, "aspect"):
        params.append(("aspect", noeud.prop["aspect"]))
    options, drapeaux_options = _expression_options(
        noeud.prop.get("options", 0))
    if options:
        params.append(("options", options))
        if imports is not None:
            imports.update(drapeaux_options)
    retourne = lambda cle, valeur: params.append((cle, valeur))
    definit_apres = lambda cle, valeur: apres.append((cle, valeur))

    if noeud.type == TYPE_FRAME:
        if _defini_par_code(noeud, "border", TYPE_FRAME, "BorderSize", 0,
                            seulement_positif=True):
            retourne("border", noeud.prop["border"])
        if _defini_par_code(noeud, "border_color", TYPE_FRAME, "BorderColor",
                            _theme_defaut(TYPE_FRAME, "BorderColor",
                                          (0, 0, 0, 1))):
            definit_apres("border_color", noeud.prop["border_color"])
        if _active(noeud, "color"):
            couleur = list(noeud.prop["color"] or [1, 1, 1, 1])
            definit_apres("colors", [couleur] * 4)

    elif noeud.type == TYPE_FRAME_BOUTON:
        if _defini_par_code(noeud, "base_color", TYPE_FRAME_BOUTON, "Color1",
                            _theme_defaut(TYPE_FRAME_BOUTON, "Color1",
                                          (0.4, 0.4, 0.4, 1))):
            retourne("base_color", noeud.prop["base_color"])
        retourne("text", noeud.prop.get("text", ""))
        if _pt_size_defini(noeud, TYPE_FRAME_BOUTON):
            retourne("pt_size", noeud.prop["pt_size"])
        if _active(noeud, "font") and noeud.prop.get("font"):
            retourne("font", _font_args(noeud.prop["font"], fonts))
        if _defini_par_code(noeud, "color", TYPE_FRAME_BOUTON, "Color",
                            _theme_defaut(TYPE_LABEL, "Color", (1, 1, 1, 1))):
            definit_apres("color", noeud.prop["color"])

    elif noeud.type == TYPE_LABEL:
        retourne("text", noeud.prop.get("text", ""))
        if _pt_size_defini(noeud, TYPE_LABEL):
            retourne("pt_size", noeud.prop["pt_size"])
        if _active(noeud, "font") and noeud.prop.get("font"):
            retourne("font", _font_args(noeud.prop["font"], fonts))
        if _defini_par_code(noeud, "color", TYPE_LABEL, "Color",
                            _theme_defaut(TYPE_LABEL, "Color", (1, 1, 1, 1))):
            retourne("color", noeud.prop["color"])
        if _defini_par_code(noeud, "outline_color", TYPE_LABEL,
                            "OutlineColor",
                            _theme_defaut(TYPE_LABEL, "OutlineColor",
                                          (0, 0, 0, 1))):
            retourne("outline_color", noeud.prop["outline_color"])
        if _defini_par_code(noeud, "outline_size", TYPE_LABEL, "OutlineSize", 0,
                            seulement_positif=True):
            retourne("outline_size", noeud.prop["outline_size"])
        if _active(noeud, "outline_smoothing"):
            retourne("outline_smoothing", noeud.prop["outline_smoothing"])

    elif noeud.type == TYPE_IMAGE:
        retourne("img", noeud.prop.get("fichier", "") or "")
        if _active(noeud, "text"):
            retourne("text", noeud.prop["text"])
        if _active(noeud, "color"):
            definit_apres("color", noeud.prop["color"])

    elif noeud.type == TYPE_BOUTON_IMAGE:
        def _image_etat(cle):
            valeur = noeud.prop.get(cle, "")
            return valeur if valeur and str(valeur) else None
        for cle_bgui, cle_prop in [("default_image", "fichier"),
                                   ("default2_image", "default2_image"),
                                   ("hover_image", "hover_image"),
                                   ("click_image", "click_image")]:
            valeur = _image_etat(cle_prop)
            if cle_bgui == "default_image" or valeur:
                # BGUI attend (img, u, v, w, h) : coordonnées de texture.
                retourne(cle_bgui, (valeur, 0, 0, 1, 1))

    elif noeud.type == TYPE_LISTE:
        retourne("items", noeud.prop.get("items", []))
        if _active(noeud, "padding"):
            retourne("padding", noeud.prop["padding"])

    elif noeud.type == TYPE_BARRE_PROGRES:
        retourne("percent", noeud.prop.get("percent", 0.5))

    elif noeud.type == TYPE_BLOC_TEXTE:
        retourne("text", noeud.prop.get("text", ""))
        if _pt_size_defini(noeud, TYPE_BLOC_TEXTE):
            retourne("pt_size", noeud.prop["pt_size"])
        if _active(noeud, "font") and noeud.prop.get("font"):
            retourne("font", _font_args(noeud.prop["font"], fonts))
        if _active(noeud, "color"):
            retourne("color", noeud.prop["color"])
        if _active(noeud, "overflow"):
            retourne("overflow", noeud.prop["overflow"])

    elif noeud.type == TYPE_SAISIE_TEXTE:
        retourne("text", noeud.prop.get("text", ""))
        prefixe = noeud.prop.get("prefix", "")
        if prefixe or _active(noeud, "prefix"):
            retourne("prefix", prefixe)
        if _pt_size_defini(noeud, TYPE_SAISIE_TEXTE):
            retourne("pt_size", noeud.prop["pt_size"])
        if _active(noeud, "font") and noeud.prop.get("font"):
            retourne("font", _font_args(noeud.prop["font"], fonts))
        if _active(noeud, "color"):
            retourne("color", noeud.prop["color"])

    elif noeud.type == TYPE_VIDEO:
        if noeud.prop.get("fichier"):
            retourne("vid", noeud.prop["fichier"])
        if _active(noeud, "play_audio"):
            retourne("play_audio", noeud.prop["play_audio"])
        if _active(noeud, "repeat"):
            retourne("repeat", noeud.prop["repeat"])
    return params, apres


# ---------------------------------------------------------------------------
# args du component ui (propriétés de l'écran)
# ---------------------------------------------------------------------------

def _ligne_play(noeud, chemin):
    """Ligne d'appel ``.play(...)`` pour une Video BGUI.

    BGUI attend ``play(start, end, use_frames=True, fps=None)`` : ces deux
    extrêmes deviennent ``range=`` du ``VideoFFmpeg`` (en secondes ; en
    images si ``use_frames``, avec ``fps`` pour la conversion). La ligne
    n'est émise que si une option de lecture a été réglée par le concepteur
    (``start``, ``end``, ``use_frames`` ou ``fps``) et qu'un fichier existe ;
    sinon ``None`` (la vidéo se lit alors par défaut via le ``repeat`` du
    constructeur).
    """
    if not noeud.prop.get("fichier"):
        return None
    reglees = ["start", "end", "use_frames", "fps"]
    if not any(_active(noeud, cle) for cle in reglees):
        return None
    defaut = {"start": 0.0, "end": 100.0, "use_frames": True, "fps": 30}
    args = []
    for cle in ("start", "end"):
        valeur = noeud.prop.get(cle, defaut[cle])
        args.append(repr(float(valeur)))
    for cle in ("use_frames", "fps"):
        if _active(noeud, cle):
            valeur = noeud.prop[cle]
            args.append(f"use_frames={_litteral_python(valeur)}"
                        if cle == "use_frames" else f"fps={_litteral_python(valeur)}")
    return f"        {chemin}.play({', '.join(args)})"


def _valeur_args(propriete):
    """Littéral de la valeur par défaut d'une propriété dans ``args``.

    Mappings :
    - ``list`` (enum)     -> ``{"a", "b", ...}`` (valeur séparée par
      virgules ou déjà une liste) ;
    - ``bpy.type.X``      -> ``bpy.types.X`` (pointeur UPBGE) ;
    - autres types        -> valeur typée courante, sinon défaut du type.
    """
    type_propriete = propriete["type"]
    try:
        valeur = valeur_typee_propriete(propriete)
    except (TypeError, ValueError):
        valeur = None

    if type_propriete == "list":
        if isinstance(valeur, str):
            items = [m.strip() for m in valeur.split(",") if m.strip()]
        else:
            items = [str(m) for m in (valeur or [])]
        if not items:
            return "set()"
        return "{" + ", ".join(repr(i) for i in items) + "}"

    if type_propriete.startswith("bpy.type."):
        return "bpy.types." + type_propriete[len("bpy.type."):]

    if valeur not in (None, ""):
        return _litteral_python(valeur)

    defaut = valeur_defaut_propriete(type_propriete)
    if type_propriete == "tuple image":
        return "[None, 0, 0, 1, 1]"
    return _litteral_python(defaut)


def _enfants_calque(racine, calque):
    """Enfants directs de l'écran appartenant au calque."""
    base = calques_ecran(racine)[0]
    return [enfant for enfant in racine.enfants
            if calque_de(enfant, base) == calque]


# ---------------------------------------------------------------------------
# Génération du texte du script
# ---------------------------------------------------------------------------

def _inventaire_attributs(racines):
    """Triplets ``(noeud, parent_attr, attr)`` pour un calque.

    Attributs uniques (dédupliqués par suffixe ``_N``), ``parent_attr`` est
    l'attribut du widget parent (``None`` pour les racines du calque).
    """
    attributs, resultat = set(), []

    def remplir(noeud, parent_attr):
        attr = nom_python(noeud.nom)
        if attr in attributs:
            k = 2
            while f"{attr}_{k}" in attributs:
                k += 1
            attr = f"{attr}_{k}"
        attributs.add(attr)
        resultat.append((noeud, parent_attr, attr))
        for enfant in noeud.enfants:
            remplir(enfant, attr)

    for noeud in racines:
        remplir(noeud, None)
    return resultat


def _lignes_widgets(widgets, noms_proprietes=None, fonts=None, imports=None):
    """Lignes de création des widgets + attributs comportementaux.

    Retourne ``(lignes, stubs)`` :
    - ``lignes`` : instructions de construction (parent = Layout ou
      l'attribut du widget parent) + raccords d'événements + attributs
      comportementaux ;
    - ``stubs``  : noms des fonctions à générer (stubs vides).
    ``imports`` (le cas échéant) reçoit les noms de classes/drapeaux BGUI
    utilisés, pour construire l'import direct ``from bgui import ...``.
    """
    lignes = []
    raccords = {}
    stubs = []

    for noeud, parent_attr, attr in widgets:
        classe = BGUI_CLASSE_PAR_TYPE.get(noeud.type)
        if classe is None:
            continue
        if imports is not None:
            imports.add(classe)
        parent = "self" if parent_attr is None else f"self.{parent_attr}"
        chemin = f"self.{attr}"
        params, apres = _params_constructeur(
            noeud, noms_proprietes, fonts, imports)
        morceaux = "".join(
            f", {cle}={valeur if cle == 'options' else _litteral_python(valeur)}"
            for cle, valeur in params)
        lignes.append(
            f"        self.{attr} = {classe}({parent}, "
            f"name={_litteral_python(noeud.nom)}{morceaux})")
        for prop, valeur in apres:
            lignes.append(
                f"        {chemin}.{prop} = {_litteral_python(valeur)}")

        if noeud.type == TYPE_VIDEO:
            ligne_play = _ligne_play(noeud, chemin)
            if ligne_play:
                lignes.append(ligne_play)

        for evenement in getattr(noeud, "evenements", []):
            declencheur = str(evenement.get("declencheur", "") or "").strip()
            fonction = nom_python(evenement.get("fonction", ""),
                                  minuscules=False)
            if not fonction or not declencheur:
                continue
            if not declencheur.startswith("on_"):
                declencheur = "on_" + declencheur
            if declencheur not in ("on_click", "on_release", "on_hover",
                                   "on_mouse_enter", "on_mouse_exit",
                                   "on_active"):
                continue
            raccords.setdefault(fonction, []).append(
                (chemin, declencheur))
            if fonction not in stubs:
                stubs.append(fonction)

        if noeud.prop.get("visible") is False:
            lignes.append(f"        self.{attr}.visible = False")
        if noeud.prop.get("frozen") is True:
            lignes.append(f"        self.{attr}.frozen = True")
        z_index = noeud.prop.get("z_index", 0)
        if z_index:
            lignes.append(f"        self.{attr}.z_index = {int(z_index)}")

    # stubs : {nom_fonction: [lignes_code]} pour les corps non vides
    stubs = {}
    for fonction, raccords_fonction in raccords.items():
        for chemin, declencheur in raccords_fonction:
            lignes.append(
                f"        {chemin}.{declencheur} = self.{fonction}")
        # Chercher le premier événement référençant cette fonction pour
        # récupérer son corps éditable (clé « code »).
        corps = []
        for noeud, _, _ in widgets:
            for ev in getattr(noeud, "evenements", []):
                if nom_python(ev.get("fonction", ""),
                              minuscules=False) == fonction:
                    corps = ev.get("code", []) or []
                    if corps:
                        break
            if corps:
                break
        if fonction not in stubs:
            stubs[fonction] = corps

    return lignes, stubs


def _bloc_etat_calque(calque, fonts=None):
    """Bloc de changement d'état du component ui pour un calque.

    ``fonts`` : noms d'attributs (ex. ``"font_1"``) des propriétés écran de
    type ``bpy.types.VectorFont``, toutes regroupées dans ``self.font`` et
    transmises au layout via ``data={"font": self.font}``.
    """
    if fonts:
        data = 'data={"font": self.font}'
    else:
        data = "data={}"
    return [
        f"            if self._etat == \"{etat_calque(calque)}\":",
        "                bge.logic.mouse.visible = True",
        f"                self._gui.load_layout({classe_calque(calque)}, "
        f"{data})",
    ]


def script_ui_en_texte(racine):
    """Génère le texte du script Python BGUI d'une scène (écran).

    Le thème est résolu au runtime à partir de la propriété écran ``cfg``
    de type ``bpy.type.Text`` (le dossier de son fichier embarque le
    ``theme.cfg``).  Si aucun al ``cfg`` n'est déclaré, il est injecté
    automatiquement dans les ``args``.
    """
    calques = calques_ecran(racine)
    etat_base = etat_calque(calques[0]) if calques else "start"

    args = [dict(p) for p in getattr(racine, "proprietes", [])]
    if not any(str(p.get("nom", "")).strip() == "cfg"
               for p in args):
        args.insert(0, {"nom": "cfg", "type": "bpy.type.Text",
                        "valeur": ""})
    noms_proprietes = {str(p.get("nom", "")).strip()
                       for p in args if p.get("nom")}
    fonts = [str(p.get("nom", "")).strip()
             for p in args
             if p.get("nom") and str(p.get("type", "")).strip()
             == "bpy.type.VectorFont"]
    if args:
        lignes_args = ["    args = OrderedDict(["]
        for p in args:
            lignes_args.append(
                f"        ({_litteral_python(p['nom'])}, {_valeur_args(p)}),")
        lignes_args.append("    ])")
    else:
        lignes_args = ["    args = OrderedDict([])"]

    imports = set()
    classes_utilisees = set()
    for calque in calques:
        for noeud, _, _ in _inventaire_attributs(
                _enfants_calque(racine, calque)):
            _, drapeaux = _expression_options(noeud.prop.get("options", 0))
            imports.update(drapeaux)
            classe = BGUI_CLASSE_PAR_TYPE.get(noeud.type)
            if classe:
                classes_utilisees.add(classe)

    classes_bgui = sorted(classes_utilisees)
    noms_bgui = list(classes_bgui)
    if imports:
        noms_bgui += sorted(imports)
    import_bgui = "from bgui import bgui_utils"
    if noms_bgui:
        import_bgui += ", " + ", ".join(noms_bgui)

    lignes = []
    lignes.append("import bge, bgui, bpy, pathlib")
    lignes.append("from collections import OrderedDict")
    lignes.append(import_bgui)
    lignes.append("")
    lignes.append("")
    lignes.append("class ui(bge.types.KX_PythonComponent):")
    lignes.extend(lignes_args)
    lignes.append("")
    lignes.append("    def start(self, args):")
    lignes.append("        self._initialized = False")
    lignes.append("        self._etat = None")
    lignes.append("")
    for p in args:
        nom = str(p.get("nom", "")).strip()
        if nom:
            ligne = f"        self._{nom_python(nom)} = args[{_litteral_python(nom)}]"
            lignes.append(ligne)
    lignes.append("")
    if fonts:
        lignes.append("        self.font = [" + ", ".join(
            f"self._{nom_python(nom)}" for nom in fonts) + "]")
    lignes.append("")
    lignes.append("    def check_etat(self):")
    lignes.append("        return getattr(self._gui, '_next_etat', None)")
    lignes.append("")
    lignes.append("    def update(self):")
    lignes.append("        if not self._initialized:")
    lignes.append('            self._gui = bgui_utils.System('
                  'bge.logic.expandPath('
                  'f"{pathlib.Path(self._cfg.filepath).parent}"))')
    lignes.append("            self._initialized = True")
    lignes.append(
        f"            self._gui._next_etat = \"{etat_base}\"")
    lignes.append("")
    lignes.append("")
    lignes.append("        self._gui._next_etat = self.check_etat()")
    lignes.append("        if self._gui._next_etat != self._etat:")
    lignes.append("            self._etat = self._gui._next_etat")
    for calque in calques:
        lignes.extend(_bloc_etat_calque(calque, fonts=fonts))
    lignes.append("        self._gui.run()  # met à jour le layout + "
                  "souris/clavier chaque frame")
    lignes.append("")

    for calque in calques:
        lignes.append("")
        lignes.append("")
        lignes.append(f"class {classe_calque(calque)}(bgui_utils.Layout):")
        lignes.append("    def __init__(self, sys, data):")
        lignes.append("        super().__init__(sys, data)")
        widgets = _inventaire_attributs(_enfants_calque(racine, calque))

        lignes_widgets, stubs = _lignes_widgets(
            widgets, noms_proprietes, fonts)
        lignes.extend(lignes_widgets)
        lignes.append("")
        lignes.append("    def update(self):")
        lignes_update = []
        for noeud, _parent_attr, _attr in widgets:
            for ligne_code in (getattr(noeud, "update_code", None) or []):
                if str(ligne_code).strip():
                    lignes_update.append(f"        {ligne_code}")
        if lignes_update:
            lignes.extend(lignes_update)
        else:
            lignes.append("        pass")
        for fonction in stubs:
            lignes.append("")
            lignes.append(f"    def {fonction}(self, widget):")
            corps = stubs[fonction]
            if corps:
                for ligne_code in corps:
                    lignes.append(f"        {ligne_code}")
            else:
                lignes.append("        pass")

    return "\n".join(lignes) + "\n"


def sauvegarder_script(racine, chemin):
    """Écrit le script généré d'une scène dans ``chemin``."""
    contenu = script_ui_en_texte(racine)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    return contenu