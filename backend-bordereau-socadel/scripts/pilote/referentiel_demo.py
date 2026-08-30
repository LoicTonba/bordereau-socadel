"""Simule, sur trois clients, ce que l'API NEXT renverra un jour.

Le référentiel de test porte 425 920 clients, tous en `not_checked` : la
campagne n'a pas encore eu lieu et l'API de recoupement n'est pas ouverte.
Toute déclaration d'abonnement y ressort donc **infirmée**, ce qui est le bon
comportement mais ne montre qu'une moitié de la règle.

Trois clients de l'itinéraire de démonstration sont donc marqués abonnés, avec
le numéro que le référentiel leur connaît déjà. Le guide peut alors montrer les
deux verdicts, confirmé et infirmé, côte à côte.

C'est une donnée d'essai, réversible : `--retablir` remet les trois clients
dans leur état d'origine. Le jour où l'API NEXT sera branchée, ce script n'aura
plus de raison d'être.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "src"))

from sqlalchemy import text  # noqa: E402

from bordereau.infrastructure.config.settings import get_settings  # noqa: E402
from bordereau.infrastructure.container import Container  # noqa: E402

#: Les trois premiers clients de l'itinéraire, dans l'ordre de marche.
CHOIX = text(
    """
    SELECT service_no, nom, telephone
    FROM clients
    WHERE code_itineraire = :code AND telephone IS NOT NULL
    ORDER BY ref_geo
    LIMIT 3
    """
)


async def marquer(code: int, *, abonnes: bool) -> list[tuple[str, str, str]]:
    """Bascule le statut WhatsApp des trois clients témoins."""
    statut = "subscribed" if abonnes else "not_checked"
    container = Container(get_settings())
    try:
        async with container.moteur.begin() as connexion:
            clients = list(await connexion.execute(CHOIX, {"code": code}))
            await connexion.execute(
                text(
                    "UPDATE clients SET whatsapp_status = :statut, "
                    "whatsapp_verifie_le = now() "
                    "WHERE service_no = ANY(:contrats)"
                ),
                {"statut": statut, "contrats": [c[0] for c in clients]},
            )
        return [tuple(c) for c in clients]
    finally:
        await container.moteur.dispose()


async def principal() -> None:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--code", type=int, default=110581)
    analyseur.add_argument(
        "--retablir", action="store_true", help="Remettre les clients en not_checked"
    )
    arguments = analyseur.parse_args()

    clients = await marquer(arguments.code, abonnes=not arguments.retablir)
    etat = "not_checked" if arguments.retablir else "subscribed"
    print(f"{len(clients)} client(s) passe(s) en {etat} :")
    for contrat, nom, telephone in clients:
        print(f"  {contrat}  {nom:32s} {telephone}")


if __name__ == "__main__":
    asyncio.run(principal())
