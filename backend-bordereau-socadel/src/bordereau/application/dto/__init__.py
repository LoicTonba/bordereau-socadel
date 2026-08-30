"""Objets de transfert entre la couche application et ses appelants.

Ce sont des dataclasses simples, sans dépendance à Pydantic ni à FastAPI :
la couche `interfaces` les traduit en schémas HTTP.
"""

from .analytics import (
    CarteKpi,
    CouvertureItineraire,
    LigneClassementAgent,
    PointSerie,
    TableauDeBord,
)
from .filtres import FiltreBordereau, FiltreItineraire
from .imports import AnomalieImport, ApercuImport, LigneApercu, ResultatImport
from .pagination import Page, PaginationParams

__all__ = [
    "AnomalieImport",
    "ApercuImport",
    "CarteKpi",
    "CouvertureItineraire",
    "FiltreBordereau",
    "FiltreItineraire",
    "LigneApercu",
    "LigneClassementAgent",
    "Page",
    "PaginationParams",
    "PointSerie",
    "ResultatImport",
    "TableauDeBord",
]
