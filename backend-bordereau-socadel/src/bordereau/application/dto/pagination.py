"""DTO de pagination, partagés par tous les listings du back-office."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")

TAILLE_PAGE_DEFAUT = 25
TAILLE_PAGE_MAX = 200


@dataclass(frozen=True, slots=True)
class PaginationParams:
    """Paramètres de pagination bornés.

    La borne haute est une protection : le tableau porte sur un référentiel de
    plus de 400 000 lignes, une page non bornée mettrait l'API à genoux.
    """

    page: int = 1
    taille: int = TAILLE_PAGE_DEFAUT
    tri: str | None = None
    ordre_descendant: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "page", max(1, self.page))
        object.__setattr__(self, "taille", max(1, min(self.taille, TAILLE_PAGE_MAX)))

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.taille

    @property
    def limite(self) -> int:
        return self.taille


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    """Tranche de résultats accompagnée de son contexte de navigation."""

    elements: Sequence[T]
    total: int
    page: int
    taille: int

    @property
    def nombre_de_pages(self) -> int:
        if self.taille <= 0:
            return 0
        return ceil(self.total / self.taille)

    @property
    def a_page_suivante(self) -> bool:
        return self.page < self.nombre_de_pages

    @property
    def a_page_precedente(self) -> bool:
        return self.page > 1

    @classmethod
    def vide(cls, params: PaginationParams) -> "Page[T]":
        return cls(elements=[], total=0, page=params.page, taille=params.taille)
