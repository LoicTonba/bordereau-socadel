"""Entité : agence SOCADEL, maille de base du périmètre.

L'agence est le point où les distributeurs prennent leurs tournées. C'est aussi
ce que porte un compte de superviseur comme périmètre, et ce que le sélecteur
de connexion propose.

Elle était jusqu'ici déduite du référentiel clients, ce qui la rendait
immuable : SOCADEL ne pouvait ni ouvrir une agence dans une zone nouvelle, ni
en fermer une dont l'accès devient impossible, sans attendre un nouvel import.
Elle devient donc une entité à part entière, que l'application tient elle-même.

Fermer plutôt que supprimer, chaque fois que c'est possible. Une agence fermée
disparaît des listes de travail mais reste attachée à la production passée et
aux comptes qui la portent ; la supprimer laisserait des périmètres orphelins.
Le motif est conservé : « zone rendue inaccessible » n'est pas « erreur de
saisie », et l'un se rouvre quand l'autre non.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from ..errors import RegleMetierViolee


@dataclass(slots=True)
class Agence:
    """Un centre de service client, replacé dans sa division et sa direction."""

    nom: str
    region: str | None = None
    division: str | None = None
    #: Vraie tant que l'agence accueille des tournées.
    ouverte: bool = True
    #: Pourquoi elle a été fermée. Vide tant qu'elle est ouverte.
    motif_fermeture: str | None = None
    fermee_le: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        nom = (self.nom or "").strip().upper()
        if not nom:
            raise RegleMetierViolee("Le nom de l'agence est obligatoire")
        # Le nom est la clé : il est porté tel quel par les comptes, les
        # itinéraires et le référentiel. On le normalise une fois, ici.
        self.nom = nom
        self.region = _propre(self.region)
        self.division = _propre(self.division)

    @property
    def territoire(self) -> str:
        """Rattachement lisible, pour une liste ou un sélecteur."""
        elements = [e for e in (self.division, self.region) if e]
        return " · ".join(elements) or "Territoire non renseigné"

    def fermer(self, motif: str, quand: datetime) -> None:
        """Retire l'agence des listes de travail, sans effacer son passé.

        Le motif est exigé : une agence fermée sans raison connue ne se rouvre
        jamais de bon cœur, faute de savoir ce qui avait justifié la fermeture.
        """
        motif = (motif or "").strip()
        if not motif:
            raise RegleMetierViolee(
                "Fermer une agence demande un motif : insécurité, "
                "réorganisation, fusion avec une autre agence."
            )
        self.ouverte = False
        self.motif_fermeture = motif
        self.fermee_le = quand

    def rouvrir(self) -> None:
        self.ouverte = True
        self.motif_fermeture = None
        self.fermee_le = None


def _propre(valeur: str | None) -> str | None:
    """Une chaîne vide est une absence de valeur, pas une valeur vide."""
    if valeur is None:
        return None
    texte = valeur.strip().upper()
    return texte or None
