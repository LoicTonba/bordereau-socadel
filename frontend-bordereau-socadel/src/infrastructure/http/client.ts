/**
 * Client HTTP unique vers l'API FastAPI.
 *
 * Toutes les requêtes du frontend passent par ici : c'est le seul endroit qui
 * connaisse l'URL de l'API, le format du jeton et la forme des erreurs.
 */

import { lireJeton, supprimerJeton } from "../storage/session";

export const URL_API =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/** Erreur applicative, telle que renvoyée par le backend. */
export class ErreurApi extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly statut: number,
  ) {
    super(message);
    this.name = "ErreurApi";
  }

  /** Vrai quand la session est à refaire : le layout redirige alors au login. */
  get estNonAuthentifie(): boolean {
    return this.statut === 401;
  }
}

interface OptionsRequete extends Omit<RequestInit, "body"> {
  /** Corps JSON. Ignoré si `formData` est fourni. */
  json?: unknown;
  formData?: FormData;
  /** Paramètres d'URL ; les tableaux sont répétés (`?statut=A&statut=B`). */
  params?: Record<string, unknown>;
}

function construireUrl(chemin: string, params?: Record<string, unknown>): string {
  const url = new URL(`${URL_API}${chemin}`);
  if (!params) return url.toString();

  for (const [cle, valeur] of Object.entries(params)) {
    if (valeur === undefined || valeur === null || valeur === "") continue;
    // FastAPI attend la clé répétée pour les listes, pas une valeur jointe.
    if (Array.isArray(valeur)) {
      for (const element of valeur) {
        if (element !== undefined && element !== null && element !== "") {
          url.searchParams.append(cle, String(element));
        }
      }
    } else {
      url.searchParams.set(cle, String(valeur));
    }
  }
  return url.toString();
}

async function extraireErreur(reponse: Response): Promise<ErreurApi> {
  let code = "erreur_reseau";
  let message = `La requête a échoué (${reponse.status})`;

  try {
    const corps = await reponse.json();
    if (typeof corps?.message === "string") message = corps.message;
    if (typeof corps?.code === "string") code = corps.code;
    // Les erreurs de validation FastAPI ont une forme différente.
    else if (Array.isArray(corps?.detail) && corps.detail.length > 0) {
      code = "validation";
      message = corps.detail[0]?.msg ?? message;
    }
  } catch {
    // Réponse non-JSON (proxy, timeout) : on garde le message générique.
  }

  return new ErreurApi(code, message, reponse.status);
}

async function requete(chemin: string, options: OptionsRequete = {}): Promise<Response> {
  const { json, formData, params, headers, ...reste } = options;

  const entetes = new Headers(headers);
  const jeton = lireJeton();
  if (jeton) entetes.set("Authorization", `Bearer ${jeton}`);

  let body: BodyInit | undefined;
  if (formData) {
    // On ne fixe pas Content-Type : le navigateur doit y mettre la frontière
    // multipart lui-même.
    body = formData;
  } else if (json !== undefined) {
    entetes.set("Content-Type", "application/json");
    body = JSON.stringify(json);
  }

  const reponse = await fetch(construireUrl(chemin, params), {
    ...reste,
    headers: entetes,
    body,
  });

  if (!reponse.ok) {
    const erreur = await extraireErreur(reponse);
    // Une session invalide est purgée immédiatement : la laisser en place
    // ferait échouer toutes les requêtes suivantes de la même façon.
    if (erreur.estNonAuthentifie) supprimerJeton();
    throw erreur;
  }

  return reponse;
}

export const api = {
  async get<T>(chemin: string, params?: Record<string, unknown>): Promise<T> {
    const reponse = await requete(chemin, { method: "GET", params });
    return reponse.json() as Promise<T>;
  },

  async post<T>(
    chemin: string,
    corps?: unknown,
    params?: Record<string, unknown>,
  ): Promise<T> {
    const reponse = await requete(chemin, { method: "POST", json: corps, params });
    return reponse.json() as Promise<T>;
  },

  async patch<T>(chemin: string, corps?: unknown): Promise<T> {
    const reponse = await requete(chemin, { method: "PATCH", json: corps });
    return reponse.json() as Promise<T>;
  },

  async postFichier<T>(
    chemin: string,
    formData: FormData,
    params?: Record<string, unknown>,
  ): Promise<T> {
    const reponse = await requete(chemin, { method: "POST", formData, params });
    return reponse.json() as Promise<T>;
  },

  /**
   * Télécharge un fichier binaire (export CSV/PDF, modèle, bordereau terrain).
   *
   * Le nom est lu dans `Content-Disposition` : c'est le backend qui le décide,
   * horodatage compris.
   */
  async telecharger(
    chemin: string,
    params?: Record<string, unknown>,
  ): Promise<{ blob: Blob; nomFichier: string; tronque: boolean }> {
    const reponse = await requete(chemin, { method: "GET", params });

    const disposition = reponse.headers.get("Content-Disposition") ?? "";
    const correspondance = disposition.match(/filename="?([^"]+)"?/);

    return {
      blob: await reponse.blob(),
      nomFichier: correspondance?.[1] ?? "export",
      tronque: reponse.headers.get("X-Export-Tronque") === "true",
    };
  },
};
