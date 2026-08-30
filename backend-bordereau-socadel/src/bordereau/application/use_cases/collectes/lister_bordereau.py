"""Cas d'usage : listing paginé et filtré du bordereau."""

from __future__ import annotations

from ....domain.entities import LigneBordereau
from ....domain.securite import ContexteAcces, Permission, restreindre
from ...dto import FiltreBordereau, Page, PaginationParams
from ...ports import UnitOfWork


class ListerBordereau:
    """Alimente le tableau principal du back-office.

    Le filtre est d'abord **rétréci au périmètre de l'appelant**, puis poussé
    jusqu'au SQL : sur un référentiel de plus de 400 000 lignes, filtrer en
    mémoire n'est pas envisageable, et contrôler après coup laisserait fuir.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self,
        contexte: ContexteAcces,
        filtre: FiltreBordereau,
        pagination: PaginationParams,
    ) -> Page[LigneBordereau]:
        contexte.exiger(Permission.BORDEREAU_LIRE)
        perimetre = restreindre(contexte, filtre)

        async with self._uow as uow:
            return await uow.lignes.rechercher(perimetre, pagination)
