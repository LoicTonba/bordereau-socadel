"""Routes de référence : ce que l'écran de connexion doit connaître avant l'authentification.

Un seul point d'entrée public, l'annuaire des agences, dont le sélecteur de
connexion a besoin pour se remplir. Il n'expose que des noms de lieux : ni
volume de portefeuille, ni identité, ni compte.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from ..deps import ContainerDep, ContexteDep
from ..schemas.bordereau import (
    AgenceSortie,
    ResultatRechercheSortie,
    TerritoireSortie,
    TrouvailleSortie,
    VoletSortie,
)

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


@router.get(
    "/recherche",
    response_model=ResultatRechercheSortie,
    summary="Rechercher dans toute l'application",
)
async def recherche(
    container: ContainerDep,
    contexte: ContexteDep,
    q: Annotated[str, Query(min_length=0, max_length=120)] = "",
) -> ResultatRechercheSortie:
    """Cherche partout, dans les limites de ce que l'appelant peut voir.

    Chaque volet passe par le cas d'usage qui sert déjà l'écran correspondant :
    un agent de terrain ne trouve que ses lignes, un superviseur que son
    agence. Un volet fermé à l'appelant est absent de la réponse, jamais
    signalé comme refusé.
    """
    resultat = await container.recherche_globale().executer(contexte, q)
    return ResultatRechercheSortie(
        terme=resultat.terme,
        total=resultat.total,
        volets=[
            VoletSortie(
                cle=volet.cle,
                libelle=volet.libelle,
                resultats=[
                    TrouvailleSortie(
                        titre=t.titre, detail=t.detail, chemin=t.chemin
                    )
                    for t in volet.resultats
                ],
            )
            for volet in resultat.volets
        ],
    )
