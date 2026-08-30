/**
 * Couleurs et vocabulaire des statuts.
 *
 * Les **libellés** sont dans les dictionnaires de traduction (`statut.*`,
 * `verdict.*`, `responsable.*`) ; ce module ne porte plus que les couleurs,
 * qui ne dépendent pas de la langue. Badge du tableau, légende du graphique et
 * sélecteur de saisie puisent donc au même endroit.
 */

import type {
  Responsable,
  StatutCollecte,
  VerdictVerification,
} from "./types";

export interface Teinte {
  couleur: string;
  fond: string;
  texte: string;
}

export const STATUTS: Record<StatutCollecte, Teinte> = {
  A_TRAITER: {
    couleur: "var(--color-statut-attente)",
    fond: "rgb(148 163 184 / 0.14)",
    texte: "#475569",
  },
  ABONNE: {
    couleur: "var(--color-statut-abonne)",
    fond: "rgb(22 163 74 / 0.14)",
    texte: "#15803d",
  },
  NON_ABONNE: {
    couleur: "var(--color-statut-non-abonne)",
    fond: "rgb(220 38 38 / 0.13)",
    texte: "#b91c1c",
  },
  INJOIGNABLE: {
    couleur: "var(--color-statut-injoignable)",
    fond: "rgb(168 85 247 / 0.14)",
    texte: "#7e22ce",
  },
  ABSENT: {
    couleur: "var(--color-statut-absent)",
    fond: "rgb(245 158 11 / 0.16)",
    texte: "#b45309",
  },
  REFUS: {
    couleur: "var(--color-statut-refus)",
    fond: "rgb(225 29 72 / 0.13)",
    texte: "#be123c",
  },
  DOUBLON: {
    couleur: "var(--color-statut-doublon)",
    fond: "rgb(100 116 139 / 0.14)",
    texte: "#475569",
  },
};

/** Statuts proposés à la saisie, dans l'ordre de fréquence sur le terrain. */
export const STATUTS_SAISISSABLES: StatutCollecte[] = [
  "ABONNE",
  "NON_ABONNE",
  "ABSENT",
  "INJOIGNABLE",
  "REFUS",
  "DOUBLON",
  "A_TRAITER",
];

export const VERDICTS: Record<VerdictVerification, Omit<Teinte, "couleur">> = {
  NON_VERIFIE: { texte: "#64748b", fond: "rgb(100 116 139 / 0.12)" },
  CONFIRME: { texte: "#15803d", fond: "rgb(22 163 74 / 0.13)" },
  INFIRME: { texte: "#b91c1c", fond: "rgb(220 38 38 / 0.13)" },
  INTROUVABLE: { texte: "#b45309", fond: "rgb(245 158 11 / 0.16)" },
};

export const RESPONSABLES: Responsable[] = [
  "TERRAIN",
  "CHATBOT",
  "CSC",
  "AUTRES",
];

/** Un statut ABONNE exige le numéro relevé : le formulaire s'y adapte. */
export function exigeNumero(statut: StatutCollecte): boolean {
  return statut === "ABONNE";
}
