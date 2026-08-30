"""Adaptateurs de messagerie electronique."""

from .adapters import (
    GenerateurJetonAleatoire,
    MessagerieFichier,
    MessagerieSmtp,
)

__all__ = [
    "GenerateurJetonAleatoire",
    "MessagerieFichier",
    "MessagerieSmtp",
]
