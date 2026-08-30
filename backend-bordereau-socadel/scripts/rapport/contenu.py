"""Contenu rédactionnel du dossier de conception."""

from __future__ import annotations

from datetime import date

from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, NextPageTemplate, PageBreak, Spacer

from . import diagrammes
from .document import encadre, legende, p, puces, tableau, titre


def _couverture() -> list:
    return [
        Spacer(1, 42 * mm),
        p("BORDEREAU INTELLIGENT DE COLLECTE WHATSAPP", "sous_titre_couverture"),
        Spacer(1, 6 * mm),
        p("Dossier de conception", "titre_couverture"),
        Spacer(1, 4 * mm),
        p(
            "Analyse du besoin · parties prenantes · modélisation UML<br/>"
            "architecture logicielle · habilitations RBAC et ABAC",
            "sous_titre_couverture",
        ),
        Spacer(1, 30 * mm),
        tableau(
            [
                ["Rubrique", "Valeur"],
                ["Client", "SOCADEL — Société Camerounaise d'Electricité"],
                ["Maître d'œuvre", "NEXT LTD — Numeric Export Technologies"],
                ["Objet", "Back-office de pilotage de la collecte de numéros WhatsApp"],
                ["Version du document", "1.0"],
                ["Date", date.today().strftime("%d/%m/%Y")],
                ["Statut", "Document de conception — base de test en cours"],
            ],
            [110, 320],
            taille=8.5,
        ),
        Spacer(1, 20 * mm),
        p(
            "Ce dossier décrit la conception effectivement appliquée dans le code. "
            "Il est généré depuis le dépôt : toute évolution du modèle se répercute "
            "en le régénérant.",
            "legende",
        ),
    ]


def _sommaire() -> list:
    return [
        PageBreak(),
        titre("Sommaire", "h1"),
        tableau(
            [
                ["§", "Section", "Contenu"],
                ["1", "Le besoin", "Constat, objectif chiffré, ce que le système résout"],
                ["2", "Parties prenantes", "Six entités, leurs responsabilités, matrice RACI"],
                ["3", "Acteurs du système", "Trois rôles applicatifs et trois systèmes externes"],
                ["4", "Cas d'utilisation", "Un diagramme par acteur, avec le détail des cas"],
                ["5", "Modèle du domaine", "Diagramme de classes et règles métier portées"],
                ["6", "Dynamique", "Trois diagrammes de séquence, un diagramme d'activité"],
                ["7", "Architecture", "Clean architecture, couches et règle de dépendance"],
                ["8", "Modèle de données", "Tables PostgreSQL, cardinalités, volumétrie"],
                ["9", "Habilitations", "RBAC, ABAC, matrice complète des permissions"],
                ["10", "Charte graphique", "Couleurs, thèmes, palette des graphiques"],
                ["11", "Décisions", "Choix structurants et leur justification"],
                ["12", "Limites", "Ce qui reste ouvert et ce qui est hors périmètre"],
            ],
            [26, 130, 274],
        ),
    ]


