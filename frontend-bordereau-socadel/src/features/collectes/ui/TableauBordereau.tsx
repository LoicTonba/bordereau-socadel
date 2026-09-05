/**
 * Le bordereau, tel qu'il se lit en production.
 *
 * Les colonnes reprennent celles du document que SOCADEL remplit déjà :
 * Check, Check Date, Rapport, Back office, Date abonnement, Statut, Identité,
 * Responsable. Retrouver ses repères compte plus qu'un joli tableau — un
 * superviseur qui ne reconnaît pas ses colonnes retourne à Excel.
 *
 * **Deux vues, pas deux tableaux.** L'agent de terrain n'a que six colonnes :
 * le client, où il habite, son numéro, et le bouton qu'il doit cliquer.
 * Le reste — le contrôle en base, les dates automatiques, le responsable — ne
 * lui apprend rien qu'il puisse changer, et l'encombrerait sur un téléphone.
 * Superviseur, administrateur et super utilisateur voient tout.
 *
 * **Chaque colonne se cherche pour elle-même.** La recherche globale répond à
 * « où est ce client » ; la ligne de recherche répond à « montre-moi cette
 * tournée-là ». Le filtre part au serveur : le tableau n'en tient que dix
 * lignes, filtrer dans le navigateur ne trouverait rien au-delà.
 */

"use client";

import { useMemo, useState } from "react";

import { useT } from "@core/i18n/PreferencesProvider";
import { STATUTS, TEINTES_RAPPORT, VERDICTS } from "@core/domain/statuts";
import type { Cle } from "@core/i18n/messages";
import type {
  FiltreBordereau,
  LigneBordereau,
  Role,
} from "@core/domain/types";
import { Badge, cx, EtatVide } from "@shared/ui/primitives";

/** Clé de `FiltreBordereau` cherchable en texte libre depuis l'en-tête. */
type CleRecherche =
  | "serviceNo"
  | "nomClient"
  | "refGeo"
  | "numeroCompteur"
  | "numeroCollecte"
  | "responsableNom";

interface Colonne {
  cle: string;
  libelle: Cle;
  /** Clé de tri côté serveur ; absente si la colonne n'est pas triable. */
  tri?: string;
  /** Colonne de `FiltreBordereau` interrogée par la case de recherche. */
  recherche?: CleRecherche;
  aligneADroite?: boolean;
  centree?: boolean;
  /** Visible dans la vue de terrain. Les autres sont réservées au bureau. */
  terrain?: boolean;
}

const COLONNES: Colonne[] = [
  {
    cle: "check",
    libelle: "bordereau.check",
    centree: true,
    terrain: true,
  },
  { cle: "checkDate", libelle: "bordereau.checkDate" },
  {
    cle: "client",
    libelle: "bordereau.client",
    tri: "nom_client",
    recherche: "nomClient",
    terrain: true,
  },
  {
    cle: "refGeo",
    libelle: "bordereau.refGeo",
    tri: "ref_geo",
    recherche: "refGeo",
    terrain: true,
  },
  {
    cle: "itineraire",
    libelle: "bordereau.itineraire",
    tri: "code_itineraire",
    aligneADroite: true,
    terrain: true,
  },
  {
    cle: "compteur",
    libelle: "bordereau.compteur",
    recherche: "numeroCompteur",
    terrain: true,
  },
  {
    cle: "numero",
    libelle: "bordereau.numeroCollecte",
    recherche: "numeroCollecte",
    terrain: true,
  },
  { cle: "rapport", libelle: "bordereau.rapport", centree: true },
  { cle: "backOffice", libelle: "bordereau.backOffice", tri: "verdict" },
  { cle: "backOfficeDate", libelle: "bordereau.backOfficeDate" },
  { cle: "dateAbonnement", libelle: "bordereau.dateAbonnement" },
  { cle: "statut", libelle: "bordereau.statut", tri: "statut" },
  { cle: "identite", libelle: "bordereau.identite" },
  {
    cle: "responsable",
    libelle: "bordereau.responsable",
    recherche: "responsableNom",
  },
];

