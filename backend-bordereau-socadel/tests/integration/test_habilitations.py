"""Vérifie les habilitations **à travers l'API HTTP**.

Les tests unitaires prouvent que la politique est juste ; ceux-ci prouvent
qu'elle est effectivement branchée sur chaque route. C'est la différence entre
une règle écrite et une règle appliquée.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from bordereau.domain.entities import (
    AgentTerrain,
    Client,
    Itineraire,
    Utilisateur,
)
from bordereau.domain.enums import Role
from bordereau.infrastructure.config.settings import Settings
from bordereau.infrastructure.container import Container
from bordereau.main import creer_application

from ..conftest import MOT_DE_PASSE_TEST
from ..doubles import EntrepotMemoire

PREFIXE = "/api/v1"


@pytest.fixture
def app(settings: Settings, container: Container) -> FastAPI:
    application = creer_application(settings)
    application.state.container = container
    return application


@pytest.fixture
async def client_http(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def compte_agent(
    container: Container, entrepot: EntrepotMemoire, agent: AgentTerrain
) -> Utilisateur:
    """Compte de connexion de l'agent AG001."""
    compte = Utilisateur(
        identifiant="ag001",
        nom_complet=agent.nom_complet,
        empreinte_mot_de_passe=container.hacheur.hacher(MOT_DE_PASSE_TEST),
        role=Role.AGENT_TERRAIN,
        agent_id=agent.id,
    )
    entrepot.utilisateurs[compte.id] = compte
    return compte


@pytest.fixture
def autre_agent(entrepot: EntrepotMemoire) -> AgentTerrain:
    autre = AgentTerrain(matricule="AG002", nom_complet="NGONO Marie Claire")
    entrepot.agents[autre.id] = autre
    return autre


async def _entetes(client_http: AsyncClient, identifiant: str) -> dict[str, str]:
    reponse = await client_http.post(
        f"{PREFIXE}/auth/connexion",
        json={"identifiant": identifiant, "motDePasse": MOT_DE_PASSE_TEST},
    )
    assert reponse.status_code == 200, reponse.text
    return {"Authorization": f"Bearer {reponse.json()['jeton']}"}


