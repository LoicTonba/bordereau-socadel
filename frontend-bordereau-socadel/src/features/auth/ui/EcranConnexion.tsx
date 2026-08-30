/**
 * Écran de connexion, en deux volets.
 *
 * À gauche, ce que fait l'application et pourquoi elle existe ; à droite, le
 * parcours en trois temps. Le superviseur n'est pas informaticien : la page lui
 * rappelle sa place dans la chaîne avant même qu'il se connecte.
 */

"use client";

import Link from "next/link";

import { useT } from "@core/i18n/PreferencesProvider";
import { LogoSocadel, MarqueSocadel } from "@shared/ui/Logo";

import { FormulaireConnexion } from "./FormulaireConnexion";

const ETAPES = ["etape1", "etape2", "etape3"] as const;

export function EcranConnexion() {
  const t = useT();

  return (
    <main className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      {/* Volet de présentation, masqué sur mobile où il ferait défiler
          le formulaire hors de l'écran. */}
      <section className="relative hidden flex-col justify-between bg-socadel-700 p-10 text-white lg:flex">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-25"
          style={{
            backgroundImage:
              "radial-gradient(circle at 18% 12%, #60b1e8 0%, transparent 45%), radial-gradient(circle at 82% 88%, #152b48 0%, transparent 55%)",
          }}
        />

        <div className="relative">
          <div className="flex items-center gap-3">
            <MarqueSocadel taille={40} />
            <div>
              <p className="text-sm font-semibold tracking-wide">SOCADEL</p>
              <p className="text-xs text-socadel-100">{t("app.societe")}</p>
            </div>
          </div>

          <h1 className="mt-12 max-w-md text-3xl leading-tight font-semibold">
            {t("login.titre")}
          </h1>
          <p className="mt-3 max-w-md text-sm text-socadel-100">
            {t("login.sousTitre")}
          </p>

          <ol className="mt-10 space-y-5">
            {ETAPES.map((etape, index) => (
              <li key={etape} className="flex gap-3.5">
                <span className="chiffres mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-white/15 text-xs font-semibold">
                  {index + 1}
                </span>
                <div>
                  <p className="text-sm font-medium">
                    {t(`login.${etape}.titre`)}
                  </p>
                  <p className="mt-0.5 max-w-sm text-xs text-socadel-100">
                    {t(`login.${etape}.texte`)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <p className="relative text-xs text-socadel-200">
          {t("app.editeurComplet")}
        </p>
      </section>

      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex justify-center lg:hidden">
            <LogoSocadel largeur={190} />
          </div>

          <FormulaireConnexion />

          {/* Les deux issues du parcours : ceux qui n'ont pas encore de compte,
              et ceux qui en ont un mais ne peuvent plus y entrer. */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs">
            <Link
              href="/inscription"
              className="font-medium text-socadel-600 hover:underline dark:text-socadel-400"
            >
              {t("login.creerCompte")}
            </Link>
            <span aria-hidden className="text-[var(--texte-tres-doux)]">
              ·
            </span>
            <Link
              href="/mot-de-passe-oublie"
              className="text-[var(--texte-doux)] hover:underline"
            >
              {t("login.motDePasseOublie")}
            </Link>
          </div>

          <p className="mt-6 text-center text-xs text-[var(--texte-tres-doux)]">
            {t("login.mentionAcces")}
            <br />
            {t("login.mentionContact")}
          </p>
        </div>
      </section>
    </main>
  );
}
