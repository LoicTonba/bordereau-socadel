/**
 * Préférences d'affichage : langue et thème.
 *
 * Les deux sont réunis parce qu'ils partagent exactement le même cycle de vie —
 * lus au montage depuis le stockage local, appliqués sur `<html>`, persistés à
 * chaque changement — et parce qu'un composant qui a besoin de l'un a presque
 * toujours besoin de l'autre.
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  interpoler,
  LANGUES,
  MESSAGES,
  type Cle,
  type Langue,
} from "./messages";

export const THEMES = ["clair", "sombre", "systeme"] as const;
export type Theme = (typeof THEMES)[number];

const CLE_LANGUE = "socadel.langue";
const CLE_THEME = "socadel.theme";

interface ValeurPreferences {
  langue: Langue;
  changerLangue: (langue: Langue) => void;
  /** Traduit une clé, en interpolant les jetons `{nom}` éventuels. */
  t: (cle: Cle, valeurs?: Record<string, string | number>) => string;
  theme: Theme;
  changerTheme: (theme: Theme) => void;
}

const ContextePreferences = createContext<ValeurPreferences | null>(null);

function lire<T extends string>(cle: string, valeurs: readonly T[], defaut: T): T {
  if (typeof window === "undefined") return defaut;
  try {
    const brut = window.localStorage.getItem(cle);
    return valeurs.includes(brut as T) ? (brut as T) : defaut;
  } catch {
    // Navigation privée ou stockage bloqué : on retombe sur le défaut.
    return defaut;
  }
}

function ecrire(cle: string, valeur: string): void {
  try {
    window.localStorage.setItem(cle, valeur);
  } catch {
    // La préférence ne survivra pas au rechargement, mais l'application
    // reste parfaitement utilisable dans cet onglet.
  }
}

export function PreferencesProvider({ children }: { children: ReactNode }) {
  // Le premier rendu doit être identique côté serveur et côté client, sinon
  // React signale une divergence d'hydratation : on part donc du défaut et on
  // applique la préférence stockée juste après le montage.
  const [langue, setLangue] = useState<Langue>("fr");
  const [theme, setTheme] = useState<Theme>("systeme");

  useEffect(() => {
    setLangue(lire(CLE_LANGUE, LANGUES, "fr"));
    setTheme(lire(CLE_THEME, THEMES, "systeme"));
  }, []);

  useEffect(() => {
    document.documentElement.lang = langue;
  }, [langue]);

  useEffect(() => {
    const racine = document.documentElement;
    if (theme === "systeme") {
      // Sans attribut, le CSS retombe sur `prefers-color-scheme`.
      racine.removeAttribute("data-theme");
    } else {
      racine.setAttribute("data-theme", theme === "sombre" ? "dark" : "light");
    }
  }, [theme]);

  const changerLangue = useCallback((suivante: Langue) => {
    setLangue(suivante);
    ecrire(CLE_LANGUE, suivante);
  }, []);

  const changerTheme = useCallback((suivant: Theme) => {
    setTheme(suivant);
    ecrire(CLE_THEME, suivant);
  }, []);

  const t = useCallback(
    (cle: Cle, valeurs?: Record<string, string | number>) =>
      interpoler(MESSAGES[langue][cle] ?? cle, valeurs),
    [langue],
  );

  const valeur = useMemo(
    () => ({ langue, changerLangue, t, theme, changerTheme }),
    [langue, changerLangue, t, theme, changerTheme],
  );

  return (
    <ContextePreferences.Provider value={valeur}>
      {children}
    </ContextePreferences.Provider>
  );
}

export function usePreferences(): ValeurPreferences {
  const contexte = useContext(ContextePreferences);
  if (!contexte) {
    throw new Error(
      "usePreferences doit être utilisé à l'intérieur de <PreferencesProvider>",
    );
  }
  return contexte;
}

/** Raccourci pour les composants qui n'ont besoin que de traduire. */
export function useT() {
  return usePreferences().t;
}
