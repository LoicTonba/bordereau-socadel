"""Objet-valeur : référence géographique SOCADEL (colonne REF_GEO)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..errors import ValidationError

#: Forme observée : `807-09-01-994-00-001`, segments de longueur variable.
_REF_GEO = re.compile(r"^\d{3}(?:-\d{2,4}){4,5}$")


@dataclass(frozen=True, slots=True)
class RefGeo:
    """Adresse technique d'un point de livraison.

    Elle encode la hiérarchie territoriale `centre-quartier-ilot-parcelle-...`.
    C'est elle qui donne l'ordre de marche de l'agent sur son itinéraire :
    trier par `cle_tri` restitue le parcours physique des maisons.
    """

    valeur: str

    def __post_init__(self) -> None:
        if not _REF_GEO.match(self.valeur):
            raise ValidationError(f"REF_GEO invalide : {self.valeur!r}")

    @classmethod
    def parse(cls, brut: str | None) -> "RefGeo":
        if brut is None:
            raise ValidationError("REF_GEO manquante")
        return cls(str(brut).strip())

    @classmethod
    def parse_ou_none(cls, brut: str | None) -> "RefGeo | None":
        try:
            return cls.parse(brut)
        except ValidationError:
            return None

    @property
    def segments(self) -> tuple[str, ...]:
        return tuple(self.valeur.split("-"))

    @property
    def centre(self) -> str:
        """Premier segment : le centre de distribution."""
        return self.segments[0]

    @property
    def cle_tri(self) -> tuple[int, ...]:
        """Clé de tri numérique, pour restituer l'ordre de marche terrain."""
        return tuple(int(s) for s in self.segments)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.valeur
