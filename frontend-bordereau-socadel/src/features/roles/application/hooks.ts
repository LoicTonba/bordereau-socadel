/** Hooks React Query des rôles. */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { rolesApi } from "../infrastructure/roles-api";

export const CLE_ROLES = ["roles"] as const;

export function useRoles() {
  return useQuery({ queryKey: CLE_ROLES, queryFn: rolesApi.lire });
}

export function useRestreindreRole() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ role, restrictions }: { role: string; restrictions: string[] }) =>
      rolesApi.restreindre(role, restrictions),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: CLE_ROLES });
      // Le profil porte les permissions effectives : la barre latérale doit
      // se recalculer sans attendre une reconnexion.
      void client.invalidateQueries({ queryKey: ["session"] });
    },
  });
}