def _besoin() -> list:
    return [
        PageBreak(),
        titre("1. Le besoin", "h1"),
        p(
            "SOCADEL distribue ses factures d'électricité sur support papier. Plus "
            "d'un client sur deux est aujourd'hui injoignable par voie numérique : "
            "sur <b>926 705 contacts en base</b>, seuls <b>428 867 sont qualifiés "
            "valides</b>, soit 46,28 %. Chaque contact non qualifié est une facture "
            "qui n'arrive pas, un client au guichet, une réclamation à traiter."
        ),
        p(
            "NEXT LTD a développé un ChatBot WhatsApp, authentifié au nom de SOCADEL "
            "auprès de Meta, qui permet à un client de recevoir sa facture "
            "numérique en moins de deux minutes. Reste à collecter les numéros : "
            "c'est l'objet de la campagne, et c'est ce que cette application pilote."
        ),
        titre("L'objectif, par paliers"),
        tableau(
            [
                ["Palier", "Cible", "Contacts qualifiés", "À collecter", "Rythme"],
                ["Palier 1", "60 %", "556 023", "+ 127 156", "≈ 4 240 / jour"],
                ["Palier 2", "75 %", "695 029", "+ 266 162", "≈ 8 870 / jour"],
                ["Cible", "90 %", "834 034", "+ 405 167", "≈ 13 500 / jour"],
            ],
            [70, 55, 110, 100, 100],
            aligne_a_droite=[1, 2, 3, 4],
        ),
        legende(
            "Les paliers rendent la progression lisible chaque semaine et permettent "
            "de réajuster le dispositif avant la fin de la campagne."
        ),
        titre("Le problème que l'application résout"),
        p(
            "Les agents de terrain — les distributeurs, qui font déjà la tournée des "
            "factures papier — parcourent des itinéraires de relève et accompagnent "
            "les clients dans le parcours d'enrôlement. Ils travaillent sur papier. "
            "C'est le superviseur qui saisit leur production dans l'application, "
            "agent par agent, jour après jour."
        ),
        encadre(
            "<b>Le principe fondateur.</b> Une déclaration de superviseur n'est pas "
            "une vérité. Quand un client s'abonne réellement, son contrat remonte au "
            "référentiel SOCADEL via le ChatBot et la plateforme MRA. Le système "
            "confronte alors chaque déclaration à ce référentiel — et c'est ce "
            "recoupement, jamais la déclaration seule, qui détermine ce qui sera payé "
            "à l'agent. La recommandation métier est explicite : « verser la prime "
            "uniquement sur les parcours menés jusqu'à la confirmation finale »."
        ),
        Spacer(1, 5 * mm),
        p(
            "Cette règle se lit directement dans le code, sur la propriété "
            "<font face='Courier'>LigneBordereau.est_remuneree</font> : elle n'est "
            "vraie que si la ligne est déclarée ABONNE <i>et</i> que le verdict de "
            "vérification est CONFIRME."
        ),
    ]


def _parties_prenantes() -> list:
    return [
        PageBreak(),
        titre("2. Les parties prenantes", "h1"),
        p(
            "La réussite de la campagne tient à la coordination de six entités sur "
            "une fenêtre courte. Toutes ne sont pas utilisatrices de l'application : "
            "la distinction est importante pour comprendre le périmètre."
        ),
        tableau(
            [
                ["Entité", "Responsabilité", "Utilise l'app ?"],
                ["NEXT LTD", "ChatBot, plateforme, support technique, suivi des enrôlements", "Oui — administrateur"],
                ["SOCADEL", "Donneur d'ordre, émetteur des factures", "Oui — superviseurs"],
                ["Régions / Centres de relève / DPSR", "Impression, distribution des supports, collecte terrain", "Oui — agents"],
                ["DASI", "Configuration du tunnel entre le ChatBot et la facturation", "Non"],
                ["Facturation", "Push WhatsApp, traitement des données à J+1, ajustements", "Non — via MRA"],
                ["DCO / Marketing", "Communication de l'opération, interne et partenaires", "Non"],
            ],
            [110, 240, 80],
        ),
        titre("Matrice de responsabilité (RACI)"),
        p(
            "R = réalise · A = approuve · C = consulté · I = informé. Elle porte sur "
            "les activités que l'application soutient, pas sur la campagne entière."
        ),
        tableau(
            [
                ["Activité", "NEXT", "SOCADEL", "Régions", "Facturation"],
                ["Fournir la plateforme et le support", "R / A", "I", "I", "I"],
                ["Affecter les itinéraires aux agents", "C", "R / A", "C", "I"],
                ["Collecter sur le terrain", "I", "A", "R", "I"],
                ["Saisir la production dans l'application", "C", "R / A", "I", "I"],
                ["Confirmer les abonnements (référentiel)", "R", "I", "I", "A"],
                ["Décider de la prime", "C", "A", "I", "C"],
            ],
            [190, 60, 70, 70, 80],
            aligne_a_droite=[1, 2, 3, 4],
        ),
    ]


