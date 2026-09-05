"""Exports PDF. Implémente le port `ExportateurPdf`.

Deux documents distincts :

* le **bordereau de terrain**, imprimé et confié à l'agent. Sa mise en page
  reproduit fidèlement `bordereau.xlsx / Feuil3` : titre de campagne, puis un
  bloc par itinéraire, en-tête `ITINERAIRE / Total client / OK-MRA`, colonnes
  `REF GEO / METER_NO / NOMS / CONTRAT / RAPPORT`, la dernière laissée vide
  pour la saisie manuscrite. C'est le document que les agents connaissent
  déjà ; le changer les obligerait à réapprendre leur outil de travail.

* l'**export de consultation**, reflet du tableau filtré à l'écran.

Les deux portent le filigrane SOCADEL et un titre centré.
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ....domain.entities import Client, LigneBordereau
from .filigrane import dessiner_filigrane, dessiner_logo_entete

#: Bleu du logo SOCADEL, échantillonné sur `LOGO_SOCADEL_CM.jpg`.
BLEU_SOCADEL = colors.HexColor("#1A76B9")
BLEU_SOMBRE = colors.HexColor("#1F5FA0")
BLEU_CLAIR = colors.HexColor("#E8F1FA")
GRIS_TEXTE = colors.HexColor("#334155")
GRIS_DOUX = colors.HexColor("#64748B")
GRIS_BORDURE = colors.HexColor("#CBD5E1")

#: Titre exact porté par le modèle Excel. Il est repris tel quel : c'est le
#: libellé que les équipes terrain reconnaissent.
TITRE_CAMPAGNE = "CAMPAGNE DE COLLECTE DE NUMERO WHATSAPP"

#: Colonnes du bordereau terrain, dans l'ordre de la feuille 3 du classeur
#: source. RAPPORT et N° WHATSAPP sont les deux seules que l'agent remplit.
COLONNES_TERRAIN = (
    "REF GEO",
    "METER_NO",
    "NOMS",
    "CONTRAT",
    "RAPPORT",
    "N° WHATSAPP",
)

#: Largeurs cumulées à 186 mm, la largeur utile d'une A4 portrait marges
#: déduites. Les deux colonnes de saisie sont les plus larges : c'est là que le
#: stylo passe.
LARGEURS_TERRAIN = (34 * mm, 26 * mm, 44 * mm, 24 * mm, 22 * mm, 36 * mm)

#: Lignes par page du bordereau imprimé. Au-delà, les cases deviennent trop
#: serrées pour qu'un agent y écrive un numéro au stylo.
LIGNES_PAR_PAGE = 22

#: Lignes vierges ajoutées en fin de bloc, pour les clients rencontrés qui ne
#: figurent pas encore au référentiel.
LIGNES_VIERGES = 3


@dataclass(frozen=True, slots=True)
class BlocItineraire:
    """Un itinéraire et ses clients, tels qu'ils s'impriment sur une page."""

    code: int
    libelle: str
    clients: Sequence[Client]


@dataclass(frozen=True, slots=True)
class _Valeur:
    """Enveloppe minimale : la grille lit `.valeur` sur ces deux champs."""

    valeur: str


@dataclass(frozen=True, slots=True)
class _LigneModele:
    """Un client d'exemple, réduit à ce que la grille sait afficher.

    Le modèle vierge ne peut pas porter de vraies entités `Client` : il est
    produit hors de tout contexte métier, avant même qu'une tournée existe. Ce
    substitut expose exactement les quatre attributs que la grille consulte,
    et rien de plus.
    """

    ref_geo: _Valeur
    numero_compteur: str
    nom: str
    service_no: _Valeur
    cle_tri_terrain: tuple[int, ...]


#: Tournées d'exemple du classeur source, telles qu'elles y figurent : trois
#: itinéraires de tailles différentes. C'est le mode d'emploi du document —
#: l'agent voit ce qu'on attend de lui avant d'avoir reçu sa vraie affectation,
#: et le superviseur reconnaît la feuille qu'il remplit déjà.
CODE_EXEMPLE = 125369

_NOMS_EXEMPLE = (
    "BILOA DAMARIS",
    "NGONO ALBERTINE",
    "MBALLA JEAN PIERRE",
    "TCHOUMI ALAIN",
    "ABDOUL AZIZ OUMAROU",
    "FOTSO CHRISTELLE",
)


def _tournee_exemple(effectif: int) -> tuple[_LigneModele, ...]:
    """Un itinéraire d'exemple de l'effectif demandé."""
    return tuple(
        _LigneModele(
            ref_geo=_Valeur(f"838-01-01-641-00-0{rang}"),
            numero_compteur="021750196246",
            nom=_NOMS_EXEMPLE[(rang - 1) % len(_NOMS_EXEMPLE)],
            service_no=_Valeur(str(203299980 + rang)),
            cle_tri_terrain=(838, 1, 1, 641, 0, rang),
        )
        for rang in range(1, effectif + 1)
    )


MODELE_EXEMPLE = _tournee_exemple(5)

#: Les trois itinéraires du modèle, dans l'ordre et les effectifs du classeur.
TOURNEES_EXEMPLE = (
    (CODE_EXEMPLE, 5),
    (12536, 3),
    (12365, 6),
)


class ExportateurPdfReportlab:
    """Génère les deux documents PDF du métier."""

    def generer_modele_terrain(self) -> bytes:
        """Le bordereau vierge distribué en exemple, avec sa tournée témoin."""
        return self.generer_template_multi(
            [
                BlocItineraire(
                    code,
                    "Exemple, à remplacer par votre tournée",
                    _tournee_exemple(effectif),
                )
                for code, effectif in TOURNEES_EXEMPLE
            ],
            nom_agent="",
            date_travail="",
        )

    # --- Bordereau de terrain imprimable ----------------------------------

    def generer_template_terrain(
        self,
        clients: Sequence[Client],
        *,
        code_itineraire: int,
        libelle_itineraire: str,
        nom_agent: str,
        date_travail: str,
    ) -> bytes:
        """Bordereau d'un seul itinéraire."""
        return self.generer_template_multi(
            [BlocItineraire(code_itineraire, libelle_itineraire, clients)],
            nom_agent=nom_agent,
            date_travail=date_travail,
        )

    def generer_template_multi(
        self,
        blocs: Sequence[BlocItineraire],
        *,
        nom_agent: str,
        date_travail: str,
    ) -> bytes:
        """Bordereau couvrant plusieurs itinéraires, un bloc par tournée.

        C'est la forme du classeur source : un agent compétent reçoit plusieurs
        itinéraires, et il part avec un seul document qui les enchaîne.
        """
        tampon = io.BytesIO()
        document = SimpleDocTemplate(
            tampon,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=26 * mm,
            bottomMargin=16 * mm,
            title=f"Bordereau de collecte, {nom_agent}",
            author="NEXT LTD, Numeric Export Technologies",
            subject=TITRE_CAMPAGNE,
        )

        styles = _styles()
        elements: list = []

        for index, bloc in enumerate(blocs):
            if index > 0:
                elements.append(PageBreak())
            elements.extend(
                _bloc_itineraire(bloc, nom_agent, date_travail, styles)
            )

        if not blocs:
            elements.extend(
                _bloc_itineraire(
                    BlocItineraire(0, ", ", []), nom_agent, date_travail, styles
                )
            )

        document.build(
            elements, onFirstPage=_habiller_page, onLaterPages=_habiller_page
        )
        return tampon.getvalue()

    # --- Export de consultation -------------------------------------------

    def exporter_bordereau(
        self, lignes: Sequence[LigneBordereau], *, titre: str
    ) -> bytes:
        """Reflet imprimable du tableau filtré à l'écran."""
        tampon = io.BytesIO()
        document = SimpleDocTemplate(
            tampon,
            pagesize=landscape(A4),  # neuf colonnes ne tiennent pas en portrait
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=24 * mm,
            bottomMargin=14 * mm,
            title=titre,
            author="NEXT LTD, Numeric Export Technologies",
        )

        styles = _styles()
        elements = [
            Paragraph(titre.upper(), styles["titre"]),
            Paragraph(
                "SOCADEL, Société Camerounaise d'Electricité",
                styles["sous_titre"],
            ),
            Paragraph(
                f"{len(lignes)} ligne(s) · document généré par la "
                f"plateforme de collecte NEXT LTD",
                styles["mention"],
            ),
            Spacer(1, 6 * mm),
        ]

        donnees = [
            [
                "CONTRAT", "NOM", "REF GEO", "ITIN.", "COMPTEUR",
                "NUMÉRO RELEVÉ", "STATUT", "VÉRIFICATION", "DATE",
            ]
        ]
        for ligne in lignes:
            donnees.append(
                [
                    ligne.service_no.valeur,
                    _tronquer(ligne.nom_client, 30),
                    ligne.ref_geo.valeur if ligne.ref_geo else "",
                    str(ligne.code_itineraire) if ligne.code_itineraire else "",
                    _tronquer(ligne.numero_compteur, 15),
                    ligne.numero_collecte.valeur if ligne.numero_collecte else "",
                    ligne.statut.value.replace("_", " ").title(),
                    ligne.verdict.value.replace("_", " ").title(),
                    ligne.date_collecte.strftime("%d/%m/%y"),
                ]
            )

        tableau = Table(
            donnees,
            repeatRows=1,
            colWidths=[
                24 * mm, 54 * mm, 36 * mm, 15 * mm, 28 * mm,
                30 * mm, 26 * mm, 26 * mm, 17 * mm,
            ],
        )
        tableau.setStyle(_style_consultation())
        elements.append(tableau)

        document.build(
            elements, onFirstPage=_habiller_page, onLaterPages=_habiller_page
        )
        return tampon.getvalue()


