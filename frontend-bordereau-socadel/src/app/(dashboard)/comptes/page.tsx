import type { Metadata } from "next";

import { EcranComptes } from "@features/comptes/ui/EcranComptes";

export const metadata: Metadata = { title: "Comptes" };

export default function PageComptes() {
  return <EcranComptes />;
}
