"""Ports de sécurité : hachage de mot de passe et jetons de session."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from ...domain.enums import Role


@runtime_checkable
class HacheurMotDePasse(Protocol):
    """Abstrait l'algorithme de hachage (bcrypt aujourd'hui, autre demain)."""

    def hacher(self, en_clair: str) -> str: ...

    def verifier(self, en_clair: str, empreinte: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class ContenuJeton:
    """Charge utile d'un jeton de session, une fois validée."""

    utilisateur_id: UUID
    identifiant: str
    role: Role
    expire_le: datetime


@runtime_checkable
class ServiceJeton(Protocol):
    """Émission et vérification des jetons d'accès."""

    def emettre(self, contenu: ContenuJeton) -> str: ...

    def decoder(self, jeton: str) -> ContenuJeton:
        """Décode et valide un jeton.

        Raises:
            JetonInvalide: si la signature est mauvaise ou le jeton expiré.
        """
        ...


@runtime_checkable
class Horloge(Protocol):
    """Source de temps injectable — rend les cas d'usage testables."""

    def maintenant(self) -> datetime: ...

    def aujourdhui(self): ...
