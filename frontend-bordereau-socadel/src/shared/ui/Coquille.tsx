/**
 * Coquille du back-office : barre latérale, en-tête et garde d'authentification.
 *
 * La navigation est filtrée par les **permissions effectives** du compte : un
 * agent de terrain n'y voit que son espace. Ce n'est pas un contrôle de
 * sécurité — l'API tranche de toute façon — mais afficher des entrées qui
 * mèneraient à un refus serait une mauvaise interface.
 *
 * Tant que la session n'est pas revalidée, ni le contenu ni l'écran de
 * connexion ne s'affichent : montrer l'un ou l'autre trop tôt provoquerait un
 * clignotement à chaque rechargement.
 */

"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import { useSession } from "@features/auth/application/SessionProvider";

import { MarqueSocadel } from "./Logo";
import { Avatar } from "./Avatar";
import { SelecteurLangue, SelecteurTheme } from "./Preferences";
import { RechercheGlobale } from "./RechercheGlobale";
import { cx } from "./primitives";

const CLE_REPLIEE = "socadel.sidebarRepliee";

interface Entree {
  href: string;
  libelle: Cle;
  aide: Cle;
  /** Permission requise pour que l'entrée apparaisse. */
  permission: string;
  /** Réservée aux comptes agent (leur unique écran). */
  agentSeulement?: boolean;
  /** Masquée pour les comptes agent. */
  saufAgent?: boolean;
}

const NAVIGATION: Entree[] = [
  {
    href: "/mon-espace",
    libelle: "nav.monEspace",
    aide: "nav.monEspace.aide",
    permission: "analytics:consulter",
    agentSeulement: true,
  },
  {
    href: "/affectations",
    libelle: "nav.affectations",
    aide: "nav.affectations.aide",
    permission: "itineraire:affecter",
    saufAgent: true,
  },
  {
    href: "/dashboard",
    libelle: "nav.dashboard",
    aide: "nav.dashboard.aide",
    permission: "analytics:consulter",
    saufAgent: true,
  },
  {
    href: "/bordereau",
    libelle: "nav.bordereau",
    aide: "nav.bordereau.aide",
    permission: "bordereau:lire",
    saufAgent: true,
  },
  {
    href: "/itineraires",
    libelle: "nav.itineraires",
    aide: "nav.itineraires.aide",
    permission: "itineraire:lire",
  },
  {
    href: "/agents",
    libelle: "nav.agents",
    aide: "nav.agents.aide",
    permission: "agent:creer",
    saufAgent: true,
  },
  {
    href: "/imports",
    libelle: "nav.imports",
    aide: "nav.imports.aide",
    permission: "import:executer",
    saufAgent: true,
  },
  {
    href: "/territoire",
    libelle: "nav.territoire",
    aide: "nav.territoire.aide",
    permission: "territoire:gerer",
    saufAgent: true,
  },
  {
    href: "/roles",
    libelle: "nav.roles",
    aide: "nav.roles.aide",
    permission: "role:lire",
    saufAgent: true,
  },
  {
    href: "/audit",
    libelle: "nav.audit",
    aide: "nav.audit.aide",
    permission: "audit:lire",
    saufAgent: true,
  },
  {
    href: "/comptes",
    libelle: "nav.comptes",
    aide: "nav.comptes.aide",
    permission: "compte:creer",
    saufAgent: true,
  },
];

