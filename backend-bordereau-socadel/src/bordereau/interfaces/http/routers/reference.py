"""Routes de référence : ce que l'écran de connexion doit connaître avant l'authentification.

Un seul point d'entrée public, l'annuaire des agences, dont le sélecteur de
connexion a besoin pour se remplir. Il n'expose que des noms de lieux : ni
volume de portefeuille, ni identité, ni compte.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..deps import ContainerDep
from ..schemas.bordereau import AgenceSortie, TerritoireSortie

router = APIRouter(prefix="/reference", tags=["Référence"])


@router.get(
    "/agences",
    response_model=TerritoireSortie,
    summary="Annuaire des agences",
)
async def agences(container: ContainerDep) -> TerritoireSortie:
    """Alimente le sélecteur d'agence de l'écran de connexion.

    Volontairement public : le sélecteur s'affiche avant toute session. Le
    maillage d'agences de SOCADEL est une information commerciale, il ne
    constitue pas un secret d'exploitation.
    """
    liste = await container.lister_agences().executer()
    return TerritoireSortie(
        agences=[
            AgenceSortie(nom=a.nom, region=a.region, division=a.division)
            for a in liste
        ]
    )
