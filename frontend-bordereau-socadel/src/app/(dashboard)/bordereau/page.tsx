import type { Metadata } from "next";

import { EcranBordereau } from "@features/collectes/ui/EcranBordereau";

export const metadata: Metadata = { title: "Bordereau" };

export default function PageBordereau() {
  return <EcranBordereau />;
}
