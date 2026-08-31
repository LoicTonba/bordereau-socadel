"""Repositories PostgreSQL des tables de référence et de pilotage.

Regroupés ici parce qu'ils sont courts et sans logique de requêtage
particulière ; les deux tables volumineuses (`clients`, `lignes_bordereau`)
ont chacune leur module.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.dto import Page, PaginationParams
from ....domain.entities import Affectation, AgentTerrain, Itineraire, Utilisateur
from ....domain.value_objects import CodeItineraire, Periode
from ..mappers.mappers import (
    affectation_vers_domaine,
    affectation_vers_orm,
    agent_vers_domaine,
    agent_vers_orm,
    itineraire_vers_domaine,
    utilisateur_vers_domaine,
    utilisateur_vers_orm,
)
from ..models.tables import (
    AffectationORM,
    AgentTerrainORM,
    ItineraireORM,
    UtilisateurORM,
)
from .lots import par_lots


class UtilisateurRepositoryPg:
    """Implémentation du port `UtilisateurRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def par_identifiant(self, identifiant: str) -> Utilisateur | None:
        row = await self._session.scalar(
            select(UtilisateurORM).where(UtilisateurORM.identifiant == identifiant)
        )
        return utilisateur_vers_domaine(row) if row else None

    async def par_id(self, utilisateur_id: UUID) -> Utilisateur | None:
        row = await self._session.get(UtilisateurORM, utilisateur_id)
        return utilisateur_vers_domaine(row) if row else None

    async def par_email(self, email: str) -> Utilisateur | None:
        row = await self._session.scalar(
            select(UtilisateurORM).where(
                UtilisateurORM.email == email.strip().lower()
            )
        )
        return utilisateur_vers_domaine(row) if row else None

    async def par_jeton_verification(self, jeton: str) -> Utilisateur | None:
        row = await self._session.scalar(
            select(UtilisateurORM).where(UtilisateurORM.jeton_verification == jeton)
        )
        return utilisateur_vers_domaine(row) if row else None

    async def par_jeton_reinitialisation(self, jeton: str) -> Utilisateur | None:
        row = await self._session.scalar(
            select(UtilisateurORM).where(
                UtilisateurORM.jeton_reinitialisation == jeton
            )
        )
        return utilisateur_vers_domaine(row) if row else None

    async def lister(self, *, statut: str | None = None) -> Sequence[Utilisateur]:
        requete = select(UtilisateurORM).order_by(UtilisateurORM.nom_complet.asc())
        if statut is not None:
            requete = requete.where(UtilisateurORM.statut == statut)
        resultat = await self._session.scalars(requete)
        return [utilisateur_vers_domaine(row) for row in resultat]

    async def enregistrer(self, utilisateur: Utilisateur) -> None:
        existant = await self._session.get(UtilisateurORM, utilisateur.id)
        row = utilisateur_vers_orm(utilisateur, existant)
        if existant is None:
            self._session.add(row)


class AgentRepositoryPg:
    """Implémentation du port `AgentRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def par_id(self, agent_id: UUID) -> AgentTerrain | None:
        row = await self._session.get(AgentTerrainORM, agent_id)
        return agent_vers_domaine(row) if row else None

    async def par_matricule(self, matricule: str) -> AgentTerrain | None:
        row = await self._session.scalar(
            select(AgentTerrainORM).where(
                AgentTerrainORM.matricule == matricule.upper()
            )
        )
        return agent_vers_domaine(row) if row else None

    async def lister(
        self, *, actifs_seulement: bool = False
    ) -> Sequence[AgentTerrain]:
        requete = select(AgentTerrainORM).order_by(AgentTerrainORM.nom_complet.asc())
        if actifs_seulement:
            requete = requete.where(AgentTerrainORM.actif.is_(True))
        resultat = await self._session.scalars(requete)
        return [agent_vers_domaine(row) for row in resultat]

    async def enregistrer(self, agent: AgentTerrain) -> None:
        existant = await self._session.get(AgentTerrainORM, agent.id)
        row = agent_vers_orm(agent, existant)
        if existant is None:
            self._session.add(row)


