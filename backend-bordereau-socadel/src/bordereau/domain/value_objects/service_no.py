"""Objet-valeur : identifiant client SOCADEL (SERVICE_NO / NIS_RAD / NUMERO_CONTRAT)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..errors import ValidationError

_SERVICE_NO = re.compile(r"^\d{6,12}$")


@dataclass(frozen=True, slots=True)
class ServiceNo:
    """Numéro de contrat client.

    Dans les fichiers sources la même valeur apparaît sous trois noms
    (`SERVICE_NO` dans le bordereau terrain, `NIS_RAD` et `NUMERO_CONTRAT`
    dans le référentiel) : c'est la clé de jointure entre la déclaration du
    superviseur et la source de vérité.
    """

    valeur: str

    def __post_init__(self) -> None:
        if not _SERVICE_NO.match(self.valeur):
            raise ValidationError(f"SERVICE_NO invalide : {self.valeur!r}")

    @classmethod
    def parse(cls, brut: str | int | None) -> "ServiceNo":
        if brut is None:
            raise ValidationError("SERVICE_NO manquant")
        texte = str(brut).strip()
        if texte.endswith(".0"):  # Excel remonte souvent les entiers en float
            texte = texte[:-2]
        return cls(texte)

    @classmethod
    def parse_ou_none(cls, brut: str | int | None) -> "ServiceNo | None":
        try:
            return cls.parse(brut)
        except ValidationError:
            return None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.valeur
