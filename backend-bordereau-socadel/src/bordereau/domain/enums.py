"""Énumérations métier partagées par tout le domaine."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Acteurs disposant d'un compte de connexion.

    Quatre rôles, en deux camps. NEXT LTD édite et exploite la plateforme,
    d'où le super utilisateur ; SOCADEL s'en sert, d'où l'administrateur, les
    superviseurs et les agents.

    L'agent de terrain a un accès volontairement réduit à la consultation de
    ses propres chiffres : son travail se fait sur le terrain, bordereau papier
    en main, et c'est le superviseur qui saisit sa production.
    """

    SUPER_UTILISATEUR = "SUPER_UTILISATEUR"
    """NEXT LTD, éditeur de la plateforme. Portée totale."""

    ADMINISTRATEUR = "ADMINISTRATEUR"
    """Responsable chez SOCADEL. Gouverne les accès de ses équipes."""

    SUPERVISEUR = "SUPERVISEUR"
    """Pilote les agents d'une agence ou d'une région."""

    AGENT_TERRAIN = "AGENT_TERRAIN"
    """Collecteur. Consultation de ses propres chiffres uniquement."""


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


class StatutCompte(str, Enum):
    """Cycle de vie d'un compte de connexion.

    Une inscription ne donne pas accès : elle dépose une demande. Sur une
    plateforme qui porte le référentiel clients de SOCADEL, un accès ne
    s'obtient pas en remplissant un formulaire.
    """

    EN_ATTENTE_VERIFICATION = "EN_ATTENTE_VERIFICATION"
    """Inscrit, mais l'adresse électronique n'est pas encore confirmée."""

    EN_ATTENTE_APPROBATION = "EN_ATTENTE_APPROBATION"
    """Adresse confirmée. Un responsable doit attribuer rôle et périmètre."""

    ACTIF = "ACTIF"
    SUSPENDU = "SUSPENDU"
    REFUSE = "REFUSE"


#: Seul cet état ouvre l'accès à la plateforme.
STATUTS_AUTORISES: frozenset[StatutCompte] = frozenset({StatutCompte.ACTIF})
