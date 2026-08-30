"""Entité : ligne de bordereau, déclaration du superviseur sur un client."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from ..enums import (
    STATUTS_PRODUCTIFS,
    STATUTS_TRAITES,
    Responsable,
    StatutCollecte,
    VerdictVerification,
)
from ..errors import RegleMetierViolee, TransitionInterdite
from ..value_objects import CodeItineraire, NumeroTelephone, RefGeo, ServiceNo


@dataclass(slots=True)
class LigneBordereau:
    """Ce que le superviseur affirme du passage de l'agent chez un client.

    Une ligne est une **déclaration**, pas une vérité : elle est saisie par le
    superviseur d'après le bordereau papier rapporté du terrain. Le champ
    `verdict` porte le résultat du recoupement ultérieur avec le référentiel
    SOCADEL, qui seul détermine si l'agent sera payé pour cette ligne.
    """

    service_no: ServiceNo
    date_collecte: date
    statut: StatutCollecte = StatutCollecte.A_TRAITER

    agent_id: UUID | None = None
    affectation_id: UUID | None = None
    client_id: UUID | None = None

    # Recopiés depuis le référentiel au moment de la génération du bordereau,
    # pour que la ligne reste lisible même si le client évolue par la suite.
    nom_client: str | None = None
    ref_geo: RefGeo | None = None
    code_itineraire: CodeItineraire | None = None
    numero_compteur: str | None = None

    numero_collecte: NumeroTelephone | None = None
    """Numéro relevé par l'agent sur le terrain."""

    responsable: Responsable | None = None
    observation: str | None = None

    verdict: VerdictVerification = VerdictVerification.NON_VERIFIE
    verifie_le: datetime | None = None

    saisi_par: UUID | None = None
    saisi_le: datetime | None = None
    modifie_le: datetime | None = None

    id: UUID = field(default_factory=uuid4)

    # --- Lecture -----------------------------------------------------------

    @property
    def est_traitee(self) -> bool:
        """L'agent est passé, quel que soit le résultat."""
        return self.statut in STATUTS_TRAITES

    @property
    def est_productive(self) -> bool:
        """La ligne compte dans la production déclarée de l'agent."""
        return self.statut in STATUTS_PRODUCTIFS

    @property
    def est_remuneree(self) -> bool:
        """La ligne est payable : déclarée productive **et** confirmée par la
        source de vérité. Une déclaration seule ne suffit jamais."""
        return self.est_productive and self.verdict is VerdictVerification.CONFIRME

    # --- Écriture ----------------------------------------------------------

    def declarer(
        self,
        statut: StatutCollecte,
        *,
        horodatage: datetime,
        superviseur_id: UUID | None = None,
        numero_collecte: NumeroTelephone | None = None,
        responsable: Responsable | None = None,
        observation: str | None = None,
    ) -> None:
        """Saisit ou corrige le résultat du passage de l'agent.

        Raises:
            RegleMetierViolee: si un abonnement est déclaré sans le numéro
                collecté, qui en est la contrepartie indispensable.
        """
        if statut is StatutCollecte.ABONNE:
            numero = numero_collecte or self.numero_collecte
            if numero is None:
                raise RegleMetierViolee(
                    "Un client déclaré ABONNE doit être accompagné du numéro collecté"
                )

        self.statut = statut
        if numero_collecte is not None:
            self.numero_collecte = numero_collecte
        if responsable is not None:
            self.responsable = responsable
        if observation is not None:
            self.observation = observation

        # Toute nouvelle déclaration invalide le verdict précédent : il faudra
        # re-confronter la ligne au référentiel.
        self.verdict = VerdictVerification.NON_VERIFIE
        self.verifie_le = None

        if self.saisi_le is None:
            self.saisi_le = horodatage
            self.saisi_par = superviseur_id
        self.modifie_le = horodatage

    def appliquer_verdict(
        self, verdict: VerdictVerification, horodatage: datetime
    ) -> None:
        """Enregistre le résultat du recoupement avec la source de vérité."""
        if not self.est_traitee:
            raise TransitionInterdite(
                "Impossible de vérifier une ligne qui n'a pas encore été déclarée"
            )
        self.verdict = verdict
        self.verifie_le = horodatage
