"""Génère le guide pratique au format PDF, depuis sa source Markdown.

    python scripts/generer_guide.py [source.md] [sortie.pdf]

Le PDF est dérivé du Markdown versionné : la documentation reste éditable en
texte, et le document imprimable suit sans effort de recopie.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.platypus import PageBreak  # noqa: E402

from rapport.document import construire  # noqa: E402
from rapport.markdown_pdf import convertir, couverture  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
SOURCE = RACINE / "GUIDE-PRATIQUE.md"
SORTIE = RACINE / "Documents" / "Bordereau-SOCADEL-Guide-pratique.pdf"

TITRE = "Bordereau intelligent de collecte WhatsApp"
SOUS_TITRE = "Guide pratique"


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else SOURCE
    sortie = Path(sys.argv[2]) if len(sys.argv) > 2 else SORTIE

    if not source.exists():
        raise SystemExit(f"Source introuvable : {source}")

    markdown = source.read_text(encoding="utf-8")

    def contenu() -> list:
        return [
            *couverture(
                TITRE,
                SOUS_TITRE,
                [
                    ["Rubrique", "Valeur"],
                    ["Client", "SOCADEL, Société Camerounaise d'Electricité"],
                    ["Maître d'œuvre", "NEXT LTD, Numeric Export Technologies"],
                    ["Objet", "Suivre les flux de la plateforme, écran par écran"],
                    ["Public", "Superviseurs, administrateurs, agents de terrain"],
                    ["Version", "1.0"],
                    ["Date", date.today().strftime("%d/%m/%Y")],
                ],
            ),
            PageBreak(),
            *convertir(markdown),
        ]

    sortie.parent.mkdir(parents=True, exist_ok=True)
    construire(
        sortie,
        contenu,
        titre=f"Bordereau SOCADEL, {SOUS_TITRE}",
        sujet="Guide d'utilisation pas à pas de la plateforme de collecte",
        pied=SOUS_TITRE,
    )

    print(f"Guide genere : {sortie}  ({sortie.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
