/**
 * Racine du site.
 *
 * Il n'y a pas de page publique : la redirection est décidée côté client, une
 * fois la session revalidée, pour ne pas exposer d'écran intermédiaire.
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useSession } from "@features/auth/application/SessionProvider";

export default function PageAccueil() {
  const router = useRouter();
  const { utilisateur, chargement } = useSession();

  useEffect(() => {
    if (chargement) return;
    // Le superviseur connecté arrive sur l'affectation : c'est sa première
    // tâche de la journée, avant même de consulter les chiffres.
    router.replace(utilisateur ? "/affectations" : "/login");
  }, [chargement, utilisateur, router]);

  return (
    <div className="grid min-h-dvh place-items-center">
      <p className="text-sm text-[var(--texte-tres-doux)]">Chargement…</p>
    </div>
  );
}
