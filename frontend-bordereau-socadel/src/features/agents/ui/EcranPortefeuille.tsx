/**
 * Portefeuille d'un agent.
 *
 * Le même écran sert deux lecteurs : l'agent connecté, pour qui c'est le seul
 * écran de la plateforme, et le superviseur, qui l'ouvre avant de confier une
 * tournée de plus. Le périmètre est décidé par l'API, pas ici.
 */

"use client";

import { useState } from "react";

import { useT } from "@core/i18n/PreferencesProvider";
import type { ItineraireDuJour, PerformanceAgent } from "@core/domain/types";
import { ErreurApi } from "@infra/http/client";
import { Avatar } from "@shared/ui/Avatar";
import { Alerte, Carte, cx, EtatVide } from "@shared/ui/primitives";

import { usePortefeuille } from "../application/hooks";

const PERIODES = [7, 14, 30, 90] as const;

export function EcranPortefeuille({
  agentId,
  estMonEspace = false,
}: {
  agentId: string;
  estMonEspace?: boolean;
}) {
  const t = useT();
  const [jours, setJours] = useState<number>(30);
  const { data, isFetching, error } = usePortefeuille(agentId, jours);

  const libellesPeriode = {
    7: t("dashboard.jours7"),
    14: t("dashboard.jours14"),
    30: t("dashboard.jours30"),
    90: t("dashboard.mois3"),
  } as const;

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex items-center gap-3">
          {data && (
            <Avatar
              nom={data.agent.nomComplet}
              url={data.agent.photoUrl}
              taille={44}
            />
          )}
          <div>
            <h1 className="text-lg font-semibold">
              {estMonEspace
                ? t("portefeuille.titre")
                : t("portefeuille.titreAutre", {
                    nom: data?.agent.nomComplet ?? "",
                  })}
            </h1>
            <p className="text-sm text-[var(--texte-doux)]">
              {data
                ? `${data.agent.matricule}${
                    data.agent.zoneRattachement
                      ? ` · ${data.agent.zoneRattachement}`
                      : ""
                  }`
                : t("portefeuille.sousTitre")}
            </p>
          </div>
        </div>

        <div
          role="group"
          aria-label={t("dashboard.periode")}
          className="flex rounded-lg border border-[var(--bordure-forte)] p-0.5"
        >
          {PERIODES.map((valeur) => (
            <button
              key={valeur}
              type="button"
              aria-pressed={jours === valeur}
              onClick={() => setJours(valeur)}
              className={cx(
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                jours === valeur
                  ? "bg-socadel-600 text-white"
                  : "text-[var(--texte-doux)] hover:bg-[var(--fond-survol)]",
              )}
            >
              {libellesPeriode[valeur]}
            </button>
          ))}
        </div>
      </header>

      {error instanceof ErreurApi && <Alerte>{error.message}</Alerte>}

      {data && (
        <div className={cx("space-y-4", isFetching && "opacity-70")}>
          <Chiffres performance={data.performance} />

          <Carte
            titre={t("portefeuille.itineraires")}
            description={`${data.debut} → ${data.fin}`}
          >
            {data.itineraires.length === 0 ? (
              <EtatVide
                titre={t("portefeuille.aucun")}
                description={t("portefeuille.aucunAide")}
              />
            ) : (
              <ul className="divide-y divide-[var(--bordure)]">
                {data.itineraires.map((itineraire) => (
                  <LigneItineraire
                    key={itineraire.affectationId}
                    itineraire={itineraire}
                  />
                ))}
              </ul>
            )}
          </Carte>

          {estMonEspace && (
            <p className="px-1 text-xs text-[var(--texte-tres-doux)]">
              {t("portefeuille.mentionSaisie")}
            </p>
          )}
        </div>
      )}

      {!data && isFetching && (
        <p className="py-16 text-center text-sm text-[var(--texte-tres-doux)]">
          {t("commun.chargement")}
        </p>
      )}
    </div>
  );
}

function Chiffres({ performance }: { performance: PerformanceAgent }) {
  const t = useT();

  const tuiles = [
    {
      libelle: t("portefeuille.affectes"),
      valeur: performance.lignesAffectees.toLocaleString("fr-FR"),
    },
    {
      libelle: t("portefeuille.traites"),
      valeur: performance.lignesTraitees.toLocaleString("fr-FR"),
    },
    {
      libelle: t("kpi.abonnements"),
      valeur: performance.abonnementsDeclares.toLocaleString("fr-FR"),
    },
    {
      libelle: t("kpi.abonnements_confirmes"),
      valeur: performance.abonnementsConfirmes.toLocaleString("fr-FR"),
      accent: "vert" as const,
    },
    {
      libelle: t("kpi.taux_fiabilite"),
      valeur: `${(performance.tauxFiabilite * 100).toFixed(1)} %`,
      accent:
        performance.tauxFiabilite >= 0.85
          ? ("vert" as const)
          : performance.tauxFiabilite >= 0.6
            ? ("ambre" as const)
            : ("rouge" as const),
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {tuiles.map((tuile) => (
        <div key={tuile.libelle} className="carte p-4">
          <p className="text-xs font-medium text-[var(--texte-doux)]">
            {tuile.libelle}
          </p>
          <p
            className={cx(
              "chiffres mt-1.5 text-2xl font-semibold tracking-tight",
              tuile.accent === "vert" && "text-green-700",
              tuile.accent === "ambre" && "text-amber-700",
              tuile.accent === "rouge" && "text-red-700",
            )}
          >
            {tuile.valeur}
          </p>
        </div>
      ))}

      {performance.lignesEnAttenteDeVerification > 0 && (
        <p className="col-span-full text-xs text-[var(--texte-tres-doux)]">
          {t("portefeuille.enAttente")} :{" "}
          <strong className="chiffres">
            {performance.lignesEnAttenteDeVerification}
          </strong>
        </p>
      )}
    </div>
  );
}

function LigneItineraire({ itineraire }: { itineraire: ItineraireDuJour }) {
  const t = useT();
  const pourcentage = itineraire.tauxCouverture * 100;
  const restants = Math.max(
    itineraire.clientsTotal - itineraire.clientsTraites,
    0,
  );

  return (
    <li className="px-5 py-3">
      <div className="mb-1.5 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <span className="chiffres text-sm font-medium">
            {itineraire.libelle}
          </span>
          <span className="ml-2 text-xs text-[var(--texte-tres-doux)]">
            {itineraire.dateTravail}
          </span>
        </div>
        <span className="chiffres text-xs text-[var(--texte-doux)]">
          {itineraire.clientsTraites.toLocaleString("fr-FR")} /{" "}
          {itineraire.clientsTotal.toLocaleString("fr-FR")}
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
        {t("couverture.abonnements", { n: itineraire.abonnements })}
        {restants > 0
          ? ` · ${t("couverture.restants", { n: restants })}`
          : ` · ${t("couverture.termine")}`}
      </p>
    </li>
  );
}
