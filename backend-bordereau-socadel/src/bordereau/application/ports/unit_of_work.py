"""Port `UnitOfWork` : frontière transactionnelle des cas d'usage.

Un cas d'usage ouvre une unité de travail, manipule les repositories qu'elle
expose, puis valide. Tout échec en cours de route annule l'ensemble — ce qui
compte pour l'import d'un bordereau : une ligne rejetée ne doit pas laisser un
demi-fichier en base.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, runtime_checkable

from .repositories import (
    AgenceRepository,
    AuditRepository,
    RestrictionRepository,
    AffectationRepository,
    AgentRepository,
    ClientRepository,
    ItineraireRepository,
    LigneBordereauRepository,
    UtilisateurRepository,
)


@runtime_checkable
class UnitOfWork(Protocol):
    """Contexte transactionnel exposant les repositories du périmètre."""

    utilisateurs: UtilisateurRepository
    agents: AgentRepository
    agences: AgenceRepository
    audit: AuditRepository
    restrictions: RestrictionRepository
    clients: ClientRepository
    itineraires: ItineraireRepository
    affectations: AffectationRepository
    lignes: LigneBordereauRepository

    async def __aenter__(self) -> "UnitOfWork": ...

    async def __aexit__(
        self,
        type_exception: type[BaseException] | None,
        exception: BaseException | None,
        trace: TracebackType | None,
    ) -> None: ...

    async def valider(self) -> None:
        """Committe la transaction."""
        ...

    async def annuler(self) -> None:
        """Annule la transaction."""
        ...
