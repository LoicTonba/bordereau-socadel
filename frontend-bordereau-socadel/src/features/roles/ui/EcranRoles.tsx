/**
 * Rôles et permissions : la matrice, et ce que le super utilisateur retranche.
 *
 * L'écran ne permet pas de créer un rôle ni d'ajouter une permission, et il le
 * dit. Les quatre rôles et leur matrice sont écrits dans le code, où ils sont
 * relus, testés et versionnés. Ce qu'on peut faire ici, c'est **retrancher** :
 * fermer un droit à un rôle, par exemple l'export à tous les superviseurs le
 * temps d'une campagne.
 *
 * La distinction est portée à l'écran plutôt que dans une note de bas de page :
 * chaque ligne montre ce que le code accorde et ce qui a été retranché, ce qui
 * rend un refus compréhensible sans aller lire le code source.
 */

"use client";

import { useMemo, useState } from "react";

import { useSession } from "@features/auth/application/SessionProvider";
import { ErreurApi } from "@infra/http/client";
import { useToasts } from "@shared/ui/Toasts";
import { Alerte, Badge, Bouton, Carte, EtatVide, cx } from "@shared/ui/primitives";

import { useRestreindreRole, useRoles } from "../application/hooks";
import type { Droit, VueRole } from "../infrastructure/roles-api";

/** Libellés lisibles des quatre rôles. */
const NOMS: Record<string, string> = {
  SUPER_UTILISATEUR: "Super utilisateur",
  ADMINISTRATEUR: "Administrateur",
  SUPERVISEUR: "Superviseur",
  AGENT_TERRAIN: "Agent de terrain",
};

const MAISONS: Record<string, string> = {
  SUPER_UTILISATEUR: "NEXT LTD",
  ADMINISTRATEUR: "SOCADEL",
  SUPERVISEUR: "SOCADEL, une agence",
  AGENT_TERRAIN: "SOCADEL, sur le terrain",
};

export function EcranRoles() {
  const { utilisateur } = useSession();
  const { notifier } = useToasts();
  const { data: roles, isFetching, error } = useRoles();
  const restreindre = useRestreindreRole();

  const [ouvert, setOuvert] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  const peutRestreindre = (utilisateur?.permissions ?? []).includes(
    "role:restreindre",
  );

  async function basculer(vue: VueRole, droit: Droit) {
    setErreur(null);
    const restrictions = vue.droits
      .filter((d) => (d.permission === droit.permission ? !d.restreinte : d.restreinte))
      .map((d) => d.permission);

    try {
      await restreindre.mutateAsync({ role: vue.role, restrictions });
      notifier(
        droit.restreinte ? "creation" : "suppression",
        droit.restreinte
          ? `« ${droit.permission} » est rendue au rôle ${NOMS[vue.role]}.`
          : `« ${droit.permission} » est retirée au rôle ${NOMS[vue.role]}.`,
      );
    } catch (exception) {
      const message =
        exception instanceof ErreurApi ? exception.message : "L'opération a échoué.";
      setErreur(message);
      notifier("echec", message);
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-lg font-semibold">Rôles et permissions</h1>
        <p className="text-sm text-[var(--texte-doux)]">
          Ce que chaque rôle porte, et ce qui lui a été retranché.
        </p>
      </header>

      {erreur && <Alerte>{erreur}</Alerte>}
      {error instanceof ErreurApi && <Alerte>{error.message}</Alerte>}

      <Alerte ton="info">
        <b>On retranche, on n&apos;ajoute jamais.</b> Les quatre rôles et leur
        matrice sont écrits dans le code, relus et testés. Retirer un droit ici
        le ferme aussitôt ; aucune écriture ne peut en ouvrir un que le code ne
        donne pas. C&apos;est ce qui rend l&apos;escalade de privilèges
        impossible par la donnée, y compris depuis une sauvegarde restaurée.
      </Alerte>

      {!roles || roles.length === 0 ? (
        <EtatVide
          titre={isFetching ? "Chargement…" : "Aucun rôle"}
          description="La matrice n'a pas pu être lue."
        />
      ) : (
        <div className="space-y-3">
          {roles.map((vue) => (
            <CarteRole
              key={vue.role}
              vue={vue}
              ouverte={ouvert === vue.role}
              peutRestreindre={
                peutRestreindre && vue.role !== "SUPER_UTILISATEUR"
              }
              enCours={restreindre.isPending}
              onBasculerOuverture={() =>
                setOuvert((actuel) => (actuel === vue.role ? null : vue.role))
              }
              onBasculerDroit={(droit) => basculer(vue, droit)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CarteRole({
  vue,
  ouverte,
  peutRestreindre,
  enCours,
  onBasculerOuverture,
  onBasculerDroit,
}: {
  vue: VueRole;
  ouverte: boolean;
  peutRestreindre: boolean;
  enCours: boolean;
  onBasculerOuverture: () => void;
  onBasculerDroit: (droit: Droit) => void;
}) {
  // Seuls les droits que le code accorde sont montrés : lister les autres
  // ferait croire qu'on pourrait les ouvrir.
  const accordes = useMemo(
    () => vue.droits.filter((d) => d.accordeeParLeCode),
    [vue.droits],
  );
  const retranches = accordes.filter((d) => d.restreinte).length;

  return (
    <Carte className="overflow-hidden">
      <button
        type="button"
        onClick={onBasculerOuverture}
        className="flex w-full items-center gap-3 px-5 py-4 text-left transition-colors hover:bg-[var(--fond-survol)]"
      >
        <span
          aria-hidden
          className="grid size-9 shrink-0 place-items-center rounded-lg bg-socadel-600 text-xs font-semibold text-white"
        >
          {vue.rang}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium">{NOMS[vue.role] ?? vue.role}</span>
          <span className="block text-xs text-[var(--texte-tres-doux)]">
            {MAISONS[vue.role] ?? ""} · rang {vue.rang}
          </span>
        </span>
        <Badge fond="#dcfce7" texte="#166534">
          {vue.nombreEffectif} droit(s)
        </Badge>
        {retranches > 0 && (
          <Badge fond="#fef3c7" texte="#92400e">
            {retranches} retranché(s)
          </Badge>
        )}
        <span aria-hidden className="text-[var(--texte-tres-doux)]">
          {ouverte ? "▲" : "▼"}
        </span>
      </button>

      {ouverte && (
        <ul className="divide-y divide-[var(--bordure)] border-t border-[var(--bordure)]">
          {accordes.map((droit) => (
            <li
              key={droit.permission}
              className="flex items-center gap-3 px-5 py-2.5"
            >
              <code
                className={cx(
                  "flex-1 text-xs",
                  droit.restreinte && "text-[var(--texte-tres-doux)] line-through",
                )}
              >
                {droit.permission}
              </code>

              {droit.restreinte ? (
                <Badge fond="#fef3c7" texte="#92400e">
                  Retranchée
                </Badge>
              ) : (
                <Badge fond="#dcfce7" texte="#166534">
                  Active
                </Badge>
              )}

              {peutRestreindre && (
                <Bouton
                  variante={droit.restreinte ? "secondaire" : "danger"}
                  taille="sm"
                  chargement={enCours}
                  onClick={() => onBasculerDroit(droit)}
                >
                  {droit.restreinte ? "Rendre" : "Retrancher"}
                </Bouton>
              )}
            </li>
          ))}
        </ul>
      )}
    </Carte>
  );
}
