/**
 * Recherche d'itinéraires et impression du bordereau de terrain.
 *
 * Écran de consultation : le superviseur y retrouve un itinéraire et réimprime
 * son bordereau, sans repasser par l'affectation.
 */

"use client";

import { useState } from "react";

import { ErreurApi } from "@infra/http/client";
import { Alerte, Bouton, Carte, EtatVide } from "@shared/ui/primitives";

import { useBordereauTerrain, useRechercheItineraires } from "../application/hooks";

export function EcranItineraires() {
  const [terme, setTerme] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);

  const { data, isFetching } = useRechercheItineraires(terme);
  const bordereau = useBordereauTerrain();

  async function imprimer(code: number) {
    setErreur(null);
    try {
      await bordereau.mutateAsync({ code });
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : "Le bordereau n'a pas pu être généré.",
      );
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-lg font-semibold">Itinéraires</h1>
        <p className="text-sm text-[var(--texte-doux)]">
          Retrouvez un itinéraire et imprimez son bordereau de relevé.
        </p>
      </header>

      {erreur && <Alerte>{erreur}</Alerte>}

      <Carte>
        <div className="border-b border-[var(--bordure)] p-4">
          <input
            type="search"
            className="champ"
            placeholder="Code de l'itinéraire, agence ou libellé — au moins 2 caractères"
            value={terme}
            onChange={(evenement) => setTerme(evenement.target.value)}
            aria-label="Rechercher un itinéraire"
          />
        </div>

        {terme.trim().length < 2 ? (
          <EtatVide
            titre="Recherchez un itinéraire"
            description="Saisissez son code — par exemple 131227 — ou le nom de son agence."
          />
        ) : isFetching ? (
          <p className="px-5 py-10 text-center text-sm text-[var(--texte-tres-doux)]">
            Recherche…
          </p>
        ) : !data || data.elements.length === 0 ? (
          <EtatVide
            titre="Aucun résultat"
            description={`Aucun itinéraire ne correspond à « ${terme} ».`}
          />
        ) : (
          <ul className="divide-y divide-[var(--bordure)]">
            {data.elements.map((itineraire) => (
              <li
                key={itineraire.id}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"
              >
                <div>
                  <p className="chiffres text-sm font-medium">
                    Itinéraire {itineraire.code}
                  </p>
                  <p className="text-xs text-[var(--texte-tres-doux)]">
                    {[itineraire.agence, itineraire.division, itineraire.region]
                      .filter(Boolean)
                      .join(" · ") || "Territoire non renseigné"}
                    {" — "}
                    {itineraire.nombreClients.toLocaleString("fr-FR")} client(s)
                  </p>
                </div>

                <Bouton
                  variante="secondaire"
                  taille="sm"
                  chargement={bordereau.isPending}
                  onClick={() => imprimer(itineraire.code)}
                >
                  Bordereau terrain (PDF)
                </Bouton>
              </li>
            ))}
          </ul>
        )}
      </Carte>
    </div>
  );
}
