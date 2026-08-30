/**
 * Sélecteurs de langue et de thème, posés dans l'en-tête.
 *
 * Deux boutons plutôt que des menus déroulants : il n'y a que deux langues et
 * trois thèmes, et un cycle au clic se manipule d'une main.
 */

"use client";

import {
  THEMES,
  usePreferences,
  type Theme,
} from "@core/i18n/PreferencesProvider";
import { LANGUES, NOMS_LANGUES } from "@core/i18n/messages";

import { cx } from "./primitives";

export function SelecteurLangue() {
  const { langue, changerLangue, t } = usePreferences();

  return (
    <div
      role="group"
      aria-label={t("langue.basculer")}
      className="flex rounded-lg border border-[var(--bordure-forte)] p-0.5"
    >
      {LANGUES.map((valeur) => (
        <button
          key={valeur}
          type="button"
          onClick={() => changerLangue(valeur)}
          aria-pressed={langue === valeur}
          title={NOMS_LANGUES[valeur]}
          className={cx(
            "rounded-md px-2 py-1 text-[11px] font-semibold uppercase transition-colors",
            langue === valeur
              ? "bg-socadel-600 text-white"
              : "text-[var(--texte-doux)] hover:bg-[var(--fond-survol)]",
          )}
        >
          {valeur}
        </button>
      ))}
    </div>
  );
}

const ICONES: Record<Theme, React.ReactNode> = {
  clair: (
    <path
      d="M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  ),
  sombre: (
    <path
      d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  ),
  systeme: (
    <path
      d="M4 4h16v11H4zM8 20h8M12 15v5"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  ),
};

const LIBELLES: Record<Theme, "theme.clair" | "theme.sombre" | "theme.systeme"> =
  {
    clair: "theme.clair",
    sombre: "theme.sombre",
    systeme: "theme.systeme",
  };

export function SelecteurTheme() {
  const { theme, changerTheme, t } = usePreferences();

  function suivant() {
    // Cycle clair → sombre → système : « système » reste accessible sans
    // menu, et c'est le mode par défaut.
    const index = THEMES.indexOf(theme);
    changerTheme(THEMES[(index + 1) % THEMES.length]);
  }

  return (
    <button
      type="button"
      onClick={suivant}
      aria-label={`${t("theme.basculer")}, ${t(LIBELLES[theme])}`}
      title={`${t("theme.basculer")}, ${t(LIBELLES[theme])}`}
      className="rounded-lg border border-[var(--bordure-forte)] p-1.5 text-[var(--texte-doux)] transition-colors hover:bg-[var(--fond-survol)]"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
        {ICONES[theme]}
      </svg>
    </button>
  );
}
