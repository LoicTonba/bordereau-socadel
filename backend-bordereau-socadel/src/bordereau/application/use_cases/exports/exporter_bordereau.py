"""Cas d'usage : export du tableau courant en CSV ou en PDF.

L'export s'appuie sur le **même filtre** que le listing à l'écran : le
superviseur exporte exactement ce qu'il voit, ni plus ni moins.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ....domain.securite import ContexteAcces, Permission, restreindre
from ...dto import FiltreBordereau
from ...ports import ExportateurCsv, ExportateurPdf, Horloge, UnitOfWork

#: Plafond de sécurité : au-delà, l'export est tronqué et l'appelant averti.
LIGNES_MAX_EXPORT = 50_000


class FormatExport(str, Enum):
    CSV = "csv"
    PDF = "pdf"


@dataclass(frozen=True, slots=True)
class CommandeExport:
    filtre: FiltreBordereau
    format: FormatExport
    titre: str = "Bordereau de collecte WhatsApp"


@dataclass(frozen=True, slots=True)
class FichierExporte:
    contenu: bytes
    nom_fichier: str
    type_mime: str
    lignes_exportees: int
    tronque: bool
    """Vrai si le plafond a été atteint : l'interface doit alors inviter le
    superviseur à affiner ses filtres."""


class ExporterBordereau:
    """Produit le fichier d'export correspondant au filtre courant."""

    def __init__(
        self,
        uow: UnitOfWork,
        csv: ExportateurCsv,
        pdf: ExportateurPdf,
        horloge: Horloge,
    ) -> None:
        self._uow = uow
        self._csv = csv
        self._pdf = pdf
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeExport
    ) -> FichierExporte:
        contexte.exiger(Permission.BORDEREAU_EXPORTER)
        perimetre = restreindre(contexte, commande.filtre)

        async with self._uow as uow:
            lignes = await uow.lignes.lister_pour_export(
                perimetre, LIGNES_MAX_EXPORT
            )

        horodatage = self._horloge.maintenant().strftime("%Y%m%d-%H%M")

        if commande.format is FormatExport.CSV:
            contenu = self._csv.exporter_bordereau(lignes)
            nom = f"bordereau-socadel-{horodatage}.csv"
            mime = "text/csv; charset=utf-8"
        else:
            contenu = self._pdf.exporter_bordereau(lignes, titre=commande.titre)
            nom = f"bordereau-socadel-{horodatage}.pdf"
            mime = "application/pdf"

        return FichierExporte(
            contenu=contenu,
            nom_fichier=nom,
            type_mime=mime,
            lignes_exportees=len(lignes),
            tronque=len(lignes) >= LIGNES_MAX_EXPORT,
        )
