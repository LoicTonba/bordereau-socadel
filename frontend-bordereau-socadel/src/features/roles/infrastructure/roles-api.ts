/** Appels HTTP des rôles et de leurs restrictions. */

import { api } from "@infra/http/client";

export interface Droit {
  permission: string;
  /** Vrai si la matrice écrite dans le code donne ce droit au rôle. */
  accordeeParLeCode: boolean;
  /** Vrai si le super utilisateur l'a retranché. */
  restreinte: boolean;
  effective: boolean;
}

export interface VueRole {
  role: string;
  rang: number;
  nombreEffectif: number;
  droits: Droit[];
}

export const rolesApi = {
  lire(): Promise<VueRole[]> {
    return api.get<VueRole[]>("/roles");
  },

  /** Remplace d'un bloc les restrictions du rôle. Ne peut jamais ajouter. */
  restreindre(role: string, restrictions: string[]): Promise<VueRole> {
    return api.put<VueRole>(`/roles/${role}/restrictions`, { restrictions });
  },
};
