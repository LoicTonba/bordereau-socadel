"""Cas d'usage : le superviseur tient lui-même son répertoire de tournées.

Les seize mille itinéraires du référentiel viennent de l'import initial. Ils ne
suffisent pas : une agence ouvre une zone, un lotissement sort de terre, une
tournée est scindée parce qu'elle est devenue trop longue. Attendre un nouvel
import pour cela reviendrait à bloquer le terrain sur un calendrier
informatique.

Deux garde-fous, et ils tiennent au fait que l'itinéraire est référencé
ailleurs.

Le code est unique et **ne se modifie pas**. C'est lui que portent les
affectations et les lignes de bordereau ; le changer romprait le lien avec la
production déjà saisie. Pour renommer, on modifie le libellé ; pour changer de
code, on crée et on n'affecte plus l'ancien.

Une tournée déjà confiée **ne se supprime pas**. La production passée y renvoie,
et l'effacer laisserait des lignes orphelines. La suppression n'est donc
possible que tant que l'itinéraire n'a jamais servi.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ....domain.entities import Itineraire
from ....domain.securite import ContexteAcces, Permission
from ....domain.value_objects import CodeItineraire
from ...errors import ConflitRessource, RessourceIntrouvable
from ...ports import UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeCreationItineraire:
    code: int
    libelle: str | None = None
    region: str | None = None
    division: str | None = None
    agence: str | None = None
    mrc: str | None = None


@dataclass(frozen=True, slots=True)
class CommandeModificationItineraire:
    code: int
    libelle: str | None = None
    region: str | None = None
    division: str | None = None
    agence: str | None = None
    mrc: str | None = None


class CreerItineraire:
    """Ouvre une tournée qui n'existait pas au référentiel."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeCreationItineraire
    ) -> Itineraire:
        contexte.exiger(Permission.ITINERAIRE_GERER)
        code = CodeItineraire(commande.code)

        async with self._uow as uow:
            if await uow.itineraires.par_code(code) is not None:
                raise ConflitRessource(
                    f"L'itinéraire {commande.code} existe déjà. "
                    "Modifiez-le plutôt que d'en créer un second."
                )

            itineraire = Itineraire(
                code=code,
                libelle=_propre(commande.libelle),
                region=_propre(commande.region),
                division=_propre(commande.division),
                # Un superviseur territorialisé crée dans son agence : lui
                # laisser en ouvrir ailleurs contournerait son périmètre.
                agence=_propre(commande.agence) or contexte.agence,
                mrc=_propre(commande.mrc),
            )
            await uow.itineraires.enregistrer_en_lot([itineraire])
            await uow.valider()

        return itineraire


class ModifierItineraire:
    """Corrige le libellé ou le rattachement territorial d'une tournée."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeModificationItineraire
    ) -> Itineraire:
        contexte.exiger(Permission.ITINERAIRE_GERER)
        code = CodeItineraire(commande.code)

        async with self._uow as uow:
            itineraire = await uow.itineraires.par_code(code)
            if itineraire is None:
                raise RessourceIntrouvable("Itinéraire", commande.code)

            # Le code n'est pas modifiable : il est la clé que portent les
            # affectations et les lignes déjà saisies.
            for champ in ("libelle", "region", "division", "agence", "mrc"):
                valeur = _propre(getattr(commande, champ))
                if valeur is not None:
                    setattr(itineraire, champ, valeur)

            await uow.itineraires.enregistrer_en_lot([itineraire])
            await uow.valider()

        return itineraire


class SupprimerItineraire:
    """Retire une tournée, tant qu'elle n'a jamais été confiée."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, contexte: ContexteAcces, code_brut: int) -> None:
        contexte.exiger(Permission.ITINERAIRE_GERER)
        code = CodeItineraire(code_brut)

        async with self._uow as uow:
            if await uow.itineraires.par_code(code) is None:
                raise RessourceIntrouvable("Itinéraire", code_brut)

            if await uow.itineraires.est_affecte(code):
                raise ConflitRessource(
                    f"L'itinéraire {code_brut} a déjà été confié à un agent. "
                    "Sa production y renvoie, il ne peut plus être supprimé ; "
                    "cessez simplement de l'affecter."
                )

            await uow.itineraires.supprimer(code)
            await uow.valider()


def _propre(valeur: str | None) -> str | None:
    """Une chaîne vide est une absence de valeur, pas une valeur vide."""
    if valeur is None:
        return None
    texte = valeur.strip()
    return texte or None
