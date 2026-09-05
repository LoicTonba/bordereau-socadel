"""Aligne une base existante sur le modèle, sans rien détruire.

    python scripts/mettre_a_niveau.py            # montre ce qui manque
    python scripts/mettre_a_niveau.py --appliquer

`seed.py --tables` s'appuie sur `create_all`, qui crée les tables absentes mais
**n'ajoute jamais une colonne** à une table existante. Une base peuplée avant
l'ouverture des comptes se retrouve donc sans `utilisateurs.statut`, et toute
connexion échoue en 500 alors que les 425 920 clients du référentiel, eux, sont
bien là et qu'il n'est pas question de les perdre.

Ce script comble l'écart : il compare le modèle à la base, et n'émet que des
`ALTER TABLE ... ADD COLUMN`. Aucune suppression, aucune modification de type.
En production, c'est Alembic qui fait foi ; ceci dépanne un poste de
développement ou une démonstration.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy.schema import CreateIndex  # noqa: E402

from bordereau.infrastructure.config.settings import get_settings  # noqa: E402
from bordereau.infrastructure.container import Container  # noqa: E402
from bordereau.infrastructure.db.base import Base  # noqa: E402

#: Valeur donnée aux lignes déjà présentes quand une colonne obligatoire
#: apparaît. Les comptes antérieurs au cycle de vie ont, de fait, été approuvés.
VALEURS_DE_REPRISE: dict[tuple[str, str], str] = {
    ("utilisateurs", "statut"): "ACTIF",
    # Les lignes anterieures a la distinction proprietaire/locataire portaient
    # implicitement le titulaire du contrat.
    ("lignes_bordereau", "identite"): "PROPRIETAIRE",
}


async def principal() -> None:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument(
        "--appliquer",
        action="store_true",
        help="Exécuter les instructions au lieu de seulement les afficher",
    )
    arguments = analyseur.parse_args()

    container = Container(get_settings())
    try:
        instructions = await _ecart(container)
        if not instructions:
            print("La base est à jour, rien à faire.")
            return

        print(f"{len(instructions)} instruction(s) :\n")
        for instruction in instructions:
            print(f"  {instruction}")

        if not arguments.appliquer:
            print("\nRelancez avec --appliquer pour les exécuter.")
            return

        async with container.moteur.begin() as connexion:
            for instruction in instructions:
                await connexion.execute(text(instruction))
        print("\nBase mise à niveau.")
    finally:
        await container.moteur.dispose()


async def _ecart(container: Container) -> list[str]:
    """Les instructions qui manquent, dans l'ordre où les exécuter."""
    async with container.moteur.begin() as connexion:
        reel = await connexion.run_sync(_relever)
        dialecte = connexion.dialect

        instructions: list[str] = []
        for nom, table in Base.metadata.tables.items():
            if nom not in reel:
                print(f"Table absente : {nom}. Lancez seed.py --tables d'abord.")
                continue

            for colonne in table.columns:
                if colonne.name in reel[nom]:
                    continue

                type_sql = colonne.type.compile(dialect=dialecte)
                # La colonne naît toujours nullable : une table peuplée
                # refuserait un NOT NULL sans valeur pour l'existant.
                instructions.append(
                    f'ALTER TABLE {nom} ADD COLUMN IF NOT EXISTS '
                    f'"{colonne.name}" {type_sql}'
                )

                reprise = VALEURS_DE_REPRISE.get((nom, colonne.name))
                if reprise is not None:
                    instructions.append(
                        f"UPDATE {nom} SET \"{colonne.name}\" = '{reprise}' "
                        f'WHERE "{colonne.name}" IS NULL'
                    )
                if not colonne.nullable and reprise is not None:
                    instructions.append(
                        f'ALTER TABLE {nom} '
                        f'ALTER COLUMN "{colonne.name}" SET NOT NULL'
                    )

            # Une colonne retiree du modele reste en base : on ne la supprime
            # pas, mais si elle est NOT NULL elle bloque toute insertion, le
            # modele ne lui fournissant plus de valeur.
            obsoletes = reel[nom] - {c.name for c in table.columns}
            for colonne in sorted(obsoletes & reel[nom].non_nulles):
                instructions.append(
                    f'ALTER TABLE {nom} ALTER COLUMN "{colonne}" DROP NOT NULL'
                )

            for index in table.indexes:
                if index.name in reel[nom].indexes:
                    continue
                instructions.append(
                    str(
                        CreateIndex(index, if_not_exists=True).compile(
                            dialect=dialecte
                        )
                    ).strip()
                )

    return instructions


class _Colonnes(set):
    """Les colonnes d'une table, avec ses index et ses contraintes."""

    indexes: set[str]
    non_nulles: set[str]


def _relever(session) -> dict[str, _Colonnes]:
    inspecteur = inspect(session)
    releve: dict[str, _Colonnes] = {}
    for nom in inspecteur.get_table_names():
        decrites = inspecteur.get_columns(nom)
        colonnes = _Colonnes(c["name"] for c in decrites)
        colonnes.indexes = {i["name"] for i in inspecteur.get_indexes(nom)}
        colonnes.non_nulles = {c["name"] for c in decrites if not c["nullable"]}
        releve[nom] = colonnes
    return releve


if __name__ == "__main__":
    asyncio.run(principal())
