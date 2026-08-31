"""Cas d'usage : le bordereau de terrain vierge, en classeur ou en PDF.

Deux formats pour deux usages. Le PDF s'imprime et part en tournée, c'est le
document que l'agent annote au stylo. Le classeur sert au superviseur qui
prépare hors application, ajoute des clients à la main, ou veut voir la
maquette avant de la distribuer.

Un seul contenu, donc, et deux enveloppes : la maquette est celle de la
feuille 3 du classeur source dans les deux cas, et une évolution de l'une
oblige à toucher l'autre, ce que le format de sortie rend visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ...ports import ExportateurPdf, GenerateurModeleTerrain


class FormatModele(str, Enum):
    XLSX = "xlsx"
    PDF = "pdf"


TYPES_MIME = {
    FormatModele.XLSX: (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    FormatModele.PDF: "application/pdf",
}


@dataclass(frozen=True, slots=True)
class ModeleTerrain:
    contenu: bytes
    nom_fichier: str
    type_mime: str


class TelechargerModeleTerrain:
    """Sert le modèle de bordereau que les agents emportent."""

    def __init__(
        self, classeur: GenerateurModeleTerrain, pdf: ExportateurPdf
    ) -> None:
        self._classeur = classeur
        self._pdf = pdf

    def executer(self, format: FormatModele) -> ModeleTerrain:
        if format is FormatModele.XLSX:
            contenu = self._classeur.generer()
        else:
            # Le PDF passe par l'exportateur du métier : l'agent reçoit la
            # maquette réelle, pas une seconde implémentation de la même.
            contenu = self._pdf.generer_modele_terrain()

        return ModeleTerrain(
            contenu=contenu,
            nom_fichier=f"modele-bordereau-terrain-socadel.{format.value}",
            type_mime=TYPES_MIME[format],
        )
