import type { Metadata } from "next";

import { EcranAgents } from "@features/agents/ui/EcranAgents";

export const metadata: Metadata = { title: "Agents" };

export default function PageAgents() {
  return <EcranAgents />;
}
