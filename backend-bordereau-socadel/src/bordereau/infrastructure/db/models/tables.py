"""Modèles ORM PostgreSQL.

Ces classes sont un **détail d'infrastructure** : elles ne sont jamais
manipulées par le domaine ni par les cas d'usage, qui ne voient que les
entités. Les mappers assurent la traduction dans les deux sens.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...db.base import Base, HorodatageMixin


def _cle_primaire() -> Mapped[UUID]:
    return mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)


class UtilisateurORM(Base, HorodatageMixin):
    """Comptes du back-office (superviseurs, administrateurs)."""

    __tablename__ = "utilisateurs"

    id: Mapped[UUID] = _cle_primaire()
    identifiant: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nom_complet: Mapped[str] = mapped_column(String(160), nullable=False)
    empreinte_mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(24), nullable=False, default="SUPERVISEUR")
    statut: Mapped[str] = mapped_column(
        String(28), nullable=False, default="EN_ATTENTE_VERIFICATION", index=True
    )

    # Rattachement d'un compte agent à sa fiche terrain : c'est lui qui
    # délimite, côté ABAC, les données que le titulaire pourra voir.
    agent_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("agents_terrain.id"), nullable=True
    )
    region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agence: Mapped[str | None] = mapped_column(String(80), nullable=True)

    photo_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    email: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Jetons à usage unique. Indexés : ils servent de clé de recherche quand
    # l'utilisateur suit un lien reçu par courriel.
    jeton_verification: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    jeton_verification_expire_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    jeton_reinitialisation: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    jeton_reinitialisation_expire_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    doit_changer_mot_de_passe: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    approuve_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approuve_par: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )
    derniere_connexion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RestrictionRoleORM(Base, HorodatageMixin):
    """Permissions retirées à un rôle par le super utilisateur.

    Cette table ne peut que **retrancher**. La matrice écrite dans le code
    reste le plafond : y ajouter une ligne ferme un droit, jamais elle n'en
    ouvre un. C'est ce qui rend l'escalade de privilèges impossible par simple
    écriture en base, y compris depuis une sauvegarde restaurée.
    """

    __tablename__ = "restrictions_role"
    __table_args__ = (
        UniqueConstraint("role", "permission", name="unicite_restriction"),
    )

    id: Mapped[UUID] = _cle_primaire()
    role: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(48), nullable=False)


class TraceAuditORM(Base):
    """Journal des gestes posés. Écrit une fois, jamais modifié.

    L'auteur est recopié plutôt que joint : un compte supprimé ne doit pas
    effacer la trace de ce qu'il a fait. Aucun corps de requête n'est conservé,
    voir l'entité correspondante.
    """

    __tablename__ = "journal_audit"
    __table_args__ = (
        Index("ix_audit_quand", "quand"),
        Index("ix_audit_auteur", "identifiant", "quand"),
    )

    id: Mapped[UUID] = _cle_primaire()
    quand: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    cible: Mapped[str | None] = mapped_column(String(200), nullable=True)
    utilisateur_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )
    identifiant: Mapped[str | None] = mapped_column(String(160), nullable=True)
    role: Mapped[str | None] = mapped_column(String(24), nullable=True)
    statut_http: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    adresse_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)


class AgenceORM(Base, HorodatageMixin):
    """Maille de base du périmètre : le centre de service client.

    Elle est tenue par l'application et non plus déduite du référentiel : c'est
    ce qui permet à SOCADEL d'ouvrir une agence dans une zone nouvelle, ou d'en
    fermer une devenue inaccessible, sans attendre un nouvel import.
    """

    __tablename__ = "agences"

    id: Mapped[UUID] = _cle_primaire()
    # Le nom est la clé métier : les comptes, les itinéraires et le référentiel
    # le portent tel quel.
    nom: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    division: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    ouverte: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    motif_fermeture: Mapped[str | None] = mapped_column(Text, nullable=True)
    fermee_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AgentTerrainORM(Base, HorodatageMixin):
    """Collecteurs de terrain."""

    __tablename__ = "agents_terrain"

    id: Mapped[UUID] = _cle_primaire()
    matricule: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    nom_complet: Mapped[str] = mapped_column(String(160), nullable=False)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    zone_rattachement: Mapped[str | None] = mapped_column(String(80), nullable=True)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    photo_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    affectations: Mapped[list["AffectationORM"]] = relationship(
        back_populates="agent", lazy="noload"
    )


class ItineraireORM(Base, HorodatageMixin):
    """Tournées de relève, extraites du référentiel."""

    __tablename__ = "itineraires"

    id: Mapped[UUID] = _cle_primaire()
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    libelle: Mapped[str | None] = mapped_column(String(160), nullable=True)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    division: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agence: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    mrc: Mapped[str | None] = mapped_column(String(80), nullable=True)
    nombre_clients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ClientORM(Base, HorodatageMixin):
    """Référentiel clients SOCADEL — la source de vérité.

    Table volumineuse (plus de 400 000 lignes) : chaque colonne servant à
    filtrer ou à joindre porte son index.
    """

    __tablename__ = "clients"
    __table_args__ = (
        Index("ix_clients_itineraire_refgeo", "code_itineraire", "ref_geo"),
        Index("ix_clients_territoire", "region", "agence"),
    )

    id: Mapped[UUID] = _cle_primaire()
    service_no: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    ref_geo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    code_itineraire: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    numero_compteur: Mapped[str | None] = mapped_column(String(40), nullable=True)

    region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    division: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agence: Mapped[str | None] = mapped_column(String(80), nullable=True)
    mrc: Mapped[str | None] = mapped_column(String(80), nullable=True)
    categorie: Mapped[str] = mapped_column(String(10), nullable=False, default="AUTRE")
    segment: Mapped[str | None] = mapped_column(String(20), nullable=True)

    whatsapp_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_checked", index=True
    )
    whatsapp_verifie_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AffectationORM(Base, HorodatageMixin):
    """Itinéraires confiés à un agent pour une journée."""

    __tablename__ = "affectations"
    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "itineraire_code",
            "date_travail",
            name="unicite_affectation_jour",
        ),
        Index("ix_affectations_jour_statut", "date_travail", "statut"),
    )

    id: Mapped[UUID] = _cle_primaire()
    agent_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("agents_terrain.id"), nullable=False
    )
    itineraire_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    date_travail: Mapped[date] = mapped_column(Date, nullable=False)
    superviseur_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False
    )
    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PLANIFIEE"
    )
    consignes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cloturee_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agent: Mapped[AgentTerrainORM] = relationship(
        back_populates="affectations", lazy="noload"
    )


class LigneBordereauORM(Base, HorodatageMixin):
    """Déclarations du superviseur, ligne à ligne."""

    __tablename__ = "lignes_bordereau"
    __table_args__ = (
        Index("ix_lignes_date_statut", "date_collecte", "statut"),
        Index("ix_lignes_agent_date", "agent_id", "date_collecte"),
        Index("ix_lignes_itineraire_date", "code_itineraire", "date_collecte"),
        Index("ix_lignes_verdict", "verdict"),
    )

    id: Mapped[UUID] = _cle_primaire()
    service_no: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    date_collecte: Mapped[date] = mapped_column(Date, nullable=False)
    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, default="A_TRAITER"
    )

    agent_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("agents_terrain.id"), nullable=True
    )
    affectation_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("affectations.id"), nullable=True, index=True
    )
    client_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("clients.id"), nullable=True
    )

    # Instantané du client au moment de l'émission du bordereau.
    nom_client: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ref_geo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    code_itineraire: Mapped[int | None] = mapped_column(Integer, nullable=True)
    numero_compteur: Mapped[str | None] = mapped_column(String(40), nullable=True)

    numero_collecte: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    # Indexé : la règle du doublon interroge cette colonne à chaque coche, et
    # le bordereau porte plusieurs centaines de milliers de lignes.

    identite: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PROPRIETAIRE"
    )
    rapport: Mapped[str | None] = mapped_column(String(8), nullable=True)
    verifie_terrain_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    date_abonnement: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valide_par: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )
    # Le nom est recopié plutôt que joint : une prime se conteste des mois
    # plus tard, quand l'agent a parfois quitté le service.
    valide_par_nom: Mapped[str | None] = mapped_column(String(160), nullable=True)

    responsable: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)

    verdict: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NON_VERIFIE"
    )
    verifie_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    saisi_par: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=True
    )
    saisi_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    modifie_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


__all__ = [
    "AffectationORM",
    "AgentTerrainORM",
    "ClientORM",
    "ItineraireORM",
    "LigneBordereauORM",
    "UtilisateurORM",
]
