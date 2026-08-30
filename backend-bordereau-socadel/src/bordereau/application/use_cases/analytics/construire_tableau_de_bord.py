"""Cas d'usage : assemblage du tableau de bord du superviseur.

Il réunit les KPI, la courbe d'évolution, le classement des agents et la
couverture des itinéraires — de quoi tenir le point quotidien avec les agents :
ce qui a été fait, ce qui progresse, quels itinéraires sont déjà couverts.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from ....domain.securite import ContexteAcces, Permission, restreindre
from ....domain.value_objects import Periode
from ...dto import FiltreBordereau, TableauDeBord
from ...ports import RequetesAnalytiques


@dataclass(frozen=True, slots=True)
class CommandeTableauDeBord:
    periode: Periode
    filtre: FiltreBordereau = FiltreBordereau()
    limite_agents: int = 10
    limite_itineraires: int = 20


class ConstruireTableauDeBord:
    """Compose les blocs du tableau de bord."""

    def __init__(self, requetes: RequetesAnalytiques) -> None:
        self._requetes = requetes

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeTableauDeBord
    ) -> TableauDeBord:
        """Récupère les cinq blocs en parallèle.

        Ils sont indépendants : les séquencer multiplierait par cinq le temps
        d'affichage de la page d'accueil.
        """
        contexte.exiger(Permission.ANALYTICS_CONSULTER)
        # Le filtre est rétréci une seule fois, en amont : les cinq blocs
        # héritent donc tous du même périmètre.
        periode = commande.periode
        filtre = restreindre(contexte, commande.filtre)

        kpis, evolution, agents, itineraires, statuts = await asyncio.gather(
            self._requetes.indicateurs(periode, filtre),
            self._requetes.evolution(periode, filtre),
            self._requetes.classement_agents(
                periode, filtre, limite=commande.limite_agents
            ),
            self._requetes.couverture_itineraires(
                periode, filtre, limite=commande.limite_itineraires
            ),
            self._requetes.repartition_statuts(periode, filtre),
        )

        return TableauDeBord(
            kpis=tuple(kpis),
            evolution=tuple(evolution),
            classement_agents=tuple(agents),
            couverture_itineraires=tuple(itineraires),
            repartition_statuts=dict(statuts),
        )
