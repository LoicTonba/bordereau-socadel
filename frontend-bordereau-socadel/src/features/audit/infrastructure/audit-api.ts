/** Appels HTTP du journal d'audit. */

import type { ReponsePaginee } from "@core/domain/types";
import { api } from "@infra/http/client";

export interface TraceAudit {
  quand: string;
  action: string;
  cible: string | null;
  auteur: string;
  role: string | null;
  statutHttp: number;
  reussi: boolean;
  adresseIp: string | null;
}

export interface FiltreAudit {
  identifiant?: string;
  action?: string;
  depuis?: string;
  jusquA?: string;
  echecsSeulement?: boolean;
  page?: number;
  taille?: number;
}

export const auditApi = {
  relire(filtre: FiltreAudit): Promise<ReponsePaginee<TraceAudit>> {
    return api.get<ReponsePaginee<TraceAudit>>("/audit", { ...filtre });
  },
};
