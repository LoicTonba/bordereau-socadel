"""Traduction entre modèles ORM et entités du domaine.

Ce module isole la seule dépendance qui traverse la frontière : le domaine
ignore SQLAlchemy, les repositories passent par ici. C'est aussi le point où
les colonnes brutes redeviennent des objets-valeurs validés.
"""

from __future__ import annotations

from ....domain.entities import (
    Affectation,
    AgentTerrain,
    Client,
    Itineraire,
    LigneBordereau,
    Utilisateur,
)
from ....domain.enums import (
    CategorieClient,
    Responsable,
    Role,
    StatutAffectation,
    StatutCollecte,
    VerdictVerification,
    WhatsappStatus,
)
from ....domain.value_objects import (
    CodeItineraire,
    NumeroTelephone,
    RefGeo,
    ServiceNo,
)
from ..models.tables import (
    AffectationORM,
    AgentTerrainORM,
    ClientORM,
    ItineraireORM,
    LigneBordereauORM,
    UtilisateurORM,
)

# --- Utilisateur -----------------------------------------------------------


def utilisateur_vers_domaine(row: UtilisateurORM) -> Utilisateur:
    return Utilisateur(
        id=row.id,
        identifiant=row.identifiant,
        nom_complet=row.nom_complet,
        empreinte_mot_de_passe=row.empreinte_mot_de_passe,
        role=Role(row.role),
        actif=row.actif,
        agent_id=row.agent_id,
        region=row.region,
        agence=row.agence,
        photo_url=row.photo_url,
        email=row.email,
        doit_changer_mot_de_passe=row.doit_changer_mot_de_passe,
        derniere_connexion=row.derniere_connexion,
    )


def utilisateur_vers_orm(entite: Utilisateur, row: UtilisateurORM | None = None) -> UtilisateurORM:
    row = row or UtilisateurORM(id=entite.id)
    row.identifiant = entite.identifiant
    row.nom_complet = entite.nom_complet
    row.empreinte_mot_de_passe = entite.empreinte_mot_de_passe
    row.role = entite.role.value
    row.actif = entite.actif
    row.agent_id = entite.agent_id
    row.region = entite.region
    row.agence = entite.agence
    row.photo_url = entite.photo_url
    row.email = entite.email
    row.doit_changer_mot_de_passe = entite.doit_changer_mot_de_passe
    row.derniere_connexion = entite.derniere_connexion
    return row


# --- Agent -----------------------------------------------------------------


def agent_vers_domaine(row: AgentTerrainORM) -> AgentTerrain:
    return AgentTerrain(
        id=row.id,
        matricule=row.matricule,
        nom_complet=row.nom_complet,
        telephone=NumeroTelephone.parse_ou_none(row.telephone),
        zone_rattachement=row.zone_rattachement,
        region=row.region,
        photo_url=row.photo_url,
        actif=row.actif,
    )


def agent_vers_orm(
    entite: AgentTerrain, row: AgentTerrainORM | None = None
) -> AgentTerrainORM:
    row = row or AgentTerrainORM(id=entite.id)
    row.matricule = entite.matricule
    row.nom_complet = entite.nom_complet
    row.telephone = entite.telephone.valeur if entite.telephone else None
    row.zone_rattachement = entite.zone_rattachement
    row.region = entite.region
    row.photo_url = entite.photo_url
    row.actif = entite.actif
    return row


# --- Itinéraire ------------------------------------------------------------


def itineraire_vers_domaine(row: ItineraireORM) -> Itineraire:
    return Itineraire(
        id=row.id,
        code=CodeItineraire(row.code),
        libelle=row.libelle,
        region=row.region,
        division=row.division,
        agence=row.agence,
        mrc=row.mrc,
        nombre_clients=row.nombre_clients,
    )


def itineraire_vers_orm(
    entite: Itineraire, row: ItineraireORM | None = None
) -> ItineraireORM:
    row = row or ItineraireORM(id=entite.id)
    row.code = entite.code.valeur
    row.libelle = entite.libelle
    row.region = entite.region
    row.division = entite.division
    row.agence = entite.agence
    row.mrc = entite.mrc
    row.nombre_clients = entite.nombre_clients
    return row


# --- Client ----------------------------------------------------------------


def client_vers_domaine(row: ClientORM) -> Client:
    return Client(
        id=row.id,
        service_no=ServiceNo(row.service_no),
        nom=row.nom,
        ref_geo=RefGeo.parse_ou_none(row.ref_geo),
        code_itineraire=CodeItineraire.parse_ou_none(row.code_itineraire),
        telephone=NumeroTelephone.parse_ou_none(row.telephone),
        numero_compteur=row.numero_compteur,
        region=row.region,
        division=row.division,
        agence=row.agence,
        mrc=row.mrc,
        categorie=CategorieClient.parse(row.categorie),
        segment=row.segment,
        whatsapp_status=WhatsappStatus(row.whatsapp_status),
        whatsapp_verifie_le=row.whatsapp_verifie_le,
    )


