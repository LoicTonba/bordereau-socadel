/** Appels HTTP des itinéraires et des affectations. */

import type {
  Itineraire,
  ReponsePaginee,
  ResultatAffectation,
} from "@core/domain/types";
import { api } from "@infra/http/client";

/** Champs d'une tournée. Le code n'est modifiable qu'à la création. */
export interface DonneesItineraire {
  code: number;
  libelle?: string | null;
  region?: string | null;
  division?: string | null;
  agence?: string | null;
}

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

  creer(donnees: DonneesItineraire): Promise<Itineraire> {
    return api.post<Itineraire>("/itineraires", donnees);
  },

  modifier(donnees: DonneesItineraire): Promise<Itineraire> {
    return api.patch<Itineraire>(`/itineraires/${donnees.code}`, donnees);
  },

  supprimer(code: number): Promise<void> {
    return api.delete<void>(`/itineraires/${code}`);
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
