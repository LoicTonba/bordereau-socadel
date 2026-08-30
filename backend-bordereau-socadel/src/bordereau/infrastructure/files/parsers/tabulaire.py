"""Lecture des fichiers de bordereau déposés par le superviseur.

Implémente le port `LecteurTabulaire`. Deux formats circulent sur le terrain :
le classeur Excel issu du modèle distribué, et le CSV qu'on obtient en
l'enregistrant autrement. Les deux sont acceptés.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Sequence
from typing import Any

import openpyxl

from ....application.dto import AnomalieImport, ApercuImport, LigneApercu
from ....application.errors import ImportInvalide
from ....domain.value_objects import ServiceNo

#: Seule colonne sans laquelle une ligne n'a aucun sens : sans contrat, on ne
#: peut ni rattacher au référentiel ni vérifier quoi que ce soit.
COLONNES_REQUISES = ("service_no",)

#: En-têtes acceptés pour chaque champ interne (le fichier terrain circule
#: sous plusieurs variantes selon qui l'a exporté).
ALIAS = {
    "service_no": ("service_no", "nis_rad", "numero_contrat", "contrat"),
    "nom_client": ("noms", "nom", "firstname", "nom_client"),
    "ref_geo": ("ref_geo", "refgeo", "ref geo"),
    "code_itineraire": ("itineraire", "num_itin", "code_itineraire"),
    "numero_compteur": ("meter_no", "numero_compteur", "compteur"),
    "numero_collecte": ("numero_telephone", "telephone", "numero"),
    "statut": ("statut", "rapport", "resultat"),
    "responsable": ("responsable",),
    "observation": ("observation", "check", "remarque"),
}


class LecteurTabulaireOpenpyxl:
    """Analyse et lit les classeurs `.xlsx` et les fichiers `.csv`."""

    def analyser(
        self, contenu: bytes, nom_fichier: str, *, taille_apercu: int = 20
    ) -> ApercuImport:
        """Parcourt le fichier sans rien écrire, pour le modal de validation.

        Les anomalies sont recensées ligne à ligne : le superviseur voit ce
        qui passera, ce qui sera ignoré et pourquoi, avant de confirmer.
        """
        lignes, entetes = self._extraire(contenu, nom_fichier)

        champs_detectes = {
            champ
            for champ, alias in ALIAS.items()
            if any(_normaliser_entete(e) in alias for e in entetes)
        }
        manquantes = tuple(
            champ for champ in COLONNES_REQUISES if champ not in champs_detectes
        )

        apercu: list[LigneApercu] = []
        anomalies: list[AnomalieImport] = []
        valides = rejetees = 0

        for index, brute in enumerate(lignes, start=2):
            normalisee = self._normaliser_ligne(brute)
            anomalies_ligne = self._controler(normalisee, index)

            if any(a.bloquante for a in anomalies_ligne):
                rejetees += 1
            else:
                valides += 1

            anomalies.extend(anomalies_ligne)
            if len(apercu) < taille_apercu:
                apercu.append(
                    LigneApercu(
                        ligne=index,
                        valeurs=normalisee,
                        anomalies=tuple(anomalies_ligne),
                    )
                )

        return ApercuImport(
            reference=_empreinte(contenu),
            nom_fichier=nom_fichier,
            colonnes_detectees=tuple(entetes),
            total_lignes=len(lignes),
            lignes_valides=valides,
            lignes_rejetees=rejetees,
            apercu=tuple(apercu),
            # Le rapport d'anomalies est borné : sur un fichier entièrement
            # fautif, tout renvoyer noierait le message utile.
            anomalies=tuple(anomalies[:200]),
            colonnes_manquantes=manquantes,
        )

    def lire_lignes(
        self, contenu: bytes, nom_fichier: str
    ) -> Sequence[dict[str, Any]]:
        lignes, _ = self._extraire(contenu, nom_fichier)
        return [self._normaliser_ligne(ligne) for ligne in lignes]

    # --- Extraction brute --------------------------------------------------

    def _extraire(
        self, contenu: bytes, nom_fichier: str
    ) -> tuple[list[dict[str, Any]], list[str]]:
        if nom_fichier.lower().endswith(".csv"):
            return self._lire_csv(contenu)
        return self._lire_xlsx(contenu)

    def _lire_csv(self, contenu: bytes) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            texte = contenu.decode("utf-8-sig")
        except UnicodeDecodeError:
            # Les exports Excel francophones sortent souvent en Latin-1.
            texte = contenu.decode("latin-1")

        # Le séparateur varie selon la locale de la machine qui a exporté.
        try:
            dialecte = csv.Sniffer().sniff(texte[:4096], delimiters=";,\t")
        except csv.Error:
            dialecte = csv.excel
            dialecte.delimiter = ";"

        lecteur = csv.DictReader(io.StringIO(texte), dialect=dialecte)
        entetes = [e for e in (lecteur.fieldnames or []) if e]
        return [dict(ligne) for ligne in lecteur], entetes

    def _lire_xlsx(self, contenu: bytes) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            classeur = openpyxl.load_workbook(
                io.BytesIO(contenu), data_only=True, read_only=True
            )
        except Exception as erreur:  # openpyxl remonte des exceptions variées
            raise ImportInvalide(
                "Classeur illisible : vérifiez qu'il s'agit bien d'un fichier Excel"
            ) from erreur

        try:
            feuille = classeur.worksheets[0]
            iterateur = feuille.iter_rows(values_only=True)

            entetes_brutes = next(iterateur, None)
            if entetes_brutes is None:
                return [], []
            entetes = [str(e).strip() if e is not None else "" for e in entetes_brutes]

            lignes: list[dict[str, Any]] = []
            for valeurs in iterateur:
                if all(v is None or str(v).strip() == "" for v in valeurs):
                    continue  # ligne de séparation ou fin de tableau
                lignes.append(dict(zip(entetes, valeurs, strict=False)))

            return lignes, [e for e in entetes if e]
        finally:
            classeur.close()

    # --- Normalisation et contrôle ----------------------------------------

    def _normaliser_ligne(self, brute: dict[str, Any]) -> dict[str, Any]:
        """Ramène les en-têtes du fichier aux noms de champs internes."""
        normalisee: dict[str, Any] = {}
        for entete, valeur in brute.items():
            cle = _normaliser_entete(entete)
            for champ, alias in ALIAS.items():
                if cle in alias and normalisee.get(champ) in (None, ""):
                    normalisee[champ] = _valeur_propre(valeur)
                    break
        return normalisee

    def _controler(
        self, ligne: dict[str, Any], numero: int
    ) -> list[AnomalieImport]:
        anomalies: list[AnomalieImport] = []

        if ServiceNo.parse_ou_none(ligne.get("service_no")) is None:
            anomalies.append(
                AnomalieImport(
                    ligne=numero,
                    colonne="SERVICE_NO",
                    message="Numéro de contrat absent ou invalide",
                    valeur=_texte(ligne.get("service_no")),
                )
            )

        if not ligne.get("statut"):
            anomalies.append(
                AnomalieImport(
                    ligne=numero,
                    colonne="STATUT",
                    message="Statut absent : la ligne sera importée « à traiter »",
                    bloquante=False,
                )
            )

        return anomalies


def _normaliser_entete(entete: object) -> str:
    return str(entete or "").strip().lower().replace(" ", "_")


def _valeur_propre(valeur: object) -> Any:
    if valeur is None:
        return None
    if isinstance(valeur, str):
        return valeur.strip() or None
    return valeur


def _texte(valeur: object) -> str | None:
    return None if valeur is None else str(valeur)


def _empreinte(contenu: bytes) -> str:
    """Identifie le fichier prévisualisé, pour garantir que la validation
    porte bien sur celui-ci et pas sur un autre déposé entre-temps."""
    return hashlib.sha256(contenu).hexdigest()[:16]
