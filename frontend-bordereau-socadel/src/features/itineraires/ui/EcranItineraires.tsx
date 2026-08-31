/**
 * Répertoire des tournées : rechercher, imprimer, et tenir la liste à jour.
 *
 * Le terrain ouvre des zones plus vite qu'un import du référentiel ne se
 * rejoue. Le superviseur peut donc créer une tournée, en corriger le libellé
 * ou le rattachement, et retirer celle qui n'a jamais servi.
 *
 * Deux règles sont visibles à l'écran plutôt qu'expliquées après coup. Le code
 * ne se modifie pas : il est la clé que portent les affectations et la
 * production déjà saisie. Et une tournée déjà confiée ne se supprime plus, le
 * serveur le refuse en le disant.
 */

"use client";

import { useState } from "react";

import type { Itineraire } from "@core/domain/types";
import { useSession } from "@features/auth/application/SessionProvider";
import { ErreurApi } from "@infra/http/client";
import { Modal } from "@shared/ui/Modal";
import { useToasts } from "@shared/ui/Toasts";
import { Alerte, Bouton, Carte, Champ, EtatVide } from "@shared/ui/primitives";

import {
  useBordereauTerrain,
  useCreerItineraire,
  useModifierItineraire,
  useRechercheItineraires,
  useSupprimerItineraire,
} from "../application/hooks";

/** Champs modifiables d'une tournée. Le code n'en fait partie qu'à la création. */
interface Brouillon {
  code: string;
  libelle: string;
  region: string;
  division: string;
  agence: string;
}

const VIDE: Brouillon = {
  code: "",
  libelle: "",
  region: "",
  division: "",
  agence: "",
};

