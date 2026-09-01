"""Rendu « fidèle » des widgets BGUI et gestion du thème.

Le thème est lu depuis un fichier de format BGUI (source/Scripts/theme.cfg) :
des sections comme ``[Frame]``, ``[FrameButton]`` ou ``[Label]`` contenant des
clés ``Nom=valeur``. Les valeurs sont des couleurs RGBA en floats 0..1, des
entiers (BorderSize, Size...), des booléens (OutlineSmoothing...) ou des
tuples image (``None, x, y, w, h``).

Deux vues du thème coexistent :

- `THEME_BGUI` : vue « typée » utilisée par les peintres (section mappée sur
  les types de nœuds de modele.py) ;
- `THEME_CRU` : vue « brute », fidèle au fichier (sections inconnues
  conservées), utilisée pour réécrire le fichier sans perte.

Priorité des valeurs d'un widget : sous-thème appliqué (« Type:Nom » si
``sub_theme`` est défini — ex. ``[Label:Titre]``) **toujours prioritaire**
pour les clés qu'il définit, puis propriété explicite du nœud, puis section
de base du type (ex. ``[Label]``), puis valeur par défaut intégrée. Une
bordure explicite à 0 laisse le thème fournir son ``BorderSize``.
"""

from __future__ import annotations

import copy
import os

from PySide6.QtCore import Qt, QRect, QRectF, QPointF
from PySide6.QtGui import (QColor, QFont, QFontDatabase, QPainter,
                           QPainterPath, QPixmap, QPolygonF)

from .modele import (TYPE_BARRE_PROGRES, TYPE_BLOC_TEXTE, TYPE_BOUTON_IMAGE,
                     TYPE_FRAME, TYPE_FRAME_BOUTON, TYPE_IMAGE, TYPE_LABEL,
                     TYPE_LISTE, TYPE_SAISIE_TEXTE, TYPE_SCREEN, TYPE_VIDEO,
                     inferer_type_propriete, noeud_defini,
                     valeur_depuis_texte, valeur_typee_propriete,
                     valeur_vers_texte)

# ---------------------------------------------------------------------------
# Thème par défaut (theme_section de BGUI) et correspondance type -> section
# ---------------------------------------------------------------------------

#: Nom de la section du fichier de thème pour chaque type de nœud.
TYPE_PAR_SECTION = {
    TYPE_SCREEN: "Screen",
    TYPE_LABEL: "Label",
    TYPE_FRAME: "Frame",
    TYPE_FRAME_BOUTON: "FrameButton",
    TYPE_IMAGE: "Image",
    TYPE_BOUTON_IMAGE: "ImageButton",
    TYPE_LISTE: "ListBox",
    TYPE_BARRE_PROGRES: "ProgressBar",
    TYPE_BLOC_TEXTE: "TextBlock",
    TYPE_SAISIE_TEXTE: "TextInput",
    TYPE_VIDEO: "Video",
}
SECTION_PAR_TYPE = {v: k for k, v in TYPE_PAR_SECTION.items()}

