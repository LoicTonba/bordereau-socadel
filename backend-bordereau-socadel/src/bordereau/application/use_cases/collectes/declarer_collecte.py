"""Cas d'usage : saisie par le superviseur du travail réalisé par un agent.

C'est le geste central de l'application — *« le but ici est au superviseur
d'entrer dans l'application ce que l'agent de terrain a fait »*.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ....domain.entities import LigneBordereau
from ....domain.enums import Responsable, StatutCollecte
from ....domain.securite import ContexteAcces, Permission
from ....domain.value_objects import NumeroTelephone
from ...errors import RessourceIntrouvable
from ...ports import Horloge, UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeDeclaration:
    ligne_id: UUID
    statut: StatutCollecte
    superviseur_id: UUID
    numero_collecte: str | None = None
    responsable: Responsable | None = None
    observation: str | None = None


@dataclass(frozen=True, slots=True)
class CommandeDeclarationEnLot:
    """Application d'un même statut à une sélection de lignes du tableau."""

    lignes_ids: tuple[UUID, ...]
    statut: StatutCollecte
    superviseur_id: UUID
    responsable: Responsable | None = None


class DeclarerCollecte:
    """Enregistre le statut d'une ligne de bordereau.

    La validation métier (un ABONNE exige un numéro) est portée par l'entité :
    ce cas d'usage se contente d'orchestrer chargement, décision et
    persistance.
    """

    def __init__(self, uow: UnitOfWork, horloge: Horloge) -> None:
        self._uow = uow
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeDeclaration
    ) -> LigneBordereau:
        """Applique la déclaration à une ligne.

        Raises:
            RessourceIntrouvable: la ligne visée n'existe pas.
            RegleMetierViolee: la déclaration viole une règle du domaine.
            ValidationError: le numéro collecté est inexploitable.
        """
        # Un agent de terrain ne saisit jamais lui-même : c'est le
        # superviseur qui reporte sa production.
        contexte.exiger(Permission.BORDEREAU_DECLARER)

        async with self._uow as uow:
            ligne = await uow.lignes.par_id(commande.ligne_id)
            if ligne is None:
                raise RessourceIntrouvable("Ligne de bordereau", commande.ligne_id)

            numero = (
                NumeroTelephone.parse(commande.numero_collecte)
                if commande.numero_collecte
                else None
            )

            ligne.declarer(
                commande.statut,
                horodatage=self._horloge.maintenant(),
                superviseur_id=commande.superviseur_id,
                numero_collecte=numero,
                responsable=commande.responsable,
                observation=commande.observation,
            )

            await uow.lignes.enregistrer(ligne)
            await uow.valider()

        return ligne

    async def executer_en_lot(
        self, contexte: ContexteAcces, commande: CommandeDeclarationEnLot
    ) -> int:
        """Applique un statut à plusieurs lignes en une seule transaction.

        Les lignes que le domaine refuse (un ABONNE sans numéro collecté, par
        exemple) sont ignorées plutôt que de faire échouer tout le lot : le
        superviseur voit alors combien de lignes ont réellement basculé.

        Returns:
            Le nombre de lignes effectivement modifiées.
        """
        from ....domain.errors import DomainError

        contexte.exiger(Permission.BORDEREAU_DECLARER)
        horodatage = self._horloge.maintenant()
        modifiees: list[LigneBordereau] = []

        async with self._uow as uow:
            for ligne_id in commande.lignes_ids:
                ligne = await uow.lignes.par_id(ligne_id)
                if ligne is None:
                    continue
                try:
                    ligne.declarer(
                        commande.statut,
                        horodatage=horodatage,
                        superviseur_id=commande.superviseur_id,
                        responsable=commande.responsable,
                    )
                except DomainError:
                    continue
                modifiees.append(ligne)

            if modifiees:
                await uow.lignes.enregistrer_en_lot(modifiees)
                await uow.valider()

        return len(modifiees)
