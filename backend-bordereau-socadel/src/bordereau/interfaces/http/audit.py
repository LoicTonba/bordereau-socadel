"""Intercepteur d'audit : il consigne les gestes, sans en gêner aucun.

Pourquoi ici et pas dans chaque cas d'usage. Répartir l'écriture du journal
sur cinquante cas d'usage garantirait qu'on en oublie un, et le jour où on
l'oublie, c'est justement celui qu'on cherchera. Un seul point de passage, la
requête HTTP, couvre tout ce qui entre par l'API.

Ce qui est consigné, et ce qui ne l'est pas.

Seules les requêtes qui **écrivent** le sont, plus les tentatives de connexion.
Journaliser chaque consultation noierait le signal : un tableau de bord ouvert
deux minutes produit des dizaines de lectures, et personne ne cherche jamais
« qui a regardé le tableau de bord ».

Le corps de la requête n'est **jamais** conservé. Il porte des mots de passe,
des numéros de téléphone, des noms de clients ; les recopier dans un journal
créerait une seconde base de données personnelles, moins protégée que la
première et consultable par d'autres personnes. Le verbe, le chemin et l'issue
suffisent à répondre à « qui a fait quoi ».
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ...application.errors import JetonInvalide
from ...domain.entities import TraceAudit

logger = logging.getLogger(__name__)

#: Verbes qui modifient l'état. Le reste n'est pas consigné.
VERBES_ECRITURE = frozenset({"POST", "PATCH", "PUT", "DELETE"})

#: Chemins consignés même en lecture : ils portent une décision d'accès.
CHEMINS_SENSIBLES = ("/auth/connexion", "/comptes/verification")


class IntercepteurAudit(BaseHTTPMiddleware):
    """Consigne chaque geste, après coup et sans jamais le faire échouer."""

    async def dispatch(self, request: Request, appeler_suivant):
        reponse = await appeler_suivant(request)

        if not _a_consigner(request):
            return reponse

        try:
            await _consigner(request, reponse.status_code)
        except Exception:
            # Le journal observe, il ne gouverne pas : un incident ici ne doit
            # pas transformer une opération réussie en erreur pour l'appelant.
            logger.exception("Trace d'audit non consignée pour %s", request.url.path)

        return reponse


def _a_consigner(request: Request) -> bool:
    if request.method in VERBES_ECRITURE:
        return True
    return any(motif in request.url.path for motif in CHEMINS_SENSIBLES)


async def _consigner(request: Request, statut: int) -> None:
    container = getattr(request.app.state, "container", None)
    if container is None:
        return

    utilisateur = await _auteur(request, container)
    chemin = request.url.path

    # Une connexion réussie crée la session : la requête n'en portait aucune,
    # et la route a donc déposé l'auteur dans l'état de la requête.
    souffle = getattr(request.state, "audit_identifiant", None)

    await container.consigner_trace().executer(
        TraceAudit(
            quand=datetime.now(tz=timezone.utc),
            action=f"{request.method} {_sans_prefixe(chemin)}",
            cible=_cible(chemin),
            utilisateur_id=utilisateur.id if utilisateur else None,
            identifiant=(
                utilisateur.identifiant if utilisateur else souffle
            ),
            role=(
                utilisateur.role.value
                if utilisateur
                else getattr(request.state, "audit_role", None)
            ),
            statut_http=statut,
            adresse_ip=_adresse(request),
        )
    )


async def _auteur(request: Request, container):
    """Qui a agi, si la requête portait une session valide.

    Une connexion refusée n'a pas d'auteur : c'est précisément l'information
    utile, et la trace la conserve avec son code d'erreur.
    """
    entete = request.headers.get("authorization", "")
    if not entete.lower().startswith("bearer "):
        return None
    try:
        return await container.recuperer_session().executer(entete[7:].strip())
    except (JetonInvalide, Exception):
        return None


def _sans_prefixe(chemin: str) -> str:
    """Retire le préfixe de version : il est le même partout et n'apprend rien."""
    for prefixe in ("/api/v1", "/api"):
        if chemin.startswith(prefixe):
            return chemin[len(prefixe) :] or "/"
    return chemin


def _cible(chemin: str) -> str | None:
    """Le dernier segment identifiant du chemin, quand il y en a un.

    `/territoire/CSC_NDOP/fermeture` a pour cible `CSC_NDOP`, pas `fermeture` :
    on cherche ce sur quoi le geste a porté, pas le nom du geste.
    """
    segments = [s for s in _sans_prefixe(chemin).split("/") if s]
    if len(segments) < 2:
        return None

    # Le dernier segment est souvent un verbe métier ; on remonte alors d'un
    # cran pour trouver l'identifiant qu'il qualifie.
    for segment in reversed(segments[1:]):
        if not segment.isalpha() or segment.isupper():
            return segment
    return segments[1]


def _adresse(request: Request) -> str | None:
    """L'adresse de l'appelant, en tenant compte d'un éventuel proxy."""
    transmise = request.headers.get("x-forwarded-for")
    if transmise:
        # Le premier élément est le client d'origine ; les suivants sont les
        # relais traversés.
        return transmise.split(",")[0].strip()[:45]
    return request.client.host if request.client else None
