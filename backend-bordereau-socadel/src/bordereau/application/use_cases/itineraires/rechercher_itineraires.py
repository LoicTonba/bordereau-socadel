"""Cas d'usage : recherche d'itinéraires pour l'écran d'affectation."""

from __future__ import annotations

from ....domain.entities import Itineraire
from ...dto import FiltreItineraire, Page, PaginationParams
from ...ports import UnitOfWork


class RechercherItineraires:
    """Alimente l'autocomplétion du formulaire d'affectation.

    Le superviseur connaît ses itinéraires par leur code ; la recherche accepte
    aussi le libellé et l'agence pour les cas où il ne l'a pas en tête.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, filtre: FiltreItineraire, pagination: PaginationParams
    ) -> Page[Itineraire]:
        async with self._uow as uow:
            return await uow.itineraires.rechercher(
                terme=filtre.terme,
                region=filtre.region,
                agence=filtre.agence,
                pagination=pagination,
            )
