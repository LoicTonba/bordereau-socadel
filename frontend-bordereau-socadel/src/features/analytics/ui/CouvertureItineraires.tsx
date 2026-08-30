/**
 * Couverture des itinéraires.
 *
 * Répond à la question que le superviseur pose chaque matin : quels itinéraires
 * sont déjà couverts, et combien de portes restent à faire. Une seule série,
 * donc une seule teinte — colorer chaque barre selon sa longueur ne ferait que
 * ré-encoder ce que la barre montre déjà.
 */

"use client";

import type { CouvertureItineraire } from "@core/domain/types";
import { Carte, EtatVide } from "@shared/ui/primitives";

export function CouvertureItineraires({
  couvertures,
}: {
  couvertures: CouvertureItineraire[];
}) {
  return (
    <Carte
      titre="Couverture des itinéraires"
      description="Part des clients déjà démarchés sur chaque tournée."
    >
      {couvertures.length === 0 ? (
        <EtatVide
          titre="Aucun itinéraire travaillé"
          description="Affectez un itinéraire à un agent pour suivre sa couverture ici."
        />
      ) : (
        <ul className="divide-y divide-[var(--bordure)]">
          {couvertures.map((couverture) => {
            const pourcentage = couverture.tauxCouverture * 100;
            const restants = Math.max(
              couverture.clientsTotal - couverture.clientsTraites,
              0,
            );

            return (
              <li key={couverture.codeItineraire} className="px-5 py-3">
                <div className="mb-1.5 flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <span className="chiffres text-sm font-medium">
                      Itinéraire {couverture.codeItineraire}
                    </span>
                    {couverture.agence && (
                      <span className="ml-2 text-xs text-[var(--texte-tres-doux)]">
                        {couverture.agence}
                      </span>
                    )}
                  </div>
                  <span className="chiffres text-xs text-[var(--texte-doux)]">
                    {couverture.clientsTraites.toLocaleString("fr-FR")} /{" "}
                    {couverture.clientsTotal.toLocaleString("fr-FR")}
                    <span className="ml-1.5 font-medium text-[var(--texte)]">
                      {pourcentage.toFixed(0)} %
                    </span>
                  </span>
                </div>

                <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--fond-survol)]">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.max(pourcentage, 1.5)}%`,
                      backgroundColor: "var(--serie-1)",
                    }}
                  />
                </div>

                <p className="mt-1 text-[11px] text-[var(--texte-tres-doux)]">
                  {couverture.abonnements.toLocaleString("fr-FR")} abonnement(s)
                  {restants > 0
                    ? ` · ${restants.toLocaleString("fr-FR")} client(s) restant(s)`
                    : " · itinéraire terminé"}
                </p>
              </li>
            );
          })}
        </ul>
      )}
    </Carte>
  );
}
