/**
 * Indicateur de robustesse du mot de passe.
 *
 * Il montre où l'on en est et, surtout, <b>ce qui manque</b> : une jauge seule
 * laisse l'utilisateur deviner. Les motifs viennent du serveur, ce sont ceux-là
 * mêmes qui refuseront l'inscription.
 */

"use client";

import type { ForceMotDePasse } from "@core/domain/types";
import { cx } from "@shared/ui/primitives";

const TEINTES = [
  "bg-red-500",
  "bg-red-500",
  "bg-amber-500",
  "bg-socadel-500",
  "bg-emerald-500",
] as const;

export function JaugeMotDePasse({ force }: { force: ForceMotDePasse | null }) {
  if (!force) return null;

  const niveau = Math.max(0, Math.min(4, force.score));

  return (
    <div className="space-y-1.5">
      <div className="flex gap-1" aria-hidden>
        {[0, 1, 2, 3].map((index) => (
          <span
            key={index}
            className={cx(
              "h-1 flex-1 rounded-full transition-colors",
              index < niveau ? TEINTES[niveau] : "bg-[var(--bordure)]",
            )}
          />
        ))}
      </div>

      <p
        // Le message est annoncé aux lecteurs d'écran, pour qui la jauge
        // colorée ne dit strictement rien.
        aria-live="polite"
        className={cx(
          "text-xs",
          force.acceptable ? "text-emerald-600" : "text-[var(--texte-doux)]",
        )}
      >
        {force.libelle}
        {force.motifs.length > 0 && ` : ${force.motifs.join(", ")}`}
      </p>
    </div>
  );
}
