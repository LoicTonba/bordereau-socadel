/**
 * Connexion en trois temps : le profil, l'agence, puis les identifiants.
 *
 * L'ordre n'est pas cosmétique. Dire d'abord qui l'on est et où l'on se trouve
 * permet d'ouvrir la session sur le bon écran, déjà cadré, plutôt que de
 * déverser un national de 181 agences et de laisser chacun filtrer. Un
 * superviseur peut même noter au passage les itinéraires que son agent lui
 * récite de mémoire : il arrive alors directement sur leur bordereau.
 *
 * Ces deux premiers choix sont des **déclarations**, pas des droits. L'API les
 * confronte au compte et refuse la session si elles divergent ; le périmètre
 * effectif reste celui du compte, appliqué côté serveur.
 */

"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Agence, Role } from "@core/domain/types";
import { ErreurApi } from "@infra/http/client";
import { Alerte, Bouton, Champ, cx } from "@shared/ui/primitives";

import { authApi } from "../infrastructure/auth-api";
import {
  PROFILS,
  destination,
  lireCodesItineraires,
  profil as decrireProfil,
} from "../domain/profils";
import { useSession } from "../application/SessionProvider";
import { ChoixAgence } from "./ChoixAgence";

type Etape = "profil" | "agence" | "identifiants";

const ETAPES: readonly Etape[] = ["profil", "agence", "identifiants"];

