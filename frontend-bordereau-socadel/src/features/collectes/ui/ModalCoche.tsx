/**
 * Le formulaire qui accompagne le coche, quand il en faut un.
 *
 * L'agent n'a qu'un geste : cliquer dans la colonne Check. Quand le numéro
 * WhatsApp est déjà sur la ligne, ce geste suffit et cette modale ne s'ouvre
 * même pas. Elle ne paraît que lorsqu'il manque le numéro — car cocher OK
 * affirme que le client s'est abonné, et cette affirmation ne vaut que
 * confrontée à un numéro.
 *
 * Trois champs au maximum, et deux d'entre eux ont déjà une réponse : Rapport
 * s'ouvre sur OK, Identité sur Propriétaire. Un relevé debout dans la rue ne
 * supporte pas davantage.
 */

"use client";

import { useEffect, useState } from "react";

import { IDENTITES, RAPPORTS } from "@core/domain/statuts";
import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import type { Identite, LigneBordereau, Rapport } from "@core/domain/types";
import { Modal } from "@shared/ui/Modal";
import { Alerte, Bouton, Champ, Selecteur } from "@shared/ui/primitives";

export function ModalCoche({
  ligne,
  enCours,
  erreur,
  onFermer,
  onValider,
}: {
  ligne: LigneBordereau | null;
  enCours: boolean;
  erreur: string | null;
  onFermer: () => void;
  onValider: (donnees: {
    rapport: Rapport;
    numeroCollecte: string;
    identite: Identite;
  }) => void;
}) {
  const t = useT();

  const [rapport, setRapport] = useState<Rapport>("OK");
  const [numero, setNumero] = useState("");
  const [identite, setIdentite] = useState<Identite>("PROPRIETAIRE");

  // Chaque ligne rouvre le formulaire à neuf : garder la saisie précédente
  // ferait porter au client suivant le numéro du précédent.
  useEffect(() => {
    if (!ligne) return;
    setRapport("OK");
    setNumero(ligne.numeroCollecte ?? "");
    setIdentite(ligne.identite ?? "PROPRIETAIRE");
  }, [ligne]);

  const numeroManquant = numero.trim() === "";

  function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();
    if (!ligne || numeroManquant) return;
    onValider({ rapport, numeroCollecte: numero.trim(), identite });
  }

  return (
    <Modal
      ouvert={ligne !== null}
      onFermer={onFermer}
      titre={t("bordereau.cocher")}
      description={ligne?.nomClient ?? ligne?.serviceNo}
      pied={
        <>
          <Bouton variante="discret" onClick={onFermer}>
            {t("bordereau.annulerSelection")}
          </Bouton>
          <Bouton
            type="submit"
            form="formulaire-coche"
            chargement={enCours}
            disabled={numeroManquant}
          >
            {t("bordereau.cocher")}
          </Bouton>
        </>
      }
    >
      <form id="formulaire-coche" onSubmit={soumettre} className="space-y-4">
        {erreur && <Alerte>{erreur}</Alerte>}

        <Selecteur
          libelle={t("bordereau.rapport")}
          value={rapport}
          onChange={(evenement) => setRapport(evenement.target.value as Rapport)}
        >
          {RAPPORTS.map((valeur) => (
            <option key={valeur} value={valeur}>
              {t(`rapport.${valeur}` as Cle)}
            </option>
          ))}
        </Selecteur>

        {/* MRA n'est pas un échec : c'est ce qu'on fait quand le réseau
            manque. Le dire ici évite qu'on le prenne pour une faute. */}
        <p className="text-xs text-[var(--texte-doux)]">
          {t(`rapport.${rapport}.aide` as Cle)}
        </p>

        <Champ
          libelle={t("bordereau.numeroDemande")}
          aide={t("bordereau.numeroDemandeAide")}
          value={numero}
          onChange={(evenement) => setNumero(evenement.target.value)}
          inputMode="tel"
          autoComplete="off"
          placeholder="677 39 87 10"
          required
        />

        <Selecteur
          libelle={t("bordereau.identite")}
          value={identite}
          onChange={(evenement) =>
            setIdentite(evenement.target.value as Identite)
          }
        >
          {IDENTITES.map((valeur) => (
            <option key={valeur} value={valeur}>
              {t(`identite.${valeur}` as Cle)}
            </option>
          ))}
        </Selecteur>
      </form>
    </Modal>
  );
}
