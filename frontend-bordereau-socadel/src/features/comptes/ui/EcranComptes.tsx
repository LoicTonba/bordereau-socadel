/**
 * Gouvernance des accès : approuver, refuser, territorialiser, débloquer.
 *
 * L'écran n'affiche que ce que l'appelant peut réellement faire. Ce n'est pas
 * un contrôle de sécurité, l'API tranche de toute façon ; c'est ce qui évite de
 * proposer un bouton qui échouerait. La hiérarchie des rangs s'applique ici
 * aussi : un administrateur ne voit aucune action sur un pair.
 */

"use client";

import { useMemo, useState } from "react";

import { useT } from "@core/i18n/PreferencesProvider";
import type { Compte, Role, StatutCompte } from "@core/domain/types";
import { ErreurApi } from "@infra/http/client";
import { useSession } from "@features/auth/application/SessionProvider";
import { useAgents } from "@features/agents/application/hooks";
import { Avatar } from "@shared/ui/Avatar";
import {
  Alerte,
  Badge,
  Bouton,
  Carte,
  Champ,
  EtatVide,
  Selecteur,
} from "@shared/ui/primitives";

import {
  useApprouver,
  useBasculerCompte,
  useComptes,
  useRefuser,
  useReinitialiserPourAutrui,
} from "../application/hooks";

/** Rang de chaque rôle. Il double celui du domaine, pour n'afficher que les
 *  actions que le serveur acceptera. */
const RANG: Record<Role, number> = {
  SUPER_UTILISATEUR: 3,
  ADMINISTRATEUR: 2,
  SUPERVISEUR: 1,
  AGENT_TERRAIN: 0,
};

const TEINTES: Record<StatutCompte, { fond: string; texte: string }> = {
  EN_ATTENTE_VERIFICATION: { fond: "#fef3c7", texte: "#92400e" },
  EN_ATTENTE_APPROBATION: { fond: "#dbeafe", texte: "#1e40af" },
  ACTIF: { fond: "#dcfce7", texte: "#166534" },
  SUSPENDU: { fond: "#f1f5f9", texte: "#475569" },
  REFUSE: { fond: "#fee2e2", texte: "#991b1b" },
};

const FILTRES: readonly (StatutCompte | "TOUS")[] = [
  "EN_ATTENTE_APPROBATION",
  "ACTIF",
  "SUSPENDU",
  "REFUSE",
  "TOUS",
];

export function EcranComptes() {
  const t = useT();
  const { utilisateur } = useSession();
  const [filtre, setFiltre] = useState<StatutCompte | "TOUS">(
    "EN_ATTENTE_APPROBATION",
  );
  const [message, setMessage] = useState<
    { ton: "info" | "succes" | "erreur"; texte: string } | null
  >(null);

  const { data: comptes, isFetching, error } = useComptes(
    filtre === "TOUS" ? undefined : filtre,
  );
  const basculer = useBasculerCompte();
  const reinitialiser = useReinitialiserPourAutrui();

  const rangAppelant = utilisateur ? RANG[utilisateur.role] : 0;

  async function agir<T>(action: Promise<T>, succes: (valeur: T) => string) {
    setMessage(null);
    try {
      setMessage({ ton: "succes", texte: succes(await action) });
    } catch (exception) {
      setMessage({
        ton: "erreur",
        texte:
          exception instanceof ErreurApi
            ? exception.message
            : t("comptes.echec"),
      });
    }
  }

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">{t("comptes.titre")}</h1>
          <p className="text-sm text-[var(--texte-doux)]">{t("comptes.sousTitre")}</p>
        </div>
        <Selecteur
          aria-label={t("comptes.filtrer")}
          value={filtre}
          onChange={(evenement) =>
            setFiltre(evenement.target.value as StatutCompte | "TOUS")
          }
          className="!w-auto !py-1.5 text-xs"
        >
          {FILTRES.map((valeur) => (
            <option key={valeur} value={valeur}>
              {valeur === "TOUS"
                ? t("comptes.tous")
                : t(`statutCompte.${valeur}`)}
            </option>
          ))}
        </Selecteur>
      </header>

      {message && <Alerte ton={message.ton}>{message.texte}</Alerte>}
      {error instanceof ErreurApi && <Alerte>{error.message}</Alerte>}

      <Carte className="overflow-hidden">
        {!comptes || comptes.length === 0 ? (
          <EtatVide
            titre={isFetching ? t("commun.chargement") : t("comptes.videTitre")}
            description={t("comptes.videTexte")}
          />
        ) : (
          <ul className="divide-y divide-[var(--bordure)]">
            {comptes.map((compte) => (
              <LigneCompte
                key={compte.id}
                compte={compte}
                // Chacun n'agit que sur les rangs strictement inférieurs au
                // sien : la règle est celle du domaine, reprise à l'écran.
                actionnable={rangAppelant > RANG[compte.role]}
                rangAppelant={rangAppelant}
                onSuspendre={(actif) =>
                  agir(
                    basculer.mutateAsync({ compteId: compte.id, actif }),
                    () =>
                      actif
                        ? t("comptes.reactive", { nom: compte.nomComplet })
                        : t("comptes.suspendu", { nom: compte.nomComplet }),
                  )
                }
                onReinitialiser={() =>
                  agir(reinitialiser.mutateAsync(compte.id), (provisoire) =>
                    t("comptes.provisoire", {
                      nom: provisoire.nomComplet,
                      motDePasse: provisoire.motDePasseProvisoire,
                    }),
                  )
                }
                onMessage={setMessage}
              />
            ))}
          </ul>
        )}
      </Carte>
    </div>
  );
}

