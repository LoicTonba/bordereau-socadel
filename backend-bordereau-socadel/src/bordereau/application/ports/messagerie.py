"""Port de messagerie électronique.

Le domaine ne rédige pas de courriels : il énonce l'événement, et la couche
application demande l'envoi. Le port permet de brancher un vrai serveur SMTP
en production et un adaptateur qui écrit sur disque en développement, sans que
les cas d'usage sachent lequel est en place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Courriel:
    """Message prêt à partir."""

    destinataire: str
    sujet: str
    corps_texte: str
    corps_html: str | None = None


@runtime_checkable
class Messagerie(Protocol):
    """Envoi de courriels transactionnels."""

    def envoyer(self, courriel: Courriel) -> None:
        """Expédie le message.

        L'implémentation ne doit **pas** faire échouer le cas d'usage appelant
        si le serveur est indisponible : un compte créé dont le courriel n'est
        pas parti reste un compte créé, et le lien peut être renvoyé.
        """
        ...


@runtime_checkable
class GenerateurJeton(Protocol):
    """Fabrique de jetons à usage unique (vérification, réinitialisation)."""

    def nouveau(self) -> str: ...
