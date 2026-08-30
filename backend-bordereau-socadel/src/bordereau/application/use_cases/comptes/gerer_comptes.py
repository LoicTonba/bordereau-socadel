"""Cas d'usage de consultation et de suspension des comptes.

L'ouverture d'un compte passe par `inscription.py`, les mots de passe par
`mots_de_passe.py`. Ce module ne garde que ce qui relève de l'exploitation
courante : lister, modifier un profil, suspendre, réactiver.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from ....domain.entities import Utilisateur
from ....domain.enums import Role, StatutCompte
from ....domain.securite import (
    ContexteAcces,
    Permission,
    dans_le_perimetre,
    peut_agir_sur_compte,
    peut_agir_sur_role,
)
from ....domain.securite.permissions import AccesRefuse
from ...errors import ConflitRessource, RessourceIntrouvable
from ...ports import UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeModificationCompte:
    compte_id: UUID
    nom_complet: str | None = None
    email: str | None = None
    telephone: str | None = None
    photo_url: str | None = None
    region: str | None = None
    agence: str | None = None
    role: Role | None = None


class ListerComptes:
    """Annuaire des comptes, restreint au périmètre de l'appelant."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, *, statut: StatutCompte | None = None
    ) -> Sequence[Utilisateur]:
        contexte.exiger(Permission.COMPTE_LIRE)

        async with self._uow as uow:
            comptes = await uow.utilisateurs.lister(
                statut=statut.value if statut else None
            )

        # On ne montre que les comptes sur lesquels on pourrait agir, plus le
        # sien : afficher un compte qu'on ne peut pas toucher n'apporte rien
        # et renseigne sur la hiérarchie au-dessus de soi.
        return [
            compte
            for compte in comptes
            if compte.id == contexte.utilisateur_id
            or (
                peut_agir_sur_role(contexte, compte.role)
                and dans_le_perimetre(contexte, compte.region, compte.agence)
            )
        ]


class ModifierCompte:
    """Met à jour un profil."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeModificationCompte
    ) -> Utilisateur:
        est_le_sien = commande.compte_id == contexte.utilisateur_id
        contexte.exiger(
            Permission.PROFIL_MODIFIER if est_le_sien else Permission.COMPTE_MODIFIER
        )

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(commande.compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", commande.compte_id)

            if not peut_agir_sur_compte(contexte, compte.id, compte.role):
                raise AccesRefuse("Vous ne pouvez pas modifier ce compte")

            if commande.nom_complet is not None:
                compte.nom_complet = commande.nom_complet
            if commande.email is not None:
                compte.email = commande.email.strip().lower()
            if commande.telephone is not None:
                compte.telephone = commande.telephone
            if commande.photo_url is not None:
                compte.photo_url = commande.photo_url

            # Le périmètre et le rôle sont des prérogatives de responsable :
            # se les attribuer soi-même reviendrait à élargir sa propre portée.
            if not est_le_sien and contexte.a(Permission.PERIMETRE_DEFINIR):
                if commande.region is not None:
                    compte.region = commande.region
                if commande.agence is not None:
                    compte.agence = commande.agence

            if commande.role is not None:
                contexte.exiger(Permission.COMPTE_CHANGER_ROLE)
                if not peut_agir_sur_role(contexte, commande.role):
                    raise AccesRefuse(
                        f"Votre rôle ne permet pas d'attribuer "
                        f"{commande.role.value}"
                    )
                compte.role = commande.role

            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        return compte


class BasculerActivationCompte:
    """Suspend un compte, ou le remet en service."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, compte_id: UUID, *, actif: bool
    ) -> Utilisateur:
        contexte.exiger(Permission.COMPTE_SUPPRIMER)

        if compte_id == contexte.utilisateur_id and not actif:
            # Se suspendre soi-même verrouillerait l'accès à la plateforme.
            raise ConflitRessource("Vous ne pouvez pas suspendre votre propre compte")

        async with self._uow as uow:
            compte = await uow.utilisateurs.par_id(compte_id)
            if compte is None:
                raise RessourceIntrouvable("Compte", compte_id)

            if not peut_agir_sur_role(contexte, compte.role):
                raise AccesRefuse("Vous ne pouvez pas agir sur ce compte")

            compte.reactiver() if actif else compte.suspendre()
            await uow.utilisateurs.enregistrer(compte)
            await uow.valider()

        return compte
