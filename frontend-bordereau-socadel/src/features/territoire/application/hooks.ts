/** Hooks React Query du maillage territorial. */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { territoireApi, type DonneesAgence } from "../infrastructure/territoire-api";

export const CLE_TERRITOIRE = ["territoire"] as const;

export function useTerritoire() {
  return useQuery({
    queryKey: CLE_TERRITOIRE,
    queryFn: territoireApi.lire,
    // Le maillage bouge de quelques agences par an : inutile de le rafraîchir
    // à chaque retour sur l'écran.
    staleTime: 5 * 60_000,
  });
}

function useInvalidation() {
  const client = useQueryClient();
  return () => {
    void client.invalidateQueries({ queryKey: CLE_TERRITOIRE });
    // Le sélecteur de connexion lit le même maillage : une agence fermée doit
    // en disparaître sans attendre un rechargement complet.
    void client.invalidateQueries({ queryKey: ["agences"] });
  };
}

export function useCreerAgence() {
  const invalider = useInvalidation();
  return useMutation({ mutationFn: territoireApi.creer, onSuccess: invalider });
}

export function useModifierAgence() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: (donnees: DonneesAgence) => territoireApi.modifier(donnees),
    onSuccess: invalider,
  });
}

export function useFermerAgence() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: ({ nom, motif }: { nom: string; motif: string }) =>
      territoireApi.fermer(nom, motif),
    onSuccess: invalider,
  });
}

export function useRouvrirAgence() {
  const invalider = useInvalidation();
  return useMutation({ mutationFn: territoireApi.rouvrir, onSuccess: invalider });
}

export function useSupprimerAgence() {
  const invalider = useInvalidation();
  return useMutation({ mutationFn: territoireApi.supprimer, onSuccess: invalider });
}

export function useImporterTerritoire() {
  const invalider = useInvalidation();
  return useMutation({ mutationFn: territoireApi.importer, onSuccess: invalider });
}