THEME_BGUI_DEFAUT = {
    TYPE_SCREEN: {"fond": (0.0, 0.0, 0.0, 1.0)},
    TYPE_LABEL: {
        "Font": "",
        "Color": (1.0, 1.0, 1.0, 1.0),
        "OutlineColor": (0.0, 0.0, 0.0, 1.0),
        "OutlineSmoothing": False,
        "Size": 30,
        "OutlineSize": 0,
    },
    TYPE_FRAME: {
        "Color1": (0.56, 0.56, 0.56, 1.0),
        "Color2": (0.63, 0.63, 0.63, 1.0),
        "Color3": (0.40, 0.40, 0.40, 1.0),
        "Color4": (0.50, 0.50, 0.50, 1.0),
        "BorderSize": 0,
        "BorderColor": (0.0, 0.0, 0.0, 1.0),
    },
    TYPE_FRAME_BOUTON: {
        "Color1": (0.45, 0.45, 0.45, 1.0),
        "Color2": (0.45, 0.45, 0.45, 1.0),
        "Color3": (0.45, 0.45, 0.45, 1.0),
        "Color4": (0.45, 0.45, 0.45, 1.0),
        "BorderSize": 1,
        "BorderColor": (0.0, 0.0, 0.0, 1.0),
        "Color": (1.0, 1.0, 1.0, 1.0),
        "LabelSubTheme": "",
    },
    TYPE_IMAGE: {},
    TYPE_BOUTON_IMAGE: {
        "BorderSize": 1,
        "BorderColor": (0.0, 0.0, 0.0, 1.0),
    },
    TYPE_LISTE: {
        "Border": 1,
        "BorderColor": (0.0, 0.0, 0.0, 1.0),
        "Padding": 0,
        "HighlightColor1": (1.0, 1.0, 1.0, 1.0),
        "HighlightColor2": (0.0, 0.0, 1.0, 1.0),
        "HighlightColor3": (0.0, 0.0, 1.0, 1.0),
        "HighlightColor4": (0.0, 0.0, 1.0, 1.0),
        "Color": (1.0, 1.0, 1.0, 1.0),
    },
    TYPE_BARRE_PROGRES: {
        "BGColor1": (0.0, 0.0, 0.0, 1.0),
        "BGColor2": (0.0, 0.0, 0.0, 1.0),
        "BGColor3": (0.0, 0.0, 0.0, 1.0),
        "BGColor4": (0.0, 0.0, 0.0, 1.0),
        "FillColor1": (0.0, 0.42, 0.02, 1.0),
        "FillColor2": (0.0, 0.42, 0.02, 1.0),
        "FillColor3": (0.0, 0.42, 0.02, 1.0),
        "FillColor4": (0.0, 0.42, 0.02, 1.0),
        "BorderSize": 1,
        "BorderColor": (0.0, 0.0, 0.0, 1.0),
    },
    TYPE_BLOC_TEXTE: {
        "LabelSubTheme": "",
    },
    TYPE_SAISIE_TEXTE: {
        "TextColor": (1.0, 1.0, 1.0, 1.0),
        "InactiveTextColor": (1.0, 1.0, 1.0, 1.0),
        "HighlightColor": (0.6, 0.6, 0.6, 0.5),
        "InactiveHighlightColor": (0.6, 0.6, 0.6, 0.5),
        "FrameColor": (0.0, 0.0, 0.0, 0.0),
        "InactiveFrameColor": (0.0, 0.0, 0.0, 0.0),
        "BorderSize": 0,
        "InactiveBorderSize": 0,
        "BorderColor": (0.0, 0.0, 0.0, 0.0),
        "InactiveBorderColor": (0.0, 0.0, 0.0, 0.0),
    },
    TYPE_VIDEO: {},
}

#: Thème actif (typé) — seule référence pour le rendu.
THEME_BGUI = copy.deepcopy(THEME_BGUI_DEFAUT)

#: Vue brute du thème chargé (fidèle au fichier), vide tant qu'aucun fichier n'a été lu.
THEME_CRU = {}


def _lire_valeur(texte):
    """Convertit la valeur d'une clé cfg en type Python utilisable.

    Délègue le format commun à :func:`modele.valeur_depuis_texte`
    (booléens, entiers, flottants, tuples RGBA, tuples image, sinon str()).
    """
    return valeur_depuis_texte(texte)


def _formater_valeur(valeur):
    """Convertit une valeur Python en texte de clé cfg."""
    return valeur_vers_texte(valeur)


#: Section spéciale du thème réservée aux propriétés du projet (nom/valeur).
SECTION_PROPRIETES = "Properties"


def proprietes_depuis_donnees(donnees):
    """Reconstruit la liste de propriétés depuis un dict cfg analysé.

    Chaque entrée ``{nom: valeur}`` de la section `[Properties]` devient
    ``{"nom", "type", "valeur"}`` avec le type déduit de la valeur.
    """
    resultat = []
    section = donnees.get(SECTION_PROPRIETES, {})
    for nom, valeur in section.items():
        resultat.append({
            "nom": nom,
            "type": inferer_type_propriete(valeur),
            "valeur": valeur,
        })
    return resultat


def resoudre_proprietes(donnees, proprietes):
    """Remplace les marqueurs ``prop.<nom>`` dans un dict cfg analysé.

    La section `[Properties]` est retirée du résultat (elle ne pilote pas
    l'affichage). Toute valeur texte égale à ``prop.<nom>`` est remplacée
    par la valeur typée de la propriété correspondante.
    """
    valeurs = {p["nom"]: valeur_typee_propriete(p) for p in proprietes}
    resultat = {}
    for section, cles in donnees.items():
        if section == SECTION_PROPRIETES:
            continue
        resolues = {}
        for cle, valeur in cles.items():
            if isinstance(valeur, str) and valeur.startswith("prop."):
                nom = valeur[len("prop."):].strip()
                resolues[cle] = valeurs.get(nom, valeur)
            else:
                resolues[cle] = valeur
        resultat[section] = resolues
    return resultat


def lire_cfg_texte(contenu):
    """Analyse le texte d'un fichier de thème en ``{section: {clé: valeur}}``.

    Les lignes vides, les commentaires ``#``/``;`` et le contenu hors section
    sont ignorés.
    """
    sections = {}
    section = None
    for ligne in contenu.splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or ligne.startswith(";"):
            continue
        if ligne.startswith("[") and ligne.endswith("]"):
            section = ligne[1:-1].strip()
            sections.setdefault(section, {})
            continue
        if section is None or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        sections[section][cle.strip()] = _lire_valeur(valeur)
    return sections


