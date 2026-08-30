"""Cas d'usage : ouverture de session, quel que soit le profil.

La connexion se fait en trois temps du point de vue de l'utilisateur : il
désigne son profil, puis l'agence où il se trouve, et seulement ensuite il
saisit ses identifiants. Ces deux premiers choix sont des **déclarations**.

Elles ne donnent aucun droit. Le rôle effectif et le périmètre restent ceux du
compte, et c'est toujours l'ABAC côté serveur qui rétrécit les requêtes. La
déclaration ne sert qu'à deux choses : présélectionner l'écran d'arrivée, et
détecter une incohérence tôt, quand un superviseur de Kribi ouvre par erreur
la session d'une autre agence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ....domain.enums import Role
from ...errors import IdentifiantsInvalides, PosteDeTravailIncoherent
from ...ports import ContenuJeton, HacheurMotDePasse, Horloge, ServiceJeton, UnitOfWork

#: Libellés des rôles, pour des messages d'erreur lisibles par un non-technicien.
LIBELLE_ROLE: dict[Role, str] = {
    Role.SUPER_UTILISATEUR: "super utilisateur",
    Role.ADMINISTRATEUR: "administrateur",
    Role.SUPERVISEUR: "superviseur",
    Role.AGENT_TERRAIN: "agent de terrain",
}


@dataclass(frozen=True, slots=True)
class CommandeConnexion:
    identifiant: str
    mot_de_passe: str

    role_declare: Role | None = None
    """Profil choisi au premier écran. Vérifié, jamais cru."""

    agence_declaree: str | None = None
    """Agence où l'utilisateur se trouve. Présélectionne, n'autorise rien."""


@dataclass(frozen=True, slots=True)
class SessionOuverte:
    """Résultat d'une authentification réussie."""

    jeton: str
    expire_dans_secondes: int
    identifiant: str
    nom_complet: str
    role: Role
    agence: str | None = None
    """Agence de travail retenue pour la session, à des fins d'affichage."""

    region: str | None = None


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
                incorrect, les trois cas sont indistinguables de l'extérieur.
            PosteDeTravailIncoherent: le mot de passe est bon, mais le profil
                ou l'agence déclarés ne correspondent pas au compte.
        """
        async with self._uow as uow:
            utilisateur = await _retrouver(uow, commande.identifiant)

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

            # Le mot de passe est validé : le titulaire a prouvé qu'il possède
            # le compte. Les messages qui suivent peuvent donc être explicites
            # sans renseigner un attaquant.
            _verifier_profil(utilisateur.role, commande.role_declare)
            agence = _agence_de_travail(
                compte_agence=utilisateur.agence,
                declaree=commande.agence_declaree,
            )

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
            agence=agence,
            region=utilisateur.region,
        )


async def _retrouver(uow: UnitOfWork, saisie: str):
    """Retrouve le compte à partir de son adresse ou de son identifiant.

    L'écran de connexion demande l'adresse électronique : c'est ce dont
    l'utilisateur se souvient, et c'est déjà ce qu'il donne à l'inscription.
    L'identifiant reste accepté pour ne pas casser les comptes de mise en route
    ni les scripts d'intégration. Le « @ » suffit à distinguer les deux, une
    adresse en étant toujours porteuse et un identifiant jamais.
    """
    saisie = saisie.strip().lower()
    if "@" in saisie:
        return await uow.utilisateurs.par_email(saisie)
    return await uow.utilisateurs.par_identifiant(saisie)


def _verifier_profil(effectif: Role, declare: Role | None) -> None:
    """Refuse une session ouverte sous un profil qui n'est pas celui du compte.

    Le contrôle est de confort, pas de sécurité : même sans lui, le jeton
    porterait le rôle réel et l'API refuserait tout ce qui le dépasse. Il évite
    surtout la confusion d'un agent qui se croit connecté en superviseur et ne
    comprend pas pourquoi son écran est vide.
    """
    if declare is None or declare is effectif:
        return
    raise PosteDeTravailIncoherent(
        f"Ce compte est enregistré comme {LIBELLE_ROLE[effectif]}, "
        f"pas comme {LIBELLE_ROLE[declare]}. Choisissez le bon profil."
    )


def _agence_de_travail(*, compte_agence: str | None, declaree: str | None) -> str | None:
    """Retient l'agence de la session, après contrôle de cohérence.

    Un compte rattaché à une agence ne peut pas ouvrir sa session ailleurs :
    c'est le signe d'une erreur de saisie, ou d'un compte utilisé par quelqu'un
    d'autre. Un compte sans rattachement, un administrateur par exemple, peut
    déclarer l'agence où il se trouve : cela ne fait que cadrer son écran
    d'accueil, son périmètre reste national.
    """
    if declaree is None or not declaree.strip():
        return compte_agence

    declaree = declaree.strip()
    if compte_agence and declaree != compte_agence:
        raise PosteDeTravailIncoherent(
            f"Ce compte est rattaché à l'agence {compte_agence}, "
            f"pas à {declaree}."
        )
    return declaree
