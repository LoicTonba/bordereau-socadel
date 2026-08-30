"""Entité : affectation d'un itinéraire à un agent pour une journée donnée."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from ..enums import StatutAffectation
from ..errors import TransitionInterdite
from ..value_objects import CodeItineraire

#: Transitions autorisées du cycle de vie d'une affectation.
_TRANSITIONS: dict[StatutAffectation, frozenset[StatutAffectation]] = {
    StatutAffectation.PLANIFIEE: frozenset(
        {StatutAffectation.EN_COURS, StatutAffectation.ANNULEE}
    ),
    StatutAffectation.EN_COURS: frozenset(
        {StatutAffectation.CLOTUREE, StatutAffectation.ANNULEE}
    ),
    StatutAffectation.CLOTUREE: frozenset(),
    StatutAffectation.ANNULEE: frozenset(),
}


@dataclass(slots=True)
class Affectation:
    """Trace le contact superviseur / agent avant la sortie terrain.

    C'est la pièce maîtresse du flux décrit par le métier : dès qu'un agent se
    présente, le superviseur enregistre les itinéraires qu'il lui confie. Cette
    affectation devient à la fois la preuve du briefing, le périmètre de
    travail de l'agent (il ne voit que ses itinéraires) et la source du
    template imprimable qu'il emportera sur le terrain.
    """

    agent_id: UUID
    itineraire_code: CodeItineraire
    date_travail: date
    superviseur_id: UUID
    statut: StatutAffectation = StatutAffectation.PLANIFIEE
    consignes: str | None = None
    cloturee_le: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    @property
    def est_ouverte(self) -> bool:
        """Une affectation ouverte accepte encore des saisies de collecte."""
        return self.statut in (StatutAffectation.PLANIFIEE, StatutAffectation.EN_COURS)

    def _transiter_vers(self, cible: StatutAffectation) -> None:
        if cible not in _TRANSITIONS[self.statut]:
            raise TransitionInterdite(
                f"Transition {self.statut.value} -> {cible.value} interdite "
                f"pour l'affectation {self.id}"
            )
        self.statut = cible

    def demarrer(self) -> None:
        """L'agent est parti sur le terrain avec son bordereau imprimé."""
        self._transiter_vers(StatutAffectation.EN_COURS)

    def cloturer(self, horodatage: datetime) -> None:
        """Le superviseur a fini de saisir la production de la journée."""
        self._transiter_vers(StatutAffectation.CLOTUREE)
        self.cloturee_le = horodatage

    def annuler(self) -> None:
        self._transiter_vers(StatutAffectation.ANNULEE)
