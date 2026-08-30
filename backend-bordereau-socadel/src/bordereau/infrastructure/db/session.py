"""Moteur asynchrone et fabrique de sessions SQLAlchemy."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config.settings import Settings


def creer_moteur(settings: Settings) -> AsyncEngine:
    """Construit le moteur asynchrone.

    `pool_pre_ping` évite les erreurs sur connexion recyclée par PostgreSQL
    après une longue période d'inactivité — cas fréquent d'un back-office
    utilisé par vagues dans la journée.
    """
    return create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
    )


def creer_fabrique_sessions(
    moteur: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Fabrique de sessions.

    `expire_on_commit=False` permet de continuer à lire les objets après un
    commit, ce dont les mappers ont besoin pour reconstruire les entités.

    `autoflush` reste **actif**. C'est ce qui garantit qu'un objet ajouté à la
    session est écrit avant l'instruction suivante : sans lui, l'affectation
    créée par `AffecterItineraires` n'existerait pas encore quand les lignes de
    bordereau qui la référencent sont insérées en lot, et PostgreSQL rejetterait
    la clé étrangère.
    """
    return async_sessionmaker(
        bind=moteur,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
    )


@asynccontextmanager
async def session_scope(
    fabrique: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Session à durée de vie explicite, annulée en cas d'erreur."""
    session = fabrique()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