def _acteurs() -> list:
    return [
        PageBreak(),
        titre("3. Les acteurs du système", "h1"),
        p(
            "Trois rôles disposent d'un compte de connexion, et trois systèmes "
            "externes interviennent dans le flux sans que l'application les pilote."
        ),
        titre("Acteurs humains"),
        tableau(
            [
                ["Acteur", "Ce qu'il fait", "Portée des données"],
                [
                    "Administrateur",
                    "Ouvre et ferme les accès, rattache les comptes agent à leur "
                    "fiche, définit les périmètres. Exerce aussi tous les droits du "
                    "superviseur.",
                    "Toutes les données, sans restriction",
                ],
                [
                    "Superviseur",
                    "Affecte les itinéraires, imprime les bordereaux, saisit la "
                    "production, importe, vérifie, exporte. Gère le répertoire des "
                    "agents (CRUD complet).",
                    "Son périmètre territorial, ou national si aucun n'est défini",
                ],
                [
                    "Agent de terrain",
                    "Se connecte et consulte ses itinéraires confiés, ses KPI et son "
                    "évolution. Rien d'autre : il travaille sur papier.",
                    "Sa seule production, imposée par la garde ABAC",
                ],
            ],
            [90, 250, 130],
        ),
        titre("Systèmes externes"),
        tableau(
            [
                ["Système", "Rôle", "Relation"],
                ["ChatBot WhatsApp", "Enrôle le client en six étapes, dans WhatsApp", "Hors périmètre — NEXT LTD"],
                ["Plateforme MRA", "Gestion des factures SOCADEL ; reçoit l'enrôlement", "Hors périmètre — SOCADEL"],
                ["Référentiel clients", "Source de vérité des abonnements confirmés", "Consommé en lecture"],
            ],
            [110, 220, 140],
        ),
        Spacer(1, 5 * mm),
        diagrammes.contexte(),
        legende(
            "Diagramme de contexte — le système, ses acteurs et son écosystème. "
            "Les liens pointillés marquent ce qui reste hors périmètre."
        ),
    ]


def _cas_utilisation() -> list:
    return [
        PageBreak(),
        titre("4. Cas d'utilisation par acteur", "h1"),
        p(
            "Un diagramme par acteur plutôt qu'un seul diagramme global : la portée "
            "de chaque rôle est justement ce qu'il faut faire ressortir, et un "
            "diagramme unique la noierait."
        ),
        titre("4.1 Superviseur — l'acteur principal"),
        diagrammes.cas_superviseur(),
        legende("Cas d'utilisation du superviseur."),
        titre("Détail des cas"),
        tableau(
            [
                ["Cas", "Déclencheur", "Résultat"],
                ["Affecter des itinéraires", "L'agent se présente au briefing", "Affectations créées + une ligne de bordereau par client"],
                ["Imprimer le bordereau terrain", "Départ de l'agent en tournée", "PDF filigrané, colonnes pré-remplies, colonne de relevé vierge"],
                ["Saisir la production", "Retour du terrain, bordereau papier en main", "Statut, numéro relevé et origine enregistrés par ligne"],
                ["Corriger en lot", "Plusieurs lignes au même statut", "Statut appliqué ; les lignes que le domaine refuse sont signalées"],
                ["Importer un bordereau", "Fichier rempli par un agent", "Aperçu, puis écriture en une transaction après validation"],
                ["Vérifier", "Fin de journée ou de campagne", "Verdict par ligne : confirmé, infirmé, introuvable"],
                ["Exporter", "Besoin de transmettre ou d'archiver", "CSV ou PDF, exactement le périmètre affiché"],
                ["Gérer les agents", "Arrivée, changement, départ d'un collecteur", "Fiche créée, modifiée ou retirée du service"],
            ],
            [95, 145, 230],
        ),
        PageBreak(),
        titre("4.2 Agent de terrain — consultation seule", "h2"),
        diagrammes.cas_agent(),
        legende("Cas d'utilisation de l'agent de terrain."),
        encadre(
            "<b>Pourquoi si peu.</b> L'agent collecte sur le terrain, avec un "
            "bordereau papier : c'est son outil de travail, et il n'a ni le temps ni "
            "toujours le réseau pour saisir en mobilité. La plateforme ne lui sert "
            "qu'à voir où il en est. Ce choix a une conséquence de sécurité "
            "appréciable : son compte, même compromis, ne permet aucune écriture."
        ),
        Spacer(1, 6 * mm),
        titre("4.3 Administrateur — gouvernance des accès", "h2"),
        diagrammes.cas_administrateur(),
        legende("Cas d'utilisation de l'administrateur."),
    ]


