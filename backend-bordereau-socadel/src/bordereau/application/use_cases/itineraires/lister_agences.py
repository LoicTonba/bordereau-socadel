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
        async with self._uow as uow:
            lignes = await uow.clients.lister_agences()

        # Un nom ne doit apparaître qu'une fois : c'est lui que le compte
        # portera comme périmètre, et deux entrées identiques dans une liste
        # déroulante n'apprennent rien à celui qui choisit.
        vues: dict[str, Agence] = {}
        for nom, region, division in lignes:
            if nom and nom not in vues:
                vues[nom] = Agence(nom=nom, region=region, division=division)
        return list(vues.values())
