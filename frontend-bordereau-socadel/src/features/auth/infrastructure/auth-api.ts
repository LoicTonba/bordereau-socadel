/** Appels HTTP d'authentification. */

import type { Session, Utilisateur } from "@core/domain/types";
import { api } from "@infra/http/client";

export const authApi = {
  connexion(identifiant: string, motDePasse: string): Promise<Session> {
    return api.post<Session>("/auth/connexion", {
      identifiant,
      motDePasse,
    });
  },

  profil(): Promise<Utilisateur> {
    return api.get<Utilisateur>("/auth/moi");
  },
};
