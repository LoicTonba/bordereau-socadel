"""Doubles en mémoire des ports de persistance.

Ils existent parce que la couche application ne dépend que de protocoles : on
peut donc exercer les cas d'usage et l'API HTTP entière sans PostgreSQL. C'est
le bénéfice concret de l'inversion de dépendance, pas un artifice de test.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime, timezone
from types import TracebackType
from uuid import UUID

from bordereau.application.dto import (
    FiltreBordereau,
    Page,
    PaginationParams,
)
from bordereau.domain.entities import (
    Agence,
    TraceAudit,
    Affectation,
    AgentTerrain,
    Client,
    Itineraire,
    LigneBordereau,
    Utilisateur,
)
from bordereau.domain.value_objects import CodeItineraire, Periode, ServiceNo


class HorlogeFigee:
    """Horloge déterministe : les assertions sur les dates deviennent stables."""

    def __init__(self, instant: datetime | None = None) -> None:
        self.instant = instant or datetime(2026, 8, 30, 9, 0, tzinfo=timezone.utc)

    def maintenant(self) -> datetime:
        return self.instant

    def aujourdhui(self) -> date:
        return self.instant.date()


class EntrepotMemoire:
    """État partagé par tous les repositories d'une même unité de travail."""

    def __init__(self) -> None:
        self.utilisateurs: dict[UUID, Utilisateur] = {}
        self.agents: dict[UUID, AgentTerrain] = {}
        self.clients: dict[UUID, Client] = {}
        self.agences: dict[str, Agence] = {}
        self.audit: list[TraceAudit] = []
        self.restrictions: dict[str, set[str]] = {}
        self.itineraires: dict[int, Itineraire] = {}
        self.affectations: dict[UUID, Affectation] = {}
        self.lignes: dict[UUID, LigneBordereau] = {}


class _Utilisateurs:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def par_identifiant(self, identifiant: str) -> Utilisateur | None:
        return next(
            (u for u in self._e.utilisateurs.values() if u.identifiant == identifiant),
            None,
        )

    async def par_id(self, utilisateur_id: UUID) -> Utilisateur | None:
        return self._e.utilisateurs.get(utilisateur_id)

    async def par_email(self, email: str) -> Utilisateur | None:
        cible = email.strip().lower()
        return next(
            (u for u in self._e.utilisateurs.values() if u.email == cible), None
        )

    async def par_jeton_verification(self, jeton: str) -> Utilisateur | None:
        return next(
            (
                u
                for u in self._e.utilisateurs.values()
                if u.jeton_verification == jeton
            ),
            None,
        )

    async def par_jeton_reinitialisation(self, jeton: str) -> Utilisateur | None:
        return next(
            (
                u
                for u in self._e.utilisateurs.values()
                if u.jeton_reinitialisation == jeton
            ),
            None,
        )

    async def lister(self, *, statut: str | None = None) -> Sequence[Utilisateur]:
        comptes = list(self._e.utilisateurs.values())
        if statut is not None:
            comptes = [u for u in comptes if u.statut.value == statut]
        return sorted(comptes, key=lambda u: u.nom_complet)

    async def enregistrer(self, utilisateur: Utilisateur) -> None:
        self._e.utilisateurs[utilisateur.id] = utilisateur


class _Agents:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def par_id(self, agent_id: UUID) -> AgentTerrain | None:
        return self._e.agents.get(agent_id)

    async def par_matricule(self, matricule: str) -> AgentTerrain | None:
        return next(
            (a for a in self._e.agents.values() if a.matricule == matricule.upper()),
            None,
        )

    async def lister(self, *, actifs_seulement: bool = False) -> Sequence[AgentTerrain]:
        agents = list(self._e.agents.values())
        if actifs_seulement:
            agents = [a for a in agents if a.actif]
        return sorted(agents, key=lambda a: a.nom_complet)

    async def enregistrer(self, agent: AgentTerrain) -> None:
        self._e.agents[agent.id] = agent


class _ClientsAnnuaire:
    """Mélange ajouté à `_Clients` : l'annuaire déduit du référentiel."""

    async def lister_agences(self):
        vues = {}
        for client in self._e.clients.values():
            if client.agence and client.agence not in vues:
                vues[client.agence] = (client.agence, client.region, client.division)
        return list(vues.values())


class _Clients(_ClientsAnnuaire):
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def par_service_no(self, service_no: ServiceNo) -> Client | None:
        return next(
            (c for c in self._e.clients.values() if c.service_no == service_no),
            None,
        )

    async def par_services_no(
        self, services_no: Iterable[ServiceNo]
    ) -> dict[str, Client]:
        recherches = {s.valeur for s in services_no}
        return {
            c.service_no.valeur: c
            for c in self._e.clients.values()
            if c.service_no.valeur in recherches
        }

    async def par_itineraire(
        self, code: CodeItineraire, pagination: PaginationParams | None = None
    ) -> Sequence[Client]:
        return [c for c in self._e.clients.values() if c.code_itineraire == code]

    async def compter_par_itineraire(self, code: CodeItineraire) -> int:
        return len(await self.par_itineraire(code))

    async def enregistrer_en_lot(self, clients: Iterable[Client]) -> int:
        total = 0
        for client in clients:
            self._e.clients[client.id] = client
            total += 1
        return total


