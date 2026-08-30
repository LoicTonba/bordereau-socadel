"""Fixtures partagées : conteneur câblé sur les doubles, jeu de données réel."""

from __future__ import annotations

from datetime import date

import pytest

from bordereau.domain.entities import AgentTerrain, Client, Itineraire, Utilisateur
from bordereau.domain.enums import CategorieClient, WhatsappStatus
from bordereau.domain.value_objects import (
    CodeItineraire,
    NumeroTelephone,
    RefGeo,
    ServiceNo,
)
from bordereau.infrastructure.config.settings import Settings
from bordereau.infrastructure.container import Container

from .doubles import EntrepotMemoire, HorlogeFigee, UnitOfWorkMemoire

MOT_DE_PASSE_TEST = "Socadel@2026"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        secret_key="cle-de-test-suffisamment-longue-pour-signer-1234",
        environnement="test",
        # Le moteur n'est jamais sollicité : les doubles court-circuitent la
        # persistance. Le DSN doit seulement être syntaxiquement valide.
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
    )


@pytest.fixture
def entrepot() -> EntrepotMemoire:
    return EntrepotMemoire()


@pytest.fixture
def horloge() -> HorlogeFigee:
    return HorlogeFigee()


@pytest.fixture
def container(
    settings: Settings, entrepot: EntrepotMemoire, horloge: HorlogeFigee
) -> Container:
    """Conteneur réel, dont seuls l'unité de travail et l'horloge sont doublés.

    Tout le reste — hacheur bcrypt, jetons JWT, exportateurs PDF et CSV — est
    l'implémentation de production : ce sont bien les vrais adaptateurs qui
    sont exercés.
    """
    conteneur = Container(settings)
    conteneur.unit_of_work = lambda: UnitOfWorkMemoire(entrepot)  # type: ignore[method-assign]
    conteneur.__dict__["horloge"] = horloge
    return conteneur


@pytest.fixture
def superviseur(container: Container, entrepot: EntrepotMemoire) -> Utilisateur:
    utilisateur = Utilisateur(
        identifiant="superviseur",
        nom_complet="Superviseur SOCADEL",
        empreinte_mot_de_passe=container.hacheur.hacher(MOT_DE_PASSE_TEST),
    )
    entrepot.utilisateurs[utilisateur.id] = utilisateur
    return utilisateur


@pytest.fixture
def agent(entrepot: EntrepotMemoire) -> AgentTerrain:
    collecteur = AgentTerrain(
        matricule="AG001",
        nom_complet="MBALLA Jean Pierre",
        telephone=NumeroTelephone.parse("+237677123456"),
        zone_rattachement="CSC_NSAM",
    )
    entrepot.agents[collecteur.id] = collecteur
    return collecteur


@pytest.fixture
def itineraire(entrepot: EntrepotMemoire) -> Itineraire:
    """Itinéraire calqué sur une tournée réelle du référentiel."""
    tournee = Itineraire(
        code=CodeItineraire(130387),
        libelle="CSC_NGAOUNDERE SUD — 130387",
        region="DRNEA",
        division="DLP ADAMAOUA",
        agence="CSC_NGAOUNDERE SUD",
        mrc="MRC_ADAMAOUA",
        nombre_clients=3,
    )
    entrepot.itineraires[tournee.code.valeur] = tournee
    return tournee


@pytest.fixture
def clients(entrepot: EntrepotMemoire, itineraire: Itineraire) -> list[Client]:
    """Trois clients repris tels quels de `bordereau2.xlsx`.

    Le premier est déjà abonné côté référentiel, les deux autres non : de quoi
    exercer les trois verdicts de vérification.
    """
    donnees = [
        ("203401046", "OUMAROU NDEJAL", "200-20-11-349-00-011", "18127224",
         "+237677398710", WhatsappStatus.SUBSCRIBED),
        ("203846816", "MAHMOUDOU YAYA", "960-20-11-067-00-011", "21330810",
         "+237674242424", WhatsappStatus.NOT_CHECKED),
        ("201783766", "BELLO HENRI", "960-20-11-078-00-011", "12026523",
         "+237697096625", WhatsappStatus.INVALID),
    ]

    crees: list[Client] = []
    for service_no, nom, ref_geo, compteur, telephone, statut in donnees:
        client = Client(
            service_no=ServiceNo(service_no),
            nom=nom,
            ref_geo=RefGeo(ref_geo),
            code_itineraire=itineraire.code,
            telephone=NumeroTelephone.parse(telephone),
            numero_compteur=compteur,
            region="DRNEA",
            division="DLP ADAMAOUA",
            agence="CSC_NGAOUNDERE SUD",
            mrc="MRC_ADAMAOUA",
            categorie=CategorieClient.BT,
            whatsapp_status=statut,
        )
        entrepot.clients[client.id] = client
        crees.append(client)

    return crees


@pytest.fixture
def jour() -> date:
    return date(2026, 8, 30)
