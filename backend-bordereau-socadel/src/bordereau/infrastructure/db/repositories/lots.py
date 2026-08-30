"""Découpage des insertions de masse.

PostgreSQL n'accepte que 32 767 paramètres liés par instruction. Une insertion
multi-lignes en consomme `nombre_de_lignes × nombre_de_colonnes` : le plafond
est donc atteint d'autant plus vite que la table est large, et il l'est pour de
bon sur ce projet — 4 000 itinéraires ou un itinéraire de 1 700 clients
suffisent. La taille de lot est calculée à partir du nombre de colonnes plutôt
que fixée en dur, pour qu'ajouter une colonne ne réintroduise pas la panne.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TypeVar

T = TypeVar("T")

#: Limite du protocole PostgreSQL sur les paramètres d'une instruction.
LIMITE_PARAMETRES = 32_767

#: Marge de sécurité : une clause `ON CONFLICT DO UPDATE` peut ajouter ses
#: propres paramètres au-delà des colonnes insérées.
MARGE = 0.9

#: Plafond de confort, indépendant de la limite technique : au-delà, le gain
#: d'un aller-retour de moins ne compense plus la mémoire mobilisée.
PLAFOND_LIGNES = 2_000


def taille_lot(nombre_de_colonnes: int, plafond: int = PLAFOND_LIGNES) -> int:
    """Nombre de lignes insérables en une seule instruction."""
    if nombre_de_colonnes <= 0:
        return plafond
    tenable = int(LIMITE_PARAMETRES * MARGE) // nombre_de_colonnes
    return max(1, min(plafond, tenable))


def par_lots(
    valeurs: Sequence[T], nombre_de_colonnes: int, plafond: int = PLAFOND_LIGNES
) -> Iterator[Sequence[T]]:
    """Découpe une séquence en tranches insérables d'un seul tenant."""
    pas = taille_lot(nombre_de_colonnes, plafond)
    for debut in range(0, len(valeurs), pas):
        yield valeurs[debut : debut + pas]
