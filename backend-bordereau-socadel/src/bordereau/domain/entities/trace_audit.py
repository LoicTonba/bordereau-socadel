"""Entité : trace d'audit, ce que quelqu'un a fait et quand.

Qui a affecté cette tournée, qui a fermé cette agence, qui a réinitialisé ce
mot de passe. Sans réponse à ces questions, une plateforme qui décide de ce
qui sera payé n'est pas défendable devant un contrôle.

Ce que la trace retient, et ce qu'elle ne retient jamais.

Elle retient l'auteur, l'instant, le geste et sa cible, et l'issue. Elle est
**immuable** : rien dans l'application ne la modifie ni ne l'efface, seul le
super utilisateur peut la lire avec l'administrateur.

Elle ne retient jamais le contenu transmis. Un corps de requête porte des mots
de passe, des numéros de téléphone, des noms de clients : les recopier dans un
journal reviendrait à créer une seconde base de données personnelles, moins
protégée que la première, et consultable par des gens qui n'ont pas à la voir.
Le geste et sa cible suffisent à répondre à « qui a fait quoi ».
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class TraceAudit:
    """Un geste posé sur la plateforme, tel qu'il restera consultable."""

    quand: datetime
    #: Verbe et chemin, par exemple `POST /territoire/CSC_NDOP/fermeture`.
    action: str
    #: Ce sur quoi le geste a porté : un nom d'agence, un code, un identifiant.
    cible: str | None = None
    utilisateur_id: UUID | None = None
    #: Recopié plutôt que joint : un compte supprimé ne doit pas effacer la
    #: trace de ce qu'il a fait.
    identifiant: str | None = None
    role: str | None = None
    statut_http: int = 200
    adresse_ip: str | None = None
    id: UUID = field(default_factory=uuid4)

    @property
    def reussi(self) -> bool:
        return 200 <= self.statut_http < 400

    @property
    def auteur(self) -> str:
        """Qui a agi, lisible sans jointure."""
        return self.identifiant or "visiteur non authentifié"
