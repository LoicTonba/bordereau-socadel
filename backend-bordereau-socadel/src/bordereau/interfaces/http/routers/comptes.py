"""Routes des comptes : inscription, approbation, mots de passe, annuaire.

L'inscription et la réinitialisation sont **publiques**, tout le reste demande
une session. Les routes publiques ne révèlent jamais si un compte existe.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from ....application.use_cases.comptes import (
    CommandeApprobation,
    CommandeChangement,
    CommandeInscription,
    CommandeModificationCompte,
    CommandeReinitialisationParJeton,
)
from ....domain.enums import StatutCompte
from ....domain.securite import mot_de_passe as politique
from ..deps import ContainerDep, ContexteDep, UtilisateurDep
from ..schemas.bordereau import (
    CompteSortie,
    ReponseForceMotDePasse,
    ReponseInscription,
    ReponseMotDePasseProvisoire,
    RequeteApprobation,
    RequeteChangementMotDePasse,
    RequeteDemandeReinitialisation,
    RequeteInscription,
    RequeteModificationCompte,
    RequeteReinitialisation,
    RequeteVerificationForce,
)

router = APIRouter(prefix="/comptes", tags=["Comptes"])

#: Réponse identique quel que soit le cas, pour ne pas révéler l'existence
#: d'une adresse dans la base.
MESSAGE_REINITIALISATION = (
    "Si un compte actif correspond à cette adresse, un lien de "
    "réinitialisation vient d'être envoyé."
)


# --- Parcours public --------------------------------------------------------


@router.post(
    "/inscription",
    response_model=ReponseInscription,
    status_code=status.HTTP_201_CREATED,
    summary="Déposer une demande d'accès",
)
async def inscription(
    requete: RequeteInscription, container: ContainerDep
) -> ReponseInscription:
    """Enregistre la demande et envoie le lien de confirmation.

    S'inscrire ne donne pas accès : la demande devra être approuvée par un
    responsable, qui attribuera le rôle et le périmètre.
    """
    compte = await container.inscrire_utilisateur().executer(
        CommandeInscription(
            identifiant=requete.identifiant,
            nom_complet=requete.nom_complet,
            email=requete.email,
            mot_de_passe=requete.mot_de_passe,
            confirmation=requete.confirmation,
            telephone=requete.telephone,
            role_souhaite=requete.role_souhaite,
        )
    )
    return ReponseInscription(
        identifiant=compte.identifiant,
        email=compte.email,
        statut=compte.statut,
        message=(
            "Votre demande est enregistrée. Confirmez votre adresse en "
            "ouvrant le lien que vous venez de recevoir par courriel."
        ),
    )


@router.post(
    "/force-mot-de-passe",
    response_model=ReponseForceMotDePasse,
    summary="Évaluer un mot de passe",
)
async def force_mot_de_passe(
    requete: RequeteVerificationForce,
) -> ReponseForceMotDePasse:
    """Retour visuel pendant la saisie, sans rien enregistrer.

    La même politique tranchera au moment de l'inscription : l'évaluation
    affichée et la règle appliquée ne peuvent pas diverger.
    """
    force = politique.evaluer(
        requete.mot_de_passe,
        identifiant=requete.identifiant,
        email=requete.email,
    )
    return ReponseForceMotDePasse(
        score=force.score,
        libelle=force.libelle,
        acceptable=force.acceptable,
        motifs=list(force.motifs),
    )


@router.get(
    "/verification",
    response_model=ReponseInscription,
    summary="Confirmer son adresse électronique",
)
async def verification(
    container: ContainerDep, jeton: Annotated[str, Query(min_length=8)]
) -> ReponseInscription:
    compte = await container.verifier_adresse().executer(jeton)
    return ReponseInscription(
        identifiant=compte.identifiant,
        email=compte.email,
        statut=compte.statut,
        message=(
            "Votre adresse est confirmée. Un responsable va examiner votre "
            "demande ; vous serez prévenu par courriel."
        ),
    )


@router.post(
    "/mot-de-passe/oubli",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Demander un lien de réinitialisation",
)
async def oubli_mot_de_passe(
    requete: RequeteDemandeReinitialisation, container: ContainerDep
) -> dict[str, str]:
    """Répond toujours la même chose.

    Dire « adresse inconnue » offrirait un moyen simple de savoir qui possède
    un compte sur la plateforme.
    """
    await container.demander_reinitialisation().executer(requete.email)
    return {"message": MESSAGE_REINITIALISATION}


@router.post(
    "/mot-de-passe/reinitialisation",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Choisir un nouveau mot de passe via le lien reçu",
)
async def reinitialisation(
    requete: RequeteReinitialisation, container: ContainerDep
) -> Response:
    await container.reinitialiser_avec_jeton().executer(
        CommandeReinitialisationParJeton(
            jeton=requete.jeton,
            nouveau_mot_de_passe=requete.nouveau_mot_de_passe,
            confirmation=requete.confirmation,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Parcours authentifié ---------------------------------------------------


@router.get("", response_model=list[CompteSortie], summary="Lister les comptes")
async def lister(
    container: ContainerDep,
    contexte: ContexteDep,
    statut: Annotated[StatutCompte | None, Query()] = None,
) -> list[CompteSortie]:
    """Annuaire restreint : on ne voit que les comptes sur lesquels on pourrait
    agir, plus le sien."""
    comptes = await container.lister_comptes().executer(contexte, statut=statut)
    return [CompteSortie.depuis_entite(c) for c in comptes]


@router.post(
    "/{compte_id}/approbation",
    response_model=CompteSortie,
    summary="Approuver une demande et attribuer rôle et périmètre",
)
async def approbation(
    compte_id: UUID,
    requete: RequeteApprobation,
    container: ContainerDep,
    contexte: ContexteDep,
) -> CompteSortie:
    """Le rôle attribué doit être strictement inférieur à celui de
    l'approbateur : on ne crée jamais son égal."""
    compte = await container.approuver_compte().executer(
        contexte,
        CommandeApprobation(
            compte_id=compte_id,
            role=requete.role,
            region=requete.region,
            agence=requete.agence,
            agent_id=requete.agent_id,
        ),
    )
    return CompteSortie.depuis_entite(compte)


