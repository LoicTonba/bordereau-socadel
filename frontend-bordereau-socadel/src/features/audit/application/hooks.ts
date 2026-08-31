/** Hooks React Query du journal d'audit. */

"use client";

import { useQuery } from "@tanstack/react-query";

import { auditApi, type FiltreAudit } from "../infrastructure/audit-api";

export function useJournal(filtre: FiltreAudit) {
  return useQuery({
    queryKey: ["audit", filtre],
    queryFn: () => auditApi.relire(filtre),
    // Le journal s'allonge en continu : garder une page en cache donnerait
    // l'impression que plus rien ne se passe.
    staleTime: 0,
    placeholderData: (precedent) => precedent,
  });
}
