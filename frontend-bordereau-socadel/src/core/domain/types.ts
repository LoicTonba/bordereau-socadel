/**
 * Types du domaine, miroir de ceux du backend.
 *
 * Ils sont volontairement redéclarés côté client plutôt que générés : le
 * frontend n'expose qu'une partie du modèle, et cette redéclaration explicite
 * rend visible tout écart de contrat au moment de la compilation.
 */

export type Role = "ADMINISTRATEUR" | "SUPERVISEUR" | "AGENT_TERRAIN";

export type StatutCollecte =
  | "A_TRAITER"
  | "ABONNE"
  | "NON_ABONNE"
  | "INJOIGNABLE"
  | "ABSENT"
  | "REFUS"
  | "DOUBLON";

export type Responsable = "TERRAIN" | "CHATBOT" | "CSC" | "AUTRES";

export type VerdictVerification =
  | "NON_VERIFIE"
  | "CONFIRME"
  | "INFIRME"
  | "INTROUVABLE";

export interface Utilisateur {
  id: string;
  identifiant: string;
  nomComplet: string;
  role: Role;
  agentId: string | null;
  region: string | null;
  agence: string | null;
  email: string | null;
  photoUrl: string | null;
  doitChangerMotDePasse: boolean;
  /** Permissions effectives du rôle, servies par l'API. La navigation s'en
   *  sert pour n'afficher que les écrans réellement accessibles. */
  permissions: string[];
  derniereConnexion: string | null;
}

export interface Session {
  jeton: string;
  expireDansSecondes: number;
  identifiant: string;
  nomComplet: string;
  role: Role;
}

export interface LigneBordereau {
  id: string;
  serviceNo: string;
  nomClient: string | null;
  refGeo: string | null;
  codeItineraire: number | null;
  numeroCompteur: string | null;
  numeroCollecte: string | null;
  statut: StatutCollecte;
  responsable: Responsable | null;
  verdict: VerdictVerification;
  dateCollecte: string;
  observation: string | null;
  agentId: string | null;
  estRemuneree: boolean;
  modifieLe: string | null;
}

export interface Agent {
  id: string;
  matricule: string;
  nomComplet: string;
  telephone: string | null;
  zoneRattachement: string | null;
  region: string | null;
  photoUrl: string | null;
  actif: boolean;
}

export interface ItineraireDuJour {
  affectationId: string;
  codeItineraire: number;
  libelle: string;
  dateTravail: string;
  statut: string;
  clientsTotal: number;
  clientsTraites: number;
  abonnements: number;
  tauxCouverture: number;
}

export interface PerformanceAgent {
  lignesAffectees: number;
  lignesTraitees: number;
  abonnementsDeclares: number;
  abonnementsConfirmes: number;
  abonnementsInfirmes: number;
  lignesEnAttenteDeVerification: number;
  tauxTraitement: number;
  tauxConversion: number;
  tauxFiabilite: number;
}

export interface Portefeuille {
  agent: Agent;
  debut: string;
  fin: string;
  itineraires: ItineraireDuJour[];
  performance: PerformanceAgent;
}

export interface Compte {
  id: string;
  identifiant: string;
  nomComplet: string;
  role: Role;
  actif: boolean;
  agentId: string | null;
  region: string | null;
  agence: string | null;
  email: string | null;
  photoUrl: string | null;
  doitChangerMotDePasse: boolean;
  derniereConnexion: string | null;
}

export interface Itineraire {
  id: string;
  code: number;
  libelle: string;
  region: string | null;
  division: string | null;
  agence: string | null;
  nombreClients: number;
}

export interface ItineraireAffecte {
  affectationId: string;
  codeItineraire: number;
  libelle: string;
  lignesGenerees: number;
}

export interface ResultatAffectation {
  agentId: string;
  matricule: string;
  nomAgent: string;
  dateTravail: string;
  itineraires: ItineraireAffecte[];
  totalLignes: number;
}

// --- Pagination -------------------------------------------------------------

export interface MetaPagination {
  page: number;
  taille: number;
  total: number;
  nombreDePages: number;
  aPageSuivante: boolean;
  aPagePrecedente: boolean;
}

export interface ReponsePaginee<T> {
  elements: T[];
  meta: MetaPagination;
}

// --- Import -----------------------------------------------------------------

export interface AnomalieImport {
  ligne: number;
  colonne: string | null;
  message: string;
  valeur: string | null;
  bloquante: boolean;
}

export interface LigneApercu {
  ligne: number;
  valeurs: Record<string, string | null>;
  anomalies: AnomalieImport[];
  estImportable: boolean;
}

export interface ApercuImport {
  reference: string;
  nomFichier: string;
  colonnesDetectees: string[];
  colonnesManquantes: string[];
  totalLignes: number;
  lignesValides: number;
  lignesRejetees: number;
  estValide: boolean;
  apercu: LigneApercu[];
  anomalies: AnomalieImport[];
}

export interface ResultatImport {
  reference: string;
  lignesCreees: number;
  lignesMisesAJour: number;
  lignesIgnorees: number;
  totalTraite: number;
  anomalies: AnomalieImport[];
}

// --- Tableau de bord --------------------------------------------------------

export interface CarteKpi {
  cle: string;
  libelle: string;
  valeur: number;
  valeurPrecedente: number | null;
  variation: number | null;
  unite: string | null;
}

export interface PointSerie {
  jour: string;
  collectes: number;
  abonnements: number;
  confirmes: number;
}

export interface LigneClassementAgent {
  agentId: string;
  matricule: string;
  nomComplet: string;
  lignesTraitees: number;
  abonnementsDeclares: number;
  abonnementsConfirmes: number;
  tauxConversion: number;
  tauxFiabilite: number;
}

export interface CouvertureItineraire {
  codeItineraire: number;
  libelle: string;
  agence: string | null;
  clientsTotal: number;
  clientsTraites: number;
  abonnements: number;
  tauxCouverture: number;
}

export interface TableauDeBord {
  kpis: CarteKpi[];
  evolution: PointSerie[];
  classementAgents: LigneClassementAgent[];
  couvertureItineraires: CouvertureItineraire[];
  repartitionStatuts: Record<string, number>;
}

// --- Filtres ----------------------------------------------------------------

export interface FiltreBordereau {
  recherche?: string;
  debut?: string;
  fin?: string;
  statut?: StatutCollecte[];
  verdict?: VerdictVerification[];
  responsable?: Responsable[];
  itineraire?: number[];
  agent?: string[];
  region?: string;
  agence?: string;
}

export interface ParamsPagination {
  page: number;
  taille: number;
  tri?: string;
  ordre?: "asc" | "desc";
}
