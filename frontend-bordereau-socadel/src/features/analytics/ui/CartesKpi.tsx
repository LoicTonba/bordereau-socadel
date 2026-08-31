/**
 * Bandeau de KPI.
 *
 * Un seul nombre par carte : ces indicateurs n'ont pas besoin d'un graphique,
 * la valeur *est* l'information, et elle est donc centrée et donnée en grand.
 * La variation par rapport à la période précédente est ce qui les rend
 * actionnables : sans elle, « 143 abonnements » ne dit pas si la journée est
 * bonne.
 *
 * Chaque carte porte une teinte qui lui est propre. Ce n'est pas décoratif :
 * cinq nombres alignés dans la même couleur se confondent, et l'œil qui revient
 * au tableau de bord cherche « la carte violette » avant de lire son libellé.
 * La teinte est attachée à l'indicateur, jamais à sa valeur : une carte ne
 * change pas de couleur parce que le chiffre baisse.
 */

"use client";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import type { CarteKpi } from "@core/domain/types";
import { cx } from "@shared/ui/primitives";

/** Teinte par indicateur : bandeau supérieur, pastille et chiffre. */
interface Teinte {
  bande: string;
  chiffre: string;
  fond: string;
}

const TEINTES: Record<string, Teinte> = {
  lignes_traitees: {
    bande: "bg-socadel-600",
    chiffre: "text-socadel-700 dark:text-socadel-300",
    fond: "bg-socadel-50/70 dark:bg-socadel-950/40",
  },
  abonnements: {
    bande: "bg-orange-500",
    chiffre: "text-orange-700 dark:text-orange-300",
    fond: "bg-orange-50/70 dark:bg-orange-950/30",
  },
  abonnements_confirmes: {
    bande: "bg-emerald-600",
    chiffre: "text-emerald-700 dark:text-emerald-300",
    fond: "bg-emerald-50/70 dark:bg-emerald-950/30",
  },
  taux_conversion: {
    bande: "bg-violet-600",
    chiffre: "text-violet-700 dark:text-violet-300",
    fond: "bg-violet-50/70 dark:bg-violet-950/30",
  },
  taux_fiabilite: {
    bande: "bg-amber-500",
    chiffre: "text-amber-700 dark:text-amber-300",
    fond: "bg-amber-50/70 dark:bg-amber-950/30",
  },
};

/** Teinte de repli, pour un indicateur que l'API ajouterait plus tard. */
const NEUTRE: Teinte = {
  bande: "bg-slate-400",
  chiffre: "text-[var(--texte)]",
  fond: "bg-[var(--fond-survol)]",
};

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
  const teinte = TEINTES[kpi.cle] ?? NEUTRE;
  const estPourcentage = kpi.unite === "%";
  const valeur = estPourcentage
    ? `${kpi.valeur.toFixed(1)} %`
    : kpi.valeur.toLocaleString("fr-FR");

  return (
    <div className="carte overflow-hidden text-center">
      {/* Un filet de couleur en tête : il identifie la carte sans empiéter
          sur la lisibilité du nombre, qui reste le sujet. */}
      <div aria-hidden className={cx("h-1 w-full", teinte.bande)} />
      <div className={cx("px-4 py-4", teinte.fond)}>
        <p className="text-xs font-medium text-[var(--texte-doux)]">
          {/* Le libellé vient traduit du dictionnaire ; celui de l'API sert
              de repli si une clé venait à manquer. */}
          {t(`kpi.${kpi.cle}` as Cle) || kpi.libelle}
        </p>
        <p
          className={cx(
            "chiffres mt-2 text-3xl font-semibold tracking-tight",
            teinte.chiffre,
          )}
        >
          {valeur}
        </p>
        <Variation variation={kpi.variation} />
      </div>
    </div>
  );
}

function Variation({ variation }: { variation: number | null }) {
  const t = useT();
  if (variation === null) {
    return (
      <p className="mt-1.5 text-[11px] text-[var(--texte-tres-doux)]">
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
        "chiffres mt-1.5 text-[11px] font-medium",
        stable
          ? "text-[var(--texte-tres-doux)]"
          : enHausse
            ? "text-green-700 dark:text-green-400"
            : "text-red-700 dark:text-red-400",
      )}
    >
      {stable
        ? t("dashboard.stable")
        : `${enHausse ? "▲" : "▼"} ${pourcentage.toFixed(1)} % ${t("dashboard.vsPeriode")}`}
    </p>
  );
}
