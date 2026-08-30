/**
 * Barre de pagination du tableau.
 *
 * Elle affiche l'étendue exacte (« 26–50 sur 1 204 ») plutôt qu'un simple
 * numéro de page : sur un référentiel de cette taille, le superviseur a besoin
 * de savoir où il en est dans le volume, pas seulement dans la liste.
 */

"use client";

import type { MetaPagination } from "@core/domain/types";

import { Bouton, Selecteur } from "./primitives";

const TAILLES = [25, 50, 100, 200];

export function Pagination({
  meta,
  onPage,
  onTaille,
}: {
  meta: MetaPagination;
  onPage: (page: number) => void;
  onTaille: (taille: number) => void;
}) {
  const premier = meta.total === 0 ? 0 : (meta.page - 1) * meta.taille + 1;
  const dernier = Math.min(meta.page * meta.taille, meta.total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--bordure)] px-4 py-3">
      <p className="chiffres text-xs text-[var(--texte-doux)]">
        <strong>{premier.toLocaleString("fr-FR")}</strong>–
        <strong>{dernier.toLocaleString("fr-FR")}</strong> sur{" "}
        <strong>{meta.total.toLocaleString("fr-FR")}</strong> ligne
        {meta.total > 1 ? "s" : ""}
      </p>

      <div className="flex items-center gap-2">
        <Selecteur
          aria-label="Lignes par page"
          value={meta.taille}
          onChange={(evenement) => onTaille(Number(evenement.target.value))}
          className="!w-auto !py-1.5 text-xs"
        >
          {TAILLES.map((taille) => (
            <option key={taille} value={taille}>
              {taille} / page
            </option>
          ))}
        </Selecteur>

        <Bouton
          variante="secondaire"
          taille="sm"
          disabled={!meta.aPagePrecedente}
          onClick={() => onPage(meta.page - 1)}
        >
          Précédent
        </Bouton>

        <span className="chiffres px-1 text-xs text-[var(--texte-doux)]">
          {meta.page} / {Math.max(meta.nombreDePages, 1)}
        </span>

        <Bouton
          variante="secondaire"
          taille="sm"
          disabled={!meta.aPageSuivante}
          onClick={() => onPage(meta.page + 1)}
        >
          Suivant
        </Bouton>
      </div>
    </div>
  );
}
