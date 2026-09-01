/** Appels HTTP d'authentification. */

import type { Agence, Role, Session, Utilisateur } from "@core/domain/types";
import { api } from "@infra/http/client";

export interface CommandeConnexion {
  identifiant: string;
  motDePasse: string;
  /** Profil déclaré au premier écran. Vérifié côté serveur, jamais cru. */
  role?: Role | null;
  /** Agence déclarée au second écran. Cadre l'accueil, n'accorde rien. */
  agence?: string | null;
}

/** Un compte de mise en route, servi seulement en mode démonstration. */
export interface CompteDemo {
  role: Role;
  email: string;
  motDePasse: string;
  agence: string | null;
}

export interface ComptesDemo {
  actif: boolean;
  avertissement: string;
  comptes: CompteDemo[];
}

export const authApi = {
  connexion(commande: CommandeConnexion): Promise<Session> {
    return api.post<Session>("/auth/connexion", {
      identifiant: commande.identifiant,
      motDePasse: commande.motDePasse,
      role: commande.role ?? null,
      agence: commande.agence ?? null,
    });
  },

  profil(): Promise<Utilisateur> {
    return api.get<Utilisateur>("/auth/moi");
  },

  /**
   * Comptes de démonstration, si l'instance en propose.
   *
   * Renvoie `null` plutôt que de lever quand le mode est coupé : une instance
   * de production répond 404, ce qui est une réponse et non une panne.
   */
  async modeDemonstration(): Promise<ComptesDemo | null> {
    try {
      return await api.get<ComptesDemo>("/reference/mode-demonstration");
    } catch {
      return null;
    }
  },

  /** Annuaire des agences, servi avant toute session. */
  agences(): Promise<{ agences: Agence[] }> {
    return api.get<{ agences: Agence[] }>("/reference/agences");
  },
};