def lire_valeur(texte):
    """Analyse une valeur saisie comme dans theme.cfg.

    Accepte les booléens, entiers, flottants, tuples de couleurs RGBA
    (``r, g, b, a``), tuples image (``None, x, y, w, h``) et, à défaut,
    une chaîne texte (str()).
    """
    return _lire_valeur(texte.strip() if texte else texte)


def theme_en_texte(donnees=None):
    """Sérialise un thème brut ({section: {clé: valeur}}) en texte cfg."""
    sections = THEME_CRU if donnees is None else donnees
    lignes = []
    for nom, cles in sections.items():
        lignes.append(f"[{nom}]")
        for cle, valeur in cles.items():
            lignes.append(f"{cle}={_formater_valeur(valeur)}")
        lignes.append("")
    return "\n".join(lignes).rstrip() + "\n"


def appliquer_theme(donnees=None, chemin=None):
    """Applique un thème (dict brut ou fichier) au rendu.

    Met à jour `THEME_BGUI` (vue typée pour les peintres) **en place** afin
    que toutes les références existantes restent valides, et `THEME_CRU`
    (vue brute utilisée pour la sauvegarde). Retourne `THEME_BGUI`.
    """
    global THEME_CRU
    if chemin is not None:
        with open(chemin, encoding="utf-8") as f:
            donnees = lire_cfg_texte(f.read())
    if donnees is None:
        donnees = {}
    THEME_CRU = dict(donnees)

    nouveau = copy.deepcopy(THEME_BGUI_DEFAUT)
    for section, cles in donnees.items():
        type_ = SECTION_PAR_TYPE.get(section)
        if type_ is None:
            continue
        for cle, valeur in cles.items():
            if cle in nouveau.get(type_, {}):
                nouveau[type_][cle] = valeur
    THEME_BGUI.clear()
    THEME_BGUI.update(nouveau)
    return THEME_BGUI


def charger_theme_fichier(chemin):
    """Charge un fichier de thème depuis le disque et l'applique."""
    return appliquer_theme(chemin=chemin)


def sauvegarder_theme_fichier(chemin, donnees=None):
    """Écrit un thème (brut, par défaut la vue courante) dans un fichier."""
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(theme_en_texte(donnees))


def reinitialiser_theme():
    """Revient au thème par défaut intégré (et vide la vue brute)."""
    global THEME_CRU
    THEME_CRU = {}
    THEME_BGUI.clear()
    THEME_BGUI.update(copy.deepcopy(THEME_BGUI_DEFAUT))


def theme_defaut_en_texte():
    """Texte cfg des valeurs par défaut intégrées (hors section Screen)."""
    sections = {}
    for type_, cles in THEME_BGUI_DEFAUT.items():
        if type_ == TYPE_SCREEN or not cles:
            continue
        section = TYPE_PAR_SECTION.get(type_)
        if section:
            sections[section] = dict(cles)
    return theme_en_texte(sections)


# ---------------------------------------------------------------------------
# Couleurs, polices et résolution des valeurs
# ---------------------------------------------------------------------------

_cache_images = {}

#: Répertoire de base des chemins relatifs « // » (convention BGUI/UPBGE).
CHEMIN_BASE_PROJET = os.getcwd()

#: Cache des familles de polices chargées depuis des fichiers (.ttf/.otf).
_cache_polices = {}


def _famille_police(noeud):
    """Famille de police à utiliser pour un widget.

    Renvoie la famille de la police choisie (fichier ``font`` du widget,
    résolu « // »/« ~/ » ou absolu) si elle existe, sinon ``None`` (sans-
    serif). La police n'est chargée qu'une seule fois (cache global Qt).
    """
    if not (noeud_defini(noeud, "font") and noeud.prop.get("font")):
        return None
    chemin = resoudre_chemin_fichier(str(noeud.prop.get("font", "")))
    if not os.path.isfile(chemin):
        return None
    if chemin not in _cache_polices:
        try:
            identifiant = QFontDatabase.addApplicationFont(chemin)
            familles = (QFontDatabase.applicationFontFamilies(identifiant)
                        if identifiant >= 0 else [])
            _cache_polices[chemin] = familles[0] if familles else None
        except Exception:
            _cache_polices[chemin] = None
    return _cache_polices[chemin]


