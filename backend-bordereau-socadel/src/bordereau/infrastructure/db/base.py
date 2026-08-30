"""Base déclarative SQLAlchemy et conventions de nommage."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

#: Nommage explicite des contraintes : sans cela, Alembic génère des noms
#: aléatoires que les migrations suivantes ne savent plus retrouver.
CONVENTION_NOMMAGE = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Racine des modèles ORM."""

    metadata = MetaData(naming_convention=CONVENTION_NOMMAGE)


class HorodatageMixin:
    """Colonnes d'audit communes, renseignées côté base."""

    cree_le: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    mis_a_jour_le: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
