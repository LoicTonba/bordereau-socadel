/**
 * Conservation du jeton de session côté navigateur.
 *
 * Le stockage se fait en `localStorage` : la session doit survivre au
 * rechargement de page, le superviseur travaillant plusieurs heures d'affilée
 * sur le tableau. Les accès sont gardés par try/catch — en navigation privée
 * ou avec les données de site bloquées, l'accesseur lui-même peut lever.
 */

const CLE_JETON = "socadel.jeton";
const CLE_PROFIL = "socadel.profil";
const CLE_POSTE = "socadel.poste";

export interface ProfilStocke {
  identifiant: string;
  nomComplet: string;
  role: string;
}

export function lireJeton(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(CLE_JETON);
  } catch {
    return null;
  }
}

export function ecrireJeton(jeton: string): void {
  try {
    window.localStorage.setItem(CLE_JETON, jeton);
  } catch {
    // Session non persistée : l'utilisateur devra se reconnecter au
    // rechargement, mais l'application reste utilisable dans cet onglet.
  }
}

export function supprimerJeton(): void {
  try {
    window.localStorage.removeItem(CLE_JETON);
    window.localStorage.removeItem(CLE_PROFIL);
    window.localStorage.removeItem(CLE_POSTE);
  } catch {
    // Rien à faire : sans stockage, il n'y a rien à purger.
  }
}

export function lireProfil(): ProfilStocke | null {
  if (typeof window === "undefined") return null;
  try {
    const brut = window.localStorage.getItem(CLE_PROFIL);
    return brut ? (JSON.parse(brut) as ProfilStocke) : null;
  } catch {
    return null;
  }
}

export function ecrireProfil(profil: ProfilStocke): void {
  try {
    window.localStorage.setItem(CLE_PROFIL, JSON.stringify(profil));
  } catch {
    // Le profil sera rechargé depuis /auth/moi à la prochaine requête.
  }
}

/**
 * Poste de travail déclaré à la connexion : profil, agence, itinéraires du jour.
 *
 * C'est une commodité d'affichage, jamais une autorisation. Le serveur ne lit
 * pas ce stockage et retranche de toute façon chaque requête au périmètre du
 * compte : modifier cette valeur dans le navigateur n'ouvre rien.
 */
export interface PosteStocke {
  role: string;
  agence: string | null;
  itineraires: number[];
}

export function lirePoste(): PosteStocke | null {
  if (typeof window === "undefined") return null;
  try {
    const brut = window.localStorage.getItem(CLE_POSTE);
    return brut ? (JSON.parse(brut) as PosteStocke) : null;
  } catch {
    return null;
  }
}

export function ecrirePoste(poste: PosteStocke): void {
  try {
    window.localStorage.setItem(CLE_POSTE, JSON.stringify(poste));
  } catch {
    // Sans stockage, l'écran d'accueil s'ouvrira simplement sans présélection.
  }
}
