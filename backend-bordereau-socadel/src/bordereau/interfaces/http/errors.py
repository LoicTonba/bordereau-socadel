"""Traduction des erreurs métier et applicatives en réponses HTTP.

Le domaine et l'application ignorent HTTP : c'est ici, et seulement ici, que
leurs exceptions reçoivent un code de statut.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ...application.errors import (
    ApplicationError,
    ConflitRessource,
    IdentifiantsInvalides,
    ImportInvalide,
    JetonInvalide,
    RessourceIntrouvable,
)
from ...domain.securite import AccesRefuse
from ...domain.errors import (
    DomainError,
    RegleMetierViolee,
    TransitionInterdite,
    ValidationError,
)

logger = logging.getLogger(__name__)

#: Starlette a renommé la constante 422 ; l'entier reste stable quelle que soit
#: la version installée.
ENTITE_NON_TRAITABLE = 422

#: Correspondance exception -> statut HTTP.
STATUTS: dict[type[Exception], int] = {
    IdentifiantsInvalides: status.HTTP_401_UNAUTHORIZED,
    JetonInvalide: status.HTTP_401_UNAUTHORIZED,
    AccesRefuse: status.HTTP_403_FORBIDDEN,
    RessourceIntrouvable: status.HTTP_404_NOT_FOUND,
    ConflitRessource: status.HTTP_409_CONFLICT,
    ImportInvalide: ENTITE_NON_TRAITABLE,
    ValidationError: ENTITE_NON_TRAITABLE,
    RegleMetierViolee: ENTITE_NON_TRAITABLE,
    TransitionInterdite: status.HTTP_409_CONFLICT,
}


def _reponse(code: str, message: str, statut: int) -> JSONResponse:
    return JSONResponse(
        status_code=statut,
        content={"code": code, "message": message},
        headers=(
            # Sans ce header, un navigateur ne présentera jamais de nouvelle
            # tentative d'authentification.
            {"WWW-Authenticate": "Bearer"}
            if statut == status.HTTP_401_UNAUTHORIZED
            else None
        ),
    )


def enregistrer_gestionnaires(app: FastAPI) -> None:
    """Branche les gestionnaires d'exceptions sur l'application."""

    @app.exception_handler(DomainError)
    async def _domaine(request: Request, erreur: DomainError) -> JSONResponse:
        statut = STATUTS.get(type(erreur), ENTITE_NON_TRAITABLE)
        return _reponse(erreur.code, erreur.message, statut)

    @app.exception_handler(ApplicationError)
    async def _application(
        request: Request, erreur: ApplicationError
    ) -> JSONResponse:
        statut = STATUTS.get(type(erreur), status.HTTP_400_BAD_REQUEST)
        return _reponse(erreur.code, erreur.message, statut)

    @app.exception_handler(Exception)
    async def _inattendue(request: Request, erreur: Exception) -> JSONResponse:
        # Le détail part dans les logs, jamais dans la réponse : un message
        # d'exception peut contenir des fragments de requête ou de données.
        logger.exception(
            "Erreur non gérée sur %s %s", request.method, request.url.path
        )
        return _reponse(
            "erreur_interne",
            "Une erreur inattendue est survenue. L'incident a été enregistré.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