function LigneCompte({
  compte,
  actionnable,
  rangAppelant,
  onSuspendre,
  onReinitialiser,
  onMessage,
}: {
  compte: Compte;
  actionnable: boolean;
  rangAppelant: number;
  onSuspendre: (actif: boolean) => void;
  onReinitialiser: () => void;
  onMessage: (
    message: { ton: "info" | "succes" | "erreur"; texte: string } | null,
  ) => void;
}) {
  const t = useT();
  const [ouvert, setOuvert] = useState(false);
  const teinte = TEINTES[compte.statut];
  const enAttente = compte.statut === "EN_ATTENTE_APPROBATION";

  return (
    <li className="px-5 py-3.5">
      <div className="flex flex-wrap items-center gap-3">
        <Avatar nom={compte.nomComplet} url={compte.photoUrl} taille={34} />

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{compte.nomComplet}</p>
          <p className="truncate text-xs text-[var(--texte-tres-doux)]">
            {compte.identifiant}
            {compte.email && ` · ${compte.email}`}
            {compte.agence && ` · ${compte.agence}`}
          </p>
        </div>

        <Badge fond={teinte.fond} texte={teinte.texte}>
          {t(`statutCompte.${compte.statut}`)}
        </Badge>
        <Badge fond="#eff7fd" texte="#1f5fa0">
          {t(`role.${compte.role}`)}
        </Badge>

        {actionnable ? (
          <div className="flex flex-wrap items-center gap-2">
            {enAttente && (
              <Bouton taille="sm" onClick={() => setOuvert((ancien) => !ancien)}>
                {t("comptes.examiner")}
              </Bouton>
            )}
            {compte.statut === "ACTIF" && (
              <>
                <Bouton
                  taille="sm"
                  variante="secondaire"
                  onClick={onReinitialiser}
                >
                  {t("comptes.reinitialiser")}
                </Bouton>
                <Bouton
                  taille="sm"
                  variante="secondaire"
                  onClick={() => onSuspendre(false)}
                >
                  {t("comptes.suspendre")}
                </Bouton>
              </>
            )}
            {compte.statut === "SUSPENDU" && (
              <Bouton taille="sm" variante="secondaire" onClick={() => onSuspendre(true)}>
                {t("comptes.reactiver")}
              </Bouton>
            )}
          </div>
        ) : (
          <p className="text-xs text-[var(--texte-tres-doux)]">
            {t("comptes.horsPortee")}
          </p>
        )}
      </div>

      {ouvert && enAttente && (
        <FormulaireApprobation
          compte={compte}
          rangAppelant={rangAppelant}
          onTermine={(texte) => {
            setOuvert(false);
            onMessage({ ton: "succes", texte });
          }}
          onErreur={(texte) => onMessage({ ton: "erreur", texte })}
        />
      )}
    </li>
  );
}

