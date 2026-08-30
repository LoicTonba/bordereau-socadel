"""Tests des objets-valeurs, sur des saisies réellement rencontrées."""

from __future__ import annotations

import pytest

from bordereau.domain.errors import ValidationError
from bordereau.domain.value_objects import (
    CodeItineraire,
    NumeroTelephone,
    RefGeo,
    ServiceNo,
)


class TestNumeroTelephone:
    @pytest.mark.parametrize(
        ("saisie", "attendu"),
        [
            ("+237694174768", "+237694174768"),
            ("694174768", "+237694174768"),
            ("237694174768", "+237694174768"),
            ("00237694174768", "+237694174768"),
            ("+237 677 66 68 82", "+237677666882"),
            ("+237-650-944-122", "+237650944122"),
        ],
    )
    def test_normalise_les_saisies_heterogenes(self, saisie: str, attendu: str) -> None:
        assert NumeroTelephone.parse(saisie).valeur == attendu

    @pytest.mark.parametrize("saisie", ["", None, "abc", "12345", "+33612345678"])
    def test_rejette_ce_qui_n_est_pas_un_numero_camerounais(self, saisie) -> None:
        with pytest.raises(ValidationError):
            NumeroTelephone.parse(saisie)

    def test_variante_tolerante_pour_les_imports_de_masse(self) -> None:
        # Un fichier de 400 000 lignes ne doit pas échouer en bloc sur une
        # saisie isolée.
        assert NumeroTelephone.parse_ou_none("n/a") is None

    def test_expose_la_forme_nationale(self) -> None:
        numero = NumeroTelephone.parse("+237694174768")
        assert numero.national == "694174768"
        assert numero.est_mobile


class TestServiceNo:
    def test_accepte_un_entier_venu_d_excel(self) -> None:
        assert ServiceNo.parse(201389431).valeur == "201389431"

    def test_retire_le_suffixe_flottant_d_excel(self) -> None:
        # openpyxl remonte volontiers les entiers longs sous forme de float.
        assert ServiceNo.parse("201389431.0").valeur == "201389431"

    def test_rejette_une_valeur_non_numerique(self) -> None:
        with pytest.raises(ValidationError):
            ServiceNo.parse("SANS OBJET")


class TestRefGeo:
    def test_expose_l_ordre_de_marche(self) -> None:
        ref = RefGeo.parse("807-09-01-994-00-001")
        assert ref.centre == "807"
        assert ref.cle_tri == (807, 9, 1, 994, 0, 1)

    def test_l_ordre_de_marche_suit_le_parcours_physique(self) -> None:
        refs = [
            RefGeo.parse("960-20-11-232-00-011"),
            RefGeo.parse("960-20-11-078-00-011"),
            RefGeo.parse("960-20-11-092-00-011"),
        ]
        ordonnees = [r.valeur for r in sorted(refs, key=lambda r: r.cle_tri)]
        assert ordonnees == [
            "960-20-11-078-00-011",
            "960-20-11-092-00-011",
            "960-20-11-232-00-011",
        ]

    def test_rejette_une_reference_malformee(self) -> None:
        with pytest.raises(ValidationError):
            RefGeo.parse("807/09/01")


class TestCodeItineraire:
    def test_accepte_les_formes_rencontrees(self) -> None:
        assert CodeItineraire.parse("131227").valeur == 131227
        assert CodeItineraire.parse(130387.0).valeur == 130387

    def test_rejette_un_code_nul_ou_negatif(self) -> None:
        with pytest.raises(ValidationError):
            CodeItineraire(0)