class _Restrictions:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def lister(self) -> dict[str, set[str]]:
        return {role: set(p) for role, p in self._e.restrictions.items()}

    async def pour(self, role: str) -> set[str]:
        return set(self._e.restrictions.get(role, set()))

    async def definir(self, role: str, permissions: set[str]) -> None:
        self._e.restrictions[role] = set(permissions)


class _Audit:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def enregistrer(self, trace) -> None:
        self._e.audit.append(trace)

    async def rechercher(
        self,
        *,
        identifiant=None,
        action=None,
        depuis=None,
        jusqu_a=None,
        echecs_seulement=False,
        pagination=None,
    ):
        params = pagination or PaginationParams()
        traces = list(reversed(self._e.audit))

        if identifiant:
            motif = identifiant.lower()
            traces = [t for t in traces if motif in (t.identifiant or "").lower()]
        if action:
            motif = action.lower()
            traces = [t for t in traces if motif in t.action.lower()]
        if echecs_seulement:
            traces = [t for t in traces if not t.reussi]

        debut = params.offset
        return Page(
            elements=traces[debut : debut + params.limite],
            total=len(traces),
            page=params.page,
            taille=params.taille,
        )


class _Agences:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def par_nom(self, nom: str):
        return self._e.agences.get(nom.strip().upper())

    async def lister(self, *, ouvertes_seulement: bool = False):
        agences = list(self._e.agences.values())
        if ouvertes_seulement:
            agences = [a for a in agences if a.ouverte]
        return sorted(agences, key=lambda a: a.nom)

    async def enregistrer(self, agence) -> None:
        self._e.agences[agence.nom] = agence

    async def supprimer(self, nom: str) -> None:
        self._e.agences.pop(nom.strip().upper(), None)

    async def compter_rattachements(self, nom: str) -> int:
        nom = nom.strip().upper()
        comptes = sum(1 for u in self._e.utilisateurs.values() if u.agence == nom)
        tournees = sum(1 for i in self._e.itineraires.values() if i.agence == nom)
        return comptes + tournees


class _Itineraires:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def par_code(self, code: CodeItineraire) -> Itineraire | None:
        return self._e.itineraires.get(code.valeur)

    async def est_affecte(self, code: CodeItineraire) -> bool:
        return any(
            a.itineraire_code == code.valeur
            for a in self._e.affectations.values()
        )

    async def supprimer(self, code: CodeItineraire) -> None:
        self._e.itineraires.pop(code.valeur, None)

    async def rechercher(
        self,
        *,
        terme: str | None = None,
        region: str | None = None,
        agence: str | None = None,
        codes=(),
        pagination: PaginationParams | None = None,
    ) -> Page[Itineraire]:
        params = pagination or PaginationParams()
        trouves = list(self._e.itineraires.values())

        if codes:
            retenus = {c.valeur for c in codes}
            trouves = [i for i in trouves if i.code.valeur in retenus]

        if terme:
            motif = terme.strip().lower()
            trouves = [
                i
                for i in trouves
                if motif in str(i.code).lower()
                or motif in (i.libelle or "").lower()
                or motif in (i.agence or "").lower()
            ]
        if agence:
            trouves = [i for i in trouves if i.agence == agence]

        debut = params.offset
        return Page(
            elements=trouves[debut : debut + params.limite],
            total=len(trouves),
            page=params.page,
            taille=params.taille,
        )

    async def enregistrer_en_lot(self, itineraires: Iterable[Itineraire]) -> int:
        total = 0
        for itineraire in itineraires:
            self._e.itineraires[itineraire.code.valeur] = itineraire
            total += 1
        return total


class _Affectations:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def par_id(self, affectation_id: UUID) -> Affectation | None:
        return self._e.affectations.get(affectation_id)

    async def lister_du_jour(self, jour: date) -> Sequence[Affectation]:
        return [a for a in self._e.affectations.values() if a.date_travail == jour]

    async def lister_par_agent(
        self, agent_id: UUID, periode: Periode
    ) -> Sequence[Affectation]:
        return [
            a
            for a in self._e.affectations.values()
            if a.agent_id == agent_id and periode.contient(a.date_travail)
        ]

    async def existe_deja(
        self, agent_id: UUID, code: CodeItineraire, jour: date
    ) -> bool:
        return any(
            a.agent_id == agent_id
            and a.itineraire_code == code
            and a.date_travail == jour
            for a in self._e.affectations.values()
        )

    async def enregistrer(self, affectation: Affectation) -> None:
        self._e.affectations[affectation.id] = affectation


