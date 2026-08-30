"""Dépendances FastAPI : conteneur, identité de l'appelant, filtres.

Ce module traduit le protocole HTTP en objets applicatifs. C'est la seule
frontière où l'on parle de requêtes, d'en-têtes et de paramètres d'URL.

Les décisions d'habilitation, elles, ne sont **pas** prises ici : la route se
contente de fournir le `ContexteAcces`, et ce sont les cas d'usage qui
tranchent. Un futur script d'administration bénéficiera donc des mêmes règles.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Query, Request

from ...application.dto import FiltreBordereau, PaginationParams
from ...application.errors import JetonInvalide
from ...domain.entities import Utilisateur
from ...domain.enums import Responsable, StatutCollecte, VerdictVerification
from ...domain.securite import ContexteAcces
from ...domain.value_objects import CodeItineraire, Periode
from ...infrastructure.container import Container


def get_container(request: Request) -> Container:
    """Le conteneur est construit une fois au démarrage et porté par l'app."""
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


async def utilisateur_courant(
    container: ContainerDep,
    authorization: Annotated[str | None, Header()] = None,
) -> Utilisateur:
    """Résout le porteur du jeton `Authorization: Bearer <jeton>`.

    Raises:
        JetonInvalide: en-tête absent, mal formé, ou session invalide.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise JetonInvalide("Authentification requise")

    jeton = authorization[7:].strip()
    if not jeton:
        raise JetonInvalide("Authentification requise")

    return await container.recuperer_session().executer(jeton)


UtilisateurDep = Annotated[Utilisateur, Depends(utilisateur_courant)]


async def contexte_acces(utilisateur: UtilisateurDep) -> ContexteAcces:
    """Identité effective de l'appelant, consommée par les gardes d'accès."""
    return utilisateur.contexte_acces()


ContexteDep = Annotated[ContexteAcces, Depends(contexte_acces)]


def pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    taille: Annotated[int, Query(ge=1, le=200)] = 25,
    tri: Annotated[str | None, Query()] = None,
    ordre: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> PaginationParams:
    return PaginationParams(
        page=page,
        taille=taille,
        tri=tri,
        ordre_descendant=ordre == "desc",
    )


PaginationDep = Annotated[PaginationParams, Depends(pagination)]


def filtre_bordereau(
    recherche: Annotated[str | None, Query(max_length=120)] = None,
    debut: Annotated[date | None, Query()] = None,
    fin: Annotated[date | None, Query()] = None,
    statut: Annotated[list[StatutCollecte] | None, Query()] = None,
    verdict: Annotated[list[VerdictVerification] | None, Query()] = None,
    responsable: Annotated[list[Responsable] | None, Query()] = None,
    itineraire: Annotated[list[int] | None, Query()] = None,
    agent: Annotated[list[UUID] | None, Query()] = None,
    region: Annotated[str | None, Query()] = None,
    division: Annotated[str | None, Query()] = None,
    agence: Annotated[str | None, Query()] = None,
) -> FiltreBordereau:
    """Assemble le filtre commun au listing, aux exports et aux KPI.

    Ce filtre exprime seulement ce que l'appelant *demande*. Le rétrécissement
    au périmètre auquel il a droit est appliqué plus loin, dans les cas
    d'usage : un client ne peut donc pas élargir sa portée par l'URL.
    """
    periode: Periode | None = None
    if debut or fin:
        # Une borne seule reste une borne : on complète l'autre plutôt que
        # d'ignorer le critère.
        periode = Periode(debut or date.min, fin or date.today())

    return FiltreBordereau(
        recherche=recherche,
        periode=periode,
        statuts=tuple(statut or ()),
        verdicts=tuple(verdict or ()),
        responsables=tuple(responsable or ()),
        itineraires=tuple(CodeItineraire(i) for i in (itineraire or ())),
        agent_ids=tuple(agent or ()),
        region=region,
        division=division,
        agence=agence,
    )


FiltreDep = Annotated[FiltreBordereau, Depends(filtre_bordereau)]


def periode_analytique(
    debut: Annotated[date | None, Query()] = None,
    fin: Annotated[date | None, Query()] = None,
    jours: Annotated[int, Query(ge=1, le=366)] = 14,
) -> Periode:
    """Fenêtre d'observation du tableau de bord et du portefeuille."""
    borne_haute = fin or date.today()
    if debut is not None:
        return Periode(debut, borne_haute)
    return Periode.derniers_jours(borne_haute, jours)


PeriodeDep = Annotated[Periode, Depends(periode_analytique)]
