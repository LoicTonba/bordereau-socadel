"""Entités du domaine : objets porteurs d'identité et de règles métier."""

from .affectation import Affectation
from .agence import Agence
from .agent_terrain import AgentTerrain
from .client import Client
from .itineraire import Itineraire
from .ligne_bordereau import LigneBordereau
from .utilisateur import Utilisateur

__all__ = [
    "Affectation",
    "Agence",
    "AgentTerrain",
    "Client",
    "Itineraire",
    "LigneBordereau",
    "Utilisateur",
]