class ItineraireRepositoryPg:
    """Implémentation du port `ItineraireRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def par_code(self, code: CodeItineraire) -> Itineraire | None:
        row = await self._session.scalar(
            select(ItineraireORM).where(ItineraireORM.code == code.valeur)
        )
        return itineraire_vers_domaine(row) if row else None

    async def rechercher(
        self,
        *,
        terme: str | None = None,
        region: str | None = None,
        agence: str | None = None,
        codes: Sequence[CodeItineraire] = (),
        pagination: PaginationParams | None = None,
    ) -> Page[Itineraire]:
        params = pagination or PaginationParams()
        requete = select(ItineraireORM)

        if codes:
            requete = requete.where(
                ItineraireORM.code.in_([c.valeur for c in codes])
            )

        if terme:
            motif = f"%{terme.strip()}%"
            conditions = [
                ItineraireORM.libelle.ilike(motif),
                ItineraireORM.agence.ilike(motif),
            ]
            # Le superviseur tape le plus souvent le code directement.
            if terme.strip().isdigit():
                conditions.append(ItineraireORM.code == int(terme.strip()))
            requete = requete.where(or_(*conditions))

        if region:
            requete = requete.where(ItineraireORM.region == region)
        if agence:
            requete = requete.where(ItineraireORM.agence == agence)

        total = await self._session.scalar(
            select(func.count()).select_from(requete.subquery())
        )
        if not total:
            return Page.vide(params)

        resultat = await self._session.scalars(
            requete.order_by(ItineraireORM.code.asc())
            .offset(params.offset)
            .limit(params.limite)
        )
        return Page(
            elements=[itineraire_vers_domaine(row) for row in resultat],
            total=total,
            page=params.page,
            taille=params.taille,
        )

    async def est_affecte(self, code: CodeItineraire) -> bool:
        total = await self._session.scalar(
            select(func.count())
            .select_from(AffectationORM)
            .where(AffectationORM.itineraire_code == code.valeur)
        )
        return bool(total)

    async def supprimer(self, code: CodeItineraire) -> None:
        await self._session.execute(
            delete(ItineraireORM).where(ItineraireORM.code == code.valeur)
        )

    async def enregistrer_en_lot(self, itineraires: Iterable[Itineraire]) -> int:
        valeurs = [
            {
                "id": i.id,
                "code": i.code.valeur,
                "libelle": i.libelle,
                "region": i.region,
                "division": i.division,
                "agence": i.agence,
                "mrc": i.mrc,
                "nombre_clients": i.nombre_clients,
            }
            for i in itineraires
        ]
        if not valeurs:
            return 0

        # Un référentiel complet compte plusieurs milliers d'itinéraires :
        # tout insérer d'un bloc dépasserait la limite de paramètres liés.
        for paquet in par_lots(valeurs, len(valeurs[0])):
            instruction = insert(ItineraireORM).values(list(paquet))
            await self._session.execute(
                instruction.on_conflict_do_update(
                    index_elements=[ItineraireORM.code],
                    set_={
                        nom: instruction.excluded[nom]
                        for nom in valeurs[0]
                        if nom not in ("id", "code")
                    },
                )
            )
        return len(valeurs)


class AffectationRepositoryPg:
    """Implémentation du port `AffectationRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def par_id(self, affectation_id: UUID) -> Affectation | None:
        row = await self._session.get(AffectationORM, affectation_id)
        return affectation_vers_domaine(row) if row else None

    async def lister_du_jour(self, jour: date) -> Sequence[Affectation]:
        resultat = await self._session.scalars(
            select(AffectationORM)
            .where(AffectationORM.date_travail == jour)
            .order_by(AffectationORM.itineraire_code.asc())
        )
        return [affectation_vers_domaine(row) for row in resultat]

    async def lister_par_agent(
        self, agent_id: UUID, periode: Periode
    ) -> Sequence[Affectation]:
        resultat = await self._session.scalars(
            select(AffectationORM)
            .where(
                AffectationORM.agent_id == agent_id,
                AffectationORM.date_travail.between(periode.debut, periode.fin),
            )
            .order_by(AffectationORM.date_travail.desc())
        )
        return [affectation_vers_domaine(row) for row in resultat]

    async def existe_deja(
        self, agent_id: UUID, code: CodeItineraire, jour: date
    ) -> bool:
        trouve = await self._session.scalar(
            select(AffectationORM.id).where(
                AffectationORM.agent_id == agent_id,
                AffectationORM.itineraire_code == code.valeur,
                AffectationORM.date_travail == jour,
            )
        )
        return trouve is not None

    async def enregistrer(self, affectation: Affectation) -> None:
        existant = await self._session.get(AffectationORM, affectation.id)
        row = affectation_vers_orm(affectation, existant)
        if existant is None:
            self._session.add(row)
