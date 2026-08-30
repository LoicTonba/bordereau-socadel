/** Appels HTTP du cycle de vie des comptes. */

import type { Compte, ForceMotDePasse, Role, StatutCompte } from "@core/domain/types";
import { api } from "@infra/http/client";

export interface DemandeInscription {
  identifiant: string;
  nomComplet: string;
  email: string;
  motDePasse: string;
  confirmation: string;
  telephone?: string | null;
  roleSouhaite?: Role | null;
}

export interface ReponseInscription {
  identifiant: string;
  email: string;
  statut: StatutCompte;
  message: string;
}

export interface DonneesApprobation {
  role: Role;
  region?: string | null;
  agence?: string | null;
  agentId?: string | null;
}

export interface MotDePasseProvisoire {
  identifiant: string;
  nomComplet: string;
  motDePasseProvisoire: string;
  consigne: string;
}

export const comptesApi = {
  // --- Parcours public ------------------------------------------------------

  inscription(demande: DemandeInscription): Promise<ReponseInscription> {
    return api.post<ReponseInscription>("/comptes/inscription", demande);
  },

  /**
   * Évalue un mot de passe pendant la frappe.
   *
   * L'évaluation est demandée au serveur plutôt que recodée ici : la même
   * politique tranchera à l'inscription, et deux implémentations finiraient
   * par diverger.
   */
  forceMotDePasse(
    motDePasse: string,
    identifiant?: string,
    email?: string,
  ): Promise<ForceMotDePasse> {
    return api.post<ForceMotDePasse>("/comptes/force-mot-de-passe", {
      motDePasse,
      identifiant: identifiant || null,
      email: email || null,
    });
  },

  verification(jeton: string): Promise<ReponseInscription> {
    return api.get<ReponseInscription>("/comptes/verification", { jeton });
  },

  oubliMotDePasse(email: string): Promise<{ message: string }> {
    return api.post<{ message: string }>("/comptes/mot-de-passe/oubli", { email });
  },

  reinitialisation(
    jeton: string,
    nouveauMotDePasse: string,
    confirmation: string,
  ): Promise<void> {
    return api.post<void>("/comptes/mot-de-passe/reinitialisation", {
      jeton,
      nouveauMotDePasse,
      confirmation,
    });
  },

  // --- Parcours authentifié -------------------------------------------------

  lister(statut?: StatutCompte): Promise<Compte[]> {
    return api.get<Compte[]>("/comptes", statut ? { statut } : undefined);
  },

  approuver(compteId: string, donnees: DonneesApprobation): Promise<Compte> {
    return api.post<Compte>(`/comptes/${compteId}/approbation`, donnees);
  },

  refuser(compteId: string, motif?: string): Promise<Compte> {
    const suffixe = motif ? `?motif=${encodeURIComponent(motif)}` : "";
    return api.post<Compte>(`/comptes/${compteId}/refus${suffixe}`);
  },

  basculerActivation(compteId: string, actif: boolean): Promise<Compte> {
    return api.patch<Compte>(`/comptes/${compteId}/activation?actif=${actif}`);
  },

  reinitialiserPourAutrui(compteId: string): Promise<MotDePasseProvisoire> {
    return api.post<MotDePasseProvisoire>(
      `/comptes/${compteId}/mot-de-passe/reinitialisation`,
    );
  },
};