export function EcranItineraires() {
  const { utilisateur } = useSession();
  const { notifier } = useToasts();

  const [terme, setTerme] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [brouillon, setBrouillon] = useState<Brouillon>(VIDE);
  const [enEdition, setEnEdition] = useState<Itineraire | null>(null);
  const [formulaireOuvert, setFormulaireOuvert] = useState(false);

  const { data, isFetching } = useRechercheItineraires(terme);
  const bordereau = useBordereauTerrain();
  const creer = useCreerItineraire();
  const modifier = useModifierItineraire();
  const supprimer = useSupprimerItineraire();

  const peutGerer = (utilisateur?.permissions ?? []).includes("itineraire:gerer");

  function ouvrirCreation() {
    setBrouillon({ ...VIDE, agence: utilisateur?.agence ?? "" });
    setEnEdition(null);
    setErreur(null);
    setFormulaireOuvert(true);
  }

  function ouvrirEdition(itineraire: Itineraire) {
    setBrouillon({
      code: String(itineraire.code),
      libelle: itineraire.libelle ?? "",
      region: itineraire.region ?? "",
      division: itineraire.division ?? "",
      agence: itineraire.agence ?? "",
    });
    setEnEdition(itineraire);
    setErreur(null);
    setFormulaireOuvert(true);
  }

  function echouer(exception: unknown, repli: string) {
    const message = exception instanceof ErreurApi ? exception.message : repli;
    setErreur(message);
    notifier("echec", message);
  }

  async function imprimer(code: number) {
    setErreur(null);
    try {
      await bordereau.mutateAsync({ code });
    } catch (exception) {
      echouer(exception, "Le bordereau n'a pas pu être généré.");
    }
  }

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);

    const donnees = {
      code: Number(brouillon.code),
      libelle: brouillon.libelle.trim() || null,
      region: brouillon.region.trim() || null,
      division: brouillon.division.trim() || null,
      agence: brouillon.agence.trim() || null,
    };

    try {
      if (enEdition) {
        await modifier.mutateAsync(donnees);
        notifier("modification", `Itinéraire ${donnees.code} mis à jour.`);
      } else {
        await creer.mutateAsync(donnees);
        notifier("creation", `Itinéraire ${donnees.code} ouvert.`);
        // La recherche se cale sur la tournée qui vient d'être créée : sans
        // cela, elle disparaîtrait dans les seize mille autres.
        setTerme(String(donnees.code));
      }
      setFormulaireOuvert(false);
    } catch (exception) {
      echouer(exception, "L'enregistrement a échoué.");
    }
  }

  async function retirer(itineraire: Itineraire) {
    setErreur(null);
    try {
      await supprimer.mutateAsync(itineraire.code);
      notifier("suppression", `Itinéraire ${itineraire.code} retiré.`);
    } catch (exception) {
      echouer(exception, "La suppression a échoué.");
    }
  }

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">Itinéraires</h1>
          <p className="text-sm text-[var(--texte-doux)]">
            Retrouvez une tournée, imprimez son bordereau, tenez la liste à jour.
          </p>
        </div>
        {peutGerer && <Bouton onClick={ouvrirCreation}>Ouvrir une tournée</Bouton>}
      </header>

      {erreur && <Alerte>{erreur}</Alerte>}

      <Carte>
        <div className="border-b border-[var(--bordure)] p-4">
          <input
            type="search"
            className="champ"
            placeholder="Code de l'itinéraire, agence ou libellé, au moins 2 caractères"
            value={terme}
            onChange={(evenement) => setTerme(evenement.target.value)}
            aria-label="Rechercher un itinéraire"
          />
        </div>

        {terme.trim().length < 2 ? (
          <EtatVide
            titre="Recherchez un itinéraire"
            description="Saisissez son code, par exemple 131227, ou le nom de son agence."
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
                <div className="min-w-0">
                  <p className="chiffres text-sm font-medium">
                    Itinéraire {itineraire.code}
                    {itineraire.libelle && (
                      <span className="ml-2 font-normal text-[var(--texte-doux)]">
                        {itineraire.libelle}
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-[var(--texte-tres-doux)]">
                    {[itineraire.agence, itineraire.division, itineraire.region]
                      .filter(Boolean)
                      .join(" · ") || "Territoire non renseigné"}
                    {" · "}
                    {itineraire.nombreClients.toLocaleString("fr-FR")} client(s)
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Bouton
                    variante="secondaire"
                    taille="sm"
                    chargement={bordereau.isPending}
                    onClick={() => imprimer(itineraire.code)}
                  >
                    Bordereau terrain (PDF)
                  </Bouton>
                  {peutGerer && (
                    <>
                      <Bouton
                        variante="secondaire"
                        taille="sm"
                        onClick={() => ouvrirEdition(itineraire)}
                      >
                        Modifier
                      </Bouton>
                      <Bouton
                        variante="danger"
                        taille="sm"
                        chargement={supprimer.isPending}
                        onClick={() => retirer(itineraire)}
                      >
                        Retirer
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
        titre={enEdition ? `Itinéraire ${enEdition.code}` : "Ouvrir une tournée"}
        description={
          enEdition
            ? "Le code n'est pas modifiable : les affectations et la production déjà saisie le portent."
            : "Le code identifie la tournée pour toute sa vie. Choisissez-le avec soin."
        }
        pied={
          <>
            <Bouton
              variante="secondaire"
              onClick={() => setFormulaireOuvert(false)}
            >
              Annuler
            </Bouton>
            <Bouton
              type="submit"
              form="formulaire-itineraire"
              chargement={creer.isPending || modifier.isPending}
              disabled={!brouillon.code}
            >
              Enregistrer
            </Bouton>
          </>
        }
      >
        <form
          id="formulaire-itineraire"
          onSubmit={soumettre}
          className="grid gap-4 sm:grid-cols-2"
          noValidate
        >
          <Champ
            name="code"
            inputMode="numeric"
            libelle="Code de l'itinéraire"
            placeholder="131227"
            required
            disabled={Boolean(enEdition)}
            value={brouillon.code}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, code: evenement.target.value })
            }
            aide={enEdition ? "Non modifiable." : "Un nombre, unique."}
          />
          <Champ
            name="libelle"
            libelle="Libellé"
            placeholder="Quartier Baladji"
            value={brouillon.libelle}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, libelle: evenement.target.value })
            }
          />
          <Champ
            name="agence"
            libelle="Agence"
            placeholder="CSC_NGAOUNDERE SUD"
            value={brouillon.agence}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, agence: evenement.target.value })
            }
            aide="Vide, la tournée rejoint votre agence."
          />
          <Champ
            name="division"
            libelle="Division"
            value={brouillon.division}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, division: evenement.target.value })
            }
          />
          <Champ
            name="region"
            libelle="Direction régionale"
            value={brouillon.region}
            onChange={(evenement) =>
              setBrouillon({ ...brouillon, region: evenement.target.value })
            }
          />
        </form>
      </Modal>
    </div>
  );
}
