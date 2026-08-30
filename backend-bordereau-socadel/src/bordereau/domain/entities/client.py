"""Entité : client SOCADEL, tel que connu par le référentiel de l'entreprise."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from ..enums import CategorieClient, WhatsappStatus
from ..value_objects import CodeItineraire, NumeroTelephone, RefGeo, ServiceNo


@dataclass(slots=True)
class Client:
    """Point de livraison à démarcher.

    Alimenté par le référentiel `bordereau2.xlsx` (425 920 lignes), c'est la
    **source de vérité** : quand un agent déclare avoir fait abonner un client,
    c'est le `whatsapp_status` de cette entité — mis à jour par le chatbot
    WhatsApp de NEXT — qui tranche.
    """

    service_no: ServiceNo
    nom: str
    ref_geo: RefGeo | None = None
    code_itineraire: CodeItineraire | None = None
    telephone: NumeroTelephone | None = None
    numero_compteur: str | None = None

    # Découpage territorial SOCADEL (NOM_AREA / NOM_ZONA / NOM_UNICOM / MRC).
    region: str | None = None
    division: str | None = None
    agence: str | None = None
    mrc: str | None = None

    categorie: CategorieClient = CategorieClient.AUTRE
    segment: str | None = None

    whatsapp_status: WhatsappStatus = WhatsappStatus.NOT_CHECKED
    whatsapp_verifie_le: datetime | None = None

    id: UUID = field(default_factory=uuid4)

    @property
    def est_abonne_whatsapp(self) -> bool:
        """Vrai uniquement si la source de vérité confirme l'abonnement."""
        return self.whatsapp_status is WhatsappStatus.SUBSCRIBED

    @property
    def cle_tri_terrain(self) -> tuple[int, ...]:
        """Ordre de parcours physique sur l'itinéraire.

        Les clients sans REF_GEO exploitable sont rejetés en fin de tournée
        plutôt que d'interrompre l'ordre de marche.
        """
        if self.ref_geo is None:
            return (10**9,)
        try:
            return self.ref_geo.cle_tri
        except ValueError:
            return (10**9,)

    def enregistrer_abonnement(
        self,
        telephone: NumeroTelephone,
        horodatage: datetime,
    ) -> None:
        """Applique le retour du chatbot WhatsApp : le client s'est abonné.

        C'est le seul chemin qui fait basculer un client en `SUBSCRIBED` ; la
        déclaration du superviseur, elle, ne touche jamais au référentiel.
        """
        self.telephone = telephone
        self.whatsapp_status = WhatsappStatus.SUBSCRIBED
        self.whatsapp_verifie_le = horodatage

    def marquer_numero_invalide(self, horodatage: datetime) -> None:
        self.whatsapp_status = WhatsappStatus.INVALID
        self.whatsapp_verifie_le = horodatage
