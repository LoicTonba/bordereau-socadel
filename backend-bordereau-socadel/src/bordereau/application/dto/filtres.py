"""DTO de filtrage du tableau de bordereau.

Un seul objet de filtre sert le listing paginé, les exports CSV/PDF et les KPI :
c'est ce qui garantit qu'un export contient exactement ce que le superviseur
voit à l'écran.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ...domain.enums import (
    Identite,
    Rapport,
    Responsable,
    StatutCollecte,
    VerdictVerification,
)
from ...domain.value_objects import CodeItineraire, Periode


@dataclass(frozen=True, slots=True)
class FiltreBordereau:
    """Critères de sélection des lignes de bordereau."""

    recherche: str | None = None
    """Recherche plein texte sur le nom, le SERVICE_NO, le compteur ou la REF_GEO."""

    # --- Recherche colonne par colonne -----------------------------------
    # La recherche globale répond à « où est ce client », les colonnes à
    # « montre-moi cette tournée-là ». Un superviseur qui tient trois cents
    # lignes cherche rarement au hasard : il sait dans quelle colonne regarder,
    # et taper le motif ailleurs ne ferait que ramener du bruit.
    service_no: str | None = None
    nom_client: str | None = None
    ref_geo: str | None = None
    numero_compteur: str | None = None
    numero_collecte: str | None = None
    responsable_nom: str | None = None
    """Le nom porté par la colonne Responsable, tel qu'il s'affiche."""

    periode: Periode | None = None
    statuts: tuple[StatutCollecte, ...] = ()
    verdicts: tuple[VerdictVerification, ...] = ()
    responsables: tuple[Responsable, ...] = ()
    rapports: tuple[Rapport, ...] = ()
    identites: tuple[Identite, ...] = ()
    verifie_terrain: bool | None = None
    """Filtre sur la colonne Check : cochée, pas cochée, ou indifférent."""

    itineraires: tuple[CodeItineraire, ...] = ()
    agent_ids: tuple[UUID, ...] = ()
    region: str | None = None
    division: str | None = None
    agence: str | None = None

    @property
    def est_vide(self) -> bool:
        """Vrai si aucun critère n'est posé — utile pour avertir l'utilisateur
        avant un export qui porterait sur tout le référentiel."""
        return not any(
            (
                self.recherche,
                self.service_no,
                self.nom_client,
                self.ref_geo,
                self.numero_compteur,
                self.numero_collecte,
                self.responsable_nom,
                self.rapports,
                self.identites,
                self.verifie_terrain,
                self.periode,
                self.statuts,
                self.verdicts,
                self.responsables,
                self.itineraires,
                self.agent_ids,
                self.region,
                self.division,
                self.agence,
            )
        )


@dataclass(frozen=True, slots=True)
class FiltreItineraire:
    """Critères de recherche d'itinéraires, pour l'écran d'affectation."""

    terme: str | None = None
    region: str | None = None
    agence: str | None = None

    codes: tuple[CodeItineraire, ...] = ()
    """Restriction à des tournées précises.

    Posée par le cas d'usage pour un agent de terrain : il ne voit que ce qui
    lui a été confié. Vide, le filtre ne restreint rien.
    """
