import type { Metadata } from "next";

import { EcranAffectation } from "@features/itineraires/ui/EcranAffectation";

export const metadata: Metadata = { title: "Affectations" };

export default function PageAffectations() {
  return <EcranAffectation />;
}