export function Coquille({ children }: { children: ReactNode }) {
  const { utilisateur, chargement, deconnecter } = useSession();
  const router = useRouter();
  const chemin = usePathname();
  const t = useT();

  const [repliee, setRepliee] = useState(false);
  const [tiroirOuvert, setTiroirOuvert] = useState(false);

  useEffect(() => {
    try {
      setRepliee(window.localStorage.getItem(CLE_REPLIEE) === "1");
    } catch {
      // Sans stockage, la barre reste dépliée : c'est l'état le plus lisible.
    }
  }, []);

  // Le tiroir mobile se referme à chaque navigation, sinon il masquerait la
  // page qu'on vient d'ouvrir.
  useEffect(() => setTiroirOuvert(false), [chemin]);

  useEffect(() => {
    if (!chargement && !utilisateur) router.replace("/login");
  }, [chargement, utilisateur, router]);

  const estAgent = utilisateur?.role === "AGENT_TERRAIN";
  const permissions = new Set(utilisateur?.permissions ?? []);
  const entrees = NAVIGATION.filter((e) => {
    if (e.agentSeulement && !estAgent) return false;
    if (e.saufAgent && estAgent) return false;
    return permissions.has(e.permission);
  });

  // Un écran qu'aucune entrée n'ouvre reste atteignable par l'URL. Ce n'est
  // pas une faille, l'API refuse de toute façon ce que le rôle ne porte pas et
  // l'ABAC rétrécit ce qu'il lit ; mais un agent de terrain qui atterrit sur un
  // bordereau vide croit à une panne. On le ramène chez lui.
  const accessible =
    entrees.length === 0 || entrees.some((e) => chemin.startsWith(e.href));

  useEffect(() => {
    if (!chargement && utilisateur && !accessible && entrees.length > 0) {
      router.replace(entrees[0].href);
    }
  }, [chargement, utilisateur, accessible, entrees, router, chemin]);

  function basculerRepli() {
    setRepliee((actuel) => {
      const suivant = !actuel;
      try {
        window.localStorage.setItem(CLE_REPLIEE, suivant ? "1" : "0");
      } catch {
        // Préférence non persistée, sans conséquence sur la session en cours.
      }
      return suivant;
    });
  }

  if (chargement || !utilisateur || !accessible) {
    return (
      <div className="grid min-h-dvh place-items-center">
        <p className="text-sm text-[var(--texte-tres-doux)]">
          {t("commun.chargementSession")}
        </p>
      </div>
    );
  }

  const barre = (
    <BarreLaterale
      entrees={entrees}
      chemin={chemin}
      repliee={repliee}
      utilisateur={utilisateur}
      onDeconnexion={deconnecter}
    />
  );

  return (
    <div className="flex min-h-dvh">
      {/* Barre fixe, à partir du large. La largeur est la seule chose qui
          change au repli : le contenu s'adapte tout seul. */}
      <aside
        className={cx(
          "hidden shrink-0 flex-col border-r border-[var(--bordure)]",
          "bg-[var(--fond-carte)] transition-[width] duration-200 lg:flex",
          repliee ? "w-[68px]" : "w-64",
        )}
      >
        {barre}
      </aside>

      {/* Tiroir mobile. */}
      {tiroirOuvert && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label={t("commun.fermer")}
            onClick={() => setTiroirOuvert(false)}
            className="absolute inset-0 bg-slate-900/45"
          />
          <aside className="absolute inset-y-0 left-0 flex w-64 flex-col border-r border-[var(--bordure)] bg-[var(--fond-carte)] shadow-xl">
            <BarreLaterale
              entrees={entrees}
              chemin={chemin}
              repliee={false}
              utilisateur={utilisateur}
              onDeconnexion={deconnecter}
            />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-[var(--bordure)] bg-[var(--fond-carte)] px-4 py-2.5">
          <button
            type="button"
            onClick={() => setTiroirOuvert(true)}
            aria-label={t("nav.ouvrirMenu")}
            className="rounded-lg p-2 text-[var(--texte-doux)] hover:bg-[var(--fond-survol)] lg:hidden"
          >
            <IconeHamburger />
          </button>

          <button
            type="button"
            onClick={basculerRepli}
            aria-label={t(repliee ? "nav.deplier" : "nav.replier")}
            title={t(repliee ? "nav.deplier" : "nav.replier")}
            className="hidden rounded-lg p-2 text-[var(--texte-doux)] hover:bg-[var(--fond-survol)] lg:block"
          >
            <IconeHamburger />
          </button>

          <div className="flex items-center gap-2 lg:hidden">
            <MarqueSocadel taille={26} />
            <span className="text-sm font-semibold">{t("app.nom")}</span>
          </div>

          {/* La recherche occupe le centre de la barre : c'est le geste le
              plus fréquent, il ne doit pas se chercher dans un coin. */}
          <div className="ml-auto flex items-center gap-1.5">
            <RechercheGlobale />
            <SelecteurLangue />
            <SelecteurTheme />
          </div>
        </header>

        {/* `min-w-0` : sans lui, le tableau large empêcherait la colonne de
            rétrécir et déborderait la fenêtre. */}
        <main className="min-w-0 flex-1 p-5">{children}</main>
      </div>
    </div>
  );
}

function BarreLaterale({
  entrees,
  chemin,
  repliee,
  utilisateur,
  onDeconnexion,
}: {
  entrees: Entree[];
  chemin: string;
  repliee: boolean;
  utilisateur: { nomComplet: string; role: string; photoUrl?: string | null };
  onDeconnexion: () => void;
}) {
  const t = useT();

  return (
    <>
      <div
        className={cx(
          "flex items-center gap-2.5 border-b border-[var(--bordure)] py-4",
          repliee ? "justify-center px-2" : "px-5",
        )}
      >
        <MarqueSocadel taille={32} />
        {!repliee && (
          <div className="leading-tight">
            <p className="text-sm font-semibold">{t("nav.bordereau")}</p>
            <p className="text-[11px] text-[var(--texte-tres-doux)]">
              {t("app.marque")}
            </p>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
        {entrees.map((entree) => {
          const actif = chemin.startsWith(entree.href);
          return (
            <Link
              key={entree.href}
              href={entree.href}
              aria-current={actif ? "page" : undefined}
              title={repliee ? t(entree.libelle) : undefined}
              className={cx(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                repliee && "justify-center px-2",
                actif
                  ? "bg-socadel-50 font-medium text-socadel-700"
                  : "text-[var(--texte-doux)] hover:bg-[var(--fond-survol)]",
              )}
            >
              <IconeEntree href={entree.href} />
              {!repliee && (
                <span className="min-w-0">
                  <span className="block truncate">{t(entree.libelle)}</span>
                  <span className="block truncate text-[11px] text-[var(--texte-tres-doux)]">
                    {t(entree.aide)}
                  </span>
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Pied de barre : qui est connecté, que la session est vivante, et par
          où sortir — les trois choses qu'on cherche en bas d'une sidebar. */}
      <div className="border-t border-[var(--bordure)] p-2">
        <div
          className={cx(
            "flex items-center gap-2.5 rounded-lg px-2 py-2",
            repliee && "justify-center px-0",
          )}
        >
          <Avatar
            nom={utilisateur.nomComplet}
            url={utilisateur.photoUrl}
            taille={repliee ? 30 : 34}
            pastille
          />
          {!repliee && (
            <div className="min-w-0 flex-1 leading-tight">
              <p className="truncate text-sm font-medium">
                {utilisateur.nomComplet}
              </p>
              <p className="flex items-center gap-1.5 text-[11px] text-[var(--texte-tres-doux)]">
                <span
                  aria-hidden
                  className="size-1.5 shrink-0 rounded-full bg-emerald-500"
                />
                {t("nav.sessionActive")}
              </p>
            </div>
          )}
        </div>

        {!repliee && (
          <p className="px-2 pb-1.5 text-[11px] text-[var(--texte-tres-doux)]">
            {t(`role.${utilisateur.role}` as Cle)}
          </p>
        )}

        <button
          type="button"
          onClick={onDeconnexion}
          title={repliee ? t("nav.deconnexion") : undefined}
          className={cx(
            "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm",
            "text-[var(--texte-doux)] transition-colors hover:bg-red-50 hover:text-red-700",
            repliee && "justify-center px-2",
          )}
        >
          <IconeSortie />
          {!repliee && t("nav.deconnexion")}
        </button>
      </div>
    </>
  );
}

// --- Icônes ----------------------------------------------------------------
// Tracées à la main plutôt qu'importées : huit glyphes ne justifient pas une
// dépendance, et le trait reste ainsi cohérent avec le reste de l'interface.

function IconeHamburger() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 6h16M4 12h16M4 18h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IconeSortie() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
      className="shrink-0"
    >
      <path
        d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const TRACES: Record<string, string> = {
  "/mon-espace": "M3 12l9-9 9 9M5 10v10h14V10",
  "/affectations": "M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",
  "/dashboard": "M3 3v18h18M7 15l4-4 3 3 5-6",
  "/bordereau": "M4 4h16v16H4zM4 9h16M9 9v11",
  "/itineraires": "M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11z M12 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
  "/agents": "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.9",
  "/imports": "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
  "/territoire": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3c-2.5 2.7-2.5 15.3 0 18",
  "/roles": "M12 2 4 6v6c0 5 3.4 8.9 8 10 4.6-1.1 8-5 8-10V6l-8-4zM9 12l2 2 4-4",
  "/audit": "M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2m-6 9 2 2 4-4",
  "/comptes": "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
};

function IconeEntree({ href }: { href: string }) {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
      className="shrink-0"
    >
      <path
        d={TRACES[href] ?? "M4 6h16M4 12h16M4 18h16"}
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
