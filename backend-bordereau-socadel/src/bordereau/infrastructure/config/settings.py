"""Configuration de l'application, lue depuis l'environnement.

C'est le seul endroit du backend qui connaît les variables d'environnement :
tout le reste reçoit ses réglages par injection.
"""

from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Réglages du service, surchargés par le fichier `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Identité du service ----------------------------------------------
    nom_application: str = "Bordereau SOCADEL"
    environnement: str = Field(default="development")
    debug: bool = False
    prefixe_api: str = "/api/v1"

    # --- Base de données ---------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://socadel:socadel@localhost:5432/bordereau_socadel",
        description="DSN PostgreSQL asynchrone (driver asyncpg).",
    )
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # --- Sécurité ----------------------------------------------------------
    secret_key: str = Field(
        default="changez-cette-cle-en-production-32-caracteres-minimum",
        description="Clé de signature des jetons de session.",
    )
    algorithme_jwt: str = "HS256"
    duree_session_minutes: int = 12 * 60
    """Une session couvre la journée de travail du superviseur."""

    # Compte semé au premier démarrage. Le mot de passe est modifiable par
    # variable d'environnement et doit l'être avant toute mise en production.
    superviseur_identifiant: str = "superviseur"
    superviseur_nom: str = "Superviseur SOCADEL"
    superviseur_mot_de_passe: str = "Socadel@2026"

    # --- CORS --------------------------------------------------------------
    # `NoDecode` désactive le décodage JSON que pydantic-settings applique par
    # défaut aux types complexes : sans lui, une valeur d'environnement écrite
    # en liste séparée par des virgules échouerait avant même d'atteindre le
    # validateur ci-dessous.
    origines_autorisees: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    # --- Import / export ---------------------------------------------------
    taille_max_import_mo: int = 25
    lignes_max_export: int = 50_000

    # --- Messagerie --------------------------------------------------------
    url_publique: str = "http://localhost:3000"
    """Base des liens envoyés par courriel. C'est l'adresse du back-office,
    pas celle de l'API : le destinataire clique et arrive sur une page."""

    smtp_hote: str | None = None
    """Laissé vide, les courriels sont écrits sur disque au lieu d'être
    expédiés. C'est le mode de développement."""

    smtp_port: int = 587
    smtp_utilisateur: str | None = None
    smtp_mot_de_passe: str | None = None
    smtp_tls: bool = True
    expediteur_courriel: str = "no-reply@numericexport.com"
    repertoire_courriels: str = "courriels"

    # --- Média -------------------------------------------------------------
    repertoire_media: str = "media"
    """Répertoire des photos de profil, servi en statique sous `/media`."""

    @field_validator("origines_autorisees", mode="before")
    @classmethod
    def _decouper_origines(cls, valeur: object) -> object:
        """Accepte aussi bien une liste JSON qu'une chaîne séparée par des
        virgules, forme la plus commode en variable d'environnement."""
        if isinstance(valeur, str) and not valeur.strip().startswith("["):
            return [part.strip() for part in valeur.split(",") if part.strip()]
        return valeur

    @field_validator("secret_key")
    @classmethod
    def _verifier_longueur_cle(cls, valeur: str) -> str:
        if len(valeur) < 32:
            raise ValueError(
                "SECRET_KEY doit faire au moins 32 caractères pour signer les jetons"
            )
        return valeur

    @property
    def duree_session(self) -> timedelta:
        return timedelta(minutes=self.duree_session_minutes)

    @property
    def est_production(self) -> bool:
        return self.environnement.lower() in ("production", "prod")


@lru_cache
def get_settings() -> Settings:
    """Instance unique, mise en cache pour éviter de relire l'environnement."""
    return Settings()
