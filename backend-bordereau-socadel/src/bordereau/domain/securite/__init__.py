"""Politique d'habilitation du domaine : rôles, permissions et périmètres."""

from .permissions import (
    MATRICE,
    RANG,
    AccesRefuse,
    ContexteAcces,
    Permission,
    dans_le_perimetre,
    peut_agir_sur_agent,
    peut_agir_sur_compte,
    peut_agir_sur_role,
    restreindre,
)

__all__ = [
    "AccesRefuse",
    "ContexteAcces",
    "MATRICE",
    "Permission",
    "RANG",
    "dans_le_perimetre",
    "peut_agir_sur_agent",
    "peut_agir_sur_compte",
    "peut_agir_sur_role",
    "restreindre",
]
