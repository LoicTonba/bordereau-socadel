"""Conteneur de dépendances : le seul endroit où les couches se rejoignent.

C'est ici — et nulle part ailleurs — que les implémentations concrètes sont
associées aux ports. Les cas d'usage reçoivent leurs collaborateurs par
construction ; ils ignorent tout de PostgreSQL, de bcrypt et de reportlab.
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from ..application.use_cases.agents import (
    BasculerActivationAgent,
    ConsulterAgent,
    ConsulterPortefeuille,
    EnregistrerAgent,
    ListerAgents,
    ModifierAgent,
)
from ..application.use_cases.analytics import ConstruireTableauDeBord
from ..application.use_cases.auth import ConnecterSuperviseur, RecupererSession
from ..application.use_cases.collectes import (
    CocherLigne,
    DecocherLigne,
    DeclarerCollecte,
    ListerBordereau,
    VerifierDeclarations,
)
from ..application.use_cases.comptes import (
    ApprouverCompte,
    BasculerActivationCompte,
    ChangerMotDePasse,
    DemanderReinitialisation,
    InscrireUtilisateur,
    ListerComptes,
    ModifierCompte,
    RefuserCompte,
    ReinitialiserAvecJeton,
    ReinitialiserParResponsable,
    VerifierAdresse,
)
from ..application.use_cases.exports import (
    ExporterBordereau,
    TelechargerModeleImport,
    TelechargerModeleTerrain,
)
from ..application.use_cases.imports import PrevisualiserImport, ValiderImport
from ..application.use_cases.audit import ConsignerTrace, RelireJournal
from ..application.use_cases.recherche_globale import RechercheGlobale
from ..application.use_cases.roles import ConsulterRoles, RestreindreRole
from ..application.use_cases.territoire import (
    CreerAgence,
    FermerAgence,
    ImporterTerritoireDepuisReferentiel,
    ListerTerritoire,
    ModifierAgence,
    RouvrirAgence,
    SupprimerAgence,
)
from ..application.use_cases.itineraires import (
    AffecterItineraires,
    CreerItineraire,
    ModifierItineraire,
    SupprimerItineraire,
    GenererTemplateTerrain,
    ListerAgences,
    RechercherItineraires,
)
from .config.settings import Settings
from .db.repositories.analytics import RequetesAnalytiquesPg
from .db.session import creer_fabrique_sessions, creer_moteur
from .db.unit_of_work import UnitOfWorkPg
from .files.exporters.csv_exporter import ExportateurCsvStandard
from .files.exporters.modele_import import GenerateurModeleXlsx
from .files.exporters.modele_terrain import GenerateurModeleTerrainXlsx
from .files.exporters.pdf_exporter import ExportateurPdfReportlab
from .files.parsers.tabulaire import LecteurTabulaireOpenpyxl
from .files.stockage_media import StockageMediaLocal
from .messagerie import (
    GenerateurJetonAleatoire,
    MessagerieFichier,
    MessagerieSmtp,
)
from .security.adapters import HacheurBcrypt, HorlogeSysteme, ServiceJetonJwt


class Container:
    """Assemble l'application au démarrage.

    Les adaptateurs sans état (hacheur, exportateurs, horloge) sont des
    singletons ; l'unité de travail, elle, est recréée à chaque cas d'usage
    pour qu'une requête HTTP ne partage jamais sa transaction avec une autre.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._moteur: AsyncEngine = creer_moteur(settings)
        self._sessions: async_sessionmaker[AsyncSession] = creer_fabrique_sessions(
            self._moteur
        )

    # --- Ressources partagées ---------------------------------------------

    @property
    def moteur(self) -> AsyncEngine:
        return self._moteur

    @property
    def fabrique_sessions(self) -> async_sessionmaker[AsyncSession]:
        return self._sessions

    def unit_of_work(self) -> UnitOfWorkPg:
        return UnitOfWorkPg(self._sessions)

    @cached_property
    def hacheur(self) -> HacheurBcrypt:
        return HacheurBcrypt()

    @cached_property
    def jetons(self) -> ServiceJetonJwt:
        return ServiceJetonJwt(self.settings.secret_key, self.settings.algorithme_jwt)

    @cached_property
    def horloge(self) -> HorlogeSysteme:
        return HorlogeSysteme()

    @cached_property
    def lecteur_tabulaire(self) -> LecteurTabulaireOpenpyxl:
        return LecteurTabulaireOpenpyxl()

    @cached_property
    def exportateur_csv(self) -> ExportateurCsvStandard:
        return ExportateurCsvStandard()

    @cached_property
    def exportateur_pdf(self) -> ExportateurPdfReportlab:
        return ExportateurPdfReportlab()

    @cached_property
    def generateur_modele(self) -> GenerateurModeleXlsx:
        return GenerateurModeleXlsx()

    @cached_property
    def generateur_modele_terrain(self) -> GenerateurModeleTerrainXlsx:
        return GenerateurModeleTerrainXlsx()

    @cached_property
    def stockage_media(self) -> StockageMediaLocal:
        return StockageMediaLocal(Path(self.settings.repertoire_media))

    @cached_property
    def generateur_jetons(self) -> GenerateurJetonAleatoire:
        return GenerateurJetonAleatoire()

    @cached_property
    def messagerie(self):
        """SMTP si un serveur est configuré, sinon écriture sur disque.

        Le choix se fait ici et nulle part ailleurs : les cas d'usage ne
        savent pas lequel des deux est en place.
        """
        if not self.settings.smtp_hote:
            return MessagerieFichier(Path(self.settings.repertoire_courriels))

        return MessagerieSmtp(
            self.settings.smtp_hote,
            self.settings.smtp_port,
            self.settings.expediteur_courriel,
            utilisateur=self.settings.smtp_utilisateur,
            mot_de_passe=self.settings.smtp_mot_de_passe,
            tls=self.settings.smtp_tls,
        )

    # --- Authentification et comptes --------------------------------------

    def connecter_superviseur(self) -> ConnecterSuperviseur:
        return ConnecterSuperviseur(
            self.unit_of_work(),
            self.hacheur,
            self.jetons,
            self.horloge,
            self.settings.duree_session,
        )

    def recuperer_session(self) -> RecupererSession:
        return RecupererSession(self.unit_of_work(), self.jetons, self.horloge)

    def lister_comptes(self) -> ListerComptes:
        return ListerComptes(self.unit_of_work())

    def modifier_compte(self) -> ModifierCompte:
        return ModifierCompte(self.unit_of_work())

    def basculer_activation_compte(self) -> BasculerActivationCompte:
        return BasculerActivationCompte(self.unit_of_work())

    # --- Inscription et cycle de vie --------------------------------------

    def inscrire_utilisateur(self) -> InscrireUtilisateur:
        return InscrireUtilisateur(
            self.unit_of_work(),
            self.hacheur,
            self.generateur_jetons,
            self.messagerie,
            self.horloge,
            self.settings.url_publique,
        )

    def verifier_adresse(self) -> VerifierAdresse:
        return VerifierAdresse(self.unit_of_work(), self.messagerie, self.horloge)

    def approuver_compte(self) -> ApprouverCompte:
        return ApprouverCompte(
            self.unit_of_work(),
            self.messagerie,
            self.horloge,
            self.settings.url_publique,
        )

    def refuser_compte(self) -> RefuserCompte:
        return RefuserCompte(self.unit_of_work(), self.messagerie)

    # --- Mots de passe -----------------------------------------------------

    def changer_mot_de_passe(self) -> ChangerMotDePasse:
        return ChangerMotDePasse(self.unit_of_work(), self.hacheur)

    def demander_reinitialisation(self) -> DemanderReinitialisation:
        return DemanderReinitialisation(
            self.unit_of_work(),
            self.generateur_jetons,
            self.messagerie,
            self.horloge,
            self.settings.url_publique,
        )

    def reinitialiser_avec_jeton(self) -> ReinitialiserAvecJeton:
        return ReinitialiserAvecJeton(
            self.unit_of_work(), self.hacheur, self.horloge
        )

    def reinitialiser_par_responsable(self) -> ReinitialiserParResponsable:
        return ReinitialiserParResponsable(
            self.unit_of_work(), self.hacheur, self.messagerie
        )

    # --- Bordereau ---------------------------------------------------------

    def lister_bordereau(self) -> ListerBordereau:
        return ListerBordereau(self.unit_of_work())

    def declarer_collecte(self) -> DeclarerCollecte:
        return DeclarerCollecte(self.unit_of_work(), self.horloge)

    def verifier_declarations(self) -> VerifierDeclarations:
        return VerifierDeclarations(self.unit_of_work(), self.horloge)

    # --- Itinéraires -------------------------------------------------------

    def affecter_itineraires(self) -> AffecterItineraires:
        return AffecterItineraires(self.unit_of_work(), self.horloge)

    def rechercher_itineraires(self) -> RechercherItineraires:
        return RechercherItineraires(self.unit_of_work())

    def lister_agences(self) -> ListerAgences:
        return ListerAgences(self.unit_of_work())

    def creer_itineraire(self) -> CreerItineraire:
        return CreerItineraire(self.unit_of_work())

    def modifier_itineraire(self) -> ModifierItineraire:
        return ModifierItineraire(self.unit_of_work())

    def supprimer_itineraire(self) -> SupprimerItineraire:
        return SupprimerItineraire(self.unit_of_work())

    def generer_template_terrain(self) -> GenererTemplateTerrain:
        return GenererTemplateTerrain(self.unit_of_work(), self.exportateur_pdf)

    # --- Agents ------------------------------------------------------------

    def lister_agents(self) -> ListerAgents:
        return ListerAgents(self.unit_of_work())

    def consulter_agent(self) -> ConsulterAgent:
        return ConsulterAgent(self.unit_of_work())

    def enregistrer_agent(self) -> EnregistrerAgent:
        return EnregistrerAgent(self.unit_of_work())

    def modifier_agent(self) -> ModifierAgent:
        return ModifierAgent(self.unit_of_work())

    def basculer_activation_agent(self) -> BasculerActivationAgent:
        return BasculerActivationAgent(self.unit_of_work())

    def consulter_portefeuille(self) -> ConsulterPortefeuille:
        return ConsulterPortefeuille(self.unit_of_work())

    # --- Import / export ---------------------------------------------------

    def previsualiser_import(self) -> PrevisualiserImport:
        return PrevisualiserImport(self.lecteur_tabulaire)

    def valider_import(self) -> ValiderImport:
        return ValiderImport(self.unit_of_work(), self.lecteur_tabulaire, self.horloge)

    def exporter_bordereau(self) -> ExporterBordereau:
        return ExporterBordereau(
            self.unit_of_work(),
            self.exportateur_csv,
            self.exportateur_pdf,
            self.horloge,
        )

    def telecharger_modele(self) -> TelechargerModeleImport:
        return TelechargerModeleImport(self.generateur_modele)

    def telecharger_modele_terrain(self) -> TelechargerModeleTerrain:
        return TelechargerModeleTerrain(
            self.generateur_modele_terrain, self.exportateur_pdf
        )

    # --- Le geste du releveur ----------------------------------------------

    def cocher_ligne(self) -> CocherLigne:
        return CocherLigne(self.unit_of_work(), self.horloge)

    def decocher_ligne(self) -> DecocherLigne:
        return DecocherLigne(self.unit_of_work(), self.horloge)

    # --- Roles et restrictions ---------------------------------------------

    def consulter_roles(self) -> ConsulterRoles:
        return ConsulterRoles(self.unit_of_work())

    def restreindre_role(self) -> RestreindreRole:
        return RestreindreRole(self.unit_of_work())

    async def restrictions_en_vigueur(self, role) -> frozenset:
        """Les permissions retirees a ce role, pretes pour le contexte d'acces.

        Relues a chaque requete : retirer un droit doit prendre effet tout de
        suite, pas au prochain redemarrage.
        """
        from ..domain.securite import Permission

        async with self.unit_of_work() as uow:
            valeurs = await uow.restrictions.pour(role.value)

        connues = {p.value: p for p in Permission}
        return frozenset(connues[v] for v in valeurs if v in connues)

    # --- Journal d'audit ---------------------------------------------------

    def consigner_trace(self) -> ConsignerTrace:
        return ConsignerTrace(self.unit_of_work())

    def relire_journal(self) -> RelireJournal:
        return RelireJournal(self.unit_of_work())

    # --- Maillage territorial ----------------------------------------------

    def lister_territoire(self) -> ListerTerritoire:
        return ListerTerritoire(self.unit_of_work())

    def creer_agence(self) -> CreerAgence:
        return CreerAgence(self.unit_of_work())

    def modifier_agence(self) -> ModifierAgence:
        return ModifierAgence(self.unit_of_work())

    def fermer_agence(self) -> FermerAgence:
        return FermerAgence(self.unit_of_work(), self.horloge)

    def rouvrir_agence(self) -> RouvrirAgence:
        return RouvrirAgence(self.unit_of_work())

    def supprimer_agence(self) -> SupprimerAgence:
        return SupprimerAgence(self.unit_of_work())

    def importer_territoire(self) -> ImporterTerritoireDepuisReferentiel:
        return ImporterTerritoireDepuisReferentiel(self.unit_of_work())

    # --- Recherche globale -------------------------------------------------

    def recherche_globale(self) -> RechercheGlobale:
        """Chaque volet est délégué au cas d'usage qui le sert déjà : les
        habilitations et le rétrécissement ABAC s'appliquent sans être
        redits."""
        return RechercheGlobale(
            self.lister_bordereau(),
            self.rechercher_itineraires(),
            self.lister_agents(),
            self.lister_comptes(),
        )

    # --- Tableau de bord ---------------------------------------------------

    def construire_tableau_de_bord(self) -> ConstruireTableauDeBord:
        """Le modèle de lecture reçoit la fabrique, pas une session.

        Les cinq requêtes du tableau de bord partent en parallèle : chacune
        doit disposer de sa propre session, une `AsyncSession` ne supportant
        qu'une opération à la fois.
        """
        return ConstruireTableauDeBord(RequetesAnalytiquesPg(self._sessions))

    # --- Cycle de vie ------------------------------------------------------

    async def fermer(self) -> None:
        await self._moteur.dispose()