class _Lignes:
    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot

    async def par_id(self, ligne_id: UUID) -> LigneBordereau | None:
        return self._e.lignes.get(ligne_id)

    def _filtrer(self, filtre: FiltreBordereau) -> list[LigneBordereau]:
        lignes = list(self._e.lignes.values())

        if filtre.recherche:
            motif = filtre.recherche.lower()
            lignes = [
                l
                for l in lignes
                if motif in (l.nom_client or "").lower()
                or motif in l.service_no.valeur
            ]
        if filtre.periode:
            lignes = [l for l in lignes if filtre.periode.contient(l.date_collecte)]
        if filtre.statuts:
            lignes = [l for l in lignes if l.statut in filtre.statuts]
        if filtre.verdicts:
            lignes = [l for l in lignes if l.verdict in filtre.verdicts]
        if filtre.itineraires:
            lignes = [l for l in lignes if l.code_itineraire in filtre.itineraires]
        if filtre.agent_ids:
            lignes = [l for l in lignes if l.agent_id in filtre.agent_ids]

        # La recherche colonne par colonne, comme la loupe d'un tableur.
        for critere, lecture in (
            (filtre.service_no, lambda l: l.service_no.valeur),
            (filtre.nom_client, lambda l: l.nom_client),
            (filtre.ref_geo, lambda l: str(l.ref_geo) if l.ref_geo else None),
            (filtre.numero_compteur, lambda l: l.numero_compteur),
            (
                filtre.numero_collecte,
                lambda l: l.numero_collecte.valeur if l.numero_collecte else None,
            ),
            (filtre.responsable_nom, lambda l: l.valide_par_nom),
        ):
            if critere and critere.strip():
                motif = critere.strip().lower()
                lignes = [l for l in lignes if motif in (lecture(l) or "").lower()]

        if filtre.rapports:
            lignes = [l for l in lignes if l.rapport in filtre.rapports]
        if filtre.identites:
            lignes = [l for l in lignes if l.identite in filtre.identites]
        if filtre.verifie_terrain is not None:
            lignes = [
                l for l in lignes if l.verifie_terrain is filtre.verifie_terrain
            ]

        return sorted(lignes, key=lambda l: (l.date_collecte, str(l.ref_geo)))

    async def rechercher_par_numero(
        self, numero: str, *, code_itineraire: int | None = None
    ) -> list[LigneBordereau]:
        trouvees = [
            l
            for l in self._e.lignes.values()
            if l.numero_collecte and l.numero_collecte.valeur == numero
        ]
        if code_itineraire is not None:
            trouvees = [
                l
                for l in trouvees
                if l.code_itineraire and l.code_itineraire.valeur == code_itineraire
            ]
        return trouvees

    async def rechercher(
        self, filtre: FiltreBordereau, pagination: PaginationParams
    ) -> Page[LigneBordereau]:
        lignes = self._filtrer(filtre)
        debut = pagination.offset
        return Page(
            elements=lignes[debut : debut + pagination.limite],
            total=len(lignes),
            page=pagination.page,
            taille=pagination.taille,
        )

    async def lister_pour_export(
        self, filtre: FiltreBordereau, limite: int
    ) -> Sequence[LigneBordereau]:
        return self._filtrer(filtre)[:limite]

    async def lister_par_affectation(
        self, affectation_id: UUID
    ) -> Sequence[LigneBordereau]:
        return [
            l for l in self._e.lignes.values() if l.affectation_id == affectation_id
        ]

    async def enregistrer(self, ligne: LigneBordereau) -> None:
        self._e.lignes[ligne.id] = ligne

    async def enregistrer_en_lot(self, lignes: Iterable[LigneBordereau]) -> int:
        total = 0
        for ligne in lignes:
            self._e.lignes[ligne.id] = ligne
            total += 1
        return total


class UnitOfWorkMemoire:
    """Unité de travail en mémoire.

    `valider` et `annuler` ne font rien : le double ne simule pas
    l'atomicité, il vérifie que les cas d'usage appellent bien le bon port au
    bon moment.
    """

    def __init__(self, entrepot: EntrepotMemoire) -> None:
        self._e = entrepot
        self.commits = 0

    async def __aenter__(self) -> "UnitOfWorkMemoire":
        self.utilisateurs = _Utilisateurs(self._e)
        self.agents = _Agents(self._e)
        self.clients = _Clients(self._e)
        self.agences = _Agences(self._e)
        self.audit = _Audit(self._e)
        self.restrictions = _Restrictions(self._e)
        self.itineraires = _Itineraires(self._e)
        self.affectations = _Affectations(self._e)
        self.lignes = _Lignes(self._e)
        return self

    async def __aexit__(
        self,
        type_exception: type[BaseException] | None,
        exception: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        return None

    async def valider(self) -> None:
        self.commits += 1

    async def annuler(self) -> None:
        return None
