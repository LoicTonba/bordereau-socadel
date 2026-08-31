"""Route de relecture du journal d'audit.

Réservée à l'administrateur SOCADEL et au super utilisateur NEXT LTD : savoir
qui a fait quoi relève de la gouvernance, pas de l'exploitation quotidienne.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from ....application.use_cases.audit import FiltreAudit
from ..deps import ContainerDep, ContexteDep, PaginationDep
from ..schemas.commun import ReponsePaginee
from ..schemas.bordereau import TraceAuditSortie

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "",
    response_model=ReponsePaginee[TraceAuditSortie],
    summary="Relire le journal des gestes posés",
)
async def relire(
    container: ContainerDep,
    contexte: ContexteDep,
    pagination: PaginationDep,
    identifiant: Annotated[str | None, Query(max_length=160)] = None,
    action: Annotated[str | None, Query(max_length=120)] = None,
    depuis: Annotated[date | None, Query()] = None,
    jusqu_a: Annotated[date | None, Query(alias="jusquA")] = None,
    echecs_seulement: Annotated[bool, Query(alias="echecsSeulement")] = False,
) -> ReponsePaginee[TraceAuditSortie]:
    """Du plus récent au plus ancien.

    Le journal ne porte aucun corps de requête : ni mot de passe, ni numéro de
    téléphone, ni nom de client. Le geste et sa cible suffisent à répondre à
    « qui a fait quoi ».
    """
    page = await container.relire_journal().executer(
        contexte,
        FiltreAudit(
            identifiant=identifiant,
            action=action,
            depuis=depuis,
            jusqu_a=jusqu_a,
            echecs_seulement=echecs_seulement,
        ),
        pagination,
    )
    return ReponsePaginee.depuis_page(
        page, [TraceAuditSortie.depuis_entite(t) for t in page.elements]
    )