/** Le terrain n'a pas besoin du reste : il ne peut rien y changer. */
function colonnesDe(role: Role | undefined): Colonne[] {
  return role === "AGENT_TERRAIN"
    ? COLONNES.filter((colonne) => colonne.terrain)
    : COLONNES;
}

export function TableauBordereau({
  lignes,
  chargement,
  role,
  selection,
  onSelection,
  onEditer,
  onCocher,
  onDecocher,
  ligneEnCours,
  filtre,
  onFiltrer,
  tri,
  ordre,
  onTrier,
}: {
  lignes: LigneBordereau[];
  chargement: boolean;
  role: Role | undefined;
  selection: Set<string>;
  onSelection: (selection: Set<string>) => void;
  onEditer: (ligne: LigneBordereau) => void;
  onCocher: (ligne: LigneBordereau) => void;
  onDecocher: (ligne: LigneBordereau) => void;
  /** Ligne dont le coche est en cours d'enregistrement. */
  ligneEnCours: string | null;
  filtre: FiltreBordereau;
  onFiltrer: (filtre: FiltreBordereau) => void;
  tri?: string;
  ordre?: "asc" | "desc";
  onTrier: (tri: string) => void;
}) {
  const t = useT();
  const estAgent = role === "AGENT_TERRAIN";
  const colonnes = useMemo(() => colonnesDe(role), [role]);

  const toutesSelectionnees = useMemo(
    () => lignes.length > 0 && lignes.every((ligne) => selection.has(ligne.id)),
    [lignes, selection],
  );

  function basculerTout() {
    if (toutesSelectionnees) {
      // On ne vide que la page courante : une sélection faite sur une autre
      // page doit survivre à la navigation.
      const reste = new Set(selection);
      lignes.forEach((ligne) => reste.delete(ligne.id));
      onSelection(reste);
    } else {
      onSelection(new Set([...selection, ...lignes.map((ligne) => ligne.id)]));
    }
  }

  function basculerLigne(id: string) {
    const suivante = new Set(selection);
    if (suivante.has(id)) suivante.delete(id);
    else suivante.add(id);
    onSelection(suivante);
  }

  function chercher(cle: CleRecherche, valeur: string) {
    const suivant = { ...filtre };
    if (valeur.trim()) suivant[cle] = valeur;
    else delete suivant[cle];
    onFiltrer(suivant);
  }

  if (!chargement && lignes.length === 0) {
    return (
      <EtatVide
        titre={t("bordereau.vide")}
        description={t("bordereau.videAide")}
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table
        className={cx(
          "w-full border-separate border-spacing-0 text-sm",
          estAgent ? "min-w-[720px]" : "min-w-[1400px]",
        )}
      >
        {/* L'en-tête reste visible quand on descend dans les lignes : sans
            cela, à la dixième ligne on ne sait plus quelle colonne on lit. */}
        <thead className="sticky top-0 z-10">
          <tr className="bg-[var(--fond-survol)] text-left">
            {!estAgent && (
              <th
                scope="col"
                rowSpan={2}
                className="w-10 border-b border-[var(--bordure)] px-3 py-2.5"
              >
                <input
                  type="checkbox"
                  aria-label={t("bordereau.client")}
                  checked={toutesSelectionnees}
                  onChange={basculerTout}
                  className="size-4 accent-socadel-600"
                />
              </th>
            )}

            {colonnes.map((colonne) => (
              <th
                key={colonne.cle}
                scope="col"
                className={cx(
                  "whitespace-nowrap px-3 pb-1 pt-2.5 text-xs font-semibold uppercase tracking-wide text-[var(--texte-doux)]",
                  colonne.aligneADroite && "text-right",
                  colonne.centree && "text-center",
                )}
              >
                {colonne.tri ? (
                  <button
                    type="button"
                    onClick={() => onTrier(colonne.tri!)}
                    // La casse est répétée ici : la remise à zéro des styles
                    // de Tailwind coupe l'héritage de `text-transform` sur les
                    // boutons, et l'en-tête paraîtrait dépareillé.
                    className="inline-flex items-center gap-1 uppercase tracking-wide hover:text-[var(--texte)]"
                  >
                    {t(colonne.libelle)}
                    {tri === colonne.tri && (
                      <span aria-hidden>{ordre === "asc" ? "↑" : "↓"}</span>
                    )}
                  </button>
                ) : (
                  <span
                    title={
                      colonne.cle === "backOffice"
                        ? t("bordereau.backOfficeAide")
                        : undefined
                    }
                  >
                    {t(colonne.libelle)}
                  </span>
                )}
              </th>
            ))}

            {/* La saisie détaillée choisit un statut et un responsable :
                l'agent n'en a pas le droit, la colonne serait un cul-de-sac. */}
            {!estAgent && (
              <th
                scope="col"
                rowSpan={2}
                className="w-20 border-b border-[var(--bordure)] px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-[var(--texte-doux)]"
              >
                {t("bordereau.action")}
              </th>
            )}
          </tr>

          {/* La ligne de recherche : une case sous chaque colonne qui en
              accepte une, vide sous les autres pour garder l'alignement. */}
          <tr className="bg-[var(--fond-survol)]">
            {colonnes.map((colonne) => (
              <th
                key={colonne.cle}
                className="border-b border-[var(--bordure)] px-2 pb-2"
              >
                {colonne.recherche ? (
                  <input
                    type="search"
                    value={filtre[colonne.recherche] ?? ""}
                    onChange={(evenement) =>
                      chercher(colonne.recherche!, evenement.target.value)
                    }
                    placeholder={t(colonne.libelle)}
                    aria-label={`${t("bordereau.rechercheColonne")} — ${t(colonne.libelle)}`}
                    className="w-full min-w-[90px] rounded-md border border-[var(--bordure)] bg-[var(--fond)] px-2 py-1 text-xs font-normal placeholder:text-[var(--texte-tres-doux)] focus:border-socadel-500 focus:outline-none focus:ring-1 focus:ring-socadel-500"
                  />
                ) : (
                  <span className="block h-[26px]" aria-hidden />
                )}
              </th>
            ))}
          </tr>
        </thead>

        <tbody className={cx(chargement && "opacity-55")}>
          {lignes.map((ligne) => {
            const statut = STATUTS[ligne.statut];
            const verdict = VERDICTS[ligne.backOffice];
            const selectionnee = selection.has(ligne.id);
            const cellule =
              "border-b border-[var(--bordure)] px-3 py-2.5 align-middle";

            return (
              <tr
                key={ligne.id}
                className={cx(
                  "transition-colors",
                  selectionnee
                    ? "bg-socadel-50/70 dark:bg-socadel-950/40"
                    : "hover:bg-[var(--fond-survol)]",
                )}
              >
                {!estAgent && (
                  <td className={cellule}>
                    <input
                      type="checkbox"
                      aria-label={ligne.nomClient ?? ligne.serviceNo}
                      checked={selectionnee}
                      onChange={() => basculerLigne(ligne.id)}
                      className="size-4 accent-socadel-600"
                    />
                  </td>
                )}

                <td className={cx(cellule, "text-center")}>
                  <BoutonCheck
                    ligne={ligne}
                    occupee={ligneEnCours === ligne.id}
                    onCocher={() => onCocher(ligne)}
                    onDecocher={() => onDecocher(ligne)}
                  />
                </td>

                {!estAgent && (
                  <td className={cx(cellule, "chiffres text-xs text-[var(--texte-doux)]")}>
                    {formaterInstant(ligne.verifieTerrainLe)}
                  </td>
                )}

                <td className={cellule}>
                  <p className="font-medium">{ligne.nomClient ?? "—"}</p>
                  <p className="chiffres text-[11px] text-[var(--texte-tres-doux)]">
                    {ligne.serviceNo}
                  </p>
                </td>

                <td className={cx(cellule, "chiffres text-xs text-[var(--texte-doux)]")}>
                  {ligne.refGeo ?? "—"}
                </td>

                <td className={cx(cellule, "chiffres text-right text-xs")}>
                  {ligne.codeItineraire ?? "—"}
                </td>

                <td className={cx(cellule, "chiffres text-xs text-[var(--texte-doux)]")}>
                  {ligne.numeroCompteur ?? "—"}
                </td>

                <td className={cx(cellule, "chiffres text-xs")}>
                  {ligne.numeroCollecte ?? (
                    <span className="text-[var(--texte-tres-doux)]">—</span>
                  )}
                </td>

                {!estAgent && (
                  <>
                    <td className={cx(cellule, "text-center")}>
                      {ligne.rapport ? (
                        <Badge
                          fond={TEINTES_RAPPORT[ligne.rapport].fond}
                          texte={TEINTES_RAPPORT[ligne.rapport].texte}
                          titre={t(`rapport.${ligne.rapport}.aide` as Cle)}
                        >
                          {t(`rapport.${ligne.rapport}` as Cle)}
                        </Badge>
                      ) : (
                        <span className="text-[var(--texte-tres-doux)]">—</span>
                      )}
                    </td>

                    <td className={cellule}>
                      <Badge
                        fond={verdict.fond}
                        texte={verdict.texte}
                        titre={t(`verdict.${ligne.backOffice}.aide` as Cle)}
                      >
                        {t(`verdict.${ligne.backOffice}` as Cle)}
                      </Badge>
                    </td>

                    <td className={cx(cellule, "chiffres text-xs text-[var(--texte-doux)]")}>
                      {formaterInstant(ligne.backOfficeLe)}
                    </td>

                    <td className={cx(cellule, "chiffres text-xs text-[var(--texte-doux)]")}>
                      {formaterInstant(ligne.dateAbonnement)}
                    </td>

                    <td className={cellule}>
                      <Badge
                        fond={statut.fond}
                        texte={statut.texte}
                        titre={t(`statut.${ligne.statut}.aide` as Cle)}
                      >
                        {t(`statut.${ligne.statut}` as Cle)}
                      </Badge>
                    </td>

                    <td className={cx(cellule, "text-xs text-[var(--texte-doux)]")}>
                      {t(`identite.${ligne.identite}` as Cle)}
                    </td>

                    {/* Un nom quand quelqu'un a obtenu l'abonnement, « MRA »
                        quand c'est la relance, rien tant que personne. */}
                    <td className={cx(cellule, "text-xs")}>
                      {ligne.auteurAffiche ?? (
                        <span className="text-[var(--texte-tres-doux)]">—</span>
                      )}
                    </td>
                  </>
                )}

                {!estAgent && (
                  <td className={cx(cellule, "text-right")}>
                    <button
                      type="button"
                      onClick={() => onEditer(ligne)}
                      className="rounded-md px-2 py-1 text-xs font-medium text-socadel-700 hover:bg-socadel-50 dark:text-socadel-300 dark:hover:bg-socadel-950"
                    >
                      {t("bordereau.saisir")}
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Le seul geste de l'agent.
 *
 * Coché, le bouton devient une pastille verte qu'un second clic annule.
 * Décoché, c'est une case vide qui appelle le clic. La cible fait 32 px de
 * côté : elle se vise au pouce, debout, dans la rue.
 */
function BoutonCheck({
  ligne,
  occupee,
  onCocher,
  onDecocher,
}: {
  ligne: LigneBordereau;
  occupee: boolean;
  onCocher: () => void;
  onDecocher: () => void;
}) {
  const t = useT();
  const coche = ligne.verifieTerrain;

  return (
    <button
      type="button"
      disabled={occupee}
      onClick={coche ? onDecocher : onCocher}
      aria-pressed={coche}
      title={coche ? t("bordereau.decocher") : t("bordereau.checkAide")}
      className={cx(
        "inline-flex size-8 items-center justify-center rounded-md border text-sm font-bold transition-colors disabled:opacity-50",
        coche
          ? "border-emerald-500 bg-emerald-500 text-white hover:bg-emerald-600"
          : "border-[var(--bordure)] bg-[var(--fond)] text-transparent hover:border-socadel-400 hover:text-socadel-300",
      )}
    >
      <span aria-hidden>✓</span>
      <span className="sr-only">
        {coche ? t("bordereau.decocher") : t("bordereau.cocher")}
      </span>
    </button>
  );
}

function formaterInstant(iso: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "2-digit",
      });
}
