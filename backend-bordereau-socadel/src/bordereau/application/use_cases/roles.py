"""Cas d'usage : lire les rôles, et restreindre ce qu'ils portent.

Un mot sur ce que ce module fait, et surtout sur ce qu'il ne fait pas.

Il ne permet pas de **créer** un rôle, ni d'en **ajouter** une permission. Les
quatre rôles et la matrice qui leur donne leurs droits sont écrits dans le
code, où ils sont relus, testés et versionnés. Les rendre modifiables en base
reviendrait à déplacer la sécurité de la plateforme dans une table que quelques
clics suffisent à changer, et à faire de chaque sauvegarde restaurée une
question de sécurité.

Il permet en revanche de **retrancher**. NEXT LTD peut retirer une permission à
un rôle, par exemple fermer l'export à tous les superviseurs le temps d'une
campagne. La matrice du code reste le plafond : aucune écriture en base
n'ouvre un droit, elle ne peut que le fermer. L'escalade de privilèges par la
donnée est ainsi impossible par construction, pas par vigilance.

Deux garde-fous s'ajoutent. Le super utilisateur ne se restreint pas lui-même,
sans quoi une fausse manœuvre fermerait la porte à tout le monde sans moyen de
la rouvrir. Et lui seul décide : l'administrateur SOCADEL exploite la
plateforme, il n'en redéfinit pas les règles.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.enums import Role
from ...domain.securite import ContexteAcces, Permission
from ...domain.securite.permissions import MATRICE, RANG, AccesRefuse
from ..errors import ConflitRessource
from ..ports import UnitOfWork


@dataclass(frozen=True, slots=True)
class DroitDeRole:
    """Une permission, et l'état dans lequel elle se trouve pour un rôle."""

    permission: str
    #: Vraie si la matrice du code la donne à ce rôle.
    accordee_par_le_code: bool
    #: Vraie si le super utilisateur l'a retranchée.
    restreinte: bool

    @property
    def effective(self) -> bool:
        return self.accordee_par_le_code and not self.restreinte


@dataclass(frozen=True, slots=True)
class VueRole:
    """Un rôle, son rang, et le détail de ses droits."""

    role: str
    rang: int
    droits: tuple[DroitDeRole, ...]

    @property
    def nombre_effectif(self) -> int:
        return sum(1 for d in self.droits if d.effective)


class ConsulterRoles:
    """La matrice complète, telle qu'elle s'applique aujourd'hui."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, contexte: ContexteAcces) -> tuple[VueRole, ...]:
        contexte.exiger(Permission.ROLE_LIRE)

        async with self._uow as uow:
            restrictions = await uow.restrictions.lister()

        return tuple(
            VueRole(
                role=role.value,
                rang=RANG.get(role, 0),
                droits=tuple(
                    DroitDeRole(
                        permission=permission.value,
                        accordee_par_le_code=permission in MATRICE.get(role, frozenset()),
                        restreinte=permission.value
                        in restrictions.get(role.value, set()),
                    )
                    for permission in Permission
                ),
            )
            # Du plus large au plus restreint : c'est l'ordre dans lequel on
            # lit une hiérarchie.
            for role in sorted(Role, key=lambda r: -RANG.get(r, 0))
        )

    async def pour(self, contexte: ContexteAcces, role: Role) -> VueRole:
        """La vue d'un seul rôle."""
        vues = await self.executer(contexte)
        return next(v for v in vues if v.role == role.value)


class RestreindreRole:
    """Retranche des permissions à un rôle. Ne peut jamais en ajouter."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, role_cible: Role, restrictions: set[str]
    ) -> VueRole:
        contexte.exiger(Permission.ROLE_RESTREINDRE)

        if role_cible is Role.SUPER_UTILISATEUR:
            raise ConflitRessource(
                "Le rôle super utilisateur ne se restreint pas : une fausse "
                "manœuvre fermerait la plateforme à tout le monde, sans moyen "
                "de la rouvrir."
            )

        if not contexte.rang > RANG.get(role_cible, 0):
            raise AccesRefuse(
                "Vous ne pouvez restreindre que les rôles de rang strictement "
                "inférieur au vôtre."
            )

        connues = {p.value for p in Permission}
        inconnues = restrictions - connues
        if inconnues:
            raise ConflitRessource(
                "Permissions inconnues : " + ", ".join(sorted(inconnues))
            )

        async with self._uow as uow:
            await uow.restrictions.definir(role_cible.value, restrictions)
            await uow.valider()

        return await ConsulterRoles(self._uow).pour(contexte, role_cible)
