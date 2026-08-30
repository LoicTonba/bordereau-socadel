"""Rendu PDF d'un document Markdown, aux couleurs SOCADEL.

Volontairement limité à la syntaxe réellement employée par les guides du
dépôt, titres, paragraphes, listes, tableaux, blocs de code, citations et
filets. Embarquer un moteur Markdown complet pour six constructions serait
disproportionné, et le rendu serait moins maîtrisé.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .dessin import BLEU, BLEU_CLAIR, BLEU_SOMBRE, GRIS_CLAIR, GRIS_FOND

GRIS_TEXTE = colors.HexColor("#334155")
GRIS_DOUX = colors.HexColor("#64748B")
FOND_CODE = colors.HexColor("#F8FAFC")
FOND_CITATION = colors.HexColor("#FFFBEB")
BORD_CITATION = colors.HexColor("#F59E0B")

#: Largeur utile d'une page A4 portrait avec les marges du gabarit.
LARGEUR_UTILE = 470.0


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "GuideH1", parent=base["Heading1"], fontSize=18, leading=23,
            textColor=BLEU_SOMBRE, spaceBefore=2, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "GuideH2", parent=base["Heading2"], fontSize=13, leading=17,
            textColor=BLEU, spaceBefore=16, spaceAfter=7,
        ),
        "h3": ParagraphStyle(
            "GuideH3", parent=base["Heading3"], fontSize=10.5, leading=14,
            textColor=GRIS_TEXTE, spaceBefore=11, spaceAfter=4,
        ),
        "corps": ParagraphStyle(
            "GuideCorps", parent=base["Normal"], fontSize=9.4, leading=14.5,
            textColor=GRIS_TEXTE, alignment=TA_JUSTIFY, spaceAfter=7,
        ),
        "puce": ParagraphStyle(
            "GuidePuce", parent=base["Normal"], fontSize=9.4, leading=14,
            textColor=GRIS_TEXTE, leftIndent=15, bulletIndent=4, spaceAfter=4,
        ),
        "numero": ParagraphStyle(
            "GuideNumero", parent=base["Normal"], fontSize=9.4, leading=14,
            textColor=GRIS_TEXTE, leftIndent=19, bulletIndent=4, spaceAfter=5,
        ),
        "code": ParagraphStyle(
            "GuideCode", fontName="Courier", fontSize=8, leading=11.5,
            textColor=colors.HexColor("#0F172A"),
        ),
        "citation": ParagraphStyle(
            "GuideCitation", parent=base["Normal"], fontSize=9, leading=13.5,
            textColor=colors.HexColor("#92400E"), alignment=TA_JUSTIFY,
        ),
        "cellule": ParagraphStyle(
            "GuideCellule", fontName="Helvetica", fontSize=8, leading=11,
            textColor=GRIS_TEXTE,
        ),
        "cellule_entete": ParagraphStyle(
            "GuideCelluleEntete", fontName="Helvetica-Bold", fontSize=8,
            leading=11, textColor=colors.white,
        ),
        "couverture_titre": ParagraphStyle(
            "GuideCouvertureTitre", parent=base["Title"], fontSize=26, leading=32,
            textColor=BLEU_SOMBRE, alignment=TA_CENTER, spaceAfter=6,
        ),
        "couverture_sous": ParagraphStyle(
            "GuideCouvertureSous", parent=base["Normal"], fontSize=12, leading=17,
            textColor=GRIS_TEXTE, alignment=TA_CENTER,
        ),
    }


S = _styles()


# --- Formatage en ligne ----------------------------------------------------

_LIEN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_GRAS = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")


def inline(texte: str) -> str:
    """Traduit le formatage Markdown en balises reportlab.

    L'échappement XML vient en premier : sans lui, une esperluette ou un
    chevron présents dans le texte casseraient le rendu du paragraphe.
    """
    texte = (
        texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    # Le libellé du lien suffit : une URL cliquable dans un document imprimé
    # n'apporte rien, et l'adresse alourdit la ligne.
    texte = _LIEN.sub(
        lambda m: m.group(1)
        if m.group(2).startswith((".", "#"))
        else f'<link href="{m.group(2)}" color="#1A76B9">{m.group(1)}</link>',
        texte,
    )
    texte = _GRAS.sub(r"<b>\1</b>", texte)
    texte = _CODE.sub(
        r'<font face="Courier" size="8.4" color="#1F5FA0">\1</font>', texte
    )
    return texte


# --- Blocs -----------------------------------------------------------------


def bloc_code(lignes: list[str]) -> Flowable:
    """Bloc de commandes, sur fond gris pâle et en chasse fixe."""
    contenu = "<br/>".join(
        ligne.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace(" ", "&nbsp;")
        or "&nbsp;"
        for ligne in lignes
    )
    tableau = Table(
        [[Paragraph(contenu, S["code"])]], colWidths=[LARGEUR_UTILE]
    )
    tableau.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), FOND_CODE),
                ("BOX", (0, 0), (-1, -1), 0.6, GRIS_CLAIR),
                # Filet bleu à gauche : signale un bloc à exécuter.
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, BLEU),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return KeepTogether([tableau, Spacer(1, 6)])


def bloc_citation(lignes: list[str]) -> Flowable:
    """Encadré d'avertissement, repris des blocs `>` du Markdown."""
    tableau = Table(
        [[Paragraph(inline(" ".join(lignes)), S["citation"])]],
        colWidths=[LARGEUR_UTILE],
    )
    tableau.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), FOND_CITATION),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, BORD_CITATION),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return KeepTogether([tableau, Spacer(1, 7)])


