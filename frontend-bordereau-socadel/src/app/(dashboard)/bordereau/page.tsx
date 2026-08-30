import { Suspense } from "react";
import type { Metadata } from "next";

import { EcranBordereau } from "@features/collectes/ui/EcranBordereau";

export const metadata: Metadata = { title: "Bordereau" };

export default function PageBordereau() {
  // L'écran lit les itinéraires passés dans l'URL par la connexion : sans
  // frontière de suspense, `useSearchParams` ferait échouer le prérendu.
  return (
    <Suspense>
      <EcranBordereau />
    </Suspense>
  );
}