def definir_base_projet(chemin):
    """Fixer le répertoire de base utilisé pour résoudre les chemins « // »."""
    global CHEMIN_BASE_PROJET
    if not chemin:
        CHEMIN_BASE_PROJET = os.getcwd()
        return
    chemin = os.path.abspath(chemin)
    if os.path.isdir(chemin):
        CHEMIN_BASE_PROJET = chemin
    else:
        CHEMIN_BASE_PROJET = os.path.dirname(chemin)


def resoudre_chemin_fichier(chemin, base=None):
    """Résout un chemin de fichier saisi par l'utilisateur.

    Formats acceptés :

    - ``//data/logo.png``  -> relatif au répertoire du projet (UPBGE)
    - ``~/Pictures/x.png`` -> relatif au répertoire personnel
    - ``/home/user/x.png`` -> chemin absolu, utilisé tel quel
    - ``data/logo.png``    -> chemin relatif, utilisé tel quel (cwd)
    """
    if not chemin:
        return chemin
    if chemin.startswith("~"):
        return os.path.expanduser(chemin)
    if chemin.startswith("//"):
        base = base or CHEMIN_BASE_PROJET or os.getcwd()
        return os.path.join(base, chemin[2:].lstrip("/"))
    return chemin


def couleur(rgba, defaut=None):
    """Convertit une couleur RGBA (floats 0..1) en QColor.

    Tolère les défauts : tuple image BGUI ``(None, x, w, h, ...)``, chaînes,
    listes trop longues (on garde les 4 premières valeurs) — on retombe sur
    le défaut puis sur du blanc si la valeur n'est pas une couleur.
    """

    def _normaliser(seq):
        if not isinstance(seq, (tuple, list)) or not seq:
            return None
        if seq[0] is None:      # tuple image (None, x, w, h, ...)
            return None
        valeurs = [v for v in seq if v is not None]
        if len(valeurs) < 3:
            return None
        try:
            r, g, b = float(valeurs[0]), float(valeurs[1]), float(valeurs[2])
            a = float(valeurs[3]) if len(valeurs) >= 4 else 1.0
            return r, g, b, a
        except (TypeError, ValueError):
            return None

    net = _normaliser(rgba)
    if net is None:
        net = _normaliser(defaut)
    if net is None:
        return QColor(255, 255, 255, 255)
    r, g, b, a = net
    return QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))


def police(pt_size, famille=None):
    """Police pour un pt_size BGUI, facteur de rendu global 7/9 (~96 dpi).

    Le facteur 7/9 (au lieu du 4/3 historique) calibre l'éditeur sur le
    rendu UPBGE : à ``pt_size`` égal, la largeur/hauteur du texte affichée
    correspond à celle du jeu (l'éditeur rendait ~1.714× = 12/7 de trop).

    ``famille`` optionnelle : une famille nommée (police choisie via le
    champ « font » du widget) remplace la police par défaut sans-serif.
    """
    police_ = QFont(famille) if famille else QFont("sans-serif")
    police_.setPixelSize(max(6, int(round(pt_size * 7 / 9))))
    return police_


def _valeur_sous_theme(noeud, type_widget, cle_theme):
    """Valeur fournie par le sous-thème du widget, sinon ``None``.

    Un widget dont ``sub_theme`` vaut « Titre » a sa valeur — si la clé est
    définie dans la section « Type:Titre » (ex. ``[Label:Titre]``) du thème
    actif — renvoyée telle quelle ; le sous-thème cible la section du type
    du widget lui-même, comme en BGUI. ``None`` = aucune clé de sous-thème
    pertinente (pas de ``sub_theme``, section absente ou clé absente).
    """
    section = TYPE_PAR_SECTION.get(noeud.type)
    sous = str(noeud.prop.get("sub_theme", "") or "").strip()
    if sous and section:
        valeurs = THEME_CRU.get(f"{section}:{sous}")
        if valeurs and cle_theme in valeurs:
            return valeurs[cle_theme]
    return None


def sous_themes_disponibles(type_widget):
    """Noms des sous-thèmes définis dans le thème actif pour un type.

    Ex. : les sections ``[Label:Titre]`` et ``[Label:Titre2]`` renvoient
    ``["Titre", "Titre2"]`` pour `TYPE_LABEL`.
    """
    section = TYPE_PAR_SECTION.get(type_widget)
    if not section:
        return []
    prefixe = section + ":"
    return sorted({nom[len(prefixe):] for nom in THEME_CRU
                   if nom.startswith(prefixe) and len(nom) > len(prefixe)})


