/**
 * Page de connexion.
 *
 * Écran en deux volets : à gauche, ce que fait l'application et pourquoi elle
 * existe ; à droite, le formulaire. Le superviseur n'est pas informaticien, la
 * page lui rappelle sa place dans la chaîne avant même qu'il se connecte.
 */

import type { Metadata } from "next";

import { FormulaireConnexion } from "@features/auth/ui/FormulaireConnexion";
import { LogoSocadel, MarqueSocadel } from "@shared/ui/Logo";

export const metadata: Metadata = {
  title: "Connexion",
};

const ETAPES = [
  {
    titre: "Affecter les itinéraires",
    texte:
      "L'agent se présente, vous notez les itinéraires que vous lui confiez et imprimez son bordereau de terrain.",
  },
  {
    titre: "Saisir la production",
    texte:
      "Au retour, vous reportez ce que l'agent a réalisé : abonnements obtenus, absents, refus.",
  },
  {
    titre: "Vérifier et payer",
    texte:
      "Le référentiel SOCADEL confirme les abonnements réellement enregistrés : c'est lui qui fait foi.",
  },
];

export default function PageConnexion() {
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
              <p className="text-xs text-socadel-100">
                Société Camerounaise d&apos;Electricité
              </p>
            </div>
          </div>

          <h1 className="mt-12 max-w-md text-3xl leading-tight font-semibold">
            Bordereau intelligent de collecte WhatsApp
          </h1>
          <p className="mt-3 max-w-md text-sm text-socadel-100">
            Suivez le travail des agents de terrain, itinéraire par itinéraire,
            et confrontez chaque déclaration au référentiel SOCADEL.
          </p>

          <ol className="mt-10 space-y-5">
            {ETAPES.map((etape, index) => (
              <li key={etape.titre} className="flex gap-3.5">
                <span className="chiffres mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-white/15 text-xs font-semibold">
                  {index + 1}
                </span>
                <div>
                  <p className="text-sm font-medium">{etape.titre}</p>
                  <p className="mt-0.5 max-w-sm text-xs text-socadel-100">
                    {etape.texte}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <p className="relative text-xs text-socadel-200">
          Une solution NEXT LTD — Numeric Export Technologies
        </p>
      </section>

      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex justify-center lg:hidden">
            <LogoSocadel largeur={190} />
          </div>

          <h2 className="text-xl font-semibold">Connexion superviseur</h2>
          <p className="mt-1 mb-7 text-sm text-[var(--texte-doux)]">
            Identifiez-vous pour accéder au bordereau de collecte.
          </p>

          <FormulaireConnexion />

          <p className="mt-8 text-center text-xs text-[var(--texte-tres-doux)]">
            Accès réservé aux superviseurs SOCADEL.
            <br />
            En cas de difficulté, contactez l&apos;administrateur NEXT LTD.
          </p>
        </div>
      </section>
    </main>
  );
}
