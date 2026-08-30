/** Hooks React Query du répertoire des agents. */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { agentsApi, type DonneesAgent } from "../infrastructure/agents-api";

export const CLE_AGENTS = ["agents"] as const;

export function useAgents(actifsSeulement = false) {
  return useQuery({
    queryKey: [...CLE_AGENTS, { actifsSeulement }],
    queryFn: () => agentsApi.lister(actifsSeulement),
    // Le répertoire change rarement dans une journée de travail.
    staleTime: 5 * 60_000,
  });
}

export function usePortefeuille(agentId: string, jours: number) {
  return useQuery({
    queryKey: [...CLE_AGENTS, "portefeuille", agentId, jours],
    queryFn: () => agentsApi.portefeuille(agentId, jours),
    enabled: Boolean(agentId),
    placeholderData: (precedent) => precedent,
  });
}

function useInvalidation() {
  const client = useQueryClient();
  return () => {
    void client.invalidateQueries({ queryKey: CLE_AGENTS });
  };
}

export function useCreerAgent() {
  const invalider = useInvalidation();
  return useMutation({ mutationFn: agentsApi.creer, onSuccess: invalider });
}

export function useModifierAgent() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: ({ agentId, ...donnees }: DonneesAgent & { agentId: string }) =>
      agentsApi.modifier(agentId, donnees),
    onSuccess: invalider,
  });
}

export function useBasculerActivation() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: ({ agentId, actif }: { agentId: string; actif: boolean }) =>
      agentsApi.basculerActivation(agentId, actif),
    onSuccess: invalider,
  });
}

export function useDeposerPhoto() {
  return useMutation({ mutationFn: agentsApi.deposerPhoto });
}
