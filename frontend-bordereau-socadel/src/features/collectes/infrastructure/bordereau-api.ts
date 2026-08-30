/** Appels HTTP du bordereau. */

import type {
  FiltreBordereau,
  LigneBordereau,
  ParamsPagination,
  Responsable,
  ReponsePaginee,
  StatutCollecte,
} from "@core/domain/types";
import { api } from "@infra/http/client";

export interface RapportVerification {
  lignesExaminees: number;
  confirmees: number;
  infirmees: number;
  introuvables: number;
  tauxConfirmation: number;
}

/** Aplati filtre et pagination en paramètres d'URL pour l'API. */
export function versParams(
  filtre: FiltreBordereau,
  pagination?: ParamsPagination,
): Record<string, unknown> {
  return {
    ...filtre,
    ...(pagination ?? {}),
  };
}

export const bordereauApi = {
  lister(
    filtre: FiltreBordereau,
    pagination: ParamsPagination,
  ): Promise<ReponsePaginee<LigneBordereau>> {
    return api.get<ReponsePaginee<LigneBordereau>>(
      "/bordereau",
      versParams(filtre, pagination),
    );
  },

  declarer(
    ligneId: string,
    donnees: {
      statut: StatutCollecte;
      numeroCollecte?: string | null;
      responsable?: Responsable | null;
      observation?: string | null;
    },
  ): Promise<LigneBordereau> {
    return api.patch<LigneBordereau>(`/bordereau/${ligneId}`, donnees);
  },

  declarerEnLot(donnees: {
    lignesIds: string[];
    statut: StatutCollecte;
    responsable?: Responsable | null;
  }): Promise<{ lignesModifiees: number; lignesDemandees: number }> {
    return api.post("/bordereau/declarations-en-lot", donnees);
  },

  verifier(filtre: FiltreBordereau): Promise<RapportVerification> {
    return api.post<RapportVerification>(
      "/bordereau/verification",
      undefined,
      versParams(filtre),
    );
  },

  exporter(filtre: FiltreBordereau, format: "csv" | "pdf") {
    return api.telecharger(`/exports/${format}`, versParams(filtre));
  },
};
