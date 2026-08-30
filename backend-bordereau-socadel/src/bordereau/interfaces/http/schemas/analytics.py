"""Schémas HTTP du tableau de bord."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from ....application.dto import TableauDeBord
from .commun import SchemaBase


class CarteKpiSortie(SchemaBase):
    cle: str
    libelle: str
    valeur: float
    valeur_precedente: float | None
    variation: float | None
    unite: str | None


class PointSerieSortie(SchemaBase):
    jour: date
    collectes: int
    abonnements: int
    confirmes: int


class LigneClassementSortie(SchemaBase):
    agent_id: UUID
    matricule: str
    nom_complet: str
    lignes_traitees: int
    abonnements_declares: int
    abonnements_confirmes: int
    taux_conversion: float
    taux_fiabilite: float


class CouvertureItineraireSortie(SchemaBase):
    code_itineraire: int
    libelle: str
    agence: str | None
    clients_total: int
    clients_traites: int
    abonnements: int
    taux_couverture: float


class ReponseTableauDeBord(SchemaBase):
    kpis: list[CarteKpiSortie]
    evolution: list[PointSerieSortie]
    classement_agents: list[LigneClassementSortie]
    couverture_itineraires: list[CouvertureItineraireSortie]
    repartition_statuts: dict[str, int]

    @classmethod
    def depuis_dto(cls, tableau: TableauDeBord) -> "ReponseTableauDeBord":
        return cls(
            kpis=[
                CarteKpiSortie(
                    cle=k.cle,
                    libelle=k.libelle,
                    valeur=k.valeur,
                    valeur_precedente=k.valeur_precedente,
                    variation=k.variation,
                    unite=k.unite,
                )
                for k in tableau.kpis
            ],
            evolution=[
                PointSerieSortie(
                    jour=p.jour,
                    collectes=p.collectes,
                    abonnements=p.abonnements,
                    confirmes=p.confirmes,
                )
                for p in tableau.evolution
            ],
            classement_agents=[
                LigneClassementSortie(
                    agent_id=a.agent_id,
                    matricule=a.matricule,
                    nom_complet=a.nom_complet,
                    lignes_traitees=a.lignes_traitees,
                    abonnements_declares=a.abonnements_declares,
                    abonnements_confirmes=a.abonnements_confirmes,
                    taux_conversion=a.taux_conversion,
                    taux_fiabilite=a.taux_fiabilite,
                )
                for a in tableau.classement_agents
            ],
            couverture_itineraires=[
                CouvertureItineraireSortie(
                    code_itineraire=c.code_itineraire,
                    libelle=c.libelle,
                    agence=c.agence,
                    clients_total=c.clients_total,
                    clients_traites=c.clients_traites,
                    abonnements=c.abonnements,
                    taux_couverture=c.taux_couverture,
                )
                for c in tableau.couverture_itineraires
            ],
            repartition_statuts=tableau.repartition_statuts,
        )
