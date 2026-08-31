"""Routes des itinéraires : recherche, affectation, bordereau imprimable."""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from ....application.dto import FiltreItineraire
from ....application.use_cases.itineraires import (
    CommandeAffectation,
    CommandeCreationItineraire,
    CommandeModificationItineraire,
    CommandeTemplateJournee,
    CommandeTemplateTerrain,
)
from ..deps import ContainerDep, ContexteDep, PaginationDep, UtilisateurDep
from ..schemas.bordereau import (
    ItineraireAffecteSortie,
    RequeteItineraire,
    ItineraireSortie,
    ReponseAffectation,
    RequeteAffectation,
)
from ..schemas.commun import ReponsePaginee

router = APIRouter(prefix="/itineraires", tags=["Itinéraires"])


@router.post(
    "",
    response_model=ItineraireSortie,
    status_code=status.HTTP_201_CREATED,
    summary="Ouvrir une tournée",
)
async def creer(
    requete: RequeteItineraire, container: ContainerDep, contexte: ContexteDep
) -> ItineraireSortie:
    """Le terrain ouvre des zones plus vite qu'un import ne se rejoue.

    Sans agence indiquée, la tournée est rattachée à celle du superviseur : lui
    laisser en ouvrir ailleurs contournerait son périmètre.
    """
    itineraire = await container.creer_itineraire().executer(
        contexte,
        CommandeCreationItineraire(
            code=requete.code,
            libelle=requete.libelle,
            region=requete.region,
            division=requete.division,
            agence=requete.agence,
            mrc=requete.mrc,
        ),
    )
    return ItineraireSortie.depuis_entite(itineraire)


@router.patch(
    "/{code}",
    response_model=ItineraireSortie,
    summary="Corriger une tournée",
)
async def modifier(
    code: int,
    requete: RequeteItineraire,
    container: ContainerDep,
    contexte: ContexteDep,
) -> ItineraireSortie:
    """Le libellé et le rattachement territorial se corrigent ; le code, non."""
    itineraire = await container.modifier_itineraire().executer(
        contexte,
        CommandeModificationItineraire(
            code=code,
            libelle=requete.libelle,
            region=requete.region,
            division=requete.division,
            agence=requete.agence,
            mrc=requete.mrc,
        ),
    )
    return ItineraireSortie.depuis_entite(itineraire)


@router.delete(
    "/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirer une tournée jamais confiée",
)
async def supprimer(
    code: int, container: ContainerDep, contexte: ContexteDep
) -> Response:
    """Une tournée déjà confiée n'est pas supprimable : la production y renvoie."""
    await container.supprimer_itineraire().executer(contexte, code)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    response_model=ReponsePaginee[ItineraireSortie],
    summary="Rechercher des itinéraires",
)
async def rechercher(
    container: ContainerDep,
    contexte: ContexteDep,
    pagination: PaginationDep,
    terme: Annotated[str | None, Query(max_length=80)] = None,
    region: Annotated[str | None, Query()] = None,
    agence: Annotated[str | None, Query()] = None,
) -> ReponsePaginee[ItineraireSortie]:
    """Alimente l'autocomplétion du formulaire d'affectation."""
    page = await container.rechercher_itineraires().executer(
        FiltreItineraire(terme=terme, region=region, agence=agence),
        pagination,
        contexte,
    )
    return ReponsePaginee.depuis_page(
        page, [ItineraireSortie.depuis_entite(i) for i in page.elements]
    )


@router.post(
    "/affectations",
    response_model=ReponseAffectation,
    status_code=status.HTTP_201_CREATED,
    summary="Affecter des itinéraires à un agent",
)
async def affecter(
    requete: RequeteAffectation,
    container: ContainerDep,
    contexte: ContexteDep,
) -> ReponseAffectation:
    """Enregistre le briefing du matin.

    L'appel crée l'affectation **et** matérialise le bordereau : une ligne par
    client de chaque itinéraire, prête à recevoir la déclaration du soir.
    """
    resultat = await container.affecter_itineraires().executer(
        contexte,
        CommandeAffectation(
            agent_id=requete.agent_id,
            codes_itineraires=tuple(requete.codes_itineraires),
            date_travail=requete.date_travail,
            superviseur_id=contexte.utilisateur_id,
            consignes=requete.consignes,
        )
    )
    return ReponseAffectation(
        agent_id=resultat.agent_id,
        matricule=resultat.matricule,
        nom_agent=resultat.nom_agent,
        date_travail=resultat.date_travail,
        itineraires=[
            ItineraireAffecteSortie(
                affectation_id=i.affectation_id,
                code_itineraire=i.code_itineraire,
                libelle=i.libelle,
                lignes_generees=i.lignes_generees,
            )
            for i in resultat.itineraires
        ],
        total_lignes=resultat.total_lignes,
    )


@router.get(
    "/{code}/bordereau-terrain.pdf",
    response_class=Response,
    summary="Télécharger le bordereau papier de l'itinéraire",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def bordereau_terrain(
    code: int,
    container: ContainerDep,
    contexte: ContexteDep,
    agent_id: Annotated[str | None, Query(alias="agentId")] = None,
) -> Response:
    """Produit le PDF que l'agent imprime et emporte sur le terrain."""
    from uuid import UUID

    document = await container.generer_template_terrain().executer(
        contexte,
        CommandeTemplateTerrain(
            code_itineraire=code,
            agent_id=UUID(agent_id) if agent_id else None,
        )
    )
    return Response(
        content=document.contenu,
        media_type=document.type_mime,
        headers={
            "Content-Disposition": f'attachment; filename="{document.nom_fichier}"'
        },
    )


@router.get(
    "/journee/{agent_id}/bordereau-terrain.pdf",
    response_class=Response,
    summary="Bordereau papier de toute la journée d'un agent",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def bordereau_journee(
    agent_id: UUID,
    container: ContainerDep,
    contexte: ContexteDep,
    date_travail: Annotated[date, Query(alias="dateTravail")],
) -> Response:
    """Un seul document pour toutes les tournées confiées ce jour-là.

    C'est la forme du classeur source : un bloc par itinéraire, enchaînés.
    L'agent part avec une seule liasse.
    """
    document = await container.generer_template_terrain().executer_journee(
        contexte, CommandeTemplateJournee(agent_id=agent_id, date_travail=date_travail)
    )
    return Response(
        content=document.contenu,
        media_type=document.type_mime,
        headers={
            "Content-Disposition": f'attachment; filename="{document.nom_fichier}"'
        },
    )
