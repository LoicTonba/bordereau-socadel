/**
 * Recherche unique, ouverte depuis la barre du haut.
 *
 * Un utilisateur qui cherche un client ne sait pas toujours quel écran
 * l'affiche, ni sous quel filtre. Ce champ répond à la question posée : on tape
 * un nom, un contrat, un matricule ou un code de tournée, et on obtient ce à
 * quoi on a droit, groupé par famille.
 *
 * Le serveur décide de ce qu'il renvoie : il interroge, pour chaque famille, le
 * cas d'usage qui sert déjà l'écran correspondant, avec les habilitations de
 * l'appelant. Une famille fermée à ce profil est simplement absente de la
 * réponse ; l'interface n'a donc aucune règle d'accès à connaître.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { useT } from "@core/i18n/PreferencesProvider";
import { api } from "@infra/http/client";

import { Modal } from "./Modal";
import { cx } from "./primitives";

interface Trouvaille {
  titre: string;
  detail: string;
  chemin: string;
}

interface Volet {
  cle: string;
  libelle: string;
  resultats: Trouvaille[];
}

interface Resultat {
  terme: string;
  total: number;
  volets: Volet[];
}

/** Attente avant d'interroger le serveur, en millisecondes. */
const ATTENTE_FRAPPE = 300;

/** En deçà, la recherche ramènerait un échantillon arbitraire. */
const LONGUEUR_MIN = 2;

export function RechercheGlobale() {
  const t = useT();
  const router = useRouter();
  const [ouvert, setOuvert] = useState(false);

  // Ctrl+K, le raccourci que tout le monde essaie en premier.
  useEffect(() => {
    function surTouche(evenement: KeyboardEvent) {
      if ((evenement.ctrlKey || evenement.metaKey) && evenement.key === "k") {
        evenement.preventDefault();
        setOuvert(true);
      }
    }
    window.addEventListener("keydown", surTouche);
    return () => window.removeEventListener("keydown", surTouche);
  }, []);

  const aller = useCallback(
    (chemin: string) => {
      setOuvert(false);
      router.push(chemin);
    },
    [router],
  );

  return (
    <>
      <button
        type="button"
        onClick={() => setOuvert(true)}
        className={cx(
          "flex items-center gap-2 rounded-lg border border-[var(--bordure)]",
          "bg-[var(--fond-carte)] px-3 py-1.5 text-sm text-[var(--texte-tres-doux)]",
          "transition-colors hover:border-socadel-400 hover:text-[var(--texte-doux)]",
          "w-40 sm:w-64",
        )}
      >
        <LoupeIcone />
        <span className="flex-1 truncate text-left">{t("recherche.invite")}</span>
        <kbd className="hidden rounded border border-[var(--bordure)] px-1 text-[10px] sm:block">
          Ctrl K
        </kbd>
      </button>

      <Modal
        ouvert={ouvert}
        onFermer={() => setOuvert(false)}
        titre={t("recherche.titre")}
        description={t("recherche.aide")}
        taille="lg"
      >
        {/* Le panneau n'est monté que lorsqu'il s'ouvre. Une modale fermée
            reste dans le document : son champ de recherche s'y ajoutait en
            double, captait les saisies destinées à l'écran, et encombrait
            l'arbre d'accessibilité d'un champ inatteignable. */}
        {ouvert && <Panneau onAller={aller} />}
      </Modal>
    </>
  );
}

function Panneau({ onAller }: { onAller: (chemin: string) => void }) {
  const t = useT();
  const [terme, setTerme] = useState("");
  const [resultat, setResultat] = useState<Resultat | null>(null);
  const [chargement, setChargement] = useState(false);
  const champ = useRef<HTMLInputElement>(null);

  // Le panneau naît à chaque ouverture : sa saisie repart donc de zéro, et il
  // ne reste plus qu'à lui donner le focus.
  useEffect(() => {
    const minuterie = setTimeout(() => champ.current?.focus(), 60);
    return () => clearTimeout(minuterie);
  }, []);

  useEffect(() => {
    if (terme.trim().length < LONGUEUR_MIN) {
      setResultat(null);
      return;
    }

    let annule = false;
    setChargement(true);
    const minuterie = setTimeout(() => {
      api
        .get<Resultat>("/reference/recherche", { q: terme.trim() })
        .then((reponse) => {
          if (!annule) setResultat(reponse);
        })
        .catch(() => {
          // Une recherche qui échoue n'a pas à interrompre le travail : la
          // liste reste vide, l'utilisateur reformule.
          if (!annule) setResultat(null);
        })
        .finally(() => {
          if (!annule) setChargement(false);
        });
    }, ATTENTE_FRAPPE);

    return () => {
      annule = true;
      clearTimeout(minuterie);
    };
  }, [terme]);

  const tropCourt = terme.trim().length > 0 && terme.trim().length < LONGUEUR_MIN;

  return (
    <div className="space-y-4">
      <input
        ref={champ}
        type="search"
        className="champ"
        placeholder={t("recherche.placeholder")}
        value={terme}
        onChange={(evenement) => setTerme(evenement.target.value)}
      />

      {tropCourt && (
        <p className="text-xs text-[var(--texte-tres-doux)]">
          {t("recherche.tropCourt")}
        </p>
      )}

      {chargement && (
        <p className="text-sm text-[var(--texte-tres-doux)]">
          {t("commun.chargement")}
        </p>
      )}

      {resultat && resultat.total === 0 && !chargement && (
        <p className="py-6 text-center text-sm text-[var(--texte-tres-doux)]">
          {t("recherche.aucun", { terme: resultat.terme })}
        </p>
      )}

      {resultat?.volets.map((volet) => (
        <section key={volet.cle} className="space-y-1.5">
          <h3 className="text-xs font-semibold tracking-wide text-socadel-700 uppercase dark:text-socadel-300">
            {volet.libelle}
          </h3>
          <ul className="divide-y divide-[var(--bordure)] overflow-hidden rounded-lg border border-[var(--bordure)]">
            {volet.resultats.map((trouvaille) => (
              <li key={`${volet.cle}-${trouvaille.titre}-${trouvaille.detail}`}>
                <button
                  type="button"
                  onClick={() => onAller(trouvaille.chemin)}
                  className="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-[var(--fond-survol)]"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">
                      {trouvaille.titre}
                    </span>
                    <span className="block truncate text-xs text-[var(--texte-tres-doux)]">
                      {trouvaille.detail}
                    </span>
                  </span>
                  <span aria-hidden className="text-[var(--texte-tres-doux)]">
                    →
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function LoupeIcone() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 20 20"
      className="size-4 shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
    >
      <circle cx="9" cy="9" r="5.5" />
      <path d="m13.5 13.5 3.5 3.5" strokeLinecap="round" />
    </svg>
  );
}
