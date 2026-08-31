"""Politique d'habilitation : RBAC pour le *quoi*, ABAC pour le *sur quoi*.

Les deux mécanismes répondent à deux questions distinctes, et les confondre est
la source habituelle des fuites de données :

* **RBAC**, le rôle autorise-t-il cette action ? Réponse booléenne, tranchée
  par `autorise()`.
* **ABAC**, sur quel périmètre de données ? Réponse non booléenne : la
  politique **rétrécit le filtre** de la requête au lieu de valider un accès
  déjà formulé.

Ce second point est délibéré. Un contrôle de la forme « cet agent a-t-il le
droit de voir cette ligne ? » doit être appelé partout, et il suffit de
l'oublier une fois pour tout exposer. En imposant le rétrécissement en amont,
une requête d'agent ne peut structurellement pas désigner les lignes d'un
autre : le périmètre est réécrit avant d'atteindre la base.

S'y ajoute une **hiérarchie** : un rôle n'agit que sur les rôles strictement
inférieurs au sien. C'est ce qui empêche un administrateur SOCADEL de toucher
au compte du super utilisateur NEXT LTD qui l'a créé.
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
    ITINERAIRE_GERER = "itineraire:gerer"

    # Répertoire des agents de terrain
    AGENT_LIRE = "agent:lire"
    AGENT_CREER = "agent:creer"
    AGENT_MODIFIER = "agent:modifier"
    AGENT_SUPPRIMER = "agent:supprimer"

    # Comptes de connexion
    COMPTE_LIRE = "compte:lire"
    COMPTE_CREER = "compte:creer"
    COMPTE_MODIFIER = "compte:modifier"
    COMPTE_SUPPRIMER = "compte:supprimer"
    COMPTE_APPROUVER = "compte:approuver"
    COMPTE_REINITIALISER = "compte:reinitialiser"
    COMPTE_CHANGER_ROLE = "compte:changer-role"

    # Périmètres territoriaux
    PERIMETRE_DEFINIR = "perimetre:definir"

    # Import de fichiers
    IMPORT_EXECUTER = "import:executer"

    # Tableau de bord
    ANALYTICS_CONSULTER = "analytics:consulter"
    ANALYTICS_NATIONAL = "analytics:national"

    # Exploitation de la plateforme
    REFERENTIEL_ADMINISTRER = "referentiel:administrer"

    # Son propre profil
    PROFIL_CONSULTER = "profil:consulter"
    PROFIL_MODIFIER = "profil:modifier"


#: Rang hiérarchique. Il ne décide pas des permissions (c'est la matrice qui
#: s'en charge) mais de **sur qui** on peut agir : un rôle n'atteint que les
#: rangs strictement inférieurs au sien.
RANG: dict[Role, int] = {
    Role.SUPER_UTILISATEUR: 3,
    Role.ADMINISTRATEUR: 2,
    Role.SUPERVISEUR: 1,
    Role.AGENT_TERRAIN: 0,
}

#: Permissions du superviseur, réutilisées par les rôles supérieurs.
_SUPERVISEUR = frozenset(
    {
        Permission.BORDEREAU_LIRE,
        Permission.BORDEREAU_DECLARER,
        Permission.BORDEREAU_VERIFIER,
        Permission.BORDEREAU_EXPORTER,
        Permission.ITINERAIRE_LIRE,
        Permission.ITINERAIRE_AFFECTER,
        Permission.ITINERAIRE_IMPRIMER,
        # Le terrain ouvre des zones plus vite qu'un import ne se rejoue : le
        # superviseur tient donc lui-même son répertoire de tournées.
        Permission.ITINERAIRE_GERER,
        Permission.AGENT_LIRE,
        Permission.AGENT_CREER,
        Permission.AGENT_MODIFIER,
        Permission.AGENT_SUPPRIMER,
        Permission.IMPORT_EXECUTER,
        Permission.ANALYTICS_CONSULTER,
        Permission.PROFIL_CONSULTER,
        Permission.PROFIL_MODIFIER,
    }
)

#: Ce que l'administrateur SOCADEL ajoute au superviseur : la gouvernance des
#: accès de ses équipes, et la vue nationale sur les chiffres.
_ADMINISTRATEUR = _SUPERVISEUR | {
    Permission.COMPTE_LIRE,
    Permission.COMPTE_CREER,
    Permission.COMPTE_MODIFIER,
    Permission.COMPTE_SUPPRIMER,
    Permission.COMPTE_APPROUVER,
    Permission.COMPTE_REINITIALISER,
    Permission.PERIMETRE_DEFINIR,
    Permission.ANALYTICS_NATIONAL,
}

#: Matrice RBAC. Chaque rôle reçoit exactement ce dont son métier a besoin.
#:
#: L'agent de terrain est volontairement le plus pauvre : sur la plateforme,
#: il se connecte et consulte ses propres chiffres, rien d'autre. Son travail
#: se fait sur le terrain, avec le bordereau papier.
MATRICE: dict[Role, frozenset[Permission]] = {
    # NEXT LTD, éditeur de la plateforme. Seul à pouvoir changer un rôle et à
    # administrer le référentiel : ce sont les deux leviers qui engagent le
    # fonctionnement du système lui-même, pas seulement son exploitation.
    Role.SUPER_UTILISATEUR: frozenset(Permission),
    Role.ADMINISTRATEUR: frozenset(_ADMINISTRATEUR),
    Role.SUPERVISEUR: _SUPERVISEUR,
    Role.AGENT_TERRAIN: frozenset(
        {
            Permission.BORDEREAU_LIRE,
            Permission.ANALYTICS_CONSULTER,
            Permission.PROFIL_CONSULTER,
        }
    ),
}


class AccesRefuse(DomainError):
    """Le rôle ne porte pas la permission demandée, ou vise trop haut."""

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
    """Périmètre territorial. `None` pour les rôles à portée nationale."""

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
    def rang(self) -> int:
        return RANG.get(self.role, 0)

    @property
    def est_agent(self) -> bool:
        return self.role is Role.AGENT_TERRAIN

    @property
    def est_superviseur(self) -> bool:
        return self.role is Role.SUPERVISEUR

    @property
    def porte_nationale(self) -> bool:
        """Vrai pour les rôles qui voient l'ensemble du territoire."""
        return self.role in (Role.SUPER_UTILISATEUR, Role.ADMINISTRATEUR)


