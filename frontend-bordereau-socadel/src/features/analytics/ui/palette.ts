/**
 * Palette des graphiques.
 *
 * Les trois teintes ont été validées pour la déficience de vision des couleurs
 * et pour le contraste, sur les deux surfaces réellement utilisées par
 * l'application (`#ffffff` en clair, `#111a2b` en sombre) :
 *
 *   clair  #1a76b9 / #eb6834 / #1baf7a — écart CVD minimal ΔE 9.2 (seuil 8)
 *   sombre #3b93dc / #d95926 / #199e70 — écart CVD minimal ΔE 9.4
 *
 * Le bleu est celui du logo SOCADEL en mode clair, et sa déclinaison claire en
 * mode sombre. L'aqua passe sous 3:1 sur fond blanc : les séries portent donc
 * toujours une légende **et** une étiquette directe sur le dernier point, et un
 * tableau de données reste accessible sous chaque graphique.
 *
 * Les couleurs sont exposées en variables CSS pour basculer clair/sombre en un
 * seul endroit ; les composants ne lisent jamais un hexadécimal en dur.
 */

export const SERIES = {
  demarches: "var(--serie-1)",
  declares: "var(--serie-2)",
  confirmes: "var(--serie-3)",
} as const;

/** Ordre fixe des séries : une entité garde sa teinte quel que soit le filtre. */
export const SERIES_EVOLUTION = [
  { cle: "collectes", libelle: "Clients démarchés", couleur: SERIES.demarches },
  { cle: "abonnements", libelle: "Abonnements déclarés", couleur: SERIES.declares },
  { cle: "confirmes", libelle: "Abonnements confirmés", couleur: SERIES.confirmes },
] as const;

export const GRILLE = "var(--grille-viz)";
export const AXE = "var(--texte-tres-doux)";
