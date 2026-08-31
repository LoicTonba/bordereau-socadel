"""Cas d'usage : la recherche unique, ouverte à tous les profils.

Un utilisateur qui cherche un client ne sait pas toujours quel écran l'affiche,
ni sous quel filtre. La recherche globale répond à la question posée, pas à
celle que l'application aurait aimé recevoir : on tape un nom, un contrat, un
matricule ou un code de tournée, et on obtient ce à quoi on a droit.

Trois principes tiennent ce cas d'usage.

Il ne contourne rien. Chaque volet est délégué au cas d'usage qui le sert
déjà, avec le contexte de l'appelant : les permissions et le rétrécissement
ABAC s'appliquent exactement comme sur l'écran correspondant. Un agent de
terrain ne trouve donc que ses propres lignes, un superviseur que son agence.

Il est silencieux sur ce qu'on n'a pas le droit de voir. Un volet auquel
l'appelant n'a pas accès n'est pas signalé comme refusé, il est simplement
absent : dire « vous n'avez pas accès aux comptes » renseignerait sur
l'existence d'un écran, et sur ce que d'autres peuvent faire.

Il est borné. Quelques résultats par volet, jamais une page entière : la
recherche oriente vers l'écran qui détient la réponse complète, elle ne le
remplace pas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ...domain.securite import ContexteAcces
from ...domain.securite.permissions import AccesRefuse
from ..dto import FiltreBordereau, FiltreItineraire, PaginationParams

#: Résultats rendus par volet. Au-delà, la liste cesse d'orienter et devient
#: un second tableau, moins bon que celui de l'écran dédié.
PAR_VOLET = 5

#: En deçà, la recherche ramènerait un échantillon arbitraire du référentiel.
LONGUEUR_MIN = 2


@dataclass(frozen=True, slots=True)
class Trouvaille:
    """Un résultat, réduit à ce qu'il faut pour choisir et pour y aller."""

    titre: str
    detail: str
    chemin: str


@dataclass(frozen=True, slots=True)
class Volet:
    """Les résultats d'une famille, avec son libellé d'affichage."""

    cle: str
    libelle: str
    resultats: tuple[Trouvaille, ...]


@dataclass(frozen=True, slots=True)
class ResultatRecherche:
    terme: str
    volets: tuple[Volet, ...] = field(default=())

    @property
    def total(self) -> int:
        return sum(len(v.resultats) for v in self.volets)


class RechercheGlobale:
    """Interroge les écrans que l'appelant peut ouvrir, et rien d'autre."""

    def __init__(
        self,
        lister_bordereau,
        rechercher_itineraires,
        lister_agents,
        lister_comptes,
    ) -> None:
        self._bordereau = lister_bordereau
        self._itineraires = rechercher_itineraires
        self._agents = lister_agents
        self._comptes = lister_comptes

    async def executer(
        self, contexte: ContexteAcces, terme: str
    ) -> ResultatRecherche:
        terme = terme.strip()
        if len(terme) < LONGUEUR_MIN:
            return ResultatRecherche(terme=terme)

        volets = []
        for construire in (
            self._volet_bordereau,
            self._volet_itineraires,
            self._volet_agents,
            self._volet_comptes,
        ):
            volet = await _sans_bruit(construire(contexte, terme))
            if volet and volet.resultats:
                volets.append(volet)

        return ResultatRecherche(terme=terme, volets=tuple(volets))

    # --- Volets -----------------------------------------------------------

    async def _volet_bordereau(self, contexte: ContexteAcces, terme: str) -> Volet:
        page = await self._bordereau.executer(
            contexte,
            FiltreBordereau(recherche=terme),
            PaginationParams(page=1, taille=PAR_VOLET),
        )
        return Volet(
            cle="bordereau",
            libelle="Lignes de bordereau",
            resultats=tuple(
                Trouvaille(
                    titre=ligne.nom_client or ligne.service_no.valeur,
                    detail=(
                        f"Contrat {ligne.service_no.valeur}"
                        + (f" · itinéraire {ligne.code_itineraire.valeur}"
                           if ligne.code_itineraire else "")
                    ),
                    chemin=f"/bordereau?recherche={ligne.service_no.valeur}",
                )
                for ligne in page.elements
            ),
        )

    async def _volet_itineraires(self, contexte: ContexteAcces, terme: str) -> Volet:
        page = await self._itineraires.executer(
            FiltreItineraire(terme=terme),
            PaginationParams(page=1, taille=PAR_VOLET),
            contexte,
        )
        return Volet(
            cle="itineraires",
            libelle="Itinéraires",
            resultats=tuple(
                Trouvaille(
                    titre=f"Itinéraire {itineraire.code.valeur}",
                    detail=(
                        f"{itineraire.agence or 'agence inconnue'} · "
                        f"{itineraire.nombre_clients} client(s)"
                    ),
                    chemin=f"/itineraires?terme={itineraire.code.valeur}",
                )
                for itineraire in page.elements
            ),
        )

    async def _volet_agents(self, contexte: ContexteAcces, terme: str) -> Volet:
        agents = await self._agents.executer(contexte, actifs_seulement=False)
        recherche = terme.casefold()
        retenus = [
            agent
            for agent in agents
            if recherche in agent.nom_complet.casefold()
            or recherche in agent.matricule.casefold()
        ][:PAR_VOLET]

        return Volet(
            cle="agents",
            libelle="Agents de terrain",
            resultats=tuple(
                Trouvaille(
                    titre=agent.nom_complet,
                    detail=f"{agent.matricule}"
                    + (f" · {agent.zone_rattachement}" if agent.zone_rattachement else ""),
                    chemin=f"/agents/{agent.id}",
                )
                for agent in retenus
            ),
        )

    async def _volet_comptes(self, contexte: ContexteAcces, terme: str) -> Volet:
        comptes = await self._comptes.executer(contexte)
        recherche = terme.casefold()
        retenus = [
            compte
            for compte in comptes
            if recherche in compte.nom_complet.casefold()
            or recherche in compte.identifiant.casefold()
            or recherche in (compte.email or "").casefold()
        ][:PAR_VOLET]

        return Volet(
            cle="comptes",
            libelle="Comptes",
            resultats=tuple(
                Trouvaille(
                    titre=compte.nom_complet,
                    detail=f"{compte.email} · {compte.role.value.lower().replace('_', ' ')}",
                    chemin="/comptes",
                )
                for compte in retenus
            ),
        )


async def _sans_bruit(coroutine):
    """Exécute un volet, et l'oublie si l'appelant n'y a pas droit.

    Un refus n'est pas une erreur ici : c'est la réponse normale pour un profil
    à qui l'écran n'est pas ouvert. Le laisser remonter transformerait une
    recherche partielle en échec complet.
    """
    try:
        return await coroutine
    except AccesRefuse:
        return None
