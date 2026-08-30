"""Routes des comptes de connexion.

Réservées à l'administrateur, à deux exceptions près : chacun consulte et
modifie son propre profil, et change son propre mot de passe.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from ....application.use_cases.comptes import (
    CommandeChangementMotDePasse,
    CommandeCreationCompte,
    CommandeModificationCompte,
)
from ..deps import ContainerDep, ContexteDep, UtilisateurDep
from ..schemas.bordereau import (
    CompteSortie,
    RequeteChangementMotDePasse,
    RequeteCreationCompte,
    RequeteModificationCompte,
)

router = APIRouter(prefix="/comptes", tags=["Comptes"])


@router.get("", response_model=list[CompteSortie], summary="Lister les comptes")
async def lister(container: ContainerDep, contexte: ContexteDep) -> list[CompteSortie]:
    comptes = await container.lister_comptes().executer(contexte)
    return [CompteSortie.depuis_entite(c) for c in comptes]


@router.post(
    "",
    response_model=CompteSortie,
    status_code=status.HTTP_201_CREATED,
    summary="Ouvrir un compte",
)
async def creer(
    requete: RequeteCreationCompte,
    container: ContainerDep,
    contexte: ContexteDep,
) -> CompteSortie:
    """Crée un compte avec un mot de passe initial à changer à la première
    connexion."""
    compte = await container.creer_compte().executer(
        contexte,
        CommandeCreationCompte(
            identifiant=requete.identifiant,
            nom_complet=requete.nom_complet,
            mot_de_passe=requete.mot_de_passe,
            role=requete.role,
            agent_id=requete.agent_id,
            region=requete.region,
            agence=requete.agence,
            email=requete.email,
            photo_url=requete.photo_url,
        ),
    )
    return CompteSortie.depuis_entite(compte)


@router.patch(
    "/{compte_id}", response_model=CompteSortie, summary="Modifier un compte"
)
async def modifier(
    compte_id: UUID,
    requete: RequeteModificationCompte,
    container: ContainerDep,
    contexte: ContexteDep,
) -> CompteSortie:
    compte = await container.modifier_compte().executer(
        contexte,
        CommandeModificationCompte(
            compte_id=compte_id,
            nom_complet=requete.nom_complet,
            email=requete.email,
            photo_url=requete.photo_url,
            region=requete.region,
            agence=requete.agence,
        ),
    )
    return CompteSortie.depuis_entite(compte)


@router.patch(
    "/{compte_id}/activation",
    response_model=CompteSortie,
    summary="Activer ou désactiver un compte",
)
async def basculer_activation(
    compte_id: UUID,
    container: ContainerDep,
    contexte: ContexteDep,
    actif: Annotated[bool, Query()] = True,
) -> CompteSortie:
    compte = await container.basculer_activation_compte().executer(
        contexte, compte_id, actif=actif
    )
    return CompteSortie.depuis_entite(compte)


@router.post(
    "/mot-de-passe",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Changer son mot de passe",
)
async def changer_mot_de_passe(
    requete: RequeteChangementMotDePasse,
    container: ContainerDep,
    contexte: ContexteDep,
    utilisateur: UtilisateurDep,
) -> Response:
    """Un mot de passe ne se change que sur son propre compte, en prouvant
    qu'on connaît l'ancien."""
    await container.changer_mot_de_passe().executer(
        contexte,
        CommandeChangementMotDePasse(
            compte_id=utilisateur.id,
            ancien_mot_de_passe=requete.ancien_mot_de_passe,
            nouveau_mot_de_passe=requete.nouveau_mot_de_passe,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
