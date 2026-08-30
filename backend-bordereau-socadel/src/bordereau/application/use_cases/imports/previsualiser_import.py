"""Cas d'usage : analyse à blanc d'un fichier déposé.

Premier temps du flux d'import voulu par le métier : rien n'est écrit en base,
le superviseur voit dans un modal ce qui *serait* importé, avec les anomalies
détectées, et décide ensuite de valider ou d'abandonner.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...dto import ApercuImport
from ...errors import ImportInvalide
from ...ports import LecteurTabulaire

#: Au-delà, le fichier est refusé avant même d'être analysé.
TAILLE_MAX_OCTETS = 25 * 1024 * 1024

EXTENSIONS_ACCEPTEES = (".xlsx", ".xls", ".csv")


@dataclass(frozen=True, slots=True)
class CommandeApercu:
    nom_fichier: str
    contenu: bytes
    taille_apercu: int = 20


class PrevisualiserImport:
    """Analyse un fichier et produit l'aperçu affiché avant validation."""

    def __init__(self, lecteur: LecteurTabulaire) -> None:
        self._lecteur = lecteur

    def executer(self, commande: CommandeApercu) -> ApercuImport:
        """Contrôle le contenant, puis délègue l'analyse du contenu.

        Raises:
            ImportInvalide: fichier vide, trop volumineux ou d'un format non
                pris en charge.
        """
        if not commande.contenu:
            raise ImportInvalide("Le fichier déposé est vide")

        if len(commande.contenu) > TAILLE_MAX_OCTETS:
            taille_mo = TAILLE_MAX_OCTETS / (1024 * 1024)
            raise ImportInvalide(
                f"Fichier trop volumineux : la limite est de {taille_mo:.0f} Mo"
            )

        nom = commande.nom_fichier.lower()
        if not nom.endswith(EXTENSIONS_ACCEPTEES):
            formats = ", ".join(EXTENSIONS_ACCEPTEES)
            raise ImportInvalide(f"Format non pris en charge. Attendu : {formats}")

        return self._lecteur.analyser(
            commande.contenu,
            commande.nom_fichier,
            taille_apercu=commande.taille_apercu,
        )
