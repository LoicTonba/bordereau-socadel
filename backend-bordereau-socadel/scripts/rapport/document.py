"""Assemblage du dossier de conception.

Le document est généré, pas rédigé à la main : il suit donc le code, et une
évolution du modèle se répercute en relançant le script.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from . import diagrammes
from .dessin import BLEU, BLEU_CLAIR, BLEU_SOMBRE, GRIS_CLAIR, GRIS_FOND

# Le filigrane du produit sert aussi au dossier : même origine, même marque.
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from bordereau.infrastructure.files.exporters.filigrane import (  # noqa: E402
    dessiner_filigrane,
    dessiner_logo_entete,
)

GRIS_TEXTE = colors.HexColor("#334155")
GRIS_DOUX = colors.HexColor("#64748B")


# --- Styles ----------------------------------------------------------------


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titre_couverture": ParagraphStyle(
            "TitreCouverture", parent=base["Title"], fontSize=26, leading=31,
            textColor=BLEU_SOMBRE, alignment=TA_CENTER, spaceAfter=8,
        ),
        "sous_titre_couverture": ParagraphStyle(
            "SousTitreCouverture", parent=base["Normal"], fontSize=12, leading=17,
            textColor=GRIS_TEXTE, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontSize=17, leading=21,
            textColor=BLEU_SOMBRE, spaceBefore=4, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontSize=12.5, leading=16,
            textColor=BLEU, spaceBefore=14, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontSize=10.5, leading=14,
            textColor=GRIS_TEXTE, spaceBefore=10, spaceAfter=4,
        ),
        "corps": ParagraphStyle(
            "Corps", parent=base["Normal"], fontSize=9.3, leading=14,
            textColor=GRIS_TEXTE, alignment=TA_JUSTIFY, spaceAfter=7,
        ),
        "puce": ParagraphStyle(
            "Puce", parent=base["Normal"], fontSize=9.3, leading=13.5,
            textColor=GRIS_TEXTE, leftIndent=13, bulletIndent=3, spaceAfter=4,
        ),
        "legende": ParagraphStyle(
            "Legende", parent=base["Normal"], fontSize=8, leading=11,
            textColor=GRIS_DOUX, alignment=TA_CENTER, spaceBefore=4,
            spaceAfter=12,
        ),
        "encadre": ParagraphStyle(
            "Encadre", parent=base["Normal"], fontSize=9, leading=13.5,
            textColor=GRIS_TEXTE, alignment=TA_JUSTIFY,
        ),
    }


S = _styles()


def p(contenu: str, style: str = "corps") -> Paragraph:
    return Paragraph(contenu, S[style])


def puces(elements: list[str]) -> list[Paragraph]:
    return [Paragraph(e, S["puce"], bulletText="•") for e in elements]


def titre(contenu: str, niveau: str = "h2") -> Paragraph:
    return Paragraph(contenu, S[niveau])


def legende(contenu: str) -> Paragraph:
    return Paragraph(contenu, S["legende"])


#: Largeur utile du gabarit portrait, marges deduites. Les captures s'y
#: ajustent, ce qui evite d'avoir a connaitre leur taille en pixels.
LARGEUR_UTILE = 470.0


def capture(chemin: Path, legende_texte: str) -> KeepTogether:
    """Insère une capture d'écran à la largeur du texte, avec sa légende.

    L'image est mise à l'échelle d'après ses proportions réelles : les captures
    sont prises en haute densité pour rester nettes à l'impression, et une
    largeur imposée sans hauteur correspondante les déformerait.

    Le cadre gris n'est pas décoratif : sans lui, une capture au fond blanc se
    fond dans la page et le lecteur ne voit plus où l'écran commence.
    """
    largeur_px, hauteur_px = ImageReader(str(chemin)).getSize()
    largeur = LARGEUR_UTILE - 30
    hauteur = largeur * hauteur_px / largeur_px

    image = Image(str(chemin), width=largeur, height=hauteur)
    cadre = Table([[image]], colWidths=[largeur + 2], hAlign="CENTER")
    cadre.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.7, GRIS_CLAIR),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    return KeepTogether([cadre, Spacer(1, 2), legende(legende_texte)])


def encadre(contenu: str) -> Table:
    """Bloc mis en exergue, pour les décisions structurantes."""
    tableau = Table([[Paragraph(contenu, S["encadre"])]], colWidths=[470])
    tableau.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F9FD")),
                ("BOX", (0, 0), (-1, -1), 0.8, BLEU),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return tableau


def tableau(
    donnees: list[list[str]],
    largeurs: list[float],
    *,
    aligne_a_droite: list[int] | None = None,
    taille: float = 8,
) -> Table:
    """Tableau de données, en-tête aux couleurs de la charte."""
    cellules = [
        [Paragraph(f"<b>{c}</b>" if i == 0 else c, _style_cellule(i, taille))
         for c in ligne]
        for i, ligne in enumerate(donnees)
    ]

    t = Table(cellules, colWidths=largeurs, repeatRows=1)
    commandes = [
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, GRIS_CLAIR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_FOND]),
    ]
    for colonne in aligne_a_droite or []:
        commandes.append(("ALIGN", (colonne, 1), (colonne, -1), "CENTER"))

    t.setStyle(TableStyle(commandes))
    return t


def _style_cellule(index_ligne: int, taille: float) -> ParagraphStyle:
    return ParagraphStyle(
        f"Cellule{index_ligne}",
        fontName="Helvetica",
        fontSize=taille,
        leading=taille + 3,
        textColor=colors.white if index_ligne == 0 else GRIS_TEXTE,
    )


# --- Habillage des pages ---------------------------------------------------


#: Libellé du pied de page, renseigné par `construire`.
_PIED = "Dossier de conception"


def _habiller(canevas, document) -> None:
    """Filigrane, logo, pied de page, sur chaque page sauf la couverture."""
    largeur, hauteur = document.pagesize
    canevas.saveState()

    if canevas.getPageNumber() > 1:
        dessiner_filigrane(canevas, largeur, hauteur)
        dessiner_logo_entete(canevas, largeur - 18 * mm - 30 * mm,
                             hauteur - 16 * mm, 30 * mm)

        canevas.setStrokeColor(GRIS_CLAIR)
        canevas.setLineWidth(0.4)
        canevas.line(18 * mm, 13 * mm, largeur - 18 * mm, 13 * mm)

        canevas.setFont("Helvetica", 7)
        canevas.setFillColor(GRIS_DOUX)
        canevas.drawString(
            18 * mm, 9 * mm,
            f"Bordereau SOCADEL, {_PIED}  |  NEXT LTD × SOCADEL",
        )
        canevas.drawRightString(
            largeur - 18 * mm, 9 * mm, f"Page {canevas.getPageNumber()}"
        )
    else:
        # Couverture : bandeaux de couleur et logo en pleine opacité, plutôt
        # que le filigrane pâle des pages intérieures.
        canevas.setFillColor(BLEU)
        canevas.rect(0, hauteur - 8 * mm, largeur, 8 * mm, fill=1, stroke=0)
        canevas.setFillColor(BLEU_CLAIR)
        canevas.rect(0, 0, largeur, 5 * mm, fill=1, stroke=0)

        largeur_logo = 62 * mm
        dessiner_logo_entete(
            canevas,
            (largeur - largeur_logo) / 2,
            hauteur - 52 * mm,
            largeur_logo,
        )

        canevas.setFont("Helvetica", 8)
        canevas.setFillColor(GRIS_DOUX)
        canevas.drawCentredString(
            largeur / 2,
            22 * mm,
            "NEXT LTD, Numeric Export Technologies  ·  team@numericexport.com",
        )

    canevas.restoreState()


def construire(
    chemin: Path,
    contenu_fabrique,
    *,
    titre: str = "Bordereau SOCADEL, Dossier de conception",
    sujet: str = "Analyse, architecture et modélisation UML",
    pied: str = "Dossier de conception",
) -> None:
    """Monte le document sur deux gabarits : portrait et paysage.

    Les diagrammes de classes et le modèle de données sont trop larges pour le
    portrait ; le paysage évite de les réduire jusqu'à l'illisible.
    """
    global _PIED
    _PIED = pied

    document = BaseDocTemplate(
        str(chemin),
        pagesize=A4,
        title=titre,
        author="NEXT LTD, Numeric Export Technologies",
        subject=sujet,
    )

    largeur_p, hauteur_p = A4
    largeur_l, hauteur_l = landscape(A4)

    document.addPageTemplates(
        [
            PageTemplate(
                id="portrait",
                frames=[
                    Frame(18 * mm, 16 * mm, largeur_p - 36 * mm,
                          hauteur_p - 34 * mm, id="corps")
                ],
                onPage=_habiller,
                pagesize=A4,
            ),
            PageTemplate(
                id="paysage",
                frames=[
                    Frame(14 * mm, 16 * mm, largeur_l - 28 * mm,
                          hauteur_l - 34 * mm, id="corps_large")
                ],
                onPage=_habiller,
                pagesize=landscape(A4),
            ),
        ]
    )

    document.build(contenu_fabrique())
