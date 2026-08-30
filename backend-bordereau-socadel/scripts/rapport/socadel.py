"""Rapport sur SOCADEL et son maillage territorial.

Les chiffres proviennent du **référentiel clients de SOCADEL lui-même**, pas
d'une source extérieure. C'est un choix assumé : une liste d'agences recopiée
d'un site web ou d'un annuaire serait invérifiable et probablement périmée,
alors que le référentiel est la base sur laquelle la campagne va s'exécuter.
Chaque nombre de ce rapport se recalcule par une requête SQL.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import NextPageTemplate, PageBreak, Spacer  # noqa: E402

from .document import encadre, legende, p, puces, tableau, titre  # noqa: E402

#: Lecture des sigles territoriaux. Elle est **déduite** de la structure du
#: référentiel (quelles divisions dépendent de quelle direction, quelles villes
#: relèvent de quelle agence) et non d'un document officiel SOCADEL. Elle est
#: présentée comme telle et reste à confirmer par la DSI.
SIGLES: list[tuple[str, str, str]] = [
    ("DCUD", "Direction du Centre Urbain de Douala", "Déduit : 5 divisions, toutes préfixées DVC DOUALA"),
    ("DCUY", "Direction du Centre Urbain de Yaoundé", "Déduit : 5 divisions, toutes préfixées DVC YAOUNDE"),
    ("DRC", "Direction Régionale du Centre, hors Yaoundé", "Déduit : Bafia, Mfou, Obala"),
    ("DRE", "Direction Régionale de l'Est", "Déduit : Bertoua et Est étendu"),
    ("DRNEA", "Direction Régionale Nord, Extrême-Nord, Adamaoua", "Déduit : les trois régions septentrionales réunies"),
    ("DRONO", "Direction Régionale Ouest et Nord-Ouest", "Déduit : Ouest (Bafoussam, Noun, Menoua) et Bamenda"),
    ("DRSANO", "Direction Régionale Sanaga et Océan", "Déduit : Édéa, Éséka, Kribi"),
    ("DRSM", "Direction Régionale du Sud", "Déduit : Ebolowa, Mbalmayo, Sangmélima"),
    ("DRSOM", "Direction Régionale Sud-Ouest et Moungo", "Déduit : Kumba, Limbé, Moungo"),
]

NIVEAUX: list[tuple[str, str, str]] = [
    ("DVC", "Division de vente, zone urbaine dense", "Douala, Yaoundé, Ouest, Limbé"),
    ("DPC", "Division provinciale, zone étendue", "Bertoua, Kribi, Kumba, Bamenda"),
    ("DLP", "Division longue portée, très grandes distances", "Adamaoua, Extrême-Nord"),
    ("CSC", "Centre de service client, l'agence sur le terrain", "Les 181 points du réseau"),
]

#: Correspondance agence vers région administrative. Établie à la lecture des
#: noms de villes, elle sert uniquement à situer le lecteur.
REGIONS_ADMIN: list[tuple[str, str, str]] = [
    ("Adamaoua", "Ngaoundéré", "DRNEA, division DLP ADAMAOUA"),
    ("Centre", "Yaoundé", "DCUY pour la ville, DRC pour le reste"),
    ("Est", "Bertoua", "DRE"),
    ("Extrême-Nord", "Maroua", "DRNEA, division DLP EXTREME-NORD"),
    ("Littoral", "Douala", "DCUD pour la ville, DRSANO et DRSOM alentour"),
    ("Nord", "Garoua", "DRNEA, division DPC NORD"),
    ("Nord-Ouest", "Bamenda", "DRONO, divisions DPC BAMENDA et BAMENDA EXT"),
    ("Ouest", "Bafoussam", "DRONO, divisions DVC OUEST 1 et 2"),
    ("Sud", "Ebolowa", "DRSM"),
    ("Sud-Ouest", "Buea", "DRSOM, divisions DPC KUMBA et DVC LIMBE"),
]


def _charger(chemin: Path) -> dict[str, dict[str, list[tuple[str, int]]]]:
    """Lit l'extraction du référentiel : région, division, agence, effectif."""
    arbre: dict[str, dict[str, list[tuple[str, int]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        morceaux = ligne.strip().split("|")
        if len(morceaux) == 4 and morceaux[3].isdigit():
            arbre[morceaux[0]][morceaux[1]].append((morceaux[2], int(morceaux[3])))
    return arbre


def _milliers(valeur: int) -> str:
    return f"{valeur :}".replace(",", " ")


def contenu(chemin_donnees: Path) -> list:
    """Compose le rapport à partir de l'extraction du référentiel."""
    arbre = _charger(chemin_donnees)

    agences = [
        (reg, div, ag, n)
        for reg, divisions in arbre.items()
        for div, liste in divisions.items()
        for ag, n in liste
    ]
    total_clients = sum(n for *_, n in agences)
    total_agences = len(agences)
    total_divisions = sum(len(d) for d in arbre.values())

    elements: list = [
        *_couverture(total_clients, total_agences, total_divisions, len(arbre)),
        *_methode(),
        *_organisation(arbre, total_clients),
        *_regions_administratives(),
        *_annuaire(arbre),
        *_noso(arbre),
        *_consequences(),
    ]
    return elements


def _couverture(clients: int, agences: int, divisions: int, regions: int) -> list:
    from datetime import date

    return [
        Spacer(1, 46 * mm),
        p("SOCADEL, SOCIÉTÉ CAMEROUNAISE D'ELECTRICITÉ", "sous_titre_couverture"),
        Spacer(1, 6 * mm),
        p("Maillage territorial", "titre_couverture"),
        Spacer(1, 4 * mm),
        p(
            "Directions régionales, divisions et agences<br/>"
            "relevées dans le référentiel clients",
            "sous_titre_couverture",
        ),
        Spacer(1, 24 * mm),
        tableau(
            [
                ["Rubrique", "Valeur"],
                ["Destinataire", "M. TONDJOU Patrick, Directeur des Systèmes d'Information et de la Technologie, NEXT LTD"],
                ["Rédigé par", "TONBA Loïc, Ingénieur des travaux informatiques, développeur web senior, NEXT LTD"],
                ["Source", "Référentiel clients SOCADEL, base de test chargée le 30/08/2026"],
                ["Volumétrie", f"{_milliers(clients)} clients, {agences} agences, {divisions} divisions, {regions} directions régionales"],
                ["Version", "1.0"],
                ["Date", date.today().strftime("%d/%m/%Y")],
            ],
            [95, 335],
            taille=8.5,
        ),
    ]


def _methode() -> list:
    return [
        PageBreak(),
        titre("1. D'où viennent ces chiffres", "h1"),
        p(
            "Ce rapport ne recopie aucune source extérieure. Toutes les données "
            "proviennent du référentiel clients de SOCADEL, celui qui a été "
            "chargé dans la plateforme et sur lequel la campagne va s'exécuter."
        ),
        encadre(
            "<b>Pourquoi ce choix.</b> Une liste d'agences reprise d'un site web, "
            "d'une page Facebook ou d'un annuaire serait invérifiable, très "
            "probablement incomplète, et périmée dès la première réorganisation. "
            "Le référentiel, lui, est la base de travail réelle : s'il contient "
            "une agence, c'est qu'elle porte des clients à démarcher. S'il n'en "
            "contient pas, la campagne ne l'atteindra pas, quelle que soit son "
            "existence sur le papier."
        ),
        Spacer(1, 5 * mm),
        p("Chaque nombre de ce document se recalcule par une requête unique :"),
        tableau(
            [
                ["Élément", "Comment il est obtenu"],
                ["Directions régionales", "Valeurs distinctes de la colonne NOM_AREA"],
                ["Divisions", "Valeurs distinctes de NOM_ZONA, rattachées à leur direction"],
                ["Agences", "Valeurs distinctes de NOM_UNICOM, rattachées à leur division"],
                ["Effectifs", "Décompte des clients par agence"],
            ],
            [140, 290],
        ),
        titre("Ce qui relève de la déduction", "h2"),
        p(
            "Le référentiel donne des sigles, pas leur signification. La lecture "
            "proposée plus loin est <b>déduite de la structure des données</b>, "
            "par exemple du fait que les cinq divisions rattachées à DCUD "
            "portent toutes le préfixe « DVC DOUALA ». Elle est signalée comme "
            "telle partout où elle apparaît, et reste à confirmer par la DSI de "
            "SOCADEL. Aucune signification n'a été inventée pour combler un "
            "blanc."
        ),
    ]


def _organisation(arbre: dict, total: int) -> list:
    lignes = [["Direction", "Divisions", "Agences", "Clients", "Part"]]
    for reg in sorted(arbre, key=lambda r: -sum(n for d in arbre[r].values() for _, n in d)):
        clients = sum(n for d in arbre[reg].values() for _, n in d)
        agences = sum(len(d) for d in arbre[reg].values())
        lignes.append(
            [
                reg,
                str(len(arbre[reg])),
                str(agences),
                _milliers(clients),
                f"{clients * 100 / total:.1f} %",
            ]
        )

    return [
        PageBreak(),
        titre("2. L'organisation territoriale", "h1"),
        p(
            "SOCADEL structure sa distribution en trois niveaux : la direction "
            "régionale, la division, puis l'agence, appelée centre de service "
            "client. C'est ce dernier niveau qui compte pour la campagne : "
            "l'agence est le point où les distributeurs prennent leurs tournées."
        ),
        titre("Les neuf directions régionales"),
        tableau(lignes, [95, 80, 80, 90, 85], aligne_a_droite=[1, 2, 3, 4]),
        legende(
            "Trois directions concentrent plus de 60 % du portefeuille : "
            "l'Ouest et Nord-Ouest, Yaoundé, et Douala."
        ),
        titre("Lecture des sigles"),
        p(
            "Signification déduite de la structure du référentiel, à confirmer "
            "par la DSI SOCADEL."
        ),
        tableau(
            [["Sigle", "Lecture proposée", "Sur quoi elle repose"]]
            + [[s, lecture, base] for s, lecture, base in SIGLES],
            [60, 190, 180],
        ),
        titre("Les trois niveaux de découpage"),
        tableau(
            [["Niveau", "Ce qu'il désigne", "Où on le rencontre"]]
            + [[n, quoi, ou] for n, quoi, ou in NIVEAUX],
            [55, 215, 160],
        ),
    ]


def _regions_administratives() -> list:
    return [
        PageBreak(),
        titre("3. Correspondance avec les régions du Cameroun", "h1"),
        p(
            "Le découpage de SOCADEL ne recoupe pas celui de l'administration : "
            "une direction régionale peut couvrir plusieurs régions "
            "administratives, et une grande ville peut avoir sa propre "
            "direction. Le tableau ci-dessous situe l'un par rapport à l'autre."
        ),
        tableau(
            [["Région administrative", "Chef-lieu", "Rattachement chez SOCADEL"]]
            + [[r, c, s] for r, c, s in REGIONS_ADMIN],
            [130, 90, 210],
        ),
        legende(
            "Les dix régions du Cameroun sont représentées dans le référentiel. "
            "Correspondance établie à la lecture des noms de villes."
        ),
        encadre(
            "<b>Deux villes ont leur propre direction.</b> Douala et Yaoundé sont "
            "traitées à part du reste de leur région administrative, avec cinq "
            "divisions chacune. C'est cohérent avec leur densité : à elles deux "
            "elles portent près de 40 % du portefeuille sur une fraction du "
            "territoire."
        ),
    ]


def _annuaire(arbre: dict) -> list:
    """Annuaire complet, une page par direction."""
    elements: list = [
        NextPageTemplate("portrait"),
        PageBreak(),
        titre("4. Annuaire des agences", "h1"),
        p(
            "Les 181 agences du référentiel, groupées par direction et par "
            "division. Le nombre entre parenthèses est celui des clients "
            "rattachés, donc le volume à démarcher."
        ),
    ]

    for reg in sorted(arbre):
        clients = sum(n for d in arbre[reg].values() for _, n in d)
        agences = sum(len(d) for d in arbre[reg].values())
        elements.append(
            titre(f"{reg}, {_milliers(clients)} clients, {agences} agences", "h2")
        )

        lignes = [["Division", "Agences, avec leur portefeuille"]]
        for div in sorted(arbre[reg]):
            liste = sorted(arbre[reg][div], key=lambda x: -x[1])
            lignes.append(
                [
                    f"{div}<br/><font size='7'>{_milliers(sum(n for _, n in liste))} clients</font>",
                    " · ".join(f"{a} ({_milliers(n)})" for a, n in liste),
                ]
            )
        elements.append(tableau(lignes, [120, 310], taille=7.5))

    return elements


def _noso(arbre: dict) -> list:
    """Ce que la donnée dit du Nord-Ouest et du Sud-Ouest."""
    nord_ouest = dict(arbre.get("DRONO", {}).get("DPC BAMENDA", []))
    nord_ouest.update(dict(arbre.get("DRONO", {}).get("DPC BAMENDA EXT", [])))
    sud_ouest = dict(arbre.get("DRSOM", {}).get("DPC KUMBA", []))
    sud_ouest.update(dict(arbre.get("DRSOM", {}).get("DVC LIMBE", [])))

    lignes_no = [["Agence", "Clients", "Lecture"]]
    for agence, n in sorted(nord_ouest.items(), key=lambda x: -x[1]):
        lecture = (
            "Portefeuille normal"
            if n > 300
            else "Présence résiduelle" if n > 10 else "Quasi nul, un seul client"
        )
        lignes_no.append([agence, _milliers(n), lecture])

    lignes_so = [["Agence", "Clients"]]
    for agence, n in sorted(sud_ouest.items(), key=lambda x: -x[1]):
        lignes_so.append([agence, _milliers(n)])

    return [
        PageBreak(),
        titre("5. Le Nord-Ouest et le Sud-Ouest", "h1"),
        p(
            "La question de la couverture dans ces deux régions se pose pour le "
            "déploiement de la campagne. Plutôt que de s'appuyer sur des "
            "informations de presse, ce chapitre s'en tient à ce que le "
            "référentiel montre."
        ),
        titre("Nord-Ouest, direction DRONO"),
        tableau(lignes_no, [150, 90, 190], aligne_a_droite=[1]),
        encadre(
            "<b>Ce que la donnée dit.</b> La couverture du Nord-Ouest est "
            "réelle mais inégale. Bamenda et sa périphérie immédiate portent des "
            "portefeuilles substantiels : Nkwen dépasse six mille clients, Mankon "
            "près de trois mille, et huit agences périphériques restent actives. "
            "En revanche, Kumbo et Ndop ne comptent <b>qu'un seul client chacune</b> "
            "dans le référentiel. Un tel écart ne s'explique pas par la "
            "démographie : ces deux agences sont présentes dans la nomenclature "
            "mais leur portefeuille n'y est pas, ou n'y est plus."
        ),
        Spacer(1, 4 * mm),
        titre("Sud-Ouest, direction DRSOM"),
        tableau(lignes_so, [230, 200], aligne_a_droite=[1]),
        legende(
            "Le Sud-Ouest est couvert normalement : Buea, Limbé, Kumba, Tiko et "
            "Mamfé portent tous des portefeuilles significatifs."
        ),
        titre("Ce qu'il faut en retenir pour la campagne"),
        *puces(
            [
                "Le Sud-Ouest peut être déployé comme les autres régions.",
                "Bamenda et sa périphérie sont exploitables, avec un peu moins de "
                "onze mille clients à démarcher sur douze agences.",
                "Kumbo et Ndop sont à écarter du chiffrage : deux clients en tout. "
                "Les y compter fausserait les objectifs assignés aux équipes.",
                "Ce constat vient du référentiel, pas d'une appréciation de la "
                "situation sur le terrain. La décision de déployer ou non relève "
                "de SOCADEL.",
            ]
        ),
    ]


def _consequences() -> list:
    return [
        PageBreak(),
        titre("6. Ce que ce maillage implique pour la plateforme", "h1"),
        p(
            "Ce n'est pas un chapitre de contexte : le maillage territorial a "
            "directement dicté la conception des habilitations."
        ),
        titre("Un superviseur ne voit que son périmètre"),
        p(
            "Avec 181 agences réparties sur les dix régions, un superviseur de "
            "Kribi n'a aucune raison de voir la production de Ngaoundéré. La "
            "plateforme impose donc à chaque superviseur une région ou une "
            "agence, et le filtre de toute requête est réécrit à ce périmètre "
            "avant d'atteindre la base."
        ),
        encadre(
            "<b>La conséquence est stricte.</b> Un superviseur sans périmètre "
            "défini ne voit rien du tout : la plateforme refuse la requête plutôt "
            "que de lui ouvrir le national par défaut. Attribuer le périmètre "
            "fait donc partie de l'approbation du compte, ce n'est pas un réglage "
            "que l'on renseigne plus tard."
        ),
        Spacer(1, 5 * mm),
        titre("Une échelle qui contraint la technique"),
        tableau(
            [
                ["Ce que le maillage impose", "Comment la plateforme y répond"],
                ["425 920 clients à filtrer", "Filtres, tri et pagination traduits en SQL, jamais appliqués en mémoire"],
                ["16 763 itinéraires", "Insertions découpées en lots calculés sur le nombre de colonnes"],
                ["181 agences à cloisonner", "Périmètre obligatoire par superviseur, appliqué en amont de la requête"],
                ["9 directions à comparer", "Vue nationale réservée à l'administrateur et au super utilisateur"],
            ],
            [175, 255],
        ),
        titre("Le déploiement se lit dans ce tableau"),
        p(
            "Les trois premières directions concentrent la majorité du "
            "portefeuille. Un déploiement par vagues, si SOCADEL le souhaite, "
            "trouve là son ordre naturel : commencer par l'Ouest, Yaoundé et "
            "Douala couvre les deux tiers du volume avec un tiers des agences."
        ),
    ]