def _domaine() -> list:
    return [
        NextPageTemplate("paysage"),
        PageBreak(),
        titre("5. Le modèle du domaine", "h1"),
        p(
            "Le domaine est modélisé en objets porteurs de règles, pas en structures "
            "de données anémiques. Les invariants sont dans les entités : une ligne "
            "déclarée abonnée sans numéro relevé est refusée par "
            "<font face='Courier'>LigneBordereau.declarer()</font>, pas par un "
            "contrôle de formulaire."
        ),
        diagrammes.classes_domaine(),
        legende(
            "Diagramme de classes du domaine. En vert la ligne de bordereau — ce que "
            "le superviseur déclare ; en orange le client — ce que le référentiel "
            "établit. Le service de vérification confronte les deux."
        ),
        NextPageTemplate("portrait"),
        PageBreak(),
        titre("Les objets-valeurs", "h2"),
        p(
            "Quatre notions métier sont modélisées en objets-valeurs immuables et "
            "auto-validants, plutôt qu'en chaînes de caractères. Elles portent leur "
            "propre normalisation, ce qui évite d'avoir à s'en souvenir à chaque "
            "usage."
        ),
        tableau(
            [
                ["Objet-valeur", "Ce qu'il garantit", "Exemple"],
                ["NumeroTelephone", "Format E.164 camerounais. Absorbe les saisies hétérogènes du terrain.", "« 694174768 » → +237694174768"],
                ["ServiceNo", "Identifiant de contrat. Clé de jointure avec le référentiel.", "203401046"],
                ["RefGeo", "Adresse technique, et surtout <b>l'ordre de marche</b> : le tri par clé numérique restitue le parcours physique des maisons.", "807-09-01-994-00-001"],
                ["CodeItineraire", "Unité de travail confiée à un agent.", "42422 (CSC_ESSOS)"],
            ],
            [95, 250, 125],
        ),
        encadre(
            "<b>Pourquoi RefGeo mérite un objet.</b> Le bordereau papier doit suivre "
            "l'ordre des maisons, sinon l'agent zigzague dans le quartier. Trier sur "
            "la chaîne brute donnerait un ordre lexicographique faux : « 960-20-11-92 » "
            "passerait avant « 960-20-11-232 ». La propriété "
            "<font face='Courier'>cle_tri</font> convertit chaque segment en entier "
            "et rétablit l'ordre réel."
        ),
        Spacer(1, 5 * mm),
        titre("La règle de vérification", "h2"),
        p(
            "C'est le cœur du dispositif. Elle est isolée dans un service de domaine "
            "pur — sans base ni transport — et se lit en quelques lignes :"
        ),
        tableau(
            [
                ["Déclaration", "État du référentiel", "Verdict", "Payable"],
                ["ABONNE", "Contrat absent du référentiel", "INTROUVABLE", "Non"],
                ["ABONNE", "whatsapp_status ≠ subscribed", "INFIRME", "Non"],
                ["ABONNE", "subscribed, mais autre numéro", "INFIRME", "Non"],
                ["ABONNE", "subscribed, numéro concordant", "CONFIRME", "<b>Oui</b>"],
                ["ABSENT / REFUS / …", "Non abonné au référentiel", "CONFIRME", "Non"],
                ["ABSENT / REFUS / …", "Abonné au référentiel", "INFIRME", "Non"],
            ],
            [95, 175, 100, 100],
            aligne_a_droite=[2, 3],
        ),
        legende(
            "Une nouvelle déclaration remet automatiquement le verdict à "
            "NON_VERIFIE : corriger une ligne oblige à la re-confronter."
        ),
    ]


