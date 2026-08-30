"""Erreurs du domaine.

Ces exceptions ne connaissent ni HTTP ni base de données : la couche
`interfaces` se charge de les traduire en réponses.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base de toutes les violations de règles métier."""

    code: str = "domain_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class ValidationError(DomainError):
    """Une valeur ne respecte pas l'invariant d'un objet-valeur ou d'une entité."""

    code = "validation_error"


class TransitionInterdite(DomainError):
    """Changement d'état refusé par la machine à états métier."""

    code = "transition_interdite"


class RegleMetierViolee(DomainError):
    """Règle de gestion violée (quota, doublon, période clôturée...)."""

    code = "regle_metier_violee"
