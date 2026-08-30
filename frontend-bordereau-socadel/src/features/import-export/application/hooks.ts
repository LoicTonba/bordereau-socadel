/** Hooks React Query de l'import et du modèle. */

"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { telechargerBlob } from "@shared/lib/telechargement";

import { importsApi } from "../infrastructure/imports-api";

export function usePrevisualiser() {
  return useMutation({ mutationFn: importsApi.previsualiser });
}

export function useValiderImport() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: importsApi.valider,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["bordereau"] });
      void client.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useTelechargerModele() {
  return useMutation({
    mutationFn: async () => {
      const fichier = await importsApi.modele();
      telechargerBlob(fichier.blob, fichier.nomFichier);
      return fichier;
    },
  });
}
