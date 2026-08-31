/**
 * Répertoire des agents de terrain, avec son cycle complet.
 *
 * « Supprimer » retire du service sans effacer : les bordereaux passés
 * référencent l'agent et fondent sa rémunération. L'interface le dit
 * explicitement plutôt que de laisser croire à une suppression.
 */

"use client";

import { useState } from "react";
import Link from "next/link";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Agent } from "@core/domain/types";
import { ErreurApi } from "@infra/http/client";
import { Avatar } from "@shared/ui/Avatar";
import { ChampPhoto } from "@shared/ui/ChampPhoto";
import { Modal } from "@shared/ui/Modal";
import { useToasts } from "@shared/ui/Toasts";
import {
  Alerte,
  Bouton,
  Carte,
  Champ,
  cx,
  EtatVide,
} from "@shared/ui/primitives";

import {
  useAgents,
  useBasculerActivation,
  useCreerAgent,
  useModifierAgent,
} from "../application/hooks";

interface Brouillon {
  matricule: string;
  nomComplet: string;
  telephone: string;
  zoneRattachement: string;
  region: string;
  photoUrl: string | null;
}

const VIDE: Brouillon = {
  matricule: "",
  nomComplet: "",
  telephone: "",
  zoneRattachement: "",
  region: "",
  photoUrl: null,
};

