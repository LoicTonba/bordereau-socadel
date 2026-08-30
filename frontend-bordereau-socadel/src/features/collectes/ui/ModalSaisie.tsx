/**
 * Modal de saisie d'une ligne de bordereau.
 *
 * Le formulaire reproduit la règle du domaine : un client déclaré abonné doit
 * être accompagné du numéro relevé. La contrainte est signalée ici pour éviter
 * un aller-retour serveur, mais reste vérifiée côté API.
 */

"use client";

import { useEffect, useState } from "react";

import {
  exigeNumero,
  RESPONSABLES,
  STATUTS_SAISISSABLES,
} from "@core/domain/statuts";
import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import type { LigneBordereau, Responsable, StatutCollecte } from "@core/domain/types";
import { ErreurApi } from "@infra/http/client";
import { Modal } from "@shared/ui/Modal";
import { Alerte, Bouton, Champ, Selecteur } from "@shared/ui/primitives";

import { useDeclarer } from "../application/hooks";

export function ModalSaisie({
  ligne,
  onFermer,
}: {
  ligne: LigneBordereau | null;
  onFermer: () => void;
}) {
  const t = useT();
  const declarer = useDeclarer();

  const [statut, setStatut] = useState<StatutCollecte>("ABONNE");
  const [numero, setNumero] = useState("");
  const [responsable, setResponsable] = useState<Responsable>("TERRAIN");
  const [observation, setObservation] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);

  // Le formulaire se recharge à chaque ligne ouverte : sans cela, la saisie
  // précédente resterait affichée sur la suivante.
  useEffect(() => {
    if (!ligne) return;
    setStatut(ligne.statut === "A_TRAITER" ? "ABONNE" : ligne.statut);
    setNumero(ligne.numeroCollecte ?? "");
    setResponsable(ligne.responsable ?? "TERRAIN");
    setObservation(ligne.observation ?? "");
    setErreur(null);
  }, [ligne]);

  const numeroManquant = exigeNumero(statut) && numero.trim() === "";

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    if (!ligne || numeroManquant) return;

    setErreur(null);
    try {
      await declarer.mutateAsync({
        ligneId: ligne.id,
        statut,
        numeroCollecte: numero.trim() || null,
        responsable,
        observation: observation.trim() || null,
      });
      onFermer();
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : t("saisie.echec"),
      );
    }
  }

  return (
    <Modal
      ouvert={ligne !== null}
      onFermer={onFermer}
      titre={t("saisie.titre")}
      description={
        ligne
          ? `${ligne.nomClient ?? t("bordereau.client")} — ${ligne.serviceNo}`
          : undefined
      }
      pied={
        <>
          <Bouton variante="secondaire" onClick={onFermer} type="button">
            {t("commun.annuler")}
          </Bouton>
          <Bouton
            type="submit"
            form="formulaire-saisie"
            chargement={declarer.isPending}
            disabled={numeroManquant}
          >
            {t("commun.enregistrer")}
          </Bouton>
        </>
      }
    >
      {ligne && (
        <form id="formulaire-saisie" onSubmit={soumettre} className="space-y-4">
          {erreur && <Alerte>{erreur}</Alerte>}

          <dl className="grid grid-cols-2 gap-3 rounded-lg bg-[var(--fond-survol)] p-3 text-xs">
            <Info libelle={t("bordereau.refGeo")} valeur={ligne.refGeo} />
            <Info
              libelle={t("bordereau.itineraire")}
              valeur={ligne.codeItineraire?.toString()}
            />
            <Info libelle={t("bordereau.compteur")} valeur={ligne.numeroCompteur} />
            <Info libelle={t("bordereau.date")} valeur={ligne.dateCollecte} />
          </dl>

          <Selecteur
            name="statut"
            libelle={t("saisie.resultat")}
            value={statut}
            onChange={(evenement) =>
              setStatut(evenement.target.value as StatutCollecte)
            }
          >
            {STATUTS_SAISISSABLES.map((valeur) => (
              <option key={valeur} value={valeur}>
                {t(`statut.${valeur}` as Cle)}
              </option>
            ))}
          </Selecteur>
          <p className="-mt-2 text-xs text-[var(--texte-tres-doux)]">
            {t(`statut.${statut}.aide` as Cle)}
          </p>

          <Champ
            name="numero"
            libelle={
              exigeNumero(statut)
                ? t("saisie.numeroObligatoire")
                : t("saisie.numero")
            }
            placeholder="+237 6XX XX XX XX"
            inputMode="tel"
            value={numero}
            onChange={(evenement) => setNumero(evenement.target.value)}
            erreur={
              numeroManquant
                ? t("saisie.numeroManquant")
                : undefined
            }
            aide={t("saisie.numeroAide")}
          />

          <Selecteur
            name="responsable"
            libelle={t("saisie.origine")}
            value={responsable}
            onChange={(evenement) =>
              setResponsable(evenement.target.value as Responsable)
            }
          >
            {RESPONSABLES.map((valeur) => (
              <option key={valeur} value={valeur}>
                {t(`responsable.${valeur}` as Cle)}
              </option>
            ))}
          </Selecteur>

          <Champ
            name="observation"
            libelle={t("saisie.observation")}
            placeholder={t("saisie.observationExemple")}
            maxLength={500}
            value={observation}
            onChange={(evenement) => setObservation(evenement.target.value)}
          />
        </form>
      )}
    </Modal>
  );
}

function Info({ libelle, valeur }: { libelle: string; valeur?: string | null }) {
  return (
    <div>
      <dt className="text-[var(--texte-tres-doux)]">{libelle}</dt>
      <dd className="chiffres mt-0.5 font-medium">{valeur || "—"}</dd>
    </div>
  );
}
