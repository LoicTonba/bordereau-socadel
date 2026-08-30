"""Cas d'usage : connexion du superviseur au back-office."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ....domain.enums import Role
from ...errors import IdentifiantsInvalides
from ...ports import ContenuJeton, HacheurMotDePasse, Horloge, ServiceJeton, UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeConnexion:
    identifiant: str
    mot_de_passe: str


@dataclass(frozen=True, slots=True)
class SessionOuverte:
    """Résultat d'une authentification réussie."""

    jeton: str
    expire_dans_secondes: int
    identifiant: str
    nom_complet: str
    role: Role


class ConnecterSuperviseur:
    """Authentifie un utilisateur et lui délivre un jeton de session."""

    def __init__(
        self,
        uow: UnitOfWork,
        hacheur: HacheurMotDePasse,
        jetons: ServiceJeton,
        horloge: Horloge,
        duree_session: timedelta,
    ) -> None:
        self._uow = uow
        self._hacheur = hacheur
        self._jetons = jetons
        self._horloge = horloge
        self._duree_session = duree_session

    async def executer(self, commande: CommandeConnexion) -> SessionOuverte:
        """Vérifie les identifiants et ouvre une session.

        Raises:
            IdentifiantsInvalides: compte inconnu, désactivé ou mot de passe
                incorrect — les trois cas sont indistinguables de l'extérieur.
        """
        async with self._uow as uow:
            utilisateur = await uow.utilisateurs.par_identifiant(
                commande.identifiant.strip().lower()
            )

            # Le hachage est calculé même quand le compte est inconnu : sans
            # cela, le temps de réponse révélerait l'existence du compte.
            empreinte = (
                utilisateur.empreinte_mot_de_passe
                if utilisateur is not None
                else self._hacheur.hacher("mot-de-passe-factice")
            )
            mot_de_passe_correct = self._hacheur.verifier(
                commande.mot_de_passe, empreinte
            )

            if (
                utilisateur is None
                or not mot_de_passe_correct
                or not utilisateur.peut_se_connecter()
            ):
                raise IdentifiantsInvalides()

            maintenant = self._horloge.maintenant()
            utilisateur.enregistrer_connexion(maintenant)
            await uow.utilisateurs.enregistrer(utilisateur)
            await uow.valider()

        expiration = maintenant + self._duree_session
        jeton = self._jetons.emettre(
            ContenuJeton(
                utilisateur_id=utilisateur.id,
                identifiant=utilisateur.identifiant,
                role=utilisateur.role,
                expire_le=expiration,
            )
        )

        return SessionOuverte(
            jeton=jeton,
            expire_dans_secondes=int(self._duree_session.total_seconds()),
            identifiant=utilisateur.identifiant,
            nom_complet=utilisateur.nom_complet,
            role=utilisateur.role,
        )
