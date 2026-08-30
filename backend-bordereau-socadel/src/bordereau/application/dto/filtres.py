"""DTO de filtrage du tableau de bordereau.

Un seul objet de filtre sert le listing paginé, les exports CSV/PDF et les KPI :
c'est ce qui garantit qu'un export contient exactement ce que le superviseur
voit à l'écran.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ...domain.enums import Responsable, StatutCollecte, VerdictVerification
from ...domain.value_objects import CodeItineraire, Periode


@dataclass(frozen=True, slots=True)
class FiltreBordereau:
    """Critères de sélection des lignes de bordereau."""

    recherche: str | None = None
    """Recherche plein texte sur le nom, le SERVICE_NO, le compteur ou la REF_GEO."""

    periode: Periode | None = None
    statuts: tuple[StatutCollecte, ...] = ()
    verdicts: tuple[VerdictVerification, ...] = ()
    responsables: tuple[Responsable, ...] = ()
    itineraires: tuple[CodeItineraire, ...] = ()
    agent_ids: tuple[UUID, ...] = ()
    region: str | None = None
    division: str | None = None
    agence: str | None = None

    @property
    def est_vide(self) -> bool:
        """Vrai si aucun critère n'est posé — utile pour avertir l'utilisateur
        avant un export qui porterait sur tout le référentiel."""
        return not any(
            (
                self.recherche,
                self.periode,
                self.statuts,
                self.verdicts,
                self.responsables,
                self.itineraires,
                self.agent_ids,
                self.region,
                self.division,
                self.agence,
            )
        )


@dataclass(frozen=True, slots=True)
class FiltreItineraire:
    """Critères de recherche d'itinéraires, pour l'écran d'affectation."""

    terme: str | None = None
    region: str | None = None
    agence: str | None = None
