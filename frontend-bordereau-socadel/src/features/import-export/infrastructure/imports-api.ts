/** Appels HTTP d'import et de téléchargement de modèle. */

import type { ApercuImport, ResultatImport } from "@core/domain/types";
import { api } from "@infra/http/client";

export const importsApi = {
  /** Analyse à blanc : rien n'est écrit, le résultat alimente le modal. */
  previsualiser(fichier: File): Promise<ApercuImport> {
    const formulaire = new FormData();
    formulaire.append("fichier", fichier);
    return api.postFichier<ApercuImport>("/imports/apercu", formulaire);
  },

  valider(donnees: {
    fichier: File;
    dateCollecte: string;
    agentId?: string;
    affectationId?: string;
  }): Promise<ResultatImport> {
    const formulaire = new FormData();
    formulaire.append("fichier", donnees.fichier);
    formulaire.append("date_collecte", donnees.dateCollecte);
    if (donnees.agentId) formulaire.append("agent_id", donnees.agentId);
    if (donnees.affectationId) {
      formulaire.append("affectation_id", donnees.affectationId);
    }
    return api.postFichier<ResultatImport>("/imports", formulaire);
  },

  /** Le modèle d'import : colonnes que le lecteur sait relire. */
  modele() {
    return api.telecharger("/imports/modele");
  },

  /** Le bordereau de terrain, celui que l'agent emporte et annote. */
  modeleTerrain(format: "pdf" | "xlsx") {
    return api.telecharger(`/imports/modele-terrain?format=${format}`);
  },
};
