/**
 * Modal de prévisualisation d'import.
 *
 * Deuxième temps du flux voulu par le métier : le fichier a été analysé sans
 * rien écrire, le superviseur voit ici ce qui *serait* importé — lignes
 * retenues, lignes rejetées et motif de chaque rejet — avant de confirmer.
 */

"use client";

import type { ApercuImport } from "@core/domain/types";
import { Modal } from "@shared/ui/Modal";
import { Alerte, Bouton, cx } from "@shared/ui/primitives";

/** Colonnes affichées dans l'aperçu, dans l'ordre du bordereau papier. */
const COLONNES = [
  { cle: "service_no", libelle: "Contrat" },
  { cle: "nom_client", libelle: "Nom" },
  { cle: "ref_geo", libelle: "Réf. géo" },
  { cle: "code_itineraire", libelle: "Itin." },
  { cle: "numero_compteur", libelle: "Compteur" },
  { cle: "numero_collecte", libelle: "N° collecté" },
  { cle: "statut", libelle: "Statut" },
] as const;

export function ModalApercuImport({
  apercu,
  enCours,
  onConfirmer,
  onFermer,
}: {
  apercu: ApercuImport | null;
  enCours: boolean;
  onConfirmer: () => void;
  onFermer: () => void;
}) {
  return (
    <Modal
      ouvert={apercu !== null}
      onFermer={onFermer}
      taille="xl"
      titre="Vérifier avant d'importer"
      description={apercu?.nomFichier}
      pied={
        <>
          <Bouton variante="secondaire" onClick={onFermer} type="button">
            Annuler
          </Bouton>
          <Bouton
            onClick={onConfirmer}
            chargement={enCours}
            disabled={!apercu?.estValide}
          >
            Importer {apercu?.lignesValides ?? 0} ligne(s)
          </Bouton>
        </>
      }
    >
      {apercu && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <Compteur libelle="Lignes lues" valeur={apercu.totalLignes} />
            <Compteur
              libelle="Lignes retenues"
              valeur={apercu.lignesValides}
              ton="succes"
            />
            <Compteur
              libelle="Lignes rejetées"
              valeur={apercu.lignesRejetees}
              ton={apercu.lignesRejetees > 0 ? "alerte" : undefined}
            />
          </div>

          {apercu.colonnesManquantes.length > 0 && (
            <Alerte>
              Colonne(s) obligatoire(s) absente(s) :{" "}
              <strong>{apercu.colonnesManquantes.join(", ")}</strong>. Repartez du
              modèle de bordereau pour être sûr des en-têtes attendus.
            </Alerte>
          )}

          {apercu.colonnesManquantes.length === 0 && !apercu.estValide && (
            <Alerte>
              Aucune ligne exploitable dans ce fichier : l&apos;import est
              impossible en l&apos;état.
            </Alerte>
          )}

          {apercu.lignesRejetees > 0 && apercu.estValide && (
            <Alerte ton="info">
              {apercu.lignesRejetees} ligne(s) seront ignorées. Les autres seront
              importées normalement.
            </Alerte>
          )}

          <div>
            <p className="mb-2 text-xs font-medium text-[var(--texte-doux)]">
              Aperçu des {apercu.apercu.length} première(s) ligne(s)
            </p>

            <div className="overflow-x-auto rounded-lg border border-[var(--bordure)]">
              <table className="w-full min-w-[820px] border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[var(--bordure)] bg-[var(--fond-survol)] text-left">
                    <th scope="col" className="px-3 py-2 font-semibold">
                      Ligne
                    </th>
                    {COLONNES.map((colonne) => (
                      <th key={colonne.cle} scope="col" className="px-3 py-2 font-semibold">
                        {colonne.libelle}
                      </th>
                    ))}
                    <th scope="col" className="px-3 py-2 font-semibold">
                      Contrôle
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {apercu.apercu.map((ligne) => (
                    <tr
                      key={ligne.ligne}
                      className={cx(
                        "border-b border-[var(--bordure)]",
                        !ligne.estImportable && "bg-red-50",
                      )}
                    >
                      <td className="chiffres px-3 py-1.5 text-[var(--texte-tres-doux)]">
                        {ligne.ligne}
                      </td>
                      {COLONNES.map((colonne) => (
                        <td key={colonne.cle} className="chiffres px-3 py-1.5">
                          {ligne.valeurs[colonne.cle] ?? (
                            <span className="text-[var(--texte-tres-doux)]">—</span>
                          )}
                        </td>
                      ))}
                      <td className="px-3 py-1.5">
                        {ligne.anomalies.length === 0 ? (
                          <span className="text-green-700">OK</span>
                        ) : (
                          <ul className="space-y-0.5">
                            {ligne.anomalies.map((anomalie, index) => (
                              <li
                                key={index}
                                className={
                                  anomalie.bloquante
                                    ? "text-red-700"
                                    : "text-amber-700"
                                }
                              >
                                {anomalie.bloquante ? "Rejet" : "Avertissement"} :{" "}
                                {anomalie.message}
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {apercu.colonnesDetectees.length > 0 && (
            <p className="text-[11px] text-[var(--texte-tres-doux)]">
              Colonnes détectées : {apercu.colonnesDetectees.join(", ")}
            </p>
          )}
        </div>
      )}
    </Modal>
  );
}

function Compteur({
  libelle,
  valeur,
  ton,
}: {
  libelle: string;
  valeur: number;
  ton?: "succes" | "alerte";
}) {
  return (
    <div className="rounded-lg border border-[var(--bordure)] p-3">
      <p className="text-[11px] text-[var(--texte-tres-doux)]">{libelle}</p>
      <p
        className={cx(
          "chiffres mt-0.5 text-xl font-semibold",
          ton === "succes" && "text-green-700",
          ton === "alerte" && "text-red-700",
        )}
      >
        {valeur.toLocaleString("fr-FR")}
      </p>
    </div>
  );
}
