"""Schémas HTTP du bordereau, des agents et des itinéraires."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from ....application.dto import AnomalieImport, ApercuImport
from ....domain.entities import AgentTerrain, Itineraire, LigneBordereau
from ....domain.enums import (
    Responsable,
    Role,
    StatutCollecte,
    StatutCompte,
    VerdictVerification,
)
from .commun import SchemaBase

# --- Authentification ------------------------------------------------------


class RequeteConnexion(SchemaBase):
    identifiant: str = Field(min_length=1, max_length=64)
    mot_de_passe: str = Field(min_length=1, max_length=128)


class ReponseConnexion(SchemaBase):
    jeton: str
    expire_dans_secondes: int
    identifiant: str
    nom_complet: str
    role: Role


class ProfilUtilisateur(SchemaBase):
    id: UUID
    identifiant: str
    nom_complet: str
    role: Role
    agent_id: UUID | None = None
    region: str | None = None
    agence: str | None = None
    email: str | None = None
    photo_url: str | None = None
    statut: StatutCompte = StatutCompte.ACTIF
    doit_changer_mot_de_passe: bool = False
    permissions: list[str] = Field(
        default_factory=list,
        description=(
            "Permissions effectives du role. Le frontend s'en sert pour "
            "n'afficher que les actions reellement disponibles."
        ),
    )
    derniere_connexion: datetime | None = None


# --- Bordereau -------------------------------------------------------------


class LigneBordereauSortie(SchemaBase):
    """Une ligne du tableau principal."""

    id: UUID
    service_no: str
    nom_client: str | None
    ref_geo: str | None
    code_itineraire: int | None
    numero_compteur: str | None
    numero_collecte: str | None
    statut: StatutCollecte
    responsable: Responsable | None
    verdict: VerdictVerification
    date_collecte: date
    observation: str | None
    agent_id: UUID | None
    est_remuneree: bool
    modifie_le: datetime | None

    @classmethod
    def depuis_entite(cls, ligne: LigneBordereau) -> "LigneBordereauSortie":
        return cls(
            id=ligne.id,
            service_no=ligne.service_no.valeur,
            nom_client=ligne.nom_client,
            ref_geo=ligne.ref_geo.valeur if ligne.ref_geo else None,
            code_itineraire=(
                ligne.code_itineraire.valeur if ligne.code_itineraire else None
            ),
            numero_compteur=ligne.numero_compteur,
            numero_collecte=(
                ligne.numero_collecte.valeur if ligne.numero_collecte else None
            ),
            statut=ligne.statut,
            responsable=ligne.responsable,
            verdict=ligne.verdict,
            date_collecte=ligne.date_collecte,
            observation=ligne.observation,
            agent_id=ligne.agent_id,
            est_remuneree=ligne.est_remuneree,
            modifie_le=ligne.modifie_le,
        )


class RequeteDeclaration(SchemaBase):
    """Saisie du superviseur sur une ligne."""

    statut: StatutCollecte
    numero_collecte: str | None = Field(
        default=None,
        description="Numéro relevé sur le terrain. Requis pour un statut ABONNE.",
    )
    responsable: Responsable | None = None
    observation: str | None = Field(default=None, max_length=500)


class RequeteDeclarationEnLot(SchemaBase):
    lignes_ids: list[UUID] = Field(min_length=1, max_length=500)
    statut: StatutCollecte
    responsable: Responsable | None = None


class ReponseDeclarationEnLot(SchemaBase):
    lignes_modifiees: int
    lignes_demandees: int


class ReponseVerification(SchemaBase):
    lignes_examinees: int
    confirmees: int
    infirmees: int
    introuvables: int
    taux_confirmation: float


# --- Agents ----------------------------------------------------------------


class AgentSortie(SchemaBase):
    id: UUID
    matricule: str
    nom_complet: str
    telephone: str | None
    zone_rattachement: str | None
    region: str | None
    photo_url: str | None
    actif: bool

    @classmethod
    def depuis_entite(cls, agent: AgentTerrain) -> "AgentSortie":
        return cls(
            id=agent.id,
            matricule=agent.matricule,
            nom_complet=agent.nom_complet,
            telephone=agent.telephone.valeur if agent.telephone else None,
            zone_rattachement=agent.zone_rattachement,
            region=agent.region,
            photo_url=agent.photo_url,
            actif=agent.actif,
        )


class RequeteCreationAgent(SchemaBase):
    matricule: str = Field(min_length=1, max_length=32)
    nom_complet: str = Field(min_length=1, max_length=160)
    telephone: str | None = None
    zone_rattachement: str | None = Field(default=None, max_length=80)
    region: str | None = Field(default=None, max_length=80)
    photo_url: str | None = Field(default=None, max_length=400)


# --- Itinéraires et affectations -------------------------------------------


class ItineraireSortie(SchemaBase):
    id: UUID
    code: int
    libelle: str
    region: str | None
    division: str | None
    agence: str | None
    nombre_clients: int

    @classmethod
    def depuis_entite(cls, itineraire: Itineraire) -> "ItineraireSortie":
        return cls(
            id=itineraire.id,
            code=itineraire.code.valeur,
            libelle=itineraire.designation,
            region=itineraire.region,
            division=itineraire.division,
            agence=itineraire.agence,
            nombre_clients=itineraire.nombre_clients,
        )


class RequeteAffectation(SchemaBase):
    """Briefing du matin : les itinéraires confiés à un agent."""

    agent_id: UUID
    codes_itineraires: list[int] = Field(min_length=1, max_length=20)
    date_travail: date
    consignes: str | None = Field(default=None, max_length=500)


class ItineraireAffecteSortie(SchemaBase):
    affectation_id: UUID
    code_itineraire: int
    libelle: str
    lignes_generees: int


class ReponseAffectation(SchemaBase):
    agent_id: UUID
    matricule: str
    nom_agent: str
    date_travail: date
    itineraires: list[ItineraireAffecteSortie]
    total_lignes: int


# --- Import ----------------------------------------------------------------


class AnomalieSortie(SchemaBase):
    ligne: int
    colonne: str | None
    message: str
    valeur: str | None
    bloquante: bool

    @classmethod
    def depuis_dto(cls, anomalie: AnomalieImport) -> "AnomalieSortie":
        # Les DTO sont des dataclasses `slots=True` : elles n'ont pas de
        # `__dict__`, d'où le passage par `asdict`.
        return cls(**asdict(anomalie))


class LigneApercuSortie(SchemaBase):
    ligne: int
    valeurs: dict[str, object]
    anomalies: list[AnomalieSortie]
    est_importable: bool


class ReponseApercuImport(SchemaBase):
    """Contenu du modal de prévisualisation, avant validation."""

    reference: str
    nom_fichier: str
    colonnes_detectees: list[str]
    colonnes_manquantes: list[str]
    total_lignes: int
    lignes_valides: int
    lignes_rejetees: int
    est_valide: bool
    apercu: list[LigneApercuSortie]
    anomalies: list[AnomalieSortie]

    @classmethod
    def depuis_dto(cls, apercu: ApercuImport) -> "ReponseApercuImport":
        return cls(
            reference=apercu.reference,
            nom_fichier=apercu.nom_fichier,
            colonnes_detectees=list(apercu.colonnes_detectees),
            colonnes_manquantes=list(apercu.colonnes_manquantes),
            total_lignes=apercu.total_lignes,
            lignes_valides=apercu.lignes_valides,
            lignes_rejetees=apercu.lignes_rejetees,
            est_valide=apercu.est_valide,
            apercu=[
                LigneApercuSortie(
                    ligne=ligne.ligne,
                    valeurs={
                        cle: (None if valeur is None else str(valeur))
                        for cle, valeur in ligne.valeurs.items()
                    },
                    anomalies=[
                        AnomalieSortie.depuis_dto(a) for a in ligne.anomalies
                    ],
                    est_importable=ligne.est_importable,
                )
                for ligne in apercu.apercu
            ],
            anomalies=[AnomalieSortie.depuis_dto(a) for a in apercu.anomalies],
        )


class ReponseResultatImport(SchemaBase):
    reference: str
    lignes_creees: int
    lignes_mises_a_jour: int
    lignes_ignorees: int
    total_traite: int
    anomalies: list[AnomalieSortie]


# --- Agents : modification et portefeuille ---------------------------------


class RequeteModificationAgent(SchemaBase):
    """Le matricule n'y figure pas : il est immuable, tous les bordereaux
    passés le référencent."""

    nom_complet: str | None = Field(default=None, min_length=1, max_length=160)
    telephone: str | None = None
    zone_rattachement: str | None = Field(default=None, max_length=80)
    region: str | None = Field(default=None, max_length=80)
    photo_url: str | None = Field(default=None, max_length=400)


class ReponsePhoto(SchemaBase):
    url: str


class ItineraireDuJourSortie(SchemaBase):
    affectation_id: UUID
    code_itineraire: int
    libelle: str
    date_travail: date
    statut: str
    clients_total: int
    clients_traites: int
    abonnements: int
    taux_couverture: float


class PerformanceSortie(SchemaBase):
    lignes_affectees: int
    lignes_traitees: int
    abonnements_declares: int
    abonnements_confirmes: int
    abonnements_infirmes: int
    lignes_en_attente_de_verification: int
    taux_traitement: float
    taux_conversion: float
    taux_fiabilite: float


class PortefeuilleSortie(SchemaBase):
    """Ce qu'un agent porte sur la période, et ce qu'il en a fait."""

    agent: AgentSortie
    debut: date
    fin: date
    itineraires: list[ItineraireDuJourSortie]
    performance: PerformanceSortie

    @classmethod
    def depuis_dto(cls, portefeuille) -> "PortefeuilleSortie":
        perf = portefeuille.performance
        return cls(
            agent=AgentSortie.depuis_entite(portefeuille.agent),
            debut=portefeuille.periode.debut,
            fin=portefeuille.periode.fin,
            itineraires=[
                ItineraireDuJourSortie(
                    affectation_id=i.affectation_id,
                    code_itineraire=i.code_itineraire,
                    libelle=i.libelle,
                    date_travail=i.date_travail,
                    statut=i.statut,
                    clients_total=i.clients_total,
                    clients_traites=i.clients_traites,
                    abonnements=i.abonnements,
                    taux_couverture=i.taux_couverture,
                )
                for i in portefeuille.itineraires
            ],
            performance=PerformanceSortie(
                lignes_affectees=perf.lignes_affectees,
                lignes_traitees=perf.lignes_traitees,
                abonnements_declares=perf.abonnements_declares,
                abonnements_confirmes=perf.abonnements_confirmes,
                abonnements_infirmes=perf.abonnements_infirmes,
                lignes_en_attente_de_verification=(
                    perf.lignes_en_attente_de_verification
                ),
                taux_traitement=perf.taux_traitement,
                taux_conversion=perf.taux_conversion,
                taux_fiabilite=perf.taux_fiabilite,
            ),
        )

# --- Comptes de connexion --------------------------------------------------


class CompteSortie(SchemaBase):
    id: UUID
    identifiant: str
    nom_complet: str
    email: str
    role: Role
    statut: StatutCompte
    actif: bool
    agent_id: UUID | None
    region: str | None
    agence: str | None
    telephone: str | None
    photo_url: str | None
    doit_changer_mot_de_passe: bool
    cree_le: datetime | None
    approuve_le: datetime | None
    derniere_connexion: datetime | None

    @classmethod
    def depuis_entite(cls, compte) -> "CompteSortie":
        return cls(
            id=compte.id,
            identifiant=compte.identifiant,
            nom_complet=compte.nom_complet,
            email=compte.email,
            role=compte.role,
            statut=compte.statut,
            actif=compte.actif,
            agent_id=compte.agent_id,
            region=compte.region,
            agence=compte.agence,
            telephone=compte.telephone,
            photo_url=compte.photo_url,
            doit_changer_mot_de_passe=compte.doit_changer_mot_de_passe,
            cree_le=compte.cree_le,
            approuve_le=compte.approuve_le,
            derniere_connexion=compte.derniere_connexion,
        )


class RequeteInscription(SchemaBase):
    """Formulaire d'inscription.

    La longueur minimale reprend celle du domaine ; la politique complète, qui
    refuse aussi les mots courants et la reprise de l'identifiant, est
    appliquée par le cas d'usage.
    """

    identifiant: str = Field(min_length=3, max_length=64)
    nom_complet: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=160)
    mot_de_passe: str = Field(min_length=10, max_length=128)
    confirmation: str = Field(min_length=10, max_length=128)
    telephone: str | None = None
    role_souhaite: Role | None = Field(
        default=None,
        description="Indication pour le responsable qui approuvera. "
        "Jamais appliquée telle quelle.",
    )


class ReponseInscription(SchemaBase):
    identifiant: str
    email: str
    statut: StatutCompte
    message: str


class RequeteVerificationForce(SchemaBase):
    mot_de_passe: str = Field(max_length=128)
    identifiant: str | None = None
    email: str | None = None


class ReponseForceMotDePasse(SchemaBase):
    score: int = Field(ge=0, le=4)
    libelle: str
    acceptable: bool
    motifs: list[str]


class RequeteApprobation(SchemaBase):
    role: Role
    region: str | None = Field(default=None, max_length=80)
    agence: str | None = Field(default=None, max_length=80)
    agent_id: UUID | None = Field(
        default=None,
        description="Obligatoire pour un compte AGENT_TERRAIN : c'est lui qui "
        "delimite les donnees visibles par le titulaire.",
    )


class RequeteModificationCompte(SchemaBase):
    nom_complet: str | None = Field(default=None, min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=160)
    telephone: str | None = None
    photo_url: str | None = Field(default=None, max_length=400)
    region: str | None = Field(default=None, max_length=80)
    agence: str | None = Field(default=None, max_length=80)
    role: Role | None = None


class RequeteChangementMotDePasse(SchemaBase):
    ancien_mot_de_passe: str = Field(min_length=1, max_length=128)
    nouveau_mot_de_passe: str = Field(min_length=10, max_length=128)
    confirmation: str = Field(min_length=10, max_length=128)


class RequeteDemandeReinitialisation(SchemaBase):
    email: str = Field(min_length=5, max_length=160)


class RequeteReinitialisation(SchemaBase):
    jeton: str = Field(min_length=8, max_length=128)
    nouveau_mot_de_passe: str = Field(min_length=10, max_length=128)
    confirmation: str = Field(min_length=10, max_length=128)


class ReponseMotDePasseProvisoire(SchemaBase):
    identifiant: str
    nom_complet: str
    mot_de_passe_provisoire: str
    consigne: str
