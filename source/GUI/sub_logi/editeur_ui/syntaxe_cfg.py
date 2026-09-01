"""Coloration syntaxique des fichiers ``*.cfg`` (format theme.cfg BGUI).

Règles :
- ``[Titre]`` et ``[Label:Titre]`` : crochets en orange, titre en blanc ;
- ``clé=valeur`` : clé en rouge, ``=`` en vert ;
- valeur :
  - numérique (ou tuple de nombres, éventuellement ``None``) : en bleu ;
  - texte : en marron ;
  - référence ``prop.nom`` : en violet.
"""

from __future__ import annotations

import re

from PySide6.QtGui import QBrush, QColor, QSyntaxHighlighter, QTextCharFormat

#: Couleurs de la coloration syntaxique des *.cfg.
COULEUR_CROCHET = QColor("#ffa500")   # orange
COULEUR_TITRE = QColor("#ffffff")     # blanc
COULEUR_CLE = QColor("#e06c75")       # rouge
COULEUR_EGAL = QColor("#98c379")      # vert
COULEUR_NOMBRE = QColor("#61afef")    # bleu
COULEUR_TEXTE = QColor("#ce9178")     # marron
COULEUR_REFERENCE = QColor("#c678dd")  # violet

#: Expression pour repérer les nombres d'une valeur (UUID compris).
_NOMBRE = re.compile(r"-?(?:\d+\.\d+|\d+)")


def classer_valeur_cfg(texte):
    """Classe la valeur d'une clé : ``reference``, ``numerique`` ou ``texte``.

    - ``prop.<nom>``                     -> reference
    - ``12``, ``1, 0.7, 0.1, 1``         -> numerique
    - ``None, 0, 0, 1, 1``               -> numerique (None toléré)
    - ``True``, ``hello``, vide          -> texte
    """
    t = texte.strip()
    if t.startswith("prop."):
        return "reference"
    morceaux = [m.strip() for m in t.split(",")]
    numerique = False
    for m in morceaux:
        if not m:
            continue
        if m.lower() == "none":
            continue
        try:
            float(m)
        except ValueError:
            return "texte"
        numerique = True
    return "numerique" if numerique else "texte"


def _format(couleur):
    fmt = QTextCharFormat()
    fmt.setForeground(QBrush(couleur))
    return fmt


class SyntaxeCfgCfg(QSyntaxHighlighter):
    """Applique la coloration syntaxique à un QPlainTextEdit/QTextEdit."""

    def __init__(self, document):
        super().__init__(document)
        self._fmt_crochet = _format(COULEUR_CROCHET)
        self._fmt_titre = _format(COULEUR_TITRE)
        self._fmt_cle = _format(COULEUR_CLE)
        self._fmt_egal = _format(COULEUR_EGAL)
        self._fmt_nombre = _format(COULEUR_NOMBRE)
        self._fmt_texte = _format(COULEUR_TEXTE)
        self._fmt_reference = _format(COULEUR_REFERENCE)

    def highlightBlock(self, texte):
        ligne = texte.strip()
        if not ligne or ligne.startswith("#") or ligne.startswith(";"):
            return

        # Section [Titre] / [Label:Titre]
        if ligne.startswith("[") and ligne.endswith("]"):
            debut = texte.find("[")
            fin = texte.rfind("]")
            self.setFormat(debut, 1, self._fmt_crochet)
            self.setFormat(fin, 1, self._fmt_crochet)
            if fin > debut + 1:
                self.setFormat(debut + 1, fin - debut - 1, self._fmt_titre)
            return

        # clé = valeur
        egal = texte.find("=")
        if egal < 0:
            return
        debut_cle = len(texte) - len(texte.lstrip())
        if egal > debut_cle:
            self.setFormat(debut_cle, egal - debut_cle, self._fmt_cle)
        self.setFormat(egal, 1, self._fmt_egal)

        valeur = texte[egal + 1:]
        debut_valeur = egal + 1 + len(valeur) - len(valeur.lstrip())
        valeur = valeur.lstrip()
        if not valeur:
            return

        if classer_valeur_cfg(valeur) == "reference":
            self.setFormat(debut_valeur, len(valeur), self._fmt_reference)
            return

        mode = classer_valeur_cfg(valeur)
        self.setFormat(debut_valeur, len(valeur), self._fmt_texte)
        if mode == "numerique":
            for m in _NOMBRE.finditer(valeur):
                self.setFormat(debut_valeur + m.start(),
                               m.end() - m.start(),
                               self._fmt_nombre)