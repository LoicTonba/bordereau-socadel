/**
 * Bandeau de KPI.
 *
 * Un seul nombre par carte : ces indicateurs n'ont pas besoin d'un graphique,
 * la valeur *est* l'information. La variation par rapport à la période
 * précédente est ce qui les rend actionnables — sans elle, « 143 abonnements »
 * ne dit pas si la journée est bonne.
 */

"use client";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import type { CarteKpi } from "@core/domain/types";
import { cx } from "@shared/ui/primitives";

export function CartesKpi({ kpis }: { kpis: CarteKpi[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {kpis.map((kpi) => (
        <Tuile key={kpi.cle} kpi={kpi} />
      ))}
    </div>
  );
}

function Tuile({ kpi }: { kpi: CarteKpi }) {
  const t = useT();
  const estPourcentage = kpi.unite === "%";
  const valeur = estPourcentage
    ? `${kpi.valeur.toFixed(1)} %`
    : kpi.valeur.toLocaleString("fr-FR");

  return (
    <div className="carte p-4">
      <p className="text-xs font-medium text-[var(--texte-doux)]">
        {/* Le libellé vient traduit du dictionnaire ; celui de l'API sert
            de repli si une clé venait à manquer. */}
        {t(`kpi.${kpi.cle}` as Cle) || kpi.libelle}
      </p>
      <p className="chiffres mt-1.5 text-2xl font-semibold tracking-tight">{valeur}</p>
      <Variation variation={kpi.variation} />
    </div>
  );
}

function Variation({ variation }: { variation: number | null }) {
  const t = useT();
  if (variation === null) {
    return (
      <p className="mt-1 text-[11px] text-[var(--texte-tres-doux)]">
        {t("dashboard.pasDeComparaison")}
      </p>
    );
  }

  const pourcentage = Math.abs(variation * 100);
  const enHausse = variation > 0;
  const stable = Math.abs(variation) < 0.005;

  return (
    <p
      className={cx(
        "chiffres mt-1 text-[11px] font-medium",
        stable
          ? "text-[var(--texte-tres-doux)]"
          : enHausse
            ? "text-green-700"
            : "text-red-700",
      )}
    >
      {/* Le signe accompagne la couleur : l'information n'est jamais portée
          par la seule teinte. */}
      {stable
        ? `→ ${t("dashboard.stable")}`
        : `${enHausse ? "↑" : "↓"} ${pourcentage.toFixed(1)} %`}
      <span className="ml-1 font-normal text-[var(--texte-tres-doux)]">
        {t("dashboard.vsPrecedent")}
      </span>
    </p>
  );
}
