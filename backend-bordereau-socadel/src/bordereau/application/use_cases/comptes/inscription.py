"""Cas d'usage de l'inscription et du cycle de vie d'un compte.

Le parcours retenu est celui des applications professionnelles, pas celui d'un
service grand public : **s'inscrire ne donne pas accès**. La plateforme porte
le référentiel clients de SOCADEL, plusieurs centaines de milliers de noms et
de numéros ; un accès ne s'obtient pas en remplissant un formulaire.

    1. l'utilisateur s'inscrit et choisit son mot de passe ;
    2. il confirme son adresse par le lien reçu ;
    3. un responsable lui attribue un rôle et un périmètre ;
    4. il est prévenu par courriel et peut se connecter.

Chaque étape est vérifiable et laisse une trace : qui a approuvé, quand.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ....domain.entities import Utilisateur
from ....domain.enums import Role, StatutCompte
from ....domain.securite import (
    ContexteAcces,
    Permission,
    mot_de_passe as politique,
    peut_agir_sur_role,
)
from ....domain.securite.permissions import AccesRefuse
from ... import courriels
from ...errors import ConflitRessource, RessourceIntrouvable
from ...ports import (
    GenerateurJeton,
    HacheurMotDePasse,
    Horloge,
    Messagerie,
    UnitOfWork,
)


@dataclass(frozen=True, slots=True)
class CommandeInscription:
    identifiant: str
    nom_complet: str
    email: str
    mot_de_passe: str
    confirmation: str
    telephone: str | None = None
    role_souhaite: Role | None = None
    """Simple indication pour le responsable qui approuvera. Elle n'est jamais
    appliquée telle quelle : c'est l'approbateur qui décide."""


@dataclass(frozen=True, slots=True)
class CommandeApprobation:
    compte_id: UUID
    role: Role
    region: str | None = None
    agence: str | None = None
    agent_id: UUID | None = None


class InscrireUtilisateur:
    """Enregistre une demande d'accès et envoie le lien de confirmation."""

    def __init__(
        self,
        uow: UnitOfWork,
        hacheur: HacheurMotDePasse,
        jetons: GenerateurJeton,
        messagerie: Messagerie,
        horloge: Horloge,
        url_publique: str,
    ) -> None:
        self._uow = uow
        self._hacheur = hacheur
        self._jetons = jetons
        self._messagerie = messagerie
        self._horloge = horloge
        self._url = url_publique.rstrip("/")

    async def executer(self, commande: CommandeInscription) -> Utilisateur:
        """Crée le compte en attente de vérification.

        Raises:
            ConflitRessource: identifiant ou adresse déjà utilisés.
            RegleMetierViolee: mot de passe trop faible, ou saisies
                divergentes, ou adresse mal formée.
        """
        politique.exiger_confirmation(commande.mot_de_passe, commande.confirmation)
        politique.exiger_valide(
            commande.mot_de_passe,
            identifiant=commande.identifiant,
            email=commande.email,
        )

        identifiant = commande.identifiant.strip().lower()
        email = commande.email.strip().lower()
        maintenant = self._horloge.maintenant()

        async with self._uow as uow:
            if await uow.utilisateurs.par_identifiant(identifiant) is not None:
                raise ConflitRessource(f"L'identifiant {identifiant} est déjà pris")
            if await uow.utilisateurs.par_email(email) is not None:
                raise ConflitRessource(
                    "Une demande existe déjà pour cette adresse électronique"
                )

            compte = Utilisateur(
                identifiant=identifiant,
                nom_complet=commande.nom_complet.strip(),
                email=email,
                empreinte_mot_de_passe=self._hacheur.hacher(commande.mot_de_passe),
                telephone=commande.telephone,
                # Le rôle réel est fixé à l'approbation. Le champ porte ici
                # une valeur d'attente sans effet : tant que le statut n'est
                # pas ACTIF, aucune permission n'est accordée.
                role=Role.SUPERVISEUR,
                statut=StatutCompte.EN_ATTENTE_VERIFICATION,
                cree_le=maintenant,
            )
            jeton = self._jetons.nouveau()
            compte.emettre_jeton_verification(jeton, maintenant)

            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        self._messagerie.envoyer(
            courriels.verification_adresse(
                compte, f"{self._url}/verification?jeton={jeton}"
            )
        )
        return compte


class VerifierAdresse:
    """Confirme l'adresse par le lien reçu, et met la demande en approbation."""

    def __init__(
        self, uow: UnitOfWork, messagerie: Messagerie, horloge: Horloge
    ) -> None:
        self._uow = uow
        self._messagerie = messagerie
        self._horloge = horloge

    async def executer(self, jeton: str) -> Utilisateur:
        """Raises:
        RessourceIntrouvable: aucun compte ne porte ce jeton.
        RegleMetierViolee: jeton périmé.
        """
        async with self._uow as uow:
            compte = await uow.utilisateurs.par_jeton_verification(jeton)
            if compte is None:
                raise RessourceIntrouvable("Lien de confirmation", jeton[:8])

            compte.verifier_adresse(jeton, self._horloge.maintenant())
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        return compte


class ApprouverCompte:
    """Attribue rôle et périmètre, puis ouvre l'accès."""

    def __init__(
        self,
        uow: UnitOfWork,
        messagerie: Messagerie,
        horloge: Horloge,
        url_publique: str,
    ) -> None:
        self._uow = uow
        self._messagerie = messagerie
        self._horloge = horloge
        self._url = url_publique.rstrip("/")

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeApprobation
    ) -> Utilisateur:
        """Raises:
        AccesRefuse: le rôle demandé n'est pas atteignable par l'approbateur.
        RessourceIntrouvable: compte inconnu.
        RegleMetierViolee: rôle incompatible avec le périmètre fourni.
        """
        contexte.exiger(Permission.COMPTE_APPROUVER)

        # On ne crée jamais son égal ni son supérieur : un administrateur
        # SOCADEL ne peut pas se doter d'un second administrateur, encore
        # moins d'un super utilisateur.
        if not peut_agir_sur_role(contexte, commande.role):
            raise AccesRefuse(
                f"Votre rôle ne permet pas d'attribuer le rôle "
                f"{commande.role.value}"
            )

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(commande.compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", commande.compte_id)

            compte.approuver(
                role=commande.role,
                approbateur_id=contexte.utilisateur_id,
                horodatage=self._horloge.maintenant(),
                region=commande.region,
                agence=commande.agence,
                agent_id=commande.agent_id,
            )
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        self._messagerie.envoyer(
            courriels.acces_ouvert(compte, f"{self._url}/login")
        )
        return compte


class RefuserCompte:
    """Écarte une demande d'accès."""

    def __init__(self, uow: UnitOfWork, messagerie: Messagerie) -> None:
        self._uow = uow
        self._messagerie = messagerie

    async def executer(
        self, contexte: ContexteAcces, compte_id: UUID, motif: str | None = None
    ) -> Utilisateur:
        contexte.exiger(Permission.COMPTE_APPROUVER)

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", compte_id)
            if not peut_agir_sur_role(contexte, compte.role):
                raise AccesRefuse("Vous ne pouvez pas agir sur ce compte")

            compte.refuser()
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        self._messagerie.envoyer(courriels.demande_refusee(compte, motif))
        return compte
