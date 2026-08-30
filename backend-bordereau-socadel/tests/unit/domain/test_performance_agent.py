"""Tests de la performance agent.

Ce module fixe la **définition de référence** des indicateurs. Le modèle de
lecture SQL (`infrastructure/db/repositories/analytics.py`) doit produire les
mêmes chiffres : c'est ici que se règle tout désaccord entre les deux.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from bordereau.domain.entities import LigneBordereau
from bordereau.domain.enums import StatutCollecte, VerdictVerification
from bordereau.domain.services import performance_agent
from bordereau.domain.value_objects import NumeroTelephone, ServiceNo

INSTANT = datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc)
JOUR = date(2026, 8, 30)


def _ligne(
    statut: StatutCollecte,
    verdict: VerdictVerification = VerdictVerification.NON_VERIFIE,
    service_no: str = "203401046",
) -> LigneBordereau:
    ligne = LigneBordereau(service_no=ServiceNo(service_no), date_collecte=JOUR)
    if statut is not StatutCollecte.A_TRAITER:
        ligne.declarer(
            statut,
            horodatage=INSTANT,
            numero_collecte=(
                NumeroTelephone.parse("+237677398710")
                if statut is StatutCollecte.ABONNE
                else None
            ),
        )
        if verdict is not VerdictVerification.NON_VERIFIE:
            ligne.appliquer_verdict(verdict, INSTANT)
    return ligne


class TestPerformanceAgent:
    def test_compte_les_lignes_par_categorie(self) -> None:
        perf = performance_agent.calculer(
            [
                _ligne(StatutCollecte.A_TRAITER, service_no="200000001"),
                _ligne(
                    StatutCollecte.ABONNE,
                    VerdictVerification.CONFIRME,
                    service_no="200000002",
                ),
                _ligne(
                    StatutCollecte.ABONNE,
                    VerdictVerification.INFIRME,
                    service_no="200000003",
                ),
                _ligne(StatutCollecte.ABSENT, service_no="200000004"),
            ]
        )

        assert perf.lignes_affectees == 4
        assert perf.lignes_traitees == 3
        assert perf.abonnements_declares == 2
        assert perf.abonnements_confirmes == 1
        assert perf.abonnements_infirmes == 1

    def test_une_ligne_absente_confirmee_n_est_pas_un_abonnement(self) -> None:
        """Le piège que le SQL avait manqué.

        Une ligne « absent » que le référentiel corrobore porte le verdict
        CONFIRME, mais ce n'est pas un abonnement : la compter comme tel
        gonflerait artificiellement la production et la fiabilité de l'agent.
        """
        perf = performance_agent.calculer(
            [
                _ligne(
                    StatutCollecte.ABSENT,
                    VerdictVerification.CONFIRME,
                    service_no="200000001",
                ),
                _ligne(
                    StatutCollecte.ABONNE,
                    VerdictVerification.INFIRME,
                    service_no="200000002",
                ),
            ]
        )

        assert perf.abonnements_declares == 1
        assert perf.abonnements_confirmes == 0
        assert perf.taux_fiabilite == 0.0, (
            "un abonnement déclaré et infirmé donne une fiabilité nulle, "
            "quel que soit le verdict des lignes non-abonnement"
        )

    def test_le_contrat_introuvable_compte_comme_infirme(self) -> None:
        perf = performance_agent.calculer(
            [_ligne(StatutCollecte.ABONNE, VerdictVerification.INTROUVABLE)]
        )
        assert perf.abonnements_infirmes == 1
        assert perf.taux_fiabilite == 0.0

    def test_les_lignes_non_verifiees_ne_penalisent_pas_la_fiabilite(self) -> None:
        """Un agent en attente de recoupement ne doit pas être noté à zéro."""
        perf = performance_agent.calculer(
            [
                _ligne(
                    StatutCollecte.ABONNE,
                    VerdictVerification.CONFIRME,
                    service_no="200000001",
                ),
                _ligne(StatutCollecte.ABONNE, service_no="200000002"),
            ]
        )

        assert perf.lignes_en_attente_de_verification == 1
        assert perf.taux_fiabilite == 1.0

    def test_les_taux_sont_nuls_sans_donnees(self) -> None:
        perf = performance_agent.calculer([])
        assert perf.taux_traitement == 0.0
        assert perf.taux_conversion == 0.0
        assert perf.taux_fiabilite == 0.0
