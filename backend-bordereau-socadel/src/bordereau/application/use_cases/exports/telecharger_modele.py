"""Cas d'usage : téléchargement du classeur vierge de saisie terrain.

Le superviseur distribue ce modèle aux agents ; les colonnes correspondent
exactement à celles que l'import sait relire, ce qui évite l'aller-retour
« fichier refusé, mauvais en-têtes ».
"""

from __future__ import annotations

from dataclasses import dataclass

from ...ports import GenerateurModeleImport


@dataclass(frozen=True, slots=True)
class ModeleTelecharge:
    contenu: bytes
    nom_fichier: str
    type_mime: str


class TelechargerModeleImport:
    """Sert le modèle de bordereau à remplir."""

    TYPE_MIME_XLSX = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    def __init__(self, generateur: GenerateurModeleImport) -> None:
        self._generateur = generateur

    def executer(self) -> ModeleTelecharge:
        return ModeleTelecharge(
            contenu=self._generateur.generer(),
            nom_fichier="modele-bordereau-terrain-socadel.xlsx",
            type_mime=self.TYPE_MIME_XLSX,
        )
