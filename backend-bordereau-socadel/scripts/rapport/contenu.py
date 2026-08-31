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
                [
                    "Destinataire",
                    "M. TONDJOU Patrick<br/>"
                    "<font size='8'>Directeur des Systèmes d'Information et de "
                    "la Technologie, NEXT LTD</font>",
                ],
                [
                    "Rédigé par",
                    "TONBA Loïc<br/>"
                    "<font size='8'>Ingénieur des travaux informatiques, "
                    "développeur web senior, NEXT LTD</font>",
                ],
                ["Client", "SOCADEL, Société Camerounaise d'Electricité"],
                ["Objet", "Back-office de pilotage de la collecte de numéros WhatsApp"],
                ["Version du document", "2.0"],
                ["Date", date.today().strftime("%d/%m/%Y")],
                ["Statut", "Document de conception, base de test en cours"],
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
                ["3", "Acteurs du système", "Quatre rôles applicatifs et trois systèmes externes"],
                ["4", "Cas d'utilisation", "Un diagramme par acteur, avec le détail des cas"],
                ["5", "Parcours par profil", "Inscription, connexion, journée de chaque acteur"],
                ["6", "Modèle du domaine", "Diagramme de classes et règles métier portées"],
                ["7", "Dynamique", "Trois diagrammes de séquence, un diagramme d'activité"],
                ["8", "Architecture", "Clean architecture, couches et règle de dépendance"],
                ["9", "Modèle de données", "Tables PostgreSQL, cardinalités, volumétrie"],
                ["10", "Habilitations", "RBAC, ABAC, hiérarchie des rôles, matrice complète"],
                ["11", "Ouverture des accès", "Inscription, courriels, territoire, rôles, audit"],
                ["12", "Changer de source", "Ce que coûtera la bascule vers l'API NEXT"],
                ["13", "Charte graphique", "Couleurs, thèmes, palette des graphiques"],
                ["14", "Décisions", "Choix structurants et leur justification"],
                ["15", "Limites", "Ce qui reste ouvert et ce qui est hors périmètre"],
            ],
            [26, 130, 274],
        ),
    ]


