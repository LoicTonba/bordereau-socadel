/** Hooks React Query du tableau de bord. */

"use client";

import { useQuery } from "@tanstack/react-query";

import type { FiltreBordereau } from "@core/domain/types";

import { analyticsApi } from "../infrastructure/analytics-api";

export const CLE_ANALYTICS = ["analytics"] as const;

export function useTableauDeBord(
  filtre: FiltreBordereau & { debut?: string; fin?: string },
) {
  return useQuery({
    queryKey: [...CLE_ANALYTICS, "tableau-de-bord", filtre],
    queryFn: () => analyticsApi.tableauDeBord(filtre),
    placeholderData: (precedent) => precedent,
  });
}