# --- Styles ----------------------------------------------------------------


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "titre": ParagraphStyle(
            "TitreSocadel",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=BLEU_SOMBRE,
            spaceAfter=2,
        ),
        "sous_titre": ParagraphStyle(
            "SousTitreSocadel",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=GRIS_TEXTE,
            spaceAfter=1,
        ),
        "mention": ParagraphStyle(
            "Mention",
            parent=base["Normal"],
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=GRIS_DOUX,
        ),
    }


# --- Bordereau de terrain --------------------------------------------------


def _bloc_itineraire(
    bloc: BlocItineraire, nom_agent: str, date_travail: str, styles
) -> list:
    """Un itinéraire complet : titre, bandeau, puis grille de saisie paginée."""
    clients = sorted(bloc.clients, key=lambda c: c.cle_tri_terrain)

    pages = [
        clients[debut : debut + LIGNES_PAR_PAGE]
        for debut in range(0, len(clients), LIGNES_PAR_PAGE)
    ] or [[]]

    elements: list = []
    for numero, page in enumerate(pages, start=1):
        if numero > 1:
            elements.append(PageBreak())

        elements.extend(
            [
                Paragraph(TITRE_CAMPAGNE, styles["titre"]),
                Paragraph(
                    "SOCADEL, Société Camerounaise d'Electricité "
                    "· opération NEXT LTD",
                    styles["sous_titre"],
                ),
                Spacer(1, 4 * mm),
                _bandeau(
                    bloc, nom_agent, date_travail, len(clients), numero, len(pages)
                ),
                Spacer(1, 2.5 * mm),
                _grille(page, derniere_page=numero == len(pages)),
                Spacer(1, 3 * mm),
                _legende_rapport(),
            ]
        )

        # La signature ne figure qu'une fois, au pied de la dernière page :
        # c'est la tournée entière qu'elle authentifie, pas chaque feuillet.
        if numero == len(pages):
            elements.extend([Spacer(1, 4 * mm), _signature()])

    return elements


