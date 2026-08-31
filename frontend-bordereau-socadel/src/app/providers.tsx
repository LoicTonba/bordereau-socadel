/** Fournisseurs applicatifs montés une seule fois, à la racine. */

"use client";

import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { PreferencesProvider } from "@core/i18n/PreferencesProvider";
import { SessionProvider } from "@features/auth/application/SessionProvider";
import { ErreurApi } from "@infra/http/client";
import { ToastsProvider } from "@shared/ui/Toasts";

export function Fournisseurs({ children }: { children: ReactNode }) {
  // Le client est créé dans un état : le recréer à chaque rendu viderait le
  // cache et relancerait toutes les requêtes.
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Le tableau change quand le superviseur saisit, pas tout seul :
            // une fenêtre de fraîcheur évite un rechargement à chaque
            // changement d'onglet.
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry(compteur, erreur) {
              // Réessayer une erreur d'authentification ou de validation ne
              // fait que retarder le message utile.
              if (erreur instanceof ErreurApi && erreur.statut < 500) return false;
              return compteur < 2;
            },
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <PreferencesProvider>
        <ToastsProvider>
          <SessionProvider>{children}</SessionProvider>
        </ToastsProvider>
      </PreferencesProvider>
    </QueryClientProvider>
  );
}
