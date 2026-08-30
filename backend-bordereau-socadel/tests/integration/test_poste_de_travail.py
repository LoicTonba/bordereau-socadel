"""La connexion déclare un profil et une agence, et la déclaration est vérifiée.

L'écran de connexion demande d'abord « qui êtes-vous » et « où êtes-vous »,
avant les identifiants. Ces deux réponses ne sont pas des droits : ce sont des
déclarations, confrontées au compte. Ces tests fixent ce contrat, notamment
qu'aucune des deux ne permet d'élargir quoi que ce soit.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from bordereau.domain.entities import Utilisateur
from bordereau.infrastructure.config.settings import Settings
from bordereau.infrastructure.container import Container
from bordereau.main import creer_application

from ..conftest import MOT_DE_PASSE_TEST

pytestmark = pytest.mark.anyio

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


async def _connexion(client_http: AsyncClient, **champs: object):
    corps: dict[str, object] = {
        "identifiant": "superviseur",
        "motDePasse": MOT_DE_PASSE_TEST,
    }
    corps.update(champs)
    return await client_http.post(f"{PREFIXE}/auth/connexion", json=corps)


class TestProfilDeclare:
    async def test_le_bon_profil_ouvre_la_session(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        reponse = await _connexion(client_http, role="SUPERVISEUR")

        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["role"] == "SUPERVISEUR"

    async def test_un_profil_trop_haut_est_refuse(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        """Se déclarer administrateur ne rend pas administrateur.

        Le contrôle est de confort, le jeton porterait de toute façon le rôle
        réel ; il évite surtout qu'un utilisateur croie être ailleurs qu'il
        n'est.
        """
        reponse = await _connexion(client_http, role="ADMINISTRATEUR")

        assert reponse.status_code == 409
        assert "superviseur" in reponse.json()["message"].lower()

    async def test_le_profil_reste_facultatif(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        """Un client qui ne déclare rien, un script d'intégration par exemple,
        se connecte comme avant."""
        reponse = await _connexion(client_http)

        assert reponse.status_code == 200


class TestAgenceDeclaree:
    async def test_son_agence_est_retenue_pour_la_session(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        reponse = await _connexion(
            client_http, role="SUPERVISEUR", agence="CSC_NGAOUNDERE SUD"
        )

        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["agence"] == "CSC_NGAOUNDERE SUD"

    async def test_une_autre_agence_est_refusee(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        """Un superviseur rattaché à Ngaoundéré Sud n'ouvre pas sa session à
        Kribi : c'est le signe d'une erreur de saisie, ou d'un compte utilisé
        par quelqu'un d'autre."""
        reponse = await _connexion(
            client_http, role="SUPERVISEUR", agence="CSC_KRIBI"
        )

        assert reponse.status_code == 409
        assert "CSC_NGAOUNDERE SUD" in reponse.json()["message"]

    async def test_sans_declaration_l_agence_du_compte_est_renvoyee(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        reponse = await _connexion(client_http)

        assert reponse.json()["agence"] == "CSC_NGAOUNDERE SUD"

    async def test_le_mot_de_passe_prime_sur_la_declaration(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        """Une déclaration incohérente ne doit pas devenir un oracle : tant que
        le mot de passe est faux, la réponse reste un 401 indifférencié."""
        reponse = await _connexion(
            client_http, motDePasse="faux", role="ADMINISTRATEUR"
        )

        assert reponse.status_code == 401
