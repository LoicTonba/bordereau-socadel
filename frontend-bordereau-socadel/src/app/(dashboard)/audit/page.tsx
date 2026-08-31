import type { Metadata } from "next";

import { EcranAudit } from "@features/audit/ui/EcranAudit";

export const metadata: Metadata = { title: "Audit et journal" };

export default function PageAudit() {
  return <EcranAudit />;
}
