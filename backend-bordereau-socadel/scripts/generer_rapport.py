"""Génère le dossier de conception au format PDF.

    python scripts/generer_rapport.py [chemin de sortie]

Le document est produit depuis le code : la matrice des permissions, par
exemple, est lue dans le domaine plutôt que recopiée.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rapport.contenu import contenu  # noqa: E402
from rapport.document import construire  # noqa: E402

DEFAUT = Path(__file__).resolve().parents[2] / "Documents" / "Bordereau-SOCADEL-Dossier-de-conception.pdf"


def main() -> None:
    chemin = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAUT
    chemin.parent.mkdir(parents=True, exist_ok=True)

    construire(chemin, contenu)

    taille = chemin.stat().st_size / 1024
    print(f"Dossier genere : {chemin}  ({taille:.0f} Ko)")


if __name__ == "__main__":
    main()
