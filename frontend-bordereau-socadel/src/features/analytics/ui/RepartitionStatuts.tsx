/**
 * Répartition des lignes par statut.
 *
 * Barres horizontales plutôt qu'un camembert : les valeurs sont proches et les
 * libellés longs, deux cas où un secteur angulaire ne se compare pas.
 *
 * Les teintes sont celles des badges du tableau — le lecteur a déjà appris
 * « vert = abonné » en saisissant. Chaque barre porte son libellé et sa valeur :
 * la couleur ne fait que renforcer, elle ne porte jamais seule l'information.
 */

"use client";

import { STATUTS } from "@core/domain/statuts";
import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import type { StatutCollecte } from "@core/domain/types";
import { Carte, EtatVide } from "@shared/ui/primitives";

export function RepartitionStatuts({
  repartition,
}: {
  repartition: Record<string, number>;
}) {
  const t = useT();
  const entrees = Object.entries(repartition)
    .filter(([, total]) => total > 0)
    .sort(([, a], [, b]) => b - a);

  const total = entrees.reduce((somme, [, valeur]) => somme + valeur, 0);
  const maximum = Math.max(...entrees.map(([, valeur]) => valeur), 1);

  return (
    <Carte
      titre={t("repartition.titre")}
      description={
        total > 0
          ? t("repartition.sousTitre", { n: total.toLocaleString("fr-FR") })
          : undefined
      }
    >
      {entrees.length === 0 ? (
        <EtatVide
          titre={t("repartition.vide")}
          description={t("repartition.videAide")}
        />
      ) : (
        <ul className="space-y-3 p-5">
          {entrees.map(([cle, valeur]) => {
            const statut = STATUTS[cle as StatutCollecte];
            const libelle = statut ? t(`statut.${cle}` as Cle) : cle;
            const part = total > 0 ? (valeur / total) * 100 : 0;

            return (
              <li key={cle}>
                <div className="mb-1 flex items-baseline justify-between gap-3 text-xs">
                  <span className="font-medium">{libelle}</span>
                  <span className="chiffres text-[var(--texte-doux)]">
                    {valeur.toLocaleString("fr-FR")}
                    <span className="ml-1.5 text-[var(--texte-tres-doux)]">
                      {part.toFixed(1)} %
                    </span>
                  </span>
                </div>
                {/* Barre fine ancrée à zéro, extrémité arrondie de 4 px. */}
                <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--fond-survol)]">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.max((valeur / maximum) * 100, 1.5)}%`,
                      backgroundColor: statut?.couleur ?? "var(--serie-1)",
                    }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Carte>
  );
}
