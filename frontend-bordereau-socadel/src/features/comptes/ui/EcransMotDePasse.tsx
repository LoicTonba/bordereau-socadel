/**
 * Les trois écrans hors session qui gravitent autour du mot de passe :
 * confirmation d'adresse, demande de lien, choix du nouveau mot de passe.
 *
 * Ils partagent le cadre de l'inscription et la même règle : ne jamais dire à
 * un visiteur non authentifié si une adresse existe.
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { useT } from "@core/i18n/PreferencesProvider";
import { ErreurApi } from "@infra/http/client";
import { Alerte, Bouton, Champ } from "@shared/ui/primitives";

import { comptesApi } from "../infrastructure/comptes-api";
import { useForceMotDePasse, useOubliMotDePasse } from "../application/hooks";
import { Cadre } from "./EcranInscription";
import { JaugeMotDePasse } from "./JaugeMotDePasse";

// --- Confirmation de l'adresse ---------------------------------------------

export function EcranVerification() {
  const t = useT();
  const parametres = useSearchParams();
  const jeton = parametres.get("jeton") ?? "";

  const [etat, setEtat] = useState<"cours" | "fait" | "echec">("cours");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!jeton) {
      setEtat("echec");
      setMessage(t("adresse.jetonAbsent"));
      return;
    }

    let annule = false;
    comptesApi
      .verification(jeton)
      .then((reponse) => {
        if (annule) return;
        setEtat("fait");
        setMessage(reponse.message);
      })
      .catch((exception) => {
        if (annule) return;
        setEtat("echec");
        setMessage(
          exception instanceof ErreurApi
            ? exception.message
            : t("adresse.echec"),
        );
      });

    return () => {
      annule = true;
    };
  }, [jeton, t]);

  return (
    <Cadre>
      <h1 className="text-xl font-semibold">{t("adresse.titre")}</h1>
      <p className="mt-3 text-sm leading-relaxed text-[var(--texte-doux)]">
        {etat === "cours" ? t("adresse.enCours") : message}
      </p>
      {etat !== "cours" && (
        <Link
          href="/login"
          className="mt-6 inline-block text-sm font-medium text-socadel-600 hover:underline dark:text-socadel-400"
        >
          {t("inscription.retourConnexion")}
        </Link>
      )}
    </Cadre>
  );
}

// --- Demande de lien de réinitialisation ------------------------------------

export function EcranOubli() {
  const t = useT();
  const demander = useOubliMotDePasse();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    // La réponse est volontairement la même que l'adresse existe ou non :
    // distinguer les deux dirait qui possède un compte.
    const reponse = await demander.mutateAsync(email).catch(() => null);
    setMessage(reponse?.message ?? t("oubli.confirmationNeutre"));
  }

  return (
    <Cadre>
      <h1 className="text-xl font-semibold">{t("oubli.titre")}</h1>
      <p className="mt-1 mb-6 text-sm leading-relaxed text-[var(--texte-doux)]">
        {t("oubli.chapeau")}
      </p>

      {message ? (
        <Alerte ton="succes">{message}</Alerte>
      ) : (
        <form onSubmit={soumettre} className="space-y-4" noValidate>
          <Champ
            name="email"
            type="email"
            libelle={t("inscription.email")}
            autoComplete="email"
            autoFocus
            required
            value={email}
            onChange={(evenement) => setEmail(evenement.target.value)}
          />
          <Bouton
            type="submit"
            className="w-full"
            chargement={demander.isPending}
            disabled={!email}
          >
            {t("oubli.envoyer")}
          </Bouton>
        </form>
      )}

      <p className="mt-6 text-center text-xs">
        <Link
          href="/login"
          className="font-medium text-socadel-600 hover:underline dark:text-socadel-400"
        >
          {t("inscription.retourConnexion")}
        </Link>
      </p>
    </Cadre>
  );
}

// --- Choix du nouveau mot de passe ------------------------------------------

export function EcranReinitialisation() {
  const t = useT();
  const router = useRouter();
  const parametres = useSearchParams();
  const jeton = parametres.get("jeton") ?? "";

  const [motDePasse, setMotDePasse] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [fait, setFait] = useState(false);

  const force = useForceMotDePasse(motDePasse);
  const discordance = confirmation.length > 0 && confirmation !== motDePasse;

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);
    setEnCours(true);
    try {
      await comptesApi.reinitialisation(jeton, motDePasse, confirmation);
      setFait(true);
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : t("reinitialisation.echec"),
      );
      setEnCours(false);
    }
  }

  if (fait) {
    return (
      <Cadre>
        <h1 className="text-xl font-semibold">{t("reinitialisation.faitTitre")}</h1>
        <p className="mt-3 text-sm leading-relaxed text-[var(--texte-doux)]">
          {t("reinitialisation.faitTexte")}
        </p>
        <Bouton className="mt-6 w-full" onClick={() => router.replace("/login")}>
          {t("login.seConnecter")}
        </Bouton>
      </Cadre>
    );
  }

  return (
    <Cadre>
      <h1 className="text-xl font-semibold">{t("reinitialisation.titre")}</h1>
      <p className="mt-1 mb-6 text-sm leading-relaxed text-[var(--texte-doux)]">
        {t("reinitialisation.chapeau")}
      </p>

      <form onSubmit={soumettre} className="space-y-4" noValidate>
        {erreur && <Alerte>{erreur}</Alerte>}
        {!jeton && <Alerte>{t("adresse.jetonAbsent")}</Alerte>}

        <div className="space-y-2">
          <Champ
            name="motDePasse"
            type="password"
            libelle={t("reinitialisation.nouveau")}
            autoComplete="new-password"
            autoFocus
            required
            value={motDePasse}
            onChange={(evenement) => setMotDePasse(evenement.target.value)}
          />
          <JaugeMotDePasse force={force} />
        </div>

        <Champ
          name="confirmation"
          type="password"
          libelle={t("inscription.confirmation")}
          autoComplete="new-password"
          required
          value={confirmation}
          onChange={(evenement) => setConfirmation(evenement.target.value)}
          erreur={discordance ? t("inscription.discordance") : undefined}
        />

        <Bouton
          type="submit"
          className="w-full"
          chargement={enCours}
          disabled={!jeton || !motDePasse || discordance || force?.acceptable === false}
        >
          {t("reinitialisation.envoyer")}
        </Bouton>
      </form>
    </Cadre>
  );
}
