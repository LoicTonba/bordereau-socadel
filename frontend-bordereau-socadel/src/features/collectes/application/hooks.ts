/** Hooks React Query du bordereau. */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { FiltreBordereau, ParamsPagination } from "@core/domain/types";
import { telechargerBlob } from "@shared/lib/telechargement";

import { bordereauApi } from "../infrastructure/bordereau-api";

/** Racine des clés de cache, pour invalider tout le bordereau d'un coup. */
export const CLE_BORDEREAU = ["bordereau"] as const;

export function useBordereau(filtre: FiltreBordereau, pagination: ParamsPagination) {
  return useQuery({
    queryKey: [...CLE_BORDEREAU, filtre, pagination],
    queryFn: () => bordereauApi.lister(filtre, pagination),
    // La page précédente reste visible pendant le chargement de la suivante :
    // sans cela, le tableau clignote à chaque changement de page ou de filtre.
    placeholderData: (precedent) => precedent,
  });
}

export function useDeclarer() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      ligneId,
      ...donnees
    }: Parameters<typeof bordereauApi.declarer>[1] & { ligneId: string }) =>
      bordereauApi.declarer(ligneId, donnees),
    onSuccess: () => {
      // Les KPI dépendent des mêmes lignes : les deux caches sont invalidés.
      void client.invalidateQueries({ queryKey: CLE_BORDEREAU });
      void client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

/**
 * Le geste du releveur.
 *
 * La ligne renvoyée est réinjectée dans le cache avant même l'invalidation :
 * sur un téléphone en bord de réseau, voir la coche basculer tout de suite
 * évite le second clic qui produirait un doublon.
 */
export function useCocher() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      ligneId,
      ...donnees
    }: Parameters<typeof bordereauApi.cocher>[1] & { ligneId: string }) =>
      bordereauApi.cocher(ligneId, donnees),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: CLE_BORDEREAU });
      void client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useDecocher() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (ligneId: string) => bordereauApi.decocher(ligneId),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: CLE_BORDEREAU });
      void client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

/** Le bordereau vierge, tel qu'il s'imprime pour le terrain. */
export function useTelechargerModele() {
  return useMutation({
    mutationFn: async (format: "pdf" | "xlsx") => {
      const fichier = await bordereauApi.telechargerModele(format);
      telechargerBlob(fichier.blob, fichier.nomFichier);
      return fichier;
    },
  });
}

export function useDeclarerEnLot() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: bordereauApi.declarerEnLot,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: CLE_BORDEREAU });
      void client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useVerifier() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (filtre: FiltreBordereau) => bordereauApi.verifier(filtre),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: CLE_BORDEREAU });
      void client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useExporter() {
  return useMutation({
    mutationFn: async ({
      filtre,
      format,
    }: {
      filtre: FiltreBordereau;
      format: "csv" | "pdf";
    }) => {
      const fichier = await bordereauApi.exporter(filtre, format);
      telechargerBlob(fichier.blob, fichier.nomFichier);
      return fichier;
    },
  });
}
