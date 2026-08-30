"""Routes d'authentification."""

from __future__ import annotations

from fastapi import APIRouter, status

from ....application.use_cases.auth import CommandeConnexion
from ....domain.securite import MATRICE
from ..deps import ContainerDep, UtilisateurDep
from ..schemas.bordereau import (
    ProfilUtilisateur,
    ReponseConnexion,
    RequeteConnexion,
)

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post(
    "/connexion",
    response_model=ReponseConnexion,
    status_code=status.HTTP_200_OK,
    summary="Ouvrir une session",
)
async def connexion(
    requete: RequeteConnexion, container: ContainerDep
) -> ReponseConnexion:
    """Authentifie l'utilisateur et renvoie son jeton de session.

    Les trois profils passent par ici : administrateur, superviseur et agent
    de terrain. C'est le rôle porté par le jeton qui détermine ensuite ce que
    chacun peut faire et voir.
    """
    session = await container.connecter_superviseur().executer(
        CommandeConnexion(
            identifiant=requete.identifiant, mot_de_passe=requete.mot_de_passe
        )
    )
    return ReponseConnexion(
        jeton=session.jeton,
        expire_dans_secondes=session.expire_dans_secondes,
        identifiant=session.identifiant,
        nom_complet=session.nom_complet,
        role=session.role,
    )


@router.get(
    "/moi",
    response_model=ProfilUtilisateur,
    summary="Profil de l'utilisateur connecté",
)
async def profil(utilisateur: UtilisateurDep) -> ProfilUtilisateur:
    """Permet au frontend de revalider une session au rechargement de page.

    La réponse porte les **permissions effectives** du rôle : l'interface s'en
    sert pour n'afficher que les actions réellement disponibles. Ce n'est pas
    un contrôle de sécurité — l'API tranche de toute façon — mais cela évite
    de proposer des boutons qui échoueraient.
    """
    return ProfilUtilisateur(
        id=utilisateur.id,
        identifiant=utilisateur.identifiant,
        nom_complet=utilisateur.nom_complet,
        role=utilisateur.role,
        statut=utilisateur.statut,
        agent_id=utilisateur.agent_id,
        region=utilisateur.region,
        agence=utilisateur.agence,
        email=utilisateur.email,
        photo_url=utilisateur.photo_url,
        doit_changer_mot_de_passe=utilisateur.doit_changer_mot_de_passe,
        permissions=sorted(p.value for p in MATRICE.get(utilisateur.role, ())),
        derniere_connexion=utilisateur.derniere_connexion,
    )