def _bandeau(
    bloc: BlocItineraire,
    nom_agent: str,
    date_travail: str,
    total_clients: int,
    page: int,
    total_pages: int,
) -> Table:
    """Bandeau d'identification, calqué sur la ligne 3 du modèle Excel.

    Le modèle porte `ITINERAIRE | code | Total client | n | OK/MRA` ; on y
    ajoute l'agent, la date et la pagination, absents du classeur mais
    indispensables dès qu'un agent emporte plusieurs tournées.
    """
    tableau = Table(
        [
            # Ligne calquée sur le modèle Excel, à l'identique.
            [
                "ITINERAIRE",
                str(bloc.code),
                "Total client",
                str(total_clients),
                "RAPPORT",
                "OK / MRA",
            ],
            # Lignes ajoutées : l'agent, la date et la page, indispensables dès
            # qu'un collecteur emporte plusieurs tournées dans un même document.
            ["AGENT", nom_agent, "", "", "DATE", date_travail],
            ["ZONE", bloc.libelle, "", "", "PAGE", f"{page} / {total_pages}"],
        ],
        colWidths=LARGEURS_TERRAIN,
    )
    tableau.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                # Les valeurs des deux dernières lignes s'étalent sur trois
                # colonnes : un nom complet ne tient pas dans une seule.
                ("SPAN", (1, 1), (3, 1)),
                ("SPAN", (1, 2), (3, 2)),
                # Cases de libellé sur fond bleu pâle, valeurs sur blanc.
                ("BACKGROUND", (0, 0), (0, -1), BLEU_CLAIR),
                ("BACKGROUND", (2, 0), (2, 0), BLEU_CLAIR),
                ("BACKGROUND", (4, 0), (4, -1), BLEU_CLAIR),
                ("TEXTCOLOR", (0, 0), (0, -1), BLEU_SOMBRE),
                ("TEXTCOLOR", (2, 0), (2, 0), BLEU_SOMBRE),
                ("TEXTCOLOR", (4, 0), (4, -1), BLEU_SOMBRE),
                ("TEXTCOLOR", (1, 0), (1, 0), BLEU_SOMBRE),
                # La consigne de saisie est rappelée en clair dès le bandeau.
                ("FONTSIZE", (5, 0), (5, 0), 8),
                ("ALIGN", (5, 0), (5, 0), "CENTER"),
                ("TEXTCOLOR", (5, 0), (5, 0), GRIS_TEXTE),
                ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tableau


