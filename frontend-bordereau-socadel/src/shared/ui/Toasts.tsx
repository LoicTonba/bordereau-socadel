/**
 * Notifications éphémères, une par action effectuée.
 *
 * Une écriture qui n'accuse pas réception laisse l'utilisateur dans le doute :
 * il reclique, et crée un doublon. Le message dit donc ce qui vient d'arriver,
 * au moment où cela arrive, et disparaît de lui-même.
 *
 * La couleur porte la **nature de l'opération**, pas son résultat : une
 * création est verte, une modification bleue, une suppression ambre, un échec
 * rouge. L'œil apprend l'association en deux jours et n'a plus à lire.
 *
 * Elle ne porte jamais l'information à elle seule : chaque notification a une
 * icône et un texte, ce qui la rend lisible en vision des couleurs déficiente
 * comme au lecteur d'écran, à qui la zone est annoncée poliment.
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { cx } from "./primitives";

/** Nature de l'opération, d'où découlent la couleur et l'icône. */
export type TonToast = "creation" | "modification" | "suppression" | "echec" | "info";

interface Toast {
  id: number;
  ton: TonToast;
  message: string;
}

interface ValeurToasts {
  /** Annonce une opération réussie ou échouée. */
  notifier: (ton: TonToast, message: string) => void;
}

const ContexteToasts = createContext<ValeurToasts | null>(null);

/** Durée d'affichage. Assez pour lire deux lignes, assez court pour ne pas gêner. */
const DUREE = 4500;

const APPARENCES: Record<TonToast, { classe: string; icone: string; role: string }> = {
  creation: {
    classe: "border-emerald-300 bg-emerald-50 text-emerald-900",
    icone: "＋",
    role: "status",
  },
  modification: {
    classe: "border-socadel-300 bg-socadel-50 text-socadel-900",
    icone: "✎",
    role: "status",
  },
  suppression: {
    classe: "border-amber-300 bg-amber-50 text-amber-900",
    icone: "⌫",
    role: "status",
  },
  echec: {
    classe: "border-red-300 bg-red-50 text-red-900",
    icone: "!",
    // Un échec interrompt : il est annoncé sans attendre une pause du lecteur.
    role: "alert",
  },
  info: {
    classe: "border-slate-300 bg-slate-50 text-slate-900",
    icone: "i",
    role: "status",
  },
};

export function ToastsProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const compteur = useRef(0);

  const retirer = useCallback((id: number) => {
    setToasts((actuels) => actuels.filter((t) => t.id !== id));
  }, []);

  const notifier = useCallback((ton: TonToast, message: string) => {
    compteur.current += 1;
    const id = compteur.current;
    // Au-delà de trois, la pile masque l'écran qu'elle commente : les plus
    // anciennes cèdent la place.
    setToasts((actuels) => [...actuels.slice(-2), { id, ton, message }]);
  }, []);

  const valeur = useMemo(() => ({ notifier }), [notifier]);

  return (
    <ContexteToasts.Provider value={valeur}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4"
      >
        {toasts.map((toast) => (
          <Bulle key={toast.id} toast={toast} onFermer={() => retirer(toast.id)} />
        ))}
      </div>
    </ContexteToasts.Provider>
  );
}

function Bulle({ toast, onFermer }: { toast: Toast; onFermer: () => void }) {
  const apparence = APPARENCES[toast.ton];

  useEffect(() => {
    const minuterie = setTimeout(onFermer, DUREE);
    return () => clearTimeout(minuterie);
  }, [onFermer]);

  return (
    <div
      role={apparence.role}
      className={cx(
        "pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-xl border",
        "px-4 py-3 text-sm shadow-lg",
        apparence.classe,
      )}
    >
      <span
        aria-hidden
        className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-white/70 text-xs font-bold"
      >
        {apparence.icone}
      </span>
      <p className="flex-1 leading-snug">{toast.message}</p>
      <button
        type="button"
        onClick={onFermer}
        aria-label="Fermer"
        className="shrink-0 rounded px-1 text-base leading-none opacity-60 hover:opacity-100"
      >
        ×
      </button>
    </div>
  );
}

export function useToasts(): ValeurToasts {
  const contexte = useContext(ContexteToasts);
  if (!contexte) {
    throw new Error("useToasts doit être utilisé à l'intérieur de <ToastsProvider>");
  }
  return contexte;
}
