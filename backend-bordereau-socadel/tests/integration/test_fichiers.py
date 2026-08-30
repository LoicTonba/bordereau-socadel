"""Tests des adaptateurs fichiers : modèle, import, exports CSV et PDF.

Ce sont les vrais générateurs qui sont exercés — openpyxl et reportlab — et le
classeur produit par le modèle est relu par le lecteur d'import : la boucle
« je télécharge le modèle, je le remplis, je le réimporte » est vérifiée de
bout en bout.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO

import openpyxl
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from bordereau.domain.entities import Client, LigneBordereau, Utilisateur
from bordereau.domain.enums import Responsable, StatutCollecte
from bordereau.domain.value_objects import (
    CodeItineraire,
    NumeroTelephone,
    RefGeo,
    ServiceNo,
)
from bordereau.infrastructure.config.settings import Settings
from bordereau.infrastructure.container import Container
from bordereau.infrastructure.files.exporters.csv_exporter import (
    ExportateurCsvStandard,
)
from bordereau.infrastructure.files.exporters.modele_import import (
    GenerateurModeleXlsx,
)
from bordereau.infrastructure.files.exporters.pdf_exporter import (
    ExportateurPdfReportlab,
)
from bordereau.infrastructure.files.parsers.tabulaire import LecteurTabulaireOpenpyxl
from bordereau.main import creer_application

from ..conftest import MOT_DE_PASSE_TEST

INSTANT = datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc)
JOUR = date(2026, 8, 30)
PREFIXE = "/api/v1"


def _ligne_exemple() -> LigneBordereau:
    ligne = LigneBordereau(
        service_no=ServiceNo("203401046"),
        date_collecte=JOUR,
        nom_client="OUMAROU NDEJAL",
        ref_geo=RefGeo("200-20-11-349-00-011"),
        code_itineraire=CodeItineraire(130387),
        numero_compteur="18127224",
    )
    ligne.declarer(
        StatutCollecte.ABONNE,
        horodatage=INSTANT,
        numero_collecte=NumeroTelephone.parse("+237677398710"),
        responsable=Responsable.TERRAIN,
    )
    return ligne


class TestModeleImport:
    def test_le_modele_est_un_classeur_valide(self) -> None:
        contenu = GenerateurModeleXlsx().generer()
        classeur = openpyxl.load_workbook(BytesIO(contenu))

        entetes = [cellule.value for cellule in classeur.active[1]]
        assert entetes[0] == "SERVICE_NO"
        assert "NUMERO_TELEPHONE" in entetes
        assert "STATUT" in entetes

    def test_le_modele_rempli_est_relu_par_l_import(self) -> None:
        """La boucle complète : ce que le superviseur télécharge doit revenir.

        Le classeur ne contient aucune ligne de garniture : une seule ligne
        remplie doit donner exactement une ligne importable, sans rejet
        fantôme qui inquiéterait le superviseur.
        """
        contenu = GenerateurModeleXlsx().generer()
        classeur = openpyxl.load_workbook(BytesIO(contenu))
        feuille = classeur.active

        feuille["A2"] = "203401046"
        feuille["B2"] = "OUMAROU NDEJAL"
        feuille["C2"] = "200-20-11-349-00-011"
        feuille["D2"] = 130387
        feuille["E2"] = "18127224"
        feuille["F2"] = "+237677398710"
        feuille["G2"] = "ABONNE"

        rempli = BytesIO()
        classeur.save(rempli)

        apercu = LecteurTabulaireOpenpyxl().analyser(
            rempli.getvalue(), "bordereau-rempli.xlsx"
        )

        assert apercu.total_lignes == 1
        assert apercu.lignes_valides == 1
        assert apercu.lignes_rejetees == 0
        assert apercu.colonnes_manquantes == ()
        assert apercu.est_valide

        ligne = apercu.apercu[0]
        assert ligne.valeurs["service_no"] == "203401046"
        assert ligne.valeurs["statut"] == "ABONNE"
        assert ligne.valeurs["numero_collecte"] == "+237677398710"
        assert ligne.est_importable


class TestLecteurImport:
    def test_analyse_un_csv_a_point_virgule(self) -> None:
        csv = (
            "SERVICE_NO;NOMS;REF_GEO;ITINERAIRE;METER_NO;NUMERO_TELEPHONE;STATUT\n"
            "203401046;OUMAROU NDEJAL;200-20-11-349-00-011;130387;18127224;"
            "+237677398710;ABONNE\n"
            "203846816;MAHMOUDOU YAYA;960-20-11-067-00-011;130387;21330810;;ABSENT\n"
        ).encode("utf-8")

        apercu = LecteurTabulaireOpenpyxl().analyser(csv, "bordereau.csv")

        assert apercu.total_lignes == 2
        assert apercu.lignes_valides == 2
        assert apercu.lignes_rejetees == 0

    def test_signale_les_lignes_sans_contrat(self) -> None:
        csv = (
            "SERVICE_NO;NOMS;STATUT\n"
            "203401046;OUMAROU NDEJAL;ABONNE\n"
            ";NOM SANS CONTRAT;ABONNE\n"
        ).encode("utf-8")

        apercu = LecteurTabulaireOpenpyxl().analyser(csv, "bordereau.csv")

        assert apercu.lignes_valides == 1
        assert apercu.lignes_rejetees == 1
        bloquantes = [a for a in apercu.anomalies if a.bloquante]
        assert bloquantes[0].colonne == "SERVICE_NO"

    def test_accepte_les_en_tetes_du_referentiel(self) -> None:
        # Les fichiers circulent sous plusieurs variantes : NIS_RAD au lieu de
        # SERVICE_NO, FIRSTNAME au lieu de NOMS.
        csv = (
            "NIS_RAD;FIRSTNAME;NUM_ITIN;STATUT\n"
            "203401046;OUMAROU NDEJAL;130387;ABONNE\n"
        ).encode("utf-8")

        apercu = LecteurTabulaireOpenpyxl().analyser(csv, "referentiel.csv")

        assert apercu.lignes_valides == 1
        assert apercu.apercu[0].valeurs["service_no"] == "203401046"
        assert apercu.apercu[0].valeurs["nom_client"] == "OUMAROU NDEJAL"

    def test_gere_un_export_en_latin_1(self) -> None:
        csv = "SERVICE_NO;NOMS;STATUT\n203401046;SANGMÉLIMA;ABONNE\n".encode("latin-1")
        apercu = LecteurTabulaireOpenpyxl().analyser(csv, "bordereau.csv")
        assert apercu.apercu[0].valeurs["nom_client"] == "SANGMÉLIMA"


class TestExports:
    def test_le_csv_porte_le_bom_et_le_point_virgule(self) -> None:
        contenu = ExportateurCsvStandard().exporter_bordereau([_ligne_exemple()])

        # Sans BOM, Excel affiche les accents en mojibake.
        assert contenu.startswith(b"\xef\xbb\xbf")
        texte = contenu.decode("utf-8-sig")
        assert texte.splitlines()[0].startswith("SERVICE_NO;NOMS;")
        assert "+237677398710" in texte

    def test_l_export_pdf_produit_un_document_valide(self) -> None:
        contenu = ExportateurPdfReportlab().exporter_bordereau(
            [_ligne_exemple()], titre="Bordereau de collecte WhatsApp"
        )
        assert contenu.startswith(b"%PDF-")
        assert len(contenu) > 1000

    def test_le_bordereau_terrain_est_genere(self) -> None:
        clients = [
            Client(
                service_no=ServiceNo("203401046"),
                nom="OUMAROU NDEJAL",
                ref_geo=RefGeo("200-20-11-349-00-011"),
                code_itineraire=CodeItineraire(130387),
                numero_compteur="18127224",
            )
        ]

        contenu = ExportateurPdfReportlab().generer_template_terrain(
            clients,
            code_itineraire=130387,
            libelle_itineraire="CSC_NGAOUNDERE SUD",
            nom_agent="MBALLA Jean Pierre (AG001)",
            date_travail="30 / 08 / 2026",
        )

        assert contenu.startswith(b"%PDF-")
        assert len(contenu) > 1000

    def test_le_bordereau_terrain_pagine_les_grands_itineraires(self) -> None:
        # 60 clients : au-delà de 25 par page, le document doit se paginer
        # plutôt que de tasser les lignes.
        clients = [
            Client(
                service_no=ServiceNo(f"2034{numero:05d}"),
                nom=f"CLIENT {numero}",
                ref_geo=RefGeo(f"200-20-11-{numero:03d}-00-011"),
                code_itineraire=CodeItineraire(130387),
            )
            for numero in range(1, 61)
        ]

        contenu = ExportateurPdfReportlab().generer_template_terrain(
            clients,
            code_itineraire=130387,
            libelle_itineraire="CSC_NGAOUNDERE SUD",
            nom_agent="MBALLA Jean Pierre",
            date_travail="30 / 08 / 2026",
        )

        assert contenu.startswith(b"%PDF-")
        assert contenu.count(b"/Type /Page") >= 3 or contenu.count(b"/Page") >= 3


class TestFluxImportHttp:
    """Le flux en deux temps voulu par le métier : aperçu, puis validation."""

    @pytest.fixture
    def app(self, settings: Settings, container: Container) -> FastAPI:
        application = creer_application(settings)
        application.state.container = container
        return application

    @pytest.fixture
    async def client_http(self, app: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

    async def _entetes(self, client_http: AsyncClient) -> dict[str, str]:
        reponse = await client_http.post(
            f"{PREFIXE}/auth/connexion",
            json={"identifiant": "superviseur", "motDePasse": MOT_DE_PASSE_TEST},
        )
        return {"Authorization": f"Bearer {reponse.json()['jeton']}"}

    async def test_l_apercu_n_ecrit_rien(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        clients: list[Client],
    ) -> None:
        entetes = await self._entetes(client_http)
        csv = (
            "SERVICE_NO;NOMS;STATUT;NUMERO_TELEPHONE\n"
            "203401046;OUMAROU NDEJAL;ABONNE;+237677398710\n"
        ).encode("utf-8")

        apercu = await client_http.post(
            f"{PREFIXE}/imports/apercu",
            headers=entetes,
            files={"fichier": ("bordereau.csv", csv, "text/csv")},
        )
        assert apercu.status_code == 200, apercu.text
        assert apercu.json()["lignesValides"] == 1

        # Aucune ligne n'a été créée : seule la validation écrit.
        listing = await client_http.get(f"{PREFIXE}/bordereau", headers=entetes)
        assert listing.json()["meta"]["total"] == 0

    async def test_la_validation_ecrit_les_lignes(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        clients: list[Client],
    ) -> None:
        entetes = await self._entetes(client_http)
        csv = (
            "SERVICE_NO;NOMS;STATUT;NUMERO_TELEPHONE\n"
            "203401046;OUMAROU NDEJAL;ABONNE;+237677398710\n"
            "203846816;MAHMOUDOU YAYA;ABSENT;\n"
        ).encode("utf-8")

        resultat = await client_http.post(
            f"{PREFIXE}/imports",
            headers=entetes,
            files={"fichier": ("bordereau.csv", csv, "text/csv")},
            data={"date_collecte": JOUR.isoformat()},
        )

        assert resultat.status_code == 201, resultat.text
        assert resultat.json()["lignesCreees"] == 2

        lignes = (
            await client_http.get(f"{PREFIXE}/bordereau", headers=entetes)
        ).json()["elements"]
        assert len(lignes) == 2

        # Le numéro doit traverser tout le pipeline d'import : sans lui, la
        # ligne ABONNE serait refusée par le domaine et silencieusement perdue.
        abonne = next(l for l in lignes if l["serviceNo"] == "203401046")
        assert abonne["statut"] == "ABONNE"
        assert abonne["numeroCollecte"] == "+237677398710"

    async def test_un_format_non_pris_en_charge_est_refuse(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = await self._entetes(client_http)

        reponse = await client_http.post(
            f"{PREFIXE}/imports/apercu",
            headers=entetes,
            files={"fichier": ("notes.txt", b"contenu", "text/plain")},
        )

        assert reponse.status_code == 422
        assert reponse.json()["code"] == "import_invalide"

    async def test_le_modele_se_telecharge(
        self, client_http: AsyncClient, superviseur: Utilisateur
    ) -> None:
        entetes = await self._entetes(client_http)

        reponse = await client_http.get(f"{PREFIXE}/imports/modele", headers=entetes)

        assert reponse.status_code == 200
        assert "modele-bordereau-terrain-socadel.xlsx" in reponse.headers[
            "content-disposition"
        ]
        # Signature ZIP : un .xlsx est une archive.
        assert reponse.content.startswith(b"PK")

    async def test_l_export_csv_reprend_le_filtre_courant(
        self,
        client_http: AsyncClient,
        superviseur: Utilisateur,
        clients: list[Client],
    ) -> None:
        entetes = await self._entetes(client_http)
        csv = (
            "SERVICE_NO;NOMS;STATUT;NUMERO_TELEPHONE\n"
            "203401046;OUMAROU NDEJAL;ABONNE;+237677398710\n"
            "203846816;MAHMOUDOU YAYA;ABSENT;\n"
        ).encode("utf-8")
        await client_http.post(
            f"{PREFIXE}/imports",
            headers=entetes,
            files={"fichier": ("bordereau.csv", csv, "text/csv")},
            data={"date_collecte": JOUR.isoformat()},
        )

        export = await client_http.get(
            f"{PREFIXE}/exports/csv", headers=entetes, params={"statut": "ABONNE"}
        )

        assert export.status_code == 200
        assert export.headers["x-export-lignes"] == "1"
        texte = export.content.decode("utf-8-sig")
        assert "OUMAROU NDEJAL" in texte
        assert "MAHMOUDOU YAYA" not in texte
