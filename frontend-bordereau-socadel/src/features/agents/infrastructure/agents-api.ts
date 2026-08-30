/** Appels HTTP du répertoire des agents. */

import type { Agent, Portefeuille } from "@core/domain/types";
import { api } from "@infra/http/client";

export interface DonneesAgent {
  nomComplet?: string;
  telephone?: string | null;
  zoneRattachement?: string | null;
  region?: string | null;
  photoUrl?: string | null;
}

export const agentsApi = {
  lister(actifsSeulement = false): Promise<Agent[]> {
    return api.get<Agent[]>("/agents", { actifsSeulement });
  },

  consulter(agentId: string): Promise<Agent> {
    return api.get<Agent>(`/agents/${agentId}`);
  },

  creer(donnees: DonneesAgent & { matricule: string; nomComplet: string }): Promise<Agent> {
    return api.post<Agent>("/agents", donnees);
  },

  modifier(agentId: string, donnees: DonneesAgent): Promise<Agent> {
    return api.patch<Agent>(`/agents/${agentId}`, donnees);
  },

  basculerActivation(agentId: string, actif: boolean): Promise<Agent> {
    return api.patch<Agent>(`/agents/${agentId}/activation?actif=${actif}`);
  },

  portefeuille(agentId: string, jours: number): Promise<Portefeuille> {
    return api.get<Portefeuille>(`/agents/${agentId}/portefeuille`, { jours });
  },

  /** Dépose la photo et renvoie son URL, à porter ensuite par le formulaire. */
  deposerPhoto(fichier: File): Promise<{ url: string }> {
    const formulaire = new FormData();
    formulaire.append("fichier", fichier);
    return api.postFichier<{ url: string }>("/agents/photo", formulaire);
  },
};