def _pc_err(noeud, cle_noeud, type_widget, cle_theme, defaut):
    """Valeur de rendu d'un widget, dans cet ordre :
    sous-thème appliqué, propriété définie par le code, thème actif,
    défaut intégré.

    Un sous-thème (section « Type:Nom » du fichier, cf.
    :func:`_valeur_sous_theme`) est **toujours prioritaire** pour les clés
    qu'il définit, même quand le widget a réglé la propriété équivalente —
    sauf la taille de police (``Size``) : comme en BGUI, un ``pt_size``
    explicitement réglé sur le widget **prime** sur la valeur du sous-thème
    (le constructeur ``Label`` ne lit ``self.theme['Size']`` que si
    ``pt_size`` n'est pas fourni). Pour les clés qu'un sous-thème ne définit
    pas, une propriété de widget n'est prioritaire que si elle diffère de la
    valeur cfg courante (et de sa valeur initiale, cf. modele.noeud_defini),
    sinon la section de base du type sert de référence. Atténuation : une
    bordure explicite à 0 (« non précisée ») laisse le thème fournir son
    ``BorderSize``, comme le fait BGUI.
    """
    sous = _valeur_sous_theme(noeud, type_widget, cle_theme)
    cfg = THEME_BGUI.get(type_widget, {}).get(cle_theme, defaut)
    if cle_theme == "Size" and noeud_defini(noeud, "pt_size", cfg):
        return noeud.prop["pt_size"]
    if sous is not None:
        return sous
    if noeud_defini(noeud, cle_noeud, cfg):
        valeur = noeud.prop[cle_noeud]
        if not (cle_theme in ("BorderSize", "Size") and not valeur):
            return valeur
    return cfg


def valeur_rendu(noeud, cle_noeud, type_widget, cle_theme, defaut):
    """Accesseur public de `_pc_err` : valeur effective (cfg ou code défini).

    L'éditeur s'en sert pour afficher la valeur réellement rendue (base =
    cfg généré) dans les champs qui ont un équivalent de thème.
    """
    return _pc_err(noeud, cle_noeud, type_widget, cle_theme, defaut)


def _bevel(painter, rect, base, bord):
    """Dessine le léger biseau des cadres/boutons :
    bord haut et gauche éclaircis, bas et droite assombris."""
    if rect.height() < 6 or rect.width() < 6:
        return
    painter.setPen(base.lighter(118))
    painter.drawLine(int(rect.left()), int(rect.top()),
                     int(rect.right() - 1), int(rect.top()))
    painter.drawLine(int(rect.left()), int(rect.top()),
                     int(rect.left()), int(rect.bottom() - 1))
    painter.setPen(base.darker(122))
    painter.drawLine(int(rect.left()), int(rect.bottom() - 1),
                     int(rect.right() - 1), int(rect.bottom() - 1))
    painter.drawLine(int(rect.right() - 1), int(rect.top()),
                     int(rect.right() - 1), int(rect.bottom() - 1))


def _peindre_bordure(painter, rect, bord, couleur_bord):
    """Dessine une bordure de `bord` px plaquée sur le bord du widget.

    Véritable bande de bord (comme en BGUI) qui sépare le contenu de
    l'extérieur : elle épouse chaque côté de `rect` sans être réduite vers
    un coin. ``couleur_bord`` est un QColor.
    """
    if bord <= 0 or rect.width() <= 0 or rect.height() <= 0:
        return
    if rect.width() <= 2 * bord or rect.height() <= 2 * bord:
        painter.fillRect(rect, couleur_bord)
        return
    trajet = QPainterPath()
    trajet.addRect(rect)
    trajet.addRect(QRectF(rect.left() + bord, rect.top() + bord,
                          rect.width() - 2 * bord, rect.height() - 2 * bord))
    painter.fillPath(trajet, couleur_bord)


def peindre_cadre(painter, rect, noeud):
    """Dessine un Frame BGUI : remplissage + bordure (bande de bord)."""
    base = couleur(_pc_err(noeud, "color", TYPE_FRAME, "Color1",
                           THEME_BGUI_DEFAUT[TYPE_FRAME]["Color1"]))
    bord = int(_pc_err(noeud, "border", TYPE_FRAME, "BorderSize", 0) or 0)
    painter.fillRect(rect, base)
    if bord > 0:
        _peindre_bordure(painter, rect, bord, couleur(
            _pc_err(noeud, "border_color", TYPE_FRAME, "BorderColor",
                    THEME_BGUI_DEFAUT[TYPE_FRAME]["BorderColor"])))
        _bevel(painter, rect.adjusted(bord + 1, bord + 1, -bord, -bord),
               base, bord)
    else:
        _bevel(painter, rect, base, bord)


