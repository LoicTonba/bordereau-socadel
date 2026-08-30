/**
 * Contexte de session : source unique de l'identité de l'utilisateur connecté.
 *
 * Au montage, le profil est revalidé auprès de l'API plutôt que lu depuis le
 * stockage local : un jeton peut avoir expiré, ou le compte avoir été
 * désactivé entre deux visites.
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import type { PosteDeTravail, Utilisateur } from "@core/domain/types";
import {
  ecrireJeton,
  ecrirePoste,
  ecrireProfil,
  lireJeton,
  supprimerJeton,
} from "@infra/storage/session";

import { authApi } from "../infrastructure/auth-api";

interface ValeurSession {
  utilisateur: Utilisateur | null;
  chargement: boolean;
  connecter: (
    identifiant: string,
    motDePasse: string,
    poste?: PosteDeTravail,
  ) => Promise<void>;
  deconnecter: () => void;
}

const ContexteSession = createContext<ValeurSession | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [utilisateur, setUtilisateur] = useState<Utilisateur | null>(null);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    let annule = false;

    async function revalider() {
      if (!lireJeton()) {
        setChargement(false);
        return;
      }
      try {
        const profil = await authApi.profil();
        if (!annule) setUtilisateur(profil);
      } catch {
        // Jeton expiré ou compte désactivé : on repart d'une session vierge.
        supprimerJeton();
      } finally {
        if (!annule) setChargement(false);
      }
    }

    void revalider();
    return () => {
      annule = true;
    };
  }, []);

  const connecter = useCallback(
    async (identifiant: string, motDePasse: string, poste?: PosteDeTravail) => {
      const session = await authApi.connexion({
        identifiant,
        motDePasse,
        role: poste?.role ?? null,
        agence: poste?.agence ?? null,
      });
      ecrireJeton(session.jeton);
      ecrireProfil({
        identifiant: session.identifiant,
        nomComplet: session.nomComplet,
        role: session.role,
      });
      // L'agence retenue est celle que le serveur renvoie, pas celle qui a été
      // demandée : c'est lui qui tranche en cas d'écart avec le compte.
      ecrirePoste({
        role: session.role,
        agence: session.agence,
        itineraires: poste?.itineraires ?? [],
      });
      setUtilisateur(await authApi.profil());
    },
    [],
  );

  const deconnecter = useCallback(() => {
    supprimerJeton();
    setUtilisateur(null);
    router.replace("/login");
  }, [router]);

  const valeur = useMemo(
    () => ({ utilisateur, chargement, connecter, deconnecter }),
    [utilisateur, chargement, connecter, deconnecter],
  );

  return <ContexteSession.Provider value={valeur}>{children}</ContexteSession.Provider>;
}

export function useSession(): ValeurSession {
  const contexte = useContext(ContexteSession);
  if (!contexte) {
    throw new Error("useSession doit être utilisé à l'intérieur de <SessionProvider>");
  }
  return contexte;
}
