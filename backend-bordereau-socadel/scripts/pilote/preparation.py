"""Remet le jeu de démonstration dans l'état qui permet de rejouer le parcours.

Le scénario affecte un itinéraire précis à un agent précis, pour la journée du
jour. La plateforme refuse à juste titre de le faire deux fois : sans remise à
zéro, le second passage capturerait un message de doublon au lieu de la carte
de succès, et le guide montrerait un échec.

Seule l'affectation de démonstration est retirée, avec les lignes qu'elle a
engendrées. Le référentiel clients n'est jamais touché.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src"))

from sqlalchemy import text  # noqa: E402

from bordereau.infrastructure.config.settings import get_settings  # noqa: E402
from bordereau.infrastructure.container import Container  # noqa: E402

#: Suppression en deux temps : les lignes portent une clé étrangère vers
#: l'affectation, elles doivent partir d'abord.
NETTOYAGE = (
    """
    DELETE FROM lignes_bordereau
    WHERE affectation_id IN (
        SELECT a.id FROM affectations a
        JOIN agents_terrain g ON g.id = a.agent_id
        WHERE g.matricule = :matricule
          AND a.date_travail = :jour
          AND a.itineraire_code = :code
    )
    """,
    """
    DELETE FROM affectations a
    USING agents_terrain g
    WHERE g.id = a.agent_id
      AND g.matricule = :matricule
      AND a.date_travail = :jour
      AND a.itineraire_code = :code
    """,
)


async def remettre_a_zero(*, matricule: str, code: int, jour: date | None = None) -> int:
    """Retire l'affectation de démonstration. Renvoie le nombre de lignes ôtées."""
    parametres = {"matricule": matricule, "jour": jour or date.today(), "code": code}
    container = Container(get_settings())
    try:
        async with container.moteur.begin() as connexion:
            lignes = (await connexion.execute(text(NETTOYAGE[0]), parametres)).rowcount
            await connexion.execute(text(NETTOYAGE[1]), parametres)
        return lignes
    finally:
        await container.moteur.dispose()


#: Demandeur fictif, recree a chaque passage pour que l'ecran de gouvernance
#: ait toujours une demande a montrer.
CANDIDAT = {
    "identifiant": "mbarga.j",
    "nomComplet": "MBARGA Jeanne",
    "email": "jeanne.mbarga@socadel.cm",
    "motDePasse": "Essos-Bertoua-2026",
    "confirmation": "Essos-Bertoua-2026",
    "roleSouhaite": "SUPERVISEUR",
}


async def deposer_une_demande(api: str = "http://localhost:8001/api/v1") -> str:
    """Depose une demande d'acces et confirme son adresse.

    L'ecran de gouvernance ne montre le formulaire d'approbation que s'il a une
    demande a traiter. Elle est donc creee ici, jusqu'a l'etape ou un
    responsable doit trancher, et pas au-dela.
    """
    import json
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    await _supprimer_candidat()

    def poster(chemin: str, corps: dict) -> dict:
        requete = Request(
            f"{api}{chemin}",
            data=json.dumps(corps).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(requete, timeout=15) as reponse:
            return json.load(reponse)

    try:
        poster("/comptes/inscription", CANDIDAT)
    except HTTPError as echec:
        return f"inscription refusee : {echec.code}"

    jeton = await _dernier_jeton_verification(CANDIDAT["email"])
    if jeton:
        with urlopen(f"{api}/comptes/verification?jeton={jeton}", timeout=15):
            pass
        return "demande deposee et adresse confirmee"
    return "demande deposee, adresse non confirmee"


async def _supprimer_candidat() -> None:
    container = Container(get_settings())
    try:
        async with container.moteur.begin() as connexion:
            await connexion.execute(
                text("DELETE FROM utilisateurs WHERE identifiant = :i"),
                {"i": CANDIDAT["identifiant"]},
            )
    finally:
        await container.moteur.dispose()


async def _dernier_jeton_verification(email: str) -> str | None:
    """Lit le jeton en base plutot que dans le courriel ecrit sur disque."""
    container = Container(get_settings())
    try:
        async with container.moteur.begin() as connexion:
            return await connexion.scalar(
                text("SELECT jeton_verification FROM utilisateurs WHERE email = :e"),
                {"e": email},
            )
    finally:
        await container.moteur.dispose()


if __name__ == "__main__":
    retirees = asyncio.run(remettre_a_zero(matricule="AG001", code=110581))
    print(f"{retirees} ligne(s) de demonstration retiree(s)")
