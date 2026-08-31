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
from bordereau.domain.enums import Role, StatutCompte
from bordereau.infrastructure.config.settings import Settings
from bordereau.infrastructure.container import Container
from bordereau.main import creer_application

from ..conftest import MOT_DE_PASSE_TEST
from ..doubles import EntrepotMemoire

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


class TestExpirationDeSession:
    """L'expiration est tranchée par l'horloge injectée, et par elle seule.

    Deux autorités sur le temps, celle de la bibliothèque JWT et celle du
    domaine, finissaient par diverger : un jeton émis sous horloge figée était
    refusé dès que l'heure réelle dépassait sa date de validité, ce qui rendait
    la suite dépendante du jour où on la lançait.
    """

    async def test_un_jeton_reste_valable_selon_l_horloge_injectee(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = {"Authorization": f"Bearer {(await _connexion(client_http)).json()['jeton']}"}

        profil = await client_http.get(f"{PREFIXE}/auth/moi", headers=entetes)

        assert profil.status_code == 200, profil.text
        assert profil.json()["identifiant"] == "superviseur"

    async def test_un_jeton_falsifie_est_refuse(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        """Ne plus vérifier l'expiration dans la bibliothèque ne doit pas
        relâcher la vérification de signature."""
        jeton = (await _connexion(client_http)).json()["jeton"]
        falsifie = jeton[:-6] + ("a" if jeton[-1] != "a" else "b") * 6

        profil = await client_http.get(
            f"{PREFIXE}/auth/moi", headers={"Authorization": f"Bearer {falsifie}"}
        )

        assert profil.status_code == 401


class TestRepertoireDesItineraires:
    """Le superviseur ouvre et corrige ses tournées, mais ne casse rien.

    Deux règles tiennent ce répertoire : le code ne se modifie pas, parce que
    les affectations et les lignes de bordereau le portent, et une tournée déjà
    confiée ne se supprime plus, parce que la production y renvoie.
    """

    async def _entetes(self, client_http: AsyncClient) -> dict[str, str]:
        reponse = await _connexion(client_http)
        return {"Authorization": f"Bearer {reponse.json()['jeton']}"}

    async def test_il_ouvre_une_tournee(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = await self._entetes(client_http)

        reponse = await client_http.post(
            f"{PREFIXE}/itineraires",
            headers=entetes,
            json={"code": 990001, "libelle": "Lotissement Nord"},
        )

        assert reponse.status_code == 201, reponse.text
        corps = reponse.json()
        assert corps["code"] == 990001
        # Sans agence indiquée, la tournée hérite du périmètre du superviseur.
        assert corps["agence"] == "CSC_NGAOUNDERE SUD"

    async def test_un_code_deja_pris_est_refuse(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = await self._entetes(client_http)
        await client_http.post(
            f"{PREFIXE}/itineraires", headers=entetes, json={"code": 990002}
        )

        doublon = await client_http.post(
            f"{PREFIXE}/itineraires", headers=entetes, json={"code": 990002}
        )

        assert doublon.status_code == 409
        assert "existe déjà" in doublon.json()["message"]

    async def test_il_corrige_le_libelle(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = await self._entetes(client_http)
        await client_http.post(
            f"{PREFIXE}/itineraires",
            headers=entetes,
            json={"code": 990003, "libelle": "Zone provisoire"},
        )

        reponse = await client_http.patch(
            f"{PREFIXE}/itineraires/990003",
            headers=entetes,
            json={"code": 990003, "libelle": "Quartier Baladji"},
        )

        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["libelle"] == "Quartier Baladji"

    async def test_il_retire_une_tournee_jamais_confiee(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = await self._entetes(client_http)
        await client_http.post(
            f"{PREFIXE}/itineraires", headers=entetes, json={"code": 990004}
        )

        reponse = await client_http.delete(
            f"{PREFIXE}/itineraires/990004", headers=entetes
        )

        assert reponse.status_code == 204


@pytest.fixture
def administrateur(container: Container, entrepot: EntrepotMemoire) -> Utilisateur:
    """Un compte administrateur, seul habilité à toucher au maillage."""
    compte = Utilisateur(
        identifiant="admin",
        nom_complet="EYENGA Flore",
        email="flore.eyenga@socadel.cm",
        empreinte_mot_de_passe=container.hacheur.hacher(MOT_DE_PASSE_TEST),
        role=Role.ADMINISTRATEUR,
        statut=StatutCompte.ACTIF,
    )
    entrepot.utilisateurs[compte.id] = compte
    return compte


class TestMaillageTerritorial:
    """SOCADEL tient son réseau : ouvrir, corriger, fermer, rouvrir.

    Une agence fermée disparaît des listes de travail mais reste attachée à la
    production passée et aux comptes qui la portent. La supprimer n'est ouvert
    que tant que rien ne s'y rattache.
    """

    async def _entetes(self, client_http: AsyncClient) -> dict[str, str]:
        reponse = await client_http.post(
            f"{PREFIXE}/auth/connexion",
            json={"identifiant": "admin", "motDePasse": MOT_DE_PASSE_TEST},
        )
        assert reponse.status_code == 200, reponse.text
        return {"Authorization": f"Bearer {reponse.json()['jeton']}"}

    async def test_l_administrateur_ouvre_une_agence(
        self, client_http: AsyncClient, administrateur
    ) -> None:
        entetes = await self._entetes(client_http)

        reponse = await client_http.post(
            f"{PREFIXE}/territoire",
            headers=entetes,
            json={"nom": "csc_lotissement", "region": "drc", "division": "dpc bafia"},
        )

        assert reponse.status_code == 201, reponse.text
        corps = reponse.json()
        # Le nom est la clé métier : il est normalisé une fois pour toutes.
        assert corps["nom"] == "CSC_LOTISSEMENT"
        assert corps["ouverte"] is True

    async def test_fermer_exige_un_motif(
        self, client_http: AsyncClient, administrateur
    ) -> None:
        entetes = await self._entetes(client_http)
        await client_http.post(
            f"{PREFIXE}/territoire", headers=entetes, json={"nom": "CSC_KUMBO"}
        )

        reponse = await client_http.post(
            f"{PREFIXE}/territoire/CSC_KUMBO/fermeture",
            headers=entetes,
            json={"motif": "  "},
        )

        assert reponse.status_code == 422

    async def test_une_agence_fermee_quitte_le_selecteur_de_connexion(
        self, client_http: AsyncClient, administrateur
    ) -> None:
        """C'est tout l'intérêt du maillage : la fermeture prend effet le jour
        même, sans attendre un nouvel import du référentiel."""
        entetes = await self._entetes(client_http)
        await client_http.post(
            f"{PREFIXE}/territoire", headers=entetes, json={"nom": "CSC_NDOP"}
        )

        avant = await client_http.get(f"{PREFIXE}/reference/agences")
        assert "CSC_NDOP" in [a["nom"] for a in avant.json()["agences"]]

        await client_http.post(
            f"{PREFIXE}/territoire/CSC_NDOP/fermeture",
            headers=entetes,
            json={"motif": "Zone rendue inaccessible"},
        )

        apres = await client_http.get(f"{PREFIXE}/reference/agences")
        assert "CSC_NDOP" not in [a["nom"] for a in apres.json()["agences"]]

    async def test_le_superviseur_ne_touche_pas_au_maillage(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        """Il travaille dans une agence, il ne décide pas de leur existence."""
        jeton = (await _connexion(client_http)).json()["jeton"]

        reponse = await client_http.post(
            f"{PREFIXE}/territoire",
            headers={"Authorization": f"Bearer {jeton}"},
            json={"nom": "CSC_INVENTEE"},
        )

        assert reponse.status_code == 403
