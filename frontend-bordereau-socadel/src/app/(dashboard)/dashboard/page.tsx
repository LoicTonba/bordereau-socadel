import type { Metadata } from "next";

import { EcranTableauDeBord } from "@features/analytics/ui/EcranTableauDeBord";

export const metadata: Metadata = { title: "Tableau de bord" };

export default function PageTableauDeBord() {
  return <EcranTableauDeBord />;
}