def _grille(clients: Sequence[Client], *, derniere_page: bool) -> Table:
    """Grille de saisie : quatre colonnes pré-imprimées, deux à remplir."""
    donnees: list[list[str]] = [list(COLONNES_TERRAIN)]
    vide = [""] * len(COLONNES_TERRAIN)

    for client in clients:
        donnees.append(
            [
                client.ref_geo.valeur if client.ref_geo else "",
                _tronquer(client.numero_compteur, 14),
                _tronquer(client.nom, 26),
                client.service_no.valeur,
                "",
                "",
            ]
        )

    # Des lignes vierges en fin de dernière page : l'agent y note les clients
    # rencontrés qui ne figurent pas encore au référentiel.
    if derniere_page:
        donnees.extend([list(vide) for _ in range(LIGNES_VIERGES)])

    tableau = Table(
        donnees,
        repeatRows=1,
        colWidths=LARGEURS_TERRAIN,
        rowHeights=[7 * mm] + [8.5 * mm] * (len(donnees) - 1),
    )

    premiere_vierge = len(donnees) - LIGNES_VIERGES if derniere_page else len(donnees)
    saisie = len(COLONNES_TERRAIN) - 2
    commandes = [
        ("BACKGROUND", (0, 0), (-1, 0), BLEU_SOCADEL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), GRIS_TEXTE),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        # Les deux colonnes à remplir sont cernées d'un trait franc : elles
        # guident le stylo sans qu'on ait à lire l'en-tête.
        ("BOX", (saisie, 1), (-1, -1), 1.1, BLEU_SOCADEL),
        ("LINEBEFORE", (saisie + 1, 1), (saisie + 1, -1), 0.7, BLEU_SOCADEL),
    ]

    if derniere_page and LIGNES_VIERGES:
        commandes.append(
            ("BACKGROUND", (0, premiere_vierge), (-1, -1), colors.HexColor("#FAFCFE"))
        )

    tableau.setStyle(TableStyle(commandes))
    return tableau