def _dynamique() -> list:
    return [
        NextPageTemplate("paysage"),
        PageBreak(),
        titre("6. La dynamique du système", "h1"),
        titre("6.1 Le briefing du matin", "h2"),
        p(
            "C'est le premier geste de la journée, et l'écran qui s'ouvre juste après "
            "la connexion du superviseur. L'agent se présente, on note les itinéraires "
            "qu'on lui confie. L'opération fait deux choses d'un coup : elle trace le "
            "briefing et elle <b>matérialise le bordereau</b>."
        ),
        diagrammes.sequence_affectation(),
        legende("Séquence — affectation d'un itinéraire et génération du bordereau."),
        encadre(
            "<b>Plusieurs itinéraires, plusieurs fois.</b> Un bon collecteur reçoit "
            "plusieurs tournées, parfois en cours de journée. Chaque appel ajoute des "
            "affectations sans toucher aux précédentes, et les chiffres de l'agent se "
            "mettent à jour. L'unicité (agent, itinéraire, jour) empêche seulement de "
            "compter deux fois la même tournée."
        ),
        PageBreak(),
        titre("6.2 La saisie et le recoupement", "h2"),
        diagrammes.sequence_verification(),
        legende(
            "Séquence — déclaration du superviseur, puis confrontation au référentiel."
        ),
        Spacer(1, 4 * mm),
        titre("6.3 L'import en deux temps", "h2"),
        p(
            "Le métier a demandé un aperçu avant toute écriture. Le flux est donc "
            "strictement séquentiel : analyser, montrer, puis écrire seulement si le "
            "superviseur confirme."
        ),
        diagrammes.sequence_import(),
        legende("Séquence — import d'un bordereau rempli."),
        NextPageTemplate("portrait"),
        PageBreak(),
        titre("6.4 Le parcours d'enrôlement du client", "h2"),
        p(
            "Ce parcours se déroule <b>hors de l'application</b>, dans WhatsApp. Il "
            "est reproduit ici parce qu'il explique ce que « abonné » veut dire, et "
            "pourquoi le référentiel peut faire foi."
        ),
        diagrammes.activite_enrolement(),
        legende(
            "Diagramme d'activité — l'enrôlement WhatsApp, de la présentation du QR "
            "code à la remontée vers le référentiel."
        ),
    ]


def _architecture() -> list:
    return [
        PageBreak(),
        titre("7. L'architecture logicielle", "h1"),
        p(
            "Le backend suit la clean architecture. Ce n'est pas une préférence "
            "esthétique : le métier a annoncé que la base actuelle est une base de "
            "test et que la vraie source de vérité arrivera par une API tierce. Le "
            "système doit donc pouvoir changer de source sans être réécrit."
        ),
        diagrammes.architecture(),
        legende("Les quatre couches et le sens des dépendances."),
        tableau(
            [
                ["Couche", "Contient", "Ne connaît pas"],
                ["domain/", "Entités, objets-valeurs, services de domaine, politique d'habilitation", "Rien — aucun framework"],
                ["application/", "Cas d'usage, ports (protocoles), DTO", "Aucun framework ; seulement le domaine"],
                ["infrastructure/", "PostgreSQL, bcrypt, JWT, openpyxl, reportlab, stockage média", "—"],
                ["interfaces/", "Routes HTTP, schémas Pydantic, mappage des erreurs", "La base de données"],
            ],
            [80, 250, 140],
        ),
        encadre(
            "<b>Ce que cela achète concrètement.</b> Le jour où l'API de recoupement "
            "NEXT sera ouverte, un seul adaptateur sera à écrire : une implémentation "
            "de <font face='Courier'>ClientRepository</font> qui interroge l'API au "
            "lieu de la table. Ni les cas d'usage, ni les règles de vérification, ni "
            "les routes ne bougeront."
        ),
        Spacer(1, 5 * mm),
        p(
            "La discipline est vérifiable, pas déclarative : les couches "
            "<font face='Courier'>domain</font> et "
            "<font face='Courier'>application</font> s'importent sur un interpréteur "
            "sans aucune dépendance installée. C'est aussi ce qui permet à la suite de "
            "tests d'exercer l'API HTTP complète en remplaçant PostgreSQL par des "
            "doubles en mémoire, sans toucher une ligne de code de production."
        ),
        titre("Le frontend"),
        p(
            "La même règle est transposée au découpage par fonctionnalité : le dossier "
            "<font face='Courier'>app/</font> ne fait que du routage, et chaque "
            "fonctionnalité est découpée en "
            "<font face='Courier'>infrastructure</font> (appels HTTP), "
            "<font face='Courier'>application</font> (hooks, état) et "
            "<font face='Courier'>ui</font> (composants)."
        ),
    ]