def peindre_bouton(painter, rect, noeud):
    """Dessine un FrameButton BGUI : fond + bord + label centré."""
    base = couleur(_pc_err(noeud, "base_color", TYPE_FRAME_BOUTON, "Color1",
                           THEME_BGUI_DEFAUT[TYPE_FRAME_BOUTON]["Color1"]))
    bord = int(_pc_err(noeud, "border", TYPE_FRAME_BOUTON, "BorderSize", 1) or 0)
    painter.fillRect(rect, base)
    if bord > 0:
        _peindre_bordure(painter, rect, bord, couleur(
            _pc_err(noeud, "border_color", TYPE_FRAME_BOUTON, "BorderColor",
                    THEME_BGUI_DEFAUT[TYPE_FRAME_BOUTON]["BorderColor"])))
        _bevel(painter, rect.adjusted(bord + 1, bord + 1, -bord, -bord),
               base, bord)
    else:
        _bevel(painter, rect, base, bord)

    pt = int(_pc_err(noeud, "pt_size", TYPE_LABEL, "Size",
                     THEME_BGUI_DEFAUT[TYPE_LABEL]["Size"]))
    painter.setFont(police(pt, _famille_police(noeud)))
    painter.setPen(couleur(_pc_err(noeud, "color", TYPE_FRAME_BOUTON, "Color",
                                   THEME_BGUI_DEFAUT[TYPE_LABEL]["Color"])))
    painter.drawText(rect, Qt.AlignCenter, str(noeud.prop.get("text", "")))


def peindre_label(painter, rect, noeud):
    """Dessine un Label BGUI : texte éventuellement avec contour."""
    texte = str(noeud.prop.get("text", ""))
    if not texte:
        return
    pt = int(_pc_err(noeud, "pt_size", TYPE_LABEL, "Size",
                     THEME_BGUI_DEFAUT[TYPE_LABEL]["Size"]))
    painter.setFont(police(pt, _famille_police(noeud)))

    contour = int(_pc_err(noeud, "outline_size", TYPE_LABEL, "OutlineSize", 0) or 0)
    if contour > 0:
        painter.setPen(couleur(_pc_err(noeud, "outline_color", TYPE_LABEL,
                                       "OutlineColor",
                                       THEME_BGUI_DEFAUT[TYPE_LABEL]["OutlineColor"])))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    painter.drawText(rect.translated(dx * contour, dy * contour),
                                     Qt.AlignLeft | Qt.AlignVCenter, texte)

    painter.setPen(couleur(_pc_err(noeud, "color", TYPE_LABEL, "Color",
                                   THEME_BGUI_DEFAUT[TYPE_LABEL]["Color"])))
    painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, texte)


def _charger_image(chemin):
    """Charge et met en cache un pixmap depuis le chemin indiqué."""
    if not chemin:
        return None
    if chemin in _cache_images:
        return _cache_images[chemin]
    pix = QPixmap(chemin)
    if pix.isNull():
        pix = None
    _cache_images[chemin] = pix
    return pix


def _peindre_image_ou_pave(painter, rect, noeud, libelle):
    """Dessine une image (étirée) ou un pavé « image manquante »."""
    chemin = resoudre_chemin_fichier(str(noeud.prop.get("fichier", "")))
    if os.path.isfile(chemin):
        pix = _charger_image(chemin)
        if pix is not None:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.drawPixmap(QRect(rect.toRect()), pix)
            return

    grille = QColor(70, 70, 70)
    trait = QColor(110, 110, 110)
    painter.fillRect(rect, grille)
    painter.setPen(trait)
    for i in range(-20, 30, 6):
        painter.drawLine(int(rect.left()) + i, int(rect.top()),
                         int(rect.left()) + i + 8, int(rect.bottom()))
    painter.setPen(QColor(200, 200, 200))
    painter.drawText(rect, Qt.AlignCenter, libelle)


def peindre_image(painter, rect, noeud):
    """Dessine une Image BGUI (étirée) ou un pavé « image manquante »."""
    _peindre_image_ou_pave(painter, rect, noeud, "image manquante")


def peindre_bouton_image(painter, rect, noeud):
    """Dessine un ImageButton BGUI : image + bordure discrète."""
    _peindre_image_ou_pave(painter, rect, noeud, "image (ImageButton)")
    bord = int(_pc_err(noeud, "border", TYPE_BOUTON_IMAGE, "BorderSize", 1) or 0)
    if bord > 0:
        _peindre_bordure(painter, rect, bord, couleur(
            _pc_err(noeud, "border_color", TYPE_BOUTON_IMAGE, "BorderColor",
                    THEME_BGUI_DEFAUT[TYPE_BOUTON_IMAGE]["BorderColor"])))