def client_vers_dict(entite: Client) -> dict[str, object]:
    """Forme utilisée par les insertions de masse (`insert().on_conflict`)."""
    return {
        "id": entite.id,
        "service_no": entite.service_no.valeur,
        "nom": entite.nom,
        "ref_geo": entite.ref_geo.valeur if entite.ref_geo else None,
        "code_itineraire": entite.code_itineraire.valeur
        if entite.code_itineraire
        else None,
        "telephone": entite.telephone.valeur if entite.telephone else None,
        "numero_compteur": entite.numero_compteur,
        "region": entite.region,
        "division": entite.division,
        "agence": entite.agence,
        "mrc": entite.mrc,
        "categorie": entite.categorie.value,
        "segment": entite.segment,
        "whatsapp_status": entite.whatsapp_status.value,
        "whatsapp_verifie_le": entite.whatsapp_verifie_le,
    }


# --- Affectation -----------------------------------------------------------


def affectation_vers_domaine(row: AffectationORM) -> Affectation:
    return Affectation(
        id=row.id,
        agent_id=row.agent_id,
        itineraire_code=CodeItineraire(row.itineraire_code),
        date_travail=row.date_travail,
        superviseur_id=row.superviseur_id,
        statut=StatutAffectation(row.statut),
        consignes=row.consignes,
        cloturee_le=row.cloturee_le,
    )


def affectation_vers_orm(
    entite: Affectation, row: AffectationORM | None = None
) -> AffectationORM:
    row = row or AffectationORM(id=entite.id)
    row.agent_id = entite.agent_id
    row.itineraire_code = entite.itineraire_code.valeur
    row.date_travail = entite.date_travail
    row.superviseur_id = entite.superviseur_id
    row.statut = entite.statut.value
    row.consignes = entite.consignes
    row.cloturee_le = entite.cloturee_le
    return row


# --- Ligne de bordereau ----------------------------------------------------


def ligne_vers_domaine(row: LigneBordereauORM) -> LigneBordereau:
    return LigneBordereau(
        id=row.id,
        service_no=ServiceNo(row.service_no),
        date_collecte=row.date_collecte,
        statut=StatutCollecte(row.statut),
        agent_id=row.agent_id,
        affectation_id=row.affectation_id,
        client_id=row.client_id,
        nom_client=row.nom_client,
        ref_geo=RefGeo.parse_ou_none(row.ref_geo),
        code_itineraire=CodeItineraire.parse_ou_none(row.code_itineraire),
        numero_compteur=row.numero_compteur,
        numero_collecte=NumeroTelephone.parse_ou_none(row.numero_collecte),
        responsable=Responsable(row.responsable) if row.responsable else None,
        observation=row.observation,
        verdict=VerdictVerification(row.verdict),
        verifie_le=row.verifie_le,
        saisi_par=row.saisi_par,
        saisi_le=row.saisi_le,
        modifie_le=row.modifie_le,
    )


def ligne_vers_orm(
    entite: LigneBordereau, row: LigneBordereauORM | None = None
) -> LigneBordereauORM:
    row = row or LigneBordereauORM(id=entite.id)
    row.service_no = entite.service_no.valeur
    row.date_collecte = entite.date_collecte
    row.statut = entite.statut.value
    row.agent_id = entite.agent_id
    row.affectation_id = entite.affectation_id
    row.client_id = entite.client_id
    row.nom_client = entite.nom_client
    row.ref_geo = entite.ref_geo.valeur if entite.ref_geo else None
    row.code_itineraire = (
        entite.code_itineraire.valeur if entite.code_itineraire else None
    )
    row.numero_compteur = entite.numero_compteur
    row.numero_collecte = (
        entite.numero_collecte.valeur if entite.numero_collecte else None
    )
    row.responsable = entite.responsable.value if entite.responsable else None
    row.observation = entite.observation
    row.verdict = entite.verdict.value
    row.verifie_le = entite.verifie_le
    row.saisi_par = entite.saisi_par
    row.saisi_le = entite.saisi_le
    row.modifie_le = entite.modifie_le
    return row


def ligne_vers_dict(entite: LigneBordereau) -> dict[str, object]:
    """Forme plate pour les insertions de masse."""
    return {
        "id": entite.id,
        "service_no": entite.service_no.valeur,
        "date_collecte": entite.date_collecte,
        "statut": entite.statut.value,
        "agent_id": entite.agent_id,
        "affectation_id": entite.affectation_id,
        "client_id": entite.client_id,
        "nom_client": entite.nom_client,
        "ref_geo": entite.ref_geo.valeur if entite.ref_geo else None,
        "code_itineraire": entite.code_itineraire.valeur
        if entite.code_itineraire
        else None,
        "numero_compteur": entite.numero_compteur,
        "numero_collecte": entite.numero_collecte.valeur
        if entite.numero_collecte
        else None,
        "responsable": entite.responsable.value if entite.responsable else None,
        "observation": entite.observation,
        "verdict": entite.verdict.value,
        "verifie_le": entite.verifie_le,
        "saisi_par": entite.saisi_par,
        "saisi_le": entite.saisi_le,
        "modifie_le": entite.modifie_le,
    }
