"""Routes du répertoire des agents de terrain.

Le superviseur y exerce le cycle complet — créer, lire, modifier, retirer du
service. L'agent connecté, lui, n'y accède que pour sa propre fiche et son
propre portefeuille : la garde ABAC des cas d'usage s'en assure.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile, status

from ....application.use_cases.agents import (
    CommandeCreationAgent,
    CommandeModificationAgent,
)
from ....infrastructure.files.stockage_media import MediaInvalide
from ....application.errors import ImportInvalide
from ..deps import ContainerDep, ContexteDep, PeriodeDep
from ..schemas.bordereau import (
    AgentSortie,
    PortefeuilleSortie,
    RequeteCreationAgent,
    RequeteModificationAgent,
    ReponsePhoto,
)

router = APIRouter(prefix="/agents", tags=["Agents de terrain"])


@router.get("", response_model=list[AgentSortie], summary="Lister les agents")
async def lister(
    container: ContainerDep,
    contexte: ContexteDep,
    actifs_seulement: Annotated[bool, Query(alias="actifsSeulement")] = False,
) -> list[AgentSortie]:
    """Répertoire, restreint au périmètre de l'appelant."""
    agents = await container.lister_agents().executer(
        contexte, actifs_seulement=actifs_seulement
    )
    return [AgentSortie.depuis_entite(a) for a in agents]


@router.post(
    "",
    response_model=AgentSortie,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un agent",
)
async def creer(
    requete: RequeteCreationAgent,
    container: ContainerDep,
    contexte: ContexteDep,
) -> AgentSortie:
    agent = await container.enregistrer_agent().executer(
        contexte,
        CommandeCreationAgent(
            matricule=requete.matricule,
            nom_complet=requete.nom_complet,
            telephone=requete.telephone,
            zone_rattachement=requete.zone_rattachement,
            region=requete.region,
            photo_url=requete.photo_url,
        ),
    )
    return AgentSortie.depuis_entite(agent)


@router.get(
    "/{agent_id}", response_model=AgentSortie, summary="Consulter une fiche agent"
)
async def consulter(
    agent_id: UUID, container: ContainerDep, contexte: ContexteDep
) -> AgentSortie:
    agent = await container.consulter_agent().executer(contexte, agent_id)
    return AgentSortie.depuis_entite(agent)


@router.patch(
    "/{agent_id}", response_model=AgentSortie, summary="Modifier une fiche agent"
)
async def modifier(
    agent_id: UUID,
    requete: RequeteModificationAgent,
    container: ContainerDep,
    contexte: ContexteDep,
) -> AgentSortie:
    """Le matricule n'est pas modifiable : tous les bordereaux passés le
    référencent."""
    agent = await container.modifier_agent().executer(
        contexte,
        CommandeModificationAgent(
            agent_id=agent_id,
            nom_complet=requete.nom_complet,
            telephone=requete.telephone,
            zone_rattachement=requete.zone_rattachement,
            region=requete.region,
            photo_url=requete.photo_url,
        ),
    )
    return AgentSortie.depuis_entite(agent)


@router.patch(
    "/{agent_id}/activation",
    response_model=AgentSortie,
    summary="Remettre en service ou retirer du service",
)
async def basculer_activation(
    agent_id: UUID,
    container: ContainerDep,
    contexte: ContexteDep,
    actif: Annotated[bool, Query()] = True,
) -> AgentSortie:
    """Un agent n'est jamais effacé : ses bordereaux passés fondent sa
    rémunération. « Supprimer » signifie ici « retirer du service »."""
    agent = await container.basculer_activation_agent().executer(
        contexte, agent_id, actif=actif
    )
    return AgentSortie.depuis_entite(agent)


@router.get(
    "/{agent_id}/portefeuille",
    response_model=PortefeuilleSortie,
    summary="Itinéraires confiés et performance",
)
async def portefeuille(
    agent_id: UUID,
    container: ContainerDep,
    contexte: ContexteDep,
    periode: PeriodeDep,
) -> PortefeuilleSortie:
    """Ce que l'agent porte et ce qu'il en a fait.

    Le superviseur l'ouvre avant d'affecter une tournée de plus ; l'agent
    l'ouvre pour lui-même — c'est son seul écran.
    """
    resultat = await container.consulter_portefeuille().executer(
        contexte, agent_id, periode
    )
    return PortefeuilleSortie.depuis_dto(resultat)


@router.post(
    "/photo",
    response_model=ReponsePhoto,
    summary="Déposer une photo de profil",
)
async def deposer_photo(
    container: ContainerDep,
    contexte: ContexteDep,
    fichier: Annotated[UploadFile, File()],
) -> ReponsePhoto:
    """Stocke la photo et renvoie son URL.

    L'URL est ensuite portée par la création ou la modification de la fiche :
    le dépôt et l'enregistrement restent deux gestes distincts, ce qui permet
    de prévisualiser avant de valider le formulaire.
    """
    try:
        url = container.stockage_media.enregistrer_photo(
            await fichier.read(),
            fichier.content_type or "application/octet-stream",
            prefixe=fichier.filename or "photo",
        )
    except MediaInvalide as erreur:
        raise ImportInvalide(str(erreur)) from erreur

    return ReponsePhoto(url=url)
