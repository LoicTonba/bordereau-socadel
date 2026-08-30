"""Objet-valeur : code d'itinéraire de relève (colonnes ITINERAIRE / NUM_ITIN)."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import ValidationError


@dataclass(frozen=True, slots=True)
class CodeItineraire:
    """Identifiant numérique d'une tournée de relève.

    C'est l'unité de travail confiée à un agent de terrain : le superviseur
    affecte des itinéraires, et l'agent ne reçoit que les clients qui en
    relèvent.
    """

    valeur: int

    def __post_init__(self) -> None:
        if self.valeur <= 0:
            raise ValidationError(f"Code itinéraire invalide : {self.valeur!r}")

    @classmethod
    def parse(cls, brut: str | int | None) -> "CodeItineraire":
        if brut is None:
            raise ValidationError("Code itinéraire manquant")
        texte = str(brut).strip()
        if texte.endswith(".0"):
            texte = texte[:-2]
        if not texte.isdigit():
            raise ValidationError(f"Code itinéraire non numérique : {brut!r}")
        return cls(int(texte))

    @classmethod
    def parse_ou_none(cls, brut: str | int | None) -> "CodeItineraire | None":
        try:
            return cls.parse(brut)
        except ValidationError:
            return None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.valeur)
