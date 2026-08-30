/** Appels HTTP des itinéraires et des affectations. */

import type {
  Itineraire,
  ReponsePaginee,
  ResultatAffectation,
} from "@core/domain/types";
import { api } from "@infra/http/client";

export const itinerairesApi = {
  rechercher(params: {
    terme?: string;
    region?: string;
    agence?: string;
    page?: number;
    taille?: number;
  }): Promise<ReponsePaginee<Itineraire>> {
    return api.get<ReponsePaginee<Itineraire>>("/itineraires", params);
  },

  affecter(donnees: {
    agentId: string;
    codesItineraires: number[];
    dateTravail: string;
    consignes?: string | null;
  }): Promise<ResultatAffectation> {
    return api.post<ResultatAffectation>("/itineraires/affectations", donnees);
  },

  /** Télécharge le bordereau papier que l'agent emporte sur le terrain. */
  bordereauTerrain(code: number, agentId?: string) {
    return api.telecharger(
      `/itineraires/${code}/bordereau-terrain.pdf`,
      agentId ? { agentId } : undefined,
    );
  },
};