def _est_separateur(ligne: str) -> bool:
    """Vrai pour la ligne `|---|---|` qui suit l'en-tête d'un tableau.

    Le tiret est exigé : `| | |` n'est pas un séparateur mais un **en-tête
    vide**, forme imposée par le Markdown quand le tableau n'a pas de titres
    de colonnes. Les confondre reviendrait à promouvoir la première ligne de
    données en en-tête.
    """
    return "-" in ligne and re.fullmatch(r"[\s|:-]+", ligne) is not None


def bloc_tableau(lignes: list[str]) -> Flowable:
    """Tableau Markdown, aux couleurs de la charte.

    Les largeurs de colonnes sont réparties au prorata de la longueur du
    contenu le plus long de chaque colonne : sans cela, une colonne d'une
    seule lettre occuperait autant qu'une colonne de phrase.
    """
    rangees = [
        [cellule.strip() for cellule in ligne.strip().strip("|").split("|")]
        for ligne in lignes
        if not _est_separateur(ligne)
    ]
    if not rangees:
        return Spacer(1, 0)

    colonnes = max(len(r) for r in rangees)
    rangees = [r + [""] * (colonnes - len(r)) for r in rangees]

    # Un tableau dont la première ligne est vide n'a pas d'en-tête : le
    # Markdown l'exige syntaxiquement, mais il ne faut pas le mettre en avant.
    avec_entete = any(cellule.strip() for cellule in rangees[0])
    if not avec_entete:
        rangees = rangees[1:]
        if not rangees:
            return Spacer(1, 0)

    poids = [
        max(len(rangee[index]) for rangee in rangees) or 1
        for index in range(colonnes)
    ]
    # La racine carrée compresse les écarts : sans elle, une colonne de phrase
    # écraserait les colonnes courtes jusqu'à les rendre illisibles.
    poids = [max(p, 8) ** 0.5 for p in poids]
    total = sum(poids)
    largeurs = [LARGEUR_UTILE * p / total for p in poids]

    cellules = [
        [
            Paragraph(
                inline(valeur),
                S["cellule_entete"]
                if (avec_entete and index == 0)
                else S["cellule"],
            )
            for valeur in rangee
        ]
        for index, rangee in enumerate(rangees)
    ]

    commandes = [
        ("GRID", (0, 0), (-1, -1), 0.4, GRIS_CLAIR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if avec_entete:
        commandes += [
            ("BACKGROUND", (0, 0), (-1, 0), BLEU),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_FOND]),
        ]
    else:
        # Sans en-tête, la première colonne fait office de libellé.
        commandes += [
            ("BACKGROUND", (0, 0), (0, -1), BLEU_CLAIR),
            ("TEXTCOLOR", (0, 0), (0, -1), BLEU_SOMBRE),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ]

    tableau = Table(cellules, colWidths=largeurs, repeatRows=1 if avec_entete else 0)
    tableau.setStyle(TableStyle(commandes))
    return KeepTogether([tableau, Spacer(1, 8)])


# --- Analyse du document ---------------------------------------------------


