"""Cas d'usage : affectation des itinéraires du jour à un agent de terrain.

C'est l'écran qui s'ouvre juste après la connexion du superviseur. Il matérialise
le briefing : *« dès que le superviseur est connecté à la plateforme, une autre
interface s'ouvre permettant d'entrer les itinéraires de l'agent de terrain en
question, car cela montre que l'agent est entré en contact avec le superviseur »*.

Affecter un itinéraire fait deux choses d'un coup : cela ouvre la journée de
travail de l'agent, et cela **matérialise son bordereau** — une ligne par client
de l'itinéraire, prête à recevoir le statut que le superviseur saisira au retour
du terrain.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ....domain.entities import Affectation, LigneBordereau
from ....domain.securite import ContexteAcces, Permission
from ....domain.value_objects import CodeItineraire
from ...errors import ConflitRessource, RessourceIntrouvable
from ...ports import Horloge, UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeAffectation:
    agent_id: UUID
    codes_itineraires: tuple[int, ...]
    date_travail: date
    superviseur_id: UUID
    consignes: str | None = None


@dataclass(frozen=True, slots=True)
class ItineraireAffecte:
    affectation_id: UUID
    code_itineraire: int
    libelle: str
    lignes_generees: int


@dataclass(frozen=True, slots=True)
class ResultatAffectation:
    agent_id: UUID
    matricule: str
    nom_agent: str
    date_travail: date
    itineraires: tuple[ItineraireAffecte, ...]

    @property
    def total_lignes(self) -> int:
        return sum(i.lignes_generees for i in self.itineraires)


class AffecterItineraires:
    """Confie un ou plusieurs itinéraires à un agent pour une journée."""

    def __init__(self, uow: UnitOfWork, horloge: Horloge) -> None:
        self._uow = uow
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeAffectation
    ) -> ResultatAffectation:
        """Crée les affectations et matérialise le bordereau correspondant.

        Raises:
            RessourceIntrouvable: agent ou itinéraire inconnu.
            ConflitRessource: itinéraire déjà affecté à cet agent ce jour-là.
            RegleMetierViolee: agent désactivé.
        """
        # Ajouter une tournée à un agent qui en porte déjà se fait par un
        # nouvel appel : les affectations s'accumulent, une par itinéraire
        # et par journée. Un bon collecteur en reçoit plusieurs.
        contexte.exiger(Permission.ITINERAIRE_AFFECTER)
        affectes: list[ItineraireAffecte] = []

        async with self._uow as uow:
            agent = await uow.agents.par_id(commande.agent_id)
            if agent is None:
                raise RessourceIntrouvable("Agent de terrain", commande.agent_id)
            agent.verifier_affectable()

            for code_brut in commande.codes_itineraires:
                code = CodeItineraire.parse(code_brut)

                itineraire = await uow.itineraires.par_code(code)
                if itineraire is None:
                    raise RessourceIntrouvable("Itinéraire", code_brut)

                if await uow.affectations.existe_deja(
                    agent.id, code, commande.date_travail
                ):
                    raise ConflitRessource(
                        f"L'itinéraire {code} est déjà affecté à {agent.matricule} "
                        f"pour le {commande.date_travail:%d/%m/%Y}"
                    )

                affectation = Affectation(
                    agent_id=agent.id,
                    itineraire_code=code,
                    date_travail=commande.date_travail,
                    superviseur_id=commande.superviseur_id,
                    consignes=commande.consignes,
                )
                await uow.affectations.enregistrer(affectation)

                lignes = await self._materialiser_bordereau(uow, affectation, code)
                affectes.append(
                    ItineraireAffecte(
                        affectation_id=affectation.id,
                        code_itineraire=code.valeur,
                        libelle=itineraire.designation,
                        lignes_generees=lignes,
                    )
                )

            await uow.valider()

        return ResultatAffectation(
            agent_id=agent.id,
            matricule=agent.matricule,
            nom_agent=agent.nom_complet,
            date_travail=commande.date_travail,
            itineraires=tuple(affectes),
        )

    async def _materialiser_bordereau(
        self, uow: UnitOfWork, affectation: Affectation, code: CodeItineraire
    ) -> int:
        """Crée une ligne vierge par client de l'itinéraire.

        Les données client sont recopiées sur la ligne : le bordereau reste
        ainsi lisible tel qu'il a été émis, même si le référentiel évolue
        ensuite.
        """
        clients = await uow.clients.par_itineraire(code)
        if not clients:
            return 0

        lignes = [
            LigneBordereau(
                service_no=client.service_no,
                date_collecte=affectation.date_travail,
                agent_id=affectation.agent_id,
                affectation_id=affectation.id,
                client_id=client.id,
                nom_client=client.nom,
                ref_geo=client.ref_geo,
                code_itineraire=code,
                numero_compteur=client.numero_compteur,
            )
            for client in sorted(clients, key=lambda c: c.cle_tri_terrain)
        ]

        return await uow.lignes.enregistrer_en_lot(lignes)