/**
 * Attribution du rôle et du périmètre au moment de l'approbation.
 *
 * Deux règles y sont rendues visibles plutôt qu'expliquées après coup : on
 * n'attribue qu'un rang strictement inférieur au sien, et un compte agent doit
 * désigner l'agent de terrain auquel il se rattache, faute de quoi son
 * titulaire verrait la production de tout le monde.
 */
function FormulaireApprobation({
  compte,
  rangAppelant,
  onTermine,
  onErreur,
}: {
  compte: Compte;
  rangAppelant: number;
  onTermine: (message: string) => void;
  onErreur: (message: string) => void;
}) {
  const t = useT();
  const approuver = useApprouver();
  const refuser = useRefuser();
  const { data: agents } = useAgents(true);

  const rolesAttribuables = useMemo(
    () =>
      (Object.keys(RANG) as Role[])
        .filter((role) => RANG[role] < rangAppelant)
        .sort((a, b) => RANG[b] - RANG[a]),
    [rangAppelant],
  );

  const [role, setRole] = useState<Role>(
    rolesAttribuables.includes(compte.role) ? compte.role : rolesAttribuables[0],
  );
  const [agence, setAgence] = useState(compte.agence ?? "");
  const [region, setRegion] = useState(compte.region ?? "");
  const [agentId, setAgentId] = useState(compte.agentId ?? "");
  const [motif, setMotif] = useState("");

  const agentRequis = role === "AGENT_TERRAIN";

  async function valider() {
    try {
      await approuver.mutateAsync({
        compteId: compte.id,
        role,
        region: region || null,
        agence: agence || null,
        agentId: agentRequis ? agentId : null,
      });
      onTermine(t("comptes.approuve", { nom: compte.nomComplet }));
    } catch (exception) {
      onErreur(
        exception instanceof ErreurApi ? exception.message : t("comptes.echec"),
      );
    }
  }

  async function rejeter() {
    try {
      await refuser.mutateAsync({ compteId: compte.id, motif: motif || undefined });
      onTermine(t("comptes.refuse", { nom: compte.nomComplet }));
    } catch (exception) {
      onErreur(
        exception instanceof ErreurApi ? exception.message : t("comptes.echec"),
      );
    }
  }

  return (
    <div className="mt-4 space-y-4 rounded-xl border border-[var(--bordure)] bg-[var(--fond-survol)] p-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Selecteur
          libelle={t("comptes.roleAttribue")}
          value={role}
          onChange={(evenement) => setRole(evenement.target.value as Role)}
        >
          {rolesAttribuables.map((valeur) => (
            <option key={valeur} value={valeur}>
              {t(`role.${valeur}`)}
            </option>
          ))}
        </Selecteur>

        {agentRequis ? (
          <Selecteur
            libelle={t("comptes.agentRattache")}
            value={agentId}
            onChange={(evenement) => setAgentId(evenement.target.value)}
          >
            <option value="">{t("comptes.choisirAgent")}</option>
            {(agents ?? []).map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.matricule}, {agent.nomComplet}
              </option>
            ))}
          </Selecteur>
        ) : (
          <Champ
            name="agence"
            libelle={t("comptes.agence")}
            placeholder="CSC_ESSOS"
            value={agence}
            onChange={(evenement) => setAgence(evenement.target.value)}
          />
        )}

        {!agentRequis && (
          <Champ
            name="region"
            libelle={t("comptes.region")}
            placeholder="DRC"
            value={region}
            onChange={(evenement) => setRegion(evenement.target.value)}
          />
        )}

        <Champ
          name="motif"
          libelle={t("comptes.motifRefus")}
          aide={t("comptes.motifAide")}
          value={motif}
          onChange={(evenement) => setMotif(evenement.target.value)}
        />
      </div>

      {role === "SUPERVISEUR" && !agence && !region && (
        <Alerte ton="info">{t("comptes.perimetreManquant")}</Alerte>
      )}

      <div className="flex flex-wrap gap-2">
        <Bouton
          taille="sm"
          chargement={approuver.isPending}
          disabled={agentRequis && !agentId}
          onClick={valider}
        >
          {t("comptes.approuver")}
        </Bouton>
        <Bouton
          taille="sm"
          variante="danger"
          chargement={refuser.isPending}
          onClick={rejeter}
        >
          {t("comptes.refuser")}
        </Bouton>
      </div>
    </div>
  );
}
