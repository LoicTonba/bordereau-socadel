"""Entité : itinéraire de relève, unité de travail de l'agent de terrain."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..value_objects import CodeItineraire


@dataclass(slots=True)
class Itineraire:
    """Tournée regroupant les clients d'une même zone de relève.

    Les agents connaissent déjà physiquement ces parcours (les maisons, l'ordre
    de passage) : l'application ne cartographie pas, elle se contente de leur
    fournir la liste ordonnée des clients à démarcher.
    """

    code: CodeItineraire
    libelle: str | None = None
    region: str | None = None
    division: str | None = None
    agence: str | None = None
    mrc: str | None = None
    nombre_clients: int = 0
    id: UUID = field(default_factory=uuid4)

    @property
    def designation(self) -> str:
        """Libellé affichable : le nom métier s'il existe, sinon le code."""
        return self.libelle or f"Itinéraire {self.code}"

    def taux_couverture(self, clients_traites: int) -> float:
        """Part des clients de l'itinéraire déjà démarchés, entre 0 et 1."""
        if self.nombre_clients <= 0:
            return 0.0
        return min(clients_traites / self.nombre_clients, 1.0)