export function EcranAgents() {
  const t = useT();
  const { data: agents = [], isLoading } = useAgents();
  const creer = useCreerAgent();
  const modifier = useModifierAgent();
  const basculer = useBasculerActivation();
  const { notifier } = useToasts();

  const [brouillon, setBrouillon] = useState<Brouillon>(VIDE);
  const [enEdition, setEnEdition] = useState<Agent | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  function ouvrirEdition(agent: Agent) {
    setEnEdition(agent);
    setBrouillon({
      matricule: agent.matricule,
      nomComplet: agent.nomComplet,
      telephone: agent.telephone ?? "",
      zoneRattachement: agent.zoneRattachement ?? "",
      region: agent.region ?? "",
      photoUrl: agent.photoUrl,
    });
    setErreur(null);
  }

  function fermerEdition() {
    setEnEdition(null);
    setBrouillon(VIDE);
  }

  async function soumettreCreation(evenement: React.FormEvent) {
    evenement.preventDefault();
    setErreur(null);
    try {
      await creer.mutateAsync({
        matricule: brouillon.matricule,
        nomComplet: brouillon.nomComplet,
        telephone: brouillon.telephone.trim() || null,
        zoneRattachement: brouillon.zoneRattachement.trim() || null,
        region: brouillon.region.trim() || null,
        photoUrl: brouillon.photoUrl,
      });
      notifier("creation", t("toast.agentCree", { nom: brouillon.nomComplet }));
      setBrouillon(VIDE);
    } catch (exception) {
      const message = messageDe(exception, t("commun.erreurGenerique"));
      setErreur(message);
      notifier("echec", message);
    }
  }

  async function soumettreEdition(evenement: React.FormEvent) {
    evenement.preventDefault();
    if (!enEdition) return;
    setErreur(null);
    try {
      await modifier.mutateAsync({
        agentId: enEdition.id,
        nomComplet: brouillon.nomComplet,
        telephone: brouillon.telephone.trim() || null,
        zoneRattachement: brouillon.zoneRattachement.trim() || null,
        region: brouillon.region.trim() || null,
        photoUrl: brouillon.photoUrl,
      });
      notifier(
        "modification",
        t("toast.agentModifie", { nom: brouillon.nomComplet }),
      );
      fermerEdition();
    } catch (exception) {
      const message = messageDe(exception, t("commun.erreurGenerique"));
      setErreur(message);
      notifier("echec", message);
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-lg font-semibold">{t("agents.titre")}</h1>
        <p className="text-sm text-[var(--texte-doux)]">{t("agents.sousTitre")}</p>
      </header>

      {erreur && !enEdition && <Alerte>{erreur}</Alerte>}

      <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
        <Carte titre={t("agents.enregistrer")}>
          <form onSubmit={soumettreCreation} className="space-y-3.5 p-5">
            <ChampPhoto
              libelle={t("agents.photo")}
              aide={t("agents.photoAide")}
              nom={brouillon.nomComplet || brouillon.matricule || "?"}
              url={brouillon.photoUrl}
              onChange={(url) =>
                setBrouillon((b) => ({ ...b, photoUrl: url }))
              }
            />
            <Champ
              name="matricule"
              libelle={t("agents.matricule")}
              placeholder="AG004"
              required
              value={brouillon.matricule}
              onChange={(e) =>
                setBrouillon((b) => ({ ...b, matricule: e.target.value }))
              }
            />
            <Champ
              name="nomComplet"
              libelle={t("agents.nomComplet")}
              placeholder="MBALLA Jean Pierre"
              required
              value={brouillon.nomComplet}
              onChange={(e) =>
                setBrouillon((b) => ({ ...b, nomComplet: e.target.value }))
              }
            />
            <Champ
              name="telephone"
              libelle={t("agents.telephone")}
              placeholder="+237 6XX XX XX XX"
              inputMode="tel"
              value={brouillon.telephone}
              onChange={(e) =>
                setBrouillon((b) => ({ ...b, telephone: e.target.value }))
              }
            />
            <Champ
              name="zone"
              libelle={t("agents.zone")}
              placeholder="CSC_NSAM"
              value={brouillon.zoneRattachement}
              onChange={(e) =>
                setBrouillon((b) => ({
                  ...b,
                  zoneRattachement: e.target.value,
                }))
              }
            />
            <Champ
              name="region"
              libelle={t("agents.region")}
              placeholder="DCUY"
              value={brouillon.region}
              onChange={(e) =>
                setBrouillon((b) => ({ ...b, region: e.target.value }))
              }
            />
            <Bouton
              type="submit"
              className="w-full"
              chargement={creer.isPending}
              disabled={!brouillon.matricule || !brouillon.nomComplet}
            >
              {t("commun.enregistrer")}
            </Bouton>
          </form>
        </Carte>

        <Carte
          titre={t("agents.repertoire")}
          description={t("agents.nombre", { n: agents.length })}
        >
          {isLoading ? (
            <p className="px-5 py-10 text-center text-sm text-[var(--texte-tres-doux)]">
              {t("commun.chargement")}
            </p>
          ) : agents.length === 0 ? (
            <EtatVide
              titre={t("agents.vide")}
              description={t("agents.videAide")}
            />
          ) : (
            <ul className="divide-y divide-[var(--bordure)]">
              {agents.map((agent) => (
                <li
                  key={agent.id}
                  className="flex flex-wrap items-center gap-3 px-5 py-3"
                >
                  <Avatar
                    nom={agent.nomComplet}
                    url={agent.photoUrl}
                    taille={38}
                    className={cx(!agent.actif && "opacity-50")}
                  />

                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">
                      {agent.nomComplet}
                      {!agent.actif && (
                        <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-normal text-slate-600">
                          {t("commun.inactif")}
                        </span>
                      )}
                    </p>
                    <p className="chiffres truncate text-xs text-[var(--texte-tres-doux)]">
                      {agent.matricule}
                      {agent.zoneRattachement && ` · ${agent.zoneRattachement}`}
                      {agent.telephone && ` · ${agent.telephone}`}
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Link
                      href={`/agents/${agent.id}`}
                      className="rounded-md px-2.5 py-1.5 text-xs font-medium text-socadel-700 hover:bg-socadel-50"
                    >
                      {t("agents.voirPortefeuille")}
                    </Link>
                    <Bouton
                      variante="secondaire"
                      taille="sm"
                      onClick={() => ouvrirEdition(agent)}
                    >
                      {t("commun.modifier")}
                    </Bouton>
                    <Bouton
                      variante="secondaire"
                      taille="sm"
                      chargement={basculer.isPending}
                      onClick={() =>
                        basculer.mutate(
                          { agentId: agent.id, actif: !agent.actif },
                          {
                            // Le retrait du service se signale en ambre : il
                            // ferme un accès, ce n'est pas une modification
                            // anodine.
                            onSuccess: () =>
                              notifier(
                                agent.actif ? "suppression" : "creation",
                                t(
                                  agent.actif
                                    ? "toast.agentRetire"
                                    : "toast.agentRemis",
                                  { nom: agent.nomComplet },
                                ),
                              ),
                            onError: () =>
                              notifier("echec", t("commun.erreurGenerique")),
                          },
                        )
                      }
                    >
                      {agent.actif
                        ? t("agents.desactiver")
                        : t("agents.reactiver")}
                    </Bouton>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="border-t border-[var(--bordure)] px-5 py-3 text-[11px] text-[var(--texte-tres-doux)]">
            {t("agents.mentionHistorique")}
          </p>
        </Carte>
      </div>

      <Modal
        ouvert={enEdition !== null}
        onFermer={fermerEdition}
        titre={t("commun.modifier")}
        description={enEdition?.matricule}
        pied={
          <>
            <Bouton variante="secondaire" type="button" onClick={fermerEdition}>
              {t("commun.annuler")}
            </Bouton>
            <Bouton
              type="submit"
              form="formulaire-agent"
              chargement={modifier.isPending}
            >
              {t("commun.enregistrer")}
            </Bouton>
          </>
        }
      >
        {enEdition && (
          <form
            id="formulaire-agent"
            onSubmit={soumettreEdition}
            className="space-y-3.5"
          >
            {erreur && <Alerte>{erreur}</Alerte>}

            <ChampPhoto
              libelle={t("agents.photo")}
              aide={t("agents.photoAide")}
              nom={brouillon.nomComplet}
              url={brouillon.photoUrl}
              onChange={(url) =>
                setBrouillon((b) => ({ ...b, photoUrl: url }))
              }
            />
            <Champ
              libelle={t("agents.nomComplet")}
              required
              value={brouillon.nomComplet}
              onChange={(e) =>
                setBrouillon((b) => ({ ...b, nomComplet: e.target.value }))
              }
            />
            <Champ
              libelle={t("agents.telephone")}
              inputMode="tel"
              value={brouillon.telephone}
              onChange={(e) =>
                setBrouillon((b) => ({ ...b, telephone: e.target.value }))
              }
            />
            <Champ
              libelle={t("agents.zone")}
              value={brouillon.zoneRattachement}
              onChange={(e) =>
                setBrouillon((b) => ({
                  ...b,
                  zoneRattachement: e.target.value,
                }))
              }
            />
            <Champ
              libelle={t("agents.region")}
              value={brouillon.region}
              onChange={(e) =>
                setBrouillon((b) => ({ ...b, region: e.target.value }))
              }
            />
          </form>
        )}
      </Modal>
    </div>
  );
}

function messageDe(exception: unknown, defaut: string): string {
  return exception instanceof ErreurApi ? exception.message : defaut;
}
