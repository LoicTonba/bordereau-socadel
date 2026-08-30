"""Rédaction des courriels transactionnels.

Le gabarit met en forme, les messages disent quoi. Le transport reste derrière
le port `Messagerie`, dans l'infrastructure.
"""

from .gabarit import Bouton, Message, en_html, en_texte
from .messages import (
    acces_ouvert,
    demande_refusee,
    reinitialisation_demandee,
    reinitialisation_par_responsable,
    verification_adresse,
)

__all__ = [
    "Bouton",
    "Message",
    "acces_ouvert",
    "demande_refusee",
    "en_html",
    "en_texte",
    "reinitialisation_demandee",
    "reinitialisation_par_responsable",
    "verification_adresse",
]
