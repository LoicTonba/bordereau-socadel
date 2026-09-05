/**
 * Barre de filtres du bordereau.
 *
 * Le filtre construit ici est le même objet qui part vers le listing, les
 * exports et la vérification : ce que le superviseur voit est exactement ce
 * qu'il exporte.
 */

"use client";

import { useEffect, useState } from "react";

import { STATUTS, STATUTS_SAISISSABLES, VERDICTS } from "@core/domain/statuts";
import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import type {
  FiltreBordereau,
  StatutCollecte,
  VerdictVerification,
} from "@core/domain/types";
import { Bouton, cx } from "@shared/ui/primitives";

export function BarreFiltres({
  filtre,
  onChanger,
  /** Vue de terrain : le contrôle en base ne le concerne pas. */
  restreinte = false,
}: {
  filtre: FiltreBordereau;
  onChanger: (filtre: FiltreBordereau) => void;
  restreinte?: boolean;
}) {
  const t = useT();
  const [recherche, setRecherche] = useState(filtre.recherche ?? "");

  // La recherche est différée : sans cela, chaque frappe déclencherait une
  // requête sur une table de plusieurs centaines de milliers de lignes.
  useEffect(() => {
    const minuteur = setTimeout(() => {
      if ((filtre.recherche ?? "") !== recherche) {
        onChanger({ ...filtre, recherche: recherche || undefined });
      }
    }, 350);
    return () => clearTimeout(minuteur);
  }, [recherche, filtre, onChanger]);

  function basculerStatut(statut: StatutCollecte) {
    const actuels = filtre.statut ?? [];
    const suivants = actuels.includes(statut)
      ? actuels.filter((valeur) => valeur !== statut)
      : [...actuels, statut];
    onChanger({ ...filtre, statut: suivants.length ? suivants : undefined });
  }

  function basculerVerdict(verdict: VerdictVerification) {
    const actuels = filtre.verdict ?? [];
    const suivants = actuels.includes(verdict)
      ? actuels.filter((valeur) => valeur !== verdict)
      : [...actuels, verdict];
    onChanger({ ...filtre, verdict: suivants.length ? suivants : undefined });
  }

  const aDesFiltres =
    Boolean(filtre.recherche) ||
    Boolean(filtre.statut?.length) ||
    Boolean(filtre.verdict?.length) ||
    Boolean(filtre.debut) ||
    Boolean(filtre.fin);

  return (
    <div className="space-y-3 border-b border-[var(--bordure)] px-4 py-3.5">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-56 flex-1">
          <label
            htmlFor="recherche"
            className="mb-1.5 block text-xs font-medium text-[var(--texte-doux)]"
          >
            {t("commun.rechercher")}
          </label>
          <input
            id="recherche"
            type="search"
            className="champ"
            placeholder={t("bordereau.rechercheePlaceholder")}
            value={recherche}
            onChange={(evenement) => setRecherche(evenement.target.value)}
          />
        </div>

        <div>
          <label
            htmlFor="debut"
            className="mb-1.5 block text-xs font-medium text-[var(--texte-doux)]"
          >
            {t("commun.du")}
          </label>
          <input
            id="debut"
            type="date"
            className="champ !w-auto"
            value={filtre.debut ?? ""}
            onChange={(evenement) =>
              onChanger({ ...filtre, debut: evenement.target.value || undefined })
            }
          />
        </div>

        <div>
          <label
            htmlFor="fin"
            className="mb-1.5 block text-xs font-medium text-[var(--texte-doux)]"
          >
            {t("commun.au")}
          </label>
          <input
            id="fin"
            type="date"
            className="champ !w-auto"
            value={filtre.fin ?? ""}
            onChange={(evenement) =>
              onChanger({ ...filtre, fin: evenement.target.value || undefined })
            }
          />
        </div>

        {aDesFiltres && (
          <Bouton
            variante="discret"
            taille="sm"
            onClick={() => {
              setRecherche("");
              onChanger({});
            }}
          >
            {t("commun.reinitialiser")}
          </Bouton>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <GroupePuces
          legende={t("bordereau.statut")}
          options={STATUTS_SAISISSABLES.map((valeur) => ({
            valeur,
            libelle: t(`statut.${valeur}` as Cle),
            couleur: STATUTS[valeur].texte,
          }))}
          selection={filtre.statut ?? []}
          onBasculer={(valeur) => basculerStatut(valeur as StatutCollecte)}
        />

        {/* Le verdict du back-office ne dit rien à l'agent : il ne le pose
            pas, ne le corrige pas, et ne peut rien en faire sur le terrain. */}
        {!restreinte && (
          <GroupePuces
            legende={t("bordereau.backOffice")}
            options={(Object.keys(VERDICTS) as VerdictVerification[]).map(
              (valeur) => ({
                valeur,
                libelle: t(`verdict.${valeur}` as Cle),
                couleur: VERDICTS[valeur].texte,
              }),
            )}
            selection={filtre.verdict ?? []}
            onBasculer={(valeur) => basculerVerdict(valeur as VerdictVerification)}
          />
        )}
      </div>
    </div>
  );
}

function GroupePuces({
  legende,
  options,
  selection,
  onBasculer,
}: {
  legende: string;
  options: { valeur: string; libelle: string; couleur: string }[];
  selection: string[];
  onBasculer: (valeur: string) => void;
}) {
  return (
    <fieldset className="flex flex-wrap items-center gap-1.5">
      <legend className="sr-only">{legende}</legend>
      <span className="mr-1 text-xs font-medium text-[var(--texte-tres-doux)]">
        {legende}
      </span>
      {options.map((option) => {
        const actif = selection.includes(option.valeur);
        return (
          <button
            key={option.valeur}
            type="button"
            aria-pressed={actif}
            onClick={() => onBasculer(option.valeur)}
            className={cx(
              "rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors",
              actif
                ? "border-transparent text-white"
                : "border-[var(--bordure-forte)] text-[var(--texte-doux)] hover:bg-[var(--fond-survol)]",
            )}
            style={actif ? { backgroundColor: option.couleur } : undefined}
          >
            {option.libelle}
          </button>
        );
      })}
    </fieldset>
  );
}
