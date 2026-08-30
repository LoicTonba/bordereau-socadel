"""Routes du bordereau : consultation, déclaration, vérification."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from ....application.use_cases.collectes import (
    CommandeDeclaration,
    CommandeDeclarationEnLot,
)
from ..deps import (
    ContainerDep,
    ContexteDep,
    FiltreDep,
    PaginationDep,
    UtilisateurDep,
)
from ..schemas.bordereau import (
    LigneBordereauSortie,
    ReponseDeclarationEnLot,
    ReponseVerification,
    RequeteDeclaration,
    RequeteDeclarationEnLot,
)
from ..schemas.commun import ReponsePaginee

router = APIRouter(prefix="/bordereau", tags=["Bordereau"])


@router.get(
    "",
    response_model=ReponsePaginee[LigneBordereauSortie],
    summary="Lister les lignes de bordereau",
)
async def lister(
    container: ContainerDep,
    contexte: ContexteDep,
    filtre: FiltreDep,
    pagination: PaginationDep,
) -> ReponsePaginee[LigneBordereauSortie]:
    """Tableau principal, filtré, paginé et restreint au périmètre.

    Un agent connecté n'y voit que sa propre production : le
    rétrécissement est appliqué par le cas d'usage, pas ici.
    """
    page = await container.lister_bordereau().executer(
        contexte, filtre, pagination
    )
    return ReponsePaginee.depuis_page(
        page, [LigneBordereauSortie.depuis_entite(l) for l in page.elements]
    )


@router.patch(
    "/{ligne_id}",
    response_model=LigneBordereauSortie,
    summary="Déclarer le résultat du passage de l'agent",
)
async def declarer(
    ligne_id: UUID,
    requete: RequeteDeclaration,
    container: ContainerDep,
    contexte: ContexteDep,
) -> LigneBordereauSortie:
    """Enregistre le statut d'une ligne, d'après le bordereau papier."""
    ligne = await container.declarer_collecte().executer(
        contexte,
        CommandeDeclaration(
            ligne_id=ligne_id,
            statut=requete.statut,
            superviseur_id=contexte.utilisateur_id,
            numero_collecte=requete.numero_collecte,
            responsable=requete.responsable,
            observation=requete.observation,
        )
    )
    return LigneBordereauSortie.depuis_entite(ligne)


@router.post(
    "/declarations-en-lot",
    response_model=ReponseDeclarationEnLot,
    summary="Appliquer un statut à une sélection de lignes",
)
async def declarer_en_lot(
    requete: RequeteDeclarationEnLot,
    container: ContainerDep,
    contexte: ContexteDep,
) -> ReponseDeclarationEnLot:
    """Traite une sélection du tableau en une seule opération.

    Les lignes que le domaine refuse sont ignorées ; l'écart entre
    `lignesDemandees` et `lignesModifiees` signale au superviseur qu'il en
    reste à traiter individuellement.
    """
    modifiees = await container.declarer_collecte().executer_en_lot(
        contexte,
        CommandeDeclarationEnLot(
            lignes_ids=tuple(requete.lignes_ids),
            statut=requete.statut,
            superviseur_id=contexte.utilisateur_id,
            responsable=requete.responsable,
        )
    )
    return ReponseDeclarationEnLot(
        lignes_modifiees=modifiees, lignes_demandees=len(requete.lignes_ids)
    )


@router.post(
    "/verification",
    response_model=ReponseVerification,
    status_code=status.HTTP_200_OK,
    summary="Confronter les déclarations à la source de vérité",
)
async def verifier(
    container: ContainerDep,
    contexte: ContexteDep,
    filtre: FiltreDep,
) -> ReponseVerification:
    """Recoupe le périmètre filtré avec le référentiel SOCADEL.

    C'est le contrôle qui départage la déclaration du superviseur et l'état
    réel de l'abonnement WhatsApp du client.
    """
    rapport = await container.verifier_declarations().executer(
        contexte, filtre
    )
    return ReponseVerification(
        lignes_examinees=rapport.lignes_examinees,
        confirmees=rapport.confirmees,
        infirmees=rapport.infirmees,
        introuvables=rapport.introuvables,
        taux_confirmation=rapport.taux_confirmation,
    )
