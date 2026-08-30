/**
 * Portrait d'un agent ou d'un utilisateur.
 *
 * Quand la photo manque — c'est le cas le plus fréquent au démarrage — on
 * affiche les initiales sur un fond dérivé du nom. La couleur est stable pour
 * une même personne, ce qui aide à la repérer dans une liste sans qu'on ait à
 * stocker quoi que ce soit.
 */

"use client";

import { useState } from "react";

import { cx } from "./primitives";

/** Teintes de repli, toutes lisibles avec du texte blanc. */
const TEINTES = [
  "#1a76b9",
  "#1f5fa0",
  "#0f766e",
  "#7e22ce",
  "#b45309",
  "#be123c",
  "#4d7c0f",
  "#0369a1",
];

function initiales(nom: string): string {
  const mots = nom.trim().split(/\s+/).filter(Boolean);
  if (mots.length === 0) return "?";
  if (mots.length === 1) return mots[0].slice(0, 2).toUpperCase();
  return (mots[0][0] + mots[mots.length - 1][0]).toUpperCase();
}

function teinte(nom: string): string {
  // Somme des codes de caractères : déterministe, donc la même personne garde
  // sa couleur d'un écran à l'autre.
  let total = 0;
  for (let i = 0; i < nom.length; i += 1) total += nom.charCodeAt(i);
  return TEINTES[total % TEINTES.length];
}

export function Avatar({
  nom,
  url,
  taille = 34,
  pastille = false,
  className,
}: {
  nom: string;
  url?: string | null;
  taille?: number;
  /** Ajoute la pastille verte de session active. */
  pastille?: boolean;
  className?: string;
}) {
  const [enEchec, setEnEchec] = useState(false);
  const afficherPhoto = Boolean(url) && !enEchec;

  return (
    <span
      className={cx("relative inline-flex shrink-0", className)}
      style={{ width: taille, height: taille }}
    >
      {afficherPhoto ? (
        // Balise native plutôt que next/image : l'URL vient de l'API, dont
        // l'hôte varie selon le déploiement.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url as string}
          alt={nom}
          width={taille}
          height={taille}
          onError={() => setEnEchec(true)}
          className="size-full rounded-full object-cover"
        />
      ) : (
        <span
          aria-hidden
          className="grid size-full place-items-center rounded-full font-semibold text-white"
          style={{
            backgroundColor: teinte(nom),
            fontSize: Math.max(10, taille * 0.36),
          }}
        >
          {initiales(nom)}
        </span>
      )}

      {pastille && (
        <span
          aria-hidden
          className="absolute right-0 bottom-0 rounded-full border-2 border-[var(--fond-carte)] bg-emerald-500"
          style={{ width: taille * 0.3, height: taille * 0.3 }}
        />
      )}
    </span>
  );
}