def peindre_liste(painter, rect, noeud):
    """Dessine une ListBox BGUI : fond, éléments, ligne sélectionnée."""
    painter.fillRect(rect, QColor(25, 25, 28))
    items = noeud.prop.get("items", [])
    if isinstance(items, str):
        items = [items]
    items = [str(i) for i in items if str(i)]
    if not items:
        painter.setPen(QColor(120, 120, 120))
        painter.drawText(rect, Qt.AlignCenter, "(liste vide)")
        return

    sel = max(0, min(len(items) - 1, int(noeud.prop.get("selected", 0))))
    hauteur_ligne = rect.height() / len(items)
    highlight = couleur(_pc_err(noeud, "highlight_color", TYPE_LISTE,
                                "HighlightColor1",
                                THEME_BGUI_DEFAUT[TYPE_LISTE]["HighlightColor1"]))
    painter.fillRect(QRectF(rect.left(), rect.top() + sel * hauteur_ligne,
                            rect.width(), hauteur_ligne), highlight)

    pt = int(_pc_err(noeud, "pt_size", TYPE_LABEL, "Size",
                     THEME_BGUI_DEFAUT[TYPE_LABEL]["Size"]))
    painter.setFont(police(pt, _famille_police(noeud)))
    painter.setPen(couleur(_pc_err(noeud, "color", TYPE_LISTE, "Color",
                                   THEME_BGUI_DEFAUT[TYPE_LISTE]["Color"])))
    for i, item in enumerate(items):
        painter.drawText(QRectF(rect.left() + 4, rect.top() + i * hauteur_ligne,
                                rect.width() - 8, hauteur_ligne),
                         Qt.AlignLeft | Qt.AlignVCenter, item)

    bord = int(_pc_err(noeud, "border", TYPE_LISTE, "Border", 1) or 0)
    if bord > 0:
        _peindre_bordure(painter, rect, bord, couleur(
            _pc_err(noeud, "border_color", TYPE_LISTE, "BorderColor",
                    THEME_BGUI_DEFAUT[TYPE_LISTE]["BorderColor"])))


def peindre_barre_progres(painter, rect, noeud):
    """Dessine une ProgressBar BGUI : fond, remplissage, bordure, %."""
    try:
        percent = max(0.0, min(1.0, float(noeud.prop.get("percent", 0.5))))
    except (TypeError, ValueError):
        percent = 0.5
    painter.fillRect(rect, couleur(
        _pc_err(noeud, "bg_color", TYPE_BARRE_PROGRES, "BGColor1",
                THEME_BGUI_DEFAUT[TYPE_BARRE_PROGRES]["BGColor1"])))
    if percent > 0:
        painter.fillRect(QRectF(rect.left(), rect.top(),
                                rect.width() * percent, rect.height()), couleur(
            _pc_err(noeud, "fill_color", TYPE_BARRE_PROGRES, "FillColor1",
                    THEME_BGUI_DEFAUT[TYPE_BARRE_PROGRES]["FillColor1"])))

    bord = int(_pc_err(noeud, "border", TYPE_BARRE_PROGRES, "BorderSize", 1) or 0)
    if bord > 0:
        _peindre_bordure(painter, rect, bord, couleur(
            _pc_err(noeud, "border_color", TYPE_BARRE_PROGRES, "BorderColor",
                    THEME_BGUI_DEFAUT[TYPE_BARRE_PROGRES]["BorderColor"])))

    painter.setPen(QColor(230, 230, 230))
    painter.drawText(rect, Qt.AlignCenter, f"{percent * 100:.0f} %")


def peindre_bloc_texte(painter, rect, noeud):
    """Dessine un TextBlock BGUI : texte multi-lignes avec retour à la ligne."""
    texte = str(noeud.prop.get("text", ""))
    if not texte:
        return
    pt = int(_pc_err(noeud, "pt_size", TYPE_LABEL, "Size",
                     THEME_BGUI_DEFAUT[TYPE_LABEL]["Size"]))
    painter.setFont(police(pt, _famille_police(noeud)))
    painter.setPen(couleur(_pc_err(noeud, "color", TYPE_LABEL, "Color",
                                   THEME_BGUI_DEFAUT[TYPE_LABEL]["Color"])))
    painter.drawText(rect.adjusted(4, 4, -4, -4),
                     Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, texte)


