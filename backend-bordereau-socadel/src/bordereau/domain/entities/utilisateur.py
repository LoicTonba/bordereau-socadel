"""Entité : compte de connexion à la plateforme."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from ..enums import Role, StatutCompte
from ..errors import RegleMetierViolee, TransitionInterdite
from ..securite import ContexteAcces

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")

#: Durée de validité d'un jeton de vérification d'adresse.
VALIDITE_VERIFICATION = timedelta(days=3)

#: Durée de validité d'un lien de réinitialisation de mot de passe. Court à
#: dessein : un lien qui traîne dans une boîte aux lettres est une porte
#: ouverte.
VALIDITE_REINITIALISATION = timedelta(hours=2)

#: Transitions autorisées du cycle de vie d'un compte.
_TRANSITIONS: dict[StatutCompte, frozenset[StatutCompte]] = {
    StatutCompte.EN_ATTENTE_VERIFICATION: frozenset(
        {StatutCompte.EN_ATTENTE_APPROBATION, StatutCompte.REFUSE}
    ),
    StatutCompte.EN_ATTENTE_APPROBATION: frozenset(
        {StatutCompte.ACTIF, StatutCompte.REFUSE}
    ),
    StatutCompte.ACTIF: frozenset({StatutCompte.SUSPENDU}),
    StatutCompte.SUSPENDU: frozenset({StatutCompte.ACTIF}),
    StatutCompte.REFUSE: frozenset(),
}


@dataclass(slots=True)
class Utilisateur:
    """Compte autorisé à se connecter.

    Quatre profils s'y connectent, avec des portées très différentes : le super
    utilisateur NEXT LTD exploite la plateforme, l'administrateur SOCADEL
    gouverne les accès de ses équipes, le superviseur pilote une agence, et
    l'agent de terrain consulte ses propres chiffres.
    """

    identifiant: str
    """Login court, ex. `p.tondjou` ou le matricule pour un agent."""

    nom_complet: str
    empreinte_mot_de_passe: str
    email: str

    role: Role = Role.SUPERVISEUR
    statut: StatutCompte = StatutCompte.EN_ATTENTE_VERIFICATION

    agent_id: UUID | None = None
    """Agent de terrain rattaché. Obligatoire pour un compte `AGENT_TERRAIN` :
    c'est lui qui délimite les données que le titulaire pourra voir."""

    region: str | None = None
    agence: str | None = None
    """Périmètre territorial d'un superviseur. SOCADEL couvre tout le pays :
    sans périmètre, un superviseur verrait la production d'agences qui ne le
    concernent pas."""

    photo_url: str | None = None
    telephone: str | None = None

    # --- Jetons à usage unique --------------------------------------------
    jeton_verification: str | None = None
    jeton_verification_expire_le: datetime | None = None
    jeton_reinitialisation: str | None = None
    jeton_reinitialisation_expire_le: datetime | None = None

    doit_changer_mot_de_passe: bool = False
    """Vrai après une réinitialisation par un responsable : le titulaire doit
    reprendre la main sur son mot de passe."""

    cree_le: datetime | None = None
    approuve_le: datetime | None = None
    approuve_par: UUID | None = None
    derniere_connexion: datetime | None = None

    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.identifiant.strip():
            raise RegleMetierViolee("L'identifiant de connexion est obligatoire")
        self.identifiant = self.identifiant.strip().lower()

        if not _EMAIL.match(self.email.strip()):
            raise RegleMetierViolee(f"Adresse électronique invalide : {self.email!r}")
        self.email = self.email.strip().lower()

        if self.role is Role.AGENT_TERRAIN and self.agent_id is None:
            # Sans rattachement, la politique ABAC ne saurait pas quoi montrer,
            # et un tel compte verrait par défaut la production de tous.
            raise RegleMetierViolee(
                "Un compte agent de terrain doit être rattaché à un agent"
            )

    # --- Lecture -----------------------------------------------------------

    @property
    def actif(self) -> bool:
        return self.statut is StatutCompte.ACTIF

    @property
    def est_agent(self) -> bool:
        return self.role is Role.AGENT_TERRAIN

    @property
    def a_un_perimetre(self) -> bool:
        return self.region is not None or self.agence is not None

    def contexte_acces(self) -> ContexteAcces:
        """Projette le compte en identité effective pour les gardes d'accès."""
        return ContexteAcces(
            utilisateur_id=self.id,
            role=self.role,
            agent_id=self.agent_id,
            region=self.region,
            agence=self.agence,
        )

    def peut_se_connecter(self) -> bool:
        return self.actif

    def motif_de_refus(self) -> str | None:
        """Explique pourquoi la connexion est refusée, en des termes utiles.

        Distinguer les cas est ici volontaire : le titulaire a déjà prouvé
        qu'il connaît son mot de passe, l'information ne renseigne donc pas un
        attaquant sur l'existence du compte.
        """
        match self.statut:
            case StatutCompte.ACTIF:
                return None
            case StatutCompte.EN_ATTENTE_VERIFICATION:
                return (
                    "Votre adresse électronique n'est pas encore confirmée. "
                    "Ouvrez le lien reçu par courriel."
                )
            case StatutCompte.EN_ATTENTE_APPROBATION:
                return (
                    "Votre inscription attend l'approbation d'un responsable. "
                    "Vous recevrez un courriel dès qu'elle sera validée."
                )
            case StatutCompte.SUSPENDU:
                return "Ce compte est suspendu. Contactez votre administrateur."
            case StatutCompte.REFUSE:
                return "Cette demande d'accès a été refusée."
        return "Ce compte n'est pas autorisé à se connecter."

    # --- Cycle de vie ------------------------------------------------------

    def _transiter_vers(self, cible: StatutCompte) -> None:
        if cible not in _TRANSITIONS[self.statut]:
            raise TransitionInterdite(
                f"Transition {self.statut.value} vers {cible.value} interdite"
            )
        self.statut = cible

    def emettre_jeton_verification(self, jeton: str, horodatage: datetime) -> None:
        self.jeton_verification = jeton
        self.jeton_verification_expire_le = horodatage + VALIDITE_VERIFICATION

    def verifier_adresse(self, jeton: str, horodatage: datetime) -> None:
        """Confirme l'adresse électronique et fait passer en attente d'approbation.

        Raises:
            RegleMetierViolee: jeton absent, faux ou périmé.
        """
        if (
            self.jeton_verification is None
            or self.jeton_verification != jeton
            or self.jeton_verification_expire_le is None
            or self.jeton_verification_expire_le <= horodatage
        ):
            raise RegleMetierViolee("Lien de confirmation invalide ou expiré")

        self._transiter_vers(StatutCompte.EN_ATTENTE_APPROBATION)
        self.jeton_verification = None
        self.jeton_verification_expire_le = None

    def approuver(
        self,
        *,
        role: Role,
        approbateur_id: UUID,
        horodatage: datetime,
        region: str | None = None,
        agence: str | None = None,
        agent_id: UUID | None = None,
    ) -> None:
        """Attribue le rôle et le périmètre, puis ouvre l'accès.

        Raises:
            RegleMetierViolee: rôle incompatible avec le périmètre fourni.
        """
        if role is Role.AGENT_TERRAIN and agent_id is None:
            raise RegleMetierViolee(
                "Un compte agent de terrain doit être rattaché à un agent"
            )
        if role is Role.SUPERVISEUR and region is None and agence is None:
            raise RegleMetierViolee(
                "Un superviseur doit recevoir une région ou une agence : "
                "sans périmètre, il verrait la production de tout le pays"
            )

        self.role = role
        self.agent_id = agent_id
        self.region = region
        self.agence = agence
        self._transiter_vers(StatutCompte.ACTIF)
        self.approuve_le = horodatage
        self.approuve_par = approbateur_id

    def refuser(self) -> None:
        self._transiter_vers(StatutCompte.REFUSE)

    def suspendre(self) -> None:
        self._transiter_vers(StatutCompte.SUSPENDU)

    def reactiver(self) -> None:
        self._transiter_vers(StatutCompte.ACTIF)

    def enregistrer_connexion(self, horodatage: datetime) -> None:
        """Trace la connexion réussie."""
        if not self.actif:
            raise RegleMetierViolee(
                self.motif_de_refus() or "Ce compte est désactivé"
            )
        self.derniere_connexion = horodatage

    # --- Mot de passe ------------------------------------------------------

    def emettre_jeton_reinitialisation(
        self, jeton: str, horodatage: datetime
    ) -> None:
        self.jeton_reinitialisation = jeton
        self.jeton_reinitialisation_expire_le = horodatage + VALIDITE_REINITIALISATION

    def reinitialiser_avec_jeton(
        self, jeton: str, empreinte: str, horodatage: datetime
    ) -> None:
        """Applique un nouveau mot de passe via le lien reçu par courriel.

        Raises:
            RegleMetierViolee: jeton absent, faux ou périmé.
        """
        if (
            self.jeton_reinitialisation is None
            or self.jeton_reinitialisation != jeton
            or self.jeton_reinitialisation_expire_le is None
            or self.jeton_reinitialisation_expire_le <= horodatage
        ):
            raise RegleMetierViolee("Lien de réinitialisation invalide ou expiré")

        self.changer_mot_de_passe(empreinte)

    def changer_mot_de_passe(self, empreinte: str) -> None:
        """Remplace le mot de passe et invalide tout lien en circulation."""
        self.empreinte_mot_de_passe = empreinte
        self.doit_changer_mot_de_passe = False
        self.jeton_reinitialisation = None
        self.jeton_reinitialisation_expire_le = None

    def imposer_mot_de_passe(self, empreinte: str) -> None:
        """Réinitialisation par un responsable.

        Le titulaire devra le remplacer dès sa prochaine connexion : un mot de
        passe qu'un tiers a choisi n'a pas à rester en place.
        """
        self.empreinte_mot_de_passe = empreinte
        self.doit_changer_mot_de_passe = True
        self.jeton_reinitialisation = None
        self.jeton_reinitialisation_expire_le = None
