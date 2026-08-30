import { Suspense } from "react";
import type { Metadata } from "next";

import { EcranVerification } from "@features/comptes/ui/EcransMotDePasse";

export const metadata: Metadata = { title: "Confirmation d'adresse" };

export default function PageVerification() {
  // Le jeton arrive par l'URL : `useSearchParams` impose une frontière de
  // suspense, sans quoi le prérendu échoue.
  return (
    <Suspense>
      <EcranVerification />
    </Suspense>
  );
}
