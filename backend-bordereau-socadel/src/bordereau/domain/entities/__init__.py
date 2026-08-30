"""Entités du domaine : objets porteurs d'identité et de règles métier."""

from .affectation import Affectation
from .agent_terrain import AgentTerrain
from .client import Client
from .itineraire import Itineraire
from .ligne_bordereau import LigneBordereau
from .utilisateur import Utilisateur

__all__ = [
    "Affectation",
    "AgentTerrain",
    "Client",
    "Itineraire",
    "LigneBordereau",
    "Utilisateur",
]
