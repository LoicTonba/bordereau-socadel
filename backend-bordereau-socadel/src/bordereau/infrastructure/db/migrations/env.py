"""Environnement Alembic, branché sur les réglages de l'application."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from bordereau.infrastructure.config.settings import get_settings
from bordereau.infrastructure.db.base import Base

# Importé pour son effet de bord : sans cela, `Base.metadata` est vide et
# l'autogénération proposerait de supprimer toutes les tables.
from bordereau.infrastructure.db.models import tables  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Génère le SQL sans se connecter, pour relecture avant application."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _appliquer(connexion) -> None:
    context.configure(
        connection=connexion,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Applique les migrations sur la base configurée."""
    moteur = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        # Les migrations sont un processus court : le pooling n'apporte rien
        # et peut retenir des connexions après la fin du script.
        poolclass=NullPool,
    )

    async with moteur.connect() as connexion:
        await connexion.run_sync(_appliquer)

    await moteur.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
