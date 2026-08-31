/** Hooks React Query des itinéraires. */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { telechargerBlob } from "@shared/lib/telechargement";

import { itinerairesApi } from "../infrastructure/itineraires-api";

export const CLE_ITINERAIRES = ["itineraires"] as const;

export function useRechercheItineraires(terme: string, actif = true) {
  return useQuery({
    queryKey: [...CLE_ITINERAIRES, "recherche", terme],
    queryFn: () => itinerairesApi.rechercher({ terme, taille: 20 }),
    // La recherche ne part qu'à partir de deux caractères : en deçà, elle
    // ramènerait un extrait arbitraire de plusieurs milliers d'itinéraires.
    enabled: actif && terme.trim().length >= 2,
  });
}

export function useAffecter() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: itinerairesApi.affecter,
    onSuccess: () => {
      // L'affectation crée les lignes du bordereau : son cache est périmé.
      void client.invalidateQueries({ queryKey: ["bordereau"] });
      void client.invalidateQueries({ queryKey: CLE_ITINERAIRES });
    },
  });
}

export function useBordereauTerrain() {
  return useMutation({
    mutationFn: async ({ code, agentId }: { code: number; agentId?: string }) => {
      const fichier = await itinerairesApi.bordereauTerrain(code, agentId);
      telechargerBlob(fichier.blob, fichier.nomFichier);
      return fichier;
    },
  });
}


/** Invalide la recherche : une tournée créée ou retirée doit s'y voir. */
function useInvalidationItineraires() {
  const client = useQueryClient();
  return () => {
    void client.invalidateQueries({ queryKey: ["itineraires"] });
  };
}

export function useCreerItineraire() {
  const invalider = useInvalidationItineraires();
  return useMutation({
    mutationFn: itinerairesApi.creer,
    onSuccess: invalider,
  });
}

export function useModifierItineraire() {
  const invalider = useInvalidationItineraires();
  return useMutation({
    mutationFn: itinerairesApi.modifier,
    onSuccess: invalider,
  });
}

export function useSupprimerItineraire() {
  const invalider = useInvalidationItineraires();
  return useMutation({
    mutationFn: itinerairesApi.supprimer,
    onSuccess: invalider,
  });
}
