"""Cas d'usage : l'annuaire territorial servant les listes déroulantes.

Le sélecteur d'agence de l'écran de connexion en a besoin **avant** toute
authentification. La liste est donc publique, ce qui est assumé : le maillage
d'agences de SOCADEL est une information commerciale, affichée en boutique et
sur son site. Aucun volume de portefeuille n'est exposé ici, seulement des
noms de lieux.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...ports import UnitOfWork


@dataclass(frozen=True, slots=True)
class Agence:
    """Une agence, replacée dans sa direction et sa division."""

    nom: str
    region: str | None
    division: str | None


class ListerAgences:
    """Renvoie les agences connues du référentiel, triées par direction."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self) -> list[Agence]:
        """Les agences ouvertes, telles que l'application les tient.

        C'est le maillage entretenu par SOCADEL qui fait foi, pas le
        référentiel clients : une agence fermée pour cause d'insécurité doit
        disparaître du sélecteur de connexion le jour même, sans attendre un
        nouvel import. Le référentiel ne sert que de repli, sur une base dont
        le maillage n'a pas encore été amorcé.
        """
        async with self._uow as uow:
            maillage = await uow.agences.lister(ouvertes_seulement=True)
            if maillage:
                return [
                    Agence(nom=a.nom, region=a.region, division=a.division)
                    for a in maillage
                ]
            lignes = await uow.clients.lister_agences()

        # Un nom ne doit apparaître qu'une fois : c'est lui que le compte
        # portera comme périmètre, et deux entrées identiques dans une liste
        # déroulante n'apprennent rien à celui qui choisit.
        vues: dict[str, Agence] = {}
        for nom, region, division in lignes:
            if nom and nom not in vues:
                vues[nom] = Agence(nom=nom, region=region, division=division)
        return list(vues.values())
