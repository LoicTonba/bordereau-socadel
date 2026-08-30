"""Repository PostgreSQL du référentiel clients."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.dto import PaginationParams
from ....domain.entities import Client
from ....domain.value_objects import CodeItineraire, ServiceNo
from ..mappers.mappers import client_vers_dict, client_vers_domaine
from ..models.tables import ClientORM
from .lots import par_lots

#: Taille des paquets de **lecture** par `IN (...)`. Au-delà, PostgreSQL bascule
#: sur un plan de requête défavorable. Les insertions, elles, sont découpées par
#: `par_lots`, qui calcule la tranche à partir du nombre de colonnes.
TAILLE_LOT = 2_000


class ClientRepositoryPg:
    """Implémentation du port `ClientRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def par_service_no(self, service_no: ServiceNo) -> Client | None:
        row = await self._session.scalar(
            select(ClientORM).where(ClientORM.service_no == service_no.valeur)
        )
        return client_vers_domaine(row) if row else None

    async def par_services_no(
        self, services_no: Iterable[ServiceNo]
    ) -> dict[str, Client]:
        valeurs = {s.valeur for s in services_no}
        if not valeurs:
            return {}

        trouves: dict[str, Client] = {}
        # Découpé en paquets : un `IN` de plusieurs milliers d'éléments fait
        # basculer PostgreSQL sur un plan de requête défavorable.
        liste = list(valeurs)
        for debut in range(0, len(liste), TAILLE_LOT):
            paquet = liste[debut : debut + TAILLE_LOT]
            resultat = await self._session.scalars(
                select(ClientORM).where(ClientORM.service_no.in_(paquet))
            )
            for row in resultat:
                trouves[row.service_no] = client_vers_domaine(row)

        return trouves

    async def par_itineraire(
        self, code: CodeItineraire, pagination: PaginationParams | None = None
    ) -> Sequence[Client]:
        requete = (
            select(ClientORM)
            .where(ClientORM.code_itineraire == code.valeur)
            .order_by(ClientORM.ref_geo.asc())
        )
        if pagination is not None:
            requete = requete.offset(pagination.offset).limit(pagination.limite)

        resultat = await self._session.scalars(requete)
        return [client_vers_domaine(row) for row in resultat]

    async def compter_par_itineraire(self, code: CodeItineraire) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(ClientORM)
            .where(ClientORM.code_itineraire == code.valeur)
        )
        return total or 0

    async def lister_agences(self) -> Sequence[tuple[str, str | None, str | None]]:
        """L'annuaire territorial, tel que le référentiel l'établit.

        La source est le référentiel clients et non la table des itinéraires :
        celle-ci rattache quinze agences à deux divisions à la fois, séquelle
        de l'import, et le sélecteur afficherait alors des doublons. Le
        référentiel, lui, donne 181 agences sans ambiguïté.
        """
        resultat = await self._session.execute(
            select(ClientORM.agence, ClientORM.region, ClientORM.division)
            .where(ClientORM.agence.is_not(None))
            .distinct()
            .order_by(
                ClientORM.region.asc(),
                ClientORM.division.asc(),
                ClientORM.agence.asc(),
            )
        )
        return [tuple(ligne) for ligne in resultat.all()]

    async def enregistrer_en_lot(self, clients: Iterable[Client]) -> int:
        """Insertion idempotente du référentiel, par paquets.

        Le conflit se résout sur `service_no` plutôt que sur l'identifiant
        technique : un réimport du fichier source doit mettre à jour le client
        existant, pas en créer un doublon.
        """
        valeurs = [client_vers_dict(client) for client in clients]
        if not valeurs:
            return 0

        ecrits = 0
        for paquet in par_lots(valeurs, len(valeurs[0])):
            instruction = insert(ClientORM).values(list(paquet))
            await self._session.execute(
                instruction.on_conflict_do_update(
                    index_elements=[ClientORM.service_no],
                    set_={
                        nom: instruction.excluded[nom]
                        for nom in paquet[0]
                        if nom not in ("id", "service_no")
                    },
                )
            )
            ecrits += len(paquet)

        return ecrits
