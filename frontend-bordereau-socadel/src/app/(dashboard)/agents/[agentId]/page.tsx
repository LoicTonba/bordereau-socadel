/** Portefeuille d'un agent, vu par le superviseur. */

import { EcranPortefeuille } from "@features/agents/ui/EcranPortefeuille";

export default async function PagePortefeuilleAgent({
  params,
}: {
  // Depuis Next 15, `params` est une promesse : elle doit être attendue.
  params: Promise<{ agentId: string }>;
}) {
  const { agentId } = await params;
  return <EcranPortefeuille agentId={agentId} />;
}
