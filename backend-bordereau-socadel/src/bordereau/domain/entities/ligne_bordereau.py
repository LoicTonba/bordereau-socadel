"""Entité : ligne de bordereau, déclaration du superviseur sur un client."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from ..enums import (
    STATUTS_PRODUCTIFS,
    STATUTS_TRAITES,
    Identite,
    Rapport,
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

    identite: Identite = Identite.PROPRIETAIRE
    """Qui est la personne dont on relève le numéro.

    Le contrat est au nom de quelqu'un, la facture est souvent payée par un
    autre. La distinction décide à qui la facture doit parvenir.
    """

    rapport: Rapport | None = None
    """Ce que l'agent rapporte du passage. Vide tant qu'il n'est pas passé.

    Le formulaire propose OK par défaut, mais la ligne ne l'affirme pas d'elle
    même : une ligne jamais visitée qui annoncerait OK serait un mensonge.
    """

    verifie_terrain_le: datetime | None = None
    """Quand l'agent a coché. C'est la colonne Check Date du bordereau."""

    date_abonnement: datetime | None = None
    """Quand la source de vérité a vu l'abonnement se produire."""

    valide_par: UUID | None = None
    valide_par_nom: str | None = None
    """Qui a coché, recopié plutôt que joint.

    Le nom reste lisible même si le compte disparaît : une prime se conteste
    des mois plus tard, quand l'agent a parfois quitté le service.
    """

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
    def verifie_terrain(self) -> bool:
        """L'agent est passé et a coché. C'est la colonne Check."""
        return self.verifie_terrain_le is not None

    @property
    def auteur_affiche(self) -> str | None:
        """Ce que la colonne Responsable montre.

        Le nom de celui qui a coché quand il y en a un, sinon la catégorie :
        une relance MRA n'a pas d'auteur humain, et c'est justement ce que la
        colonne doit dire.
        """
        if self.responsable is None:
            # Personne n'a encore obtenu l'abonnement. Afficher le nom de
            # l'agent qui est passé laisserait croire qu'il l'a obtenu, et
            # c'est de la prime qu'il s'agit.
            return None
        if self.responsable is Responsable.TERRAIN and self.valide_par_nom:
            return self.valide_par_nom
        return self.responsable.value

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

    def cocher(
        self,
        *,
        horodatage: datetime,
        agent_id: UUID | None = None,
        agent_nom: str | None = None,
        rapport: Rapport = Rapport.OK,
        numero_collecte: NumeroTelephone | None = None,
        identite: Identite | None = None,
    ) -> None:
        """Le geste du releveur : un clic, et la ligne est renseignée.

        C'est le seul geste qu'il pose, et il est volontairement pauvre. Un
        releveur en tournée, sous le soleil, avec un téléphone à une main, ne
        remplit pas un formulaire : il coche.

        Deux issues seulement. `OK`, le client est allé au bout du parcours
        WhatsApp et la ligne se déclare abonnée. `MRA`, la zone n'a pas de
        couverture : le numéro est pris, la relance se fera depuis MRA, et la
        ligne reste à traiter parce que rien n'est encore acquis.

        Raises:
            RegleMetierViolee: si un OK est coché sans numéro à confronter.
        """
        numero = numero_collecte or self.numero_collecte
        if rapport is Rapport.OK and numero is None:
            raise RegleMetierViolee(
                "Cocher OK affirme que le client s'est abonné : le numéro "
                "relevé doit l'accompagner, c'est lui qui sera confronté au "
                "référentiel."
            )

        if numero_collecte is not None:
            self.numero_collecte = numero_collecte
        if identite is not None:
            self.identite = identite

        self.rapport = rapport
        self.verifie_terrain_le = horodatage
        self.valide_par = agent_id
        self.valide_par_nom = agent_nom

        if rapport is Rapport.OK:
            self.statut = StatutCollecte.ABONNE
            self.responsable = Responsable.TERRAIN
        else:
            # Rien n'est acquis : MRA relancera, et c'est elle qui sera portée
            # en responsable si le client finit par s'abonner.
            self.statut = StatutCollecte.A_TRAITER
            self.responsable = None

        # Toute nouvelle déclaration invalide le verdict précédent.
        self.verdict = VerdictVerification.NON_VERIFIE
        self.verifie_le = None
        self.date_abonnement = None

        if self.saisi_le is None:
            self.saisi_le = horodatage
            self.saisi_par = agent_id
        self.modifie_le = horodatage

    def decocher(self, *, horodatage: datetime) -> None:
        """Annule le coche. La ligne redevient à traiter."""
        self.rapport = None
        self.verifie_terrain_le = None
        self.valide_par = None
        self.valide_par_nom = None
        self.statut = StatutCollecte.A_TRAITER
        self.responsable = None
        self.verdict = VerdictVerification.NON_VERIFIE
        self.verifie_le = None
        self.date_abonnement = None
        self.modifie_le = horodatage

    def attribuer_a_la_relance(self, *, horodatage: datetime) -> None:
        """La campagne MRA a obtenu l'abonnement, pas l'agent.

        L'agent est intéressé à la collecte, la relance automatique ne l'est
        pas : lui attribuer cet abonnement fausserait sa prime.
        """
        self.statut = StatutCollecte.ABONNE
        self.responsable = Responsable.MRA
        self.valide_par = None
        self.valide_par_nom = None
        self.verdict = VerdictVerification.NON_VERIFIE
        self.verifie_le = None
        self.modifie_le = horodatage

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
        """Enregistre le résultat du recoupement avec la source de vérité.

        C'est la colonne **Back office** du bordereau, celle qui interroge la
        base des abonnements : le client est-il vraiment allé au bout du
        parcours WhatsApp. Trois colonnes se remplissent seules à ce
        moment-là — la date du contrôle, la date d'abonnement, et le statut.

        Une ligne partie en relance MRA se vérifie aussi, alors qu'elle n'a
        rien déclaré d'abonné : c'est même tout l'intérêt du contrôle, savoir
        si la campagne a fini par aboutir. Quand elle aboutit, la colonne
        Responsable affiche **MRA** et non le nom de l'agent : la relance
        automatique a obtenu l'abonnement, pas lui, et sa prime ne doit pas
        s'en trouver gonflée.
        """
        if not self.est_traitee and not self.verifie_terrain:
            raise TransitionInterdite(
                "Impossible de vérifier une ligne qui n'a pas encore été déclarée"
            )
        self.verdict = verdict
        self.verifie_le = horodatage

        if verdict is not VerdictVerification.CONFIRME:
            self.date_abonnement = None
            return

        if self.rapport is Rapport.MRA:
            # La campagne a abouti là où l'agent n'avait pas de réseau.
            self.statut = StatutCollecte.ABONNE
            self.responsable = Responsable.MRA
            self.valide_par = None
            self.valide_par_nom = None
        elif self.statut is not StatutCollecte.ABONNE:
            # Un « absent » corroboré reste un absent : le verdict confirme la
            # déclaration, il ne la transforme pas en abonnement.
            return

        self.date_abonnement = horodatage
