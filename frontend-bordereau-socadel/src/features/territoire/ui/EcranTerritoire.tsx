/**
 * Maillage territorial : agences, divisions, directions régionales.
 *
 * Le réseau bouge. Une agence ouvre dans un lotissement neuf, une autre devient
 * inaccessible et cesse d'accueillir des tournées. Cet écran permet de suivre
 * ces mouvements le jour même, sans attendre un nouvel import du référentiel.
 *
 * Deux choses y sont rendues visibles plutôt qu'expliquées ailleurs. Le nom
 * d'une agence n'est pas modifiable : comptes, itinéraires et référentiel le
 * portent tel quel. Et une agence se **ferme** avant de se supprimer : fermée,
 * elle quitte les listes de travail et le sélecteur de connexion, mais reste
 * attachée à la production passée.
 */

"use client";

import { useMemo, useState } from "react";

import { ErreurApi } from "@infra/http/client";
import { Modal } from "@shared/ui/Modal";
import { useToasts } from "@shared/ui/Toasts";
import {
  Alerte,
  Badge,
  Bouton,
  Carte,
  Champ,
  EtatVide,
  Selecteur,
  cx,
} from "@shared/ui/primitives";

import {
  useCreerAgence,
  useFermerAgence,
  useImporterTerritoire,
  useModifierAgence,
  useRouvrirAgence,
  useSupprimerAgence,
  useTerritoire,
} from "../application/hooks";
import type { Agence } from "../infrastructure/territoire-api";

type Filtre = "OUVERTES" | "FERMEES" | "TOUTES";

const FILTRES: readonly { cle: Filtre; libelle: string }[] = [
  { cle: "OUVERTES", libelle: "Agences ouvertes" },
  { cle: "FERMEES", libelle: "Agences fermées" },
  { cle: "TOUTES", libelle: "Toutes" },
];

