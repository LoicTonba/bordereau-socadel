"""Produit les quatre guides d'utilisation et le rapport de recette.

    python scripts/generer_guides.py

Les captures doivent avoir été prises au préalable :

    python scripts/captures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from rapport import guides  # noqa: E402
from rapport.document import construire  # noqa: E402
from rapport.recette import rapport_de_recette  # noqa: E402

SORTIE = RACINE.parent / "Documents"
CAPTURES = RACINE / "scripts" / "rapport" / "captures"

DOCUMENTS = (
    (
        "Guide-Superviseur.pdf",
        guides.superviseur,
        "Bordereau SOCADEL, Guide du superviseur",
        "Affecter, saisir, verifier, exporter",
        "Guide du superviseur",
    ),
    (
        "Guide-Agent-de-terrain.pdf",
        guides.agent_terrain,
        "Bordereau SOCADEL, Guide de l'agent de terrain",
        "Consulter ses itineraires et ses chiffres",
        "Guide de l'agent de terrain",
    ),
    (
        "Guide-Administrateur.pdf",
        guides.administrateur,
        "Bordereau SOCADEL, Guide de l'administrateur",
        "Gouverner les acces et les perimetres",
        "Guide de l'administrateur",
    ),
    (
        "Guide-Super-utilisateur.pdf",
        guides.super_utilisateur,
        "Bordereau SOCADEL, Guide du super utilisateur",
        "Exploiter la plateforme et repondre de son fonctionnement",
        "Guide du super utilisateur",
    ),
)


def main() -> None:
    if not (CAPTURES / "journal.json").exists():
        raise SystemExit(
            "Captures absentes. Lancez d'abord : python scripts/captures.py"
        )

    SORTIE.mkdir(parents=True, exist_ok=True)
    journal = json.loads((CAPTURES / "journal.json").read_text(encoding="utf-8"))

    for fichier, fabrique, titre, sujet, pied in DOCUMENTS:
        chemin = SORTIE / fichier
        construire(chemin, fabrique, titre=titre, sujet=sujet, pied=pied)
        print(f"  {fichier:34s} {chemin.stat().st_size / 1024:6.0f} Ko")

    chemin = SORTIE / "Rapport-de-recette.pdf"
    construire(
        chemin,
        lambda: rapport_de_recette(journal),
        titre="Bordereau SOCADEL, Rapport de recette",
        sujet="Parcours executes profil par profil, et ce qui a ete observe",
        pied="Rapport de recette",
    )
    print(f"  {'Rapport-de-recette.pdf':34s} {chemin.stat().st_size / 1024:6.0f} Ko")


if __name__ == "__main__":
    main()
