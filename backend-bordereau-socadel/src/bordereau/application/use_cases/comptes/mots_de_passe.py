"""Cas d'usage de gestion des mots de passe.

Trois chemins, pour trois situations réelles :

* le titulaire **change** son mot de passe en connaissant l'ancien ;
* il l'a **oublié** et demande un lien par courriel ;
* un responsable le **réinitialise** pour lui, parce qu'il n'a plus accès à sa
  boîte ou qu'il faut débloquer la situation tout de suite. La hiérarchie
  s'applique : chacun ne réinitialise que les rangs inférieurs au sien.
"""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from uuid import UUID

from ....domain.securite import (
    ContexteAcces,
    Permission,
    mot_de_passe as politique,
    peut_agir_sur_role,
)
from ....domain.securite.permissions import AccesRefuse
from ...errors import IdentifiantsInvalides, RessourceIntrouvable
from ...ports import (
    Courriel,
    GenerateurJeton,
    HacheurMotDePasse,
    Horloge,
    Messagerie,
    UnitOfWork,
)

#: Longueur du mot de passe provisoire généré lors d'une réinitialisation par
#: un responsable. Généreuse : il transite de vive voix ou par courriel.
LONGUEUR_PROVISOIRE = 14


@dataclass(frozen=True, slots=True)
class CommandeChangement:
    compte_id: UUID
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str
    confirmation: str


@dataclass(frozen=True, slots=True)
class CommandeReinitialisationParJeton:
    jeton: str
    nouveau_mot_de_passe: str
    confirmation: str


@dataclass(frozen=True, slots=True)
class MotDePasseProvisoire:
    """Ce qu'un responsable communique au titulaire après réinitialisation."""

    identifiant: str
    nom_complet: str
    mot_de_passe: str


