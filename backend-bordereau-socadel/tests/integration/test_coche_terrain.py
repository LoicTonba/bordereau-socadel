"""Le geste du releveur, de bout en bout à travers l'API.

Sur le terrain, l'agent n'a qu'une chose à faire : cliquer dans la colonne
Check. La date s'inscrit d'elle-même, son nom part en Responsable, et le
statut bascule. Ces tests fixent ce contrat, et surtout ce qu'il refuse :
cocher la tournée d'un collègue, ou porter deux fois le même numéro sur un
même itinéraire.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from bordereau.domain.entities import AgentTerrain, LigneBordereau, Utilisateur
from bordereau.domain.enums import Role, StatutCompte
from bordereau.domain.value_objects import CodeItineraire, RefGeo, ServiceNo
from bordereau.infrastructure.config.settings import Settings
from bordereau.infrastructure.container import Container
from bordereau.main import creer_application

from ..conftest import MOT_DE_PASSE_TEST
from ..doubles import EntrepotMemoire

pytestmark = pytest.mark.anyio

PREFIXE = "/api/v1"
JOUR = date(2026, 8, 30)
ITINERAIRE = 125369


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
    compte = Utilisateur(
        identifiant="ag001",
        nom_complet=agent.nom_complet,
        email="ag001@socadel.cm",
        empreinte_mot_de_passe=container.hacheur.hacher(MOT_DE_PASSE_TEST),
        role=Role.AGENT_TERRAIN,
        statut=StatutCompte.ACTIF,
        agent_id=agent.id,
    )
    entrepot.utilisateurs[compte.id] = compte
    return compte


def _poser_ligne(
    entrepot: EntrepotMemoire, service_no: str, agent_id
) -> LigneBordereau:
    ligne = LigneBordereau(
        service_no=ServiceNo(service_no),
        date_collecte=JOUR,
        nom_client="OUMAROU NDEJAL",
        ref_geo=RefGeo("200-20-11-349-00-011"),
        code_itineraire=CodeItineraire(ITINERAIRE),
        numero_compteur="18127224",
        agent_id=agent_id,
    )
    entrepot.lignes[ligne.id] = ligne
    return ligne


async def _entetes(client_http: AsyncClient, identifiant: str) -> dict[str, str]:
    reponse = await client_http.post(
        f"{PREFIXE}/auth/connexion",
        json={"identifiant": identifiant, "motDePasse": MOT_DE_PASSE_TEST},
    )
    assert reponse.status_code == 200, reponse.text
    return {"Authorization": f"Bearer {reponse.json()['jeton']}"}


class TestUnClicSuffit:
    async def test_cocher_renseigne_tout_le_reste(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        ligne = _poser_ligne(entrepot, "203401046", agent.id)
        entetes = await _entetes(client_http, "ag001")

        reponse = await client_http.post(
            f"{PREFIXE}/bordereau/{ligne.id}/coche",
            json={"rapport": "OK", "numeroCollecte": "677398710"},
            headers=entetes,
        )

        assert reponse.status_code == 200, reponse.text
        corps = reponse.json()
        assert corps["rapport"] == "OK"
        assert corps["verifieTerrain"] is True
        # La date de la colonne Check Date s'inscrit d'elle-meme.
        assert corps["verifieTerrainLe"] is not None
        assert corps["statut"] == "ABONNE"
        # La colonne Responsable porte le nom de celui qui a coche.
        assert corps["auteurAffiche"] == agent.nom_complet
        # Le back-office n'a pas encore controle : la colonne reste vide.
        assert corps["backOffice"] == "NON_VERIFIE"
        assert corps["backOfficeLe"] is None

    async def test_mra_prend_le_numero_sans_declarer_l_abonnement(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        """Hors couverture, l'agent releve le numero et MRA relancera."""
        ligne = _poser_ligne(entrepot, "203401047", agent.id)
        entetes = await _entetes(client_http, "ag001")

        reponse = await client_http.post(
            f"{PREFIXE}/bordereau/{ligne.id}/coche",
            json={"rapport": "MRA", "numeroCollecte": "699112233"},
            headers=entetes,
        )

        assert reponse.status_code == 200, reponse.text
        corps = reponse.json()
        assert corps["rapport"] == "MRA"
        # Rien n'est acquis : la ligne reste a traiter, sans responsable.
        assert corps["statut"] == "A_TRAITER"
        assert corps["auteurAffiche"] is None

    async def test_decocher_remet_la_ligne_a_traiter(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        ligne = _poser_ligne(entrepot, "203401048", agent.id)
        entetes = await _entetes(client_http, "ag001")
        await client_http.post(
            f"{PREFIXE}/bordereau/{ligne.id}/coche",
            json={"rapport": "OK", "numeroCollecte": "677398711"},
            headers=entetes,
        )

        reponse = await client_http.delete(
            f"{PREFIXE}/bordereau/{ligne.id}/coche", headers=entetes
        )

        assert reponse.status_code == 200, reponse.text
        corps = reponse.json()
        assert corps["verifieTerrain"] is False
        assert corps["statut"] == "A_TRAITER"


class TestCeQueLeCocheRefuse:
    async def test_un_meme_numero_ne_sert_pas_deux_contrats_du_meme_itineraire(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        """Le contournement le plus simple : porter son propre numero partout."""
        premiere = _poser_ligne(entrepot, "203401046", agent.id)
        seconde = _poser_ligne(entrepot, "203401047", agent.id)
        entetes = await _entetes(client_http, "ag001")

        await client_http.post(
            f"{PREFIXE}/bordereau/{premiere.id}/coche",
            json={"rapport": "OK", "numeroCollecte": "677398710"},
            headers=entetes,
        )
        refus = await client_http.post(
            f"{PREFIXE}/bordereau/{seconde.id}/coche",
            json={"rapport": "OK", "numeroCollecte": "677398710"},
            headers=entetes,
        )

        assert refus.status_code == 409, refus.text
        # Le refus nomme le contrat deja servi : la correction ne demande
        # aucune enquete.
        assert "203401046" in refus.text

    async def test_l_agent_ne_coche_pas_la_tournee_d_un_collegue(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
    ) -> None:
        ligne = _poser_ligne(entrepot, "203401049", uuid4())
        entetes = await _entetes(client_http, "ag001")

        refus = await client_http.post(
            f"{PREFIXE}/bordereau/{ligne.id}/coche",
            json={"rapport": "OK", "numeroCollecte": "677398712"},
            headers=entetes,
        )

        assert refus.status_code == 403, refus.text

    async def test_un_ok_sans_numero_est_refuse(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        """Cocher OK affirme un abonnement : il faut le numero qui le prouve."""
        ligne = _poser_ligne(entrepot, "203401050", agent.id)
        entetes = await _entetes(client_http, "ag001")

        refus = await client_http.post(
            f"{PREFIXE}/bordereau/{ligne.id}/coche",
            json={"rapport": "OK"},
            headers=entetes,
        )

        assert refus.status_code == 422, refus.text


class TestRechercheParColonne:
    async def test_chaque_colonne_se_cherche_pour_elle_meme(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        _poser_ligne(entrepot, "203401046", agent.id)
        autre = _poser_ligne(entrepot, "999999999", agent.id)
        autre.nom_client = "NGONO Marie"
        entetes = await _entetes(client_http, "ag001")

        reponse = await client_http.get(
            f"{PREFIXE}/bordereau",
            params={"nomClient": "ngono"},
            headers=entetes,
        )

        assert reponse.status_code == 200, reponse.text
        elements = reponse.json()["elements"]
        assert [e["serviceNo"] for e in elements] == ["999999999"]

    async def test_une_ligne_decochee_ne_bloque_plus_le_numero(
        self,
        client_http: AsyncClient,
        entrepot: EntrepotMemoire,
        compte_agent: Utilisateur,
        agent: AgentTerrain,
    ) -> None:
        """Le releveur qui s'est trompé de contrat doit pouvoir se corriger.

        Décocher laisse le numéro sur la ligne — il a bien été relevé — mais
        cette ligne n'affirme plus rien. Continuer à bloquer sur elle
        interdirait la correction que le décoche vient précisément d'amorcer.
        """
        mauvaise = _poser_ligne(entrepot, "203401046", agent.id)
        bonne = _poser_ligne(entrepot, "203401047", agent.id)
        entetes = await _entetes(client_http, "ag001")

        await client_http.post(
            f"{PREFIXE}/bordereau/{mauvaise.id}/coche",
            json={"rapport": "OK", "numeroCollecte": "677398710"},
            headers=entetes,
        )
        await client_http.delete(
            f"{PREFIXE}/bordereau/{mauvaise.id}/coche", headers=entetes
        )

        reprise = await client_http.post(
            f"{PREFIXE}/bordereau/{bonne.id}/coche",
            json={"rapport": "OK", "numeroCollecte": "677398710"},
            headers=entetes,
        )

        assert reprise.status_code == 200, reprise.text