def _donnees() -> list:
    return [
        NextPageTemplate("paysage"),
        PageBreak(),
        titre("8. Le modèle de données", "h1"),
        diagrammes.modele_donnees(),
        legende(
            "Modèle physique PostgreSQL. Les volumétries indiquées sont celles de la "
            "base de test actuellement chargée."
        ),
        NextPageTemplate("portrait"),
        PageBreak(),
        titre("Volumétrie et conséquences de conception", "h2"),
        p(
            "Le référentiel compte <b>425 920 clients</b> et <b>16 763 itinéraires</b>. "
            "Cette échelle n'est pas un détail d'exploitation : elle a dicté plusieurs "
            "choix structurants."
        ),
        tableau(
            [
                ["Contrainte", "Conséquence retenue"],
                ["Table de 425 920 lignes", "Filtres, tri et pagination traduits en SQL, jamais appliqués en mémoire"],
                ["Vérification d'un lot", "Chargement des clients en une seule requête groupée, au lieu d'un accès par ligne"],
                ["Limite de 32 767 paramètres liés (PostgreSQL)", "Insertions découpées en lots calculés à partir du nombre de colonnes"],
                ["Import du référentiel (46 Mo)", "Lecture en flux, écriture par paquets de 5 000 — le classeur n'est jamais chargé entier"],
                ["Exports potentiellement massifs", "Plafond de 50 000 lignes, signalé au client par un en-tête dédié"],
                ["Cinq requêtes de KPI en parallèle", "Une session par requête : une session SQLAlchemy ne supporte qu'une opération à la fois"],
            ],
            [180, 290],
        ),
    ]


def _habilitations() -> list:
    return [
        PageBreak(),
        titre("9. Les habilitations", "h1"),
        p(
            "Deux mécanismes répondent à deux questions distinctes. Les confondre est "
            "la source habituelle des fuites de données."
        ),
        diagrammes.habilitations(),
        legende("RBAC et ABAC — le « quoi » et le « sur quoi »."),
        encadre(
            "<b>Le choix décisif.</b> L'ABAC ne valide pas un accès déjà formulé : il "
            "<b>réécrit le filtre</b> avant qu'il n'atteigne la base. Un agent qui "
            "demanderait explicitement la production d'un collègue voit son paramètre "
            "écrasé, et obtient zéro ligne. Un contrôle a posteriori aurait dû être "
            "appelé partout, et il aurait suffi de l'oublier une fois."
        ),
        PageBreak(),
        titre("Matrice complète des permissions", "h2"),
        _matrice_permissions(),
        legende(
            "Matrice RBAC appliquée dans le code "
            "(<font face='Courier'>domain/securite/permissions.py</font>). "
            "L'administrateur porte l'intégralité des permissions."
        ),
        titre("Règles ABAC", "h2"),
        tableau(
            [
                ["Rôle", "Rétrécissement appliqué"],
                ["Administrateur", "Aucun — périmètre complet"],
                ["Superviseur", "Sa région et son agence, si un périmètre lui est défini ; sinon national"],
                ["Agent de terrain", "Son propre agent_id, imposé quoi qu'il demande"],
            ],
            [110, 360],
        ),
    ]


