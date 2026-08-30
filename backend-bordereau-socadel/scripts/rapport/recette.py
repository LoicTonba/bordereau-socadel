"""Rapport de recette : ce qui a été exécuté, et ce qui a été observé.

Il est construit depuis le journal du parcours, pas rédigé après coup. Chaque
ligne correspond à une action réellement effectuée dans le navigateur, et le
constat est ce que la plateforme a répondu, tel quel.
"""

from __future__ import annotations

from datetime import date

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from .document import encadre, legende, p, puces, tableau, titre

#: Ordre de lecture des profils : du parcours d'entrée au plus large.
ORDRE = ("Commun", "Superviseur", "Agent de terrain", "Administrateur",
         "Super utilisateur")


def rapport_de_recette(journal: list[dict]) -> list:
    par_profil: dict[str, list[dict]] = {}
    for etape in journal:
        par_profil.setdefault(etape["profil"], []).append(etape)

    captures = sum(1 for e in journal if e["capture"])

    contenu = [
        Spacer(1, 40 * mm),
        p("BORDEREAU INTELLIGENT DE COLLECTE WHATSAPP", "sous_titre_couverture"),
        Spacer(1, 6 * mm),
        p("Rapport de recette", "titre_couverture"),
        Spacer(1, 4 * mm),
        p(
            "Parcours exécutés profil par profil, sur la plateforme en "
            "fonctionnement",
            "sous_titre_couverture",
        ),
        Spacer(1, 26 * mm),
        tableau(
            [
                ["Rubrique", "Valeur"],
                [
                    "Destinataire",
                    "M. TONDJOU Patrick<br/>"
                    "<font size='8'>Directeur des Systèmes d'Information et de "
                    "la Technologie, NEXT LTD</font>",
                ],
                [
                    "Exécuté par",
                    "TONBA Loïc<br/>"
                    "<font size='8'>Ingénieur des travaux informatiques, "
                    "développeur web senior, NEXT LTD</font>",
                ],
                ["Date d'exécution", date.today().strftime("%d/%m/%Y")],
                ["Étapes exécutées", str(len(journal))],
                ["Écrans capturés", str(captures)],
                ["Profils couverts", "Les quatre"],
            ],
            [110, 320],
            taille=8.5,
        ),
        PageBreak(),
        titre("Ce qui a été fait", "h1"),
        p(
            "Un navigateur a été piloté de bout en bout sur la plateforme en "
            "fonctionnement : API sur le port 8001, back-office sur le port "
            "3000, base PostgreSQL chargée des 425 920 clients du référentiel "
            "SOCADEL. Aucune étape n'est simulée."
        ),
        p(
            "Le parcours ouvre une session pour chacun des quatre profils, "
            "exécute les gestes de son métier, et enregistre l'écran obtenu. "
            "Les constats ci-dessous sont les réponses de la plateforme, "
            "recopiées sans retouche."
        ),
        titre("Conditions du test", "h2"),
        *puces(
            [
                "Comptes de mise en route, connexion par <b>adresse "
                "électronique</b>.",
                "Itinéraire de démonstration : <b>110581</b>, agence "
                "CSC_NGAOUNDERE SUD, 73 clients au référentiel.",
                "Trois clients de cet itinéraire ont été marqués abonnés dans le "
                "référentiel de test, pour que la confrontation puisse rendre un "
                "verdict <b>confirmé</b> aussi bien qu'<b>infirmé</b>. Sans cela, "
                "la base étant intégralement en <font face='Courier'>not_checked"
                "</font>, seul le verdict infirmé serait observable.",
                "L'affectation de démonstration est retirée avant chaque "
                "exécution, pour que le parcours soit rejouable à l'identique.",
            ]
        ),
        encadre(
            "<b>Ce que ce rapport ne prouve pas.</b> La vérification s'appuie "
            "aujourd'hui sur une base de test, pas sur l'API NEXT adossée à MRA, "
            "qui n'est pas encore ouverte. La <i>mécanique</i> de recoupement est "
            "donc démontrée de bout en bout ; les <i>abonnements réels</i> ne le "
            "seront qu'une fois l'API branchée."
        ),
        PageBreak(),
    ]

    for profil in ORDRE:
        etapes = par_profil.get(profil)
        if not etapes:
            continue
        contenu.append(titre(_TITRES[profil], "h1"))
        contenu.append(p(_INTROS[profil]))
        contenu.append(
            tableau(
                [["N°", "Action exécutée", "Ce que la plateforme a répondu"]]
                + [
                    [str(index), etape["action"], etape["constat"]]
                    for index, etape in enumerate(etapes, 1)
                ],
                [26, 174, 230],
                taille=8,
            )
        )
        contenu.append(
            legende(
                f"{len(etapes)} étape(s), "
                f"{sum(1 for e in etapes if e['capture'])} écran(s) capturé(s). "
                "Les captures figurent dans le guide du profil concerné."
            )
        )
        contenu.append(Spacer(1, 5 * mm))

    contenu += [
        PageBreak(),
        titre("Ce que le parcours a établi", "h1"),
        tableau(
            [
                ["Règle attendue", "Observation"],
                [
                    "Le profil déclaré à la connexion est vérifié contre le compte",
                    "Un compte superviseur déclarant « administrateur » est "
                    "refusé, avec un message qui nomme le bon profil.",
                ],
                [
                    "L'agence déclarée est vérifiée contre le périmètre",
                    "Une agence autre que celle du compte est refusée, en "
                    "nommant celle qui est attendue.",
                ],
                [
                    "Un abonnement déclaré exige son numéro",
                    "L'enregistrement est bloqué tant que le numéro relevé "
                    "manque, avec la raison affichée.",
                ],
                [
                    "La confrontation au référentiel tranche par le numéro",
                    "Deux abonnements déclarés à l'identique : celui dont le "
                    "numéro correspond est confirmé, l'autre infirmé.",
                ],
                [
                    "Un itinéraire n'est confié qu'une fois par jour et par agent",
                    "La seconde tentative est refusée en nommant l'agent et la "
                    "date, au lieu de créer un doublon.",
                ],
                [
                    "L'agent de terrain n'a accès qu'à son espace",
                    "Une entrée de navigation sur une, et une adresse saisie à "
                    "la main ramène sur Mon espace.",
                ],
                [
                    "Le superviseur ne voit que son agence",
                    "Le bordereau n'affiche que les lignes de "
                    "CSC_NGAOUNDERE SUD ; l'administrateur voit le national.",
                ],
            ],
            [190, 240],
        ),
        Spacer(1, 6 * mm),
        p(
            "Le parcours est rejouable : <font face='Courier'>python "
            "scripts/captures.py</font> le déroule à nouveau et régénère les "
            "captures, <font face='Courier'>python scripts/generer_guides.py"
            "</font> reconstruit les quatre guides et ce rapport.",
            "legende",
        ),
    ]
    return contenu


_TITRES = {
    "Commun": "Parcours d'entrée, commun aux quatre profils",
    "Superviseur": "Parcours du superviseur",
    "Agent de terrain": "Parcours de l'agent de terrain",
    "Administrateur": "Parcours de l'administrateur",
    "Super utilisateur": "Parcours du super utilisateur",
}

_INTROS = {
    "Commun": (
        "La connexion en trois temps, le refus d'un poste incohérent, et les "
        "deux écrans qui encadrent le cycle de vie d'un compte."
    ),
    "Superviseur": (
        "La journée complète : du briefing du matin à la confrontation au "
        "référentiel, en passant par la saisie de la production."
    ),
    "Agent de terrain": (
        "Le parcours le plus court, et la vérification qu'il l'est vraiment."
    ),
    "Administrateur": (
        "La gouvernance des accès, depuis la demande en attente jusqu'à "
        "l'attribution du périmètre."
    ),
    "Super utilisateur": (
        "Les mêmes gestes que l'administrateur, exercés sur un rang de plus."
    ),
}