def restreindre(contexte: ContexteAcces, filtre):
    """Garde ABAC : réécrit un `FiltreBordereau` au périmètre de l'appelant.

    C'est le point de passage obligé de toute lecture de bordereau ou de KPI.
    Un agent y voit son `agent_id` imposé, quoi qu'il ait demandé ; un
    superviseur y voit son agence imposée.

    Args:
        contexte: identité effective de l'appelant.
        filtre: le `FiltreBordereau` demandé.

    Returns:
        Le filtre rétréci. Jamais élargi.

    Raises:
        AccesRefuse: si le contexte ne permet de délimiter aucun périmètre sûr.
    """
    if contexte.porte_nationale:
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
    # SOCADEL compte des agences dans tout le pays, et un superviseur de Kribi
    # n'a pas à voir la production de Ngaoundéré.
    if contexte.region is None and contexte.agence is None:
        raise AccesRefuse(
            "Aucun périmètre n'est défini pour ce superviseur. "
            "Un administrateur doit lui attribuer une région ou une agence."
        )

    restreint = filtre
    if contexte.region is not None:
        restreint = replace(restreint, region=contexte.region)
    if contexte.agence is not None:
        restreint = replace(restreint, agence=contexte.agence)
    return restreint


def dans_le_perimetre(
    contexte: ContexteAcces, region: str | None, agence: str | None
) -> bool:
    """Vrai si un objet rattaché à ce territoire relève de l'appelant.

    Sert aux entités que le filtre de bordereau ne couvre pas : fiches agent,
    itinéraires, comptes.
    """
    if contexte.porte_nationale:
        return True
    if contexte.agence is not None and agence != contexte.agence:
        return False
    if contexte.region is not None and region != contexte.region:
        return False
    return True


def peut_agir_sur_role(contexte: ContexteAcces, cible: Role) -> bool:
    """Vrai si l'appelant peut agir sur un compte portant ce rôle.

    La règle est simple et sans exception : **strictement au-dessus**. Un
    administrateur SOCADEL gère ses superviseurs et ses agents, jamais un autre
    administrateur ni le super utilisateur NEXT LTD qui l'a créé.
    """
    return contexte.rang > RANG.get(cible, 0)


def peut_agir_sur_agent(contexte: ContexteAcces, agent_id: UUID) -> bool:
    """Règle ABAC du répertoire des agents.

    Un agent de terrain n'a aucune main sur le répertoire, pas même sur sa
    propre fiche : c'est le superviseur qui la tient.
    """
    if contexte.porte_nationale:
        return True
    if contexte.est_agent:
        return False
    return contexte.a(Permission.AGENT_MODIFIER)


def peut_agir_sur_compte(
    contexte: ContexteAcces, compte_id: UUID, role_cible: Role
) -> bool:
    """Règle ABAC des comptes de connexion.

    Chacun agit sur le sien ; au-delà, la hiérarchie tranche.
    """
    if compte_id == contexte.utilisateur_id:
        return True
    return peut_agir_sur_role(contexte, role_cible)
