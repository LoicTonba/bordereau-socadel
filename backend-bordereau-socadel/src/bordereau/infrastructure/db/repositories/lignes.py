"""Repository PostgreSQL des lignes de bordereau.

C'est la table la plus sollicitée : le tableau du back-office, les exports et
la vérification y puisent tous. Filtres, tri et pagination sont donc traduits
en SQL plutôt qu'appliqués après chargement.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.dto import FiltreBordereau, Page, PaginationParams
from ....domain.entities import LigneBordereau
from ..mappers.mappers import ligne_vers_dict, ligne_vers_domaine, ligne_vers_orm
from ..models.tables import LigneBordereauORM
from .lots import par_lots

#: Colonnes que le client peut demander au tri. La liste est fermée : accepter
#: un nom de colonne arbitraire ouvrirait une injection par l'ORDER BY.
COLONNES_TRIABLES = {
    "date_collecte": LigneBordereauORM.date_collecte,
    "nom_client": LigneBordereauORM.nom_client,
    "service_no": LigneBordereauORM.service_no,
    "statut": LigneBordereauORM.statut,
    "verdict": LigneBordereauORM.verdict,
    "code_itineraire": LigneBordereauORM.code_itineraire,
    "ref_geo": LigneBordereauORM.ref_geo,
    "modifie_le": LigneBordereauORM.modifie_le,
}

TRI_PAR_DEFAUT = LigneBordereauORM.date_collecte


class LigneBordereauRepositoryPg:
    """Implémentation du port `LigneBordereauRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def par_id(self, ligne_id: UUID) -> LigneBordereau | None:
        row = await self._session.get(LigneBordereauORM, ligne_id)
        return ligne_vers_domaine(row) if row else None

    async def rechercher(
        self, filtre: FiltreBordereau, pagination: PaginationParams
    ) -> Page[LigneBordereau]:
        base = self._appliquer_filtre(select(LigneBordereauORM), filtre)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        if not total:
            return Page.vide(pagination)

        colonne = COLONNES_TRIABLES.get(pagination.tri or "", TRI_PAR_DEFAUT)
        ordre = colonne.desc() if pagination.ordre_descendant else colonne.asc()

        resultat = await self._session.scalars(
            base.order_by(ordre, LigneBordereauORM.id)
            .offset(pagination.offset)
            .limit(pagination.limite)
        )

        return Page(
            elements=[ligne_vers_domaine(row) for row in resultat],
            total=total,
            page=pagination.page,
            taille=pagination.taille,
        )

    async def lister_pour_export(
        self, filtre: FiltreBordereau, limite: int
    ) -> Sequence[LigneBordereau]:
        requete = self._appliquer_filtre(select(LigneBordereauORM), filtre)
        resultat = await self._session.scalars(
            requete.order_by(
                LigneBordereauORM.date_collecte.desc(),
                LigneBordereauORM.ref_geo.asc(),
            ).limit(limite)
        )
        return [ligne_vers_domaine(row) for row in resultat]

    async def lister_par_affectation(
        self, affectation_id: UUID
    ) -> Sequence[LigneBordereau]:
        resultat = await self._session.scalars(
            select(LigneBordereauORM)
            .where(LigneBordereauORM.affectation_id == affectation_id)
            .order_by(LigneBordereauORM.ref_geo.asc())
        )
        return [ligne_vers_domaine(row) for row in resultat]

    async def rechercher_par_numero(
        self, numero: str, *, code_itineraire: int | None = None
    ) -> Sequence[LigneBordereau]:
        """Les lignes qui portent déjà ce numéro, sur la tournée s'il y en a une.

        Sert la règle du doublon : un même numéro ne peut servir deux contrats
        d'un même itinéraire. La colonne est indexée, le bordereau comptant
        plusieurs centaines de milliers de lignes.
        """
        requete = select(LigneBordereauORM).where(
            LigneBordereauORM.numero_collecte == numero
        )
        if code_itineraire is not None:
            requete = requete.where(
                LigneBordereauORM.code_itineraire == code_itineraire
            )

        resultat = await self._session.scalars(requete)
        return [ligne_vers_domaine(row) for row in resultat]

    async def enregistrer(self, ligne: LigneBordereau) -> None:
        existant = await self._session.get(LigneBordereauORM, ligne.id)
        row = ligne_vers_orm(ligne, existant)
        if existant is None:
            self._session.add(row)

    async def enregistrer_en_lot(self, lignes: Iterable[LigneBordereau]) -> int:
        """Insère ou met à jour un lot, découpé en instructions tenables.

        L'affectation d'un itinéraire crée d'un coup plusieurs centaines de
        lignes : les insérer une par une multiplierait les allers-retours, mais
        tout envoyer d'un bloc dépasserait la limite de paramètres liés dès
        qu'un itinéraire compte plus de 1 600 clients.
        """
        valeurs = [ligne_vers_dict(ligne) for ligne in lignes]
        if not valeurs:
            return 0

        for paquet in par_lots(valeurs, len(valeurs[0])):
            instruction = insert(LigneBordereauORM).values(list(paquet))
            await self._session.execute(
                instruction.on_conflict_do_update(
                    index_elements=[LigneBordereauORM.id],
                    set_={
                        nom: instruction.excluded[nom]
                        for nom in valeurs[0]
                        if nom != "id"
                    },
                )
            )
        return len(valeurs)

    # --- Traduction du filtre en SQL --------------------------------------

    def _appliquer_filtre(
        self, requete: Select, filtre: FiltreBordereau
    ) -> Select:
        if filtre.recherche:
            motif = f"%{filtre.recherche.strip()}%"
            requete = requete.where(
                or_(
                    LigneBordereauORM.nom_client.ilike(motif),
                    LigneBordereauORM.service_no.ilike(motif),
                    LigneBordereauORM.numero_compteur.ilike(motif),
                    LigneBordereauORM.ref_geo.ilike(motif),
                    LigneBordereauORM.numero_collecte.ilike(motif),
                )
            )

        # Chaque colonne se cherche pour elle-même. `contient` filtre sur un
        # fragment, comme le fait la loupe d'un tableur : personne ne connaît
        # un SERVICE_NO en entier de mémoire.
        for critere, colonne in (
            (filtre.service_no, LigneBordereauORM.service_no),
            (filtre.nom_client, LigneBordereauORM.nom_client),
            (filtre.ref_geo, LigneBordereauORM.ref_geo),
            (filtre.numero_compteur, LigneBordereauORM.numero_compteur),
            (filtre.numero_collecte, LigneBordereauORM.numero_collecte),
            (filtre.responsable_nom, LigneBordereauORM.valide_par_nom),
        ):
            if critere and critere.strip():
                requete = requete.where(colonne.ilike(f"%{critere.strip()}%"))

        if filtre.rapports:
            requete = requete.where(
                LigneBordereauORM.rapport.in_([r.value for r in filtre.rapports])
            )

        if filtre.identites:
            requete = requete.where(
                LigneBordereauORM.identite.in_([i.value for i in filtre.identites])
            )

        if filtre.verifie_terrain is not None:
            # La colonne Check n'est qu'une date posée ou absente.
            requete = requete.where(
                LigneBordereauORM.verifie_terrain_le.is_not(None)
                if filtre.verifie_terrain
                else LigneBordereauORM.verifie_terrain_le.is_(None)
            )

        if filtre.periode:
            requete = requete.where(
                LigneBordereauORM.date_collecte.between(
                    filtre.periode.debut, filtre.periode.fin
                )
            )

        if filtre.statuts:
            requete = requete.where(
                LigneBordereauORM.statut.in_([s.value for s in filtre.statuts])
            )

        if filtre.verdicts:
            requete = requete.where(
                LigneBordereauORM.verdict.in_([v.value for v in filtre.verdicts])
            )

        if filtre.responsables:
            requete = requete.where(
                LigneBordereauORM.responsable.in_(
                    [r.value for r in filtre.responsables]
                )
            )

        if filtre.itineraires:
            requete = requete.where(
                LigneBordereauORM.code_itineraire.in_(
                    [i.valeur for i in filtre.itineraires]
                )
            )

        if filtre.agent_ids:
            requete = requete.where(
                LigneBordereauORM.agent_id.in_(list(filtre.agent_ids))
            )

        # Le découpage territorial n'est pas porté par la ligne : on le
        # rapatrie du référentiel via le client rattaché.
        if filtre.region or filtre.division or filtre.agence:
            from ..models.tables import ClientORM

            sous_requete = select(ClientORM.id)
            if filtre.region:
                sous_requete = sous_requete.where(ClientORM.region == filtre.region)
            if filtre.division:
                sous_requete = sous_requete.where(
                    ClientORM.division == filtre.division
                )
            if filtre.agence:
                sous_requete = sous_requete.where(ClientORM.agence == filtre.agence)
            requete = requete.where(LigneBordereauORM.client_id.in_(sous_requete))

        return requete
