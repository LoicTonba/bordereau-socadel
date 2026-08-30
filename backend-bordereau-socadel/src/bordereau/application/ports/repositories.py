"""Ports de persistance.

Ce sont des *protocoles* : la couche application les déclare, la couche
infrastructure les implémente. C'est l'inversion de dépendance qui permet de
remplacer PostgreSQL par un double en mémoire dans les tests, sans toucher aux
cas d'usage.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date
from typing import Protocol, runtime_checkable
from uuid import UUID

from ...domain.entities import (
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
        pagination: PaginationParams | None = None,
    ) -> Page[Itineraire]: ...

    async def enregistrer_en_lot(self, itineraires: Iterable[Itineraire]) -> int: ...


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
