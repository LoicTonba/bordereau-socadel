/**
 * Journal d'audit : qui a fait quoi, quand, et avec quelle issue.
 *
 * Réservé à l'administrateur SOCADEL et au super utilisateur NEXT LTD. La
 * plateforme décide de ce qui sera payé : sans réponse à « qui a affecté cette
 * tournée » ou « qui a fermé cette agence », elle n'est pas défendable devant
 * un contrôle.
 *
 * Le journal ne porte **aucun contenu transmis** : ni mot de passe, ni numéro
 * de téléphone, ni nom de client. Le geste et sa cible suffisent, et les
 * recopier créerait une seconde base de données personnelles, moins protégée
 * que la première.
 */

"use client";

import { useState } from "react";

import { ErreurApi } from "@infra/http/client";
import { Pagination } from "@shared/ui/Pagination";
import {
  Alerte,
  Badge,
  Bouton,
  Carte,
  Champ,
  EtatVide,
  cx,
} from "@shared/ui/primitives";

import { useJournal } from "../application/hooks";
import type { FiltreAudit } from "../infrastructure/audit-api";

const VIDE: FiltreAudit = { page: 1, taille: 25 };

export function EcranAudit() {
  const [filtre, setFiltre] = useState<FiltreAudit>(VIDE);
  const { data, isFetching, error } = useJournal(filtre);

  function poser(champs: Partial<FiltreAudit>) {
    // Changer de critère remet la pagination à zéro : rester en page 7 d'un
    // résultat qui n'en compte plus que 2 afficherait un journal vide.
    setFiltre((actuel) => ({ ...actuel, ...champs, page: 1 }));
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-lg font-semibold">Audit et journal</h1>
        <p className="text-sm text-[var(--texte-doux)]">
          Qui a fait quoi sur la plateforme, du plus récent au plus ancien.
        </p>
      </header>

      {error instanceof ErreurApi && <Alerte>{error.message}</Alerte>}

      <Carte className="overflow-hidden">
        <div className="flex flex-wrap items-end gap-3 border-b border-[var(--bordure)] p-4">
          <Champ
            name="auteur"
            libelle="Auteur"
            placeholder="admin, superviseur…"
            className="min-w-48"
            value={filtre.identifiant ?? ""}
            onChange={(evenement) =>
              poser({ identifiant: evenement.target.value || undefined })
            }
          />
          <Champ
            name="action"
            libelle="Action"
            placeholder="territoire, connexion, affectation…"
            className="min-w-52"
            value={filtre.action ?? ""}
            onChange={(evenement) =>
              poser({ action: evenement.target.value || undefined })
            }
          />
          <Champ
            name="depuis"
            type="date"
            libelle="Du"
            value={filtre.depuis ?? ""}
            onChange={(evenement) =>
              poser({ depuis: evenement.target.value || undefined })
            }
          />
          <Champ
            name="jusquA"
            type="date"
            libelle="Au"
            value={filtre.jusquA ?? ""}
            onChange={(evenement) =>
              poser({ jusquA: evenement.target.value || undefined })
            }
          />

          <Bouton
            variante={filtre.echecsSeulement ? "primaire" : "secondaire"}
            taille="sm"
            onClick={() => poser({ echecsSeulement: !filtre.echecsSeulement })}
          >
            Échecs seulement
          </Bouton>
          <Bouton variante="discret" taille="sm" onClick={() => setFiltre(VIDE)}>
            Réinitialiser
          </Bouton>
        </div>

        {!data || data.elements.length === 0 ? (
          <EtatVide
            titre={isFetching ? "Chargement…" : "Aucune trace"}
            description="Aucun geste ne correspond à ces critères sur la période."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-[var(--bordure)] text-left text-xs text-[var(--texte-doux)]">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Quand</th>
                  <th className="px-4 py-2.5 font-medium">Auteur</th>
                  <th className="px-4 py-2.5 font-medium">Action</th>
                  <th className="px-4 py-2.5 font-medium">Cible</th>
                  <th className="px-4 py-2.5 font-medium">Issue</th>
                  <th className="px-4 py-2.5 font-medium">Origine</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--bordure)]">
                {data.elements.map((trace, rang) => (
                  <tr key={`${trace.quand}-${rang}`}>
                    <td className="chiffres px-4 py-2.5 whitespace-nowrap text-xs text-[var(--texte-doux)]">
                      {formaterInstant(trace.quand)}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="block truncate font-medium">
                        {trace.auteur}
                      </span>
                      {trace.role && (
                        <span className="block text-xs text-[var(--texte-tres-doux)]">
                          {trace.role.toLowerCase().replace(/_/g, " ")}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <code className="text-xs">{trace.action}</code>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-[var(--texte-doux)]">
                      {trace.cible ?? "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <Badge
                        fond={trace.reussi ? "#dcfce7" : "#fee2e2"}
                        texte={trace.reussi ? "#166534" : "#991b1b"}
                        titre={`Code HTTP ${trace.statutHttp}`}
                      >
                        {trace.reussi ? "Réussi" : `Refusé ${trace.statutHttp}`}
                      </Badge>
                    </td>
                    <td className="chiffres px-4 py-2.5 text-xs text-[var(--texte-tres-doux)]">
                      {trace.adresseIp ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.elements.length > 0 && (
          <Pagination
            meta={data.meta}
            onPage={(page) => setFiltre((actuel) => ({ ...actuel, page }))}
            onTaille={(taille) =>
              setFiltre((actuel) => ({ ...actuel, taille, page: 1 }))
            }
          />
        )}
      </Carte>

      <p
        className={cx(
          "rounded-lg border border-[var(--bordure)] bg-[var(--fond-survol)]",
          "px-4 py-3 text-xs leading-relaxed text-[var(--texte-doux)]",
        )}
      >
        Le journal retient l&apos;auteur, l&apos;instant, le geste et son issue.
        Il ne retient <b>jamais</b> le contenu transmis : ni mot de passe, ni
        numéro de téléphone, ni nom de client. Il enregistre les écritures et
        les tentatives de connexion, pas les consultations.
      </p>
    </div>
  );
}

/** Date et heure locales, sans la seconde de trop. */
function formaterInstant(iso: string): string {
  const instant = new Date(iso);
  if (Number.isNaN(instant.getTime())) return iso;
  return instant.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
