"""Schémas HTTP transverses : pagination, erreurs, énumérations exposées."""

from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from ....application.dto import Page

T = TypeVar("T")


class SchemaBase(BaseModel):
    """Configuration commune : sérialisation en camelCase côté frontend."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda nom: "".join(
            mot if index == 0 else mot.capitalize()
            for index, mot in enumerate(nom.split("_"))
        ),
    )


class MetaPagination(SchemaBase):
    page: int
    taille: int
    total: int
    nombre_de_pages: int
    a_page_suivante: bool
    a_page_precedente: bool


class ReponsePaginee(SchemaBase, Generic[T]):
    """Enveloppe standard des listings."""

    elements: Sequence[T]
    meta: MetaPagination

    @classmethod
    def depuis_page(cls, page: Page, elements: Sequence[T]) -> "ReponsePaginee[T]":
        return cls(
            elements=elements,
            meta=MetaPagination(
                page=page.page,
                taille=page.taille,
                total=page.total,
                nombre_de_pages=page.nombre_de_pages,
                a_page_suivante=page.a_page_suivante,
                a_page_precedente=page.a_page_precedente,
            ),
        )


class ReponseErreur(SchemaBase):
    """Format unique des erreurs, pour que le frontend n'ait qu'un cas à gérer."""

    code: str = Field(description="Identifiant stable de l'erreur, ex. `acces_refuse`")
    message: str = Field(description="Message affichable tel quel à l'utilisateur")
    details: dict[str, object] | None = None
