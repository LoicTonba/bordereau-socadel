"""Point d'entrée ASGI : composition et configuration de l'application.

C'est le sommet de l'arbre de dépendances — le seul module qui connaisse à la
fois FastAPI, le conteneur et les réglages.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .infrastructure.config.settings import Settings, get_settings
from .infrastructure.container import Container
from .interfaces.http.api import creer_routeur
from .interfaces.http.audit import IntercepteurAudit
from .interfaces.http.errors import enregistrer_gestionnaires

logger = logging.getLogger(__name__)

DESCRIPTION = """
API du bordereau intelligent de collecte de numéros WhatsApp.

Le superviseur affecte les itinéraires aux agents de terrain, imprime leur
bordereau de travail, puis saisit au retour ce que chaque agent a réalisé.
Les déclarations sont ensuite confrontées au référentiel SOCADEL, qui fait
foi pour la rémunération.

Réalisé par **NEXT LTD** (Numeric Export Technologies) pour **SOCADEL**.
"""


def creer_application(settings: Settings | None = None) -> FastAPI:
    """Construit l'application.

    Args:
        settings: réglages explicites, principalement pour les tests ; à
            défaut, ils sont lus depuis l'environnement.
    """
    settings = settings or get_settings()

    @asynccontextmanager
    async def cycle_de_vie(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = Container(settings)
        logger.info(
            "Démarrage de %s en environnement %s",
            settings.nom_application,
            settings.environnement,
        )
        try:
            yield
        finally:
            # Le pool de connexions doit être rendu proprement, sinon
            # PostgreSQL garde des sessions ouvertes après l'arrêt.
            await app.state.container.fermer()

    app = FastAPI(
        title=settings.nom_application,
        description=DESCRIPTION,
        version="1.0.0",
        docs_url="/docs" if not settings.est_production else None,
        redoc_url=None,
        openapi_url="/openapi.json" if not settings.est_production else None,
        lifespan=cycle_de_vie,
    )

    # Le journal est monte avant CORS : il observe la requete telle qu'elle
    # ressort, code de statut compris.
    if settings.mode_demo:
        # Bruyant a dessein : ce reglage expose les mots de passe de mise en
        # route a un visiteur non authentifie. Il n'a rien a faire en
        # production, et personne ne doit pouvoir dire qu'il l'ignorait.
        logger.warning(
            "MODE DEMONSTRATION ACTIF : les comptes de mise en route et leurs "
            "mots de passe sont exposes publiquement. A desactiver "
            "imperativement en production (MODE_DEMO=false)."
        )

    app.add_middleware(IntercepteurAudit)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origines_autorisees,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Le frontend lit ces en-têtes pour nommer le fichier téléchargé et
        # signaler un export tronqué ; sans exposition explicite, le navigateur
        # les masque en cross-origin.
        expose_headers=[
            "Content-Disposition",
            "X-Export-Lignes",
            "X-Export-Tronque",
        ],
    )

    enregistrer_gestionnaires(app)
    app.include_router(creer_routeur(settings.prefixe_api))

    # Les photos de profil sont servies en statique depuis le même hôte que
    # l'API : le frontend n'a donc qu'une seule origine à connaître.
    repertoire_media = Path(settings.repertoire_media)
    repertoire_media.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=repertoire_media), name="media")

    @app.get("/sante", tags=["Service"], summary="Sonde de disponibilité")
    async def sante() -> dict[str, str]:
        return {"statut": "ok", "service": settings.nom_application}

    return app


app = creer_application()
