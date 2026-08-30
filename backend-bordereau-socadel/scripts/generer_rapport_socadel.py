"""Génère le rapport sur SOCADEL et son maillage territorial.

    python scripts/generer_rapport_socadel.py

Les données sont extraites du référentiel en base au moment de la génération :
le document ne peut donc pas diverger de la réalité de la plateforme.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text  # noqa: E402

from bordereau.infrastructure.config.settings import get_settings  # noqa: E402
from bordereau.infrastructure.container import Container  # noqa: E402
from rapport.document import construire  # noqa: E402
from rapport.socadel import contenu  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "Documents" / "SOCADEL-Maillage-territorial.pdf"
EXTRACTION = Path(__file__).resolve().parent / "rapport" / "_territoire.txt"

REQUETE = text("""
    SELECT region, division, agence, count(*)
    FROM clients
    WHERE region IS NOT NULL
    GROUP BY region, division, agence
    ORDER BY region, division, agence
""")


async def extraire() -> None:
    """Écrit l'arborescence territoriale depuis la base."""
    container = Container(get_settings())
    try:
        async with container.fabrique_sessions() as session:
            lignes = (await session.execute(REQUETE)).all()
    finally:
        await container.fermer()

    EXTRACTION.write_text(
        "\n".join(f"{r}|{d}|{a}|{n}" for r, d, a, n in lignes), encoding="utf-8"
    )
    print(f"Extraction : {len(lignes)} agences depuis la base")


def main() -> None:
    asyncio.run(extraire())

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    construire(
        SORTIE,
        lambda: contenu(EXTRACTION),
        titre="SOCADEL, maillage territorial",
        sujet="Directions regionales, divisions et agences du reseau SOCADEL",
        pied="Maillage territorial",
    )
    print(f"Rapport genere : {SORTIE}  ({SORTIE.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
