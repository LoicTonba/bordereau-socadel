"""Cas d'usage du répertoire des agents de terrain.

Chaque cas d'usage commence par une garde RBAC : c'est la couche application
qui décide, pas la route HTTP. Une même règle vaut donc quel que soit le
transport, et un futur script d'administration ne pourra pas la contourner.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from ....domain.entities import AgentTerrain
from ....domain.securite import ContexteAcces, Permission, peut_agir_sur_agent
from ....domain.securite.permissions import AccesRefuse
from ....domain.value_objects import NumeroTelephone
from ...errors import ConflitRessource, RessourceIntrouvable
from ...ports import UnitOfWork


@dataclass(frozen=True, slots=True)
class CommandeCreationAgent:
    matricule: str
    nom_complet: str
    telephone: str | None = None
    zone_rattachement: str | None = None
    region: str | None = None
    photo_url: str | None = None


@dataclass(frozen=True, slots=True)
class CommandeModificationAgent:
    agent_id: UUID
    nom_complet: str | None = None
    telephone: str | None = None
    zone_rattachement: str | None = None
    region: str | None = None
    photo_url: str | None = None


class ListerAgents:
    """Répertoire, restreint au périmètre de l'appelant.

    Un superviseur territorialisé ne voit que les agents de sa région ; un
    agent connecté ne voit que sa propre fiche.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self,
        contexte: ContexteAcces,
        *,
        actifs_seulement: bool = False,
    ) -> Sequence[AgentTerrain]:
        contexte.exiger(Permission.AGENT_LIRE)

        async with self._uow as uow:
            agents = await uow.agents.lister(actifs_seulement=actifs_seulement)

        if contexte.est_agent:
            return [a for a in agents if a.id == contexte.agent_id]

        if contexte.region is not None:
            return [a for a in agents if a.region == contexte.region]

        return agents


class ConsulterAgent:
    """Fiche d'un agent."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(self, contexte: ContexteAcces, agent_id: UUID) -> AgentTerrain:
        contexte.exiger(Permission.AGENT_LIRE)

        # Un agent ne consulte que sa propre fiche.
        if contexte.est_agent and agent_id != contexte.agent_id:
            raise AccesRefuse("Vous ne pouvez consulter que votre propre fiche")

        async with self._uow as uow:
            agent = await uow.agents.par_id(agent_id)

        if agent is None:
            raise RessourceIntrouvable("Agent de terrain", agent_id)
        return agent


class EnregistrerAgent:
    """Crée un agent de terrain."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeCreationAgent
    ) -> AgentTerrain:
        """Enregistre un nouvel agent.

        Raises:
            AccesRefuse: le rôle n'autorise pas la création.
            ConflitRessource: le matricule est déjà pris.
            RegleMetierViolee: matricule ou nom vide.
        """
        contexte.exiger(Permission.AGENT_CREER)
        matricule = commande.matricule.strip().upper()

        async with self._uow as uow:
            if await uow.agents.par_matricule(matricule) is not None:
                raise ConflitRessource(f"Le matricule {matricule} existe déjà")

            agent = AgentTerrain(
                matricule=matricule,
                nom_complet=commande.nom_complet,
                telephone=NumeroTelephone.parse_ou_none(commande.telephone),
                zone_rattachement=commande.zone_rattachement,
                # Un superviseur territorialisé ne crée que dans sa région.
                region=commande.region or contexte.region,
                photo_url=commande.photo_url,
            )
            await uow.agents.enregistrer(agent)
            await uow.valider()

        return agent


class ModifierAgent:
    """Met à jour la fiche d'un agent."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeModificationAgent
    ) -> AgentTerrain:
        contexte.exiger(Permission.AGENT_MODIFIER)
        if not peut_agir_sur_agent(contexte, commande.agent_id):
            raise AccesRefuse("Vous ne pouvez pas modifier cette fiche")

        async with self._uow as uow:
            agent = await uow.agents.par_id(commande.agent_id)
            if agent is None:
                raise RessourceIntrouvable("Agent de terrain", commande.agent_id)

            agent.modifier(
                nom_complet=commande.nom_complet,
                telephone=NumeroTelephone.parse_ou_none(commande.telephone),
                zone_rattachement=commande.zone_rattachement,
                region=commande.region,
                photo_url=commande.photo_url,
            )
            await uow.agents.enregistrer(agent)
            await uow.valider()

        return agent


class BasculerActivationAgent:
    """Active ou désactive un agent sans jamais le supprimer.

    Les bordereaux passés référencent l'agent : l'effacer détruirait
    l'historique sur lequel repose sa rémunération. « Supprimer » signifie donc
    ici « retirer du service ».
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def executer(
        self, contexte: ContexteAcces, agent_id: UUID, *, actif: bool
    ) -> AgentTerrain:
        contexte.exiger(
            Permission.AGENT_MODIFIER if actif else Permission.AGENT_SUPPRIMER
        )
        if not peut_agir_sur_agent(contexte, agent_id):
            raise AccesRefuse("Vous ne pouvez pas agir sur cette fiche")

        async with self._uow as uow:
            agent = await uow.agents.par_id(agent_id)
            if agent is None:
                raise RessourceIntrouvable("Agent de terrain", agent_id)

            agent.reactiver() if actif else agent.desactiver()
            await uow.agents.enregistrer(agent)
            await uow.valider()

        return agent