class ChangerMotDePasse:
    """Le titulaire change le sien, en prouvant qu'il connaît l'ancien."""

    def __init__(self, uow: UnitOfWork, hacheur: HacheurMotDePasse) -> None:
        self._uow = uow
        self._hacheur = hacheur

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeChangement
    ) -> None:
        """Raises:
        AccesRefuse: tentative sur le compte d'un autre.
        IdentifiantsInvalides: ancien mot de passe incorrect.
        RegleMetierViolee: nouveau mot de passe trop faible ou mal confirmé.
        """
        if commande.compte_id != contexte.utilisateur_id:
            raise AccesRefuse(
                "Un mot de passe ne se change que sur son propre compte"
            )

        politique.exiger_confirmation(
            commande.nouveau_mot_de_passe, commande.confirmation
        )

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(commande.compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", commande.compte_id)

            if not self._hacheur.verifier(
                commande.ancien_mot_de_passe, compte.empreinte_mot_de_passe
            ):
                raise IdentifiantsInvalides()

            politique.exiger_valide(
                commande.nouveau_mot_de_passe,
                identifiant=compte.identifiant,
                email=compte.email,
            )
            compte.changer_mot_de_passe(
                self._hacheur.hacher(commande.nouveau_mot_de_passe)
            )
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()


class DemanderReinitialisation:
    """Envoie un lien de réinitialisation à l'adresse du compte."""

    def __init__(
        self,
        uow: UnitOfWork,
        jetons: GenerateurJeton,
        messagerie: Messagerie,
        horloge: Horloge,
        url_publique: str,
    ) -> None:
        self._uow = uow
        self._jetons = jetons
        self._messagerie = messagerie
        self._horloge = horloge
        self._url = url_publique.rstrip("/")

    async def executer(self, email: str) -> None:
        """Ne dit jamais si l'adresse existe.

        Répondre « adresse inconnue » offrirait à un tiers un moyen simple de
        savoir qui possède un compte. Le cas d'usage se termine donc
        silencieusement lorsque l'adresse n'est pas connue, et l'appelant
        renvoie toujours la même réponse.
        """
        adresse = email.strip().lower()
        maintenant = self._horloge.maintenant()

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_email(adresse)
            if compte is None or not compte.actif:
                return

            jeton = self._jetons.nouveau()
            compte.emettre_jeton_reinitialisation(jeton, maintenant)
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        self._messagerie.envoyer(
            Courriel(
                destinataire=compte.email,
                sujet="Réinitialisation de votre mot de passe, Bordereau SOCADEL",
                corps_texte=(
                    f"Bonjour {compte.nom_complet},\n\n"
                    "Une réinitialisation de mot de passe a été demandée pour "
                    f"le compte « {compte.identifiant} ».\n\n"
                    "Choisissez un nouveau mot de passe en ouvrant ce lien :\n"
                    f"{self._url}/reinitialisation?jeton={jeton}\n\n"
                    "Le lien est valable deux heures et ne fonctionne qu'une "
                    "fois.\n\n"
                    "Si vous n'êtes pas à l'origine de cette demande, ignorez "
                    "ce message : votre mot de passe actuel reste valable."
                    "\n\n---\n"
                    "Bordereau SOCADEL, solution NEXT LTD.\n"
                    "Ce message est automatique, merci de ne pas y répondre."
                ),
            )
        )


class ReinitialiserAvecJeton:
    """Applique le nouveau mot de passe choisi via le lien reçu."""

    def __init__(
        self, uow: UnitOfWork, hacheur: HacheurMotDePasse, horloge: Horloge
    ) -> None:
        self._uow = uow
        self._hacheur = hacheur
        self._horloge = horloge

    async def executer(self, commande: CommandeReinitialisationParJeton) -> None:
        """Raises:
        RessourceIntrouvable: aucun compte ne porte ce jeton.
        RegleMetierViolee: jeton périmé, ou mot de passe non conforme.
        """
        politique.exiger_confirmation(
            commande.nouveau_mot_de_passe, commande.confirmation
        )

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_jeton_reinitialisation(
                commande.jeton
            )
            if compte is None:
                raise RessourceIntrouvable("Lien de réinitialisation", "…")

            politique.exiger_valide(
                commande.nouveau_mot_de_passe,
                identifiant=compte.identifiant,
                email=compte.email,
            )
            compte.reinitialiser_avec_jeton(
                commande.jeton,
                self._hacheur.hacher(commande.nouveau_mot_de_passe),
                self._horloge.maintenant(),
            )
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()


class ReinitialiserParResponsable:
    """Un responsable remet un mot de passe provisoire à un subordonné."""

    def __init__(
        self, uow: UnitOfWork, hacheur: HacheurMotDePasse, messagerie: Messagerie
    ) -> None:
        self._uow = uow
        self._hacheur = hacheur
        self._messagerie = messagerie

    async def executer(
        self, contexte: ContexteAcces, compte_id: UUID
    ) -> MotDePasseProvisoire:
        """Génère un mot de passe provisoire, à changer à la prochaine connexion.

        Raises:
            AccesRefuse: le compte visé n'est pas d'un rang inférieur.
            RessourceIntrouvable: compte inconnu.
        """
        contexte.exiger(Permission.COMPTE_REINITIALISER)

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", compte_id)

            if not peut_agir_sur_role(contexte, compte.role):
                raise AccesRefuse(
                    "Votre rôle ne permet pas de réinitialiser ce compte"
                )

            provisoire = _mot_de_passe_provisoire()
            compte.imposer_mot_de_passe(self._hacheur.hacher(provisoire))
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        self._messagerie.envoyer(
            Courriel(
                destinataire=compte.email,
                sujet="Votre mot de passe a été réinitialisé, Bordereau SOCADEL",
                corps_texte=(
                    f"Bonjour {compte.nom_complet},\n\n"
                    "Un responsable a réinitialisé votre mot de passe. Un mot "
                    "de passe provisoire vous a été remis, et vous devrez le "
                    "remplacer dès votre prochaine connexion.\n\n"
                    "Si vous n'avez rien demandé, prévenez immédiatement votre "
                    "administrateur."
                    "\n\n---\n"
                    "Bordereau SOCADEL, solution NEXT LTD.\n"
                    "Ce message est automatique, merci de ne pas y répondre."
                ),
            )
        )

        # Le mot de passe est renvoyé à l'appelant, jamais écrit dans le
        # courriel : le responsable le communique de vive voix.
        return MotDePasseProvisoire(
            identifiant=compte.identifiant,
            nom_complet=compte.nom_complet,
            mot_de_passe=provisoire,
        )


def _mot_de_passe_provisoire() -> str:
    """Chaîne aléatoire lisible, sans caractères qu'on confond à l'oral.

    Les I, l, O et 0 sont écartés : ce mot de passe se dicte au téléphone.
    """
    alphabet = (
        "".join(c for c in string.ascii_letters if c not in "IlO")
        + "".join(c for c in string.digits if c not in "01")
        + "!@#$%"
    )
    return "".join(secrets.choice(alphabet) for _ in range(LONGUEUR_PROVISOIRE))
