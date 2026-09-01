"""Cas d'usage : consigner et relire les gestes posés sur la plateforme.

L'écriture n'est pas un cas d'usage comme les autres : elle ne doit **jamais**
faire échouer le geste qu'elle observe. Une base d'audit indisponible ne peut
pas empêcher un superviseur d'affecter sa tournée. Le journal avale donc ses
erreurs, comme la messagerie, et les trace pour l'exploitant.

La lecture, elle, est gouvernée : seuls l'administrateur SOCADEL et le super
utilisateur NEXT LTD y ont accès. Le superviseur n'a pas à savoir qui a
consulté quoi, et l'agent encore moins.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from ...domain.entities import TraceAudit
from ...domain.securite import ContexteAcces, Permission
from ..dto import Page, PaginationParams
from ..ports import UnitOfWork

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FiltreAudit:
    """Critères de relecture du journal."""

    identifiant: str | None = None
    action: str | None = None
    depuis: date | None = None
    jusqu_a: date | None = None
    #: Ne garder que les gestes qui ont échoué, pour repérer les tentatives.
    echecs_seulement: bool = False


class ConsignerTrace:
    """Écrit une trace. N'échoue jamais du point de vue de l'appelant."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, trace: TraceAudit) -> None:
        try:
            async with self._uow as uow:
                await uow.audit.enregistrer(trace)
                await uow.valider()
        except Exception:
            # Voir l'en-tête du module : le journal observe, il ne gouverne
            # pas. Un incident ici est un incident d'exploitation, pas un
            # refus opposé à l'utilisateur.
            logger.exception(
                "Trace d'audit non consignée : %s par %s", trace.action, trace.auteur
            )


class RelireJournal:
    """Le journal, du plus récent au plus ancien."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self,
        contexte: ContexteAcces,
        filtre: FiltreAudit,
        pagination: PaginationParams,
    ) -> Page[TraceAudit]:
        contexte.exiger(Permission.AUDIT_LIRE)

        async with self._uow as uow:
            return await uow.audit.rechercher(
                identifiant=filtre.identifiant,
                action=filtre.action,
                depuis=_debut(filtre.depuis),
                jusqu_a=_fin(filtre.jusqu_a),
                echecs_seulement=filtre.echecs_seulement,
                pagination=pagination,
            )


def _debut(jour: date | None) -> datetime | None:
    """Une date de début couvre la journée entière, dès minuit."""
    return datetime.combine(jour, datetime.min.time()) if jour else None


def _fin(jour: date | None) -> datetime | None:
    """Une date de fin couvre la journée entière, jusqu'à son dernier instant.

    Sans cela, filtrer « jusqu'au 31 août » exclurait tout le 31 août, ce que
    personne n'attend.
    """
    return datetime.combine(jour, datetime.max.time()) if jour else None
