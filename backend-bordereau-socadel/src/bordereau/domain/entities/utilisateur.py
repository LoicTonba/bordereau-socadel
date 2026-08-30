"""Entité : compte de connexion à la plateforme."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from ..enums import Role
from ..errors import RegleMetierViolee
from ..securite import ContexteAcces


@dataclass(slots=True)
class Utilisateur:
    """Compte autorisé à se connecter.

    Trois profils s'y connectent, avec des portées très différentes :
    l'administrateur gère les comptes et le référentiel, le superviseur pilote
    les agents et saisit leur production, et l'agent de terrain se contente de
    consulter ses propres chiffres.
    """

    identifiant: str
    """Login court, ex. `superviseur` ou le matricule pour un agent."""

    nom_complet: str
    empreinte_mot_de_passe: str
    role: Role = Role.SUPERVISEUR
    actif: bool = True

    agent_id: UUID | None = None
    """Agent de terrain rattaché. Obligatoire pour un compte `AGENT_TERRAIN` :
    c'est lui qui délimite les données que le titulaire pourra voir."""

    region: str | None = None
    agence: str | None = None
    """Périmètre territorial d'un superviseur. `None` = périmètre national."""

    photo_url: str | None = None
    email: str | None = None
    derniere_connexion: datetime | None = None
    doit_changer_mot_de_passe: bool = False
    """Vrai tant que le titulaire n'a pas remplacé son mot de passe initial."""

    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.identifiant.strip():
            raise RegleMetierViolee("L'identifiant de connexion est obligatoire")
        self.identifiant = self.identifiant.strip().lower()

        if self.role is Role.AGENT_TERRAIN and self.agent_id is None:
            # Sans rattachement, la politique ABAC ne saurait pas quoi montrer,
            # et un tel compte verrait par défaut la production de tous.
            raise RegleMetierViolee(
                "Un compte agent de terrain doit être rattaché à un agent"
            )

    @property
    def est_administrateur(self) -> bool:
        return self.role is Role.ADMINISTRATEUR

    @property
    def est_agent(self) -> bool:
        return self.role is Role.AGENT_TERRAIN

    def contexte_acces(self) -> ContexteAcces:
        """Projette le compte en identité effective pour les gardes d'accès."""
        return ContexteAcces(
            utilisateur_id=self.id,
            role=self.role,
            agent_id=self.agent_id,
            region=self.region,
            agence=self.agence,
        )

    def peut_se_connecter(self) -> bool:
        return self.actif

    def enregistrer_connexion(self, horodatage: datetime) -> None:
        """Trace la connexion réussie — refuser un compte désactivé est une
        décision métier, pas un détail d'infrastructure."""
        if not self.actif:
            raise RegleMetierViolee("Ce compte est désactivé")
        self.derniere_connexion = horodatage

    def changer_mot_de_passe(self, empreinte: str) -> None:
        self.empreinte_mot_de_passe = empreinte
        self.doit_changer_mot_de_passe = False