export function EcranTerritoire() {
  const { notifier } = useToasts();
  const { data, isFetching, error } = useTerritoire();

  const creer = useCreerAgence();
  const modifier = useModifierAgence();
  const fermer = useFermerAgence();
  const rouvrir = useRouvrirAgence();
  const supprimer = useSupprimerAgence();
  const importer = useImporterTerritoire();

  const [filtre, setFiltre] = useState<Filtre>("OUVERTES");
  const [recherche, setRecherche] = useState("");
  const [region, setRegion] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);

  const [formulaireOuvert, setFormulaireOuvert] = useState(false);
  const [enEdition, setEnEdition] = useState<Agence | null>(null);
  const [brouillon, setBrouillon] = useState({ nom: "", region: "", division: "" });

  const [aFermer, setAFermer] = useState<Agence | null>(null);
  const [motif, setMotif] = useState("");

  const agences = useMemo(() => {
    const terme = recherche.trim().toUpperCase();
    return (data?.agences ?? []).filter((agence) => {
      if (filtre === "OUVERTES" && !agence.ouverte) return false;
      if (filtre === "FERMEES" && agence.ouverte) return false;
      if (region && agence.region !== region) return false;
      if (!terme) return true;
      return (
        agence.nom.includes(terme) ||
        (agence.division ?? "").includes(terme) ||
        (agence.region ?? "").includes(terme)
      );
    });
  }, [data, filtre, recherche, region]);

  function echouer(exception: unknown, repli: string) {
    const message = exception instanceof ErreurApi ? exception.message : repli;
    setErreur(message);
    notifier("echec", message);
  }

  function ouvrirCreation() {
    setBrouillon({ nom: "", region: "", division: "" });
    setEnEdition(null);
    setErreur(null);
    setFormulaireOuvert(true);
  }

  function ouvrirEdition(agence: Agence) {
    setBrouillon({
      nom: agence.nom,
      region: agence.region ?? "",
      division: agence.division ?? "",
    });
    setEnEdition(agence);
    setErreur(null);
    setFormulaireOuvert(true);
  }

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);
    const donnees = {
      nom: brouillon.nom.trim(),
      region: brouillon.region.trim() || null,
      division: brouillon.division.trim() || null,
    };

    try {
      if (enEdition) {
        await modifier.mutateAsync(donnees);
        notifier("modification", `${donnees.nom} est à jour.`);
      } else {
        await creer.mutateAsync(donnees);
        notifier("creation", `${donnees.nom.toUpperCase()} est ouverte.`);
      }
      setFormulaireOuvert(false);
    } catch (exception) {
      echouer(exception, "L'enregistrement a échoué.");
    }
  }

  async function confirmerFermeture(evenement: React.FormEvent) {
    evenement.preventDefault();
    if (!aFermer) return;
    setErreur(null);
    try {
      await fermer.mutateAsync({ nom: aFermer.nom, motif });
      notifier("suppression", `${aFermer.nom} est fermée.`);
      setAFermer(null);
      setMotif("");
    } catch (exception) {
      echouer(exception, "La fermeture a échoué.");
    }
  }

  async function agir(promesse: Promise<unknown>, message: string, ton: "creation" | "suppression") {
    setErreur(null);
    try {
      await promesse;
      notifier(ton, message);
    } catch (exception) {
      echouer(exception, "L'opération a échoué.");
    }
  }

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">Maillage territorial</h1>
          <p className="text-sm text-[var(--texte-doux)]">
            Les agences de SOCADEL, leurs divisions et leurs directions
            régionales.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Bouton
            variante="secondaire"
            chargement={importer.isPending}
            onClick={() =>
              agir(
                importer
                  .mutateAsync()
                  .then((r) => notifier("info" as never, r.message)),
                "Maillage repris du référentiel.",
                "creation",
              )
            }
          >
            Reprendre du référentiel
          </Bouton>
          <Bouton onClick={ouvrirCreation}>Ouvrir une agence</Bouton>
        </div>
      </header>

      {erreur && <Alerte>{erreur}</Alerte>}
      {error instanceof ErreurApi && <Alerte>{error.message}</Alerte>}

      {data && (
        <div className="grid gap-3 sm:grid-cols-3">
          <Compteur libelle="Agences" valeur={data.agences.length} teinte="bg-socadel-600" />
          <Compteur libelle="Divisions" valeur={data.divisions.length} teinte="bg-violet-600" />
          <Compteur
            libelle="Directions régionales"
            valeur={data.regions.length}
            teinte="bg-orange-500"
          />
        </div>
      )}

      <Carte className="overflow-hidden">
        <div className="flex flex-wrap items-end gap-3 border-b border-[var(--bordure)] p-4">
          <div className="min-w-56 flex-1">
            <label
              htmlFor="recherche-agence"
              className="mb-1.5 block text-xs font-medium text-[var(--texte-doux)]"
            >
              Rechercher
            </label>
            <input
              id="recherche-agence"
              type="search"
              className="champ"
              placeholder="Nom d'agence, division ou direction"
              value={recherche}
              onChange={(evenement) => setRecherche(evenement.target.value)}
            />
          </div>
          <Selecteur
            libelle="Direction régionale"
            value={region}
            onChange={(evenement) => setRegion(evenement.target.value)}
            className="!w-auto"
          >
            <option value="">Toutes</option>
            {(data?.regions ?? []).map((valeur) => (
              <option key={valeur} value={valeur}>
                {valeur}
              </option>
            ))}
          </Selecteur>
          <Selecteur
            libelle="État"
            value={filtre}
            onChange={(evenement) => setFiltre(evenement.target.value as Filtre)}
            className="!w-auto"
          >
            {FILTRES.map((option) => (
              <option key={option.cle} value={option.cle}>
                {option.libelle}
              </option>
            ))}
          </Selecteur>
        </div>

        {agences.length === 0 ? (
          <EtatVide
            titre={isFetching ? "Chargement…" : "Aucune agence"}
            description="Modifiez le filtre, ou reprenez le maillage depuis le référentiel clients."
          />
        ) : (
          <ul className="divide-y divide-[var(--bordure)]">
            {agences.map((agence) => (
              <li
                key={agence.nom}
                className="flex flex-wrap items-center gap-3 px-5 py-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="flex items-center gap-2 text-sm font-medium">
                    {agence.nom}
                    {!agence.ouverte && (
                      <Badge fond="#fee2e2" texte="#991b1b">
                        Fermée
                      </Badge>
                    )}
                  </p>
                  <p className="truncate text-xs text-[var(--texte-tres-doux)]">
                    {agence.territoire}
                    {agence.motifFermeture && ` · ${agence.motifFermeture}`}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Bouton
                    variante="secondaire"
                    taille="sm"
                    onClick={() => ouvrirEdition(agence)}
                  >
                    Modifier
                  </Bouton>
                  {agence.ouverte ? (
                    <Bouton
                      variante="secondaire"
                      taille="sm"
                      onClick={() => {
                        setAFermer(agence);
                        setMotif("");
                      }}
                    >
                      Fermer
                    </Bouton>
                  ) : (
                    <>
                      <Bouton
                        taille="sm"
                        chargement={rouvrir.isPending}
                        onClick={() =>
                          agir(
                            rouvrir.mutateAsync(agence.nom),
                            `${agence.nom} est rouverte.`,
                            "creation",
                          )
                        }
                      >
                        Rouvrir
                      </Bouton>
                      <Bouton
                        variante="danger"
                        taille="sm"
                        chargement={supprimer.isPending}
                        onClick={() =>
                          agir(
                            supprimer.mutateAsync(agence.nom),
                            `${agence.nom} est supprimée.`,
                            "suppression",
                          )
                        }
                      >
                        Supprimer
                      </Bouton>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Carte>

      <Modal
        ouvert={formulaireOuvert}
        onFermer={() => setFormulaireOuvert(false)}
        titre={enEdition ? enEdition.nom : "Ouvrir une agence"}
        description={
          enEdition
            ? "Le nom n'est pas modifiable : les comptes, les itinéraires et le référentiel le portent."
            : "Le nom sera mis en majuscules : c'est la clé que porteront les comptes et les tournées."
        }
        pied={
          <>
            <Bouton variante="secondaire" onClick={() => setFormulaireOuvert(false)}>
              Annuler
            </Bouton>
            <Bouton
              type="submit"
              form="formulaire-agence"
              chargement={creer.isPending || modifier.isPending}
              disabled={!brouillon.nom.trim()}
            >
              Enregistrer
            </Bouton>
          </>
        }
      >
        <form
          id="formulaire-agence"
          onSubmit={soumettre}
          className="grid gap-4 sm:grid-cols-2"
          noValidate
        >
          <Champ
            name="nom"
            libelle="Nom de l'agence"
            placeholder="CSC_NGAOUNDERE SUD"
            required
            disabled={Boolean(enEdition)}
            value={brouillon.nom}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, nom: evenement.target.value })
            }
            aide={enEdition ? "Non modifiable." : undefined}
          />
          <Champ
            name="division"
            libelle="Division"
            placeholder="DPC NGAOUNDERE"
            value={brouillon.division}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, division: evenement.target.value })
            }
          />
          <Champ
            name="region"
            libelle="Direction régionale"
            placeholder="DRNEA"
            value={brouillon.region}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, region: evenement.target.value })
            }
          />
        </form>
      </Modal>

      <Modal
        ouvert={Boolean(aFermer)}
        onFermer={() => setAFermer(null)}
        titre={aFermer ? `Fermer ${aFermer.nom}` : "Fermer une agence"}
        description="L'agence quitte les listes de travail et le sélecteur de connexion. Sa production passée reste."
        pied={
          <>
            <Bouton variante="secondaire" onClick={() => setAFermer(null)}>
              Annuler
            </Bouton>
            <Bouton
              type="submit"
              form="formulaire-fermeture"
              variante="danger"
              chargement={fermer.isPending}
              disabled={motif.trim().length < 3}
            >
              Fermer l&apos;agence
            </Bouton>
          </>
        }
      >
        <form id="formulaire-fermeture" onSubmit={confirmerFermeture} noValidate>
          <Champ
            name="motif"
            libelle="Motif de la fermeture"
            placeholder="Zone rendue inaccessible"
            required
            value={motif}
            onChange={(evenement) => setMotif(evenement.target.value)}
            aide="Il est conservé : sans lui, personne ne saura s'il faut rouvrir."
          />
        </form>
      </Modal>
    </div>
  );
}

function Compteur({
  libelle,
  valeur,
  teinte,
}: {
  libelle: string;
  valeur: number;
  teinte: string;
}) {
  return (
    <div className="carte overflow-hidden text-center">
      <div aria-hidden className={cx("h-1 w-full", teinte)} />
      <div className="px-4 py-3">
        <p className="text-xs font-medium text-[var(--texte-doux)]">{libelle}</p>
        <p className="chiffres mt-1 text-2xl font-semibold">
          {valeur.toLocaleString("fr-FR")}
        </p>
      </div>
    </div>
  );
}
