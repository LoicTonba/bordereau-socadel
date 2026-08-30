"""Port de lecture analytique (modèle de lecture séparé).

Les KPI ne se calculent pas en chargeant des entités : agréger 400 000 lignes
en mémoire serait absurde. Ce port expose donc des *requêtes* qui renvoient
directement des DTO, et que l'infrastructure traduit en agrégations SQL.
C'est une séparation lecture/écriture assumée : les repositories servent les
cas d'usage transactionnels, celui-ci sert l'affichage.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ...domain.value_objects import Periode
from ..dto.analytics import (
    CarteKpi,
    CouvertureItineraire,
    LigneClassementAgent,
    PointSerie,
)
from ..dto.filtres import FiltreBordereau


@runtime_checkable
class RequetesAnalytiques(Protocol):
    async def indicateurs(
        self, periode: Periode, filtre: FiltreBordereau
    ) -> Sequence[CarteKpi]:
        """Cartes du bandeau supérieur, avec comparaison à la période
        précédente de même longueur."""
        ...

    async def evolution(
        self, periode: Periode, filtre: FiltreBordereau
    ) -> Sequence[PointSerie]:
        """Série journalière alimentant la courbe d'évolution."""
        ...

    async def classement_agents(
        self, periode: Periode, filtre: FiltreBordereau, limite: int = 10
    ) -> Sequence[LigneClassementAgent]:
        """Palmarès des agents, base des entretiens de suivi individuel."""
        ...

    async def couverture_itineraires(
        self, periode: Periode, filtre: FiltreBordereau, limite: int = 20
    ) -> Sequence[CouvertureItineraire]:
        """Avancement par itinéraire : ce qui est couvert, ce qui reste."""
        ...

    async def repartition_statuts(
        self, periode: Periode, filtre: FiltreBordereau
    ) -> dict[str, int]:
        """Décompte par statut, pour le graphique de répartition."""
        ...
