/**
 * Sélecteur d'agence de l'écran de connexion.
 *
 * SOCADEL compte 181 agences : une liste déroulante native serait
 * impraticable, et personne ne la parcourt jusqu'à Ngaoundéré. La recherche
 * filtre sur le nom, la division et la direction, ce qui permet de taper aussi
 * bien « ESSOS » que « DOUALA ».
 */

"use client";

import { useMemo, useState } from "react";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Agence } from "@core/domain/types";
import { Champ, cx } from "@shared/ui/primitives";

/** Au-delà, la liste défile plutôt que d'allonger la page indéfiniment. */
const RESULTATS_MAX = 40;

interface Proprietes {
  agences: Agence[];
  chargement: boolean;
  indisponible: boolean;
  /** Le national n'est proposé qu'aux profils qui le portent réellement. */
  autoriserNational: boolean;
  valeur: string | null;
  onChange: (agence: string | null) => void;
}

export function ChoixAgence({
  agences,
  chargement,
  indisponible,
  autoriserNational,
  valeur,
  onChange,
}: Proprietes) {
  const t = useT();
  const [terme, setTerme] = useState("");

  const resultats = useMemo(() => {
    const recherche = terme.trim().toLowerCase();
    if (!recherche) return agences.slice(0, RESULTATS_MAX);
    return agences
      .filter((a) =>
        [a.nom, a.division, a.region]
          .filter(Boolean)
          .some((champ) => champ!.toLowerCase().includes(recherche)),
      )
      .slice(0, RESULTATS_MAX);
  }, [agences, terme]);

  return (
    <div className="space-y-3">
      <Champ
        name="rechercheAgence"
        libelle={t("poste.agence.recherche")}
        placeholder={t("poste.agence.placeholder")}
        autoComplete="off"
        value={terme}
        onChange={(evenement) => setTerme(evenement.target.value)}
      />

      {indisponible && (
        <p className="text-xs text-amber-600">{t("poste.agence.indisponible")}</p>
      )}

      <div
        role="listbox"
        aria-label={t("poste.agence.titre")}
        className="max-h-64 overflow-y-auto rounded-lg border border-[var(--bordure)]"
      >
        {autoriserNational && (
          <OptionAgence
            selectionnee={valeur === null}
            titre={t("poste.agence.nationale")}
            onClick={() => onChange(null)}
          />
        )}

        {chargement && (
          <p className="px-3 py-4 text-sm text-[var(--texte-tres-doux)]">
            {t("poste.agence.chargement")}
          </p>
        )}

        {!chargement && resultats.length === 0 && (
          <p className="px-3 py-4 text-sm text-[var(--texte-tres-doux)]">
            {t("poste.agence.aucune")}
          </p>
        )}

        {resultats.map((agence) => (
          <OptionAgence
            key={agence.nom}
            selectionnee={valeur === agence.nom}
            titre={agence.nom}
            detail={[agence.division, agence.region].filter(Boolean).join(", ")}
            onClick={() => onChange(agence.nom)}
          />
        ))}
      </div>

      {agences.length > 0 && (
        <p className="text-xs text-[var(--texte-tres-doux)]">
          {t("poste.agence.nombre", { n: agences.length })}
        </p>
      )}
    </div>
  );
}

function OptionAgence({
  selectionnee,
  titre,
  detail,
  onClick,
}: {
  selectionnee: boolean;
  titre: string;
  detail?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={selectionnee}
      onClick={onClick}
      className={cx(
        "flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left",
        "border-b border-[var(--bordure)] last:border-b-0 transition-colors",
        selectionnee
          ? "bg-socadel-50 dark:bg-socadel-950"
          : "hover:bg-[var(--fond-survol)]",
      )}
    >
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium">{titre}</span>
        {detail && (
          <span className="block truncate text-xs text-[var(--texte-tres-doux)]">
            {detail}
          </span>
        )}
      </span>
      {selectionnee && (
        <span aria-hidden className="text-socadel-600 dark:text-socadel-400">
          <svg viewBox="0 0 20 20" className="size-4" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0L3.3 9.7a1 1 0 1 1 1.4-1.4l3.8 3.8 6.8-6.8a1 1 0 0 1 1.4 0Z"
              clipRule="evenodd"
            />
          </svg>
        </span>
      )}
    </button>
  );
}
