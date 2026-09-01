import type { Metadata } from "next";

import { EcranRoles } from "@features/roles/ui/EcranRoles";

export const metadata: Metadata = { title: "Rôles et permissions" };

export default function PageRoles() {
  return <EcranRoles />;
}