@dataclass
class _Etat:
    """Accumulateur du bloc en cours d'analyse."""

    elements: list = field(default_factory=list)
    tampon: list[str] = field(default_factory=list)
    mode: str | None = None

    puce: str | None = None
    """Marqueur de l'élément de liste en cours, s'il y en a un."""

    def vider(self) -> None:
        """Clôt le bloc courant et l'ajoute au document."""
        if not self.tampon:
            self.mode = None
            self.puce = None
            return

        match self.mode:
            case "code":
                self.elements.append(bloc_code(self.tampon))
            case "tableau":
                self.elements.append(bloc_tableau(self.tampon))
            case "citation":
                self.elements.append(bloc_citation(self.tampon))
            case "paragraphe":
                self.elements.append(
                    Paragraph(inline(" ".join(self.tampon)), S["corps"])
                )
            case "puce" | "numero":
                # Un élément de liste peut s'étendre sur plusieurs lignes du
                # Markdown : elles sont recollées avant le rendu, sinon un
                # `**gras**` à cheval sortirait avec ses astérisques.
                self.elements.append(
                    Paragraph(
                        inline(" ".join(self.tampon)),
                        S[self.mode],
                        bulletText=self.puce,
                    )
                )

        self.tampon = []
        self.mode = None
        self.puce = None


_TITRE = re.compile(r"^(#{1,4})\s+(.*)")
_PUCE = re.compile(r"^[-*]\s+(.*)")
_NUMERO = re.compile(r"^(\d+)\.\s+(.*)")


def convertir(markdown: str, *, ignorer_h1: bool = True) -> list:
    """Transforme un document Markdown en flowables reportlab.

    Args:
        markdown: le document source.
        ignorer_h1: n'émet pas le titre de niveau 1, celui-ci figurant déjà
            sur la page de couverture.
    """
    etat = _Etat()
    dans_code = False

    for ligne_brute in markdown.splitlines():
        ligne = ligne_brute.rstrip()

        # Les blocs de code se délimitent eux-mêmes : tout leur contenu est
        # pris tel quel, sans interprétation.
        if ligne.startswith("```"):
            if dans_code:
                etat.vider()
                dans_code = False
            else:
                etat.vider()
                etat.mode = "code"
                dans_code = True
            continue

        if dans_code:
            etat.tampon.append(ligne_brute)
            continue

        if not ligne.strip():
            etat.vider()
            continue

        if ligne.startswith("|"):
            if etat.mode != "tableau":
                etat.vider()
                etat.mode = "tableau"
            etat.tampon.append(ligne)
            continue

        if ligne.startswith(">"):
            if etat.mode != "citation":
                etat.vider()
                etat.mode = "citation"
            etat.tampon.append(ligne.lstrip("> ").rstrip())
            continue

        if re.fullmatch(r"-{3,}", ligne.strip()):
            etat.vider()
            etat.elements.append(Spacer(1, 4))
            etat.elements.append(
                HRFlowable(
                    width="100%", thickness=0.7, color=GRIS_CLAIR,
                    spaceBefore=2, spaceAfter=10,
                )
            )
            continue

        if (titre := _TITRE.match(ligne)) is not None:
            etat.vider()
            niveau = len(titre.group(1))
            if niveau == 1 and ignorer_h1:
                continue
            etat.elements.append(
                Paragraph(inline(titre.group(2)), S[f"h{min(niveau, 3)}"])
            )
            continue

        if (puce := _PUCE.match(ligne)) is not None:
            etat.vider()
            etat.mode = "puce"
            etat.puce = "•"
            etat.tampon.append(puce.group(1))
            continue

        if (numero := _NUMERO.match(ligne)) is not None:
            etat.vider()
            etat.mode = "numero"
            etat.puce = f"{numero.group(1)}."
            etat.tampon.append(numero.group(2))
            continue

        # Ligne ordinaire : elle prolonge l'élément de liste en cours, ou
        # ouvre un paragraphe.
        if etat.mode not in ("paragraphe", "puce", "numero"):
            etat.vider()
            etat.mode = "paragraphe"
        etat.tampon.append(ligne.strip())

    etat.vider()
    return etat.elements


def couverture(titre: str, sous_titre: str, mentions: list[list[str]]) -> list:
    """Page de garde commune aux documents générés."""
    from .document import tableau as tableau_charte

    return [
        Spacer(1, 48 * mm),
        Paragraph(titre.upper(), S["couverture_sous"]),
        Spacer(1, 6 * mm),
        Paragraph(sous_titre, S["couverture_titre"]),
        Spacer(1, 26 * mm),
        tableau_charte(mentions, [120, 310], taille=8.5),
    ]
