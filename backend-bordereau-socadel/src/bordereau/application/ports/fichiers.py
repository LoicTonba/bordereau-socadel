"""Ports de manipulation de fichiers : lecture des imports, écriture des exports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from ...domain.entities import Client, LigneBordereau
from ..dto.imports import ApercuImport


@runtime_checkable
class LecteurTabulaire(Protocol):
    """Lit un classeur Excel ou un CSV déposé par le superviseur."""

    def analyser(
        self, contenu: bytes, nom_fichier: str, *, taille_apercu: int = 20
    ) -> ApercuImport:
        """Analyse le fichier **sans rien écrire**, pour alimenter le modal de
        prévisualisation."""
        ...

    def lire_lignes(
        self, contenu: bytes, nom_fichier: str
    ) -> Sequence[dict[str, Any]]:
        """Itère les lignes normalisées, une fois l'import validé."""
        ...


@runtime_checkable
class ExportateurCsv(Protocol):
    """Sérialise le tableau courant en CSV."""

    def exporter_bordereau(self, lignes: Sequence[LigneBordereau]) -> bytes: ...


@runtime_checkable
class ExportateurPdf(Protocol):
    """Produit les deux documents PDF du métier.

    Le premier est un export de consultation (ce que le superviseur voit à
    l'écran) ; le second est le **template de travail** que l'agent imprime et
    emporte sur le terrain.
    """

    def exporter_bordereau(
        self, lignes: Sequence[LigneBordereau], *, titre: str
    ) -> bytes: ...

    def generer_template_terrain(
        self,
        clients: Sequence[Client],
        *,
        code_itineraire: int,
        libelle_itineraire: str,
        nom_agent: str,
        date_travail: str,
    ) -> bytes:
        """Bordereau d'un itinéraire isolé."""
        ...

    def generer_template_multi(
        self,
        blocs: Sequence[object],
        *,
        nom_agent: str,
        date_travail: str,
    ) -> bytes:
        """Bordereau enchaînant plusieurs itinéraires, un bloc par tournée.

        Reproduit la maquette de `bordereau.xlsx / Feuil3` : en-tête campagne,
        puis pour chaque tournée son bandeau `ITINERAIRE / Total client /
        OK-MRA` et les colonnes REF GEO / METER_NO / NOMS / CONTRAT / RAPPORT,
        la dernière laissée vide pour la saisie manuscrite.
        """
        ...


@runtime_checkable
class GenerateurModeleImport(Protocol):
    """Fournit le classeur vierge que le superviseur distribue aux agents."""

    def generer(self) -> bytes: ...
