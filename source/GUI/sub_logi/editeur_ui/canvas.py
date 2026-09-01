"""Canvas de simulation de l'écran BGUI.

Ce widget est l'équivalent de la *viewport 2D* de Godot : il rend un arbre
de nœuds (voir modele.py) tel que BGUI le dessinerait dans l'écran du
moteur, et permet d'interagir avec la souris :

- clic            -> sélectionne le widget (le plus haut sous le curseur)
- glisser         -> déplace le widget sélectionné
- poignées coins  -> redimensionne le widget sélectionné

L'écran simulé est adapté (fit) dans le widget. Les coordonnées manipulées
sont converties de/normalisées (0..1, relatives au parent), ce sont celles
stockées dans le modèle.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .modele import CALQUE_BASE, TYPE_SCREEN, NoeudUI
from .modele import calques_ecran
from .theme_bgui import THEME_BGUI, couleur, peindre_widget

TAILLE_POIGNEE = 8.0
ACCENT = QColor(74, 144, 217)


class CanvasBGUI(QWidget):
    """Vue de simulation de l'écran UPBGE."""

    selection_changee = Signal(object)      # nœud sélectionné (ou None)
    modele_change = Signal()                # l'arbre a été modifié
    geo_changee = Signal(object)            # pos/size modifiés (nœud)
    souris_changee = Signal(float, float, float, float)
                                            # px_x, px_y, norm_x, norm_y

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = None                   # NoeudUI racine (Screen)
        self.selection = None               # nœud sélectionné
        self.calque_actif = CALQUE_BASE     # nom du calque affiché
        self.ordre_peinture = []            # [(noeud, rect_scene)] affichés
        self.carte_parent = {}              # id(noeud) -> rect_scene parent
        self._noeud_vers_rect = {}          # id(noeud) -> rect_scene
        self.scale = 1.0
        self.origine = QPointF(0.0, 0.0)
        self.interaction = None             # dict d'état du glisser
        self.sur_poignee = None             # poignée survolée (hg|hd|bg|bd)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    # ------------------------------------------------------------------
    # API publique (utilisée par l'éditeur)
    # ------------------------------------------------------------------

    def definir_scene(self, racine):
        """Remplace la scène affichée et réinitialise la sélection."""
        self.scene = racine
        self.selection = None
        self.calque_actif = CALQUE_BASE     # on commence par le calque de base
        self.rafraichir()
        self.modele_change.emit()

    def selection_actuelle(self):
        return self.selection

    def definir_selection(self, noeud):
        if noeud is self.selection:
            return
        self.selection = noeud
        self.update()
        self.selection_changee.emit(noeud)

    def taille_ecran(self):
        """Dimensions (largeur, hauteur) de l'écran simulé en pixels."""
        if self.scene is None:
            return 1280, 720
        l, h = self.scene.prop.get("res", [1280, 720])
        return int(l), int(h)

    def maj_taille_ecran(self, largeur, hauteur):
        if self.scene is None:
            return
        self.scene.prop["res"] = [int(largeur), int(hauteur)]
        self.rafraichir()

    def _couleur_fond_ecran(self):
        """Couleur de fond de l'écran dans l'aperçu (propriété « Color »).

        Vaut ``self.scene.prop["color"]`` si elle est réglée (propriété de
        l'inspecteur Screen), sinon la couleur du thème. Ne sert qu'au
        logiciel (aperçu) et n'est jamais exportée dans le script généré.
        """
        if self.scene is None:
            return couleur(THEME_BGUI[TYPE_SCREEN]["fond"])
        c = self.scene.prop.get("color")
        if isinstance(c, (list, tuple)) and len(c) >= 3:
            return couleur(tuple(float(v) for v in c[:4]))
        return couleur(THEME_BGUI[TYPE_SCREEN]["fond"])

    def rafraichir(self):
        """Reconstruit l'ordre de peinture et redessine."""
        self._construire_arbres()
        self.update()

    def calques(self):
        """Noms des calques de la scène affichée (défaut : ``start``)."""
        if self.scene is None:
            return [CALQUE_BASE]
        return calques_ecran(self.scene)

    def set_calque_actif(self, nom):
        """Affiche le calque nommé (retourne ``False`` si inconnu)."""
        if self.scene is None or nom not in self.calques():
            return False
        self.calque_actif = nom
        self.rafraichir()
        return True

    def def_base_projet(self, chemin_base):
        """Change la base de résolution des chemins « // » puis redessine.

        Les images/vidéos dont le chemin commence par ``//`` sont résolues
        par theme_bgui.resoudre_chemin_fichier, qui lit la base courante
        au moment du rendu : un simple rafraîchissement suffit pour tenir
        compte du nouveau dossier.
        """
        self.rafraichir()

    def rect_parent_scene(self, noeud):
        """Rectangle (pixels de scène) du parent utilisé pour la
        normalisation de pos/size. Vaut l'écran entier pour la racine."""
        if noeud is None:
            return QRectF(0, 0, *self.taille_ecran())
        return self.carte_parent.get(id(noeud),
                                     QRectF(0, 0, *self.taille_ecran()))

    def rect_scene(self, noeud):
        """Rectangle du nœud en pixels de scène (None si non affiché)."""
        return self._noeud_vers_rect.get(id(noeud))

    def parent_de(self, racine, cible):
        """Retourne le nœud parent de `cible` (ou None si c'est la racine)."""
        for e in racine.enfants:
            if e is cible:
                return racine
            res = self.parent_de(e, cible)
            if res is not None:
                return res
        return None

    # ------------------------------------------------------------------
    # Construction de l'ordre de peinture (layout récursif)
    # ------------------------------------------------------------------

    def _construire_arbres(self):
        self.ordre_peinture = []
        self.carte_parent = {}
        self._noeud_vers_rect = {}
        if self.scene is None:
            return
        ec_l, ec_h = self.taille_ecran()
        rect_ecran = QRectF(0, 0, ec_l, ec_h)
        self.carte_parent[id(self.scene)] = rect_ecran
        self._parcourir(self.scene, rect_ecran)

    def _parcourir(self, noeud, rect_parent):
        enfants = noeud.enfants
        if noeud is self.scene:
            # Un Screen n'affiche que les enfants du calque actif ; le reste
            # de la hiérarchie (sous un Frame) suit son conteneur.
            base = self.calques()[0]
            enfants = [e for e in noeud.enfants
                       if e.prop.get("calque", base) == self.calque_actif]
        for enfant in sorted(enfants,
                             key=lambda n: n.prop.get("z_index", 0)):
            if not enfant.prop.get("visible", True):
                continue
            rect = self._rect_enfant(enfant, rect_parent)
            if rect.width() > 0 and rect.height() > 0:
                self.ordre_peinture.append((enfant, rect))
                self._noeud_vers_rect[id(enfant)] = rect
                self.carte_parent[id(enfant)] = QRectF(rect_parent)
                self._parcourir(enfant, rect)

    @staticmethod
    def _rect_enfant(noeud, rect_parent):
        """Rectangle (pixels de scène) d'un enfant dans SON parent.

        BGUI : l'origine (0,0) est en bas à gauche et y croît vers le haut.
        `pos` est le coin bas-gauche du widget, `size` s'étend en x vers la
        droite et en y vers le haut. Qt, lui, travaille en y descendant : on
        retourne donc le rectangle converti.
        """
        pos = noeud.prop.get("pos", [0.0, 0.0])
        size = noeud.prop.get("size", [1.0, 1.0])
        haut = (1.0 - pos[1] - size[1]) * rect_parent.height()
        return QRectF(rect_parent.x() + pos[0] * rect_parent.width(),
                      rect_parent.y() + haut,
                      size[0] * rect_parent.width(),
                      size[1] * rect_parent.height())

    # ------------------------------------------------------------------
    # Transformations de coordonnées (widget <-> scène)
    # ------------------------------------------------------------------

    def _scene_a_widget(self, pt_scene):
        return QPointF(pt_scene.x() * self.scale + self.origine.x(),
                       pt_scene.y() * self.scale + self.origine.y())

    def _widget_a_scene(self, pt_widget):
        if self.scale <= 0:
            return pt_widget
        return QPointF((pt_widget.x() - self.origine.x()) / self.scale,
                       (pt_widget.y() - self.origine.y()) / self.scale)

    def _scene_a_widget_rect(self, r):
        return QRectF(r.x() * self.scale + self.origine.x(),
                      r.y() * self.scale + self.origine.y(),
                      r.width() * self.scale, r.height() * self.scale)

    def _calculer_affichage(self):
        w, h = max(1, self.width()), max(1, self.height())
        ec_l, ec_h = self.taille_ecran()
        if ec_l <= 0 or ec_h <= 0:
            self.scale = 1.0
            self.origine = QPointF(0, 0)
            return
        self.scale = min(w / ec_l, h / ec_h)
        self.origine = QPointF((w - ec_l * self.scale) / 2.0,
                               (h - ec_h * self.scale) / 2.0)

    # ------------------------------------------------------------------
    # Interaction souris
    # ------------------------------------------------------------------

    def _poignees(self, rect_widget):
        return {
            "hg": QPointF(rect_widget.left(), rect_widget.top()),
            "hd": QPointF(rect_widget.right(), rect_widget.top()),
            "bg": QPointF(rect_widget.left(), rect_widget.bottom()),
            "bd": QPointF(rect_widget.right(), rect_widget.bottom()),
        }

    def _poignee_sous_souris(self, pos_widget, rect_scene):
        rect_widget = self._scene_a_widget_rect(rect_scene)
        for nom, pt in self._poignees(rect_widget).items():
            if (abs(pos_widget.x() - pt.x()) <= TAILLE_POIGNEE / 2 + 2 and
                    abs(pos_widget.y() - pt.y()) <= TAILLE_POIGNEE / 2 + 2):
                return nom
        return None

    def _noeud_sous_souris(self, pt_scene):
        for noeud, rect in reversed(self.ordre_peinture):
            if rect.contains(pt_scene):
                return noeud
        return None

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.scene is None:
            return super().mousePressEvent(event)

        pos_widget = QPointF(event.position())
        pt_scene = self._widget_a_scene(pos_widget)
        ec_l, ec_h = self.taille_ecran()
        if not (0 <= pt_scene.x() <= ec_l and 0 <= pt_scene.y() <= ec_h):
            return

        rect_sel = self.rect_scene(self.selection)
        if rect_sel is not None:
            coin = self._poignee_sous_souris(pos_widget, rect_sel)
            if coin:
                parent = self.rect_parent_scene(self.selection)
                self.interaction = {
                    "zone": "resize", "coin": coin, "debut": pt_scene,
                    "pos_debut": list(self.selection.prop.get("pos", [0, 0])),
                    "taille_debut": list(self.selection.prop.get("size", [1, 1])),
                    "taille_parent": (parent.width(), parent.height()),
                }
                return

        noeud = self._noeud_sous_souris(pt_scene)
        self.definir_selection(noeud)
        if noeud is not None:
            parent = self.rect_parent_scene(noeud)
            self.interaction = {
                "zone": "move", "noeud": noeud, "debut": pt_scene,
                "pos_debut": list(noeud.prop.get("pos", [0, 0])),
                "taille_parent": (parent.width(), parent.height()),
            }

    def mouseMoveEvent(self, event):
        pos_widget = QPointF(event.position())
        pt_scene = self._widget_a_scene(pos_widget)

        rect_sel = self.rect_scene(self.selection)
        poignee = None
        if rect_sel is not None:
            poignee = self._poignee_sous_souris(pos_widget, rect_sel)
        if poignee and self.interaction is None:
            self.setCursor(Qt.SizeFDiagCursor if poignee in ("hg", "bd")
                           else Qt.SizeBDiagCursor)
        elif self.interaction is None:
            self.unsetCursor()
        self.sur_poignee = poignee

        if self.interaction is not None:
            info = self.interaction
            dx = pt_scene.x() - info["debut"].x()
            dy = pt_scene.y() - info["debut"].y()
            p_l, p_h = info["taille_parent"]
            cible = info.get("noeud", self.selection)
            if cible is None:
                self.interaction = None
                return

            if info["zone"] == "move":
                self._deplacer(cible, info, dx, dy, p_l, p_h)
            else:
                self._redimensionner(cible, info, dx, dy, p_l, p_h)
            self._construire_arbres()
            self.update()
            self.geo_changee.emit(cible)

        ec_l, ec_h = self.taille_ecran()
        self.souris_changee.emit(pt_scene.x(), pt_scene.y(),
                                 pt_scene.x() / ec_l,
                                 1.0 - pt_scene.y() / ec_h)

    def mouseReleaseEvent(self, event):
        self.interaction = None
        self.update()

    def leaveEvent(self, event):
        self.sur_poignee = None
        self.unsetCursor()

    # ------------------------------------------------------------------
    # Glisser / redimensionner (en valeurs normalisées relative au parent)
    # ------------------------------------------------------------------

    def _deplacer(self, noeud, info, dx, dy, p_l, p_h):
        px = info["pos_debut"][0] + (dx / p_l if p_l else 0.0)
        py = info["pos_debut"][1] - (dy / p_h if p_h else 0.0)
        noeud.prop["pos"] = [
            max(0.0, min(1.0, px)),
            max(0.0, min(1.0, py)),
        ]

    def _redimensionner(self, noeud, info, dx, dy, p_l, p_h):
        ndx = (dx / p_l) if p_l else 0.0
        ndy = (dy / p_h) if p_h else 0.0
        px0, py0 = info["pos_debut"]
        w0, h0 = info["taille_debut"]
        coin = info["coin"]

        if "g" in coin:
            px = px0 + ndx
            w = w0 - ndx
        else:
            px = px0
            w = w0 + ndx
        if "h" in coin:
            py = py0
            h = h0 - ndy
        else:
            py = py0 - ndy
            h = h0 + ndy

        w, h = max(0.01, w), max(0.01, h)
        px = max(0.0, min(1.0 - w, px))
        py = max(0.0, min(1.0 - h, py))
        noeud.prop["pos"] = [px, py]
        noeud.prop["size"] = [w, h]

    # ------------------------------------------------------------------
    # Peinture
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(26, 26, 28))
        if self.scene is None:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "Aucune scène : utilisez les boutons de la"
                             " barre d'outils pour ajouter des widgets")
            return

        ec_l, ec_h = self.taille_ecran()
        self._calculer_affichage()

        # écran + widgets (espace scène)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.save()
        painter.translate(self.origine)
        painter.scale(self.scale, self.scale)
        painter.fillRect(QRectF(0, 0, ec_l, ec_h),
                         self._couleur_fond_ecran())
        for noeud, rect in self.ordre_peinture:
            peindre_widget(painter, rect, noeud)
        painter.restore()

        # cadre de l'écran + libellé de résolution (espace widget)
        rect_ecran = QRectF(self.origine.x(), self.origine.y(),
                            ec_l * self.scale, ec_h * self.scale)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(QPen(QColor(90, 90, 95), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect_ecran)
        painter.setPen(QColor(200, 200, 205))
        painter.drawText(QPointF(rect_ecran.left() + 6,
                                 rect_ecran.top() + 14),
                         f"{ec_l} × {ec_h}")

        self._peindre_selection(painter)

    def _peindre_selection(self, painter):
        if self.selection is None:
            return
        rect_scene = self.rect_scene(self.selection)
        if rect_scene is None:
            return
        rect_widget = self._scene_a_widget_rect(rect_scene)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(ACCENT, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect_widget.adjusted(1, 1, -1, -1))

        for nom, pt in self._poignees(rect_widget).items():
            poignee = QRectF(pt.x() - TAILLE_POIGNEE / 2,
                             pt.y() - TAILLE_POIGNEE / 2,
                             TAILLE_POIGNEE, TAILLE_POIGNEE)
            if nom == self.sur_poignee:
                painter.setBrush(ACCENT.lighter(130))
            else:
                painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QPen(ACCENT, 1))
            painter.drawRect(poignee)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

    def sizeHint(self):
        return QSize(800, 500)