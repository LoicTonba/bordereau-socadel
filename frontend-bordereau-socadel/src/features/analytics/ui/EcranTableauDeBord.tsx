/** Écran d'accueil du superviseur : KPI, évolution, répartition, couverture. */

"use client";

import { useState } from "react";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import { ErreurApi } from "@infra/http/client";
import { Alerte, cx } from "@shared/ui/primitives";

import { useTableauDeBord } from "../application/hooks";
import { CartesKpi } from "./CartesKpi";
import { ClassementAgents } from "./ClassementAgents";
import { CouvertureItineraires } from "./CouvertureItineraires";
import { GraphiqueEvolution } from "./GraphiqueEvolution";
import { RepartitionStatuts } from "./RepartitionStatuts";

const PERIODES = [
  { jours: 7, libelle: "dashboard.jours7" },
  { jours: 14, libelle: "dashboard.jours14" },
  { jours: 30, libelle: "dashboard.jours30" },
  { jours: 90, libelle: "dashboard.mois3" },
] as const satisfies readonly { jours: number; libelle: Cle }[];

function ilYA(jours: number): string {
  const date = new Date();
  date.setDate(date.getDate() - (jours - 1));
  return date.toISOString().slice(0, 10);
}

export function EcranTableauDeBord() {
  const t = useT();
  const [jours, setJours] = useState<number>(14);

  const { data, isFetching, error } = useTableauDeBord({
    debut: ilYA(jours),
    fin: new Date().toISOString().slice(0, 10),
  });

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">{t("dashboard.titre")}</h1>
          <p className="text-sm text-[var(--texte-doux)]">
            {t("dashboard.sousTitre")}
          </p>
        </div>

        {/* Les filtres tiennent sur une seule rangée, au-dessus des graphiques. */}
        <div
          role="group"
          aria-label={t("dashboard.periode")}
          className="flex rounded-lg border border-[var(--bordure-forte)] p-0.5"
        >
          {PERIODES.map((periode) => (
            <button
              key={periode.jours}
              type="button"
              aria-pressed={jours === periode.jours}
              onClick={() => setJours(periode.jours)}
              className={cx(
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                jours === periode.jours
                  ? "bg-socadel-600 text-white"
                  : "text-[var(--texte-doux)] hover:bg-[var(--fond-survol)]",
              )}
            >
              {t(periode.libelle)}
            </button>
          ))}
        </div>
      </header>

      {error instanceof ErreurApi && <Alerte>{error.message}</Alerte>}

      <div className={cx("space-y-4", isFetching && "opacity-70")}>
        {data && (
          <>
            <CartesKpi kpis={data.kpis} />

            <GraphiqueEvolution points={data.evolution} />

            <div className="grid gap-4 xl:grid-cols-2">
              <RepartitionStatuts repartition={data.repartitionStatuts} />
              <CouvertureItineraires couvertures={data.couvertureItineraires} />
            </div>

            <ClassementAgents agents={data.classementAgents} />
          </>
        )}

        {!data && isFetching && (
          <p className="py-16 text-center text-sm text-[var(--texte-tres-doux)]">
            {t("dashboard.chargement")}
          </p>
        )}
      </div>
    </div>
  );
}
