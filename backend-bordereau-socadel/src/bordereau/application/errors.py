"""Erreurs applicatives : échecs de cas d'usage, distincts des erreurs métier.

Le refus d'accès ne figure pas ici : c'est une règle métier, portée par
`domain.securite.AccesRefuse`. En avoir deux versions homonymes conduisait
l'une des deux à échapper au mappage HTTP et à ressortir en 422 au lieu de 403.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base des erreurs levées par les cas d'usage."""

    code: str = "application_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class RessourceIntrouvable(ApplicationError):
    """L'entité visée n'existe pas."""

    code = "ressource_introuvable"

    def __init__(self, ressource: str, identifiant: object) -> None:
        super().__init__(f"{ressource} introuvable : {identifiant}")
        self.ressource = ressource
        self.identifiant = identifiant


class IdentifiantsInvalides(ApplicationError):
    """Login ou mot de passe incorrect.

    Le message reste volontairement générique : distinguer « compte inconnu »
    de « mot de passe faux » renseignerait un attaquant sur les comptes
    existants.
    """

    code = "identifiants_invalides"

    def __init__(self) -> None:
        super().__init__("Identifiant ou mot de passe incorrect")


class JetonInvalide(ApplicationError):
    """Jeton de session absent, expiré ou falsifié."""

    code = "jeton_invalide"


class ConflitRessource(ApplicationError):
    """L'opération heurte un état existant (doublon d'affectation, etc.)."""

    code = "conflit"


class ImportInvalide(ApplicationError):
    """Le fichier déposé ne peut pas être exploité."""

    code = "import_invalide"
