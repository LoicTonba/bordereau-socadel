/**
 * Tableau du bordereau.
 *
 * C'est l'écran de travail du superviseur : il y retrouve les clients confiés
 * aux agents et y reporte, ligne à ligne, ce que chacun a réalisé.
 */

"use client";

import { useMemo, useState } from "react";

import { useT } from "@core/i18n/PreferencesProvider";
import { STATUTS, VERDICTS } from "@core/domain/statuts";
import type { Cle } from "@core/i18n/messages";
import type { LigneBordereau } from "@core/domain/types";
import { Badge, cx, EtatVide } from "@shared/ui/primitives";

interface Colonne {
  cle: string;
  libelle: Cle;
  /** Clé de tri côté serveur ; absente si la colonne n'est pas triable. */
  tri?: string;
  aligneADroite?: boolean;
}

/** `libelle` porte la clé de traduction, résolue au rendu. */
const COLONNES: Colonne[] = [
  { cle: "client", libelle: "bordereau.client", tri: "nom_client" },
  { cle: "refGeo", libelle: "bordereau.refGeo", tri: "ref_geo" },
  {
    cle: "itineraire",
    libelle: "bordereau.itineraire",
    tri: "code_itineraire",
    aligneADroite: true,
  },
  { cle: "compteur", libelle: "bordereau.compteur" },
  { cle: "numero", libelle: "bordereau.numeroCollecte" },
  { cle: "statut", libelle: "bordereau.statut", tri: "statut" },
  { cle: "verdict", libelle: "bordereau.verification", tri: "verdict" },
  { cle: "date", libelle: "bordereau.date", tri: "date_collecte" },
];

export function TableauBordereau({
  lignes,
  chargement,
  selection,
  onSelection,
  onEditer,
  tri,
  ordre,
  onTrier,
}: {
  lignes: LigneBordereau[];
  chargement: boolean;
  selection: Set<string>;
  onSelection: (selection: Set<string>) => void;
  onEditer: (ligne: LigneBordereau) => void;
  tri?: string;
  ordre?: "asc" | "desc";
  onTrier: (tri: string) => void;
}) {
  const t = useT();
  const [survolee, setSurvolee] = useState<string | null>(null);

  const toutesSelectionnees = useMemo(
    () => lignes.length > 0 && lignes.every((ligne) => selection.has(ligne.id)),
    [lignes, selection],
  );

  function basculerTout() {
    if (toutesSelectionnees) {
      // On ne vide que la page courante : une sélection faite sur une autre
      // page doit survivre à la navigation.
      const reste = new Set(selection);
      lignes.forEach((ligne) => reste.delete(ligne.id));
      onSelection(reste);
    } else {
      onSelection(new Set([...selection, ...lignes.map((ligne) => ligne.id)]));
    }
  }

  function basculerLigne(id: string) {
    const suivante = new Set(selection);
    if (suivante.has(id)) suivante.delete(id);
    else suivante.add(id);
    onSelection(suivante);
  }

  if (!chargement && lignes.length === 0) {
    return (
      <EtatVide
        titre={t("bordereau.vide")}
        description={t("bordereau.videAide")}
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1000px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-[var(--bordure)] bg-[var(--fond-survol)] text-left">
            <th scope="col" className="w-10 px-3 py-2.5">
              <input
                type="checkbox"
                aria-label={t("bordereau.client")}
                checked={toutesSelectionnees}
                onChange={basculerTout}
                className="size-4 accent-socadel-600"
              />
            </th>
            {COLONNES.map((colonne) => (
              <th
                key={colonne.cle}
                scope="col"
                className={cx(
                  "px-3 py-2.5 text-xs font-semibold text-[var(--texte-doux)]",
                  colonne.aligneADroite && "text-right",
                )}
              >
                {colonne.tri ? (
                  <button
                    type="button"
                    onClick={() => onTrier(colonne.tri!)}
                    className="inline-flex items-center gap-1 hover:text-[var(--texte)]"
                  >
                    {t(colonne.libelle)}
                    {tri === colonne.tri && (
                      <span aria-hidden>{ordre === "asc" ? "↑" : "↓"}</span>
                    )}
                  </button>
                ) : (
                  t(colonne.libelle)
                )}
              </th>
            ))}
            <th scope="col" className="w-20 px-3 py-2.5 text-right text-xs font-semibold text-[var(--texte-doux)]">
              {t("bordereau.action")}
            </th>
          </tr>
        </thead>

        <tbody className={cx(chargement && "opacity-55")}>
          {lignes.map((ligne) => {
            const statut = STATUTS[ligne.statut];
            const verdict = VERDICTS[ligne.verdict];
            const selectionnee = selection.has(ligne.id);

            return (
              <tr
                key={ligne.id}
                onMouseEnter={() => setSurvolee(ligne.id)}
                onMouseLeave={() => setSurvolee(null)}
                className={cx(
                  "border-b border-[var(--bordure)] transition-colors",
                  selectionnee
                    ? "bg-socadel-50/70"
                    : survolee === ligne.id && "bg-[var(--fond-survol)]",
                )}
              >
                <td className="px-3 py-2.5">
                  <input
                    type="checkbox"
                    aria-label={ligne.nomClient ?? ligne.serviceNo}
                    checked={selectionnee}
                    onChange={() => basculerLigne(ligne.id)}
                    className="size-4 accent-socadel-600"
                  />
                </td>

                <td className="px-3 py-2.5">
                  <p className="font-medium">{ligne.nomClient ?? "—"}</p>
                  <p className="chiffres text-[11px] text-[var(--texte-tres-doux)]">
                    {ligne.serviceNo}
                  </p>
                </td>

                <td className="chiffres px-3 py-2.5 text-xs text-[var(--texte-doux)]">
                  {ligne.refGeo ?? "—"}
                </td>

                <td className="chiffres px-3 py-2.5 text-right text-xs">
                  {ligne.codeItineraire ?? "—"}
                </td>

                <td className="chiffres px-3 py-2.5 text-xs text-[var(--texte-doux)]">
                  {ligne.numeroCompteur ?? "—"}
                </td>

                <td className="chiffres px-3 py-2.5 text-xs">
                  {ligne.numeroCollecte ?? (
                    <span className="text-[var(--texte-tres-doux)]">—</span>
                  )}
                </td>

                <td className="px-3 py-2.5">
                  <Badge
                    fond={statut.fond}
                    texte={statut.texte}
                    titre={t(`statut.${ligne.statut}.aide` as Cle)}
                  >
                    {t(`statut.${ligne.statut}` as Cle)}
                  </Badge>
                </td>

                <td className="px-3 py-2.5">
                  <Badge
                    fond={verdict.fond}
                    texte={verdict.texte}
                    titre={t(`verdict.${ligne.verdict}.aide` as Cle)}
                  >
                    {t(`verdict.${ligne.verdict}` as Cle)}
                  </Badge>
                </td>

                <td className="chiffres px-3 py-2.5 text-xs text-[var(--texte-doux)]">
                  {formaterDate(ligne.dateCollecte)}
                </td>

                <td className="px-3 py-2.5 text-right">
                  <button
                    type="button"
                    onClick={() => onEditer(ligne)}
                    className="rounded-md px-2 py-1 text-xs font-medium text-socadel-700 hover:bg-socadel-50"
                  >
                    {t("bordereau.saisir")}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function formaterDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit" });
}
