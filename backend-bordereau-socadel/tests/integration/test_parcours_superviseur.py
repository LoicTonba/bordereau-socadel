"""Parcours complet du superviseur, à travers l'API HTTP réelle.

Le conteneur est celui de production, à deux doubles près : l'unité de travail
(en mémoire au lieu de PostgreSQL) et l'horloge. Le hachage bcrypt, les jetons
JWT, la génération PDF et l'analyse des classeurs Excel sont les vrais
adaptateurs.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from bordereau.domain.entities import AgentTerrain, Client, Itineraire, Utilisateur
from bordereau.infrastructure.config.settings import Settings
from bordereau.infrastructure.container import Container
from bordereau.main import creer_application

from ..conftest import MOT_DE_PASSE_TEST

PREFIXE = "/api/v1"


@pytest.fixture
def app(settings: Settings, container: Container) -> FastAPI:
    application = creer_application(settings)
    # Le conteneur est posé directement : le cycle de vie de l'application
    # en construirait un branché sur PostgreSQL.
    application.state.container = container
    return application


@pytest.fixture
async def client_http(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def _connecter(client_http: AsyncClient) -> dict[str, str]:
    reponse = await client_http.post(
        f"{PREFIXE}/auth/connexion",
        json={"identifiant": "superviseur", "motDePasse": MOT_DE_PASSE_TEST},
    )
    assert reponse.status_code == 200, reponse.text
    return {"Authorization": f"Bearer {reponse.json()['jeton']}"}


class TestAuthentification:
    async def test_connexion_reussie(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        reponse = await client_http.post(
            f"{PREFIXE}/auth/connexion",
            json={"identifiant": "superviseur", "motDePasse": MOT_DE_PASSE_TEST},
        )

        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["identifiant"] == "superviseur"
        assert corps["role"] == "SUPERVISEUR"
        assert corps["jeton"]

    async def test_mot_de_passe_incorrect(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        reponse = await client_http.post(
            f"{PREFIXE}/auth/connexion",
            json={"identifiant": "superviseur", "motDePasse": "faux"},
        )
        assert reponse.status_code == 401
        assert reponse.json()["code"] == "identifiants_invalides"

    async def test_compte_inconnu_donne_le_meme_message(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        # Un message distinct révélerait quels comptes existent.
        reponse = await client_http.post(
            f"{PREFIXE}/auth/connexion",
            json={"identifiant": "inconnu", "motDePasse": MOT_DE_PASSE_TEST},
        )
        assert reponse.status_code == 401
        assert reponse.json()["message"] == "Identifiant ou mot de passe incorrect"

    async def test_acces_refuse_sans_jeton(self, client_http: AsyncClient) -> None:
        reponse = await client_http.get(f"{PREFIXE}/bordereau")
        assert reponse.status_code == 401


class TestParcoursComplet:
    async def test_du_briefing_a_la_verification(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        agent: AgentTerrain,
        itineraire: Itineraire,
        clients: list[Client],
        jour: date,
    ) -> None:
        """Déroule la journée type : affecter, saisir, vérifier, exporter."""
        entetes = await _connecter(client_http)

        # 1. Le superviseur confie l'itinéraire à l'agent.
        affectation = await client_http.post(
            f"{PREFIXE}/itineraires/affectations",
            headers=entetes,
            json={
                "agentId": str(agent.id),
                "codesItineraires": [itineraire.code.valeur],
                "dateTravail": jour.isoformat(),
                "consignes": "Commencer par le quartier haut.",
            },
        )
        assert affectation.status_code == 201, affectation.text
        assert affectation.json()["totalLignes"] == 3, (
            "une ligne de bordereau par client de l'itinéraire"
        )

        # 2. Le bordereau est matérialisé, prêt à la saisie.
        listing = await client_http.get(f"{PREFIXE}/bordereau", headers=entetes)
        assert listing.status_code == 200
        lignes = listing.json()["elements"]
        assert len(lignes) == 3
        assert all(ligne["statut"] == "A_TRAITER" for ligne in lignes)

        # Les lignes suivent l'ordre de marche, pas l'ordre de la base.
        assert [ligne["refGeo"] for ligne in lignes] == [
            "200-20-11-349-00-011",
            "960-20-11-067-00-011",
            "960-20-11-078-00-011",
        ]

        # 3. Saisie au retour du terrain : un abonnement, un absent.
        abonne = next(l for l in lignes if l["serviceNo"] == "203401046")
        declaration = await client_http.patch(
            f"{PREFIXE}/bordereau/{abonne['id']}",
            headers=entetes,
            json={
                "statut": "ABONNE",
                "numeroCollecte": "677398710",
                "responsable": "TERRAIN",
            },
        )
        assert declaration.status_code == 200, declaration.text
        assert declaration.json()["numeroCollecte"] == "+237677398710", (
            "le numéro saisi sans indicatif est normalisé"
        )

        absent = next(l for l in lignes if l["serviceNo"] == "203846816")
        await client_http.patch(
            f"{PREFIXE}/bordereau/{absent['id']}",
            headers=entetes,
            json={"statut": "ABSENT"},
        )

        # 4. Confrontation au référentiel SOCADEL.
        verification = await client_http.post(
            f"{PREFIXE}/bordereau/verification", headers=entetes
        )
        assert verification.status_code == 200, verification.text
        rapport = verification.json()
        assert rapport["lignesExaminees"] == 2
        assert rapport["confirmees"] == 2, (
            "l'abonné est confirmé par le référentiel, l'absent aussi "
            "(le référentiel ne le voit pas abonné)"
        )

        # 5. La ligne confirmée devient payable.
        apres = await client_http.get(f"{PREFIXE}/bordereau", headers=entetes)
        ligne_abonne = next(
            l for l in apres.json()["elements"] if l["serviceNo"] == "203401046"
        )
        assert ligne_abonne["verdict"] == "CONFIRME"
        assert ligne_abonne["estRemuneree"] is True

    async def test_abonnement_declare_sans_numero_est_refuse(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        agent: AgentTerrain,
        itineraire: Itineraire,
        clients: list[Client],
        jour: date,
    ) -> None:
        entetes = await _connecter(client_http)
        await client_http.post(
            f"{PREFIXE}/itineraires/affectations",
            headers=entetes,
            json={
                "agentId": str(agent.id),
                "codesItineraires": [itineraire.code.valeur],
                "dateTravail": jour.isoformat(),
            },
        )
        lignes = (
            await client_http.get(f"{PREFIXE}/bordereau", headers=entetes)
        ).json()["elements"]

        reponse = await client_http.patch(
            f"{PREFIXE}/bordereau/{lignes[0]['id']}",
            headers=entetes,
            json={"statut": "ABONNE"},
        )

        assert reponse.status_code == 422
        assert reponse.json()["code"] == "regle_metier_violee"

    async def test_double_affectation_du_meme_itineraire_refusee(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        agent: AgentTerrain,
        itineraire: Itineraire,
        clients: list[Client],
        jour: date,
    ) -> None:
        entetes = await _connecter(client_http)
        corps = {
            "agentId": str(agent.id),
            "codesItineraires": [itineraire.code.valeur],
            "dateTravail": jour.isoformat(),
        }

        premiere = await client_http.post(
            f"{PREFIXE}/itineraires/affectations", headers=entetes, json=corps
        )
        assert premiere.status_code == 201

        seconde = await client_http.post(
            f"{PREFIXE}/itineraires/affectations", headers=entetes, json=corps
        )
        # Sinon la production de la journée serait comptée deux fois.
        assert seconde.status_code == 409
        assert seconde.json()["code"] == "conflit"


class TestFiltragePagination:
    async def test_le_filtre_par_statut_restreint_le_listing(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        agent: AgentTerrain,
        itineraire: Itineraire,
        clients: list[Client],
        jour: date,
    ) -> None:
        entetes = await _connecter(client_http)
        await client_http.post(
            f"{PREFIXE}/itineraires/affectations",
            headers=entetes,
            json={
                "agentId": str(agent.id),
                "codesItineraires": [itineraire.code.valeur],
                "dateTravail": jour.isoformat(),
            },
        )
        lignes = (
            await client_http.get(f"{PREFIXE}/bordereau", headers=entetes)
        ).json()["elements"]

        await client_http.patch(
            f"{PREFIXE}/bordereau/{lignes[0]['id']}",
            headers=entetes,
            json={"statut": "ABSENT"},
        )

        filtre = await client_http.get(
            f"{PREFIXE}/bordereau", headers=entetes, params={"statut": "ABSENT"}
        )
        assert filtre.json()["meta"]["total"] == 1

    async def test_la_pagination_expose_son_contexte(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        agent: AgentTerrain,
        itineraire: Itineraire,
        clients: list[Client],
        jour: date,
    ) -> None:
        entetes = await _connecter(client_http)
        await client_http.post(
            f"{PREFIXE}/itineraires/affectations",
            headers=entetes,
            json={
                "agentId": str(agent.id),
                "codesItineraires": [itineraire.code.valeur],
                "dateTravail": jour.isoformat(),
            },
        )

        page = await client_http.get(
            f"{PREFIXE}/bordereau", headers=entetes, params={"page": 1, "taille": 2}
        )
        meta = page.json()["meta"]

        assert meta["total"] == 3
        assert meta["nombreDePages"] == 2
        assert meta["aPageSuivante"] is True
        assert meta["aPagePrecedente"] is False
        assert len(page.json()["elements"]) == 2