def _legende_rapport() -> Table:
    """Ce que l'agent doit écrire, expliqué sur le papier lui-même.

    Deux mots seulement, et leur conséquence. Un agent qui a oublié la consigne
    du briefing la retrouve sur son bordereau, il n'a personne à rappeler.
    """
    tableau = Table(
        [
            [
                "OK",
                "Le client est allé au bout du parcours WhatsApp : il figure "
                "désormais dans la base.",
            ],
            [
                "MRA",
                "Le numéro est pris mais l'enrôlement reste à faire : il sera "
                "relancé depuis Gestion Campagnes, sur MRA.",
            ],
            [
                "N° WHATSAPP",
                "À renseigner quand le client est absent et qu'un proche donne "
                "son numéro, ou quand le relevé diffère du contrat.",
            ],
        ],
        colWidths=(24 * mm, 162 * mm),
    )
    tableau.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("TEXTCOLOR", (0, 0), (0, -1), BLEU_SOMBRE),
                ("TEXTCOLOR", (1, 0), (1, -1), GRIS_TEXTE),
                ("BACKGROUND", (0, 0), (0, -1), BLEU_CLAIR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, GRIS_BORDURE),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tableau


def _signature() -> Table:
    """Le pied du modèle : c'est lui qui authentifie le retour de tournée."""
    tableau = Table(
        [
            ["DATE ET SIGNATURE SUPERVISEUR SOCADEL / ENTREPRISE", ""],
            ["Superviseur SOCADEL", "Agent de terrain"],
            ["", ""],
        ],
        colWidths=(93 * mm, 93 * mm),
        rowHeights=(7 * mm, 6 * mm, 18 * mm),
    )
    tableau.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 0), (1, 0), BLEU_CLAIR),
                ("TEXTCOLOR", (0, 0), (1, 0), BLEU_SOMBRE),
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTSIZE", (0, 1), (-1, 1), 7.5),
                ("TEXTCOLOR", (0, 1), (-1, 1), GRIS_DOUX),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
            ]
        )
    )
    return tableau


def _style_consultation() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), BLEU_SOCADEL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("TEXTCOLOR", (0, 1), (-1, -1), GRIS_TEXTE),
            ("GRID", (0, 0), (-1, -1), 0.4, GRIS_BORDURE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BLEU_CLAIR]),
        ]
    )


# --- Habillage des pages ---------------------------------------------------


def _habiller_page(canevas, document) -> None:
    """Filigrane, logo d'en-tête et pied de page.

    Le filigrane est posé en premier, donc sous le contenu ; le logo et le pied
    viennent par-dessus.
    """
    largeur, hauteur = document.pagesize

    dessiner_filigrane(canevas, largeur, hauteur)
    dessiner_logo_entete(
        canevas, largeur - 12 * mm - 32 * mm, hauteur - 14 * mm, 32 * mm
    )

    canevas.saveState()
    canevas.setStrokeColor(GRIS_BORDURE)
    canevas.setLineWidth(0.4)
    canevas.line(12 * mm, 11 * mm, largeur - 12 * mm, 11 * mm)

    canevas.setFont("Helvetica", 6.5)
    canevas.setFillColor(GRIS_DOUX)
    canevas.drawString(
        12 * mm,
        7.5 * mm,
        "SOCADEL, Société Camerounaise d'Electricité  |  Solution NEXT LTD "
        ", Numeric Export Technologies",
    )
    canevas.drawRightString(
        largeur - 12 * mm, 7.5 * mm, f"Page {canevas.getPageNumber()}"
    )
    canevas.restoreState()


def _tronquer(valeur: str | None, longueur: int) -> str:
    """Coupe proprement : une cellule débordante casse la grille imprimée."""
    if not valeur:
        return ""
    texte = str(valeur)
    return texte if len(texte) <= longueur else f"{texte[: longueur - 1]}…"
