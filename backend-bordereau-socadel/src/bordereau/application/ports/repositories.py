"""Ports de persistance.

Ce sont des *protocoles* : la couche application les déclare, la couche
infrastructure les implémente. C'est l'inversion de dépendance qui permet de
remplacer PostgreSQL par un double en mémoire dans les tests, sans toucher aux
cas d'usage.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from ...domain.entities import (
    Agence,
    TraceAudit,
    Affectation,
    AgentTerrain,
    Client,
    Itineraire,
    LigneBordereau,
    Utilisateur,
)
from ...domain.value_objects import CodeItineraire, Periode, ServiceNo
from ..dto.pagination import Page, PaginationParams
from ..dto.filtres import FiltreBordereau


@runtime_checkable
class UtilisateurRepository(Protocol):
    async def par_identifiant(self, identifiant: str) -> Utilisateur | None: ...

    async def par_id(self, utilisateur_id: UUID) -> Utilisateur | None: ...

    async def par_email(self, email: str) -> Utilisateur | None: ...

    async def par_jeton_verification(self, jeton: str) -> Utilisateur | None: ...

    async def par_jeton_reinitialisation(self, jeton: str) -> Utilisateur | None: ...

    async def lister(
        self, *, statut: str | None = None
    ) -> Sequence[Utilisateur]: ...

    async def enregistrer(self, utilisateur: Utilisateur) -> None: ...


@runtime_checkable
class AgentRepository(Protocol):
    async def par_id(self, agent_id: UUID) -> AgentTerrain | None: ...

    async def par_matricule(self, matricule: str) -> AgentTerrain | None: ...

    async def lister(self, *, actifs_seulement: bool = False) -> Sequence[AgentTerrain]: ...

    async def enregistrer(self, agent: AgentTerrain) -> None: ...


@runtime_checkable
class RestrictionRepository(Protocol):
    """Permissions retirées aux rôles. Ne peut que retrancher."""

    async def lister(self) -> dict[str, set[str]]:
        """Les restrictions en vigueur, indexées par rôle."""
        ...

    async def pour(self, role: str) -> set[str]: ...

    async def definir(self, role: str, permissions: set[str]) -> None:
        """Remplace les restrictions d'un rôle par celles fournies."""
        ...


@runtime_checkable
class AuditRepository(Protocol):
    """Journal des gestes posés. On y ajoute, on n'en retire jamais."""

    async def enregistrer(self, trace: TraceAudit) -> None: ...

    async def rechercher(
        self,
        *,
        identifiant: str | None = None,
        action: str | None = None,
        depuis: datetime | None = None,
        jusqu_a: datetime | None = None,
        echecs_seulement: bool = False,
        pagination: PaginationParams | None = None,
    ) -> Page[TraceAudit]: ...


@runtime_checkable
class AgenceRepository(Protocol):
    """Le maillage territorial, tenu par l'application."""

    async def par_nom(self, nom: str) -> Agence | None: ...

    async def lister(self, *, ouvertes_seulement: bool = False) -> Sequence[Agence]: ...

    async def enregistrer(self, agence: Agence) -> None: ...

    async def supprimer(self, nom: str) -> None: ...

    async def compter_rattachements(self, nom: str) -> int:
        """Nombre de comptes et d'itinéraires qui portent cette agence.

        Non nul, la suppression est refusée : effacer laisserait des périmètres
        pointant dans le vide.
        """
        ...


@runtime_checkable
class ClientRepository(Protocol):
    """Accès au référentiel SOCADEL — la source de vérité."""

    async def par_service_no(self, service_no: ServiceNo) -> Client | None: ...

    async def par_services_no(
        self, services_no: Iterable[ServiceNo]
    ) -> dict[str, Client]:
        """Chargement en lot, indexé par `service_no`.

        Indispensable pour vérifier un bordereau entier sans provoquer un
        accès par ligne sur une table de plusieurs centaines de milliers
        d'enregistrements.
        """
        ...

    async def par_itineraire(
        self, code: CodeItineraire, pagination: PaginationParams | None = None
    ) -> Sequence[Client]: ...

    async def compter_par_itineraire(self, code: CodeItineraire) -> int: ...

    async def lister_agences(self) -> Sequence[tuple[str, str | None, str | None]]:
        """Annuaire distinct (agence, région, division), trié par territoire."""
        ...

    async def enregistrer_en_lot(self, clients: Iterable[Client]) -> int:
        """Insertion/mise à jour de masse pour l'import du référentiel."""
        ...


@runtime_checkable
class ItineraireRepository(Protocol):
    async def par_code(self, code: CodeItineraire) -> Itineraire | None: ...

    async def rechercher(
        self,
        *,
        terme: str | None = None,
        region: str | None = None,
        agence: str | None = None,
        codes: Sequence[CodeItineraire] = (),
        pagination: PaginationParams | None = None,
    ) -> Page[Itineraire]: ...

    async def enregistrer_en_lot(self, itineraires: Iterable[Itineraire]) -> int: ...

    async def est_affecte(self, code: CodeItineraire) -> bool:
        """Vrai si la tournée a déjà été confiée à un agent.

        Une tournée qui a servi ne se supprime plus : la production saisie y
        renvoie, et l'effacer laisserait des lignes orphelines.
        """
        ...

    async def supprimer(self, code: CodeItineraire) -> None: ...


@runtime_checkable
class AffectationRepository(Protocol):
    async def par_id(self, affectation_id: UUID) -> Affectation | None: ...

    async def lister_du_jour(self, jour: date) -> Sequence[Affectation]: ...

    async def lister_par_agent(
        self, agent_id: UUID, periode: Periode
    ) -> Sequence[Affectation]: ...

    async def existe_deja(
        self, agent_id: UUID, code: CodeItineraire, jour: date
    ) -> bool:
        """Empêche d'affecter deux fois le même itinéraire au même agent le
        même jour — sinon la production serait comptée en double."""
        ...

    async def enregistrer(self, affectation: Affectation) -> None: ...


@runtime_checkable
class LigneBordereauRepository(Protocol):
    async def par_id(self, ligne_id: UUID) -> LigneBordereau | None: ...

    async def rechercher(
        self, filtre: FiltreBordereau, pagination: PaginationParams
    ) -> Page[LigneBordereau]: ...

    async def lister_pour_export(
        self, filtre: FiltreBordereau, limite: int
    ) -> Sequence[LigneBordereau]:
        """Variante non paginée et bornée, pour les exports PDF / CSV."""
        ...

    async def lister_par_affectation(
        self, affectation_id: UUID
    ) -> Sequence[LigneBordereau]: ...

    async def enregistrer(self, ligne: LigneBordereau) -> None: ...

    async def enregistrer_en_lot(self, lignes: Iterable[LigneBordereau]) -> int: ...