def _matrice_permissions():
    """Matrice construite depuis le code, pas recopiée à la main."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from bordereau.domain.enums import Role
    from bordereau.domain.securite import MATRICE, Permission

    lignes = [["Permission", "Admin.", "Superviseur", "Agent"]]
    for permission in Permission:
        lignes.append(
            [
                permission.value,
                *[
                    "✓" if permission in MATRICE[role] else "—"
                    for role in (
                        Role.ADMINISTRATEUR,
                        Role.SUPERVISEUR,
                        Role.AGENT_TERRAIN,
                    )
                ],
            ]
        )

    return tableau(lignes, [200, 80, 100, 90], aligne_a_droite=[1, 2, 3], taille=7.5)


def _charte() -> list:
    return [
        PageBreak(),
        titre("10. La charte graphique", "h1"),
        p(
            "L'identité repose sur deux couleurs seulement : le <b>bleu du logo "
            "SOCADEL</b> et le <b>blanc</b>. Le bleu a été échantillonné directement "
            "sur le fichier fourni, pas approché à l'œil."
        ),
        tableau(
            [
                ["Rôle", "Valeur", "Usage"],
                ["Bleu SOCADEL", "#1A76B9", "Couleur primaire : actions, en-têtes, accents, PDF"],
                ["Blanc", "#FFFFFF", "Surface des cartes et des tableaux, texte sur bleu"],
                ["Fond clair", "#F6F8FB", "Arrière-plan de l'application en thème clair"],
                ["Fond sombre", "#0B1220", "Arrière-plan en thème sombre"],
                ["Surface sombre", "#111A2B", "Cartes et tableaux en thème sombre"],
            ],
            [95, 80, 295],
        ),
        titre("Thèmes clair et sombre"),
        p(
            "Le thème sombre n'est pas une inversion automatique : ses valeurs sont "
            "choisies pour leur propre surface. L'utilisateur dispose de trois états — "
            "clair, sombre, ou suivre le système — et son choix est conservé."
        ),
        titre("Couleurs des graphiques"),
        p(
            "La palette a été validée pour la déficience de vision des couleurs et "
            "pour le contraste, sur les deux surfaces réellement utilisées."
        ),
        tableau(
            [
                ["Série", "Clair (#FFFFFF)", "Sombre (#111A2B)"],
                ["Clients démarchés", "#1A76B9", "#3B93DC"],
                ["Abonnements déclarés", "#EB6834", "#D95926"],
                ["Abonnements confirmés", "#1BAF7A", "#199E70"],
            ],
            [180, 145, 145],
            aligne_a_droite=[1, 2],
        ),
        legende(
            "Écart minimal entre teintes adjacentes sous simulation de daltonisme : "
            "ΔE 9,2 en clair et 9,4 en sombre, pour un seuil de 8. L'identité d'une "
            "série ne repose jamais sur la seule couleur : légende permanente, "
            "étiquette en fin de courbe et vue tableau."
        ),
        titre("Internationalisation"),
        p(
            "L'interface est intégralement disponible en français et en anglais. Le "
            "français est la langue de référence — celle du métier SOCADEL — et le "
            "type des clés de traduction est dérivé du dictionnaire français : une clé "
            "oubliée en anglais devient une erreur de compilation, pas une chaîne "
            "manquante découverte en production."
        ),
    ]


def _decisions() -> list:
    return [
        PageBreak(),
        titre("11. Les décisions de conception", "h1"),
        p(
            "Les choix ci-dessous ont été pris en connaissance de leurs alternatives. "
            "Ils sont listés avec ce qui les motive."
        ),
        _decision(
            "Le référentiel fait foi, jamais la déclaration",
            "Une ligne n'est payable que si elle est déclarée abonnée et confirmée "
            "par le référentiel. C'est la traduction directe de la recommandation "
            "métier sur la prime, et le dispositif devient auto-contrôlé.",
        ),
        _decision(
            "Affecter matérialise le bordereau",
            "L'affectation crée immédiatement une ligne par client de l'itinéraire, "
            "en recopiant les données du client. Le bordereau reste ainsi lisible tel "
            "qu'il a été émis, même si le référentiel évolue ensuite.",
        ),
        _decision(
            "Un seul objet de filtre",
            "Le même objet sert le listing, les exports et les KPI. C'est ce qui "
            "garantit qu'un export contient exactement ce que le superviseur voit à "
            "l'écran — un écart entre les deux serait invisible et coûteux.",
        ),
        _decision(
            "Lecture et écriture séparées pour les indicateurs",
            "Les KPI ne chargent pas d'entités : un port dédié renvoie directement "
            "des DTO, traduits en agrégations SQL. Agréger 425 920 lignes en mémoire "
            "n'aurait aucun sens.",
        ),
        _decision(
            "Un agent n'est jamais supprimé",
            "« Supprimer » signifie retirer du service. Les bordereaux passés "
            "référencent l'agent et fondent sa rémunération : les effacer détruirait "
            "la preuve du travail accompli.",
        ),
        _decision(
            "L'import se fait en deux temps",
            "Analyse à blanc, aperçu, puis écriture sur confirmation. Rien n'est "
            "écrit tant que le superviseur n'a pas vu ce qui passerait et ce qui "
            "serait rejeté, avec le motif de chaque rejet.",
        ),
        _decision(
            "Le compte agent est en lecture seule",
            "Conséquence directe du fonctionnement réel : l'agent travaille sur "
            "papier. Bénéfice de sécurité, son compte ne permet aucune écriture même "
            "s'il était compromis.",
        ),
        _decision(
            "Le filigrane sur les documents",
            "Une page imprimée circule seule, détachée de l'application. Le logo en "
            "filigrane atteste de son origine, et son opacité de 6 % ne gêne ni la "
            "lecture ni l'écriture au stylo dans les cases.",
        ),
    ]


def _decision(titre_court: str, justification: str):
    return KeepTogether(
        [
            p(f"<b>{titre_court}</b>", "h3"),
            p(justification),
        ]
    )


def _limites() -> list:
    return [
        PageBreak(),
        titre("12. Limites connues et suite", "h1"),
        p(
            "Ce qui suit est énoncé sans détour : un dossier de conception qui tairait "
            "ses zones d'ombre ne servirait à rien."
        ),
        titre("Ce qui reste ouvert"),
        tableau(
            [
                ["Sujet", "État actuel", "Ce qu'il faut"],
                [
                    "API de recoupement NEXT / MRA",
                    "Non ouverte. La vérification s'appuie sur une base de test "
                    "chargée depuis un export.",
                    "Un adaptateur <font face='Courier'>ClientRepository</font> "
                    "interrogeant l'API. Le reste du système est prêt.",
                ],
                [
                    "Périmètre territorial des superviseurs",
                    "Le mécanisme existe et est testé, mais aucun périmètre n'est "
                    "attribué : tous les superviseurs sont nationaux.",
                    "Renseigner région et agence sur les comptes concernés.",
                ],
                [
                    "Migrations Alembic",
                    "Configurées, mais le schéma a été créé directement pour les "
                    "essais.",
                    "Générer la révision initiale avant la mise en production.",
                ],
                [
                    "Mot de passe et clé de signature",
                    "Valeurs de développement.",
                    "À remplacer impérativement avant toute exposition.",
                ],
            ],
            [110, 180, 180],
        ),
        titre("Hors périmètre assumé"),
        *puces(
            [
                "Le ChatBot WhatsApp et son tunnel : développés et exploités par NEXT LTD, "
                "hors de cette application.",
                "La plateforme MRA : c'est un système SOCADEL distinct, que "
                "l'application ne pilote pas et ne remplace pas.",
                "Le calcul et le versement effectif de la prime : l'application "
                "fournit la base vérifiée, la décision reste métier.",
                "La saisie en mobilité par l'agent : écartée volontairement, le "
                "travail de terrain se fait sur papier.",
            ]
        ),
        Spacer(1, 8 * mm),
        encadre(
            "<b>Sur la qualité du logiciel.</b> Le backend est couvert par 91 tests "
            "automatisés — domaine, cas d'usage, adaptateurs de fichiers et API HTTP "
            "complète, habilitations comprises. Le parcours complet a par ailleurs été "
            "déroulé contre une instance PostgreSQL réelle chargée des 425 920 clients."
        ),
    ]


def contenu() -> list:
    """Assemble le document dans l'ordre."""
    return [
        *_couverture(),
        *_sommaire(),
        *_besoin(),
        *_parties_prenantes(),
        *_acteurs(),
        *_cas_utilisation(),
        *_domaine(),
        *_dynamique(),
        *_architecture(),
        *_donnees(),
        *_habilitations(),
        *_charte(),
        *_decisions(),
        *_limites(),
    ]
