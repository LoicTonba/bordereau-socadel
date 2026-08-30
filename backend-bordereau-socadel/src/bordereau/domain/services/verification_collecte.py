"""Service de domaine : confrontation d'une déclaration à la source de vérité.

Le métier l'a posé comme principe : *« la source de vérité sera notre API qui
va vérifier notre BD dans le serveur et puis vérifiera si l'agent de terrain a
raison ou pas »*. Cette règle est du domaine pur — elle ne dépend d'aucun
transport ni d'aucun stockage — et elle est donc implémentée ici plutôt que
dans un cas d'usage.
"""

from __future__ import annotations

from ..entities import Client, LigneBordereau
from ..enums import StatutCollecte, VerdictVerification


def verifier(ligne: LigneBordereau, client: Client | None) -> VerdictVerification:
    """Détermine si la déclaration du superviseur est corroborée.

    Args:
        ligne: la déclaration saisie d'après le bordereau papier.
        client: l'enregistrement du référentiel SOCADEL correspondant, ou
            `None` si le SERVICE_NO déclaré n'y figure pas.

    Returns:
        Le verdict à appliquer à la ligne.
    """
    if client is None:
        return VerdictVerification.INTROUVABLE

    if not ligne.est_traitee:
        return VerdictVerification.NON_VERIFIE

    if ligne.statut is StatutCollecte.ABONNE:
        # Déclaré abonné : le référentiel doit confirmer l'abonnement WhatsApp
        # et porter le numéro effectivement collecté sur le terrain.
        if not client.est_abonne_whatsapp:
            return VerdictVerification.INFIRME
        if (
            ligne.numero_collecte is not None
            and client.telephone is not None
            and ligne.numero_collecte != client.telephone
        ):
            return VerdictVerification.INFIRME
        return VerdictVerification.CONFIRME

    # Déclaré non abonné : le référentiel ne doit pas, lui, le voir abonné.
    if client.est_abonne_whatsapp:
        return VerdictVerification.INFIRME
    return VerdictVerification.CONFIRME