@router.post(
    "/{compte_id}/refus",
    response_model=CompteSortie,
    summary="Refuser une demande d'accès",
)
async def refus(
    compte_id: UUID,
    container: ContainerDep,
    contexte: ContexteDep,
    motif: Annotated[str | None, Query(max_length=300)] = None,
) -> CompteSortie:
    compte = await container.refuser_compte().executer(contexte, compte_id, motif)
    return CompteSortie.depuis_entite(compte)


@router.patch(
    "/{compte_id}", response_model=CompteSortie, summary="Modifier un compte"
)
async def modifier(
    compte_id: UUID,
    requete: RequeteModificationCompte,
    container: ContainerDep,
    contexte: ContexteDep,
) -> CompteSortie:
    compte = await container.modifier_compte().executer(
        contexte,
        CommandeModificationCompte(
            compte_id=compte_id,
            nom_complet=requete.nom_complet,
            email=requete.email,
            telephone=requete.telephone,
            photo_url=requete.photo_url,
            region=requete.region,
            agence=requete.agence,
            role=requete.role,
        ),
    )
    return CompteSortie.depuis_entite(compte)


@router.patch(
    "/{compte_id}/activation",
    response_model=CompteSortie,
    summary="Suspendre ou réactiver un compte",
)
async def activation(
    compte_id: UUID,
    container: ContainerDep,
    contexte: ContexteDep,
    actif: Annotated[bool, Query()] = True,
) -> CompteSortie:
    compte = await container.basculer_activation_compte().executer(
        contexte, compte_id, actif=actif
    )
    return CompteSortie.depuis_entite(compte)


@router.post(
    "/{compte_id}/mot-de-passe/reinitialisation",
    response_model=ReponseMotDePasseProvisoire,
    summary="Réinitialiser le mot de passe d'un subordonné",
)
async def reinitialiser_par_responsable(
    compte_id: UUID, container: ContainerDep, contexte: ContexteDep
) -> ReponseMotDePasseProvisoire:
    """Génère un mot de passe provisoire, à communiquer de vive voix.

    Il n'est jamais écrit dans le courriel de notification, et le titulaire
    devra le remplacer dès sa prochaine connexion.
    """
    provisoire = await container.reinitialiser_par_responsable().executer(
        contexte, compte_id
    )
    return ReponseMotDePasseProvisoire(
        identifiant=provisoire.identifiant,
        nom_complet=provisoire.nom_complet,
        mot_de_passe_provisoire=provisoire.mot_de_passe,
        consigne=(
            "Communiquez ce mot de passe de vive voix. Le titulaire devra le "
            "remplacer à sa prochaine connexion."
        ),
    )


@router.post(
    "/mot-de-passe",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Changer son propre mot de passe",
)
async def changer_mot_de_passe(
    requete: RequeteChangementMotDePasse,
    container: ContainerDep,
    contexte: ContexteDep,
    utilisateur: UtilisateurDep,
) -> Response:
    await container.changer_mot_de_passe().executer(
        contexte,
        CommandeChangement(
            compte_id=utilisateur.id,
            ancien_mot_de_passe=requete.ancien_mot_de_passe,
            nouveau_mot_de_passe=requete.nouveau_mot_de_passe,
            confirmation=requete.confirmation,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
