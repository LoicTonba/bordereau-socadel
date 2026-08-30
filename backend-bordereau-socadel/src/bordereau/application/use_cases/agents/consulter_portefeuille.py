"""Cas d'usage : portefeuille d'un agent de terrain.

Il sert deux lectures qui demandent exactement les mêmes chiffres :

* le **superviseur** l'ouvre avant d'affecter, pour voir ce que l'agent porte
  déjà — un bon collecteur reçoit plusieurs itinéraires, et il faut savoir
  lesquels avant d'en ajouter ;
* l'**agent** l'ouvre pour lui-même : c'est la seule chose qu'il fait sur la
  plateforme.

La différence de droits ne change pas le calcul, seulement le périmètre : la
garde ABAC s'en occupe en amont.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ....domain.entities import AgentTerrain
from ....domain.securite import ContexteAcces, Permission
from ....domain.securite.permissions import AccesRefuse
from ....domain.services.performance_agent import PerformanceAgent, calculer
from ....domain.value_objects import Periode
from ...dto import FiltreBordereau
from ...errors import RessourceIntrouvable
from ...ports import UnitOfWork

#: Borne de lecture du portefeuille : au-delà, on entre dans l'historique, qui
#: relève des exports plutôt que de l'écran de suivi.
LIGNES_MAX = 5_000


@dataclass(frozen=True, slots=True)
class ItineraireDuJour:
    """Un itinéraire confié, avec son avancement."""

    affectation_id: UUID
    code_itineraire: int
    libelle: str
    date_travail: date
    statut: str
    clients_total: int
    clients_traites: int
    abonnements: int

    @property
    def taux_couverture(self) -> float:
        if self.clients_total <= 0:
            return 0.0
        return min(self.clients_traites / self.clients_total, 1.0)


@dataclass(frozen=True, slots=True)
class Portefeuille:
    """Ce qu'un agent porte sur une période, et ce qu'il en a fait."""

    agent: AgentTerrain
    periode: Periode
    itineraires: tuple[ItineraireDuJour, ...]
    performance: PerformanceAgent

    @property
    def itineraires_en_cours(self) -> tuple[ItineraireDuJour, ...]:
        """Ceux qui restent à terminer — ce que le superviseur regarde avant
        d'en confier un de plus."""
        return tuple(i for i in self.itineraires if i.taux_couverture < 1.0)


class ConsulterPortefeuille:
    """Assemble le portefeuille d'un agent sur une période."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, agent_id: UUID, periode: Periode
    ) -> Portefeuille:
        """Renvoie les itinéraires confiés et la performance associée.

        Raises:
            AccesRefuse: un agent qui demanderait le portefeuille d'un autre.
            RessourceIntrouvable: agent inconnu.
        """
        contexte.exiger(Permission.ANALYTICS_CONSULTER)

        if contexte.est_agent and agent_id != contexte.agent_id:
            raise AccesRefuse(
                "Vous ne pouvez consulter que votre propre portefeuille"
            )

        async with self._uow as uow:
            agent = await uow.agents.par_id(agent_id)
            if agent is None:
                raise RessourceIntrouvable("Agent de terrain", agent_id)

            affectations = await uow.affectations.lister_par_agent(agent_id, periode)

            # Toutes les lignes de l'agent sur la période, chargées une fois :
            # elles servent à la fois au décompte par itinéraire et au calcul
            # de performance.
            lignes = await uow.lignes.lister_pour_export(
                FiltreBordereau(agent_ids=(agent_id,), periode=periode), LIGNES_MAX
            )

            details = []
            for affectation in affectations:
                code = affectation.itineraire_code
                itineraire = await uow.itineraires.par_code(code)
                du_lot = [l for l in lignes if l.affectation_id == affectation.id]

                details.append(
                    ItineraireDuJour(
                        affectation_id=affectation.id,
                        code_itineraire=code.valeur,
                        libelle=(
                            itineraire.designation
                            if itineraire
                            else f"Itinéraire {code}"
                        ),
                        date_travail=affectation.date_travail,
                        statut=affectation.statut.value,
                        clients_total=len(du_lot),
                        clients_traites=sum(1 for l in du_lot if l.est_traitee),
                        abonnements=sum(1 for l in du_lot if l.est_productive),
                    )
                )

        return Portefeuille(
            agent=agent,
            periode=periode,
            itineraires=tuple(
                sorted(details, key=lambda i: i.date_travail, reverse=True)
            ),
            performance=calculer(lignes),
        )