export function FormulaireConnexion() {
  const t = useT();
  const router = useRouter();
  const { connecter } = useSession();

  const [etape, setEtape] = useState<Etape>("profil");
  const [role, setRole] = useState<Role | null>(null);
  const [agence, setAgence] = useState<string | null>(null);

  const [identifiant, setIdentifiant] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [saisieItineraires, setSaisieItineraires] = useState("");

  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const { agences, chargement, indisponible } = useAnnuaire();
  const { codes, invalide } = useMemo(
    () => lireCodesItineraires(saisieItineraires),
    [saisieItineraires],
  );

  function choisirProfil(suivant: Role) {
    setRole(suivant);
    setAgence(null);
    setErreur(null);
    setEtape("agence");
  }

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);
    setEnCours(true);

    try {
      await connecter(identifiant, motDePasse, {
        role: role!,
        agence,
        itineraires: codes,
      });
      router.replace(destination(role!, codes));
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi ? exception.message : t("login.echec"),
      );
      setEnCours(false);
    }
  }

  return (
    <div className="space-y-6">
      <Fil etape={etape} />

      {erreur && <Alerte>{erreur}</Alerte>}

      {etape === "profil" && (
        <section className="space-y-4">
          <Entete
            titre={t("poste.profil.titre")}
            aide={t("poste.profil.aide")}
          />
          <ul className="space-y-2.5">
            {PROFILS.map((p) => (
              <li key={p.role}>
                <CarteProfil
                  role={p.role}
                  maison={p.maison}
                  onClick={() => choisirProfil(p.role)}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      {etape === "agence" && role && (
        <section className="space-y-4">
          <Entete
            titre={t("poste.agence.titre")}
            aide={t("poste.agence.aide")}
          />
          <ChoixAgence
            agences={agences}
            chargement={chargement}
            indisponible={indisponible}
            // Seuls les profils à portée nationale peuvent s'en tenir au
            // national ; un superviseur travaille toujours quelque part.
            autoriserNational={!decrireProfil(role).ancreDansUneAgence}
            valeur={agence}
            onChange={setAgence}
          />
          <div className="flex gap-3">
            <Bouton
              type="button"
              variante="secondaire"
              onClick={() => setEtape("profil")}
            >
              {t("poste.retour")}
            </Bouton>
            <Bouton
              type="button"
              className="flex-1"
              disabled={decrireProfil(role).ancreDansUneAgence && !agence}
              onClick={() => setEtape("identifiants")}
            >
              {t("poste.continuer")}
            </Bouton>
          </div>
        </section>
      )}

      {etape === "identifiants" && role && (
        <form onSubmit={soumettre} className="space-y-4" noValidate>
          <Entete titre={t("poste.identifiants.titre")} />

          <Recapitulatif
            role={role}
            agence={agence}
            onChanger={() => setEtape("profil")}
          />

          <Champ
            name="identifiant"
            type="email"
            libelle={t("login.identifiant")}
            placeholder={t("login.identifiantExemple")}
            aide={t("login.identifiantAide")}
            autoComplete="username"
            autoFocus
            required
            value={identifiant}
            onChange={(evenement) => setIdentifiant(evenement.target.value)}
          />

          <Champ
            name="motDePasse"
            type="password"
            libelle={t("login.motDePasse")}
            placeholder="••••••••"
            aide={t("login.motDePasseAide")}
            autoComplete="current-password"
            required
            value={motDePasse}
            onChange={(evenement) => setMotDePasse(evenement.target.value)}
          />

          {role === "SUPERVISEUR" && (
            <Champ
              name="itineraires"
              inputMode="numeric"
              libelle={t("poste.itineraires.libelle")}
              placeholder={t("poste.itineraires.placeholder")}
              autoComplete="off"
              value={saisieItineraires}
              onChange={(evenement) => setSaisieItineraires(evenement.target.value)}
              erreur={invalide ? t("poste.itineraires.invalide") : undefined}
              aide={
                codes.length > 0
                  ? t("poste.itineraires.compte", { n: codes.length })
                  : t("poste.itineraires.aide")
              }
            />
          )}

          <div className="flex gap-3">
            <Bouton
              type="button"
              variante="secondaire"
              onClick={() => setEtape("agence")}
            >
              {t("poste.retour")}
            </Bouton>
            <Bouton
              type="submit"
              chargement={enCours}
              className="flex-1"
              disabled={!identifiant || !motDePasse}
            >
              {enCours ? t("login.connexionEnCours") : t("login.seConnecter")}
            </Bouton>
          </div>
        </form>
      )}
    </div>
  );
}

/**
 * L'annuaire des agences, chargé une fois pour toutes.
 *
 * Il est servi avant authentification : le sélecteur doit se remplir alors
 * qu'aucune session n'existe. Son indisponibilité ne bloque pas la connexion,
 * elle prive seulement de la présélection.
 */
function useAnnuaire() {
  const [agences, setAgences] = useState<Agence[]>([]);
  const [chargement, setChargement] = useState(true);
  const [indisponible, setIndisponible] = useState(false);

  useEffect(() => {
    let annule = false;

    authApi
      .agences()
      .then((reponse) => {
        if (!annule) setAgences(reponse.agences);
      })
      .catch(() => {
        if (!annule) setIndisponible(true);
      })
      .finally(() => {
        if (!annule) setChargement(false);
      });

    return () => {
      annule = true;
    };
  }, []);

  return { agences, chargement, indisponible };
}

function Entete({ titre, aide }: { titre: string; aide?: string }) {
  return (
    <div>
      <h3 className="text-base font-semibold">{titre}</h3>
      {aide && (
        <p className="mt-1 text-xs leading-relaxed text-[var(--texte-tres-doux)]">
          {aide}
        </p>
      )}
    </div>
  );
}

function Fil({ etape }: { etape: Etape }) {
  const t = useT();
  const position = ETAPES.indexOf(etape);

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-[var(--texte-tres-doux)]">
        {t("poste.etape", { n: position + 1 })}
      </p>
      <div className="flex gap-1.5" aria-hidden>
        {ETAPES.map((_, index) => (
          <span
            key={index}
            className={cx(
              "h-1 flex-1 rounded-full transition-colors",
              index <= position
                ? "bg-socadel-600 dark:bg-socadel-400"
                : "bg-[var(--bordure)]",
            )}
          />
        ))}
      </div>
    </div>
  );
}

function CarteProfil({
  role,
  maison,
  onClick,
}: {
  role: Role;
  maison: string;
  onClick: () => void;
}) {
  const t = useT();
  return (
    <button
      type="button"
      onClick={onClick}
      className={cx(
        "group flex w-full items-center gap-3.5 rounded-xl border p-3.5 text-left",
        "border-[var(--bordure)] bg-[var(--fond-carte)] transition-colors",
        "hover:border-socadel-400 hover:bg-socadel-50 dark:hover:bg-socadel-950",
      )}
    >
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-lg bg-socadel-600 text-xs font-semibold text-white"
      >
        {INITIALES[role]}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium">{t(`role.${role}`)}</span>
        <span className="block truncate text-xs text-[var(--texte-tres-doux)]">
          {maison}, {t(`poste.profil.${role}`)}
        </span>
      </span>
      <span
        aria-hidden
        className="text-[var(--texte-tres-doux)] transition-transform group-hover:translate-x-0.5"
      >
        <svg viewBox="0 0 20 20" className="size-4" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M7.3 4.3a1 1 0 0 1 1.4 0l5 5a1 1 0 0 1 0 1.4l-5 5a1 1 0 0 1-1.4-1.4L11.58 10 7.3 5.7a1 1 0 0 1 0-1.4Z"
            clipRule="evenodd"
          />
        </svg>
      </span>
    </button>
  );
}

/** Deux lettres suffisent à distinguer les quatre profils dans la pastille. */
const INITIALES: Record<Role, string> = {
  SUPER_UTILISATEUR: "SU",
  ADMINISTRATEUR: "AD",
  SUPERVISEUR: "SV",
  AGENT_TERRAIN: "AG",
};

function Recapitulatif({
  role,
  agence,
  onChanger,
}: {
  role: Role;
  agence: string | null;
  onChanger: () => void;
}) {
  const t = useT();
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg bg-[var(--fond-survol)] px-3 py-2.5">
      <p className="min-w-0 truncate text-xs text-[var(--texte-doux)]">
        {t("poste.recapitulatif", {
          profil: t(`role.${role}`),
          agence: agence ?? t("poste.agence.nationale"),
        })}
      </p>
      <button
        type="button"
        onClick={onChanger}
        className="shrink-0 text-xs font-medium text-socadel-600 hover:underline dark:text-socadel-400"
      >
        {t("poste.changer")}
      </button>
    </div>
  );
}
