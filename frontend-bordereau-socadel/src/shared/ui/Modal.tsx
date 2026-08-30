/**
 * Boîte de dialogue modale, bâtie sur l'élément natif `<dialog>`.
 *
 * Le natif apporte gratuitement le piège de focus, la fermeture par Échap et
 * l'inertie de l'arrière-plan — trois choses qu'une modale maison rate presque
 * toujours. Elle sert notamment à la prévisualisation d'import, où le
 * superviseur doit pouvoir parcourir puis confirmer sans perdre le contexte.
 */

"use client";

import { useEffect, useRef, type ReactNode } from "react";

import { cx } from "./primitives";

export function Modal({
  ouvert,
  onFermer,
  titre,
  description,
  taille = "md",
  pied,
  children,
}: {
  ouvert: boolean;
  onFermer: () => void;
  titre: string;
  description?: string;
  taille?: "md" | "lg" | "xl";
  pied?: ReactNode;
  children: ReactNode;
}) {
  const reference = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialogue = reference.current;
    if (!dialogue) return;

    if (ouvert && !dialogue.open) dialogue.showModal();
    else if (!ouvert && dialogue.open) dialogue.close();
  }, [ouvert]);

  useEffect(() => {
    const dialogue = reference.current;
    if (!dialogue) return;

    // `close` couvre aussi la fermeture par Échap, que React ne voit pas.
    const surFermeture = () => onFermer();
    dialogue.addEventListener("close", surFermeture);
    return () => dialogue.removeEventListener("close", surFermeture);
  }, [onFermer]);

  const largeurs = { md: "max-w-lg", lg: "max-w-3xl", xl: "max-w-6xl" } as const;

  return (
    <dialog
      ref={reference}
      aria-labelledby="titre-modal"
      // Le fond est peint par le backdrop ; `p-0` retire la marge par défaut
      // du user-agent, qui décalerait le contenu.
      className={cx(
        "w-[calc(100vw-2rem)] rounded-xl p-0 backdrop:bg-slate-900/45",
        "bg-[var(--fond-carte)] text-[var(--texte)] shadow-2xl",
        largeurs[taille],
      )}
      onClick={(evenement) => {
        // Un clic sur le backdrop atteint le <dialog> lui-même, jamais ses
        // enfants : c'est ainsi qu'on distingue « dehors » de « dedans ».
        if (evenement.target === reference.current) onFermer();
      }}
    >
      <header className="flex items-start justify-between gap-4 border-b border-[var(--bordure)] px-5 py-4">
        <div>
          <h2 id="titre-modal" className="text-base font-semibold">
            {titre}
          </h2>
          {description && (
            <p className="mt-0.5 text-xs text-[var(--texte-tres-doux)]">{description}</p>
          )}
        </div>
        <button
          type="button"
          onClick={onFermer}
          aria-label="Fermer"
          className="rounded-md px-2 py-1 text-lg leading-none text-[var(--texte-tres-doux)] hover:bg-[var(--fond-survol)]"
        >
          ×
        </button>
      </header>

      <div className="max-h-[65vh] overflow-auto px-5 py-4">{children}</div>

      {pied && (
        <footer className="flex items-center justify-end gap-2 border-t border-[var(--bordure)] px-5 py-3.5">
          {pied}
        </footer>
      )}
    </dialog>
  );
}
