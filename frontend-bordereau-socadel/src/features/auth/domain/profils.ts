/**
 * Les quatre profils, du plus large au plus restreint.
 *
 * L'ordre est celui de la hiérarchie des rangs, pas un ordre alphabétique :
 * l'écran de connexion doit rendre lisible d'un coup d'œil que le super
 * utilisateur porte tout et que l'agent de terrain ne porte presque rien.
 */

import type { Role } from "@core/domain/types";

export interface Profil {
  role: Role;
  /** Organisation d'appartenance, affichée sous le nom du rôle. */
  maison: string;
  /** Écran d'accueil naturel du profil. */
  accueil: string;
  /** Vrai si le profil travaille dans une agence donnée. */
  ancreDansUneAgence: boolean;
}

export const PROFILS: readonly Profil[] = [
  {
    role: "SUPER_UTILISATEUR",
    maison: "NEXT LTD",
    accueil: "/dashboard",
    ancreDansUneAgence: false,
  },
  {
    role: "ADMINISTRATEUR",
    maison: "SOCADEL",
    accueil: "/dashboard",
    ancreDansUneAgence: false,
  },
  {
    role: "SUPERVISEUR",
    maison: "SOCADEL",
    accueil: "/affectations",
    ancreDansUneAgence: true,
  },
  {
    role: "AGENT_TERRAIN",
    maison: "SOCADEL",
    accueil: "/mon-espace",
    ancreDansUneAgence: true,
  },
] as const;

export function profil(role: Role): Profil {
  return PROFILS.find((p) => p.role === role) ?? PROFILS[2];
}

/**
 * Où atterrir une fois la session ouverte.
 *
 * Le superviseur qui a noté les itinéraires annoncés par son agent arrive
 * directement sur le bordereau filtré ; c'est tout l'intérêt de les avoir
 * saisis avant de se connecter. Sans itinéraires, il arrive sur l'écran
 * d'affectation, sa première tâche de la journée.
 */
export function destination(role: Role, itineraires: readonly number[]): string {
  if (role === "SUPERVISEUR" && itineraires.length > 0) {
    const parametres = itineraires.map((code) => `itineraire=${code}`).join("&");
    return `/bordereau?${parametres}`;
  }
  return profil(role).accueil;
}

/**
 * Lit les codes qu'un superviseur saisit à la volée.
 *
 * L'agent les récite de mémoire ; la saisie accepte donc les espaces, les
 * virgules et les points-virgules sans rien exiger. Les doublons sont écartés,
 * l'ordre de dictée est conservé.
 */
export function lireCodesItineraires(saisie: string): {
  codes: number[];
  invalide: boolean;
} {
  const morceaux = saisie
    .split(/[\s,;]+/)
    .map((m) => m.trim())
    .filter(Boolean);

  const codes: number[] = [];
  let invalide = false;

  for (const morceau of morceaux) {
    if (!/^\d+$/.test(morceau)) {
      invalide = true;
      continue;
    }
    const code = Number(morceau);
    if (!codes.includes(code)) codes.push(code);
  }

  return { codes, invalide };
}
