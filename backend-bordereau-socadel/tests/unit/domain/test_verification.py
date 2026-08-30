"""Tests de la règle qui départage l'agent et la source de vérité."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from bordereau.domain.entities import Client, LigneBordereau
from bordereau.domain.enums import StatutCollecte, VerdictVerification, WhatsappStatus
from bordereau.domain.errors import RegleMetierViolee
from bordereau.domain.services import verification_collecte
from bordereau.domain.value_objects import NumeroTelephone, ServiceNo

INSTANT = datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc)
JOUR = date(2026, 8, 30)


def _ligne(statut: StatutCollecte, numero: str | None = None) -> LigneBordereau:
    ligne = LigneBordereau(
        service_no=ServiceNo("203401046"),
        date_collecte=JOUR,
        nom_client="OUMAROU NDEJAL",
    )
    ligne.declarer(
        statut,
        horodatage=INSTANT,
        numero_collecte=NumeroTelephone.parse(numero) if numero else None,
    )
    return ligne


def _client(statut: WhatsappStatus, telephone: str = "+237677398710") -> Client:
    return Client(
        service_no=ServiceNo("203401046"),
        nom="OUMAROU NDEJAL",
        telephone=NumeroTelephone.parse(telephone),
        whatsapp_status=statut,
    )


class TestVerification:
    def test_abonnement_corrobore_par_le_referentiel(self) -> None:
        verdict = verification_collecte.verifier(
            _ligne(StatutCollecte.ABONNE, "+237677398710"),
            _client(WhatsappStatus.SUBSCRIBED),
        )
        assert verdict is VerdictVerification.CONFIRME

    def test_abonnement_declare_que_le_referentiel_ignore(self) -> None:
        # Cas central du dispositif anti-fraude : l'agent affirme un abonnement
        # que le chatbot WhatsApp n'a jamais enregistré.
        verdict = verification_collecte.verifier(
            _ligne(StatutCollecte.ABONNE, "+237677398710"),
            _client(WhatsappStatus.NOT_CHECKED),
        )
        assert verdict is VerdictVerification.INFIRME

    def test_abonnement_sur_un_autre_numero_que_celui_releve(self) -> None:
        verdict = verification_collecte.verifier(
            _ligne(StatutCollecte.ABONNE, "+237600000000"),
            _client(WhatsappStatus.SUBSCRIBED, telephone="+237677398710"),
        )
        assert verdict is VerdictVerification.INFIRME

    def test_non_abonnement_corrobore(self) -> None:
        verdict = verification_collecte.verifier(
            _ligne(StatutCollecte.NON_ABONNE),
            _client(WhatsappStatus.NOT_CHECKED),
        )
        assert verdict is VerdictVerification.CONFIRME

    def test_non_abonnement_contredit_par_le_referentiel(self) -> None:
        verdict = verification_collecte.verifier(
            _ligne(StatutCollecte.NON_ABONNE),
            _client(WhatsappStatus.SUBSCRIBED),
        )
        assert verdict is VerdictVerification.INFIRME

    def test_contrat_absent_du_referentiel(self) -> None:
        verdict = verification_collecte.verifier(
            _ligne(StatutCollecte.ABONNE, "+237677398710"), None
        )
        assert verdict is VerdictVerification.INTROUVABLE

    def test_ligne_non_declaree_reste_non_verifiee(self) -> None:
        ligne = LigneBordereau(service_no=ServiceNo("203401046"), date_collecte=JOUR)
        verdict = verification_collecte.verifier(
            ligne, _client(WhatsappStatus.SUBSCRIBED)
        )
        assert verdict is VerdictVerification.NON_VERIFIE


class TestRemuneration:
    def test_une_ligne_n_est_payable_que_si_elle_est_confirmee(self) -> None:
        ligne = _ligne(StatutCollecte.ABONNE, "+237677398710")
        assert not ligne.est_remuneree, "une déclaration seule ne suffit jamais"

        ligne.appliquer_verdict(VerdictVerification.CONFIRME, INSTANT)
        assert ligne.est_remuneree

    def test_une_nouvelle_declaration_invalide_le_verdict(self) -> None:
        ligne = _ligne(StatutCollecte.ABONNE, "+237677398710")
        ligne.appliquer_verdict(VerdictVerification.CONFIRME, INSTANT)

        ligne.declarer(StatutCollecte.ABSENT, horodatage=INSTANT)

        assert ligne.verdict is VerdictVerification.NON_VERIFIE
        assert not ligne.est_remuneree


class TestInvariants:
    def test_un_abonnement_exige_le_numero_collecte(self) -> None:
        ligne = LigneBordereau(service_no=ServiceNo("203401046"), date_collecte=JOUR)
        with pytest.raises(RegleMetierViolee, match="numéro collecté"):
            ligne.declarer(StatutCollecte.ABONNE, horodatage=INSTANT)

    def test_les_autres_statuts_n_exigent_pas_de_numero(self) -> None:
        ligne = LigneBordereau(service_no=ServiceNo("203401046"), date_collecte=JOUR)
        ligne.declarer(StatutCollecte.ABSENT, horodatage=INSTANT)
        assert ligne.statut is StatutCollecte.ABSENT
