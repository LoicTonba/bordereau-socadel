"""Cas d'usage : recoupement des déclarations avec la source de vérité.

C'est la promesse du système : *« la source de vérité sera notre API qui va
vérifier notre BD dans le serveur et puis vérifiera si l'agent de terrain a
raison ou pas »*. Dès qu'un client s'abonne via le chatbot WhatsApp, son
contrat remonte au référentiel ; ce cas d'usage confronte alors chaque
déclaration à cet état.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ....domain.enums import VerdictVerification
from ....domain.securite import ContexteAcces, Permission, restreindre
from ....domain.services import verification_collecte
from ...dto import FiltreBordereau
from ...ports import Horloge, UnitOfWork

#: Borne haute d'un passage de vérification, pour garder un temps de réponse
#: prévisible sur une API synchrone.
LOT_MAX = 5_000


@dataclass(frozen=True, slots=True)
class RapportVerification:
    """Bilan d'un passage de vérification."""

    lignes_examinees: int
    confirmees: int
    infirmees: int
    introuvables: int

    @property
    def taux_confirmation(self) -> float:
        verifiees = self.confirmees + self.infirmees
        if verifiees == 0:
            return 0.0
        return self.confirmees / verifiees


class VerifierDeclarations:
    """Applique un verdict à chaque ligne déclarée d'un périmètre donné."""

    def __init__(self, uow: UnitOfWork, horloge: Horloge) -> None:
        self._uow = uow
        self._horloge = horloge

    async def executer(
        self, contexte: ContexteAcces, filtre: FiltreBordereau
    ) -> RapportVerification:
        """Vérifie toutes les lignes traitées correspondant au filtre."""
        contexte.exiger(Permission.BORDEREAU_VERIFIER)
        filtre = restreindre(contexte, filtre)
        horodatage = self._horloge.maintenant()
        examinees = confirmees = infirmees = introuvables = 0

        async with self._uow as uow:
            lignes = await uow.lignes.lister_pour_export(filtre, LOT_MAX)
            candidates = [ligne for ligne in lignes if ligne.est_traitee]

            # Un seul aller-retour en base pour tout le lot : la vérification
            # ligne à ligne serait quadratique sur un gros bordereau.
            clients = await uow.clients.par_services_no(
                {ligne.service_no for ligne in candidates}
            )

            for ligne in candidates:
                client = clients.get(ligne.service_no.valeur)
                verdict = verification_collecte.verifier(ligne, client)
                ligne.appliquer_verdict(verdict, horodatage)

                examinees += 1
                match verdict:
                    case VerdictVerification.CONFIRME:
                        confirmees += 1
                    case VerdictVerification.INFIRME:
                        infirmees += 1
                    case VerdictVerification.INTROUVABLE:
                        introuvables += 1

            if candidates:
                await uow.lignes.enregistrer_en_lot(candidates)
                await uow.valider()

        return RapportVerification(
            lignes_examinees=examinees,
            confirmees=confirmees,
            infirmees=infirmees,
            introuvables=introuvables,
        )

    async def executer_pour_affectation(
        self, affectation_id: UUID
    ) -> RapportVerification:
        """Vérifie la production d'une journée d'agent, à sa clôture."""
        horodatage = self._horloge.maintenant()
        examinees = confirmees = infirmees = introuvables = 0

        async with self._uow as uow:
            lignes = await uow.lignes.lister_par_affectation(affectation_id)
            candidates = [ligne for ligne in lignes if ligne.est_traitee]
            clients = await uow.clients.par_services_no(
                {ligne.service_no for ligne in candidates}
            )

            for ligne in candidates:
                verdict = verification_collecte.verifier(
                    ligne, clients.get(ligne.service_no.valeur)
                )
                ligne.appliquer_verdict(verdict, horodatage)
                examinees += 1
                match verdict:
                    case VerdictVerification.CONFIRME:
                        confirmees += 1
                    case VerdictVerification.INFIRME:
                        infirmees += 1
                    case VerdictVerification.INTROUVABLE:
                        introuvables += 1

            if candidates:
                await uow.lignes.enregistrer_en_lot(candidates)
                await uow.valider()

        return RapportVerification(
            lignes_examinees=examinees,
            confirmees=confirmees,
            infirmees=infirmees,
            introuvables=introuvables,
        )
