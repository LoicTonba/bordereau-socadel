"""Modèle de lecture analytique en SQL.

Implémente le port `RequetesAnalytiques`. Tout est agrégé côté PostgreSQL :
c'est la seule façon de tenir un temps d'affichage correct sur un historique
qui grossit d'un bordereau par agent et par jour.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import timedelta

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ....application.dto import (
    CarteKpi,
    CouvertureItineraire,
    FiltreBordereau,
    LigneClassementAgent,
    PointSerie,
)
from ....domain.enums import StatutCollecte, VerdictVerification
from ....domain.value_objects import Periode
from ..models.tables import AgentTerrainORM, ItineraireORM, LigneBordereauORM


class RequetesAnalytiquesPg:
    """Agrégations du tableau de bord.

    Chaque méthode ouvre sa propre session. C'est délibéré : le tableau de bord
    lance ses cinq requêtes en parallèle, or une `AsyncSession` ne supporte
    qu'une opération à la fois — les faire partager une session lèverait
    « another operation is in progress ».
    """

    def __init__(self, fabrique: async_sessionmaker[AsyncSession]) -> None:
        self._fabrique = fabrique

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[AsyncSession]:
        session = self._fabrique()
        try:
            yield session
        finally:
            await session.close()

    # --- Cartes du bandeau supérieur --------------------------------------

    async def indicateurs(
        self, periode: Periode, filtre: FiltreBordereau
    ) -> Sequence[CarteKpi]:
        courant = await self._compter(periode, filtre)
        precedent = await self._compter(self._periode_precedente(periode), filtre)

        return (
            CarteKpi(
                cle="lignes_traitees",
                libelle="Clients démarchés",
                valeur=courant["traitees"],
                valeur_precedente=precedent["traitees"],
            ),
            CarteKpi(
                cle="abonnements",
                libelle="Abonnements déclarés",
                valeur=courant["abonnes"],
                valeur_precedente=precedent["abonnes"],
            ),
            CarteKpi(
                cle="abonnements_confirmes",
                libelle="Abonnements confirmés",
                valeur=courant["confirmes"],
                valeur_precedente=precedent["confirmes"],
            ),
            CarteKpi(
                cle="taux_conversion",
                libelle="Taux de conversion",
                valeur=_ratio(courant["abonnes"], courant["traitees"]),
                valeur_precedente=_ratio(
                    precedent["abonnes"], precedent["traitees"]
                ),
                unite="%",
            ),
            CarteKpi(
                cle="taux_fiabilite",
                libelle="Fiabilité des déclarations",
                valeur=_ratio(
                    courant["confirmes"], courant["confirmes"] + courant["infirmes"]
                ),
                valeur_precedente=_ratio(
                    precedent["confirmes"],
                    precedent["confirmes"] + precedent["infirmes"],
                ),
                unite="%",
            ),
        )

    async def _compter(
        self, periode: Periode, filtre: FiltreBordereau
    ) -> dict[str, int]:
        requete = self._filtrer(
            select(
                func.count().label("total"),
                func.count()
                .filter(LigneBordereauORM.statut != StatutCollecte.A_TRAITER.value)
                .label("traitees"),
                func.count()
                .filter(LigneBordereauORM.statut == StatutCollecte.ABONNE.value)
                .label("abonnes"),
                # Confirmé/infirmé se comptent **sur les abonnements déclarés**
                # seulement : une ligne « absent » corroborée par le référentiel
                # n'est pas un abonnement confirmé. C'est la définition portée
                # par `domain.services.performance_agent`.
                func.count()
                .filter(_abonnement_confirme())
                .label("confirmes"),
                func.count()
                .filter(_abonnement_infirme())
                .label("infirmes"),
            ),
            periode,
            filtre,
        )
        async with self._session() as session:
            ligne = (await session.execute(requete)).one()
        return {
            "total": ligne.total or 0,
            "traitees": ligne.traitees or 0,
            "abonnes": ligne.abonnes or 0,
            "confirmes": ligne.confirmes or 0,
            "infirmes": ligne.infirmes or 0,
        }

    # --- Courbe d'évolution ------------------------------------------------

    async def evolution(
        self, periode: Periode, filtre: FiltreBordereau
    ) -> Sequence[PointSerie]:
        requete = self._filtrer(
            select(
                LigneBordereauORM.date_collecte.label("jour"),
                func.count()
                .filter(LigneBordereauORM.statut != StatutCollecte.A_TRAITER.value)
                .label("collectes"),
                func.count()
                .filter(LigneBordereauORM.statut == StatutCollecte.ABONNE.value)
                .label("abonnements"),
                func.count()
                .filter(_abonnement_confirme())
                .label("confirmes"),
            ),
            periode,
            filtre,
        ).group_by(LigneBordereauORM.date_collecte)

        async with self._session() as session:
            lignes = (await session.execute(requete)).all()
        mesures = {ligne.jour: ligne for ligne in lignes}

        # La série est complétée jour par jour : un trou dans les données
        # deviendrait un trou dans la courbe, illisible pour le superviseur.
        return [
            PointSerie(
                jour=jour,
                collectes=mesures[jour].collectes if jour in mesures else 0,
                abonnements=mesures[jour].abonnements if jour in mesures else 0,
                confirmes=mesures[jour].confirmes if jour in mesures else 0,
            )
            for jour in periode.jours()
        ]

    # --- Classement des agents --------------------------------------------

    async def classement_agents(
        self, periode: Periode, filtre: FiltreBordereau, limite: int = 10
    ) -> Sequence[LigneClassementAgent]:
        traitees = func.count().filter(
            LigneBordereauORM.statut != StatutCollecte.A_TRAITER.value
        )
        abonnes = func.count().filter(
            LigneBordereauORM.statut == StatutCollecte.ABONNE.value
        )
        confirmes = func.count().filter(_abonnement_confirme())
        infirmes = func.count().filter(_abonnement_infirme())

        requete = (
            self._filtrer(
                select(
                    AgentTerrainORM.id.label("agent_id"),
                    AgentTerrainORM.matricule,
                    AgentTerrainORM.nom_complet,
                    traitees.label("traitees"),
                    abonnes.label("abonnes"),
                    confirmes.label("confirmes"),
                    infirmes.label("infirmes"),
                ).join(
                    AgentTerrainORM,
                    AgentTerrainORM.id == LigneBordereauORM.agent_id,
                ),
                periode,
                filtre,
            )
            .group_by(
                AgentTerrainORM.id,
                AgentTerrainORM.matricule,
                AgentTerrainORM.nom_complet,
            )
            .order_by(abonnes.desc())
            .limit(limite)
        )

        async with self._session() as session:
            lignes = (await session.execute(requete)).all()

        return [
            LigneClassementAgent(
                agent_id=ligne.agent_id,
                matricule=ligne.matricule,
                nom_complet=ligne.nom_complet,
                lignes_traitees=ligne.traitees,
                abonnements_declares=ligne.abonnes,
                abonnements_confirmes=ligne.confirmes,
                taux_conversion=_fraction(ligne.abonnes, ligne.traitees),
                taux_fiabilite=_fraction(
                    ligne.confirmes, ligne.confirmes + ligne.infirmes
                ),
            )
            for ligne in lignes
        ]

    # --- Couverture des itinéraires ---------------------------------------

    async def couverture_itineraires(
        self, periode: Periode, filtre: FiltreBordereau, limite: int = 20
    ) -> Sequence[CouvertureItineraire]:
        traites = func.count().filter(
            LigneBordereauORM.statut != StatutCollecte.A_TRAITER.value
        )
        abonnes = func.count().filter(
            LigneBordereauORM.statut == StatutCollecte.ABONNE.value
        )

        requete = (
            self._filtrer(
                select(
                    LigneBordereauORM.code_itineraire.label("code"),
                    func.max(ItineraireORM.libelle).label("libelle"),
                    func.max(ItineraireORM.agence).label("agence"),
                    func.max(ItineraireORM.nombre_clients).label("clients_total"),
                    traites.label("traites"),
                    abonnes.label("abonnes"),
                ).outerjoin(
                    ItineraireORM,
                    ItineraireORM.code == LigneBordereauORM.code_itineraire,
                ),
                periode,
                filtre,
            )
            .where(LigneBordereauORM.code_itineraire.is_not(None))
            .group_by(LigneBordereauORM.code_itineraire)
            .order_by(traites.desc())
            .limit(limite)
        )

        async with self._session() as session:
            lignes = (await session.execute(requete)).all()

        return [
            CouvertureItineraire(
                code_itineraire=ligne.code,
                libelle=ligne.libelle or f"Itinéraire {ligne.code}",
                agence=ligne.agence,
                clients_total=ligne.clients_total or ligne.traites,
                clients_traites=ligne.traites,
                abonnements=ligne.abonnes,
            )
            for ligne in lignes
        ]

    # --- Répartition par statut -------------------------------------------

    async def repartition_statuts(
        self, periode: Periode, filtre: FiltreBordereau
    ) -> dict[str, int]:
        requete = self._filtrer(
            select(LigneBordereauORM.statut, func.count().label("total")),
            periode,
            filtre,
        ).group_by(LigneBordereauORM.statut)

        async with self._session() as session:
            lignes = (await session.execute(requete)).all()
        return {ligne.statut: ligne.total for ligne in lignes}

    # --- Fabrique de clauses WHERE ----------------------------------------

    def _filtrer(
        self, requete: Select, periode: Periode, filtre: FiltreBordereau
    ) -> Select:
        """Applique la période et les critères communs.

        La période passée en argument prime sur celle du filtre : elle sert
        justement à rejouer la même requête sur la période précédente.
        """
        requete = requete.where(
            LigneBordereauORM.date_collecte.between(periode.debut, periode.fin)
        )

        if filtre.agent_ids:
            requete = requete.where(
                LigneBordereauORM.agent_id.in_(list(filtre.agent_ids))
            )
        if filtre.itineraires:
            requete = requete.where(
                LigneBordereauORM.code_itineraire.in_(
                    [i.valeur for i in filtre.itineraires]
                )
            )
        if filtre.statuts:
            requete = requete.where(
                LigneBordereauORM.statut.in_([s.value for s in filtre.statuts])
            )

        return requete

    @staticmethod
    def _periode_precedente(periode: Periode) -> Periode:
        """Fenêtre de même longueur, immédiatement antérieure."""
        duree = timedelta(days=periode.nombre_de_jours)
        return Periode(periode.debut - duree, periode.fin - duree)


def _abonnement_confirme():
    """Abonnement déclaré **et** corroboré par le référentiel : ligne payable."""
    return and_(
        LigneBordereauORM.statut == StatutCollecte.ABONNE.value,
        LigneBordereauORM.verdict == VerdictVerification.CONFIRME.value,
    )


def _abonnement_infirme():
    """Abonnement déclaré que le référentiel contredit ou ne retrouve pas."""
    return and_(
        LigneBordereauORM.statut == StatutCollecte.ABONNE.value,
        LigneBordereauORM.verdict.in_(
            (
                VerdictVerification.INFIRME.value,
                VerdictVerification.INTROUVABLE.value,
            )
        ),
    )


def _fraction(numerateur: int, denominateur: int) -> float:
    """Proportion entre 0 et 1, nulle si le dénominateur l'est."""
    if not denominateur:
        return 0.0
    return round(numerateur / denominateur, 4)


def _ratio(numerateur: int, denominateur: int) -> float:
    """Pourcentage arrondi à une décimale, pour les cartes KPI."""
    return round(_fraction(numerateur, denominateur) * 100, 1)
