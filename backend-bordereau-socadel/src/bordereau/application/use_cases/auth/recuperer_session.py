"""Cas d'usage : résolution de l'utilisateur courant à partir de son jeton."""

from __future__ import annotations

from ....domain.entities import Utilisateur
from ...errors import JetonInvalide
from ...ports import Horloge, ServiceJeton, UnitOfWork


class RecupererSession:
    """Transforme un jeton en utilisateur, pour les dépendances des routes."""

    def __init__(
        self, uow: UnitOfWork, jetons: ServiceJeton, horloge: Horloge
    ) -> None:
        self._uow = uow
        self._jetons = jetons
        self._horloge = horloge

    async def executer(self, jeton: str) -> Utilisateur:
        """Valide le jeton et recharge le compte associé.

        Le compte est rechargé à chaque requête plutôt que reconstruit depuis
        le jeton : une désactivation prend ainsi effet immédiatement, sans
        attendre l'expiration.

        Raises:
            JetonInvalide: jeton illisible, expiré, ou compte désormais absent
                ou désactivé.
        """
        contenu = self._jetons.decoder(jeton)

        if contenu.expire_le <= self._horloge.maintenant():
            raise JetonInvalide("Session expirée, merci de vous reconnecter")

        async with self._uow as uow:
            utilisateur = await uow.utilisateurs.par_id(contenu.utilisateur_id)

        if utilisateur is None or not utilisateur.peut_se_connecter():
            raise JetonInvalide("Ce compte n'est plus autorisé à se connecter")

        return utilisateur
