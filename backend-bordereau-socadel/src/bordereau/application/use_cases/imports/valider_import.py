"""Cas d'usage : écriture effective d'un import, après validation du modal.

Second temps du flux : le superviseur a vu l'aperçu et confirme. Les lignes
saisies par l'agent sur le bordereau papier sont alors rapprochées du
référentiel et deviennent des déclarations exploitables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ....domain.entities import LigneBordereau
from ....domain.enums import Responsable, StatutCollecte
from ....domain.errors import DomainError
from ....domain.securite import ContexteAcces, Permission
from ....domain.value_objects import (
    CodeItineraire,
    NumeroTelephone,
    RefGeo,
    ServiceNo,
)
from ...dto import AnomalieImport, ResultatImport
from ...errors import ImportInvalide
from ...ports import Horloge, LecteurTabulaire, UnitOfWork

#: Vocabulaire tel qu'il est écrit à la main sur les bordereaux papier.
SYNONYMES_STATUT: dict[str, StatutCollecte] = {
    "abonne": StatutCollecte.ABONNE,
    "abonné": StatutCollecte.ABONNE,
    "ok": StatutCollecte.ABONNE,
    "oui": StatutCollecte.ABONNE,
    "non abonne": StatutCollecte.NON_ABONNE,
    "non abonné": StatutCollecte.NON_ABONNE,
    "non": StatutCollecte.NON_ABONNE,
    "x": StatutCollecte.NON_ABONNE,
    "absent": StatutCollecte.ABSENT,
    "injoignable": StatutCollecte.INJOIGNABLE,
    "refus": StatutCollecte.REFUS,
    "doublon": StatutCollecte.DOUBLON,
}


@dataclass(frozen=True, slots=True)
class CommandeValidationImport:
    nom_fichier: str
    contenu: bytes
    superviseur_id: UUID
    date_collecte: date
    agent_id: UUID | None = None
    affectation_id: UUID | None = None


class ValiderImport:
    """Transforme un fichier de bordereau terrain en lignes de déclaration."""

    def __init__(
        self, uow: UnitOfWork, lecteur: LecteurTabulaire, horloge: Horloge
    ) -> None:
        self._uow = uow
        self._lecteur = lecteur
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeValidationImport
    ) -> ResultatImport:
        """Écrit l'import dans une transaction unique.

        Les lignes fautives sont collectées comme anomalies et ignorées ; les
        lignes saines sont insérées. Une erreur technique en cours de route
        annule l'ensemble, pour ne jamais laisser un demi-fichier en base.

        Raises:
            ImportInvalide: le fichier ne contient aucune ligne exploitable.
        """
        contexte.exiger(Permission.IMPORT_EXECUTER)
        brutes = self._lecteur.lire_lignes(commande.contenu, commande.nom_fichier)
        if not brutes:
            raise ImportInvalide("Aucune ligne exploitable dans le fichier")

        resultat = ResultatImport(reference=commande.nom_fichier)
        horodatage = self._horloge.maintenant()
        a_ecrire: list[LigneBordereau] = []

        async with self._uow as uow:
            # Les lignes arrivent déjà normalisées : c'est le contrat du port
            # `LecteurTabulaire`, qui seul connaît les variantes d'en-têtes.
            for index, normalisee in enumerate(brutes, start=2):  # ligne 1 = en-tête
                service_no = ServiceNo.parse_ou_none(normalisee.get("service_no"))
                if service_no is None:
                    resultat.anomalies.append(
                        AnomalieImport(
                            ligne=index,
                            colonne="SERVICE_NO",
                            message="Numéro de contrat absent ou invalide",
                            valeur=_texte(normalisee.get("service_no")),
                        )
                    )
                    resultat.lignes_ignorees += 1
                    continue

                client = await uow.clients.par_service_no(service_no)
                if client is None:
                    resultat.anomalies.append(
                        AnomalieImport(
                            ligne=index,
                            colonne="SERVICE_NO",
                            message="Contrat absent du référentiel SOCADEL",
                            valeur=service_no.valeur,
                            bloquante=False,
                        )
                    )

                ligne = LigneBordereau(
                    service_no=service_no,
                    date_collecte=commande.date_collecte,
                    agent_id=commande.agent_id,
                    affectation_id=commande.affectation_id,
                    client_id=client.id if client else None,
                    nom_client=_texte(normalisee.get("nom_client"))
                    or (client.nom if client else None),
                    ref_geo=RefGeo.parse_ou_none(normalisee.get("ref_geo"))
                    or (client.ref_geo if client else None),
                    code_itineraire=CodeItineraire.parse_ou_none(
                        normalisee.get("code_itineraire")
                    )
                    or (client.code_itineraire if client else None),
                    numero_compteur=_texte(normalisee.get("numero_compteur"))
                    or (client.numero_compteur if client else None),
                )

                statut = _lire_statut(normalisee.get("statut"))
                numero = NumeroTelephone.parse_ou_none(
                    normalisee.get("numero_collecte")
                )

                if numero is None and normalisee.get("numero_collecte"):
                    resultat.anomalies.append(
                        AnomalieImport(
                            ligne=index,
                            colonne="NUMERO_TELEPHONE",
                            message="Numéro illisible, la ligne est importée sans",
                            valeur=_texte(normalisee.get("numero_collecte")),
                            bloquante=False,
                        )
                    )

                try:
                    ligne.declarer(
                        statut,
                        horodatage=horodatage,
                        superviseur_id=commande.superviseur_id,
                        numero_collecte=numero,
                        responsable=_lire_responsable(normalisee.get("responsable")),
                        observation=_texte(normalisee.get("observation")),
                    )
                except DomainError as erreur:
                    resultat.anomalies.append(
                        AnomalieImport(
                            ligne=index,
                            colonne="STATUT",
                            message=erreur.message,
                            valeur=_texte(normalisee.get("statut")),
                        )
                    )
                    resultat.lignes_ignorees += 1
                    continue

                a_ecrire.append(ligne)

            if a_ecrire:
                resultat.lignes_creees = await uow.lignes.enregistrer_en_lot(a_ecrire)
                await uow.valider()

        return resultat


def _texte(valeur: object) -> str | None:
    if valeur is None:
        return None
    texte = str(valeur).strip()
    return texte or None


def _lire_statut(valeur: object) -> StatutCollecte:
    """Interprète la colonne statut, en tolérant les notations manuscrites."""
    texte = _texte(valeur)
    if texte is None:
        return StatutCollecte.A_TRAITER
    normalise = texte.lower()
    if normalise in SYNONYMES_STATUT:
        return SYNONYMES_STATUT[normalise]
    try:
        return StatutCollecte(texte.upper().replace(" ", "_"))
    except ValueError:
        return StatutCollecte.A_TRAITER


def _lire_responsable(valeur: object) -> Responsable | None:
    texte = _texte(valeur)
    if texte is None:
        return None
    try:
        return Responsable(texte.upper())
    except ValueError:
        return Responsable.AUTRES
