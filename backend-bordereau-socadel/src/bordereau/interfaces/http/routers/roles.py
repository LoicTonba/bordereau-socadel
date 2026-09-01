"""Routes des rôles : lire la matrice, et retrancher ce qu'un rôle porte.

On ne crée pas de rôle ici, et on n'ajoute aucune permission. Les quatre rôles
et leur matrice sont écrits dans le code, où ils sont relus, testés et
versionnés ; la base ne peut que **retrancher**. Voir le cas d'usage pour le
raisonnement complet.
"""

from __future__ import annotations

from fastapi import APIRouter

from ....domain.enums import Role
from ..deps import ContainerDep, ContexteDep
from ..schemas.bordereau import RequeteRestriction, VueRoleSortie

router = APIRouter(prefix="/roles", tags=["Rôles"])


@router.get("", response_model=list[VueRoleSortie], summary="Lire la matrice")
async def lire(
    container: ContainerDep, contexte: ContexteDep
) -> list[VueRoleSortie]:
    """Les quatre rôles, leur rang, et le détail de leurs droits.

    Chaque droit indique s'il est accordé par le code et s'il a été retranché :
    c'est ce qui rend un refus compréhensible sans lire le code source.
    """
    vues = await container.consulter_roles().executer(contexte)
    return [VueRoleSortie.depuis_vue(v) for v in vues]


@router.put(
    "/{role}/restrictions",
    response_model=VueRoleSortie,
    summary="Retrancher des permissions à un rôle",
)
async def restreindre(
    role: Role,
    requete: RequeteRestriction,
    container: ContainerDep,
    contexte: ContexteDep,
) -> VueRoleSortie:
    """Remplace d'un bloc les restrictions du rôle.

    Ce qui n'est plus listé lui est rendu. Le rôle super utilisateur ne se
    restreint pas : une fausse manœuvre fermerait la plateforme à tout le
    monde, sans moyen de la rouvrir.
    """
    vue = await container.restreindre_role().executer(
        contexte, role, set(requete.restrictions)
    )
    return VueRoleSortie.depuis_vue(vue)
