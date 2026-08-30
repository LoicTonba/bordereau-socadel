"""Primitives de dessin des diagrammes UML.

Les diagrammes sont tracés plutôt qu'importés en image : ils restent nets à
l'impression, se régénèrent avec le document, et suivent la charte SOCADEL.

Toutes les fonctions travaillent sur un `Drawing` reportlab et raisonnent en
points, origine en bas à gauche.
"""

from __future__ import annotations

from dataclasses import dataclass

from reportlab.graphics.shapes import (
    Circle,
    Drawing,
    Line,
    Polygon,
    Rect,
    String,
)
from reportlab.lib import colors

# --- Charte ----------------------------------------------------------------

BLEU = colors.HexColor("#1A76B9")
BLEU_SOMBRE = colors.HexColor("#1F5FA0")
BLEU_CLAIR = colors.HexColor("#E8F1FA")
BLEU_TRES_CLAIR = colors.HexColor("#F4F9FD")
BLANC = colors.white
GRIS = colors.HexColor("#64748B")
GRIS_CLAIR = colors.HexColor("#CBD5E1")
GRIS_FOND = colors.HexColor("#F1F5F9")
TEXTE = colors.HexColor("#0F172A")
VERT = colors.HexColor("#16A34A")
ORANGE = colors.HexColor("#EA7B34")
ROUGE = colors.HexColor("#DC2626")

POLICE = "Helvetica"
POLICE_GRAS = "Helvetica-Bold"
POLICE_ITAL = "Helvetica-Oblique"


@dataclass(frozen=True)
class Boite:
    """Rectangle positionné, avec de quoi s'ancrer aux autres."""

    x: float
    y: float
    largeur: float
    hauteur: float

    @property
    def centre_x(self) -> float:
        return self.x + self.largeur / 2

    @property
    def centre_y(self) -> float:
        return self.y + self.hauteur / 2

    @property
    def haut(self) -> float:
        return self.y + self.hauteur

    @property
    def droite(self) -> float:
        return self.x + self.largeur


def texte(
    d: Drawing,
    x: float,
    y: float,
    contenu: str,
    *,
    taille: float = 8,
    couleur=TEXTE,
    police: str = POLICE,
    ancrage: str = "start",
) -> None:
    d.add(
        String(
            x,
            y,
            contenu,
            fontName=police,
            fontSize=taille,
            fillColor=couleur,
            textAnchor=ancrage,
        )
    )


def _lignes_ajustees(contenu: str, largeur: float, taille: float) -> list[str]:
    """Découpe un libellé pour qu'il tienne dans la largeur donnée.

    Approximation volontairement simple : la largeur moyenne d'un caractère
    Helvetica vaut environ 0,5 em, ce qui suffit pour des libellés courts.
    """
    max_car = max(4, int(largeur / (taille * 0.5)))
    mots, lignes, courante = contenu.split(), [], ""
    for mot in mots:
        candidat = f"{courante} {mot}".strip()
        if len(candidat) <= max_car:
            courante = candidat
        else:
            if courante:
                lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


def boite(
    d: Drawing,
    x: float,
    y: float,
    largeur: float,
    hauteur: float,
    libelle: str,
    *,
    fond=BLANC,
    bordure=BLEU,
    couleur_texte=TEXTE,
    taille: float = 8,
    police: str = POLICE,
    rayon: float = 3,
    epaisseur: float = 1,
    sous_titre: str | None = None,
) -> Boite:
    """Trace un rectangle arrondi et y centre son libellé."""
    d.add(
        Rect(
            x,
            y,
            largeur,
            hauteur,
            rx=rayon,
            ry=rayon,
            fillColor=fond,
            strokeColor=bordure,
            strokeWidth=epaisseur,
        )
    )

    lignes = _lignes_ajustees(libelle, largeur - 8, taille)
    if sous_titre:
        lignes = lignes + _lignes_ajustees(sous_titre, largeur - 8, taille - 1)

    hauteur_bloc = len(lignes) * (taille + 2)
    depart = y + hauteur / 2 + hauteur_bloc / 2 - taille

    for index, ligne in enumerate(lignes):
        principale = index < len(_lignes_ajustees(libelle, largeur - 8, taille))
        texte(
            d,
            x + largeur / 2,
            depart - index * (taille + 2),
            ligne,
            taille=taille if principale else taille - 1,
            couleur=couleur_texte if principale else GRIS,
            police=police if principale else POLICE,
            ancrage="middle",
        )

    return Boite(x, y, largeur, hauteur)


