/**
 * Espace de l'agent de terrain — son unique écran.
 *
 * L'identifiant vient de la session : un agent ne peut pas viser un autre
 * portefeuille, et l'API le refuserait de toute façon.
 */

"use client";

import { useSession } from "@features/auth/application/SessionProvider";
import { EcranPortefeuille } from "@features/agents/ui/EcranPortefeuille";
import { useT } from "@core/i18n/PreferencesProvider";

export default function PageMonEspace() {
  const { utilisateur } = useSession();
  const t = useT();

  if (!utilisateur?.agentId) {
    return (
      <p className="py-16 text-center text-sm text-[var(--texte-tres-doux)]">
        {t("portefeuille.aucunAide")}
      </p>
    );
  }

  return <EcranPortefeuille agentId={utilisateur.agentId} estMonEspace />;
}
