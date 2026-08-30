"""Routes du tableau de bord."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query

from ....application.use_cases.analytics import CommandeTableauDeBord
from ....domain.value_objects import Periode
from ..deps import ContainerDep, ContexteDep, FiltreDep, PeriodeDep
from ..schemas.analytics import ReponseTableauDeBord

router = APIRouter(prefix="/analytics", tags=["Tableau de bord"])

#: Fenêtre par défaut : deux semaines, assez pour voir une tendance sans noyer
#: la courbe.
JOURS_PAR_DEFAUT = 14


@router.get(
    "/tableau-de-bord",
    response_model=ReponseTableauDeBord,
    summary="KPI, évolution, classement et couverture",
)
async def tableau_de_bord(
    container: ContainerDep,
    contexte: ContexteDep,
    filtre: FiltreDep,
    debut: Annotated[date | None, Query()] = None,
    fin: Annotated[date | None, Query()] = None,
) -> ReponseTableauDeBord:
    """Assemble l'écran d'accueil du superviseur.

    La période porte sur les indicateurs ; les autres critères du filtre
    (agent, itinéraire, statut) restreignent le périmètre observé.
    """
    borne_haute = fin or date.today()
    periode = (
        Periode(debut, borne_haute)
        if debut
        else Periode(borne_haute - timedelta(days=JOURS_PAR_DEFAUT - 1), borne_haute)
    )

    tableau = await container.construire_tableau_de_bord().executer(
        contexte, CommandeTableauDeBord(periode=periode, filtre=filtre)
    )
    return ReponseTableauDeBord.depuis_dto(tableau)
