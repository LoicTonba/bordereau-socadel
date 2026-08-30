import type { Metadata } from "next";

import { EcranConnexion } from "@features/auth/ui/EcranConnexion";

export const metadata: Metadata = {
  title: "Connexion",
};

export default function PageConnexion() {
  return <EcranConnexion />;
}