def _besoin() -> list:
    return [
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
        titre("L'objectif"),
        encadre(
            "<b>Faciliter la redistribution des factures SOCADEL par WhatsApp</b>, "
            "le réseau social le plus utilisé par les clients. Tout le reste, "
            "le bordereau papier, les itinéraires, la vérification, n'existe "
            "que pour servir cet objectif : mettre en face de chaque abonné un "
            "numéro WhatsApp valide, par lequel sa facture lui parviendra."
        ),
        Spacer(1, 5 * mm),
        p(
            "La collecte s'appuie sur un réseau déjà en place. SOCADEL compte "
            "<b>181 agences</b> réparties sur les dix régions du Cameroun, "
            "regroupées en 33 divisions et 9 directions régionales, pour un "
            "portefeuille de <b>425 920 clients</b> dans le référentiel chargé. "
            "Le détail de ce maillage fait l'objet d'un document séparé."
        ),
        titre("Le problème que l'application résout"),
        p(
            "Les agents de terrain, les distributeurs, qui font déjà la tournée des "
            "factures papier, parcourent des itinéraires de relève et accompagnent "
            "les clients dans le parcours d'enrôlement. Ils travaillent sur papier. "
            "C'est le superviseur qui saisit leur production dans l'application, "
            "agent par agent, jour après jour."
        ),
        encadre(
            "<b>Le principe fondateur.</b> Une déclaration de superviseur n'est pas "
            "une vérité. Quand un client s'abonne réellement, son contrat remonte au "
            "référentiel SOCADEL via le ChatBot et la plateforme MRA. Le système "
            "confronte alors chaque déclaration à ce référentiel, et c'est ce "
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
        titre("2. Les parties prenantes", "h1"),
        p(
            "La réussite de la campagne tient à la coordination de six entités sur "
            "une fenêtre courte. Toutes ne sont pas utilisatrices de l'application : "
            "la distinction est importante pour comprendre le périmètre."
        ),
        tableau(
            [
                ["Entité", "Responsabilité", "Utilise l'app ?"],
                ["NEXT LTD", "ChatBot, plateforme, support technique, suivi des enrôlements", "Oui, administrateur"],
                ["SOCADEL", "Donneur d'ordre, émetteur des factures", "Oui, superviseurs"],
                ["Régions / Centres de relève / DPSR", "Impression, distribution des supports, collecte terrain", "Oui, agents"],
                ["DASI", "Configuration du tunnel entre le ChatBot et la facturation", "Non"],
                ["Facturation", "Push WhatsApp, traitement des données à J+1, ajustements", "Non, via MRA"],
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
        titre("3. Les acteurs du système", "h1"),
        p(
            "Quatre rôles disposent d'un compte de connexion, répartis en deux "
            "camps. NEXT LTD édite et exploite la plateforme, d'où le super "
            "utilisateur. SOCADEL s'en sert, d'où l'administrateur, les "
            "superviseurs et les agents. Trois systèmes externes interviennent "
            "dans le flux sans que l'application les pilote."
        ),
        titre("Acteurs humains"),
        tableau(
            [
                ["Acteur", "Chez qui", "Ce qu'il fait", "Portée des données"],
                [
                    "Super utilisateur",
                    "NEXT LTD",
                    "Exploite la plateforme. Seul à pouvoir changer le rôle d'un "
                    "compte et administrer le référentiel, les deux leviers qui "
                    "engagent le fonctionnement du système lui-même.",
                    "Tout, sans restriction",
                ],
                [
                    "Administrateur",
                    "SOCADEL",
                    "Responsable côté client. Approuve les demandes d'accès, "
                    "attribue les périmètres, réinitialise les mots de passe de "
                    "ses équipes. Exerce aussi tous les droits du superviseur.",
                    "Toutes les données SOCADEL",
                ],
                [
                    "Superviseur",
                    "SOCADEL, une agence",
                    "Affecte les itinéraires, imprime les bordereaux, saisit la "
                    "production, importe, vérifie, exporte. Gère le répertoire "
                    "des agents.",
                    "Son agence ou sa région, obligatoirement",
                ],
                [
                    "Agent de terrain",
                    "SOCADEL, terrain",
                    "Se connecte et consulte ses itinéraires confiés et ses "
                    "chiffres. Rien d'autre : il travaille sur papier.",
                    "Sa seule production",
                ],
            ],
            [72, 78, 200, 120],
        ),
        encadre(
            "<b>La différence entre le super utilisateur et l'administrateur.</b> "
            "Elle n'est pas de degré mais de nature. L'administrateur SOCADEL "
            "<i>exploite</i> la plateforme : il ouvre les accès de ses équipes, "
            "définit qui voit quelle agence, débloque un mot de passe oublié. Le "
            "super utilisateur NEXT LTD en <i>répond</i> : il peut changer le "
            "rôle d'un compte existant, y compris promouvoir un administrateur, "
            "et administrer le référentiel sur lequel repose toute la "
            "vérification. Ces deux leviers touchent au fonctionnement du "
            "système, pas à son usage quotidien."
        ),
        titre("Systèmes externes"),
        tableau(
            [
                ["Système", "Rôle", "Relation"],
                ["ChatBot WhatsApp", "Enrôle le client en six étapes, dans WhatsApp", "Hors périmètre, NEXT LTD"],
                ["Plateforme MRA", "Gestion des factures SOCADEL ; reçoit l'enrôlement", "Hors périmètre, SOCADEL"],
                ["Référentiel clients", "Source de vérité des abonnements confirmés", "Consommé en lecture"],
            ],
            [110, 220, 140],
        ),
        Spacer(1, 4 * mm),
        titre("Comment lire ce diagramme", "h3"),
        p(
            "Le rectangle bleu au centre est la plateforme. À sa gauche, "
            "les bonshommes sont les personnes qui s'y connectent ; les "
            "flèches qui en partent disent ce que chacun vient y faire. "
            "À droite, les trois cadres pâles sont des systèmes qui "
            "existent indépendamment de nous. <b>Les flèches en pointillé "
            "signalent ce que la plateforme ne pilote pas</b> : le ChatBot "
            "et MRA appartiennent à d'autres périmètres. La seule flèche "
            "pleine vers la droite, « vérifie », est le lien que nous "
            "exerçons vraiment."
        ),
        KeepTogether(
            [
                diagrammes.contexte(),
                legende(
                    "Diagramme de contexte : le système, ses quatre acteurs et "
                    "son écosystème."
                ),
            ]
        ),
    ]


def _cas_utilisation() -> list:
    return [
        titre("4. Cas d'utilisation par acteur", "h1"),
        p(
            "Un diagramme par acteur plutôt qu'un seul diagramme global : la "
            "portée de chaque rôle est justement ce qu'il faut faire "
            "ressortir, et un diagramme unique la noierait."
        ),
        KeepTogether(
            [
                titre("Comment lire ces diagrammes", "h3"),
                p(
                    "Le grand cadre gris délimite la plateforme : ce qui est "
                    "dedans est réalisé par le logiciel. Chaque ovale est un "
                    "<b>cas d'utilisation</b>, c'est-à-dire un service rendu à "
                    "l'acteur, formulé de son point de vue et non du point de vue "
                    "technique. Les traits relient l'acteur aux cas qu'il peut "
                    "déclencher : leur nombre donne d'un coup d'œil l'étendue de "
                    "son rôle. Comparez les quatre diagrammes qui suivent, la "
                    "différence de longueur des listes est le message principal."
                ),
            ]
        ),
        KeepTogether(
            [
                titre("4.1 Superviseur, l'acteur principal", "h2"),
                diagrammes.cas_superviseur(),
                legende("Cas d'utilisation du superviseur."),
            ]
        ),
        titre("Détail des cas du superviseur", "h3"),
        tableau(
            [
                ["Cas", "Déclencheur", "Résultat"],
                ["Affecter des itinéraires", "L'agent se présente au briefing", "Affectations créées et une ligne de bordereau par client"],
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
        KeepTogether(
            [
                titre("4.2 Agent de terrain, consultation seule", "h2"),
                diagrammes.cas_agent(),
                legende("Cas d'utilisation de l'agent de terrain."),
            ]
        ),
        encadre(
            "<b>Pourquoi si peu.</b> L'agent collecte sur le terrain, avec un "
            "bordereau papier : c'est son outil de travail, et il n'a ni le "
            "temps ni toujours le réseau pour saisir en mobilité. La plateforme "
            "ne lui sert qu'à voir où il en est. Ce choix a une conséquence de "
            "sécurité appréciable : son compte, même compromis, ne permet aucune "
            "écriture."
        ),
        KeepTogether(
            [
                titre("4.3 Administrateur SOCADEL, gouvernance des accès", "h2"),
                diagrammes.cas_administrateur(),
                legende("Cas d'utilisation de l'administrateur."),
            ]
        ),
        KeepTogether(
            [
                titre("4.4 Super utilisateur NEXT LTD", "h2"),
                p(
                    "Deux cas seulement le distinguent de l'administrateur, mais "
                    "ce sont ceux qui engagent le fonctionnement du système."
                ),
                diagrammes.cas_super_utilisateur(),
                legende(
                    "Cas d'utilisation du super utilisateur. En bleu soutenu, "
                    "ce que lui seul peut faire."
                ),
            ]
        ),
    ]

def _parcours() -> list:
    return [
        NextPageTemplate("paysage"),
        PageBreak(),
        titre("5. Les parcours, profil par profil", "h1"),
        p(
            "Le chapitre précédent dit ce que chaque acteur <b>peut</b> faire. "
            "Il ne dit pas dans quel ordre, ni à quel moment de la journée. "
            "C'est pourtant l'ordre qui fait le travail : on n'imprime pas un "
            "bordereau avant d'avoir affecté les itinéraires, et on ne vérifie "
            "pas une production qui n'a pas encore été saisie."
        ),
        p(
            "Les cinq diagrammes qui suivent se lisent en même temps que le "
            "guide pratique : chaque étape numérotée correspond à un écran, "
            "dans le même ordre."
        ),
        KeepTogether(
            [
                titre("Comment lire ces diagrammes", "h3"),
                p(
                    "Chaque rectangle bleuté est une <b>étape</b>, numérotée dans "
                    "l'ordre où elle survient, et la ligne du dessous précise ce "
                    "qui s'y passe. Les flèches pleines enchaînent, les pointillés "
                    "marquent un passage que la plateforme ne pilote pas. <b>Les "
                    "cadres gris sont hors application</b> : c'est le travail de "
                    "terrain, papier en main. Le vert est un aboutissement, le "
                    "rouge un refus, le bleu plein une réserve."
                ),
            ]
        ),
        titre("5.1 S'inscrire et obtenir un accès", "h2"),
        p(
            "Le même pour les quatre profils, en trois temps et une décision : "
            "on se déclare, on prouve son adresse, un responsable tranche."
        ),
        KeepTogether(
            [
                diagrammes.parcours_inscription(),
                legende(
                    "Parcours d'inscription. En vert le compte ouvert, en rouge "
                    "la demande refusée ; dans les deux cas un courriel part."
                ),
            ]
        ),
        titre("5.2 Se connecter en trois temps", "h2"),
        p(
            "La connexion demande d'abord <b>qui</b> et <b>où</b>, avant "
            "l'identifiant. Ce n'est pas une formalité de plus : c'est ce qui "
            "permet d'ouvrir la session sur le bon écran, déjà cadré, plutôt "
            "que de déverser un national de 181 agences et de laisser chacun "
            "filtrer. Un superviseur peut même noter au passage les itinéraires "
            "que son agent lui récite de mémoire, et arriver directement sur "
            "leur bordereau."
        ),
        KeepTogether(
            [
                diagrammes.parcours_connexion(),
                legende(
                    "Parcours de connexion. Les cinq atterrissages possibles, "
                    "selon le profil et selon que le superviseur a noté ou non "
                    "des itinéraires."
                ),
            ]
        ),
        encadre(
            "<b>Ce que le choix de profil et d'agence ne fait pas.</b> Il "
            "n'accorde rien. Le serveur confronte la déclaration au compte et "
            "refuse la session si elles divergent ; le rôle porté par le jeton "
            "reste celui du compte, et l'ABAC rétrécit les requêtes au "
            "périmètre du compte, pas à l'agence annoncée. Un superviseur qui "
            "déclarerait une autre agence se verrait simplement refuser "
            "l'entrée. La déclaration est un confort de saisie, doublé d'un "
            "garde-fou contre la session ouverte au mauvais poste."
        ),
        titre("5.3 La journée du superviseur", "h2"),
        p(
            "C'est le parcours le plus long, parce que c'est lui qui porte le "
            "dispositif. Les quatre premières étapes sont strictement "
            "séquentielles ; les quatre suivantes se reprennent au fil de la "
            "journée, à mesure que les agents rentrent."
        ),
        KeepTogether(
            [
                diagrammes.parcours_superviseur(),
                legende(
                    "Journée du superviseur. Le cadre gris est le seul moment "
                    "où le travail sort de l'application."
                ),
            ]
        ),
        titre("5.4 L'agent de terrain", "h2"),
        p(
            "Trois étapes, aucune écriture. La brièveté du parcours n'est pas "
            "un manque de fonctionnalités, c'est la traduction d'un choix : "
            "l'agent travaille sur papier, le superviseur saisit."
        ),
        KeepTogether(
            [
                diagrammes.parcours_agent(),
                legende(
                    "Parcours de l'agent de terrain, le plus court du système."
                ),
            ]
        ),
        titre("5.5 La gouvernance des accès", "h2"),
        p(
            "L'administrateur SOCADEL et le super utilisateur NEXT LTD "
            "partagent le même tronc. Un seul diagramme suffit donc, et il "
            "rend visible la seule chose qui les sépare : deux gestes, en bas "
            "à droite."
        ),
        KeepTogether(
            [
                diagrammes.parcours_gouvernance(),
                legende(
                    "Gouvernance des accès. En bleu plein, ce que seul le super "
                    "utilisateur peut faire."
                ),
            ]
        ),
        tableau(
            [
                ["Profil", "Écran d'arrivée", "Étapes du parcours", "Écritures"],
                ["Super utilisateur", "Tableau de bord national", "1 tronc commun, plus 2 gestes réservés", "Toutes"],
                ["Administrateur", "Tableau de bord national", "4 étapes de gouvernance", "Comptes et périmètres"],
                ["Superviseur", "Écran d'affectation, ou bordereau cadré", "8 étapes, dont 4 séquentielles", "Production et agents"],
                ["Agent de terrain", "Mon espace", "3 étapes", "<b>Aucune</b>"],
            ],
            [110, 190, 250, 150],
        ),
        legende(
            "Résumé des cinq parcours. La colonne des écritures est la "
            "traduction opérationnelle de la hiérarchie des rôles."
        ),
        NextPageTemplate("portrait"),
        PageBreak(),
    ]


def _domaine() -> list:
    return [
        titre("6. Le modèle du domaine", "h1"),
        p(
            "Le domaine est modélisé en objets porteurs de règles, pas en "
            "structures de données anémiques. Les invariants sont dans les "
            "entités : une ligne déclarée abonnée sans numéro relevé est refusée "
            "par <font face='Courier'>LigneBordereau.declarer()</font>, pas par "
            "un contrôle de formulaire."
        ),
        titre("Les objets-valeurs", "h2"),
        p(
            "Quatre notions métier sont modélisées en objets-valeurs immuables "
            "et auto-validants, plutôt qu'en chaînes de caractères. Elles "
            "portent leur propre normalisation, ce qui évite d'avoir à s'en "
            "souvenir à chaque usage."
        ),
        tableau(
            [
                ["Objet-valeur", "Ce qu'il garantit", "Exemple"],
                ["NumeroTelephone", "Format E.164 camerounais. Absorbe les saisies hétérogènes du terrain.", "« 694174768 » donne +237694174768"],
                ["ServiceNo", "Identifiant de contrat. Clé de jointure avec le référentiel.", "203401046"],
                ["RefGeo", "Adresse technique, et surtout <b>l'ordre de marche</b> : le tri par clé numérique restitue le parcours physique des maisons.", "807-09-01-994-00-001"],
                ["CodeItineraire", "Unité de travail confiée à un agent.", "42422 (CSC_ESSOS)"],
            ],
            [95, 250, 125],
        ),
        encadre(
            "<b>Pourquoi RefGeo mérite un objet.</b> Le bordereau papier doit "
            "suivre l'ordre des maisons, sinon l'agent zigzague dans le "
            "quartier. Trier sur la chaîne brute donnerait un ordre "
            "lexicographique faux : « 960-20-11-92 » passerait avant "
            "« 960-20-11-232 ». La propriété <font face='Courier'>cle_tri</font> "
            "convertit chaque segment en entier et rétablit l'ordre réel."
        ),
        titre("La règle de vérification", "h2"),
        p(
            "C'est le cœur du dispositif. Elle est isolée dans un service de "
            "domaine pur, sans base ni transport, et se lit en quelques lignes :"
        ),
        tableau(
            [
                ["Déclaration", "État du référentiel", "Verdict", "Payable"],
                ["ABONNE", "Contrat absent du référentiel", "INTROUVABLE", "Non"],
                ["ABONNE", "whatsapp_status différent de subscribed", "INFIRME", "Non"],
                ["ABONNE", "subscribed, mais autre numéro", "INFIRME", "Non"],
                ["ABONNE", "subscribed, numéro concordant", "CONFIRME", "<b>Oui</b>"],
                ["ABSENT, REFUS, etc.", "Non abonné au référentiel", "CONFIRME", "Non"],
                ["ABSENT, REFUS, etc.", "Abonné au référentiel", "INFIRME", "Non"],
            ],
            [95, 175, 100, 100],
            aligne_a_droite=[2, 3],
        ),
        legende(
            "Une nouvelle déclaration remet automatiquement le verdict à "
            "NON_VERIFIE : corriger une ligne oblige à la re-confronter."
        ),
        # Le diagramme de classes ouvre le passage en paysage, que les
        # séquences du chapitre suivant prolongent sans nouvelle bascule.
        titre("Le diagramme de classes", "h2"),
        p(
            "Chaque rectangle est une <b>classe</b> : son nom en haut sur fond "
            "bleu, ses données en dessous. La mention entre guillemets doubles, "
            "« entité » ou « service », indique sa nature. Les flèches sont les "
            "relations, et leur étiquette se lit dans le sens de la flèche : "
            "« matérialise 1..* » signifie qu'une affectation donne naissance à "
            "une ou plusieurs lignes de bordereau. Le petit losange plein marque "
            "une <b>composition</b> : les lignes n'existent pas sans leur "
            "affectation. Les couleurs portent le sens du dispositif : en vert "
            "ce que le superviseur déclare, en orange ce que le référentiel "
            "établit, et entre les deux le service qui les confronte."
        ),
        NextPageTemplate("paysage"),
        PageBreak(),
        diagrammes.classes_domaine(),
        legende(
            "Diagramme de classes du domaine. En vert la ligne de bordereau, ce "
            "que le superviseur déclare ; en orange le client, ce que le "
            "référentiel établit."
        ),
    ]

def _dynamique() -> list:
    return [
        # Toujours en paysage : le chapitre precedent a ouvert le passage.
        titre("7. La dynamique du système", "h1"),
        titre("7.1 Le briefing du matin", "h2"),
        p(
            "C'est le premier geste de la journée, et l'écran qui s'ouvre juste après "
            "la connexion du superviseur. L'agent se présente, on note les itinéraires "
            "qu'on lui confie. L'opération fait deux choses d'un coup : elle trace le "
            "briefing et elle <b>matérialise le bordereau</b>."
        ),
        titre("Comment lire un diagramme de séquence", "h3"),
        p(
            "Les rectangles du haut sont les <b>participants</b>, et le trait "
            "vertical pointillé sous chacun est sa ligne de vie : le temps "
            "s'écoule vers le bas. Chaque flèche horizontale est un message, "
            "envoyé par le participant de départ à celui d'arrivée. Les flèches "
            "<b>pleines et bleues</b> sont des demandes, les <b>pointillées et "
            "grises</b> des réponses. La barre bleue posée sur une ligne de vie "
            "indique que ce participant est en train de travailler. Lire de haut "
            "en bas donne donc l'ordre exact des opérations."
        ),
        diagrammes.sequence_affectation(),
        legende("Séquence, affectation d'un itinéraire et génération du bordereau."),
        encadre(
            "<b>Plusieurs itinéraires, plusieurs fois.</b> Un bon collecteur reçoit "
            "plusieurs tournées, parfois en cours de journée. Chaque appel ajoute des "
            "affectations sans toucher aux précédentes, et les chiffres de l'agent se "
            "mettent à jour. L'unicité (agent, itinéraire, jour) empêche seulement de "
            "compter deux fois la même tournée."
        ),
        titre("7.2 La saisie et le recoupement", "h2"),
        diagrammes.sequence_verification(),
        legende(
            "Séquence, déclaration du superviseur, puis confrontation au référentiel."
        ),
        Spacer(1, 4 * mm),
        titre("7.3 L'import en deux temps", "h2"),
        p(
            "Le métier a demandé un aperçu avant toute écriture. Le flux est donc "
            "strictement séquentiel : analyser, montrer, puis écrire seulement si le "
            "superviseur confirme."
        ),
        diagrammes.sequence_import(),
        legende("Séquence, import d'un bordereau rempli."),
        NextPageTemplate("portrait"),
        PageBreak(),
        titre("7.4 Le parcours d'enrôlement du client", "h2"),
        p(
            "Ce parcours se déroule <b>hors de l'application</b>, dans WhatsApp. Il "
            "est reproduit ici parce qu'il explique ce que « abonné » veut dire, et "
            "pourquoi le référentiel peut faire foi."
        ),
        titre("Comment lire ce diagramme", "h3"),
        p(
            "Le disque plein en haut à gauche est le point de départ, le cercle "
            "creux en bas à droite la fin. Chaque rectangle est une étape, les "
            "flèches donnent l'ordre. Le <b>losange</b> au milieu est une "
            "décision : deux issues en partent, étiquetées OUI et NON, et le "
            "chemin NON boucle vers la saisie précédente pour que le client "
            "corrige sans quitter la conversation."
        ),
        diagrammes.activite_enrolement(),
        legende(
            "Diagramme d'activité, l'enrôlement WhatsApp, de la présentation du QR "
            "code à la remontée vers le référentiel."
        ),
    ]


def _architecture() -> list:
    return [
        titre("8. L'architecture logicielle", "h1"),
        p(
            "Le backend suit la clean architecture. Ce n'est pas une préférence "
            "esthétique : le métier a annoncé que la base actuelle est une base de "
            "test et que la vraie source de vérité arrivera par une API tierce. Le "
            "système doit donc pouvoir changer de source sans être réécrit."
        ),
        titre("Comment lire ce schéma", "h3"),
        p(
            "Les trois bandes empilées sont les couches du logiciel, la plus "
            "intérieure en bas et la plus foncée. Les flèches verticales disent "
            "« dépend de » et <b>pointent toutes vers le bas</b> : c'est la règle "
            "de dépendance. La bande grise du dessous, l'infrastructure, n'a pas "
            "de flèche vers le haut : elle fournit des implémentations sans "
            "jamais être nommée par les couches supérieures, ce que figure le "
            "trait qui la contourne."
        ),
        diagrammes.architecture(),
        legende("Les quatre couches et le sens des dépendances."),
        tableau(
            [
                ["Couche", "Contient", "Ne connaît pas"],
                ["domain/", "Entités, objets-valeurs, services de domaine, politique d'habilitation", "Rien, aucun framework"],
                ["application/", "Cas d'usage, ports (protocoles), DTO", "Aucun framework ; seulement le domaine"],
                ["infrastructure/", "PostgreSQL, bcrypt, JWT, openpyxl, reportlab, stockage média", ", "],
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
        titre("9. Le modèle de données", "h1"),
        titre("Comment lire ce diagramme", "h3"),
        p(
            "Même lecture que le diagramme de classes, appliquée aux tables. "
            "<b>PK</b> désigne la clé primaire, <b>FK</b> une clé étrangère qui "
            "pointe vers une autre table, <b>UQ</b> une contrainte d'unicité. "
            "Les étiquettes des flèches sont les cardinalités : « 1..N » se lit "
            "« un enregistrement de gauche correspond à un ou plusieurs à "
            "droite ». Les deux tables en couleur sont les volumineuses."
        ),
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
                ["Import du référentiel (46 Mo)", "Lecture en flux, écriture par paquets de 5 000, le classeur n'est jamais chargé entier"],
                ["Exports potentiellement massifs", "Plafond de 50 000 lignes, signalé au client par un en-tête dédié"],
                ["Cinq requêtes de KPI en parallèle", "Une session par requête : une session SQLAlchemy ne supporte qu'une opération à la fois"],
            ],
            [180, 290],
        ),
    ]


def _habilitations() -> list:
    return [
        titre("10. Les habilitations", "h1"),
        p(
            "Deux mécanismes répondent à deux questions distinctes. Les confondre est "
            "la source habituelle des fuites de données."
        ),
        titre("Comment lire ce schéma", "h3"),
        p(
            "Une requête entre par le haut et se voit attribuer un contexte "
            "d'accès. Deux chemins en partent : à gauche le contrôle RBAC, qui "
            "répond par oui ou non et peut refuser la requête ; à droite la "
            "garde ABAC, qui ne refuse rien mais <b>réécrit le périmètre</b> de "
            "la demande. Les deux encadrés du bas montrent les issues : un refus "
            "à gauche, un périmètre rétréci à droite."
        ),
        diagrammes.habilitations(),
        legende("RBAC et ABAC : le « quoi » et le « sur quoi »."),
        encadre(
            "<b>Le choix décisif.</b> L'ABAC ne valide pas un accès déjà formulé : il "
            "<b>réécrit le filtre</b> avant qu'il n'atteigne la base. Un agent qui "
            "demanderait explicitement la production d'un collègue voit son paramètre "
            "écrasé, et obtient zéro ligne. Un contrôle a posteriori aurait dû être "
            "appelé partout, et il aurait suffi de l'oublier une fois."
        ),
        titre("Matrice complète des permissions", "h2"),
        _matrice_permissions(),
        legende(
            "Matrice RBAC appliquée dans le code "
            "(<font face='Courier'>domain/securite/permissions.py</font>). "
            "Seul le super utilisateur NEXT LTD porte l'intégralité des permissions. Les deux que l'administrateur SOCADEL n'a pas, changer un rôle et administrer le référentiel, engagent le fonctionnement de la plateforme."
        ),
        titre("Règles ABAC", "h2"),
        tableau(
            [
                ["Rôle", "Rétrécissement appliqué au filtre"],
                ["Super utilisateur", "Aucun, portée nationale"],
                ["Administrateur", "Aucun, portée nationale sur les données SOCADEL"],
                [
                    "Superviseur",
                    "Son agence et sa région, imposées. <b>Sans périmètre défini, "
                    "la requête est refusée</b> plutôt que d'ouvrir le national : "
                    "SOCADEL compte 181 agences, et un superviseur de Kribi n'a "
                    "pas à voir la production de Ngaoundéré.",
                ],
                ["Agent de terrain", "Son propre identifiant d'agent, imposé quoi qu'il demande"],
            ],
            [110, 360],
        ),
        titre("La hiérarchie des rôles", "h2"),
        p(
            "Le RBAC dit ce qu'un rôle peut faire, l'ABAC sur quelles données. "
            "Une troisième règle dit <b>sur qui</b> : chacun n'agit que sur les "
            "rangs strictement inférieurs au sien."
        ),
        tableau(
            [
                ["Rang", "Rôle", "Peut agir sur", "Ne peut pas agir sur"],
                ["3", "Super utilisateur", "Les trois rangs inférieurs", "Un autre super utilisateur"],
                ["2", "Administrateur", "Superviseur, agent", "Un pair, le super utilisateur"],
                ["1", "Superviseur", "Agent de terrain", "Un pair, et au-dessus"],
                ["0", "Agent de terrain", "Personne", "Tout le monde"],
            ],
            [45, 110, 150, 165],
            aligne_a_droite=[0],
        ),
        legende(
            "Règle vérifiée par un test qui parcourt les seize combinaisons "
            "possibles de rôle appelant et de rôle cible."
        ),
        KeepTogether(
            [
                titre("Comment lire ce diagramme", "h3"),
                p(
                    "Les quatre rôles sont empilés du plus large au plus "
                    "restreint. <b>La largeur de chaque boîte est "
                    "proportionnelle à sa portée</b> : elle se lit sans lire le "
                    "texte. La flèche verticale porte la règle « agit sur » et "
                    "ne relie que des paliers voisins ; par transitivité, un "
                    "rang atteint donc tous ceux qui sont sous lui, et jamais "
                    "son propre niveau."
                ),
                diagrammes.hierarchie_roles(),
                legende(
                    "Hiérarchie des rôles. La largeur décroît avec le rang, "
                    "l'escalade de privilèges est fermée par construction."
                ),
            ]
        ),
    ]


def _matrice_permissions():
    """Matrice construite depuis le code, pas recopiée à la main.

    Elle est lue dans `domain.securite.MATRICE` au moment de la génération :
    le document ne peut donc pas diverger de ce que la plateforme applique.
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from bordereau.domain.enums import Role
    from bordereau.domain.securite import MATRICE, Permission

    ordre = (
        Role.SUPER_UTILISATEUR,
        Role.ADMINISTRATEUR,
        Role.SUPERVISEUR,
        Role.AGENT_TERRAIN,
    )
    lignes = [["Permission", "Super utilis.", "Admin.", "Superviseur", "Agent"]]
    for permission in Permission:
        lignes.append(
            [
                permission.value,
                *[
                    "oui" if permission in MATRICE[role] else "."
                    for role in ordre
                ],
            ]
        )

    return tableau(
        lignes, [170, 80, 70, 85, 65], aligne_a_droite=[1, 2, 3, 4], taille=7
    )

def _charte() -> list:
    return [
        titre("13. La charte graphique", "h1"),
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
            "choisies pour leur propre surface. L'utilisateur dispose de trois états, "
            "clair, sombre, ou suivre le système, et son choix est conservé."
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
            "français est la langue de référence, celle du métier SOCADEL, et le "
            "type des clés de traduction est dérivé du dictionnaire français : une clé "
            "oubliée en anglais devient une erreur de compilation, pas une chaîne "
            "manquante découverte en production."
        ),
    ]


def _decisions() -> list:
    return [
        titre("14. Les décisions de conception", "h1"),
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
            "l'écran, un écart entre les deux serait invisible et coûteux.",
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
        titre("15. Limites connues et suite", "h1"),
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
            "<b>Sur la qualité du logiciel.</b> Le backend est couvert par 96 tests "
            "automatisés, domaine, cas d'usage, adaptateurs de fichiers et API HTTP "
            "complète, habilitations comprises. Le parcours complet a par ailleurs été "
            "déroulé contre une instance PostgreSQL réelle chargée des 425 920 clients."
        ),
    ]



def _cycle_de_vie_comptes() -> list:
    return [
        titre("11. L'ouverture des accès", "h1"),
        p(
            "La plateforme porte le référentiel clients de SOCADEL, plus de "
            "quatre cent mille noms et numéros de téléphone. Un accès ne "
            "s'obtient donc pas en remplissant un formulaire : <b>s'inscrire "
            "dépose une demande</b>, elle n'ouvre rien."
        ),
        titre("Les quatre étapes"),
        tableau(
            [
                ["Étape", "Qui agit", "Ce qui se passe", "État du compte"],
                [
                    "1. Inscription",
                    "Le demandeur",
                    "Il choisit son identifiant, son adresse et son propre mot "
                    "de passe, saisi deux fois.",
                    "En attente de vérification",
                ],
                [
                    "2. Confirmation",
                    "Le demandeur",
                    "Il ouvre le lien reçu par courriel, valable trois jours.",
                    "En attente d'approbation",
                ],
                [
                    "3. Approbation",
                    "Un responsable",
                    "Il attribue le rôle et, pour un superviseur, le périmètre.",
                    "Actif",
                ],
                [
                    "4. Notification",
                    "La plateforme",
                    "Un second courriel confirme l'ouverture de l'accès.",
                    "Actif",
                ],
            ],
            [80, 75, 200, 115],
        ),
        legende(
            "Tant que le compte n'est pas actif, la connexion est refusée même "
            "avec le bon mot de passe, et le message explique précisément à "
            "quelle étape le dossier est bloqué."
        ),
        encadre(
            "<b>Pourquoi l'approbation ne peut pas être automatique.</b> Deux "
            "informations manquent au formulaire d'inscription et ne peuvent "
            "venir que d'un responsable : le <i>rôle</i>, car personne ne "
            "s'attribue ses propres droits, et le <i>périmètre</i>, car il "
            "faut savoir de quelle agence relève ce superviseur parmi les 181 "
            "du réseau. Un compte agent doit en outre être rattaché à sa fiche "
            "terrain, faute de quoi la garde ABAC ne saurait pas quelles "
            "données lui montrer."
        ),
        titre("La politique de mot de passe", "h2"),
        p(
            "Elle suit les recommandations actuelles du NIST : privilégier la "
            "<b>longueur</b> et refuser les mots notoirement compromis, plutôt "
            "qu'imposer un jeu de caractères qui pousse surtout à écrire "
            "« Password1! » sur un papier collé à l'écran."
        ),
        tableau(
            [
                ["Règle", "Motif"],
                ["Au moins dix caractères", "La longueur protège plus que la variété"],
                [
                    "Ni mot courant, ni terme du projet",
                    "« socadel », « bordereau » et leurs variantes accentuées "
                    "sont les premiers essais d'un attaquant",
                ],
                [
                    "Ni reprise de l'identifiant ou de l'adresse",
                    "Un mot de passe déductible du login n'en est pas un",
                ],
                [
                    "Double saisie à l'inscription",
                    "Une faute de frappe verrouillerait le titulaire dehors",
                ],
            ],
            [175, 255],
        ),
        p(
            "La règle vit dans le domaine, pas dans un validateur de "
            "formulaire : elle s'applique donc à l'identique à l'inscription, "
            "au changement volontaire et à la réinitialisation. L'interface "
            "affiche une jauge en direct pendant la saisie, alimentée par la "
            "même fonction que celle qui tranchera à l'enregistrement : "
            "l'évaluation montrée et la règle appliquée ne peuvent pas diverger."
        ),
        titre("Le mot de passe oublié", "h2"),
        p("Deux chemins, selon que le titulaire a encore accès à sa boîte."),
        tableau(
            [
                ["Situation", "Mécanisme", "Garde-fou"],
                [
                    "Il a accès à sa boîte",
                    "Lien de réinitialisation envoyé par courriel, valable deux "
                    "heures et utilisable une seule fois.",
                    "La réponse est toujours identique, que l'adresse existe ou "
                    "non : dire « adresse inconnue » indiquerait qui possède un "
                    "compte.",
                ],
                [
                    "Il n'y a plus accès",
                    "Un responsable réinitialise. La plateforme génère un mot "
                    "de passe provisoire sans I, l, O ni 0, pour qu'il se dicte "
                    "au téléphone sans confusion.",
                    "Le provisoire n'est jamais écrit dans le courriel, et le "
                    "titulaire doit le remplacer dès la connexion suivante.",
                ],
            ],
            [95, 180, 155],
        ),
        titre("Qui peut réinitialiser pour qui", "h2"),
        p(
            "La même règle qu'ailleurs : <b>strictement au-dessus</b>. Elle est "
            "vérifiée par un test qui parcourt les seize combinaisons possibles."
        ),
        tableau(
            [
                ["Le rôle...", "peut agir sur", "ne peut pas agir sur"],
                ["Super utilisateur", "Administrateur, superviseur, agent", "Un autre super utilisateur"],
                ["Administrateur", "Superviseur, agent", "Un autre administrateur, le super utilisateur"],
                ["Superviseur", "Agent", "Un autre superviseur, et au-dessus"],
                ["Agent de terrain", "Personne", "Tout le monde"],
            ],
            [110, 165, 155],
        ),
        encadre(
            "<b>Ce que cette règle empêche concrètement.</b> Un compte "
            "d'administrateur compromis ne permet pas de se créer un complice "
            "au même rang, ni de toucher au compte NEXT LTD qui l'a ouvert. "
            "L'escalade de privilèges par création de compte est structurellement "
            "fermée, ce n'est pas une vérification qu'on pourrait oublier "
            "d'appeler quelque part."
        ),
        titre("Les courriels", "h2"),
        p(
            "Quatre messages transactionnels : confirmation d'adresse, "
            "ouverture d'accès, refus, réinitialisation. Ils sont courts et "
            "disent qui écrit, pourquoi, et quoi faire."
        ),
        p(
            "L'envoi passe par un port applicatif, avec deux implémentations. "
            "En développement, les messages sont <b>écrits sur disque</b>, un "
            "fichier par courriel : on relit le lien sans configurer de serveur. "
            "En production, un adaptateur SMTP prend le relais, et rien d'autre "
            "ne change dans le code."
        ),
        encadre(
            "<b>Un envoi qui échoue ne fait jamais échouer l'opération.</b> Un "
            "compte créé dont le courriel n'est pas parti reste un compte créé, "
            "et le lien peut être renvoyé. Faire tomber une inscription parce "
            "que le serveur de messagerie tousse serait un mauvais échange."
        ),
        titre("11.5 Le maillage territorial", "h2"),
        p(
            "L'agence est la maille du périmètre : c'est elle qu'un compte de "
            "superviseur porte, et elle que le sélecteur de connexion propose. "
            "Elle était déduite du référentiel clients, donc immuable : ouvrir "
            "une agence dans une zone nouvelle, ou en fermer une devenue "
            "inaccessible, supposait de rejouer un import de plus de quatre cent "
            "mille lignes. Ce n'est pas une opération qu'on demande à un "
            "responsable d'agence."
        ),
        p(
            "Le maillage est donc une entité à part entière, que l'application "
            "tient. Deux règles le protègent, et elles tiennent au fait que "
            "l'agence est référencée ailleurs."
        ),
        tableau(
            [
                ["Règle", "Ce qu'elle empêche"],
                [
                    "Le nom d'une agence ne se modifie pas",
                    "Comptes, itinéraires et référentiel le portent tel quel : le "
                    "changer romprait les trois liens d'un coup.",
                ],
                [
                    "On ferme avant de supprimer",
                    "Une agence fermée quitte les listes de travail et le "
                    "sélecteur de connexion le jour même, mais reste attachée à "
                    "la production passée. La suppression n'est ouverte que tant "
                    "que rien ne s'y rattache.",
                ],
                [
                    "Le motif de fermeture est exigé",
                    "Une agence fermée sans raison connue ne se rouvre jamais de "
                    "bon cœur, faute de savoir ce qui l'avait justifiée.",
                ],
            ],
            [140, 290],
        ),
        legende(
            "181 agences, 33 divisions et 9 directions régionales ont été "
            "reprises du référentiel à la mise en route. L'application fait foi "
            "ensuite."
        ),
        titre("11.6 Restreindre un rôle, jamais l'étendre", "h2"),
        p(
            "Le super utilisateur peut retirer une permission à un rôle, par "
            "exemple fermer l'export à tous les superviseurs le temps d'une "
            "campagne. Il ne peut pas en ajouter, et cette asymétrie est "
            "délibérée."
        ),
        encadre(
            "<b>La matrice du code reste le plafond.</b> Les quatre rôles et "
            "leurs droits sont écrits dans le dépôt, où ils sont relus, testés et "
            "versionnés. La table des restrictions ne peut que retrancher : "
            "aucune écriture en base n'ouvre un droit, y compris depuis une "
            "sauvegarde restaurée. L'escalade de privilèges par la donnée est "
            "ainsi fermée par construction, et non par vigilance."
        ),
        p(
            "Deux garde-fous s'ajoutent. Le rôle super utilisateur ne se "
            "restreint pas lui-même, sans quoi une fausse manœuvre fermerait la "
            "plateforme à tout le monde sans moyen de la rouvrir. Et lui seul "
            "décide : l'administrateur SOCADEL lit la matrice, ce qui rend un "
            "refus compréhensible, mais ne la modifie pas."
        ),
        p(
            "Les restrictions sont relues à chaque requête plutôt que mises en "
            "cache : retirer un droit prend effet tout de suite, pas au prochain "
            "redémarrage."
        ),
        titre("11.7 Le journal d'audit", "h2"),
        p(
            "Qui a affecté cette tournée, qui a fermé cette agence, qui a "
            "réinitialisé ce mot de passe. Une plateforme qui décide de ce qui "
            "sera payé doit pouvoir répondre, sinon elle n'est pas défendable "
            "devant un contrôle."
        ),
        p(
            "L'écriture passe par un <b>point unique</b>, l'intercepteur HTTP. "
            "Répartir la consignation sur cinquante cas d'usage garantirait qu'on "
            "en oublie un, et le jour où on l'oublie, c'est justement celui qu'on "
            "cherchera."
        ),
        tableau(
            [
                ["Ce que le journal retient", "Ce qu'il ne retient jamais"],
                [
                    "L'auteur, l'instant, le geste et sa cible, l'issue et "
                    "l'adresse d'origine. Les écritures et les tentatives de "
                    "connexion.",
                    "Le contenu transmis : mots de passe, numéros de téléphone, "
                    "noms de clients. Et les consultations, qui noieraient le "
                    "signal sans rien apprendre.",
                ],
            ],
            [215, 215],
        ),
        legende(
            "Recopier les corps de requête créerait une seconde base de données "
            "personnelles, moins protégée que la première et consultable par des "
            "gens qui n'ont pas à la voir. Un test vérifie qu'aucun mot de passe "
            "n'y figure."
        ),
        p(
            "La lecture est gouvernée : administrateur SOCADEL et super "
            "utilisateur NEXT LTD. Le superviseur n'a pas à savoir qui a consulté "
            "quoi, et l'agent encore moins."
        ),
        titre("11.8 Le mode démonstration", "h2"),
        p(
            "Le premier écran de connexion propose <b>Démonstration</b> ou "
            "<b>Réel</b>. En démonstration, choisir un profil suffit : l'agence "
            "et les identifiants sont préremplis. C'est ce qu'il faut pour une "
            "prise en main, où retaper une adresse à chaque essai use la patience "
            "avant même d'avoir vu l'application."
        ),
        encadre(
            "<b>Ce mode expose des mots de passe à un visiteur non "
            "authentifié.</b> Il est donc faux par défaut, sa route répond 404 "
            "quand il est coupé, et l'application l'annonce bruyamment dans son "
            "journal au démarrage quand il est actif. Il n'a rien à faire sur "
            "l'instance qui portera le référentiel réel."
        ),
        titre("11.9 L'envoi des courriels", "h2"),
        p(
            "Les cinq messages du cycle de vie d'un compte partent par un vrai "
            "serveur, configuré hors du dépôt. Le port <font face='Courier'>"
            "Messagerie</font> masque ce choix : un adaptateur écrit sur disque "
            "en développement, l'autre parle SMTP, et aucun cas d'usage ne sait "
            "lequel est en place."
        ),
        p(
            "Les deux <b>avalent leurs erreurs</b>. Un compte créé dont le "
            "courriel n'est pas parti reste un compte créé : faire échouer une "
            "inscription parce qu'un serveur de messagerie tousse serait pire que "
            "ne pas envoyer un message, qui peut de toute façon être renvoyé."
        ),
    ]



def _bascule_source() -> list:
    return [
        titre("12. Changer de source de vérité", "h1"),
        p(
            "C'est la question posée dès le départ : la base actuelle est une "
            "base de test, et la vraie source de vérité arrivera par l'API que "
            "NEXT LTD exposera sur la base MRA. Ce chapitre montre ce que cette "
            "bascule coûtera réellement."
        ),
        titre("Ce qui est déjà en place"),
        p(
            "La couche application ne connaît pas PostgreSQL. Elle déclare un "
            "<b>port</b>, c'est-à-dire un contrat, et l'infrastructure fournit "
            "une implémentation. Le contrat qui porte la source de vérité tient "
            "en cinq méthodes :"
        ),
        tableau(
            [
                ["Méthode du port ClientRepository", "Ce qu'elle rend"],
                ["par_service_no(numero)", "Un client, ou rien"],
                ["par_services_no(numeros)", "Plusieurs clients d'un coup, indexés par contrat"],
                ["par_itineraire(code)", "Les clients d'une tournée"],
                ["compter_par_itineraire(code)", "Leur nombre"],
                ["enregistrer_en_lot(clients)", "Écriture de masse, pour l'import initial"],
            ],
            [190, 240],
        ),
        titre("Ce que la bascule demandera"),
        tableau(
            [
                ["Élément", "À faire", "Ampleur"],
                [
                    "Adaptateur d'API",
                    "Une classe qui implémente les cinq méthodes ci-dessus en "
                    "appelant l'API NEXT au lieu d'interroger la table.",
                    "Un fichier nouveau",
                ],
                [
                    "Conteneur",
                    "Une ligne à changer, celle qui associe le port à son "
                    "implémentation.",
                    "Une ligne",
                ],
                [
                    "Domaine, cas d'usage, routes, interface",
                    "Rien.",
                    "Aucune modification",
                ],
                [
                    "Tests",
                    "Les 96 tests existants restent valables : ils s'exécutent "
                    "déjà contre un double en mémoire, preuve que la couche "
                    "métier ne dépend d'aucune base.",
                    "Aucune modification",
                ],
            ],
            [130, 230, 70],
        ),
        encadre(
            "<b>La preuve est déjà faite, pas seulement annoncée.</b> La suite "
            "de tests exerce l'API HTTP complète, authentification et "
            "habilitations comprises, en remplaçant PostgreSQL par des objets "
            "en mémoire. Si le métier était couplé à la base, ces tests ne "
            "pourraient pas s'écrire. Qu'ils passent démontre que la "
            "substitution fonctionne : l'adaptateur d'API NEXT sera un troisième "
            "interlocuteur, au même titre."
        ),
        Spacer(1, 5 * mm),
        titre("Une bascule progressive reste possible", "h2"),
        p(
            "Rien n'oblige à basculer d'un bloc. Un adaptateur composite peut "
            "interroger l'API en premier et retomber sur la table locale quand "
            "l'API ne répond pas ou ne connaît pas le contrat. Le reste du "
            "système ne verra aucune différence, puisqu'il ne voit que le "
            "contrat."
        ),
        titre("Ce qui restera à décider avec la DSI"),
        *puces(
            [
                "Le format de réponse de l'API et le champ qui porte l'état "
                "d'abonnement WhatsApp, aujourd'hui « whatsapp_status ».",
                "Le mode d'authentification à l'API, et où loger le secret.",
                "La tolérance en cas d'indisponibilité : refuser la "
                "vérification, ou la différer et la rejouer.",
                "La fréquence de rafraîchissement, si l'on conserve une copie "
                "locale pour les écrans de consultation.",
            ]
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
        *_parcours(),
        *_domaine(),
        *_dynamique(),
        *_architecture(),
        *_donnees(),
        *_habilitations(),
        *_cycle_de_vie_comptes(),
        *_bascule_source(),
        *_charte(),
        *_decisions(),
        *_limites(),
    ]
