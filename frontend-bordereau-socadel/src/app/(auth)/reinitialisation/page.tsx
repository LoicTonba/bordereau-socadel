import { Suspense } from "react";
import type { Metadata } from "next";

import { EcranReinitialisation } from "@features/comptes/ui/EcransMotDePasse";

export const metadata: Metadata = { title: "Nouveau mot de passe" };

export default function PageReinitialisation() {
  return (
    <Suspense>
      <EcranReinitialisation />
    </Suspense>
  );
}
