/** Hooks React Query du cycle de vie des comptes. */

"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { ForceMotDePasse, StatutCompte } from "@core/domain/types";

import { comptesApi, type DonneesApprobation } from "../infrastructure/comptes-api";

export const CLE_COMPTES = ["comptes"] as const;

/** Délai avant d'interroger le serveur pendant la frappe, en millisecondes. */
const ATTENTE_FRAPPE = 350;

export function useComptes(statut?: StatutCompte) {
  return useQuery({
    queryKey: [...CLE_COMPTES, { statut: statut ?? null }],
    queryFn: () => comptesApi.lister(statut),
  });
}

function useInvalidation() {
  const client = useQueryClient();
  return () => {
    void client.invalidateQueries({ queryKey: CLE_COMPTES });
  };
}

export function useApprouver() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: ({ compteId, ...donnees }: DonneesApprobation & { compteId: string }) =>
      comptesApi.approuver(compteId, donnees),
    onSuccess: invalider,
  });
}

export function useRefuser() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: ({ compteId, motif }: { compteId: string; motif?: string }) =>
      comptesApi.refuser(compteId, motif),
    onSuccess: invalider,
  });
}

export function useBasculerCompte() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: ({ compteId, actif }: { compteId: string; actif: boolean }) =>
      comptesApi.basculerActivation(compteId, actif),
    onSuccess: invalider,
  });
}

export function useReinitialiserPourAutrui() {
  const invalider = useInvalidation();
  return useMutation({
    mutationFn: (compteId: string) => comptesApi.reinitialiserPourAutrui(compteId),
    onSuccess: invalider,
  });
}

export function useInscription() {
  return useMutation({ mutationFn: comptesApi.inscription });
}

export function useOubliMotDePasse() {
  return useMutation({ mutationFn: comptesApi.oubliMotDePasse });
}

/**
 * Évalue le mot de passe en cours de saisie, avec un temps d'attente.
 *
 * Sans ce délai, chaque frappe déclencherait une requête ; l'utilisateur verrait
 * en plus la jauge sauter à chaque lettre. L'évaluation vient du serveur pour
 * que la jauge affichée et la règle appliquée ne puissent pas diverger.
 */
export function useForceMotDePasse(
  motDePasse: string,
  identifiant?: string,
  email?: string,
): ForceMotDePasse | null {
  const [force, setForce] = useState<ForceMotDePasse | null>(null);

  useEffect(() => {
    if (motDePasse.length < 4) {
      setForce(null);
      return;
    }

    let annule = false;
    const minuterie = setTimeout(() => {
      comptesApi
        .forceMotDePasse(motDePasse, identifiant, email)
        .then((resultat) => {
          if (!annule) setForce(resultat);
        })
        .catch(() => {
          // L'indicateur est un confort : son échec ne doit pas bloquer la
          // saisie, et l'inscription tranchera de toute façon.
          if (!annule) setForce(null);
        });
    }, ATTENTE_FRAPPE);

    return () => {
      annule = true;
      clearTimeout(minuterie);
    };
  }, [motDePasse, identifiant, email]);

  return force;
}
