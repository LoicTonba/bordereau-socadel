"""Implémentation PostgreSQL du port `UnitOfWork`."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories.clients import ClientRepositoryPg
from .repositories.divers import (
    AgenceRepositoryPg,
    AffectationRepositoryPg,
    AgentRepositoryPg,
    ItineraireRepositoryPg,
    UtilisateurRepositoryPg,
)
from .repositories.lignes import LigneBordereauRepositoryPg


class UnitOfWorkPg:
    """Ouvre une session par bloc `async with` et expose les repositories.

    L'unité de travail est réentrante mais **non partagée** : chaque cas
    d'usage en instancie une, ce qui garantit qu'une requête HTTP ne peut pas
    voir la transaction en cours d'une autre.
    """

    def __init__(self, fabrique: async_sessionmaker[AsyncSession]) -> None:
        self._fabrique = fabrique
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWorkPg":
        self._session = self._fabrique()

        self.utilisateurs = UtilisateurRepositoryPg(self._session)
        self.agents = AgentRepositoryPg(self._session)
        self.agences = AgenceRepositoryPg(self._session)
        self.clients = ClientRepositoryPg(self._session)
        self.itineraires = ItineraireRepositoryPg(self._session)
        self.affectations = AffectationRepositoryPg(self._session)
        self.lignes = LigneBordereauRepositoryPg(self._session)

        return self

    async def __aexit__(
        self,
        type_exception: type[BaseException] | None,
        exception: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        try:
            # Toute sortie sans `valider()` explicite annule : un cas d'usage
            # qui lève ne doit jamais laisser d'écriture partielle derrière lui.
            if type_exception is not None:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def valider(self) -> None:
        if self._session is not None:
            await self._session.commit()

    async def annuler(self) -> None:
        if self._session is not None:
            await self._session.rollback()
