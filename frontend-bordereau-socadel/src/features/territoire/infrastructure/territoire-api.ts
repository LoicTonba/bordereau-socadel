/** Appels HTTP du maillage territorial. */

import { api } from "@infra/http/client";

export interface Agence {
  nom: string;
  region: string | null;
  division: string | null;
  /** Rattachement lisible, prêt pour une liste. */
  territoire: string;
  ouverte: boolean;
  motifFermeture: string | null;
  fermeeLe: string | null;
}

export interface Territoire {
  agences: Agence[];
  regions: string[];
  divisions: string[];
}

export interface DonneesAgence {
  nom: string;
  region?: string | null;
  division?: string | null;
}

export const territoireApi = {
  lire(): Promise<Territoire> {
    return api.get<Territoire>("/territoire");
  },

  creer(donnees: DonneesAgence): Promise<Agence> {
    return api.post<Agence>("/territoire", donnees);
  },

  modifier(donnees: DonneesAgence): Promise<Agence> {
    return api.patch<Agence>(`/territoire/${encodeURIComponent(donnees.nom)}`, donnees);
  },

  fermer(nom: string, motif: string): Promise<Agence> {
    return api.post<Agence>(`/territoire/${encodeURIComponent(nom)}/fermeture`, {
      motif,
    });
  },

  rouvrir(nom: string): Promise<Agence> {
    return api.post<Agence>(`/territoire/${encodeURIComponent(nom)}/reouverture`);
  },

  supprimer(nom: string): Promise<void> {
    return api.delete<void>(`/territoire/${encodeURIComponent(nom)}`);
  },

  /** Reprend les agences que le référentiel connaît et que l'application ignore. */
  importer(): Promise<{ ajoutees: number; message: string }> {
    return api.post<{ ajoutees: number; message: string }>(
      "/territoire/import-referentiel",
    );
  },
};
