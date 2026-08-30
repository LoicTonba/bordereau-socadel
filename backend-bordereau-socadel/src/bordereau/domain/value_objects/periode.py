"""Objet-valeur : intervalle de dates fermé, utilisé par les KPI et les exports."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta

from ..errors import ValidationError


@dataclass(frozen=True, slots=True)
class Periode:
    """Intervalle `[debut, fin]` inclusif."""

    debut: date
    fin: date

    def __post_init__(self) -> None:
        if self.debut > self.fin:
            raise ValidationError(
                f"Période invalide : début {self.debut} postérieur à la fin {self.fin}"
            )

    @classmethod
    def jour(cls, jour: date) -> "Periode":
        return cls(jour, jour)

    @classmethod
    def derniers_jours(cls, fin: date, nombre: int) -> "Periode":
        if nombre < 1:
            raise ValidationError("Une période couvre au moins un jour")
        return cls(fin - timedelta(days=nombre - 1), fin)

    @property
    def nombre_de_jours(self) -> int:
        return (self.fin - self.debut).days + 1

    def contient(self, jour: date) -> bool:
        return self.debut <= jour <= self.fin

    def jours(self) -> Iterator[date]:
        """Itère sur chaque jour, pour construire des séries temporelles sans trou."""
        for offset in range(self.nombre_de_jours):
            yield self.debut + timedelta(days=offset)
