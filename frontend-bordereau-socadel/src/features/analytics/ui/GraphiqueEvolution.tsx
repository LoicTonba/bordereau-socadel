/**
 * Courbe d'évolution de la collecte.
 *
 * Trois séries emboîtées — démarchés ⊃ déclarés ⊃ confirmés — sur **un seul
 * axe** : elles se comptent dans la même unité, un second axe inventerait une
 * corrélation absente des données.
 *
 * L'aqua passe sous le seuil de contraste de 3:1 sur fond blanc ; l'identité
 * des séries ne repose donc jamais sur la seule couleur : légende permanente,
 * étiquette directe sur le dernier point, et vue tableau accessible.
 */

"use client";

import { useState } from "react";
import {
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PointSerie } from "@core/domain/types";
import { Carte } from "@shared/ui/primitives";

import { AXE, GRILLE, SERIES_EVOLUTION } from "./palette";

export function GraphiqueEvolution({ points }: { points: PointSerie[] }) {
  const [vueTableau, setVueTableau] = useState(false);

  const donnees = points.map((point) => ({
    ...point,
    etiquette: formaterJourCourt(point.jour),
  }));

  return (
    <Carte
      titre="Évolution de la collecte"
      description="Ce que les agents ont démarché, déclaré, et ce que le référentiel confirme."
      actions={
        <button
          type="button"
          onClick={() => setVueTableau((actuel) => !actuel)}
          className="rounded-md border border-[var(--bordure-forte)] px-2.5 py-1 text-xs hover:bg-[var(--fond-survol)]"
        >
          {vueTableau ? "Voir le graphique" : "Voir les données"}
        </button>
      }
    >
      <Legende />

      {vueTableau ? (
        <TableauDonnees points={points} />
      ) : (
        <div className="h-72 px-2 pb-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={donnees}
              margin={{ top: 8, right: 56, bottom: 4, left: 0 }}
            >
              {/* Grille horizontale seule et pleine : le trait pointillé
                  ajoute du bruit sans rien apporter à la lecture. */}
              <CartesianGrid
                stroke={GRILLE}
                strokeWidth={1}
                vertical={false}
              />
              <XAxis
                dataKey="etiquette"
                tick={{ fontSize: 11, fill: AXE }}
                tickLine={false}
                axisLine={{ stroke: GRILLE }}
                minTickGap={16}
              />
              <YAxis
                tick={{ fontSize: 11, fill: AXE }}
                tickLine={false}
                axisLine={false}
                width={44}
                allowDecimals={false}
              />
              <Tooltip
                cursor={{ stroke: AXE, strokeWidth: 1 }}
                content={<Infobulle />}
              />

              {SERIES_EVOLUTION.map((serie) => (
                <Line
                  key={serie.cle}
                  type="monotone"
                  dataKey={serie.cle}
                  name={serie.libelle}
                  stroke={serie.couleur}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--fond-carte)" }}
                  isAnimationActive={false}
                >
                  {/* Étiquette directe sur le dernier point : la valeur de fin
                      de série se lit sans passer par la légende. */}
                  <LabelList
                    dataKey={serie.cle}
                    content={(proprietes) => (
                      <EtiquetteFinale
                        {...proprietes}
                        dernierIndex={donnees.length - 1}
                      />
                    )}
                  />
                </Line>
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Carte>
  );
}

function Legende() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 px-5 pt-3.5">
      {SERIES_EVOLUTION.map((serie) => (
        <span
          key={serie.cle}
          className="flex items-center gap-1.5 text-xs text-[var(--texte-doux)]"
        >
          <span
            aria-hidden
            className="h-0.5 w-4 rounded-full"
            style={{ backgroundColor: serie.couleur }}
          />
          {serie.libelle}
        </span>
      ))}
    </div>
  );
}

interface ProprietesInfobulle {
  active?: boolean;
  label?: string;
  payload?: { dataKey: string; value: number; color: string; name: string }[];
}

function Infobulle({ active, label, payload }: ProprietesInfobulle) {
  if (!active || !payload?.length) return null;

  return (
    <div className="carte px-3 py-2 text-xs">
      <p className="mb-1.5 font-medium">{label}</p>
      <ul className="space-y-1">
        {payload.map((entree) => (
          <li key={entree.dataKey} className="flex items-center gap-2">
            <span
              aria-hidden
              className="size-2 shrink-0 rounded-full"
              style={{ backgroundColor: entree.color }}
            />
            {/* Le libellé reste en encre de texte : la couleur est portée par
                la pastille, jamais par les mots. */}
            <span className="text-[var(--texte-doux)]">{entree.name}</span>
            <span className="chiffres ml-auto font-medium">
              {entree.value.toLocaleString("fr-FR")}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TableauDonnees({ points }: { points: PointSerie[] }) {
  return (
    <div className="max-h-72 overflow-auto">
      <table className="w-full border-collapse text-xs">
        <thead className="sticky top-0 bg-[var(--fond-survol)]">
          <tr className="text-left">
            <th scope="col" className="px-4 py-2 font-semibold">
              Jour
            </th>
            {SERIES_EVOLUTION.map((serie) => (
              <th key={serie.cle} scope="col" className="px-4 py-2 text-right font-semibold">
                {serie.libelle}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {points.map((point) => (
            <tr key={point.jour} className="border-t border-[var(--bordure)]">
              <td className="px-4 py-1.5">{formaterJourLong(point.jour)}</td>
              <td className="chiffres px-4 py-1.5 text-right">{point.collectes}</td>
              <td className="chiffres px-4 py-1.5 text-right">{point.abonnements}</td>
              <td className="chiffres px-4 py-1.5 text-right">{point.confirmes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formaterJourCourt(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}

function formaterJourLong(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleDateString("fr-FR", {
        weekday: "short",
        day: "2-digit",
        month: "long",
      });
}

interface ProprietesEtiquette {
  x?: string | number;
  y?: string | number;
  value?: string | number;
  index?: number;
  dernierIndex: number;
}

/** N'affiche la valeur qu'au bout de la courbe : un nombre sur chaque point
 *  rendrait le graphique illisible. */
function EtiquetteFinale({
  x,
  y,
  value,
  index,
  dernierIndex,
}: ProprietesEtiquette) {
  if (index !== dernierIndex || value === undefined) return null;

  return (
    <text
      x={Number(x) + 8}
      y={Number(y)}
      dy={4}
      fontSize={11}
      fontWeight={600}
      // L'étiquette porte l'encre de texte, pas la couleur de la série.
      fill="var(--texte)"
    >
      {Number(value).toLocaleString("fr-FR")}
    </text>
  );
}
