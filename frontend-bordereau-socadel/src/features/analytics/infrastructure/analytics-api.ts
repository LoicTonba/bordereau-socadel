/** Appels HTTP du tableau de bord. */

import type { FiltreBordereau, TableauDeBord } from "@core/domain/types";
import { api } from "@infra/http/client";

export type FiltreTableauDeBord = FiltreBordereau & {
  debut?: string;
  fin?: string;
};

export const analyticsApi = {
  tableauDeBord(filtre: FiltreTableauDeBord): Promise<TableauDeBord> {
    // L'étalement produit un littéral d'objet, seule forme que le client HTTP
    // accepte comme sac de paramètres (une interface n'a pas de signature
    // d'index).
    return api.get<TableauDeBord>("/analytics/tableau-de-bord", { ...filtre });
  },
};