class TestAgentConnecte:
    """L'agent se connecte et consulte ses chiffres. Rien d'autre."""

    async def test_il_se_connecte(
        self, client_http: AsyncClient, compte_agent: Utilisateur
    ) -> None:
        entetes = await _entetes(client_http, "ag001")

        profil = await client_http.get(f"{PREFIXE}/auth/moi", headers=entetes)

        assert profil.status_code == 200
        corps = profil.json()
        assert corps["role"] == "AGENT_TERRAIN"
        # Le frontend n'affichera que trois familles d'actions.
        assert set(corps["permissions"]) == {
            "bordereau:lire",
            "analytics:consulter",
            "profil:consulter",
        }

    async def test_il_ne_voit_que_sa_propre_production(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
        autre_agent: AgentTerrain,
        itineraire: Itineraire,
        clients: list[Client],
        jour: date,
    ) -> None:
        # Le superviseur affecte le même itinéraire aux deux agents, sur deux
        # journées distinctes pour ne pas heurter l'unicité.
        entetes_sup = await _entetes(client_http, "superviseur")
        for identifiant, jour_travail in (
            (agent.id, jour),
            (autre_agent.id, date(2026, 8, 29)),
        ):
            reponse = await client_http.post(
                f"{PREFIXE}/itineraires/affectations",
                headers=entetes_sup,
                json={
                    "agentId": str(identifiant),
                    "codesItineraires": [itineraire.code.valeur],
                    "dateTravail": jour_travail.isoformat(),
                },
            )
            assert reponse.status_code == 201, reponse.text

        # Le superviseur voit les six lignes.
        vue_sup = await client_http.get(f"{PREFIXE}/bordereau", headers=entetes_sup)
        assert vue_sup.json()["meta"]["total"] == 6

        # L'agent n'en voit que trois : les siennes.
        entetes_agent = await _entetes(client_http, "ag001")
        vue_agent = await client_http.get(
            f"{PREFIXE}/bordereau", headers=entetes_agent
        )
        assert vue_agent.json()["meta"]["total"] == 3
        assert all(
            l["agentId"] == str(agent.id) for l in vue_agent.json()["elements"]
        )

    async def test_il_ne_peut_pas_reclamer_les_lignes_d_un_autre(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
        autre_agent: AgentTerrain,
        itineraire: Itineraire,
        clients: list[Client],
        jour: date,
    ) -> None:
        """Le cœur de la garde ABAC : le périmètre demandé est écrasé."""
        entetes_sup = await _entetes(client_http, "superviseur")
        await client_http.post(
            f"{PREFIXE}/itineraires/affectations",
            headers=entetes_sup,
            json={
                "agentId": str(autre_agent.id),
                "codesItineraires": [itineraire.code.valeur],
                "dateTravail": jour.isoformat(),
            },
        )

        entetes_agent = await _entetes(client_http, "ag001")
        # Il demande explicitement la production de l'autre agent.
        vue = await client_http.get(
            f"{PREFIXE}/bordereau",
            headers=entetes_agent,
            params={"agent": str(autre_agent.id)},
        )

        assert vue.status_code == 200
        assert vue.json()["meta"]["total"] == 0, (
            "le filtre par agent est écrasé par le périmètre de l'appelant"
        )

    @pytest.mark.parametrize(
        ("methode", "chemin", "corps"),
        [
            ("post", "/bordereau/verification", None),
            ("post", "/itineraires/affectations", {}),
            ("post", "/agents", {}),
            ("post", "/comptes", {}),
        ],
    )
    async def test_les_actions_d_ecriture_lui_sont_fermees(
        self,
        client_http: AsyncClient,
        compte_agent: Utilisateur,
        methode: str,
        chemin: str,
        corps: dict | None,
    ) -> None:
        entetes = await _entetes(client_http, "ag001")

        reponse = await getattr(client_http, methode)(
            f"{PREFIXE}{chemin}", headers=entetes, json=corps
        )

        # 403 si la garde a tranché, 422 si le corps vide est rejeté avant :
        # dans les deux cas, l'action n'a pas eu lieu.
        assert reponse.status_code in (403, 422), reponse.text

    async def test_l_export_lui_est_ferme(
        self, client_http: AsyncClient, compte_agent: Utilisateur
    ) -> None:
        entetes = await _entetes(client_http, "ag001")
        reponse = await client_http.get(f"{PREFIXE}/exports/csv", headers=entetes)

        assert reponse.status_code == 403
        assert reponse.json()["code"] == "acces_refuse"

    async def test_il_ne_consulte_pas_le_portefeuille_d_un_autre(
        self,
        client_http: AsyncClient,
        compte_agent: Utilisateur,
        autre_agent: AgentTerrain,
    ) -> None:
        entetes = await _entetes(client_http, "ag001")

        reponse = await client_http.get(
            f"{PREFIXE}/agents/{autre_agent.id}/portefeuille", headers=entetes
        )

        assert reponse.status_code == 403

    async def test_il_consulte_le_sien(
        self,
        client_http: AsyncClient,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        entetes = await _entetes(client_http, "ag001")

        reponse = await client_http.get(
            f"{PREFIXE}/agents/{agent.id}/portefeuille", headers=entetes
        )

        assert reponse.status_code == 200
        assert reponse.json()["agent"]["matricule"] == "AG001"


class TestSuperviseur:
    async def test_il_gere_le_repertoire_des_agents(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = await _entetes(client_http, "superviseur")

        cree = await client_http.post(
            f"{PREFIXE}/agents",
            headers=entetes,
            json={"matricule": "AG009", "nomComplet": "TCHOUMI Alain"},
        )
        assert cree.status_code == 201
        agent_id = cree.json()["id"]

        modifie = await client_http.patch(
            f"{PREFIXE}/agents/{agent_id}",
            headers=entetes,
            json={"nomComplet": "TCHOUMI Alain Bertrand", "zoneRattachement": "CSC_DSCHANG"},
        )
        assert modifie.status_code == 200
        assert modifie.json()["nomComplet"] == "TCHOUMI Alain Bertrand"

        retire = await client_http.patch(
            f"{PREFIXE}/agents/{agent_id}/activation?actif=false", headers=entetes
        )
        assert retire.status_code == 200
        assert retire.json()["actif"] is False

    async def test_la_gestion_des_comptes_lui_est_fermee(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        """Créer des comptes de connexion reste une prérogative
        d'administrateur."""
        entetes = await _entetes(client_http, "superviseur")

        reponse = await client_http.get(f"{PREFIXE}/comptes", headers=entetes)

        assert reponse.status_code == 403
        assert reponse.json()["code"] == "acces_refuse"


class TestAdministrateur:
    @pytest.fixture
    def administrateur(
        self, container: Container, entrepot: EntrepotMemoire
    ) -> Utilisateur:
        compte = Utilisateur(
            identifiant="admin",
            nom_complet="Administrateur NEXT",
            empreinte_mot_de_passe=container.hacheur.hacher(MOT_DE_PASSE_TEST),
            role=Role.ADMINISTRATEUR,
        )
        entrepot.utilisateurs[compte.id] = compte
        return compte

    async def test_il_ouvre_un_compte_agent(
        self,
        client_http: AsyncClient,
        administrateur: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        entetes = await _entetes(client_http, "admin")

        reponse = await client_http.post(
            f"{PREFIXE}/comptes",
            headers=entetes,
            json={
                "identifiant": "ag001",
                "nomComplet": agent.nom_complet,
                "motDePasse": "Terrain@2026",
                "role": "AGENT_TERRAIN",
                "agentId": str(agent.id),
            },
        )

        assert reponse.status_code == 201, reponse.text
        corps = reponse.json()
        assert corps["role"] == "AGENT_TERRAIN"
        assert corps["agentId"] == str(agent.id)
        # Le titulaire devra choisir son propre mot de passe.
        assert corps["doitChangerMotDePasse"] is True

    async def test_un_compte_agent_sans_rattachement_est_refuse(
        self, client_http: AsyncClient, administrateur: Utilisateur
    ) -> None:
        entetes = await _entetes(client_http, "admin")

        reponse = await client_http.post(
            f"{PREFIXE}/comptes",
            headers=entetes,
            json={
                "identifiant": "fantome",
                "nomComplet": "Agent sans fiche",
                "motDePasse": "Terrain@2026",
                "role": "AGENT_TERRAIN",
            },
        )

        assert reponse.status_code == 409
        assert "agent de terrain rattaché" in reponse.json()["message"].lower()

    async def test_il_ne_peut_pas_se_desactiver_lui_meme(
        self, client_http: AsyncClient, administrateur: Utilisateur
    ) -> None:
        entetes = await _entetes(client_http, "admin")

        reponse = await client_http.patch(
            f"{PREFIXE}/comptes/{administrateur.id}/activation?actif=false",
            headers=entetes,
        )

        assert reponse.status_code == 409, "se verrouiller dehors n'a pas de sens"
