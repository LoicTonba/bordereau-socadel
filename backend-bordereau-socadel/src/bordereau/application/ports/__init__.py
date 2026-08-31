"""Ports : contrats que l'infrastructure doit satisfaire.

La règle de dépendance de la clean architecture veut que le code métier ne
pointe jamais vers un détail technique. Ces protocoles sont le point de
retournement : l'application les déclare, l'infrastructure s'y conforme.
"""

from .analytics import RequetesAnalytiques
from .messagerie import Courriel, GenerateurJeton, Messagerie
from .fichiers import (
    ExportateurCsv,
    ExportateurPdf,
    GenerateurModeleImport,
    GenerateurModeleTerrain,
    LecteurTabulaire,
)
from .repositories import (
    AffectationRepository,
    AgentRepository,
    ClientRepository,
    ItineraireRepository,
    LigneBordereauRepository,
    UtilisateurRepository,
)
from .securite import ContenuJeton, HacheurMotDePasse, Horloge, ServiceJeton
from .unit_of_work import UnitOfWork

__all__ = [
    "AffectationRepository",
    "AgentRepository",
    "ClientRepository",
    "ContenuJeton",
    "Courriel",
    "GenerateurJeton",
    "ExportateurCsv",
    "ExportateurPdf",
    "GenerateurModeleImport",
    "GenerateurModeleTerrain",
    "HacheurMotDePasse",
    "Horloge",
    "ItineraireRepository",
    "LecteurTabulaire",
    "LigneBordereauRepository",
    "Messagerie",
    "RequetesAnalytiques",
    "ServiceJeton",
    "UnitOfWork",
    "UtilisateurRepository",
]
