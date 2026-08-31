/**
 * Écran d'affectation des itinéraires.
 *
 * C'est le premier écran après la connexion, parce que c'est le premier geste
 * de la journée du superviseur : l'agent se présente, on note les itinéraires
 * qu'on lui confie, puis on imprime son bordereau de terrain.
 *
 * L'affectation fait deux choses d'un coup côté serveur : elle trace le
 * briefing et matérialise le bordereau (une ligne par client de l'itinéraire).
 */

"use client";

import { useState } from "react";

import type { Itineraire, ResultatAffectation } from "@core/domain/types";
import { useAgents } from "@features/agents/application/hooks";
import { ErreurApi } from "@infra/http/client";
import { useToasts } from "@shared/ui/Toasts";
import {
  Alerte,
  Bouton,
  Carte,
  Champ,
  cx,
  EtatVide,
  Selecteur,
} from "@shared/ui/primitives";

import {
  useAffecter,
  useBordereauTerrain,
  useRechercheItineraires,
} from "../application/hooks";

function aujourdhui(): string {
  return new Date().toISOString().slice(0, 10);
}

export function EcranAffectation() {
  const { data: agents = [], isLoading: chargementAgents } = useAgents(true);
  const affecter = useAffecter();
  const { notifier } = useToasts();
  const bordereauTerrain = useBordereauTerrain();

  const [agentId, setAgentId] = useState("");
  const [dateTravail, setDateTravail] = useState(aujourdhui);
  const [consignes, setConsignes] = useState("");
  const [terme, setTerme] = useState("");
  const [choisis, setChoisis] = useState<Itineraire[]>([]);
  const [resultat, setResultat] = useState<ResultatAffectation | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  const { data: resultatsRecherche, isFetching } = useRechercheItineraires(terme);

  const totalClients = choisis.reduce(
    (somme, itineraire) => somme + itineraire.nombreClients,
    0,
  );

  function ajouter(itineraire: Itineraire) {
    if (choisis.some((choisi) => choisi.code === itineraire.code)) return;
    setChoisis((actuels) => [...actuels, itineraire]);
    setTerme("");
  }

  function retirer(code: number) {
    setChoisis((actuels) => actuels.filter((itineraire) => itineraire.code !== code));
  }

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);
    setResultat(null);

    try {
      setResultat(
        await affecter.mutateAsync({
          agentId,
          codesItineraires: choisis.map((itineraire) => itineraire.code),
          dateTravail,
          consignes: consignes.trim() || null,
        }),
      );
      setChoisis([]);
      setConsignes("");
      notifier("creation", "Itinéraires affectés, le bordereau est prêt.");
    } catch (exception) {
      const message =
        exception instanceof ErreurApi
          ? exception.message
          : "L'affectation a échoué.";
      setErreur(message);
      notifier("echec", message);
    }
  }

  const pretASoumettre = agentId !== "" && choisis.length > 0 && dateTravail !== "";

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-lg font-semibold">Affectation des itinéraires</h1>
        <p className="text-sm text-[var(--texte-doux)]">
          L&apos;agent se présente : notez les itinéraires que vous lui confiez,
          puis imprimez son bordereau de terrain.
        </p>
      </header>

      {erreur && <Alerte>{erreur}</Alerte>}

      {resultat && (
        <Carte
          titre="Affectation enregistrée"
          description={`${resultat.nomAgent} (${resultat.matricule}), ${resultat.itineraires.length} itinéraire(s), ${resultat.totalLignes} ligne(s) de bordereau créées.`}
        >
          <ul className="divide-y divide-[var(--bordure)]">
            {resultat.itineraires.map((itineraire) => (
              <li
                key={itineraire.affectationId}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"
              >
                <div>
                  <p className="text-sm font-medium">{itineraire.libelle}</p>
                  <p className="chiffres text-xs text-[var(--texte-tres-doux)]">
                    Itinéraire {itineraire.codeItineraire} ·{" "}
                    {itineraire.lignesGenerees} client(s)
                  </p>
                </div>
                <Bouton
                  taille="sm"
                  variante="secondaire"
                  chargement={bordereauTerrain.isPending}
                  onClick={() =>
                    bordereauTerrain.mutate({
                      code: itineraire.codeItineraire,
                      agentId: resultat.agentId,
                    })
                  }
                >
                  Imprimer le bordereau
                </Bouton>
              </li>
            ))}
          </ul>
        </Carte>
      )}

      <form onSubmit={soumettre} className="grid gap-4 lg:grid-cols-[1fr_1.1fr]">
        <Carte titre="Agent et journée" className="p-5">
          <div className="space-y-4">
            <Selecteur
              name="agent"
              libelle="Agent de terrain"
              value={agentId}
              onChange={(evenement) => setAgentId(evenement.target.value)}
              required
            >
              <option value="">
                {chargementAgents ? "Chargement…" : "Sélectionner un agent"}
              </option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.nomComplet}, {agent.matricule}
                  {agent.zoneRattachement ? ` (${agent.zoneRattachement})` : ""}
                </option>
              ))}
            </Selecteur>

            {!chargementAgents && agents.length === 0 && (
              <Alerte ton="info">
                Aucun agent actif n&apos;est enregistré. Créez-en un depuis
                l&apos;écran « Agents » avant d&apos;affecter un itinéraire.
              </Alerte>
            )}

            <Champ
              name="dateTravail"
              type="date"
              libelle="Journée de travail"
              value={dateTravail}
              onChange={(evenement) => setDateTravail(evenement.target.value)}
              required
            />

            <Champ
              name="consignes"
              libelle="Consignes (facultatif)"
              placeholder="Quartier prioritaire, point de rendez-vous…"
              maxLength={500}
              value={consignes}
              onChange={(evenement) => setConsignes(evenement.target.value)}
            />
          </div>
        </Carte>

        <Carte
          titre="Itinéraires confiés"
          description={
            choisis.length > 0
              ? `${choisis.length} itinéraire(s) · ${totalClients.toLocaleString("fr-FR")} client(s) à démarcher`
              : "Recherchez par code, agence ou libellé."
          }
          className="flex flex-col"
        >
          <div className="border-b border-[var(--bordure)] p-4">
            <input
              type="search"
              className="champ"
              placeholder="Code de l'itinéraire, ex. 131227, ou nom d'agence"
              value={terme}
              onChange={(evenement) => setTerme(evenement.target.value)}
              aria-label="Rechercher un itinéraire"
            />

            {terme.trim().length >= 2 && (
              <div className="mt-2 max-h-56 overflow-auto rounded-lg border border-[var(--bordure)]">
                {isFetching && (
                  <p className="px-3 py-2.5 text-xs text-[var(--texte-tres-doux)]">
                    Recherche…
                  </p>
                )}

                {!isFetching && resultatsRecherche?.elements.length === 0 && (
                  <p className="px-3 py-2.5 text-xs text-[var(--texte-tres-doux)]">
                    Aucun itinéraire ne correspond à « {terme} ».
                  </p>
                )}

                {resultatsRecherche?.elements.map((itineraire) => {
                  const deja = choisis.some(
                    (choisi) => choisi.code === itineraire.code,
                  );
                  return (
                    <button
                      key={itineraire.id}
                      type="button"
                      disabled={deja}
                      onClick={() => ajouter(itineraire)}
                      className={cx(
                        "flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm",
                        deja
                          ? "cursor-not-allowed opacity-50"
                          : "hover:bg-[var(--fond-survol)]",
                      )}
                    >
                      <span>
                        <span className="chiffres font-medium">{itineraire.code}</span>
                        <span className="ml-2 text-xs text-[var(--texte-doux)]">
                          {itineraire.agence ?? itineraire.libelle}
                        </span>
                      </span>
                      <span className="chiffres text-xs text-[var(--texte-tres-doux)]">
                        {itineraire.nombreClients.toLocaleString("fr-FR")} clients
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="flex-1">
            {choisis.length === 0 ? (
              <EtatVide
                titre="Aucun itinéraire sélectionné"
                description="Recherchez un itinéraire ci-dessus pour le confier à l'agent."
              />
            ) : (
              <ul className="divide-y divide-[var(--bordure)]">
                {choisis.map((itineraire) => (
                  <li
                    key={itineraire.code}
                    className="flex items-center justify-between gap-3 px-4 py-2.5"
                  >
                    <div>
                      <p className="chiffres text-sm font-medium">
                        Itinéraire {itineraire.code}
                      </p>
                      <p className="text-xs text-[var(--texte-tres-doux)]">
                        {itineraire.agence ?? "—"} ·{" "}
                        {itineraire.nombreClients.toLocaleString("fr-FR")} client(s)
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => retirer(itineraire.code)}
                      className="rounded-md px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                    >
                      Retirer
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="border-t border-[var(--bordure)] p-4">
            <Bouton
              type="submit"
              className="w-full"
              disabled={!pretASoumettre}
              chargement={affecter.isPending}
            >
              Affecter et générer le bordereau
            </Bouton>
            <p className="mt-2 text-center text-xs text-[var(--texte-tres-doux)]">
              Une ligne de bordereau sera créée pour chaque client des
              itinéraires retenus.
            </p>
          </div>
        </Carte>
      </form>
    </div>
  );
}
