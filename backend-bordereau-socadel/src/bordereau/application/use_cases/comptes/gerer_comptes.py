"""Cas d'usage des comptes de connexion.

Réservés à l'administrateur, à une exception près : chacun peut changer son
propre mot de passe.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from ....domain.entities import Utilisateur
from ....domain.enums import Role
from ....domain.securite import ContexteAcces, Permission, peut_agir_sur_compte
from ....domain.securite.permissions import AccesRefuse
from ...errors import ConflitRessource, IdentifiantsInvalides, RessourceIntrouvable
from ...ports import HacheurMotDePasse, UnitOfWork

#: Longueur minimale d'un mot de passe choisi par l'utilisateur.
LONGUEUR_MIN_MOT_DE_PASSE = 8


@dataclass(frozen=True, slots=True)
class CommandeCreationCompte:
    identifiant: str
    nom_complet: str
    mot_de_passe: str
    role: Role
    agent_id: UUID | None = None
    region: str | None = None
    agence: str | None = None
    email: str | None = None
    photo_url: str | None = None


@dataclass(frozen=True, slots=True)
class CommandeModificationCompte:
    compte_id: UUID
    nom_complet: str | None = None
    email: str | None = None
    photo_url: str | None = None
    region: str | None = None
    agence: str | None = None


@dataclass(frozen=True, slots=True)
class CommandeChangementMotDePasse:
    compte_id: UUID
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str


class ListerComptes:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, contexte: ContexteAcces) -> Sequence[Utilisateur]:
        contexte.exiger(Permission.COMPTE_LIRE)
        async with self._uow as uow:
            return await uow.utilisateurs.lister()


class CreerCompte:
    """Ouvre un compte de connexion.

    Un compte d'agent est créé avec un mot de passe initial que son titulaire
    devra remplacer : le superviseur le lui communique de vive voix, et le
    drapeau `doit_changer_mot_de_passe` force la reprise en main.
    """

    def __init__(self, uow: UnitOfWork, hacheur: HacheurMotDePasse) -> None:
        self._uow = uow
        self._hacheur = hacheur

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeCreationCompte
    ) -> Utilisateur:
        contexte.exiger(Permission.COMPTE_CREER)

        identifiant = commande.identifiant.strip().lower()
        if len(commande.mot_de_passe) < LONGUEUR_MIN_MOT_DE_PASSE:
            raise ConflitRessource(
                f"Le mot de passe doit faire au moins "
                f"{LONGUEUR_MIN_MOT_DE_PASSE} caractères"
            )

        async with self._uow as uow:
            if await uow.utilisateurs.par_identifiant(identifiant) is not None:
                raise ConflitRessource(f"L'identifiant {identifiant} est déjà pris")

            if commande.role is Role.AGENT_TERRAIN:
                if commande.agent_id is None:
                    raise ConflitRessource(
                        "Un compte agent doit désigner l'agent de terrain rattaché"
                    )
                if await uow.agents.par_id(commande.agent_id) is None:
                    raise RessourceIntrouvable(
                        "Agent de terrain", commande.agent_id
                    )

            compte = Utilisateur(
                identifiant=identifiant,
                nom_complet=commande.nom_complet,
                empreinte_mot_de_passe=self._hacheur.hacher(commande.mot_de_passe),
                role=commande.role,
                agent_id=commande.agent_id,
                region=commande.region,
                agence=commande.agence,
                email=commande.email,
                photo_url=commande.photo_url,
                doit_changer_mot_de_passe=True,
            )
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        return compte


class ModifierCompte:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeModificationCompte
    ) -> Utilisateur:
        # Modifier son propre profil ne demande pas la permission « comptes ».
        est_le_sien = commande.compte_id == contexte.utilisateur_id
        contexte.exiger(
            Permission.PROFIL_MODIFIER if est_le_sien else Permission.COMPTE_MODIFIER
        )
        if not peut_agir_sur_compte(contexte, commande.compte_id):
            raise AccesRefuse("Vous ne pouvez pas modifier ce compte")

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(commande.compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", commande.compte_id)

            if commande.nom_complet is not None:
                compte.nom_complet = commande.nom_complet
            if commande.email is not None:
                compte.email = commande.email
            if commande.photo_url is not None:
                compte.photo_url = commande.photo_url

            # Le périmètre territorial est une prérogative d'administrateur :
            # se l'attribuer soi-même reviendrait à élargir sa propre portée.
            if contexte.est_administrateur:
                if commande.region is not None:
                    compte.region = commande.region
                if commande.agence is not None:
                    compte.agence = commande.agence

            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        return compte


class BasculerActivationCompte:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, compte_id: UUID, *, actif: bool
    ) -> Utilisateur:
        contexte.exiger(Permission.COMPTE_SUPPRIMER)

        if compte_id == contexte.utilisateur_id and not actif:
            # Se désactiver soi-même verrouillerait l'accès à la plateforme.
            raise ConflitRessource("Vous ne pouvez pas désactiver votre propre compte")

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", compte_id)

            compte.actif = actif
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        return compte


class ChangerMotDePasse:
    """Chacun change le sien, en prouvant qu'il connaît l'ancien."""

    def __init__(self, uow: UnitOfWork, hacheur: HacheurMotDePasse) -> None:
        self._uow = uow
        self._hacheur = hacheur

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeChangementMotDePasse
    ) -> None:
        if commande.compte_id != contexte.utilisateur_id:
            raise AccesRefuse("Un mot de passe ne se change que sur son propre compte")

        if len(commande.nouveau_mot_de_passe) < LONGUEUR_MIN_MOT_DE_PASSE:
            raise ConflitRessource(
                f"Le mot de passe doit faire au moins "
                f"{LONGUEUR_MIN_MOT_DE_PASSE} caractères"
            )

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(commande.compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", commande.compte_id)

            if not self._hacheur.verifier(
                commande.ancien_mot_de_passe, compte.empreinte_mot_de_passe
            ):
                raise IdentifiantsInvalides()

            compte.changer_mot_de_passe(
                self._hacheur.hacher(commande.nouveau_mot_de_passe)
            )
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()
