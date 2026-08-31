"""Routes de référence : ce que l'écran de connexion doit connaître avant l'authentification.

Un seul point d'entrée public, l'annuaire des agences, dont le sélecteur de
connexion a besoin pour se remplir. Il n'expose que des noms de lieux : ni
volume de portefeuille, ni identité, ni compte.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from fastapi import HTTPException

from ..deps import ContainerDep, ContexteDep, ReglagesDep
from ..schemas.bordereau import (
    AgenceSortie,
    ResultatRechercheSortie,
    TerritoireSortie,
    TrouvailleSortie,
    VoletSortie,
)

router = APIRouter(prefix="/reference", tags=["Référence"])


@router.get(
    "/agences",
    response_model=TerritoireSortie,
    summary="Annuaire des agences",
)
async def agences(container: ContainerDep) -> TerritoireSortie:
    """Alimente le sélecteur d'agence de l'écran de connexion.

    Volontairement public : le sélecteur s'affiche avant toute session. Le
    maillage d'agences de SOCADEL est une information commerciale, il ne
    constitue pas un secret d'exploitation.
    """
    liste = await container.lister_agences().executer()
    return TerritoireSortie(
        agences=[
            AgenceSortie(nom=a.nom, region=a.region, division=a.division)
            for a in liste
        ]
    )


@router.get(
    "/recherche",
    response_model=ResultatRechercheSortie,
    summary="Rechercher dans toute l'application",
)
async def recherche(
    container: ContainerDep,
    contexte: ContexteDep,
    q: Annotated[str, Query(min_length=0, max_length=120)] = "",
) -> ResultatRechercheSortie:
    """Cherche partout, dans les limites de ce que l'appelant peut voir.

    Chaque volet passe par le cas d'usage qui sert déjà l'écran correspondant :
    un agent de terrain ne trouve que ses lignes, un superviseur que son
    agence. Un volet fermé à l'appelant est absent de la réponse, jamais
    signalé comme refusé.
    """
    resultat = await container.recherche_globale().executer(contexte, q)
    return ResultatRechercheSortie(
        terme=resultat.terme,
        total=resultat.total,
        volets=[
            VoletSortie(
                cle=volet.cle,
                libelle=volet.libelle,
                resultats=[
                    TrouvailleSortie(
                        titre=t.titre, detail=t.detail, chemin=t.chemin
                    )
                    for t in volet.resultats
                ],
            )
            for volet in resultat.volets
        ],
    )


#: Comptes de mise en route, tels que le seed les cree. Ils ne sont servis
#: qu'en mode demonstration, et le mot de passe n'est jamais lu en base : il
#: est ecrit ici, en clair, parce que c'est deja ce que fait le guide.
COMPTES_DEMO = (
    ("SUPER_UTILISATEUR", "tonbaloic6@gmail.com", "Ngaoundal-Kribi-88", None),
    ("ADMINISTRATEUR", "tonbaloic@gmail.com", "Bandjoun-Maroua-77", None),
    ("SUPERVISEUR", "loicdjimgou@gmail.com", "Ngaoundere-Sud-2026",
     "CSC_NGAOUNDERE SUD"),
    ("AGENT_TERRAIN", "objectifloic@gmail.com", "Terrain-Essos-2026",
     "CSC_NGAOUNDERE SUD"),
)


@router.get(
    "/mode-demonstration",
    summary="Comptes de demonstration, si le mode est actif",
)
async def mode_demonstration(reglages: ReglagesDep) -> dict[str, object]:
    """Sert les comptes de mise en route, pour une prise en main immediate.

    Refuse net quand le mode est inactif : renvoyer une liste vide laisserait
    croire que la route existe toujours et invite a insister.
    """
    if not reglages.mode_demo:
        raise HTTPException(
            status_code=404,
            detail="Le mode demonstration n'est pas actif sur cette instance.",
        )

    return {
        "actif": True,
        "avertissement": (
            "Ces comptes servent a la prise en main. Chaque titulaire doit "
            "changer son mot de passe, et ce mode doit etre coupe en "
            "production."
        ),
        "comptes": [
            {"role": role, "email": email, "motDePasse": mot_de_passe,
             "agence": agence}
            for role, email, mot_de_passe, agence in COMPTES_DEMO
        ],
    }