def fleche(
    d: Drawing,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    couleur=GRIS,
    epaisseur: float = 1,
    pointe: bool = True,
    pointillee: bool = False,
    libelle: str | None = None,
    taille_libelle: float = 7,
) -> None:
    """Trace un segment orienté, éventuellement annoté."""
    ligne = Line(x1, y1, x2, y2, strokeColor=couleur, strokeWidth=epaisseur)
    if pointillee:
        ligne.strokeDashArray = [3, 2]
    d.add(ligne)

    if pointe:
        _pointe(d, x1, y1, x2, y2, couleur)

    if libelle:
        # Le libellé est posé au milieu, légèrement au-dessus du trait.
        texte(
            d,
            (x1 + x2) / 2,
            (y1 + y2) / 2 + 3,
            libelle,
            taille=taille_libelle,
            couleur=GRIS,
            ancrage="middle",
        )


def _pointe(d: Drawing, x1: float, y1: float, x2: float, y2: float, couleur) -> None:
    """Triangle de fin de flèche, orienté par le segment."""
    import math

    angle = math.atan2(y2 - y1, x2 - x1)
    longueur, ouverture = 6.0, 0.42

    d.add(
        Polygon(
            [
                x2,
                y2,
                x2 - longueur * math.cos(angle - ouverture),
                y2 - longueur * math.sin(angle - ouverture),
                x2 - longueur * math.cos(angle + ouverture),
                y2 - longueur * math.sin(angle + ouverture),
            ],
            fillColor=couleur,
            strokeColor=couleur,
        )
    )


def acteur(
    d: Drawing, x: float, y: float, nom: str, *, couleur=BLEU_SOMBRE, role: str | None = None
) -> None:
    """Bonhomme-bâton UML, `(x, y)` étant le bas de la silhouette."""
    tete = 5.0
    d.add(
        Circle(x, y + 26, tete, fillColor=BLANC, strokeColor=couleur, strokeWidth=1.4)
    )
    d.add(Line(x, y + 21, x, y + 9, strokeColor=couleur, strokeWidth=1.4))
    d.add(Line(x - 8, y + 17, x + 8, y + 17, strokeColor=couleur, strokeWidth=1.4))
    d.add(Line(x, y + 9, x - 6, y, strokeColor=couleur, strokeWidth=1.4))
    d.add(Line(x, y + 9, x + 6, y, strokeColor=couleur, strokeWidth=1.4))

    texte(d, x, y - 9, nom, taille=7.5, police=POLICE_GRAS, ancrage="middle")
    if role:
        texte(d, x, y - 18, role, taille=6.5, couleur=GRIS, ancrage="middle")


def cas_utilisation(
    d: Drawing,
    x: float,
    y: float,
    largeur: float,
    hauteur: float,
    libelle: str,
    *,
    fond=BLEU_TRES_CLAIR,
    bordure=BLEU,
) -> Boite:
    """Ellipse de cas d'utilisation, approchée par un rectangle très arrondi.

    reportlab ne dessine pas de texte le long d'une ellipse : le rectangle à
    grand rayon reste lisible et évite les débordements de libellé.
    """
    return boite(
        d,
        x,
        y,
        largeur,
        hauteur,
        libelle,
        fond=fond,
        bordure=bordure,
        rayon=hauteur / 2,
        taille=7,
    )


def cadre_systeme(
    d: Drawing, x: float, y: float, largeur: float, hauteur: float, titre: str
) -> None:
    """Frontière du système, avec son nom en haut."""
    d.add(
        Rect(
            x,
            y,
            largeur,
            hauteur,
            rx=4,
            ry=4,
            fillColor=None,
            strokeColor=GRIS_CLAIR,
            strokeWidth=1,
        )
    )
    d.add(
        Rect(
            x,
            y + hauteur - 16,
            largeur,
            16,
            rx=4,
            ry=4,
            fillColor=GRIS_FOND,
            strokeColor=GRIS_CLAIR,
            strokeWidth=1,
        )
    )
    texte(
        d,
        x + largeur / 2,
        y + hauteur - 11,
        titre,
        taille=7.5,
        police=POLICE_GRAS,
        couleur=BLEU_SOMBRE,
        ancrage="middle",
    )


