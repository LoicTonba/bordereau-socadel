import type { Metadata } from "next";

import { EcranOubli } from "@features/comptes/ui/EcransMotDePasse";

export const metadata: Metadata = { title: "Mot de passe oublié" };

export default function PageOubli() {
  return <EcranOubli />;
}
