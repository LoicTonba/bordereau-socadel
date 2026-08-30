"""Énumérations métier partagées par tout le domaine."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Acteurs disposant d'un compte de connexion.

    L'agent de terrain en fait partie, mais avec un accès volontairement réduit
    à la consultation de ses propres chiffres : son travail se fait sur le
    terrain, bordereau papier en main, et c'est le superviseur qui saisit sa
    production.
    """

    ADMINISTRATEUR = "ADMINISTRATEUR"
    SUPERVISEUR = "SUPERVISEUR"
    AGENT_TERRAIN = "AGENT_TERRAIN"


class StatutCollecte(str, Enum):
    """Statut déclaré par le superviseur pour une ligne de bordereau.

    Reprend les valeurs saisies dans la colonne STATUT de `bordereau.xlsx`.
    """

    A_TRAITER = "A_TRAITER"
    ABONNE = "ABONNE"
    NON_ABONNE = "NON_ABONNE"
    INJOIGNABLE = "INJOIGNABLE"
    ABSENT = "ABSENT"
    REFUS = "REFUS"
    DOUBLON = "DOUBLON"


#: Statuts qui comptent comme « travail productif » pour la rémunération agent.
STATUTS_PRODUCTIFS: frozenset[StatutCollecte] = frozenset({StatutCollecte.ABONNE})

#: Statuts considérés comme traités (l'agent est passé, quel que soit le résultat).
STATUTS_TRAITES: frozenset[StatutCollecte] = frozenset(
    s for s in StatutCollecte if s is not StatutCollecte.A_TRAITER
)


class Responsable(str, Enum):
    """Origine de l'abonnement (colonne RESPONSABLE de `bordereau.xlsx`)."""

    TERRAIN = "TERRAIN"
    CHATBOT = "CHATBOT"
    CSC = "CSC"
    AUTRES = "AUTRES"


class WhatsappStatus(str, Enum):
    """Statut WhatsApp du numéro tel que renvoyé par la source de vérité.

    Valeurs observées dans `bordereau2.xlsx` (colonne WHATSAPP_STATUS).
    """

    NOT_CHECKED = "not_checked"
    VALID = "valid"
    INVALID = "invalid"
    SUBSCRIBED = "subscribed"


class VerdictVerification(str, Enum):
    """Résultat du recoupement déclaration superviseur / source de vérité."""

    NON_VERIFIE = "NON_VERIFIE"
    CONFIRME = "CONFIRME"
    INFIRME = "INFIRME"
    INTROUVABLE = "INTROUVABLE"


class StatutAffectation(str, Enum):
    """Cycle de vie d'une affectation d'itinéraire à un agent de terrain."""

    PLANIFIEE = "PLANIFIEE"
    EN_COURS = "EN_COURS"
    CLOTUREE = "CLOTUREE"
    ANNULEE = "ANNULEE"


class CategorieClient(str, Enum):
    """Catégorie tarifaire SOCADEL (colonne CATEGORIE / MARQUE_CLIENT)."""

    BT = "BT"
    MT = "MT"
    HT = "HT"
    CCOM = "CCOM"
    AUTRE = "AUTRE"

    @classmethod
    def parse(cls, valeur: str | None) -> "CategorieClient":
        if not valeur:
            return cls.AUTRE
        try:
            return cls(str(valeur).strip().upper())
        except ValueError:
            return cls.AUTRE