def peindre_saisie_texte(painter, rect, noeud):
    """Dessine un TextInput BGUI : cadre, préfixe, texte et curseur."""
    actif = bool(noeud.prop.get("active", False))
    fond = couleur(_pc_err(noeud, "frame_color", TYPE_SAISIE_TEXTE,
                           "FrameColor" if actif else "InactiveFrameColor",
                           THEME_BGUI_DEFAUT[TYPE_SAISIE_TEXTE]["FrameColor"]))
    if fond.alpha() > 0:
        painter.fillRect(rect, fond)

    bord = int(_pc_err(noeud, "border", TYPE_SAISIE_TEXTE,
                       "BorderSize" if actif else "InactiveBorderSize", 0) or 0)
    if bord > 0:
        _peindre_bordure(painter, rect, bord, couleur(
            _pc_err(noeud, "border_color", TYPE_SAISIE_TEXTE,
                    "BorderColor" if actif else "InactiveBorderColor",
                    THEME_BGUI_DEFAUT[TYPE_SAISIE_TEXTE]["BorderColor"])))

    pt = int(_pc_err(noeud, "pt_size", TYPE_LABEL, "Size",
                     THEME_BGUI_DEFAUT[TYPE_LABEL]["Size"]))
    painter.setFont(police(pt, _famille_police(noeud)))
    couleur_texte = _pc_err(noeud, "color", TYPE_SAISIE_TEXTE,
                            "TextColor" if actif else "InactiveTextColor",
                            THEME_BGUI_DEFAUT[TYPE_SAISIE_TEXTE]["TextColor"])
    prefixe = str(noeud.prop.get("prefix", ""))
    texte = str(noeud.prop.get("text", ""))

    x = rect.left() + 6
    rect_texte = QRectF(rect.left() + 6, rect.top(),
                        rect.width() - 12, rect.height())
    painter.setPen(couleur(couleur_texte))
    if prefixe:
        painter.drawText(rect_texte, Qt.AlignLeft | Qt.AlignVCenter, prefixe)
        x += painter.fontMetrics().horizontalAdvance(prefixe) + 2

    rect_texte.setLeft(x)
    painter.drawText(rect_texte, Qt.AlignLeft | Qt.AlignVCenter, texte)

    if actif:
        curseur = x + painter.fontMetrics().horizontalAdvance(texte)
        painter.drawLine(QPointF(curseur, rect.top() + 4),
                         QPointF(curseur, rect.bottom() - 4))


def peindre_video(painter, rect, noeud):
    """Dessine une Video BGUI : vignette, sinon le nom du fichier vidéo.

    Une vidéo n'est pas décodable en image statique ici : quand le fichier
    existe mais n'est pas une image, on affiche son nom sur un pavé sombre.
    La lecture réelle se fait dans UPBGE.
    """
    chemin = resoudre_chemin_fichier(str(noeud.prop.get("fichier", "")))
    if os.path.isfile(chemin):
        pix = _charger_image(chemin)
        if pix is not None:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.drawPixmap(QRect(rect.toRect()), pix)
        else:
            painter.fillRect(rect, QColor(18, 18, 20))
            painter.setPen(QColor(140, 140, 145))
            painter.drawText(rect.adjusted(6, 4, -6, -6),
                             Qt.AlignLeft | Qt.AlignTop,
                             os.path.basename(chemin) or "(vidéo)")
    else:
        _peindre_image_ou_pave(painter, rect, noeud, "vidéo manquante")

    hauteur_bande = max(8.0, rect.height() * 0.25)
    bande = QRectF(rect.left(), rect.bottom() - hauteur_bande,
                   rect.width(), hauteur_bande)
    painter.fillRect(bande, QColor(0, 0, 0, 150))

    cy = rect.bottom() - hauteur_bande / 2
    painter.setBrush(QColor(255, 255, 255))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(QPolygonF([
        QPointF(rect.center().x() - 8, cy - 9),
        QPointF(rect.center().x() - 8, cy + 9),
        QPointF(rect.center().x() + 12, cy),
    ]))


def peindre_widget(painter, rect, noeud):
    """Point d'entrée : dessine un widget selon son type."""
    if noeud.type == TYPE_FRAME:
        peindre_cadre(painter, rect, noeud)
    elif noeud.type == TYPE_FRAME_BOUTON:
        peindre_bouton(painter, rect, noeud)
    elif noeud.type == TYPE_LABEL:
        peindre_label(painter, rect, noeud)
    elif noeud.type == TYPE_IMAGE:
        peindre_image(painter, rect, noeud)
    elif noeud.type == TYPE_BOUTON_IMAGE:
        peindre_bouton_image(painter, rect, noeud)
    elif noeud.type == TYPE_LISTE:
        peindre_liste(painter, rect, noeud)
    elif noeud.type == TYPE_BARRE_PROGRES:
        peindre_barre_progres(painter, rect, noeud)
    elif noeud.type == TYPE_BLOC_TEXTE:
        peindre_bloc_texte(painter, rect, noeud)
    elif noeud.type == TYPE_SAISIE_TEXTE:
        peindre_saisie_texte(painter, rect, noeud)
    elif noeud.type == TYPE_VIDEO:
        peindre_video(painter, rect, noeud)