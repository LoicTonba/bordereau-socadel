"""Cas d'usage : génération du bordereau papier remis à l'agent de terrain.

Le superviseur imprime ce document et le confie à l'agent : *« le superviseur
pourra exporter en PDF son template de travail que l'agent de terrain imprimera
pour aller faire le relevé des numéros, car ils maîtrisent déjà les maisons et
les parcours des itinéraires »*.

La mise en page reproduit `bordereau.xlsx / Feuil3` : un bloc par itinéraire,
en-tête `ITINERAIRE / Total client / OK-MRA`, colonnes REF GEO / METER_NO /
NOMS / CONTRAT / RAPPORT — la dernière laissée vide pour l'écriture.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ....domain.securite import ContexteAcces, Permission
from ....domain.value_objects import CodeItineraire, Periode
from ...errors import RessourceIntrouvable
from ...ports import ExportateurPdf, UnitOfWork

#: Date à compléter à la main quand aucune journée n'est précisée.
DATE_A_REMPLIR = "____ / ____ / __________"
AGENT_A_REMPLIR = "____________________________"


@dataclass(frozen=True, slots=True)
class CommandeTemplateTerrain:
    """Bordereau d'un itinéraire isolé."""

    code_itineraire: int
    agent_id: UUID | None = None
    """Facultatif : pré-remplit le nom de l'agent sur l'en-tête."""


@dataclass(frozen=True, slots=True)
class CommandeTemplateJournee:
    """Bordereau de toutes les tournées confiées à un agent pour une journée."""

    agent_id: UUID
    date_travail: date


@dataclass(frozen=True, slots=True)
class DocumentGenere:
    contenu: bytes
    nom_fichier: str
    type_mime: str


class GenererTemplateTerrain:
    """Produit le PDF imprimable, pour un itinéraire ou pour une journée."""

    def __init__(self, uow: UnitOfWork, pdf: ExportateurPdf) -> None:
        self._uow = uow
        self._pdf = pdf

    async def executer(
        self, contexte: ContexteAcces, commande: CommandeTemplateTerrain
    ) -> DocumentGenere:
        """Assemble le document à partir des clients d'un itinéraire.

        Raises:
            AccesRefuse: le rôle n'autorise pas l'impression.
            RessourceIntrouvable: itinéraire ou agent inconnu.
        """
        from ....infrastructure.files.exporters.pdf_exporter import BlocItineraire

        contexte.exiger(Permission.ITINERAIRE_IMPRIMER)
        code = CodeItineraire.parse(commande.code_itineraire)

        async with self._uow as uow:
            itineraire = await uow.itineraires.par_code(code)
            if itineraire is None:
                raise RessourceIntrouvable("Itinéraire", commande.code_itineraire)

            nom_agent = AGENT_A_REMPLIR
            if commande.agent_id is not None:
                agent = await uow.agents.par_id(commande.agent_id)
                if agent is None:
                    raise RessourceIntrouvable("Agent de terrain", commande.agent_id)
                nom_agent = f"{agent.nom_complet} ({agent.matricule})"

            clients = await uow.clients.par_itineraire(code)

        contenu = self._pdf.generer_template_multi(
            [BlocItineraire(code.valeur, itineraire.designation, clients)],
            nom_agent=nom_agent,
            date_travail=DATE_A_REMPLIR,
        )

        return DocumentGenere(
            contenu=contenu,
            nom_fichier=f"bordereau-terrain-itineraire-{code.valeur}.pdf",
            type_mime="application/pdf",
        )

    async def executer_journee(
        self, contexte: ContexteAcces, commande: CommandeTemplateJournee
    ) -> DocumentGenere:
        """Assemble un document unique couvrant toutes les tournées du jour.

        C'est la forme du classeur source : un agent compétent reçoit plusieurs
        itinéraires et part avec un seul document qui les enchaîne, un bloc par
        tournée.
        """
        from ....infrastructure.files.exporters.pdf_exporter import BlocItineraire

        contexte.exiger(Permission.ITINERAIRE_IMPRIMER)

        async with self._uow as uow:
            agent = await uow.agents.par_id(commande.agent_id)
            if agent is None:
                raise RessourceIntrouvable("Agent de terrain", commande.agent_id)

            affectations = await uow.affectations.lister_par_agent(
                commande.agent_id, Periode.jour(commande.date_travail)
            )

            blocs = []
            for affectation in affectations:
                code = affectation.itineraire_code
                itineraire = await uow.itineraires.par_code(code)
                clients = await uow.clients.par_itineraire(code)
                blocs.append(
                    BlocItineraire(
                        code.valeur,
                        itineraire.designation if itineraire else f"Itinéraire {code}",
                        clients,
                    )
                )

        contenu = self._pdf.generer_template_multi(
            blocs,
            nom_agent=f"{agent.nom_complet} ({agent.matricule})",
            date_travail=commande.date_travail.strftime("%d / %m / %Y"),
        )

        return DocumentGenere(
            contenu=contenu,
            nom_fichier=(
                f"bordereau-terrain-{agent.matricule}-"
                f"{commande.date_travail:%Y%m%d}.pdf"
            ),
            type_mime="application/pdf",
        )
