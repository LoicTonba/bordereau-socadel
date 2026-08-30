"""Assemblage du routeur principal de l'API."""

from __future__ import annotations

from fastapi import APIRouter

from .routers import (
    agents,
    analytics,
    auth,
    bordereau,
    comptes,
    imports_exports,
    itineraires,
    reference,
)


def creer_routeur(prefixe: str) -> APIRouter:
    """Monte tous les sous-routeurs sous le préfixe de version."""
    routeur = APIRouter(prefix=prefixe)

    routeur.include_router(auth.router)
    routeur.include_router(bordereau.router)
    routeur.include_router(itineraires.router)
    routeur.include_router(agents.router)
    routeur.include_router(comptes.router)
    routeur.include_router(imports_exports.router)
    routeur.include_router(analytics.router)
    routeur.include_router(reference.router)

    return routeur
