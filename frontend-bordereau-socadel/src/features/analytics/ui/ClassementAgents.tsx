/**
 * Classement des agents.
 *
 * Un tableau, pas un graphique : le superviseur y lit des chiffres exacts pour
 * son point quotidien avec chaque agent, pas une silhouette.
 *
 * La colonne « fiabilité » est la plus importante — c'est la part des
 * abonnements déclarés que le référentiel confirme. Un fort volume assorti
 * d'une fiabilité basse signale des déclarations qui ne se matérialisent pas.
 */

"use client";

import type { LigneClassementAgent } from "@core/domain/types";
import { Carte, cx, EtatVide } from "@shared/ui/primitives";

export function ClassementAgents({ agents }: { agents: LigneClassementAgent[] }) {
  return (
    <Carte
      titre="Performance des agents"
      description="Base de l'entretien de suivi : volume, conversion et fiabilité."
    >
      {agents.length === 0 ? (
        <EtatVide
          titre="Aucune production sur la période"
          description="Les chiffres apparaîtront dès la première saisie de bordereau."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-[var(--bordure)] bg-[var(--fond-survol)] text-left text-xs text-[var(--texte-doux)]">
                <th scope="col" className="px-5 py-2.5 font-semibold">
                  Agent
                </th>
                <th scope="col" className="px-3 py-2.5 text-right font-semibold">
                  Démarchés
                </th>
                <th scope="col" className="px-3 py-2.5 text-right font-semibold">
                  Abonnements
                </th>
                <th scope="col" className="px-3 py-2.5 text-right font-semibold">
                  Confirmés
                </th>
                <th scope="col" className="px-3 py-2.5 text-right font-semibold">
                  Conversion
                </th>
                <th scope="col" className="px-5 py-2.5 text-right font-semibold">
                  Fiabilité
                </th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.agentId} className="border-b border-[var(--bordure)]">
                  <td className="px-5 py-2.5">
                    <p className="font-medium">{agent.nomComplet}</p>
                    <p className="chiffres text-[11px] text-[var(--texte-tres-doux)]">
                      {agent.matricule}
                    </p>
                  </td>
                  <td className="chiffres px-3 py-2.5 text-right">
                    {agent.lignesTraitees.toLocaleString("fr-FR")}
                  </td>
                  <td className="chiffres px-3 py-2.5 text-right">
                    {agent.abonnementsDeclares.toLocaleString("fr-FR")}
                  </td>
                  <td className="chiffres px-3 py-2.5 text-right">
                    {agent.abonnementsConfirmes.toLocaleString("fr-FR")}
                  </td>
                  <td className="chiffres px-3 py-2.5 text-right">
                    {(agent.tauxConversion * 100).toFixed(1)} %
                  </td>
                  <td className="px-5 py-2.5 text-right">
                    <Fiabilite taux={agent.tauxFiabilite} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Carte>
  );
}

function Fiabilite({ taux }: { taux: number }) {
  const pourcentage = taux * 100;
  // Trois paliers de lecture ; le nombre reste affiché, la couleur n'est qu'un
  // repère secondaire.
  const niveau =
    pourcentage >= 85 ? "bon" : pourcentage >= 60 ? "moyen" : "faible";

  return (
    <span
      className={cx(
        "chiffres text-sm font-medium",
        niveau === "bon" && "text-green-700",
        niveau === "moyen" && "text-amber-700",
        niveau === "faible" && "text-red-700",
      )}
      title={
        niveau === "faible"
          ? "Une part importante des abonnements déclarés n'est pas confirmée par le référentiel."
          : undefined
      }
    >
      {pourcentage.toFixed(1)} %
    </span>
  );
}
