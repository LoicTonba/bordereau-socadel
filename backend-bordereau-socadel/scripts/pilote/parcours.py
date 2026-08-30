"""Gestes communs à tous les parcours : se connecter, se déconnecter.

Ils sont isolés ici parce que les quatre scénarios les répètent, et qu'une
connexion qui change de forme ne doit se corriger qu'à un seul endroit.
"""

from __future__ import annotations

import asyncio

from .navigateur import Navigateur

BASE = "http://localhost:3000"

#: Libellé de la carte de profil, tel qu'il s'affiche à la première étape.
LIBELLE_PROFIL = {
    "SUPER_UTILISATEUR": "Super utilisateur",
    "ADMINISTRATEUR": "Administrateur",
    "SUPERVISEUR": "Superviseur",
    "AGENT_TERRAIN": "Agent de terrain",
}


async def aller_a_la_connexion(n: Navigateur) -> None:
    """Ouvre l'écran de connexion sur une session vierge.

    Le stockage est purgé au passage : sans cela, la session précédente
    renverrait droit au tableau de bord et le parcours ne serait pas rejoué.
    """
    await n.aller(f"{BASE}/login")
    await n.evaluer("try { localStorage.clear(); } catch (e) {}")
    await n.aller(f"{BASE}/login")
    await n.attendre("button", texte=LIBELLE_PROFIL["SUPERVISEUR"])


async def choisir_profil(n: Navigateur, role: str) -> None:
    await n.cliquer("ul button", texte=LIBELLE_PROFIL[role])
    await n.attendre("h3", texte="Où travaillez-vous")


async def choisir_agence(n: Navigateur, agence: str | None) -> None:
    """Sélectionne l'agence, ou le national quand le profil le permet."""
    if agence is None:
        await n.cliquer('[role="option"]', texte="Portée nationale")
    else:
        # La recherche évite de faire défiler les 181 agences.
        await n.remplir('input[name="rechercheAgence"]', agence.replace("CSC_", ""))
        await n.cliquer('[role="option"]', texte=agence)
    await n.cliquer("button", texte="Continuer")
    await n.attendre('input[name="identifiant"]')


async def saisir_identifiants(
    n: Navigateur, email: str, mot_de_passe: str, itineraires: str = ""
) -> None:
    await n.remplir('input[name="identifiant"]', email)
    await n.remplir('input[name="motDePasse"]', mot_de_passe)
    if itineraires:
        await n.remplir('input[name="itineraires"]', itineraires)


async def valider_connexion(n: Navigateur, ecran_attendu: str) -> None:
    await n.cliquer('button[type="submit"]')
    await n.attendre("h1", texte=ecran_attendu)


async def connecter(
    n: Navigateur,
    *,
    role: str,
    email: str,
    mot_de_passe: str,
    agence: str | None,
    ecran_attendu: str,
    itineraires: str = "",
) -> None:
    """Déroule les trois étapes d'un bout à l'autre."""
    await aller_a_la_connexion(n)
    await choisir_profil(n, role)
    await choisir_agence(n, agence)
    await saisir_identifiants(n, email, mot_de_passe, itineraires)
    await valider_connexion(n, ecran_attendu)


async def naviguer(n: Navigateur, chemin: str, titre_attendu: str) -> None:
    """Ouvre un écran du back-office par la barre latérale."""
    await n.cliquer(f'a[href="{chemin}"]')
    await n.attendre("h1", texte=titre_attendu)
    # Les écrans chargent leurs données après le montage : sans ce répit, la
    # capture montrerait un tableau vide qui se remplit juste après.
    await asyncio.sleep(1.2)
