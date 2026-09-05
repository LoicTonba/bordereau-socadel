"""Guides d'utilisation, un par profil, illustrés des écrans réels.

Chaque guide se lit sans rien connaître de la plateforme. Il suit l'ordre des
gestes d'une journée de travail, pas l'ordre des menus, et chaque étape est
accompagnée de la capture prise pendant le parcours de recette : ce que le
lecteur voit sur le papier est exactement ce qu'il verra à l'écran.

Les captures viennent de `scripts/captures.py`, qui pilote un vrai navigateur.
Elles ne sont donc jamais retouchées, et une interface qui change se voit
immédiatement au guide suivant.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer

from .document import capture, encadre, legende, p, puces, tableau, titre

CAPTURES = Path(__file__).resolve().parent / "captures"

#: Comptes de mise en route. Ils sont dans le guide parce qu'un guide sans
#: identifiants n'est pas suivable ; ils sont à remplacer avant production.
IDENTIFIANTS = {
    "SUPER_UTILISATEUR": ("tonbaloic6@gmail.com", "Ngaoundal-Kribi-88"),
    "ADMINISTRATEUR": ("tonbaloic@gmail.com", "Bandjoun-Maroua-77"),
    "SUPERVISEUR": ("loicdjimgou@gmail.com", "Ngaoundere-Sud-2026"),
    "AGENT_TERRAIN": ("objectifloic@gmail.com", "Terrain-Essos-2026"),
}


def _ecran(nom: str, texte: str):
    return capture(CAPTURES / f"{nom}.png", texte)


# --- Pièces communes aux quatre guides --------------------------------------


def _couverture(profil: str, maison: str, sous_titre: str) -> list:
    return [
        Spacer(1, 40 * mm),
        p("BORDEREAU INTELLIGENT DE COLLECTE WHATSAPP", "sous_titre_couverture"),
        Spacer(1, 6 * mm),
        p(f"Guide d'utilisation<br/>{profil}", "titre_couverture"),
        Spacer(1, 4 * mm),
        p(sous_titre, "sous_titre_couverture"),
        Spacer(1, 26 * mm),
        tableau(
            [
                ["Rubrique", "Valeur"],
                ["Profil décrit", f"{profil}, {maison}"],
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
                ["Date", date.today().strftime("%d/%m/%Y")],
                ["Captures", "Prises sur la plateforme en fonctionnement"],
            ],
            [110, 320],
            taille=8.5,
        ),
        Spacer(1, 16 * mm),
        p(
            "Toutes les captures de ce guide ont été prises pendant un parcours "
            "réel, conduit du premier écran au dernier. Aucune n'est une "
            "maquette.",
            "legende",
        ),
        PageBreak(),
    ]


def _connexion(role: str, agence: str | None, particularite: list | None = None) -> list:
    """Le chapitre de connexion, décliné selon le profil."""
    email, mot_de_passe = IDENTIFIANTS[role]
    choix_agence = (
        f"Cherchez <b>{agence}</b> : tapez les premières lettres, la liste des "
        "181 agences se réduit à mesure."
        if agence
        else "Vous portez une vue nationale : choisissez <b>Portée nationale, "
        "toutes les agences</b> en haut de la liste."
    )

    return [
        titre("1. Se connecter", "h1"),
        p(
            "La page de connexion ne demande pas votre mot de passe en premier. "
            "Elle demande d'abord <b>qui vous êtes</b>, puis <b>où vous êtes</b>. "
            "Ce n'est pas une formalité de plus : c'est ce qui permet d'ouvrir "
            "votre session sur le bon écran, déjà cadré sur votre travail."
        ),
        titre("Démonstration ou réel", "h2"),
        p(
            "Deux modes vous sont proposés en haut du premier écran. En "
            "<b>Démonstration</b>, choisir votre profil suffit : l'agence et les "
            "identifiants sont préremplis, et vous arrivez directement au "
            "troisième écran, prêt à valider. C'est ce qu'il faut pour une prise "
            "en main, où retaper une adresse à chaque essai use la patience "
            "avant même d'avoir vu l'application."
        ),
        p(
            "En <b>Réel</b>, rien n'est prérempli : vous choisissez votre "
            "profil, votre agence, et vous saisissez vos identifiants. C'est le "
            "mode de tous les jours."
        ),
        _ecran("commun-01b-demonstration",
               "En démonstration, l'adresse et le mot de passe sont déjà là."),
        encadre(
            "<b>Le mode démonstration est coupé en production.</b> Il expose des "
            "mots de passe à un visiteur non authentifié : c'est acceptable sur "
            "une instance de découverte, jamais sur celle qui porte le "
            "référentiel réel. Le sélecteur disparaît alors de l'écran."
        ),
        titre("Étape 1, votre profil", "h2"),
        p(
            "Quatre cartes, de la portée la plus large à la plus restreinte. "
            f"Choisissez <b>{_LIBELLE[role]}</b>."
        ),
        _ecran("commun-01-profil", "Premier écran : quatre profils, un seul est le vôtre."),
        titre("Étape 2, votre agence", "h2"),
        p(choix_agence),
        _ecran("commun-02-agence", "La recherche filtre sur le nom, la division et la direction."),
        titre("Étape 3, vos identifiants", "h2"),
        p(
            "Un bandeau rappelle le profil et l'agence retenus, avec un lien "
            "<b>Changer</b> si vous vous êtes trompé. Saisissez ensuite votre "
            "adresse électronique et votre mot de passe."
        ),
        tableau(
            [
                ["Champ", "Valeur pour ce guide"],
                ["Adresse électronique", email],
                ["Mot de passe", mot_de_passe],
            ],
            [150, 280],
        ),
        legende(
            "Comptes de mise en route. Changez votre mot de passe à la première "
            "connexion : ces valeurs figurent dans un document."
        ),
        _ecran("commun-03-identifiants", "Le profil et l'agence sont rappelés au-dessus des champs."),
        *(particularite or []),
        titre("Si l'accès est refusé", "h2"),
        p(
            "Deux refus possibles, et ils ne disent pas la même chose."
        ),
        tableau(
            [
                ["Message", "Ce qu'il faut faire"],
                [
                    "Identifiant ou mot de passe incorrect",
                    "Le compte ou le mot de passe est faux. La plateforme ne dit "
                    "jamais lequel des deux : le contraire permettrait de "
                    "découvrir qui possède un compte.",
                ],
                [
                    "Ce compte est enregistré comme…",
                    "Votre mot de passe est bon, mais vous avez choisi le mauvais "
                    "profil. Revenez au premier écran et prenez le bon.",
                ],
                [
                    "Ce compte est rattaché à l'agence…",
                    "Vous avez déclaré une autre agence que la vôtre. Corrigez, "
                    "ou rapprochez-vous de votre administrateur si votre "
                    "rattachement a changé.",
                ],
            ],
            [150, 280],
        ),
        _ecran("commun-04-poste-refuse", "Un profil qui ne correspond pas au compte est refusé, avec la raison."),
        encadre(
            "<b>Le profil et l'agence ne vous donnent aucun droit.</b> Ils sont "
            "confrontés à votre compte, et la session est refusée s'ils "
            "divergent. Ce que vous voyez reste défini par votre compte, pas par "
            "ce que vous déclarez à l'entrée."
        ),
        PageBreak(),
    ]


_LIBELLE = {
    "SUPER_UTILISATEUR": "Super utilisateur",
    "ADMINISTRATEUR": "Administrateur",
    "SUPERVISEUR": "Superviseur",
    "AGENT_TERRAIN": "Agent de terrain",
}


def _compte_et_mot_de_passe() -> list:
    """Chapitre commun : obtenir un compte, en changer le mot de passe."""
    return [
        titre("Obtenir un compte, ou en reprendre la main", "h1"),
        titre("Demander un accès", "h2"),
        p(
            "S'inscrire <b>ne donne pas accès</b>. La plateforme porte le "
            "référentiel clients de SOCADEL, plus de quatre cent mille noms et "
            "numéros de téléphone : un accès s'accorde, il ne se prend pas. Le "
            "parcours compte quatre temps."
        ),
        *puces(
            [
                "Vous remplissez le formulaire et <b>choisissez vous-même votre "
                "mot de passe</b>, saisi deux fois. Une jauge vous dit en direct "
                "s'il tient.",
                "Un courriel part vers votre adresse. Tant que vous n'avez pas "
                "ouvert le lien, la connexion est refusée, même avec le bon mot "
                "de passe.",
                "Un responsable examine votre demande, vous attribue un profil "
                "et, si vous êtes superviseur, une agence.",
                "Un second courriel vous prévient que l'accès est ouvert.",
            ]
        ),
        _ecran("commun-05-inscription", "Le formulaire de demande d'accès. Le profil y est souhaité, pas acquis."),
        titre("Mot de passe oublié", "h2"),
        p(
            "Cliquez <b>Mot de passe oublié</b> sous le formulaire de connexion, "
            "indiquez l'adresse de votre compte, et suivez le lien reçu. Il est "
            "valable deux heures et ne fonctionne qu'une fois."
        ),
        p(
            "La plateforme répond toujours la même chose, que l'adresse existe ou "
            "non. Ce n'est pas une maladresse : dire « adresse inconnue » "
            "offrirait un moyen simple de savoir qui possède un compte."
        ),
        _ecran("commun-06-mot-de-passe-oublie", "Une seule adresse demandée, une seule réponse possible."),
        p(
            "Si vous n'avez plus accès à votre boîte, votre responsable peut "
            "réinitialiser pour vous : il vous remettra un mot de passe "
            "provisoire <b>de vive voix</b>, jamais par écrit, et vous devrez le "
            "remplacer à la connexion suivante."
        ),
        PageBreak(),
    ]


def _pied_de_guide(profil: str) -> list:
    return [
        titre("Ce qu'il faut retenir", "h1"),
        tableau(
            [
                ["Question", "Réponse"],
                ["Où je me connecte", "http://localhost:3000 en développement"],
                ["Mon profil", profil],
                [
                    "Qui contacter",
                    "Votre administrateur SOCADEL pour un accès ou un mot de "
                    "passe ; NEXT LTD pour un dysfonctionnement de la plateforme.",
                ],
                [
                    "Si un écran reste vide",
                    "Vérifiez d'abord votre filtre, puis votre périmètre : un "
                    "superviseur ne voit que son agence.",
                ],
            ],
            [130, 300],
        ),
        Spacer(1, 6 * mm),
        p(
            "Ce guide est généré depuis le dépôt, en même temps que les captures. "
            "Une évolution de l'interface se répercute en le régénérant : il ne "
            "peut donc pas décrire un écran qui n'existe plus.",
            "legende",
        ),
    ]


# --- Superviseur ------------------------------------------------------------


def superviseur() -> list:
    return [
        *_couverture(
            "Superviseur",
            "SOCADEL, une agence",
            "Affecter les itinéraires · saisir la production · vérifier et exporter",
        ),
        titre("Votre rôle", "h1"),
        p(
            "Vous êtes le pivot du dispositif. L'agent de terrain collecte sur "
            "papier ; c'est vous qui lui confiez ses itinéraires le matin, qui "
            "saisissez ce qu'il a réalisé au retour, et qui confrontez ces "
            "déclarations au référentiel SOCADEL. C'est cette confrontation qui "
            "décide de ce qui sera payé."
        ),
        tableau(
            [
                ["Vous pouvez", "Vous ne pouvez pas"],
                [
                    "Affecter des itinéraires, imprimer les bordereaux papier, "
                    "saisir et corriger la production, vérifier, exporter, gérer "
                    "le répertoire de vos agents.",
                    "Voir la production d'une autre agence, créer un compte de "
                    "connexion, approuver une demande d'accès, changer un rôle.",
                ],
            ],
            [215, 215],
        ),
        Spacer(1, 4 * mm),
        *_connexion(
            "SUPERVISEUR",
            "CSC_NGAOUNDERE SUD",
            particularite=[
                titre("Le raccourci qui vous fait gagner la matinée", "h2"),
                p(
                    "À la troisième étape, vous disposez d'un champ de plus : "
                    "<b>Itinéraires annoncés par l'agent</b>. L'agent connaît ses "
                    "itinéraires par cœur ; pendant qu'il vous les récite, notez "
                    "les codes séparés par un espace, par exemple "
                    "<font face='Courier'>110581 110583</font>."
                ),
                p(
                    "Vous n'arrivez alors pas sur l'écran d'affectation mais "
                    "<b>directement sur le bordereau, déjà filtré sur ces "
                    "itinéraires</b>. Sans code saisi, la connexion se comporte "
                    "normalement."
                ),
            ],
        ),
        titre("2. Le briefing du matin", "h1"),
        p(
            "Vous arrivez directement ici, et c'est voulu : c'est votre première "
            "tâche de la journée."
        ),
        _ecran("sv-01-arrivee", "L'écran d'affectation, à l'ouverture de la session."),
        p(
            "Choisissez l'agent, laissez la date du jour, puis cherchez les "
            "itinéraires qu'il vous annonce. La recherche accepte le code, le "
            "nom de l'agence ou le libellé. Chaque itinéraire retenu affiche son "
            "nombre de clients : c'est le volume à démarcher."
        ),
        _ecran("sv-02-affectation-saisie", "L'itinéraire 110581 confié à AG001 : 73 clients à démarcher."),
        p(
            "Validez avec <b>Affecter et générer le bordereau</b>. La plateforme "
            "crée une ligne de bordereau par client, et vous propose "
            "immédiatement le PDF à imprimer pour l'agent."
        ),
        _ecran("sv-03-affectation-faite", "73 lignes créées en une transaction, et le bordereau papier prêt."),
        encadre(
            "<b>Un itinéraire ne se confie qu'une fois par jour et par agent.</b> "
            "Si vous recommencez, la plateforme vous le dit au lieu de créer un "
            "doublon : deux bordereaux pour la même tournée conduiraient à payer "
            "deux fois la même collecte."
        ),
        PageBreak(),
        titre("3. Imprimer le bordereau papier", "h1"),
        p(
            "Le PDF suit le modèle Excel que vos agents connaissent : références "
            "géographiques, compteur, nom, contrat, et une colonne vierge pour "
            "le relevé. Les clients y sont rangés <b>dans l'ordre de marche des "
            "maisons</b>, pas par ordre alphabétique : l'agent ne zigzague pas "
            "dans le quartier."
        ),
        p(
            "Vous pouvez le réimprimer à tout moment depuis l'écran "
            "<b>Itinéraires</b>, sans refaire l'affectation."
        ),
        titre("4. Saisir la production au retour", "h1"),
        p(
            "L'agent revient avec son bordereau annoté. Ouvrez <b>Bordereau</b> : "
            "vous y voyez les lignes de votre agence, et rien d'autre."
        ),
        _ecran("sv-04-bordereau", "Le bordereau de collecte, cadré sur votre agence."),
        p(
            "Retrouvez un client par son nom, son contrat ou son compteur dans le "
            "champ de recherche, puis cliquez <b>Saisir</b> au bout de sa ligne."
        ),
        _ecran("sv-05-saisie", "La fenêtre de saisie rappelle la référence géographique et le compteur."),
        p(
            "Si vous déclarez un abonnement, le <b>numéro relevé devient "
            "obligatoire</b>. La plateforme refuse d'enregistrer sans lui, et "
            "elle a raison : un abonnement sans numéro ne peut être vérifié par "
            "personne, donc pas payé."
        ),
        _ecran("sv-06-numero-exige", "Un abonné déclaré sans numéro : la plateforme bloque et explique."),
        _ecran("sv-07-saisie-complete", "Le numéro renseigné, l'enregistrement redevient possible."),
        p(
            "Pour plusieurs lignes au même résultat, cochez-les dans le tableau "
            "et appliquez le statut en une fois. Les lignes que la règle refuse, "
            "un abonnement sans numéro par exemple, vous sont signalées plutôt "
            "qu'écrites en silence."
        ),
        PageBreak(),
        titre("5. Le contrôle Back office", "h1"),
        p(
            "C'est le cœur du dispositif. Le bouton <b>Back office</b> confronte "
            "chacune des déclarations à ce que SOCADEL enregistre réellement "
            "dans sa base des abonnements, et rend un verdict par ligne. La "
            "colonne <b>Back office</b> du tableau porte ce verdict, et la "
            "colonne <b>Back office Date</b> l'instant du contrôle."
        ),
        p(
            "Trois colonnes se remplissent alors d'elles-mêmes : la date du "
            "contrôle, la <b>date d'abonnement</b>, et le <b>statut</b> qui "
            "passe à « abonné » lorsque la base confirme. Une ligne partie en "
            "relance <b>MRA</b> que la campagne a fini par convertir porte "
            "alors <b>MRA</b> en Responsable, et non le nom de l'agent : c'est "
            "la relance automatique qui a obtenu l'abonnement, et la prime doit "
            "le dire."
        ),
        tableau(
            [
                ["Verdict", "Ce qu'il signifie", "Payable"],
                ["Confirmé", "Le référentiel corrobore votre déclaration", "Oui"],
                [
                    "Infirmé",
                    "Le référentiel dit autre chose : abonnement absent, ou "
                    "numéro différent de celui relevé",
                    "Non",
                ],
                ["Introuvable", "Le contrat déclaré n'existe pas au référentiel", "Non"],
                ["Non vérifié", "La ligne n'a pas encore été confrontée", "Non"],
            ],
            [80, 280, 70],
            aligne_a_droite=[2],
        ),
        _ecran("sv-08-verification", "Deux lignes confrontées : une confirmée, une infirmée."),
        p(
            "Filtrez sur <b>Abonné</b> pour ne voir que les abonnements déclarés "
            "et leur verdict. Ici, deux déclarations identiques en apparence, "
            "deux issues différentes : celle dont le numéro relevé correspond à "
            "celui du référentiel est confirmée, l'autre non."
        ),
        _ecran("sv-09-verdicts", "Même statut déclaré, verdicts opposés : c'est le numéro qui tranche."),
        encadre(
            "<b>Corriger une ligne remet son verdict à zéro.</b> Une déclaration "
            "modifiée repasse en « non vérifié » et devra être re-confrontée. "
            "Personne ne peut donc faire passer une ligne infirmée en confirmée "
            "en la retouchant."
        ),
        PageBreak(),
        titre("6. Suivre, exporter, gérer", "h1"),
        titre("Le tableau de bord", "h2"),
        p(
            "Volume collecté, taux de confirmation, évolution jour par jour, "
            "classement de vos agents. Tout y est cadré sur votre agence."
        ),
        _ecran("sv-10-tableau-de-bord", "Le tableau de bord du superviseur."),
        titre("Les exports", "h2"),
        p(
            "<b>Exporter CSV</b> et <b>Exporter PDF</b> reprennent exactement le "
            "périmètre affiché à l'écran, filtres compris. Ce que vous voyez est "
            "ce que vous exportez, sans surprise."
        ),
        titre("Le répertoire de vos agents", "h2"),
        p(
            "Arrivée, changement d'affectation, départ : vous tenez la fiche de "
            "chaque collecteur. Un agent retiré du service n'apparaît plus dans "
            "la liste d'affectation, mais sa production passée reste."
        ),
        _ecran("sv-12-agents", "Le répertoire des collecteurs."),
        titre("Importer un bordereau rempli", "h2"),
        p(
            "Si un agent vous rend un fichier plutôt qu'un papier, "
            "<b>Import / Export</b> vous en donne le modèle, puis affiche un "
            "<b>aperçu</b> : lignes valides, lignes rejetées et leur motif. Rien "
            "n'est écrit avant que vous validiez cet aperçu."
        ),
        _ecran("sv-13-imports", "L'import se valide sur aperçu, jamais à l'aveugle."),
        titre("Tenir votre répertoire de tournées", "h1"),
        p(
            "Le terrain ouvre des zones plus vite qu'un import du référentiel ne "
            "se rejoue. Depuis l'écran <b>Itinéraires</b>, vous ouvrez une "
            "tournée, corrigez son libellé ou son rattachement, et retirez celle "
            "qui n'a jamais servi."
        ),
        tableau(
            [
                ["Règle", "Pourquoi"],
                [
                    "Le code d'une tournée ne se modifie pas",
                    "Les affectations et les lignes de bordereau déjà saisies le "
                    "portent : le changer romprait ce lien.",
                ],
                [
                    "Une tournée déjà confiée ne se supprime pas",
                    "La production y renvoie ; l'effacer laisserait des lignes "
                    "orphelines. Cessez simplement de l'affecter.",
                ],
                [
                    "Sans agence indiquée, la tournée rejoint la vôtre",
                    "Vous laisser en ouvrir ailleurs contournerait votre "
                    "périmètre.",
                ],
            ],
            [170, 260],
        ),
        _ecran("sv-11-itineraires",
               "Le répertoire des tournées, en recherche et en modification."),
        titre("Chercher, sans savoir où", "h1"),
        p(
            "Le champ de la barre du haut, ou <b>Ctrl+K</b>, ouvre une recherche "
            "qui traverse toute l'application : un nom de client, un contrat, un "
            "matricule d'agent, un code de tournée. Les résultats sont groupés "
            "par famille et vous emmènent à l'écran qui détient la réponse "
            "complète."
        ),
        p(
            "Vous ne verrez jamais que ce à quoi votre profil donne accès : la "
            "recherche interroge, pour chaque famille, le même moteur que "
            "l'écran correspondant. Une famille qui ne vous est pas ouverte est "
            "simplement absente des résultats."
        ),
        _ecran("sv-14-recherche",
               "La recherche globale, cadrée sur le périmètre de l'appelant."),
        PageBreak(),
        titre("7. Le raccourci du lendemain", "h1"),
        p(
            "Au matin suivant, reconnectez-vous en notant les itinéraires que "
            "l'agent vous annonce. Vous arrivez sur le bordereau déjà filtré, "
            "avec un bandeau qui le rappelle et un lien <b>Tout afficher</b> pour "
            "en sortir."
        ),
        _ecran("sv-15-bordereau-cadre", "Arrivée directe sur la tournée annoncée, sans passer par les filtres."),
        Spacer(1, 4 * mm),
        *_compte_et_mot_de_passe(),
        *_pied_de_guide("Superviseur, SOCADEL, une agence"),
    ]


# --- Agent de terrain -------------------------------------------------------


def agent_terrain() -> list:
    return [
        *_couverture(
            "Agent de terrain",
            "SOCADEL, sur le terrain",
            "Cocher les abonnements · suivre ses chiffres",
        ),
        titre("Votre rôle", "h1"),
        p(
            "Vous démarchez les clients de votre tournée et vous les aidez à "
            "s'abonner au service WhatsApp de SOCADEL. Dans la plateforme, vous "
            "n'avez <b>qu'un seul geste</b> : cocher la case Check en face du "
            "client qui s'est abonné."
        ),
        encadre(
            "<b>Un clic, et tout le reste se remplit seul.</b> La date du "
            "passage s'inscrit, le statut passe à « abonné », et votre nom "
            "apparaît en Responsable — c'est lui qui vous vaudra la ligne au "
            "moment du décompte. Vous n'avez ni date à saisir, ni statut à "
            "choisir, ni case à cocher ailleurs."
        ),
        Spacer(1, 4 * mm),
        *_connexion("AGENT_TERRAIN", "votre agence"),
        titre("2. Votre espace", "h1"),
        p(
            "Vous arrivez sur <b>Mon espace</b> : les itinéraires qu'on vous a "
            "confiés, votre production, et votre évolution sur les derniers "
            "jours."
        ),
        _ecran("ag-01-mon-espace", "Mon espace : vos itinéraires, votre production, votre évolution."),
        *puces(
            [
                "<b>Vos itinéraires confiés</b>, avec la date et le nombre de "
                "clients à démarcher.",
                "<b>Votre production</b> : abonnements obtenus, absents, refus, "
                "et le taux de confirmation du référentiel.",
                "<b>Votre évolution</b> sur les dernières journées, pour situer "
                "aujourd'hui par rapport à la semaine.",
            ]
        ),
        titre("3. Votre bordereau", "h1"),
        p(
            "L'entrée <b>Bordereau</b> ouvre la liste des clients de vos "
            "tournées, et rien d'autre : vous n'y voyez jamais ceux d'un "
            "collègue. Les colonnes sont réduites à ce qui vous sert — le nom du "
            "client, où il habite, son compteur, son numéro, et le bouton à "
            "cliquer. Les dix premières lignes s'affichent ; les suivantes sont "
            "en bas de page."
        ),
        _ecran("ag-02-bordereau", "Votre bordereau : les colonnes du relevé, et la colonne Check."),
        p(
            "Chaque colonne a sa propre case de recherche, sous son titre. Tapez "
            "un début de nom, de compteur ou de référence : la liste se réduit à "
            "mesure. C'est la manière la plus rapide de retrouver le client qui "
            "est devant vous."
        ),
        titre("Cocher un client", "h2"),
        p(
            "Cliquez sur le carré de la colonne <b>Check</b>. Il devient vert, et "
            "c'est fini."
        ),
        _ecran("ag-03-coche", "La ligne cochée : la date et le statut se sont remplis seuls."),
        p(
            "Si le numéro WhatsApp du client n'est pas encore sur la ligne, une "
            "petite fenêtre vous le demande avant d'enregistrer. C'est le seul "
            "moment où vous tapez quelque chose."
        ),
        _ecran("ag-04-modale-coche", "Le numéro relevé, le rapport et l'identité de la personne."),
        titre("Les trois questions de cette fenêtre", "h2"),
        *puces(
            [
                "<b>Rapport</b> — laissez <b>OK</b> : le client s'est abonné. "
                "Choisissez <b>MRA</b> seulement si vous êtes dans une zone sans "
                "réseau : le numéro est enregistré, l'équipe MRA relancera le "
                "client par WhatsApp, et vous n'avez plus à y revenir.",
                "<b>Numéro WhatsApp relevé</b> — celui sur lequel le client a "
                "reçu le message. Tapez-le comme vous le lisez, avec ou sans "
                "espaces : la plateforme le met en forme.",
                "<b>Identité</b> — <b>Propriétaire</b> par défaut. Choisissez "
                "<b>Locataire</b> quand la personne occupe le logement sans être "
                "au contrat, et <b>Relation</b> quand c'est un proche qui "
                "répond : la facture doit partir au bon numéro.",
            ]
        ),
        encadre(
            "<b>Un même numéro ne peut pas servir deux clients d'une même "
            "tournée.</b> Si vous le tentez, la plateforme refuse et vous dit "
            "quel contrat porte déjà ce numéro. Vérifiez le relevé — c'est "
            "presque toujours une ligne de décalage — ou signalez le cas à votre "
            "superviseur."
        ),
        titre("Se corriger", "h2"),
        p(
            "Cliquez de nouveau sur le carré vert : la ligne redevient à traiter. "
            "Vous pouvez alors cocher la bonne. Rien n'est perdu, et personne "
            "n'a besoin d'intervenir."
        ),
        titre("4. Ce que vous ne voyez pas, et pourquoi", "h1"),
        p(
            "Votre bordereau ne montre pas les colonnes <b>Back office</b>, "
            "<b>Date abonnement</b> ni <b>Responsable</b>. Ce ne sont pas des "
            "secrets : ce sont des colonnes que <b>vous ne remplissez pas</b>. "
            "Le back-office contrôle ensuite, dans la base des abonnements, que "
            "le client est bien allé au bout du parcours WhatsApp. Ce contrôle "
            "ne vous demande rien et vous encombrerait l'écran."
        ),
        titre("Si un chiffre vous paraît faux", "h2"),
        p(
            "Un abonnement peut apparaître <b>infirmé</b> si le numéro relevé ne "
            "correspond pas à celui que SOCADEL connaît ; le client devra alors "
            "reprendre l'enrôlement WhatsApp. Pour tout le reste, rapprochez-vous "
            "de votre superviseur : il voit la feuille entière, colonnes de "
            "contrôle comprises."
        ),
        Spacer(1, 4 * mm),
        *_compte_et_mot_de_passe(),
        *_pied_de_guide("Agent de terrain, SOCADEL"),
    ]


# --- Administrateur ---------------------------------------------------------


def administrateur() -> list:
    return [
        *_couverture(
            "Administrateur",
            "SOCADEL",
            "Gouverner les accès · attribuer les périmètres · débloquer",
        ),
        titre("Votre rôle", "h1"),
        p(
            "Vous êtes responsable côté SOCADEL. Vous n'êtes pas là pour saisir "
            "de la production, mais pour <b>décider qui entre</b>, sur quel "
            "territoire, et pour débloquer ceux qui ne peuvent plus se connecter. "
            "Vous portez une vue nationale sur les données SOCADEL."
        ),
        tableau(
            [
                ["Vous pouvez", "Vous ne pouvez pas"],
                [
                    "Approuver ou refuser une demande d'accès, attribuer une "
                    "agence ou une région, suspendre et réactiver un compte, "
                    "réinitialiser un mot de passe, et tout ce que fait un "
                    "superviseur.",
                    "Créer un autre administrateur, agir sur un pair ou sur le "
                    "super utilisateur NEXT LTD, changer le rôle d'un compte "
                    "existant, administrer le référentiel clients.",
                ],
            ],
            [215, 215],
        ),
        encadre(
            "<b>Personne n'agit sur son propre rang.</b> Vous ne pouvez ni créer "
            "un second administrateur, ni suspendre votre propre compte. Ce n'est "
            "pas une limitation arbitraire : c'est ce qui empêche un compte "
            "compromis de se démultiplier."
        ),
        Spacer(1, 4 * mm),
        *_connexion("ADMINISTRATEUR", None),
        titre("2. Votre tableau de bord", "h1"),
        p(
            "Vous arrivez sur la vue nationale : le volume de l'ensemble du "
            "réseau, le taux de confirmation, l'évolution. C'est votre point de "
            "situation avant d'entrer dans le détail."
        ),
        _ecran("ad-01-tableau-de-bord", "Le tableau de bord national."),
        titre("3. Gouverner les accès", "h1"),
        p(
            "L'entrée <b>Comptes</b> est la vôtre. Elle s'ouvre par défaut sur "
            "les demandes <b>en attente d'approbation</b> : ce sont les personnes "
            "qui se sont inscrites et ont confirmé leur adresse."
        ),
        _ecran("ad-02-comptes", "Les comptes, filtrés sur les demandes à trancher."),
        p(
            "Cliquez <b>Examiner</b> pour ouvrir la demande. Trois décisions vous "
            "appartiennent."
        ),
        tableau(
            [
                ["Décision", "Ce qu'elle emporte"],
                [
                    "Le profil attribué",
                    "Seuls les rangs inférieurs au vôtre vous sont proposés : "
                    "superviseur et agent de terrain.",
                ],
                [
                    "Le périmètre",
                    "Une agence ou une région pour un superviseur. <b>Sans "
                    "périmètre, ses requêtes sont refusées</b> plutôt que "
                    "d'ouvrir les 181 agences.",
                ],
                [
                    "L'agent rattaché",
                    "Obligatoire pour un compte agent : c'est ce rattachement qui "
                    "délimite ce que son titulaire verra.",
                ],
            ],
            [110, 320],
        ),
        _ecran("ad-03-approbation", "L'examen d'une demande : profil, périmètre, et motif en cas de refus."),
        p(
            "Un refus part avec le <b>motif</b> que vous indiquez : le demandeur "
            "le reçoit par courriel, et peut déposer une nouvelle demande."
        ),
        PageBreak(),
        titre("4. Débloquer un mot de passe", "h1"),
        p(
            "Quand un superviseur ou un agent ne peut plus se connecter et n'a "
            "plus accès à sa boîte, ouvrez son compte et cliquez "
            "<b>Réinitialiser le mot de passe</b>."
        ),
        p(
            "La plateforme génère un mot de passe provisoire lisible au "
            "téléphone, sans I, l, O ni 0 pour éviter les confusions à l'oral. "
            "<b>Il ne part jamais par courriel</b> : vous le communiquez de vive "
            "voix, et le titulaire devra le remplacer à sa prochaine connexion."
        ),
        titre("Suspendre plutôt que supprimer", "h2"),
        p(
            "Un départ, une absence prolongée, un doute : suspendez le compte. "
            "Il ne peut plus se connecter, mais sa production passée reste "
            "attachée à son nom. Vous le réactivez d'un clic au retour."
        ),
        titre("Le maillage territorial", "h1"),
        p(
            "Le réseau bouge : une agence ouvre dans un lotissement neuf, une "
            "autre devient inaccessible. L'écran <b>Territoire</b> vous permet de "
            "suivre ces mouvements le jour même, sans attendre un nouvel import "
            "du référentiel clients."
        ),
        _ecran("ad-04-territoire",
               "Les 181 agences, leurs divisions et leurs directions régionales."),
        tableau(
            [
                ["Geste", "Ce qu'il emporte"],
                [
                    "Ouvrir une agence",
                    "Elle rejoint aussitôt le sélecteur de connexion et les "
                    "listes de travail.",
                ],
                [
                    "Corriger un rattachement",
                    "Division et direction se modifient. <b>Le nom, non</b> : "
                    "comptes, itinéraires et référentiel le portent tel quel.",
                ],
                [
                    "Fermer une agence",
                    "Elle quitte les listes et le sélecteur de connexion le jour "
                    "même, mais reste attachée à la production passée. Le motif "
                    "est exigé.",
                ],
                [
                    "Supprimer une agence",
                    "Réservé à la correction d'une saisie : dès qu'un compte ou "
                    "une tournée s'y rattache, seule la fermeture reste possible.",
                ],
            ],
            [130, 300],
        ),
        PageBreak(),
        titre("Les rôles et leurs permissions", "h1"),
        p(
            "L'écran <b>Rôles</b> montre ce que chaque profil porte réellement. "
            "Il rend un refus compréhensible sans aller lire le code : on y voit "
            "le rang, le nombre de droits effectifs, et le détail de chacun."
        ),
        _ecran("ad-05-roles",
               "Les quatre rôles, du plus large au plus restreint."),
        encadre(
            "<b>On retranche, on n'ajoute jamais.</b> Les quatre rôles et leur "
            "matrice sont écrits dans le code, où ils sont relus, testés et "
            "versionnés. Retirer un droit ici le ferme aussitôt ; aucune écriture "
            "en base ne peut en ouvrir un que le code ne donne pas. C'est ce qui "
            "rend l'escalade de privilèges impossible par la donnée, y compris "
            "depuis une sauvegarde restaurée."
        ),
        titre("Le journal d'audit", "h1"),
        p(
            "Qui a affecté cette tournée, qui a fermé cette agence, qui a "
            "réinitialisé ce mot de passe. L'écran <b>Audit et journal</b> "
            "répond, du plus récent au plus ancien, avec des filtres par auteur, "
            "par action et par période."
        ),
        _ecran("ad-06-audit",
               "Le journal : l'auteur, le geste, la cible et l'issue."),
        p(
            "Le journal enregistre les <b>écritures</b> et les <b>tentatives de "
            "connexion</b>, pas les consultations : un tableau de bord ouvert "
            "deux minutes produit des dizaines de lectures, et personne ne "
            "cherche qui l'a regardé."
        ),
        encadre(
            "<b>Il ne retient jamais le contenu transmis.</b> Ni mot de passe, ni "
            "numéro de téléphone, ni nom de client. Les recopier créerait une "
            "seconde base de données personnelles, moins protégée que la "
            "première et consultable par des gens qui n'ont pas à la voir. Le "
            "geste et sa cible suffisent à répondre à « qui a fait quoi »."
        ),
        PageBreak(),
        titre("5. Ce que vous voyez du terrain", "h1"),
        p(
            "Rien ne vous empêche d'ouvrir le bordereau : votre portée est "
            "nationale, vous y voyez toutes les agences. C'est utile pour "
            "arbitrer une réclamation, moins pour le travail quotidien, qui "
            "revient au superviseur."
        ),
        _ecran("ad-07-bordereau", "Le bordereau vu en portée nationale, sans restriction d'agence."),
        Spacer(1, 4 * mm),
        *_compte_et_mot_de_passe(),
        *_pied_de_guide("Administrateur, SOCADEL"),
    ]


# --- Super utilisateur ------------------------------------------------------


def super_utilisateur() -> list:
    return [
        *_couverture(
            "Super utilisateur",
            "NEXT LTD",
            "Exploiter la plateforme · répondre de son fonctionnement",
        ),
        titre("Votre rôle", "h1"),
        p(
            "Vous êtes l'exploitant de la plateforme, chez NEXT LTD. "
            "L'administrateur SOCADEL s'en <b>sert</b> ; vous en <b>répondez</b>. "
            "Vous faites tout ce qu'il fait, plus deux gestes qui engagent le "
            "fonctionnement du système."
        ),
        tableau(
            [
                ["Ce que vous seul pouvez faire", "Pourquoi cela vous revient"],
                [
                    "Changer le rôle d'un compte existant, y compris promouvoir "
                    "un administrateur",
                    "C'est le geste qui ouvre la gouvernance à quelqu'un. Le "
                    "laisser à SOCADEL reviendrait à lui permettre de se "
                    "démultiplier sans contrôle.",
                ],
                [
                    "Administrer le référentiel clients",
                    "C'est la source sur laquelle repose toute la vérification. "
                    "Qui peut la modifier peut décider de ce qui sera payé.",
                ],
            ],
            [180, 250],
        ),
        encadre(
            "<b>Vous non plus n'agissez pas sur votre propre rang.</b> Un super "
            "utilisateur ne peut ni créer ni suspendre un autre super "
            "utilisateur. La règle vaut pour les quatre profils, sans exception : "
            "elle ferme l'escalade de privilèges par construction."
        ),
        Spacer(1, 4 * mm),
        *_connexion("SUPER_UTILISATEUR", None),
        titre("2. Votre tableau de bord", "h1"),
        p(
            "La même vue nationale que l'administrateur, sur l'ensemble du "
            "réseau SOCADEL."
        ),
        _ecran("su-01-tableau-de-bord", "Le tableau de bord, en portée nationale."),
        titre("3. Les comptes", "h1"),
        p(
            "L'écran est celui de l'administrateur, mais vous y agissez sur les "
            "trois rangs inférieurs, administrateurs compris."
        ),
        _ecran("su-02-comptes", "Les comptes : vous les voyez tous, sauf vos pairs."),
        _ecran("su-03-approbation", "L'examen d'une demande. Le profil administrateur vous est ouvert."),
        titre("4. Le référentiel et la bascule à venir", "h1"),
        p(
            "Aujourd'hui la vérification s'appuie sur une base de test chargée "
            "depuis le classeur SOCADEL : 425 920 clients, tous en "
            "<font face='Courier'>not_checked</font> puisque la campagne n'a pas "
            "encore eu lieu. <b>Toute déclaration d'abonnement y ressort donc "
            "infirmée</b>, ce qui est le comportement correct."
        ),
        p(
            "Le jour où l'API NEXT sera ouverte sur la base MRA, un seul "
            "adaptateur sera à écrire : le port de lecture du référentiel est "
            "déjà en place, et rien d'autre dans le code ne sait d'où viennent "
            "les données."
        ),
        tableau(
            [
                ["Sujet", "État aujourd'hui", "Ce qui reste"],
                [
                    "Source de vérité",
                    "Base de test PostgreSQL, 425 920 clients",
                    "Brancher l'API NEXT / MRA",
                ],
                [
                    "Statuts WhatsApp",
                    "Tous en not_checked",
                    "Alimentés par l'enrôlement réel",
                ],
                [
                    "Périmètres",
                    "Mécanisme en place, superviseur sans périmètre bloqué",
                    "Attribuer les 181 agences aux superviseurs réels",
                ],
                [
                    "Mots de passe et clé de signature",
                    "Valeurs de mise en route",
                    "À remplacer impérativement",
                ],
            ],
            [110, 190, 130],
        ),
        titre("Le maillage territorial", "h1"),
        p(
            "Le réseau bouge : une agence ouvre dans un lotissement neuf, une "
            "autre devient inaccessible. L'écran <b>Territoire</b> vous permet de "
            "suivre ces mouvements le jour même, sans attendre un nouvel import "
            "du référentiel clients."
        ),
        _ecran("su-04-territoire",
               "Les 181 agences, leurs divisions et leurs directions régionales."),
        tableau(
            [
                ["Geste", "Ce qu'il emporte"],
                [
                    "Ouvrir une agence",
                    "Elle rejoint aussitôt le sélecteur de connexion et les "
                    "listes de travail.",
                ],
                [
                    "Corriger un rattachement",
                    "Division et direction se modifient. <b>Le nom, non</b> : "
                    "comptes, itinéraires et référentiel le portent tel quel.",
                ],
                [
                    "Fermer une agence",
                    "Elle quitte les listes et le sélecteur de connexion le jour "
                    "même, mais reste attachée à la production passée. Le motif "
                    "est exigé.",
                ],
                [
                    "Supprimer une agence",
                    "Réservé à la correction d'une saisie : dès qu'un compte ou "
                    "une tournée s'y rattache, seule la fermeture reste possible.",
                ],
            ],
            [130, 300],
        ),
        PageBreak(),
        titre("Les rôles et leurs permissions", "h1"),
        p(
            "L'écran <b>Rôles</b> montre ce que chaque profil porte réellement. "
            "Il rend un refus compréhensible sans aller lire le code : on y voit "
            "le rang, le nombre de droits effectifs, et le détail de chacun."
        ),
        _ecran("su-05-roles",
               "Les quatre rôles, du plus large au plus restreint."),
        encadre(
            "<b>On retranche, on n'ajoute jamais.</b> Les quatre rôles et leur "
            "matrice sont écrits dans le code, où ils sont relus, testés et "
            "versionnés. Retirer un droit ici le ferme aussitôt ; aucune écriture "
            "en base ne peut en ouvrir un que le code ne donne pas. C'est ce qui "
            "rend l'escalade de privilèges impossible par la donnée, y compris "
            "depuis une sauvegarde restaurée."
        ),
        titre("Le journal d'audit", "h1"),
        p(
            "Qui a affecté cette tournée, qui a fermé cette agence, qui a "
            "réinitialisé ce mot de passe. L'écran <b>Audit et journal</b> "
            "répond, du plus récent au plus ancien, avec des filtres par auteur, "
            "par action et par période."
        ),
        _ecran("su-06-audit",
               "Le journal : l'auteur, le geste, la cible et l'issue."),
        p(
            "Le journal enregistre les <b>écritures</b> et les <b>tentatives de "
            "connexion</b>, pas les consultations : un tableau de bord ouvert "
            "deux minutes produit des dizaines de lectures, et personne ne "
            "cherche qui l'a regardé."
        ),
        encadre(
            "<b>Il ne retient jamais le contenu transmis.</b> Ni mot de passe, ni "
            "numéro de téléphone, ni nom de client. Les recopier créerait une "
            "seconde base de données personnelles, moins protégée que la "
            "première et consultable par des gens qui n'ont pas à la voir. Le "
            "geste et sa cible suffisent à répondre à « qui a fait quoi »."
        ),
        PageBreak(),
        titre("5. Ce que vous voyez du terrain", "h1"),
        _ecran("su-07-bordereau", "Le bordereau, sans aucune restriction de périmètre."),
        Spacer(1, 4 * mm),
        *_compte_et_mot_de_passe(),
        *_pied_de_guide("Super utilisateur, NEXT LTD"),
    ]
