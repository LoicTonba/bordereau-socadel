"""Politique d'habilitation : RBAC pour le *quoi*, ABAC pour le *sur quoi*.

Les deux mécanismes répondent à deux questions distinctes, et les confondre est
la source habituelle des fuites de données :

* **RBAC** — le rôle autorise-t-il cette action ? Réponse booléenne, tranchée
  par `autorise()`.
* **ABAC** — sur quel périmètre de données ? Réponse non booléenne : la
  politique **rétrécit le filtre** de la requête au lieu de valider un accès
  déjà formulé.

Ce second point est délibéré. Un contrôle de la forme « cet agent a-t-il le
droit de voir cette ligne ? » doit être appelé partout, et il suffit de
l'oublier une fois pour tout exposer. En imposant le rétrécissement en amont,
une requête d'agent ne peut structurellement pas désigner les lignes d'un
autre : le périmètre est réécrit avant d'atteindre la base.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from uuid import UUID

from ..enums import Role
from ..errors import DomainError


class Permission(str, Enum):
    """Actions élémentaires du système."""

    # Bordereau de collecte
    BORDEREAU_LIRE = "bordereau:lire"
    BORDEREAU_DECLARER = "bordereau:declarer"
    BORDEREAU_VERIFIER = "bordereau:verifier"
    BORDEREAU_EXPORTER = "bordereau:exporter"

    # Itinéraires et affectations
    ITINERAIRE_LIRE = "itineraire:lire"
    ITINERAIRE_AFFECTER = "itineraire:affecter"
    ITINERAIRE_IMPRIMER = "itineraire:imprimer"

    # Répertoire des agents de terrain
    AGENT_LIRE = "agent:lire"
    AGENT_CREER = "agent:creer"
    AGENT_MODIFIER = "agent:modifier"
    AGENT_SUPPRIMER = "agent:supprimer"

    # Comptes de connexion (superviseurs, administrateurs, agents)
    COMPTE_LIRE = "compte:lire"
    COMPTE_CREER = "compte:creer"
    COMPTE_MODIFIER = "compte:modifier"
    COMPTE_SUPPRIMER = "compte:supprimer"

    # Import de fichiers
    IMPORT_EXECUTER = "import:executer"

    # Tableau de bord
    ANALYTICS_CONSULTER = "analytics:consulter"

    # Son propre profil
    PROFIL_CONSULTER = "profil:consulter"
    PROFIL_MODIFIER = "profil:modifier"


#: Matrice RBAC. Chaque rôle reçoit exactement ce dont son métier a besoin.
#:
#: L'agent de terrain est volontairement le plus pauvre : sur la plateforme,
#: il se connecte et consulte ses propres chiffres, rien d'autre. Son travail
#: se fait sur le terrain, avec le bordereau papier.
MATRICE: dict[Role, frozenset[Permission]] = {
    Role.ADMINISTRATEUR: frozenset(Permission),
    Role.SUPERVISEUR: frozenset(
        {
            Permission.BORDEREAU_LIRE,
            Permission.BORDEREAU_DECLARER,
            Permission.BORDEREAU_VERIFIER,
            Permission.BORDEREAU_EXPORTER,
            Permission.ITINERAIRE_LIRE,
            Permission.ITINERAIRE_AFFECTER,
            Permission.ITINERAIRE_IMPRIMER,
            Permission.AGENT_LIRE,
            Permission.AGENT_CREER,
            Permission.AGENT_MODIFIER,
            Permission.AGENT_SUPPRIMER,
            Permission.IMPORT_EXECUTER,
            Permission.ANALYTICS_CONSULTER,
            Permission.PROFIL_CONSULTER,
            Permission.PROFIL_MODIFIER,
        }
    ),
    Role.AGENT_TERRAIN: frozenset(
        {
            Permission.BORDEREAU_LIRE,
            Permission.ANALYTICS_CONSULTER,
            Permission.PROFIL_CONSULTER,
        }
    ),
}


class AccesRefuse(DomainError):
    """Le rôle ne porte pas la permission demandée."""

    code = "acces_refuse"


@dataclass(frozen=True, slots=True)
class ContexteAcces:
    """Identité effective de l'appelant, telle qu'elle sert aux décisions.

    Elle réunit ce que le RBAC consomme (le rôle) et ce que l'ABAC consomme
    (les attributs : agent rattaché, périmètre territorial).
    """

    utilisateur_id: UUID
    role: Role

    agent_id: UUID | None = None
    """Renseigné quand le compte est celui d'un agent de terrain."""

    region: str | None = None
    agence: str | None = None
    """Périmètre territorial d'un superviseur. `None` = périmètre national."""

    def a(self, permission: Permission) -> bool:
        return permission in MATRICE.get(self.role, frozenset())

    def exiger(self, permission: Permission) -> None:
        """Garde RBAC.

        Raises:
            AccesRefuse: si le rôle ne porte pas la permission.
        """
        if not self.a(permission):
            raise AccesRefuse(
                f"Le rôle {self.role.value} n'autorise pas l'action "
                f"« {permission.value} »"
            )

    @property
    def est_agent(self) -> bool:
        return self.role is Role.AGENT_TERRAIN

    @property
    def est_administrateur(self) -> bool:
        return self.role is Role.ADMINISTRATEUR


def restreindre(contexte: ContexteAcces, filtre):
    """Garde ABAC : réécrit un `FiltreBordereau` au périmètre de l'appelant.

    C'est le point de passage obligé de toute lecture de bordereau ou de KPI.
    Un agent y voit son `agent_id` imposé, quoi qu'il ait demandé ; un
    superviseur territorialisé y voit sa région imposée.

    Args:
        contexte: identité effective de l'appelant.
        filtre: le `FiltreBordereau` demandé.

    Returns:
        Le filtre rétréci. Jamais élargi.
    """
    if contexte.est_administrateur:
        return filtre

    if contexte.est_agent:
        if contexte.agent_id is None:
            # Un compte agent sans agent rattaché ne peut rien voir : renvoyer
            # le filtre inchangé exposerait tout le bordereau.
            raise AccesRefuse(
                "Ce compte agent n'est rattaché à aucun agent de terrain"
            )
        # L'agent ne voit que sa propre production, quoi qu'il demande.
        return replace(filtre, agent_ids=(contexte.agent_id,))

    # Superviseur : son périmètre territorial prime sur ce qu'il a demandé.
    restreint = filtre
    if contexte.region is not None:
        restreint = replace(restreint, region=contexte.region)
    if contexte.agence is not None:
        restreint = replace(restreint, agence=contexte.agence)
    return restreint


def peut_agir_sur_agent(contexte: ContexteAcces, agent_id: UUID) -> bool:
    """Règle ABAC du répertoire des agents.

    Un agent de terrain n'a aucune main sur le répertoire, pas même sur sa
    propre fiche : c'est le superviseur qui la tient.
    """
    if contexte.est_administrateur:
        return True
    if contexte.est_agent:
        return False
    return contexte.a(Permission.AGENT_MODIFIER)


def peut_agir_sur_compte(contexte: ContexteAcces, compte_id: UUID) -> bool:
    """Règle ABAC des comptes de connexion.

    Seul l'administrateur gère les comptes d'autrui ; chacun peut agir sur le
    sien.
    """
    if contexte.est_administrateur:
        return True
    return compte_id == contexte.utilisateur_id
