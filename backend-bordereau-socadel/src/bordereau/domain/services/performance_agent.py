"""Service de domaine : calcul de la performance déclarée d'un agent.

Ces agrégats alimentent les KPI du tableau de bord et, à terme, le calcul de
rémunération. Ils sont volontairement calculés sur des entités en mémoire :
les repositories peuvent produire les mêmes chiffres en SQL pour les grands
volumes, mais cette implémentation reste la définition de référence, testable
sans base de données.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..entities import LigneBordereau
from ..enums import StatutCollecte, VerdictVerification


@dataclass(frozen=True, slots=True)
class PerformanceAgent:
    """Photographie chiffrée du travail d'un agent sur une période."""

    lignes_affectees: int
    lignes_traitees: int
    abonnements_declares: int
    abonnements_confirmes: int
    abonnements_infirmes: int
    lignes_en_attente_de_verification: int

    @property
    def taux_traitement(self) -> float:
        """Part du portefeuille effectivement démarché."""
        if self.lignes_affectees == 0:
            return 0.0
        return self.lignes_traitees / self.lignes_affectees

    @property
    def taux_conversion(self) -> float:
        """Part des visites transformées en abonnement déclaré."""
        if self.lignes_traitees == 0:
            return 0.0
        return self.abonnements_declares / self.lignes_traitees

    @property
    def taux_fiabilite(self) -> float:
        """Part des abonnements déclarés que le référentiel confirme.

        C'est l'indicateur anti-fraude : un agent au fort volume mais à la
        fiabilité basse déclare des abonnements qui ne se matérialisent pas.
        Les lignes encore non vérifiées sont exclues du dénominateur pour ne
        pas pénaliser un agent en attente de recoupement.
        """
        verifiees = self.abonnements_confirmes + self.abonnements_infirmes
        if verifiees == 0:
            return 0.0
        return self.abonnements_confirmes / verifiees


def calculer(lignes: Iterable[LigneBordereau]) -> PerformanceAgent:
    """Agrège une collection de lignes de bordereau en indicateurs."""
    affectees = traitees = declares = confirmes = infirmes = en_attente = 0

    for ligne in lignes:
        affectees += 1
        if ligne.est_traitee:
            traitees += 1
        if ligne.statut is StatutCollecte.ABONNE:
            declares += 1
            match ligne.verdict:
                case VerdictVerification.CONFIRME:
                    confirmes += 1
                case VerdictVerification.INFIRME | VerdictVerification.INTROUVABLE:
                    infirmes += 1
                case VerdictVerification.NON_VERIFIE:
                    en_attente += 1

    return PerformanceAgent(
        lignes_affectees=affectees,
        lignes_traitees=traitees,
        abonnements_declares=declares,
        abonnements_confirmes=confirmes,
        abonnements_infirmes=infirmes,
        lignes_en_attente_de_verification=en_attente,
    )
