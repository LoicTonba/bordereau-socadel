"""Cas d'usage : recherche d'itinéraires.

Deux publics pour un même écran. Le superviseur y cherche les tournées de son
agence pour les confier ; l'agent de terrain y consulte celles qu'on lui a
confiées, et rien d'autre.

Le rétrécissement est posé sur le filtre avant que la requête parte, comme
pour le bordereau : un agent ne peut donc pas élargir sa vue par l'URL.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from ....domain.entities import Itineraire
from ....domain.securite import ContexteAcces
from ....domain.securite.permissions import AccesRefuse
from ....domain.value_objects import Periode
from ...dto import FiltreItineraire, Page, PaginationParams
from ...ports import UnitOfWork

#: Profondeur d'historique sur laquelle un agent retrouve ses tournées. Au-delà
#: la liste n'aide plus : ce sont des affectations closes depuis longtemps.
JOURS_HISTORIQUE = 60


class RechercherItineraires:
    """Alimente l'autocomplétion du formulaire d'affectation.

    Le superviseur connaît ses itinéraires par leur code ; la recherche accepte
    aussi le libellé et l'agence pour les cas où il ne l'a pas en tête.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self,
        filtre: FiltreItineraire,
        pagination: PaginationParams,
        contexte: ContexteAcces | None = None,
    ) -> Page[Itineraire]:
        async with self._uow as uow:
            if contexte is not None and contexte.est_agent:
                filtre = replace(filtre, codes=await self._siennes(uow, contexte))
                if not filtre.codes:
                    # Aucune tournée confiée : la page est vide, pas ouverte.
                    return Page.vide(pagination)

            return await uow.itineraires.rechercher(
                terme=filtre.terme,
                region=filtre.region,
                agence=filtre.agence,
                codes=filtre.codes,
                pagination=pagination,
            )

    async def _siennes(self, uow, contexte: ContexteAcces) -> tuple:
        """Les codes des tournées confiées à cet agent, sur la période utile."""
        if contexte.agent_id is None:
            raise AccesRefuse(
                "Ce compte agent n'est rattaché à aucun agent de terrain"
            )

        fin = date.today()
        affectations = await uow.affectations.lister_par_agent(
            contexte.agent_id, Periode(fin - timedelta(days=JOURS_HISTORIQUE), fin)
        )
        # Un même itinéraire peut avoir été confié plusieurs jours de suite.
        return tuple({a.itineraire_code for a in affectations})
