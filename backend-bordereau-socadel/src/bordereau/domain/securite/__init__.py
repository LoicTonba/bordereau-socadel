"""Politique d'habilitation du domaine : rôles, permissions et périmètres."""

from .permissions import (
    MATRICE,
    AccesRefuse,
    ContexteAcces,
    Permission,
    peut_agir_sur_agent,
    peut_agir_sur_compte,
    restreindre,
)

__all__ = [
    "AccesRefuse",
    "ContexteAcces",
    "MATRICE",
    "Permission",
    "peut_agir_sur_agent",
    "peut_agir_sur_compte",
    "restreindre",
]
