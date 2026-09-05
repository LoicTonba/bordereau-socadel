"""Cas d'usage : le geste du releveur, un clic sur la colonne Check.

C'est le seul geste qu'un agent de terrain pose, et il est volontairement
pauvre. Un releveur en tournée, debout, avec un téléphone à une main, ne
remplit pas un formulaire : il coche. Tout le reste, le back-office le
renseigne ensuite en confrontant la déclaration au référentiel.

Deux règles gouvernent ce geste, et les deux viennent de la réunion du
4 septembre avec SOCADEL.

**Un numéro ne se déclare qu'une fois par itinéraire.** Le DPSR craint le
contournement : un releveur payé à la ligne peut être tenté de porter son
propre numéro, ou celui d'un proche, sur plusieurs contrats voisins. Le
refus est net, et il nomme la ligne déjà servie pour que la correction soit
possible sans enquête.

**Le numéro reste attaché à son contrat.** Deux releveurs ne peuvent pas
renseigner le même contrat : la ligne appartient à une affectation, et
l'affectation à un agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ....domain.entities import LigneBordereau
from ....domain.enums import Identite, Rapport
from ....domain.securite import ContexteAcces, Permission, restreindre
from ....domain.securite.permissions import AccesRefuse
from ....domain.value_objects import NumeroTelephone
from ...dto import FiltreBordereau
from ...errors import ConflitRessource, RessourceIntrouvable
from ...ports import Horloge, UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeCoche:
    ligne_id: UUID
    rapport: Rapport = Rapport.OK
    numero_collecte: str | None = None
    identite: Identite | None = None


class CocherLigne:
    """Bascule une ligne à OK ou MRA, d'un seul geste."""

    def __init__(self, uow: UnitOfWork, horloge: Horloge) -> None:
        self._uow = uow
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeCoche
    ) -> LigneBordereau:
        contexte.exiger(Permission.BORDEREAU_COCHER)

        async with self._uow as uow:
            ligne = await uow.lignes.par_id(commande.ligne_id)
            if ligne is None:
                raise RessourceIntrouvable("Ligne de bordereau", commande.ligne_id)

            _exiger_dans_le_perimetre(contexte, ligne)

            numero = _numero(commande, ligne)
            if numero is not None:
                await _exiger_numero_unique_sur_itineraire(uow, ligne, numero)

            ligne.cocher(
                horodatage=self._horloge.maintenant(),
                agent_id=contexte.utilisateur_id,
                agent_nom=await _nom_de(uow, contexte),
                rapport=commande.rapport,
                numero_collecte=numero,
                identite=commande.identite,
            )
            await uow.lignes.enregistrer(ligne)
            await uow.valider()

        return ligne


class DecocherLigne:
    """Annule un coche posé par erreur. La ligne redevient à traiter."""

    def __init__(self, uow: UnitOfWork, horloge: Horloge) -> None:
        self._uow = uow
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, ligne_id: UUID
    ) -> LigneBordereau:
        contexte.exiger(Permission.BORDEREAU_COCHER)

        async with self._uow as uow:
            ligne = await uow.lignes.par_id(ligne_id)
            if ligne is None:
                raise RessourceIntrouvable("Ligne de bordereau", ligne_id)

            _exiger_dans_le_perimetre(contexte, ligne)

            ligne.decocher(horodatage=self._horloge.maintenant())
            await uow.lignes.enregistrer(ligne)
            await uow.valider()

        return ligne


# --- Gardes ----------------------------------------------------------------


def _exiger_dans_le_perimetre(contexte: ContexteAcces, ligne: LigneBordereau) -> None:
    """Un agent ne coche que ses propres lignes.

    Le rétrécissement ABAC protège la lecture ; l'écriture demande le même
    contrôle, ligne par ligne, sinon un agent pourrait cocher celles d'un
    collègue en visant leur identifiant.
    """
    if not contexte.est_agent:
        return
    if ligne.agent_id is None or ligne.agent_id != contexte.agent_id:
        raise AccesRefuse(
            "Cette ligne appartient à la tournée d'un autre agent."
        )


def _numero(commande: CommandeCoche, ligne: LigneBordereau) -> NumeroTelephone | None:
    if commande.numero_collecte:
        # L'agent tape ce qu'il lit sur le combine du client : 677 39 87 10,
        # pas +237677398710. La normalisation est notre travail, pas le sien.
        return NumeroTelephone.parse(commande.numero_collecte)
    return ligne.numero_collecte


async def _exiger_numero_unique_sur_itineraire(
    uow, ligne: LigneBordereau, numero: NumeroTelephone
) -> None:
    """Refuse un numéro déjà déclaré ailleurs sur la même tournée.

    Le même numéro sur deux contrats voisins est le contournement le plus
    simple qui soit : le releveur porte son propre numéro, la ligne passe en
    abonnée, et la prime tombe. Le refus nomme le contrat déjà servi, pour que
    la correction ne demande pas d'enquête.
    """
    if ligne.code_itineraire is None:
        return

    doublons = await uow.lignes.rechercher_par_numero(
        numero.valeur, code_itineraire=ligne.code_itineraire.valeur
    )
    # Seule une ligne effectivement cochée « sert » un contrat. Une ligne
    # décochée garde son numéro — il a bien été relevé — mais elle n'affirme
    # plus rien, et bloquer sur elle refuserait une correction légitime : le
    # releveur qui s'est trompé de contrat décoche l'un pour cocher l'autre.
    autres = [d for d in doublons if d.id != ligne.id and d.verifie_terrain]
    if not autres:
        return

    contrats = ", ".join(sorted({d.service_no.valeur for d in autres})[:3])
    raise ConflitRessource(
        f"Le numéro {numero.valeur} est déjà déclaré sur l'itinéraire "
        f"{ligne.code_itineraire.valeur}, au contrat {contrats}. "
        "Un même numéro ne peut servir deux contrats de la même tournée : "
        "vérifiez le relevé, ou signalez le cas à votre superviseur."
    )


async def _nom_de(uow, contexte: ContexteAcces) -> str | None:
    """Le nom de celui qui coche, tel qu'il apparaîtra en Responsable."""
    compte = await uow.utilisateurs.par_id(contexte.utilisateur_id)
    return compte.nom_complet if compte else None


def filtre_du_perimetre(contexte: ContexteAcces) -> FiltreBordereau:
    """Le filtre vide, rétréci au périmètre de l'appelant."""
    return restreindre(contexte, FiltreBordereau())
