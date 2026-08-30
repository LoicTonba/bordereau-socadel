/**
 * Primitives d'interface aux couleurs SOCADEL.
 *
 * Elles n'encapsulent que ce qui se répète : au-delà, les écrans composent
 * directement en Tailwind plutôt que d'empiler des abstractions.
 */

"use client";

import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

export function cx(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

// --- Bouton -----------------------------------------------------------------

type VarianteBouton = "primaire" | "secondaire" | "discret" | "danger";

const VARIANTES: Record<VarianteBouton, string> = {
  primaire:
    "bg-socadel-600 text-white hover:bg-socadel-700 active:bg-socadel-800 shadow-sm",
  secondaire:
    "bg-[var(--fond-carte)] text-[var(--texte)] border border-[var(--bordure-forte)] hover:bg-[var(--fond-survol)]",
  discret: "text-[var(--texte-doux)] hover:bg-[var(--fond-survol)]",
  danger: "bg-red-600 text-white hover:bg-red-700",
};

interface ProprietesBouton extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: VarianteBouton;
  taille?: "sm" | "md";
  chargement?: boolean;
  icone?: ReactNode;
}

export function Bouton({
  variante = "primaire",
  taille = "md",
  chargement = false,
  icone,
  className,
  children,
  disabled,
  ...reste
}: ProprietesBouton) {
  return (
    <button
      {...reste}
      // Un bouton en cours de traitement reste inactif : sans cela, un
      // double-clic déclencherait deux imports ou deux affectations.
      disabled={disabled || chargement}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium",
        "transition-colors disabled:cursor-not-allowed disabled:opacity-55",
        taille === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2.5 text-sm",
        VARIANTES[variante],
        className,
      )}
    >
      {chargement ? <Rouet /> : icone}
      {children}
    </button>
  );
}

function Rouet() {
  return (
    <span
      aria-hidden
      className="size-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
    />
  );
}

// --- Champs -----------------------------------------------------------------

interface ProprietesChamp extends InputHTMLAttributes<HTMLInputElement> {
  libelle?: string;
  aide?: string;
  erreur?: string;
}

export function Champ({ libelle, aide, erreur, className, id, ...reste }: ProprietesChamp) {
  const identifiant = id ?? reste.name;
  return (
    <div className="space-y-1.5">
      {libelle && (
        <label
          htmlFor={identifiant}
          className="block text-sm font-medium text-[var(--texte-doux)]"
        >
          {libelle}
        </label>
      )}
      <input
        {...reste}
        id={identifiant}
        aria-invalid={erreur ? true : undefined}
        aria-describedby={erreur && identifiant ? `${identifiant}-erreur` : undefined}
        className={cx("champ", erreur && "border-red-500", className)}
      />
      {erreur ? (
        <p id={identifiant ? `${identifiant}-erreur` : undefined} className="text-xs text-red-600">
          {erreur}
        </p>
      ) : (
        aide && <p className="text-xs text-[var(--texte-tres-doux)]">{aide}</p>
      )}
    </div>
  );
}

interface ProprietesSelecteur extends SelectHTMLAttributes<HTMLSelectElement> {
  libelle?: string;
}

export function Selecteur({ libelle, className, id, children, ...reste }: ProprietesSelecteur) {
  const identifiant = id ?? reste.name;
  return (
    <div className="space-y-1.5">
      {libelle && (
        <label
          htmlFor={identifiant}
          className="block text-sm font-medium text-[var(--texte-doux)]"
        >
          {libelle}
        </label>
      )}
      <select {...reste} id={identifiant} className={cx("champ", className)}>
        {children}
      </select>
    </div>
  );
}

// --- Conteneurs -------------------------------------------------------------

export function Carte({
  titre,
  description,
  actions,
  className,
  children,
}: {
  titre?: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section className={cx("carte", className)}>
      {(titre || actions) && (
        <header className="flex items-start justify-between gap-4 border-b border-[var(--bordure)] px-5 py-4">
          <div>
            {titre && <h2 className="text-sm font-semibold">{titre}</h2>}
            {description && (
              <p className="mt-0.5 text-xs text-[var(--texte-tres-doux)]">{description}</p>
            )}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export function Badge({
  children,
  fond,
  texte,
  titre,
}: {
  children: ReactNode;
  fond: string;
  texte: string;
  titre?: string;
}) {
  return (
    <span
      title={titre}
      className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap"
      style={{ backgroundColor: fond, color: texte }}
    >
      {children}
    </span>
  );
}

/** Bandeau d'erreur, utilisé au même endroit sur tous les écrans. */
export function Alerte({
  ton = "erreur",
  children,
}: {
  ton?: "erreur" | "info" | "succes";
  children: ReactNode;
}) {
  const tons = {
    erreur: "border-red-200 bg-red-50 text-red-800",
    info: "border-socadel-200 bg-socadel-50 text-socadel-800",
    succes: "border-green-200 bg-green-50 text-green-800",
  } as const;

  return (
    <div role="alert" className={cx("rounded-lg border px-4 py-3 text-sm", tons[ton])}>
      {children}
    </div>
  );
}

/** Message d'état vide : dit ce qui manque et ce qu'il faut faire ensuite. */
export function EtatVide({
  titre,
  description,
  action,
}: {
  titre: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-14 text-center">
      <p className="text-sm font-medium">{titre}</p>
      <p className="max-w-sm text-xs text-[var(--texte-tres-doux)]">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
