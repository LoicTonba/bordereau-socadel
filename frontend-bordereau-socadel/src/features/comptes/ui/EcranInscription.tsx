/**
 * Formulaire d'inscription.
 *
 * S'inscrire ne donne pas accès, et la page le dit avant le premier champ : la
 * plateforme porte le référentiel clients de SOCADEL, un accès s'accorde. Le
 * demandeur choisit son propre mot de passe, ce qui évite le mot de passe
 * provisoire transmis par courriel, lisible pendant des années dans une boîte.
 */

"use client";

import { useState } from "react";
import Link from "next/link";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Role } from "@core/domain/types";
import { ErreurApi } from "@infra/http/client";
import { PROFILS } from "@features/auth/domain/profils";
import { Alerte, Bouton, Champ, Selecteur } from "@shared/ui/primitives";
import { LogoSocadel } from "@shared/ui/Logo";

import { useForceMotDePasse, useInscription } from "../application/hooks";
import { JaugeMotDePasse } from "./JaugeMotDePasse";

export function EcranInscription() {
  const t = useT();
  const inscrire = useInscription();

  const [identifiant, setIdentifiant] = useState("");
  const [nomComplet, setNomComplet] = useState("");
  const [email, setEmail] = useState("");
  const [telephone, setTelephone] = useState("");
  const [roleSouhaite, setRoleSouhaite] = useState<Role>("SUPERVISEUR");
  const [motDePasse, setMotDePasse] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [depose, setDepose] = useState<string | null>(null);

  const force = useForceMotDePasse(motDePasse, identifiant, email);
  const discordance = confirmation.length > 0 && confirmation !== motDePasse;

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);
    try {
      const reponse = await inscrire.mutateAsync({
        identifiant,
        nomComplet,
        email,
        motDePasse,
        confirmation,
        telephone: telephone || null,
        roleSouhaite,
      });
      setDepose(reponse.message);
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : t("inscription.echec"),
      );
    }
  }

  if (depose) {
    return (
      <Cadre>
        <h1 className="text-xl font-semibold">{t("inscription.deposeeTitre")}</h1>
        <p className="mt-3 text-sm leading-relaxed text-[var(--texte-doux)]">
          {depose}
        </p>
        <p className="mt-4 text-xs leading-relaxed text-[var(--texte-tres-doux)]">
          {t("inscription.deposeeSuite")}
        </p>
        <Link
          href="/login"
          className="mt-6 inline-block text-sm font-medium text-socadel-600 hover:underline dark:text-socadel-400"
        >
          {t("inscription.retourConnexion")}
        </Link>
      </Cadre>
    );
  }

  return (
    <Cadre>
      <h1 className="text-xl font-semibold">{t("inscription.titre")}</h1>
      <p className="mt-1 mb-6 text-sm leading-relaxed text-[var(--texte-doux)]">
        {t("inscription.chapeau")}
      </p>

      <form onSubmit={soumettre} className="space-y-4" noValidate>
        {erreur && <Alerte>{erreur}</Alerte>}

        <Champ
          name="nomComplet"
          libelle={t("inscription.nomComplet")}
          placeholder="MBARGA Jeanne"
          autoComplete="name"
          required
          value={nomComplet}
          onChange={(evenement) => setNomComplet(evenement.target.value)}
        />

        <Champ
          name="identifiant"
          libelle={t("inscription.identifiant")}
          aide={t("inscription.identifiantAide")}
          autoComplete="username"
          required
          value={identifiant}
          onChange={(evenement) => setIdentifiant(evenement.target.value)}
        />

        <Champ
          name="email"
          type="email"
          libelle={t("inscription.email")}
          autoComplete="email"
          required
          value={email}
          onChange={(evenement) => setEmail(evenement.target.value)}
        />

        <Champ
          name="telephone"
          type="tel"
          libelle={t("inscription.telephone")}
          placeholder="+237 6 94 17 47 68"
          autoComplete="tel"
          value={telephone}
          onChange={(evenement) => setTelephone(evenement.target.value)}
        />

        <Selecteur
          name="roleSouhaite"
          libelle={t("inscription.roleSouhaite")}
          value={roleSouhaite}
          onChange={(evenement) => setRoleSouhaite(evenement.target.value as Role)}
        >
          {PROFILS.map((profil) => (
            <option key={profil.role} value={profil.role}>
              {t(`role.${profil.role}`)}, {profil.maison}
            </option>
          ))}
        </Selecteur>
        <p className="-mt-2 text-xs text-[var(--texte-tres-doux)]">
          {t("inscription.roleAide")}
        </p>

        <div className="space-y-2">
          <Champ
            name="motDePasse"
            type="password"
            libelle={t("inscription.motDePasse")}
            autoComplete="new-password"
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
          chargement={inscrire.isPending}
          disabled={
            !identifiant ||
            !nomComplet ||
            !email ||
            !motDePasse ||
            discordance ||
            force?.acceptable === false
          }
        >
          {t("inscription.envoyer")}
        </Bouton>
      </form>

      <p className="mt-6 text-center text-xs text-[var(--texte-tres-doux)]">
        {t("inscription.dejaInscrit")}{" "}
        <Link
          href="/login"
          className="font-medium text-socadel-600 hover:underline dark:text-socadel-400"
        >
          {t("login.seConnecter")}
        </Link>
      </p>
    </Cadre>
  );
}

/** Cadre commun aux écrans hors session : logo, carte centrée, fond neutre. */
export function Cadre({ children }: { children: React.ReactNode }) {
  return (
    <main className="grid min-h-dvh place-items-center bg-[var(--fond)] px-6 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <LogoSocadel largeur={180} />
        </div>
        <div className="rounded-2xl border border-[var(--bordure)] bg-[var(--fond-carte)] p-7 shadow-sm">
          {children}
        </div>
      </div>
    </main>
  );
}