def classe(
    d: Drawing,
    x: float,
    y: float,
    largeur: float,
    nom: str,
    attributs: list[str],
    *,
    stereotype: str | None = None,
    fond=BLANC,
    bordure=BLEU,
) -> Boite:
    """Classe UML : compartiment de nom, puis compartiment d'attributs."""
    ligne_h = 9.5
    hauteur_nom = 16 + (8 if stereotype else 0)
    hauteur = hauteur_nom + len(attributs) * ligne_h + 6

    d.add(
        Rect(
            x,
            y,
            largeur,
            hauteur,
            fillColor=fond,
            strokeColor=bordure,
            strokeWidth=1,
        )
    )
    d.add(
        Rect(
            x,
            y + hauteur - hauteur_nom,
            largeur,
            hauteur_nom,
            fillColor=BLEU_CLAIR,
            strokeColor=bordure,
            strokeWidth=1,
        )
    )

    haut = y + hauteur - 11
    if stereotype:
        texte(
            d,
            x + largeur / 2,
            haut,
            f"«{stereotype}»",
            taille=6.5,
            couleur=GRIS,
            police=POLICE_ITAL,
            ancrage="middle",
        )
        haut -= 8

    texte(
        d,
        x + largeur / 2,
        haut,
        nom,
        taille=8,
        police=POLICE_GRAS,
        couleur=BLEU_SOMBRE,
        ancrage="middle",
    )

    for index, attribut in enumerate(attributs):
        texte(
            d,
            x + 5,
            y + hauteur - hauteur_nom - 9 - index * ligne_h,
            attribut,
            taille=6.8,
            couleur=TEXTE,
        )

    return Boite(x, y, largeur, hauteur)


def losange(d: Drawing, x: float, y: float, taille: float = 5, plein: bool = True) -> None:
    """Losange de composition (plein) ou d'agrégation (creux)."""
    d.add(
        Polygon(
            [x, y + taille, x + taille, y, x, y - taille, x - taille, y],
            fillColor=BLEU if plein else BLANC,
            strokeColor=BLEU,
            strokeWidth=1,
        )
    )


def ligne_de_vie(
    d: Drawing, x: float, haut: float, bas: float, libelle: str, largeur: float = 78
) -> float:
    """En-tête de participant et sa ligne de vie verticale.

    Returns:
        L'abscisse centrale, pour y accrocher les messages.
    """
    boite(
        d,
        x - largeur / 2,
        haut - 18,
        largeur,
        18,
        libelle,
        fond=BLEU_CLAIR,
        bordure=BLEU,
        taille=7,
        police=POLICE_GRAS,
    )
    trait = Line(x, haut - 18, x, bas, strokeColor=GRIS_CLAIR, strokeWidth=1)
    trait.strokeDashArray = [3, 3]
    d.add(trait)
    return x


def activation(d: Drawing, x: float, haut: float, bas: float) -> None:
    """Barre d'activation d'un participant."""
    d.add(
        Rect(
            x - 3.5,
            bas,
            7,
            haut - bas,
            fillColor=BLEU_CLAIR,
            strokeColor=BLEU,
            strokeWidth=0.8,
        )
    )


def message(
    d: Drawing,
    x1: float,
    x2: float,
    y: float,
    libelle: str,
    *,
    retour: bool = False,
) -> None:
    """Message de séquence, plein à l'aller et pointillé au retour."""
    fleche(
        d,
        x1,
        y,
        x2,
        y,
        couleur=GRIS if retour else BLEU_SOMBRE,
        pointillee=retour,
        epaisseur=1,
    )
    texte(
        d,
        (x1 + x2) / 2,
        y + 3.5,
        libelle,
        taille=6.6,
        couleur=GRIS if retour else TEXTE,
        ancrage="middle",
    )


def note(
    d: Drawing, x: float, y: float, largeur: float, hauteur: float, contenu: str
) -> None:
    """Note UML : rectangle au coin supérieur droit replié."""
    pli = 8.0
    d.add(
        Polygon(
            [
                x, y,
                x, y + hauteur,
                x + largeur - pli, y + hauteur,
                x + largeur, y + hauteur - pli,
                x + largeur, y,
            ],
            fillColor=colors.HexColor("#FFFBEB"),
            strokeColor=colors.HexColor("#F59E0B"),
            strokeWidth=0.8,
        )
    )
    d.add(
        Line(
            x + largeur - pli, y + hauteur,
            x + largeur - pli, y + hauteur - pli,
            strokeColor=colors.HexColor("#F59E0B"), strokeWidth=0.8,
        )
    )
    d.add(
        Line(
            x + largeur - pli, y + hauteur - pli,
            x + largeur, y + hauteur - pli,
            strokeColor=colors.HexColor("#F59E0B"), strokeWidth=0.8,
        )
    )

    for index, ligne in enumerate(_lignes_ajustees(contenu, largeur - 12, 6.6)):
        texte(
            d,
            x + 6,
            y + hauteur - 12 - index * 8.5,
            ligne,
            taille=6.6,
            couleur=colors.HexColor("#92400E"),
        )
