"""Routes du maillage territorial : agences, divisions, directions régionales.

Le réseau bouge, et l'application doit suivre sans attendre un nouvel import du
référentiel. Ces routes sont réservées à l'administrateur SOCADEL et au super
utilisateur NEXT LTD : le maillage est une décision de l'exploitant, pas du
superviseur qui y travaille.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from ....application.use_cases.territoire import CommandeAgence
from ..deps import ContainerDep, ContexteDep
from ..schemas.bordereau import (
    AgenceDetail,
    RequeteAgence,
    RequeteFermetureAgence,
    TerritoireDetail,
)

router = APIRouter(prefix="/territoire", tags=["Territoire"])


@router.get("", response_model=TerritoireDetail, summary="Lire le maillage")
async def lire(
    container: ContainerDep,
    contexte: ContexteDep,
    ouvertes_seulement: Annotated[bool, Query(alias="ouvertesSeulement")] = False,
) -> TerritoireDetail:
    """Les agences, avec leurs divisions et leurs directions régionales."""
    territoire = await container.lister_territoire().executer(
        contexte, ouvertes_seulement=ouvertes_seulement
    )
    return TerritoireDetail(
        agences=[AgenceDetail.depuis_entite(a) for a in territoire.agences],
        regions=list(territoire.regions),
        divisions=list(territoire.divisions),
    )


@router.post(
    "",
    response_model=AgenceDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Ouvrir une agence",
)
async def creer(
    requete: RequeteAgence, container: ContainerDep, contexte: ContexteDep
) -> AgenceDetail:
    agence = await container.creer_agence().executer(
        contexte,
        CommandeAgence(
            nom=requete.nom, region=requete.region, division=requete.division
        ),
    )
    return AgenceDetail.depuis_entite(agence)


@router.patch(
    "/{nom}", response_model=AgenceDetail, summary="Corriger un rattachement"
)
async def modifier(
    nom: str,
    requete: RequeteAgence,
    container: ContainerDep,
    contexte: ContexteDep,
) -> AgenceDetail:
    """Le nom n'est pas modifiable : comptes et itinéraires le portent."""
    agence = await container.modifier_agence().executer(
        contexte,
        nom,
        CommandeAgence(
            nom=nom, region=requete.region, division=requete.division
        ),
    )
    return AgenceDetail.depuis_entite(agence)


@router.post(
    "/{nom}/fermeture", response_model=AgenceDetail, summary="Fermer une agence"
)
async def fermer(
    nom: str,
    requete: RequeteFermetureAgence,
    container: ContainerDep,
    contexte: ContexteDep,
) -> AgenceDetail:
    """Retire l'agence des listes de travail, sans effacer son passé.

    Le motif est exigé : une agence fermée sans raison connue ne se rouvre
    jamais de bon cœur, faute de savoir ce qui l'avait justifiée.
    """
    agence = await container.fermer_agence().executer(contexte, nom, requete.motif)
    return AgenceDetail.depuis_entite(agence)


@router.post(
    "/{nom}/reouverture", response_model=AgenceDetail, summary="Rouvrir une agence"
)
async def rouvrir(
    nom: str, container: ContainerDep, contexte: ContexteDep
) -> AgenceDetail:
    agence = await container.rouvrir_agence().executer(contexte, nom)
    return AgenceDetail.depuis_entite(agence)


@router.delete(
    "/{nom}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une agence sans rattachement",
)
async def supprimer(
    nom: str, container: ContainerDep, contexte: ContexteDep
) -> Response:
    """Réservé à la correction d'une saisie : dès qu'un compte ou une tournée
    s'y rattache, seule la fermeture reste possible."""
    await container.supprimer_agence().executer(contexte, nom)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/import-referentiel",
    summary="Amorcer le maillage depuis le référentiel clients",
)
async def importer(
    container: ContainerDep, contexte: ContexteDep
) -> dict[str, object]:
    """Reprend les agences que le référentiel connaît et que l'application
    ignore encore. Utile une fois, à la mise en route."""
    ajoutees = await container.importer_territoire().executer(contexte)
    return {
        "ajoutees": ajoutees,
        "message": (
            f"{ajoutees} agence(s) reprises du référentiel."
            if ajoutees
            else "Le maillage était déjà complet."
        ),
    }
