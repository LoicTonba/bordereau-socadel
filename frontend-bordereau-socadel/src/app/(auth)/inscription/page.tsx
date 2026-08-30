import type { Metadata } from "next";

import { EcranInscription } from "@features/comptes/ui/EcranInscription";

export const metadata: Metadata = { title: "Inscription" };

export default function PageInscription() {
  return <EcranInscription />;
}
