"""Cas d'usage : SOCADEL tient son maillage territorial.

Le réseau bouge. Une agence ouvre dans un lotissement neuf, une autre devient
inaccessible et cesse d'accueillir des tournées, une division est redécoupée.
Jusqu'ici la liste était déduite du référentiel clients : la mettre à jour
supposait de rejouer un import de quatre cent mille lignes, ce qui n'est pas
une opération qu'on demande à un responsable d'agence.

Qui en a le droit. L'administrateur SOCADEL, parce que le maillage est une
décision de l'exploitant, et le super utilisateur NEXT LTD qui porte tout. Pas
le superviseur : il travaille dans une agence, il ne décide pas de leur
existence.

Fermer plutôt que supprimer. Une agence fermée disparaît des listes de travail
mais reste attachée à la production passée et aux comptes qui la portent. La
suppression n'est ouverte que tant que rien ne la référence, et le cas d'usage
le vérifie plutôt que de laisser la base trancher par une erreur de clé.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ...domain.entities import Agence
from ...domain.securite import ContexteAcces, Permission
from ..errors import ConflitRessource, RessourceIntrouvable
from ..ports import Horloge, UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeAgence:
    nom: str
    region: str | None = None
    division: str | None = None


@dataclass(frozen=True, slots=True)
class Territoire:
    """Le maillage, tel qu'un écran de pilotage veut le lire."""

    agences: tuple[Agence, ...]

    @property
    def regions(self) -> tuple[str, ...]:
        return tuple(sorted({a.region for a in self.agences if a.region}))

    @property
    def divisions(self) -> tuple[str, ...]:
        return tuple(sorted({a.division for a in self.agences if a.division}))


class ListerTerritoire:
    """Le maillage complet, ouvert à quiconque peut lire un périmètre."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, *, ouvertes_seulement: bool = False
    ) -> Territoire:
        contexte.exiger(Permission.PERIMETRE_DEFINIR)
        async with self._uow as uow:
            agences = await uow.agences.lister(ouvertes_seulement=ouvertes_seulement)
        return Territoire(agences=tuple(agences))


class CreerAgence:
    """Ouvre une agence que le référentiel ne connaissait pas."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeAgence
    ) -> Agence:
        contexte.exiger(Permission.TERRITOIRE_GERER)
        agence = Agence(
            nom=commande.nom, region=commande.region, division=commande.division
        )

        async with self._uow as uow:
            if await uow.agences.par_nom(agence.nom) is not None:
                raise ConflitRessource(
                    f"L'agence {agence.nom} existe déjà. Rouvrez-la si elle "
                    "est fermée, plutôt que d'en créer une seconde."
                )
            await uow.agences.enregistrer(agence)
            await uow.valider()

        return agence


class ModifierAgence:
    """Corrige le rattachement d'une agence. Son nom, lui, ne bouge pas."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, nom: str, commande: CommandeAgence
    ) -> Agence:
        contexte.exiger(Permission.TERRITOIRE_GERER)

        async with self._uow as uow:
            agence = await uow.agences.par_nom(nom.strip().upper())
            if agence is None:
                raise RessourceIntrouvable("Agence", nom)

            # Le nom est la clé que portent les comptes, les itinéraires et le
            # référentiel : le changer romprait ces trois liens d'un coup.
            if commande.region is not None:
                agence.region = commande.region.strip().upper() or None
            if commande.division is not None:
                agence.division = commande.division.strip().upper() or None

            await uow.agences.enregistrer(agence)
            await uow.valider()

        return agence


class FermerAgence:
    """Retire une agence des listes de travail, sans effacer son passé."""

    def __init__(self, uow: UnitOfWork, horloge: Horloge) -> None:
        self._uow = uow
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, nom: str, motif: str
    ) -> Agence:
        contexte.exiger(Permission.TERRITOIRE_GERER)

        async with self._uow as uow:
            agence = await uow.agences.par_nom(nom.strip().upper())
            if agence is None:
                raise RessourceIntrouvable("Agence", nom)

            agence.fermer(motif, self._horloge.maintenant())
            await uow.agences.enregistrer(agence)
            await uow.valider()

        return agence


class RouvrirAgence:
    """Remet une agence en service."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, contexte: ContexteAcces, nom: str) -> Agence:
        contexte.exiger(Permission.TERRITOIRE_GERER)

        async with self._uow as uow:
            agence = await uow.agences.par_nom(nom.strip().upper())
            if agence is None:
                raise RessourceIntrouvable("Agence", nom)

            agence.rouvrir()
            await uow.agences.enregistrer(agence)
            await uow.valider()

        return agence


class SupprimerAgence:
    """Efface une agence, tant que rien ne s'y rattache.

    Réservé à la correction d'une saisie. Dès qu'un compte porte l'agence
    comme périmètre ou qu'une tournée y est rattachée, la fermeture est la
    seule voie : effacer laisserait des périmètres pointant dans le vide.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, contexte: ContexteAcces, nom: str) -> None:
        contexte.exiger(Permission.TERRITOIRE_GERER)
        nom = nom.strip().upper()

        async with self._uow as uow:
            if await uow.agences.par_nom(nom) is None:
                raise RessourceIntrouvable("Agence", nom)

            attaches = await uow.agences.compter_rattachements(nom)
            if attaches:
                raise ConflitRessource(
                    f"{attaches} élément(s) se rattachent encore à {nom}, "
                    "comptes ou itinéraires. Fermez l'agence plutôt que de la "
                    "supprimer : sa production passée y renvoie."
                )

            await uow.agences.supprimer(nom)
            await uow.valider()


class ImporterTerritoireDepuisReferentiel:
    """Amorce le maillage à partir du référentiel clients.

    Utile une seule fois, à la mise en route : les 181 agences que SOCADEL
    exploite déjà sont dans le classeur, il serait absurde de les ressaisir.
    Ensuite, c'est l'application qui fait foi.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, contexte: ContexteAcces) -> int:
        contexte.exiger(Permission.TERRITOIRE_GERER)

        async with self._uow as uow:
            connues = {a.nom for a in await uow.agences.lister()}
            nouvelles: list[Agence] = []

            for nom, region, division in await uow.clients.lister_agences():
                if not nom or nom.strip().upper() in connues:
                    continue
                agence = Agence(nom=nom, region=region, division=division)
                connues.add(agence.nom)
                nouvelles.append(agence)

            for agence in nouvelles:
                await uow.agences.enregistrer(agence)
            await uow.valider()

        return len(nouvelles)


def agences_ouvertes(territoire: Territoire) -> Sequence[Agence]:
    return [a for a in territoire.agences if a.ouverte]
