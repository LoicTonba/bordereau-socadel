/** Formulaire de connexion du superviseur. */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ErreurApi } from "@infra/http/client";
import { Alerte, Bouton, Champ } from "@shared/ui/primitives";

import { useSession } from "../application/SessionProvider";

export function FormulaireConnexion() {
  const router = useRouter();
  const { connecter } = useSession();

  const [identifiant, setIdentifiant] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);
    setEnCours(true);

    try {
      await connecter(identifiant, motDePasse);
      // Le superviseur arrive sur l'écran d'affectation : sa première tâche
      // de la journée est d'enregistrer les itinéraires confiés aux agents.
      router.replace("/affectations");
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : "Connexion impossible. Vérifiez que le serveur est démarré.",
      );
      setEnCours(false);
    }
  }

  return (
    <form onSubmit={soumettre} className="space-y-4" noValidate>
      {erreur && <Alerte>{erreur}</Alerte>}

      <Champ
        name="identifiant"
        libelle="Identifiant"
        placeholder="superviseur"
        autoComplete="username"
        autoFocus
        required
        value={identifiant}
        onChange={(evenement) => setIdentifiant(evenement.target.value)}
      />

      <Champ
        name="motDePasse"
        type="password"
        libelle="Mot de passe"
        placeholder="••••••••"
        autoComplete="current-password"
        required
        value={motDePasse}
        onChange={(evenement) => setMotDePasse(evenement.target.value)}
      />

      <Bouton
        type="submit"
        chargement={enCours}
        className="w-full"
        disabled={!identifiant || !motDePasse}
      >
        {enCours ? "Connexion…" : "Se connecter"}
      </Bouton>
    </form>
  );
}
