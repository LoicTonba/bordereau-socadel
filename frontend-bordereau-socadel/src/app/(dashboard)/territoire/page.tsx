import type { Metadata } from "next";

import { EcranTerritoire } from "@features/territoire/ui/EcranTerritoire";

export const metadata: Metadata = { title: "Territoire" };

export default function PageTerritoire() {
  return <EcranTerritoire />;
}
