"""Routes d'import (aperçu puis validation) et d'export (CSV, PDF, modèle)."""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Response, UploadFile, status

from ....application.use_cases.exports import CommandeExport, FormatExport
from ....application.use_cases.imports import (
    CommandeApercu,
    CommandeValidationImport,
)
from ..deps import ContainerDep, ContexteDep, FiltreDep, UtilisateurDep
from ..schemas.bordereau import (
    AnomalieSortie,
    ReponseApercuImport,
    ReponseResultatImport,
)

router = APIRouter(tags=["Import / Export"])


@router.post(
    "/imports/apercu",
    response_model=ReponseApercuImport,
    status_code=status.HTTP_200_OK,
    summary="Prévisualiser un fichier avant import",
)
async def previsualiser(
    container: ContainerDep,
    contexte: ContexteDep,
    utilisateur: UtilisateurDep,
    fichier: Annotated[UploadFile, File()],
) -> ReponseApercuImport:
    """Analyse le fichier **sans rien écrire**.

    C'est le contenu du modal de prévisualisation : le superviseur voit ce qui
    passerait, ce qui serait rejeté et pourquoi, avant de confirmer.
    """
    apercu = container.previsualiser_import().executer(
        CommandeApercu(
            nom_fichier=fichier.filename or "import.xlsx",
            contenu=await fichier.read(),
        )
    )
    return ReponseApercuImport.depuis_dto(apercu)


@router.post(
    "/imports",
    response_model=ReponseResultatImport,
    status_code=status.HTTP_201_CREATED,
    summary="Valider et appliquer un import",
)
async def valider(
    container: ContainerDep,
    contexte: ContexteDep,
    utilisateur: UtilisateurDep,
    fichier: Annotated[UploadFile, File()],
    date_collecte: Annotated[date, Form()],
    agent_id: Annotated[str | None, Form()] = None,
    affectation_id: Annotated[str | None, Form()] = None,
) -> ReponseResultatImport:
    """Écrit l'import confirmé, en une seule transaction."""
    resultat = await container.valider_import().executer(
        contexte,
        CommandeValidationImport(
            nom_fichier=fichier.filename or "import.xlsx",
            contenu=await fichier.read(),
            superviseur_id=utilisateur.id,
            date_collecte=date_collecte,
            agent_id=UUID(agent_id) if agent_id else None,
            affectation_id=UUID(affectation_id) if affectation_id else None,
        )
    )
    return ReponseResultatImport(
        reference=resultat.reference,
        lignes_creees=resultat.lignes_creees,
        lignes_mises_a_jour=resultat.lignes_mises_a_jour,
        lignes_ignorees=resultat.lignes_ignorees,
        total_traite=resultat.total_traite,
        anomalies=[AnomalieSortie.depuis_dto(a) for a in resultat.anomalies],
    )


@router.get(
    "/imports/modele",
    response_class=Response,
    summary="Télécharger le modèle de bordereau terrain",
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}}},
)
async def modele(
    container: ContainerDep, contexte: ContexteDep
) -> Response:
    """Classeur vierge distribué aux agents, aux colonnes attendues à l'import."""
    fichier = container.telecharger_modele().executer()
    return Response(
        content=fichier.contenu,
        media_type=fichier.type_mime,
        headers={
            "Content-Disposition": f'attachment; filename="{fichier.nom_fichier}"'
        },
    )


@router.get(
    "/exports/{format}",
    response_class=Response,
    summary="Exporter le tableau courant",
    responses={200: {"content": {"text/csv": {}, "application/pdf": {}}}},
)
async def exporter(
    format: FormatExport,
    container: ContainerDep,
    contexte: ContexteDep,
    filtre: FiltreDep,
) -> Response:
    """Exporte exactement le périmètre affiché à l'écran.

    L'en-tête `X-Export-Tronque` avertit le frontend qu'un plafond a été
    atteint et que le filtre mérite d'être affiné.
    """
    fichier = await container.exporter_bordereau().executer(
        contexte, CommandeExport(filtre=filtre, format=format)
    )
    return Response(
        content=fichier.contenu,
        media_type=fichier.type_mime,
        headers={
            "Content-Disposition": f'attachment; filename="{fichier.nom_fichier}"',
            "X-Export-Lignes": str(fichier.lignes_exportees),
            "X-Export-Tronque": str(fichier.tronque).lower(),
        },
    )
