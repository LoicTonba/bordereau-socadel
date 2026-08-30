/** Écran complet du bordereau : filtres, actions groupées, tableau, pagination. */

"use client";

import { useCallback, useState } from "react";

import { STATUTS_SAISISSABLES } from "@core/domain/statuts";
import { useT } from "@core/i18n/PreferencesProvider";
import type { Cle } from "@core/i18n/messages";
import type {
  FiltreBordereau,
  LigneBordereau,
  ParamsPagination,
  StatutCollecte,
} from "@core/domain/types";
import { ErreurApi } from "@infra/http/client";
import { Pagination } from "@shared/ui/Pagination";
import { Alerte, Bouton, Carte, Selecteur } from "@shared/ui/primitives";

import {
  useBordereau,
  useDeclarerEnLot,
  useExporter,
  useVerifier,
} from "../application/hooks";
import { BarreFiltres } from "./BarreFiltres";
import { ModalSaisie } from "./ModalSaisie";
import { TableauBordereau } from "./TableauBordereau";

const PAGINATION_INITIALE: ParamsPagination = {
  page: 1,
  taille: 25,
  tri: "date_collecte",
  ordre: "desc",
};

export function EcranBordereau() {
  const t = useT();
  const [filtre, setFiltre] = useState<FiltreBordereau>({});
  const [pagination, setPagination] = useState<ParamsPagination>(PAGINATION_INITIALE);
  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [ligneEditee, setLigneEditee] = useState<LigneBordereau | null>(null);
  const [statutLot, setStatutLot] = useState<StatutCollecte>("ABONNE");
  const [message, setMessage] = useState<
    { ton: "info" | "succes" | "erreur"; texte: string } | null
  >(null);

  const { data, isFetching, error } = useBordereau(filtre, pagination);
  const declarerEnLot = useDeclarerEnLot();
  const verifier = useVerifier();
  const exporter = useExporter();

  // Changer de filtre remet la pagination à zéro : rester en page 12 d'un
  // résultat qui n'en compte plus que 3 afficherait un tableau vide.
  const changerFiltre = useCallback((suivant: FiltreBordereau) => {
    setFiltre(suivant);
    setPagination((actuelle) => ({ ...actuelle, page: 1 }));
    setSelection(new Set());
  }, []);

  function trier(cle: string) {
    setPagination((actuelle) => ({
      ...actuelle,
      tri: cle,
      ordre: actuelle.tri === cle && actuelle.ordre === "desc" ? "asc" : "desc",
      page: 1,
    }));
  }

  async function appliquerEnLot() {
    setMessage(null);
    try {
      const resultat = await declarerEnLot.mutateAsync({
        lignesIds: [...selection],
        statut: statutLot,
      });
      setSelection(new Set());

      const ignorees = resultat.lignesDemandees - resultat.lignesModifiees;
      setMessage({
        ton: ignorees > 0 ? "info" : "succes",
        texte:
          ignorees > 0
            ? t("lot.resultatPartiel", {
                modifiees: resultat.lignesModifiees,
                ignorees,
              })
            : t("lot.resultat", { n: resultat.lignesModifiees }),
      });
    } catch (exception) {
      setMessage({
        ton: "erreur",
        texte:
          exception instanceof ErreurApi
            ? exception.message
            : t("lot.echec"),
      });
    }
  }

  async function lancerVerification() {
    setMessage(null);
    try {
      const rapport = await verifier.mutateAsync(filtre);
      setMessage({
        ton: "succes",
        texte: t("verification.resultat", {
          examinees: rapport.lignesExaminees,
          confirmees: rapport.confirmees,
          infirmees: rapport.infirmees,
          introuvables: rapport.introuvables,
        }),
      });
    } catch (exception) {
      setMessage({
        ton: "erreur",
        texte:
          exception instanceof ErreurApi
            ? exception.message
            : t("verification.echec"),
      });
    }
  }

  async function telecharger(format: "csv" | "pdf") {
    setMessage(null);
    try {
      const fichier = await exporter.mutateAsync({ filtre, format });
      if (fichier.tronque) {
        setMessage({
          ton: "info",
          texte:
            t("export.tronque"),
        });
      }
    } catch (exception) {
      setMessage({
        ton: "erreur",
        texte:
          exception instanceof ErreurApi ? exception.message : t("export.echec"),
      });
    }
  }

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">{t("bordereau.titre")}</h1>
          <p className="text-sm text-[var(--texte-doux)]">
            {t("bordereau.sousTitre")}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Bouton
            variante="secondaire"
            taille="sm"
            onClick={lancerVerification}
            chargement={verifier.isPending}
          >
            {t("bordereau.verifier")}
          </Bouton>
          <Bouton
            variante="secondaire"
            taille="sm"
            onClick={() => telecharger("csv")}
            chargement={exporter.isPending}
          >
            {t("bordereau.exporterCsv")}
          </Bouton>
          <Bouton
            variante="secondaire"
            taille="sm"
            onClick={() => telecharger("pdf")}
            chargement={exporter.isPending}
          >
            {t("bordereau.exporterPdf")}
          </Bouton>
        </div>
      </header>

      {message && <Alerte ton={message.ton}>{message.texte}</Alerte>}
      {error instanceof ErreurApi && <Alerte>{error.message}</Alerte>}

      <Carte className="overflow-hidden">
        <BarreFiltres filtre={filtre} onChanger={changerFiltre} />

        {selection.size > 0 && (
          <div className="flex flex-wrap items-center gap-3 border-b border-[var(--bordure)] bg-socadel-50 px-4 py-2.5">
            <p className="chiffres text-sm font-medium text-socadel-800">
              {t("bordereau.selection", { n: selection.size })}
            </p>

            <Selecteur
              aria-label={t("bordereau.statut")}
              value={statutLot}
              onChange={(evenement) =>
                setStatutLot(evenement.target.value as StatutCollecte)
              }
              className="!w-auto !py-1.5 text-xs"
            >
              {STATUTS_SAISISSABLES.map((valeur) => (
                <option key={valeur} value={valeur}>
                  {t(`statut.${valeur}` as Cle)}
                </option>
              ))}
            </Selecteur>

            <Bouton
              taille="sm"
              onClick={appliquerEnLot}
              chargement={declarerEnLot.isPending}
            >
              {t("bordereau.appliquer")}
            </Bouton>
            <Bouton variante="discret" taille="sm" onClick={() => setSelection(new Set())}>
              {t("bordereau.annulerSelection")}
            </Bouton>
          </div>
        )}

        <TableauBordereau
          lignes={data?.elements ?? []}
          chargement={isFetching}
          selection={selection}
          onSelection={setSelection}
          onEditer={setLigneEditee}
          tri={pagination.tri}
          ordre={pagination.ordre}
          onTrier={trier}
        />

        {data && (
          <Pagination
            meta={data.meta}
            onPage={(page) => setPagination((actuelle) => ({ ...actuelle, page }))}
            onTaille={(taille) =>
              setPagination((actuelle) => ({ ...actuelle, taille, page: 1 }))
            }
          />
        )}
      </Carte>

      <ModalSaisie ligne={ligneEditee} onFermer={() => setLigneEditee(null)} />
    </div>
  );
}
