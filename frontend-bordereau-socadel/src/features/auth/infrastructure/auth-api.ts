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

  /** Annuaire des agences, servi avant toute session. */
  agences(): Promise<{ agences: Agence[] }> {
    return api.get<{ agences: Agence[] }>("/reference/agences");
  },
};
