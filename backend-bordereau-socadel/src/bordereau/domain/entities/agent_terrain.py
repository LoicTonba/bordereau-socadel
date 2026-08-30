"""Entité : agent de terrain, collecteur de numéros WhatsApp."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..errors import RegleMetierViolee
from ..value_objects import NumeroTelephone


@dataclass(slots=True)
class AgentTerrain:
    """Collecteur qui parcourt les itinéraires, muni du bordereau imprimé.

    Il n'a pas de compte applicatif : il est identifié par son matricule et
    rattaché aux affectations que le superviseur lui attribue. Sa production
    déclarée sert de base à sa rémunération.
    """

    matricule: str
    nom_complet: str
    telephone: NumeroTelephone | None = None
    zone_rattachement: str | None = None
    """Agence ou centre de rattachement, ex. `CSC_NSAM`."""

    region: str | None = None
    photo_url: str | None = None
    """Portrait de l'agent, affiché au répertoire et sur le bordereau papier."""

    actif: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.matricule.strip():
            raise RegleMetierViolee("Le matricule de l'agent est obligatoire")
        if not self.nom_complet.strip():
            raise RegleMetierViolee("Le nom de l'agent est obligatoire")
        self.matricule = self.matricule.strip().upper()
        self.nom_complet = self.nom_complet.strip()

    def modifier(
        self,
        *,
        nom_complet: str | None = None,
        telephone: NumeroTelephone | None = None,
        zone_rattachement: str | None = None,
        region: str | None = None,
        photo_url: str | None = None,
    ) -> None:
        """Met à jour la fiche. Le matricule, lui, ne change jamais : il est
        référencé par tous les bordereaux passés."""
        if nom_complet is not None:
            if not nom_complet.strip():
                raise RegleMetierViolee("Le nom de l'agent est obligatoire")
            self.nom_complet = nom_complet.strip()
        if telephone is not None:
            self.telephone = telephone
        if zone_rattachement is not None:
            self.zone_rattachement = zone_rattachement
        if region is not None:
            self.region = region
        if photo_url is not None:
            self.photo_url = photo_url

    def desactiver(self) -> None:
        self.actif = False

    def reactiver(self) -> None:
        self.actif = True

    def verifier_affectable(self) -> None:
        """Garde-fou appelé avant toute nouvelle affectation d'itinéraire."""
        if not self.actif:
            raise RegleMetierViolee(
                f"L'agent {self.matricule} est désactivé : affectation impossible"
            )
