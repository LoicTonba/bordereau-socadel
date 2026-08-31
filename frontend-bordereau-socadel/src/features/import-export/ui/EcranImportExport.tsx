/**
 * Écran d'import / export.
 *
 * Le flux est volontairement en deux temps : dépôt du fichier, puis modal de
 * prévisualisation à valider. Rien n'est écrit tant que le superviseur n'a pas
 * confirmé sur la foi de l'aperçu.
 */

"use client";

import { useRef, useState } from "react";

import type { ApercuImport, ResultatImport } from "@core/domain/types";
import { useAgents } from "@features/agents/application/hooks";
import { ErreurApi } from "@infra/http/client";
import { Alerte, Bouton, Carte, Champ, Selecteur } from "@shared/ui/primitives";

import {
  usePrevisualiser,
  useTelechargerModele,
  useTelechargerModeleTerrain,
  useValiderImport,
} from "../application/hooks";
import { ModalApercuImport } from "./ModalApercuImport";

const EXTENSIONS = ".xlsx,.xls,.csv";

export function EcranImportExport() {
  const champFichier = useRef<HTMLInputElement>(null);
  const { data: agents = [] } = useAgents(true);

  const previsualiser = usePrevisualiser();
  const validerImport = useValiderImport();
  const modele = useTelechargerModele();
  const modeleTerrain = useTelechargerModeleTerrain();

  const [fichier, setFichier] = useState<File | null>(null);
  const [apercu, setApercu] = useState<ApercuImport | null>(null);
  const [dateCollecte, setDateCollecte] = useState(() =>
    new Date().toISOString().slice(0, 10),
  );
  const [agentId, setAgentId] = useState("");
  const [resultat, setResultat] = useState<ResultatImport | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  async function deposer(nouveauFichier: File) {
    setErreur(null);
    setResultat(null);
    setFichier(nouveauFichier);

    try {
      setApercu(await previsualiser.mutateAsync(nouveauFichier));
    } catch (exception) {
      setFichier(null);
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : "Le fichier n'a pas pu être analysé.",
      );
    }
  }

  async function confirmer() {
    if (!fichier) return;
    setErreur(null);

    try {
      setResultat(
        await validerImport.mutateAsync({
          fichier,
          dateCollecte,
          agentId: agentId || undefined,
        }),
      );
      fermerApercu();
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : "L'import a échoué.",
      );
    }
  }

  function fermerApercu() {
    setApercu(null);
    setFichier(null);
    // Le champ est réinitialisé pour qu'un même fichier redéposé déclenche
    // bien un nouvel événement `change`.
    if (champFichier.current) champFichier.current.value = "";
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-lg font-semibold">Import et export</h1>
        <p className="text-sm text-[var(--texte-doux)]">
          Distribuez le modèle aux agents, puis importez leurs bordereaux remplis.
        </p>
      </header>

      {erreur && <Alerte>{erreur}</Alerte>}

      {resultat && (
        <Alerte ton="succes">
          Import terminé : {resultat.lignesCreees} ligne(s) enregistrée(s)
          {resultat.lignesIgnorees > 0 &&
            `, ${resultat.lignesIgnorees} ignorée(s)`}
          .
          {resultat.anomalies.length > 0 && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs font-medium">
                Voir les {resultat.anomalies.length} anomalie(s)
              </summary>
              <ul className="mt-1.5 max-h-40 space-y-0.5 overflow-auto text-xs">
                {resultat.anomalies.map((anomalie, index) => (
                  <li key={index}>
                    Ligne {anomalie.ligne} — {anomalie.colonne} :{" "}
                    {anomalie.message}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </Alerte>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Carte
          titre="Bordereau de terrain"
          description="Le document que l'agent emporte et annote au stylo."
        >
          <div className="space-y-3 p-5">
            <p className="text-sm text-[var(--texte-doux)]">
              Maquette de la campagne : un bandeau par tournée, les colonnes
              pré-remplies, et deux colonnes à remplir, <b>RAPPORT</b> et{" "}
              <b>N° WhatsApp</b>. La légende et la ligne de signature figurent
              sur le document.
            </p>
            <div className="flex flex-wrap gap-2">
              <Bouton
                onClick={() => modeleTerrain.mutate("pdf")}
                chargement={modeleTerrain.isPending}
              >
                Bordereau terrain (.pdf)
              </Bouton>
              <Bouton
                variante="secondaire"
                onClick={() => modeleTerrain.mutate("xlsx")}
                chargement={modeleTerrain.isPending}
              >
                Bordereau terrain (.xlsx)
              </Bouton>
            </div>
            <p className="text-xs text-[var(--texte-tres-doux)]">
              Le PDF s&apos;imprime et part en tournée. Le classeur sert à
              préparer ou compléter une tournée hors application.
            </p>
          </div>
        </Carte>

        <Carte
          titre="Modèle d'import"
          description="Le classeur à remplir pour réinjecter une production."
        >
          <div className="space-y-3 p-5">
            <p className="text-sm text-[var(--texte-doux)]">
              Ses en-têtes sont exactement ceux que l&apos;import sait relire, et
              les colonnes Statut et Responsable proposent des listes fermées :
              un fichier issu de ce modèle ne sera jamais refusé pour cause de
              colonnes inattendues.
            </p>
            <Bouton
              variante="secondaire"
              onClick={() => modele.mutate()}
              chargement={modele.isPending}
            >
              Modèle d&apos;import (.xlsx)
            </Bouton>
          </div>
        </Carte>

        <Carte
          titre="Importer un bordereau rempli"
          description="Un aperçu vous sera présenté avant tout enregistrement."
        >
          <div className="space-y-4 p-5">
            <Champ
              name="dateCollecte"
              type="date"
              libelle="Journée de collecte"
              value={dateCollecte}
              onChange={(evenement) => setDateCollecte(evenement.target.value)}
              aide="Date à laquelle les visites ont eu lieu."
            />

            <Selecteur
              name="agent"
              libelle="Agent concerné (facultatif)"
              value={agentId}
              onChange={(evenement) => setAgentId(evenement.target.value)}
            >
              <option value="">Non précisé</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.nomComplet} — {agent.matricule}
                </option>
              ))}
            </Selecteur>

            <div>
              <label
                htmlFor="fichier"
                className="mb-1.5 block text-sm font-medium text-[var(--texte-doux)]"
              >
                Fichier du bordereau
              </label>
              <input
                ref={champFichier}
                id="fichier"
                type="file"
                accept={EXTENSIONS}
                className="champ file:mr-3 file:rounded-md file:border-0 file:bg-socadel-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-socadel-700"
                onChange={(evenement) => {
                  const choisi = evenement.target.files?.[0];
                  if (choisi) void deposer(choisi);
                }}
                disabled={previsualiser.isPending}
              />
              <p className="mt-1.5 text-xs text-[var(--texte-tres-doux)]">
                Formats acceptés : Excel (.xlsx, .xls) et CSV. 25 Mo maximum.
                {previsualiser.isPending && " Analyse en cours…"}
              </p>
            </div>
          </div>
        </Carte>
      </div>

      <ModalApercuImport
        apercu={apercu}
        enCours={validerImport.isPending}
        onConfirmer={confirmer}
        onFermer={fermerApercu}
      />
    </div>
  );
}
