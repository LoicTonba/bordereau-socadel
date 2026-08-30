"""DTO du flux d'import : prévisualisation puis validation.

Le métier impose deux temps — *« avoir un modal de preview de data d'abord,
ensuite valider l'import »*. Ces objets portent ce contrat : `ApercuImport`
est le résultat de l'analyse à blanc, `ResultatImport` celui de l'écriture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AnomalieImport:
    """Problème détecté sur une ligne du fichier déposé."""

    ligne: int
    """Numéro de ligne dans le fichier source, en-tête comprise (1-indexé)."""

    colonne: str | None
    message: str
    valeur: str | None = None
    bloquante: bool = True
    """Une anomalie bloquante empêche l'insertion de la ligne ; une anomalie
    non bloquante (numéro absent, observation vide) la laisse passer."""


@dataclass(frozen=True, slots=True)
class LigneApercu:
    """Ligne normalisée telle qu'elle sera insérée, pour affichage dans le modal."""

    ligne: int
    valeurs: dict[str, Any]
    anomalies: tuple[AnomalieImport, ...] = ()

    @property
    def est_importable(self) -> bool:
        return not any(a.bloquante for a in self.anomalies)


@dataclass(frozen=True, slots=True)
class ApercuImport:
    """Résultat de l'analyse à blanc d'un fichier déposé.

    Rien n'a encore été écrit en base : le superviseur valide sur la foi de cet
    aperçu, et le jeton `reference` sert alors à rejouer l'import sur le fichier
    exact qui a été prévisualisé.
    """

    reference: str
    nom_fichier: str
    colonnes_detectees: tuple[str, ...]
    total_lignes: int
    lignes_valides: int
    lignes_rejetees: int
    apercu: tuple[LigneApercu, ...]
    """Échantillon de tête, borné pour ne pas transporter tout le fichier."""

    anomalies: tuple[AnomalieImport, ...] = ()
    colonnes_manquantes: tuple[str, ...] = ()

    @property
    def est_valide(self) -> bool:
        """Un fichier est importable s'il a la bonne structure et au moins une
        ligne exploitable."""
        return not self.colonnes_manquantes and self.lignes_valides > 0


@dataclass(slots=True)
class ResultatImport:
    """Bilan de l'import effectivement appliqué."""

    reference: str
    lignes_creees: int = 0
    lignes_mises_a_jour: int = 0
    lignes_ignorees: int = 0
    anomalies: list[AnomalieImport] = field(default_factory=list)

    @property
    def total_traite(self) -> int:
        return self.lignes_creees + self.lignes_mises_a_jour
