"""DTO des indicateurs affichés sur le tableau de bord du superviseur."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CarteKpi:
    """Valeur d'un indicateur, avec sa variation par rapport à la période
    précédente de même longueur — c'est la variation qui rend un KPI actionnable."""

    cle: str
    libelle: str
    valeur: float
    valeur_precedente: float | None = None
    unite: str | None = None

    @property
    def variation(self) -> float | None:
        """Variation relative, ou `None` si la comparaison n'a pas de sens."""
        if self.valeur_precedente is None or self.valeur_precedente == 0:
            return None
        return (self.valeur - self.valeur_precedente) / self.valeur_precedente


@dataclass(frozen=True, slots=True)
class PointSerie:
    """Point d'une série temporelle d'évolution."""

    jour: date
    collectes: int
    abonnements: int
    confirmes: int


@dataclass(frozen=True, slots=True)
class LigneClassementAgent:
    """Ligne du classement des agents, pour le suivi individuel."""

    agent_id: UUID
    matricule: str
    nom_complet: str
    lignes_traitees: int
    abonnements_declares: int
    abonnements_confirmes: int
    taux_conversion: float
    taux_fiabilite: float


@dataclass(frozen=True, slots=True)
class CouvertureItineraire:
    """Avancement d'un itinéraire : combien de portes restent à faire."""

    code_itineraire: int
    libelle: str
    agence: str | None
    clients_total: int
    clients_traites: int
    abonnements: int

    @property
    def taux_couverture(self) -> float:
        if self.clients_total <= 0:
            return 0.0
        return min(self.clients_traites / self.clients_total, 1.0)


@dataclass(frozen=True, slots=True)
class TableauDeBord:
    """Agrégat complet renvoyé à l'écran d'accueil du superviseur."""

    kpis: tuple[CarteKpi, ...]
    evolution: tuple[PointSerie, ...]
    classement_agents: tuple[LigneClassementAgent, ...]
    couverture_itineraires: tuple[CouvertureItineraire, ...]
    repartition_statuts: dict[str, int]
