"""Diagrammes UML du dossier de conception.

Chaque fonction renvoie un `Drawing` prêt à être inséré dans le flux du
document. Les dimensions sont calées sur la largeur utile d'une page A4 en
portrait (environ 470 pt) ou en paysage (environ 720 pt).
"""

from __future__ import annotations

from reportlab.graphics.shapes import Drawing, Line, Rect

from .dessin import (
    Boite,
    BLANC,
    BLEU,
    BLEU_CLAIR,
    BLEU_SOMBRE,
    BLEU_TRES_CLAIR,
    GRIS,
    GRIS_CLAIR,
    GRIS_FOND,
    ORANGE,
    POLICE,
    POLICE_GRAS,
    ROUGE,
    TEXTE,
    VERT,
    acteur,
    activation,
    boite,
    cadre_systeme,
    cas_utilisation,
    classe,
    fleche,
    ligne_de_vie,
    losange,
    message,
    note,
    texte,
)

LARGEUR = 470.0


# --- 1. Contexte du système ------------------------------------------------


def contexte() -> Drawing:
    """Le système au milieu de son écosystème.

    Montre ce que le bordereau touche et, surtout, ce qu'il ne fait pas : le
    ChatBot et MRA sont hors périmètre, l'API de recoupement reste à ouvrir.
    """
    d = Drawing(LARGEUR, 320)

    centre = boite(
        d, 158, 138, 158, 54,
        "Bordereau SOCADEL",
        sous_titre="Back-office de pilotage",
        fond=BLEU, couleur_texte=BLANC, bordure=BLEU_SOMBRE,
        taille=9.5, police=POLICE_GRAS,
    )

    # Les quatre rôles, du plus large au plus restreint.
    acteur(d, 46, 262, "Super utilisateur", role="NEXT LTD")
    acteur(d, 46, 188, "Administrateur", role="SOCADEL")
    acteur(d, 46, 114, "Superviseur", role="SOCADEL, une agence")
    acteur(d, 46, 40, "Agent de terrain", role="Distributeur")

    chatbot = boite(
        d, 358, 246, 102, 38, "ChatBot WhatsApp",
        sous_titre="NEXT LTD, Meta", fond=BLEU_TRES_CLAIR, taille=8,
    )
    mra = boite(
        d, 358, 154, 102, 38, "Plateforme MRA",
        sous_titre="SOCADEL, facturation", fond=BLEU_TRES_CLAIR, taille=8,
    )
    referentiel = boite(
        d, 358, 62, 102, 38, "Référentiel clients",
        sous_titre="Base de test aujourd'hui", fond=BLEU_TRES_CLAIR, taille=8,
    )

    # Chaque flèche vise sa propre hauteur sur le bord gauche : un point de
    # convergence unique empilait les quatre étiquettes au même endroit.
    for y_acteur, y_bord, libelle in (
        (272, 186, "exploite"),
        (198, 172, "gouverne"),
        (124, 158, "pilote"),
        (50, 144, "consulte"),
    ):
        fleche(d, 63, y_acteur, centre.x, y_bord, libelle=libelle)

    # Le pointillé dit déjà le hors-périmètre, l'étiquette ferait doublon et
    # viendrait mordre sur le cadre central.
    fleche(d, centre.droite, 178, chatbot.x, 262, pointillee=True)
    fleche(d, centre.droite, 166, mra.x, 172, pointillee=True)
    fleche(d, centre.droite, 154, referentiel.x, 82, libelle="vérifie")

    fleche(d, chatbot.centre_x, chatbot.y, mra.centre_x, mra.haut,
           libelle="enrôlement")
    fleche(d, mra.centre_x, mra.y, referentiel.centre_x, referentiel.haut,
           libelle="alimente")

    note(
        d, 132, 6, 216, 40,
        "L'API de recoupement NEXT et MRA n'est pas encore ouverte : la "
        "vérification s'appuie aujourd'hui sur une base de test.",
    )
    return d


# --- 2. Cas d'utilisation par acteur ---------------------------------------


def cas_superviseur() -> Drawing:
    d = Drawing(LARGEUR, 330)
    cadre_systeme(d, 110, 10, 350, 310, "Bordereau SOCADEL")
    acteur(d, 45, 150, "Superviseur")

    cas = [
        ("Affecter des itinéraires", 268),
        ("Imprimer le bordereau terrain", 236),
        ("Saisir la production de l'agent", 204),
        ("Corriger en lot une sélection", 172),
        ("Importer un bordereau rempli", 140),
        ("Vérifier auprès du référentiel", 108),
        ("Exporter CSV / PDF", 76),
        ("Gérer les agents (CRUD)", 44),
    ]
    for libelle, y in cas:
        b = cas_utilisation(d, 145, y, 280, 24, libelle)
        fleche(d, 58, 160, b.x, b.centre_y, pointe=False, couleur=GRIS_CLAIR)

    note(
        d, 145, 16, 280, 22,
        "Le superviseur ne gère pas les comptes de connexion : "
        "c'est une prérogative d'administrateur.",
    )
    return d


def cas_agent() -> Drawing:
    d = Drawing(LARGEUR, 210)
    cadre_systeme(d, 110, 10, 350, 190, "Bordereau SOCADEL")
    acteur(d, 45, 95, "Agent de terrain")

    for libelle, y in (
        ("Se connecter", 148),
        ("Cocher les clients abonnés", 116),
        ("Consulter ses itinéraires confiés", 84),
        ("Consulter ses KPI et son évolution", 52),
    ):
        b = cas_utilisation(d, 145, y, 280, 24, libelle)
        fleche(d, 58, 105, b.x, b.centre_y, pointe=False, couleur=GRIS_CLAIR)

    note(
        d, 145, 16, 280, 30,
        "Portée volontairement réduite : un seul geste d'écriture, cocher, "
        "et seulement sur sa propre tournée.",
    )
    return d


def cas_super_utilisateur() -> Drawing:
    """Ce que NEXT LTD peut faire et que SOCADEL ne peut pas."""
    d = Drawing(LARGEUR, 224)
    cadre_systeme(d, 108, 8, 352, 206, "Bordereau SOCADEL")
    acteur(d, 44, 100, "Super utilisateur", role="NEXT LTD")

    for libelle, y, saillant in (
        ("Changer le rôle d'un compte existant", 160, True),
        ("Administrer le référentiel clients", 128, True),
        ("Réinitialiser n'importe quel mot de passe", 96, False),
        ("Exercer tous les droits de l'administrateur", 64, False),
    ):
        b = cas_utilisation(
            d, 142, y, 282, 24, libelle,
            fond=BLEU if saillant else BLEU_TRES_CLAIR,
            bordure=BLEU_SOMBRE if saillant else BLEU,
            couleur_texte=BLANC if saillant else TEXTE,
            police=POLICE_GRAS if saillant else POLICE,
        )
        fleche(d, 57, 110, b.x, b.centre_y, pointe=False, couleur=GRIS_CLAIR)

    note(
        d, 142, 12, 282, 30,
        "Les deux cas en bleu soutenu sont les seuls que l'administrateur "
        "SOCADEL n'a pas. Ils engagent le fonctionnement du système, et non "
        "son exploitation quotidienne.",
    )
    return d


def cas_administrateur() -> Drawing:
    d = Drawing(LARGEUR, 224)
    cadre_systeme(d, 108, 8, 352, 206, "Bordereau SOCADEL")
    acteur(d, 44, 100, "Administrateur", role="SOCADEL")

    for libelle, y in (
        ("Approuver ou refuser une demande d'accès", 160),
        ("Attribuer un périmètre à un superviseur", 128),
        ("Réinitialiser le mot de passe de ses équipes", 96),
        ("Exercer tous les droits du superviseur", 64),
    ):
        b = cas_utilisation(d, 142, y, 282, 24, libelle)
        fleche(d, 57, 110, b.x, b.centre_y, pointe=False, couleur=GRIS_CLAIR)

    note(
        d, 142, 12, 282, 30,
        "Portée nationale sur les données SOCADEL, mais aucune main sur un "
        "pair ni sur le super utilisateur qui lui a ouvert l'accès.",
    )
    return d


# --- 3. Classes du domaine -------------------------------------------------


def classes_domaine() -> Drawing:
    """Modèle du domaine, sans aucune trace d'infrastructure."""
    d = Drawing(740, 400)

    utilisateur = classe(
        d, 20, 250, 150, "Utilisateur",
        ["identifiant", "role : Role", "agent_id : UUID?", "region / agence",
         "actif", "+ contexte_acces()"],
        stereotype="entité",
    )
    agent = classe(
        d, 20, 90, 150, "AgentTerrain",
        ["matricule", "nom_complet", "telephone : NumeroTelephone?",
         "zone_rattachement", "photo_url", "actif"],
        stereotype="entité",
    )
    affectation = classe(
        d, 215, 210, 155, "Affectation",
        ["agent_id", "itineraire_code", "date_travail", "superviseur_id",
         "statut : StatutAffectation", "+ demarrer() / cloturer()"],
        stereotype="entité",
    )
    itineraire = classe(
        d, 215, 60, 155, "Itineraire",
        ["code : CodeItineraire", "libelle", "region / agence",
         "nombre_clients", "+ taux_couverture()"],
        stereotype="entité",
    )
    ligne = classe(
        d, 415, 195, 165, "LigneBordereau",
        ["service_no : ServiceNo", "statut : StatutCollecte",
         "numero_collecte", "verdict : Verdict", "+ declarer()",
         "+ appliquer_verdict()", "+ est_remuneree"],
        stereotype="entité",
        bordure=VERT,
    )
    client = classe(
        d, 415, 40, 165, "Client",
        ["service_no : ServiceNo", "nom", "ref_geo : RefGeo",
         "code_itineraire", "whatsapp_status", "+ est_abonne_whatsapp"],
        stereotype="source de vérité",
        bordure=ORANGE,
    )
    verif = classe(
        d, 605, 120, 100, "verification",
        ["+ verifier(ligne,", "   client)", "→ Verdict"],
        stereotype="service",
        fond=GRIS_FOND,
    )

    fleche(d, utilisateur.centre_x, utilisateur.y, agent.centre_x, agent.haut,
           pointillee=True, libelle="0..1")
    fleche(d, utilisateur.droite, 275, affectation.x, 275, libelle="crée")
    fleche(d, agent.droite, 140, affectation.x, 232, libelle="1..*")
    losange(d, affectation.x - 6, 232)
    fleche(d, itineraire.droite, 100, client.x, 90, libelle="1..*")
    fleche(d, affectation.droite, 250, ligne.x, 250, libelle="matérialise 1..*")
    losange(d, ligne.x - 6, 250, plein=True)
    fleche(d, client.centre_x, client.haut, ligne.centre_x, ligne.y,
           pointillee=True, libelle="instantané")
    fleche(d, ligne.droite, 230, verif.x, 172, libelle="confronte")
    fleche(d, client.droite, 95, verif.x, 132, libelle="fait foi")
    fleche(d, affectation.centre_x, affectation.y, itineraire.centre_x,
           itineraire.haut, libelle="porte sur")

    note(
        d, 20, 10, 350, 34,
        "est_remuneree = déclarée ABONNE ET verdict CONFIRME. "
        "La déclaration seule ne suffit jamais : c'est la règle de prime du dispositif.",
    )
    return d


# --- 4. Séquences ----------------------------------------------------------

def sequence_affectation() -> Drawing:
    """Du briefing du matin au bordereau imprimé."""
    d = Drawing(700, 300)
    haut, bas = 282, 34

    sup = ligne_de_vie(d, 60, haut, bas, "Superviseur", 92)
    ui = ligne_de_vie(d, 210, haut, bas, "Écran affectation", 110)
    api = ligne_de_vie(d, 370, haut, bas, "API + cas d'usage", 112)
    bd = ligne_de_vie(d, 570, haut, bas, "PostgreSQL", 92)

    activation(d, ui, 248, 62)
    activation(d, api, 234, 74)

    message(d, sup, ui, 248, "choisit l'agent et ses itinéraires")
    message(d, ui, api, 234, "POST /itineraires/affectations")
    message(d, api, api + 46, 214, "exiger(ITINERAIRE_AFFECTER)")
    message(d, api, bd, 194, "l'agent et l'itinéraire existent-ils ?")
    message(d, bd, api, 176, "oui", retour=True)
    message(d, api, bd, 158, "déjà affecté ce jour-là ?")
    message(d, bd, api, 140, "non", retour=True)
    message(d, api, bd, 122, "INSERT affectation")
    message(d, bd, api, 104, "clients triés par REF_GEO", retour=True)
    message(d, api, bd, 86, "INSERT des lignes, par lots")
    message(d, api, ui, 68, "201 Created", retour=True)
    message(d, ui, sup, 50, "bordereau prêt à imprimer", retour=True)

    note(
        d, 40, 6, 620, 22,
        "Une seule transaction : l'affectation et ses lignes sont écrites ensemble, ou pas du tout.",
    )
    return d


def sequence_verification() -> Drawing:
    """Saisie du soir, puis recoupement avec la source de vérité."""
    d = Drawing(700, 300)
    haut, bas = 282, 34

    sup = ligne_de_vie(d, 60, haut, bas, "Superviseur", 92)
    api = ligne_de_vie(d, 225, haut, bas, "API + cas d'usage", 112)
    dom = ligne_de_vie(d, 400, haut, bas, "Domaine", 92)
    bd = ligne_de_vie(d, 570, haut, bas, "Référentiel", 92)

    activation(d, api, 248, 56)

    message(d, sup, api, 248, "PATCH /bordereau/{id}, statut ABONNE")
    message(d, api, dom, 230, "ligne.declarer(ABONNE, numéro)")
    message(d, dom, api, 212, "verdict remis à NON_VERIFIE", retour=True)
    message(d, api, bd, 194, "UPDATE de la ligne")

    trait = Line(40, 178, 660, 178, strokeColor=GRIS_CLAIR, strokeWidth=0.8)
    trait.strokeDashArray = [4, 3]
    d.add(trait)
    texte(d, 40, 182, ", plus tard : le contrôle, ", taille=6.5, couleur=GRIS)

    message(d, sup, api, 158, "POST /bordereau/verification")
    message(d, api, bd, 140, "clients par SERVICE_NO, en un seul lot")
    message(d, bd, api, 122, "whatsapp_status de chacun", retour=True)
    message(d, api, dom, 104, "verifier(ligne, client)")
    message(d, dom, api, 86, "CONFIRME / INFIRME / INTROUVABLE", retour=True)
    message(d, api, bd, 68, "UPDATE des verdicts, par lots")
    message(d, api, sup, 50, "rapport de vérification", retour=True)

    note(
        d, 40, 6, 620, 22,
        "Un seul aller-retour pour tout le lot : vérifier ligne à ligne serait quadratique.",
    )
    return d


def sequence_import() -> Drawing:
    """Import en deux temps : aperçu, puis validation."""
    d = Drawing(700, 250)
    haut, bas = 232, 34

    sup = ligne_de_vie(d, 75, haut, bas, "Superviseur", 92)
    ui = ligne_de_vie(d, 255, haut, bas, "Modal d'aperçu", 104)
    api = ligne_de_vie(d, 435, haut, bas, "API", 80)
    bd = ligne_de_vie(d, 600, haut, bas, "PostgreSQL", 92)

    activation(d, ui, 198, 62)

    message(d, sup, ui, 198, "dépose le fichier")
    message(d, ui, api, 180, "POST /imports/apercu")
    message(d, api, ui, 162, "lignes valides, rejetées, et motifs", retour=True)
    message(d, ui, sup, 144, "affiche l'aperçu", retour=True)

    trait = Line(40, 128, 660, 128, strokeColor=GRIS_CLAIR, strokeWidth=0.8)
    trait.strokeDashArray = [4, 3]
    d.add(trait)
    texte(d, 40, 132, ", rien n'est encore écrit, ", taille=6.5, couleur=GRIS)

    message(d, sup, ui, 108, "confirme")
    message(d, ui, api, 90, "POST /imports")
    message(d, api, bd, 72, "INSERT, en une transaction unique")
    message(d, api, sup, 50, "bilan et anomalies", retour=True)

    note(
        d, 40, 6, 620, 22,
        "Le double temps est une exigence métier : on valide sur la foi de l'aperçu, jamais à l'aveugle.",
    )
    return d


# --- 5. Activité : parcours d'enrôlement -----------------------------------


def activite_enrolement() -> Drawing:
    """Le parcours WhatsApp du client, tel que décrit par le dispositif NEXT."""
    d = Drawing(LARGEUR, 340)

    d.add(Rect(30, 312, 12, 12, rx=6, ry=6, fillColor=BLEU_SOMBRE,
               strokeColor=BLEU_SOMBRE))
    texte(d, 50, 315, "L'agent présente le QR code, le lien ou le numéro", taille=7.5)

    etapes = [
        ("Le client ouvre WhatsApp et écrit « Bonjour »", 278),
        ("Il choisit sa langue : 1 français · 2 anglais", 246),
        ("Il choisit le service : 1 Facture Digitale", 214),
        ("Il saisit son numéro de contrat (9 chiffres, 20…)", 182),
        ("Le ChatBot affiche le nom trouvé au référentiel", 150),
    ]
    precedent_y = 312
    for libelle, y in etapes:
        b = boite(d, 60, y, 300, 24, libelle, fond=BLEU_TRES_CLAIR, taille=7.5)
        fleche(d, 210, precedent_y - (12 if precedent_y == 312 else 0), 210, b.haut)
        precedent_y = y

    # Décision.
    d.add(
        Rect(170, 100, 80, 34, fillColor=BLANC, strokeColor=BLEU, strokeWidth=1),
    )
    texte(d, 210, 121, "Le client", taille=7, ancrage="middle")
    texte(d, 210, 112, "confirme ?", taille=7, police=POLICE_GRAS, ancrage="middle")
    fleche(d, 210, 150, 210, 134)

    fleche(d, 250, 117, 330, 117, libelle="OUI")
    boite(d, 330, 100, 130, 34, "Abonnement activé",
          sous_titre="consentement horodaté",
          fond=VERT, couleur_texte=BLANC, bordure=VERT, taille=8)

    fleche(d, 170, 117, 90, 117, libelle="NON")
    boite(d, 20, 100, 70, 34, "Reprise de la saisie", fond=BLEU_TRES_CLAIR, taille=7)
    fleche(d, 55, 134, 60, 182, pointillee=True)

    fleche(d, 395, 100, 395, 76)
    boite(d, 300, 42, 160, 34, "MRA reçoit le contrat",
          sous_titre="le référentiel devient la preuve",
          fond=ORANGE, couleur_texte=BLANC, bordure=ORANGE, taille=8)

    d.add(Rect(389, 20, 12, 12, rx=6, ry=6, fillColor=BLANC,
               strokeColor=BLEU_SOMBRE, strokeWidth=1.6))
    fleche(d, 395, 42, 395, 32)

    note(
        d, 20, 20, 260, 60,
        "Le parcours s'auto-contrôle : il ne peut aboutir que depuis un compte "
        "WhatsApp actif, et le nom affiché est celui du référentiel. "
        "Un numéro collecté est donc déjà un numéro validé.",
    )
    return d


# --- 6. Architecture en couches --------------------------------------------


def architecture() -> Drawing:
    """Les quatre couches et le sens des dépendances."""
    d = Drawing(LARGEUR, 300)

    couches = [
        ("interfaces/, routes HTTP, schémas Pydantic", 240, BLEU_TRES_CLAIR, BLEU),
        ("application/, cas d'usage, ports, DTO", 180, BLEU_CLAIR, BLEU),
        ("domain/, entités, objets-valeurs, règles", 120, BLEU, BLEU_SOMBRE),
    ]
    for libelle, y, fond, bordure in couches:
        blanc = fond == BLEU
        boite(d, 90, y, 290, 46, libelle,
              fond=fond, bordure=bordure,
              couleur_texte=BLANC if blanc else None or BLEU_SOMBRE,
              taille=8.5, police=POLICE_GRAS)

    boite(d, 90, 40, 290, 46,
          "infrastructure/, PostgreSQL, bcrypt, JWT, openpyxl, reportlab",
          fond=GRIS_FOND, bordure=GRIS, taille=8)

    fleche(d, 235, 240, 235, 226, libelle="dépend de")
    fleche(d, 235, 180, 235, 166, libelle="dépend de")
    fleche(d, 380, 63, 400, 63, pointe=False, couleur=GRIS_CLAIR)
    fleche(d, 400, 63, 400, 143, pointe=False, couleur=GRIS_CLAIR)
    fleche(d, 400, 143, 385, 143, couleur=GRIS_CLAIR, libelle="")
    texte(d, 405, 100, "implémente", taille=6.8, couleur=GRIS)
    texte(d, 405, 91, "les ports", taille=6.8, couleur=GRIS)

    note(
        d, 20, 258, 430, 34,
        "Les flèches ne pointent que vers l'intérieur. L'infrastructure ne fournit "
        "que des implémentations : elle n'est jamais nommée par les couches hautes.",
    )
    note(
        d, 20, 4, 430, 28,
        "Vérifiable : les couches domain et application s'importent sur un "
        "interpréteur nu, sans FastAPI ni SQLAlchemy installés.",
    )
    return d


# --- 7. Habilitations ------------------------------------------------------


def habilitations() -> Drawing:
    """RBAC pour le « quoi », ABAC pour le « sur quoi »."""
    d = Drawing(LARGEUR, 250)

    boite(d, 20, 195, 430, 40,
          "Requête authentifiée → ContexteAcces (rôle + agent_id + périmètre)",
          fond=BLEU_CLAIR, taille=8.5, police=POLICE_GRAS)

    rbac = boite(d, 40, 110, 180, 62,
                 "RBAC, exiger(permission)",
                 sous_titre="Le rôle porte-t-il ce droit ? Réponse booléenne.",
                 fond=BLANC, bordure=BLEU, taille=8.5, police=POLICE_GRAS)
    abac = boite(d, 250, 110, 180, 62,
                 "ABAC, restreindre(filtre)",
                 sous_titre="Sur quelles données ? Le filtre est réécrit.",
                 fond=BLANC, bordure=ORANGE, taille=8.5, police=POLICE_GRAS)

    fleche(d, 130, 195, 130, 172)
    fleche(d, 340, 195, 340, 172)

    boite(d, 40, 52, 180, 40, "403 si le droit manque",
          fond=BLANC, bordure=ROUGE, couleur_texte=ROUGE, taille=8)
    boite(d, 250, 52, 180, 40, "Périmètre rétréci, jamais élargi",
          fond=BLANC, bordure=VERT, couleur_texte=VERT, taille=8)

    fleche(d, rbac.centre_x, rbac.y, 130, 92)
    fleche(d, abac.centre_x, abac.y, 340, 92)

    note(
        d, 20, 4, 430, 40,
        "Le rétrécissement en amont est délibéré : un contrôle a posteriori "
        "(« cet agent a-t-il le droit de voir cette ligne ? ») doit être appelé "
        "partout, et il suffit de l'oublier une fois pour tout exposer.",
    )
    return d


def hierarchie_roles() -> Drawing:
    """La règle qui dit sur qui chacun peut agir."""
    d = Drawing(LARGEUR, 232)

    rangs = [
        ("Super utilisateur", "NEXT LTD", 3, 178, BLEU_SOMBRE, BLANC),
        ("Administrateur", "SOCADEL", 2, 130, BLEU, BLANC),
        ("Superviseur", "une agence", 1, 82, BLEU_CLAIR, BLEU_SOMBRE),
        ("Agent de terrain", "sa production", 0, 34, BLEU_TRES_CLAIR, BLEU_SOMBRE),
    ]

    boites = []
    for nom, portee, rang, y, fond, encre in rangs:
        # La largeur décroît avec le rang : la portée se lit au premier regard.
        largeur = 150 + rang * 62
        b = boite(
            d, 96, y, largeur, 36, f"rang {rang}  {nom}",
            sous_titre=portee, fond=fond, bordure=BLEU_SOMBRE,
            couleur_texte=encre, taille=8.5, police=POLICE_GRAS,
        )
        boites.append(b)

    # Chaque rang n'atteint que celui d'en dessous, et par transitivité les
    # suivants : une seule flèche par palier suffit à le dire.
    for haut, bas in zip(boites, boites[1:]):
        fleche(d, 80, haut.centre_y, 80, bas.centre_y + 4,
               couleur=BLEU, epaisseur=1.2)
    texte(d, 22, 118, "agit sur", taille=7, couleur=GRIS, police=POLICE_GRAS)

    note(
        d, 96, 2, 336, 26,
        "Strictement inférieur : un administrateur ne crée pas un second "
        "administrateur. L'escalade de privilèges est fermée par construction.",
    )
    return d


# --- 8. Modèle physique ----------------------------------------------------


def modele_donnees() -> Drawing:
    """Tables PostgreSQL et cardinalités."""
    d = Drawing(720, 330)

    utilisateurs = classe(
        d, 20, 210, 150, "utilisateurs",
        ["PK id : uuid", "UQ identifiant", "role, actif", "FK agent_id →",
         "region, agence", "photo_url, email"],
        stereotype="table",
    )
    agents = classe(
        d, 20, 60, 150, "agents_terrain",
        ["PK id : uuid", "UQ matricule", "nom_complet, telephone",
         "zone_rattachement", "region, photo_url", "actif"],
        stereotype="table",
    )
    affectations = classe(
        d, 215, 175, 165, "affectations",
        ["PK id : uuid", "FK agent_id", "itineraire_code", "date_travail",
         "FK superviseur_id", "UQ (agent, itin, jour)"],
        stereotype="table",
    )
    itineraires = classe(
        d, 215, 45, 165, "itineraires",
        ["PK id : uuid", "UQ code : int", "libelle, region", "agence, mrc",
         "nombre_clients", "≈ 16 763 lignes"],
        stereotype="table",
    )
    lignes = classe(
        d, 420, 165, 165, "lignes_bordereau",
        ["PK id : uuid", "service_no, date", "statut, verdict",
         "numero_collecte", "FK agent / affectation", "FK client_id"],
        stereotype="table", bordure=VERT,
    )
    clients = classe(
        d, 420, 30, 165, "clients",
        ["PK id : uuid", "UQ service_no", "ref_geo, code_itineraire",
         "whatsapp_status", "region / division / agence", "≈ 425 920 lignes"],
        stereotype="table", bordure=ORANGE,
    )

    fleche(d, utilisateurs.centre_x, utilisateurs.y, agents.centre_x,
           agents.haut, libelle="0..1")
    fleche(d, agents.droite, 120, affectations.x, 200, libelle="1..N")
    fleche(d, utilisateurs.droite, 240, affectations.x, 240, libelle="1..N")
    fleche(d, affectations.droite, 220, lignes.x, 220, libelle="1..N")
    fleche(d, clients.droite, 60, 605, 60, pointe=False, couleur=GRIS_CLAIR)
    fleche(d, 605, 60, 605, 200, pointe=False, couleur=GRIS_CLAIR)
    fleche(d, 605, 200, lignes.droite, 200, libelle="1..N")
    fleche(d, itineraires.droite, 80, clients.x, 80, libelle="1..N")
    fleche(d, affectations.centre_x, affectations.y, itineraires.centre_x,
           itineraires.haut, libelle="N..1")

    note(
        d, 20, 10, 350, 34,
        "L'unicité (agent, itinéraire, jour) empêche de compter deux fois la même "
        "production. Aucun agent n'est jamais supprimé : on le retire du service.",
    )
    return d


# --- 10. Parcours par profil -----------------------------------------------
#
# Ces diagrammes sont larges : ils sont posés en paysage. Chaque boîte est une
# étape, chaque flèche l'enchaînement. Ce qui sort du logiciel, le travail sur
# le terrain, est tramé en pointillé pour qu'on ne le confonde pas avec un
# écran de l'application.

#: Largeur utile d'une page A4 en paysage, marges déduites.
LARGEUR_PAYSAGE = 720.0


def _etape(
    d: Drawing,
    x: float,
    y: float,
    largeur: float,
    numero: str,
    titre_etape: str,
    detail: str,
    *,
    hauteur: float = 54,
    fond=BLEU_TRES_CLAIR,
    bordure=BLEU,
    encre=TEXTE,
) -> Boite:
    """Une étape numérotée du parcours.

    Le numéro est dans le libellé plutôt que dans une pastille séparée : à
    cette taille, une pastille coûterait plus de place qu'elle n'en clarifie.
    """
    return boite(
        d, x, y, largeur, hauteur,
        f"{numero}. {titre_etape}",
        sous_titre=detail,
        fond=fond, bordure=bordure, couleur_texte=encre,
        taille=8, police=POLICE_GRAS,
    )


def _decision(d: Drawing, x: float, y: float, largeur: float, hauteur: float,
              question: str) -> Boite:
    """Point de décision. Le fond blanc le distingue des étapes bleutées."""
    return boite(
        d, x, y, largeur, hauteur, question,
        fond=BLANC, bordure=BLEU_SOMBRE, taille=8, police=POLICE_GRAS,
        epaisseur=1.4,
    )


def parcours_inscription() -> Drawing:
    """De la demande d'accès au compte utilisable."""
    d = Drawing(LARGEUR_PAYSAGE, 254)

    a = _etape(
        d, 8, 196, 218,
        "1", "Le demandeur s'inscrit",
        "identité, profil souhaité, agence, mot de passe et sa confirmation",
    )
    b = _etape(
        d, 251, 196, 218,
        "2", "Un courriel part vers son adresse",
        "lien de confirmation valable trois jours",
    )
    c = _etape(
        d, 494, 196, 218,
        "3", "Il confirme son adresse",
        "le compte passe en attente d'approbation",
    )
    fleche(d, a.droite, a.centre_y, b.x, b.centre_y)
    fleche(d, b.droite, b.centre_y, c.x, c.centre_y)

    question = _decision(
        d, 494, 96, 218, 54,
        "Un responsable approuve la demande ?",
    )
    fleche(d, c.centre_x, c.y, question.centre_x, question.haut)

    accorde = boite(
        d, 251, 96, 218, 54, "Compte actif",
        sous_titre="courriel d'ouverture, avec identifiant, profil et périmètre",
        fond=VERT, couleur_texte=BLANC, bordure=VERT, taille=8, police=POLICE_GRAS,
    )
    fleche(d, question.x, question.centre_y, accorde.droite, accorde.centre_y,
           libelle="oui")

    refuse = boite(
        d, 8, 96, 218, 54, "Demande refusée",
        sous_titre="courriel motivé, une nouvelle demande reste possible",
        fond=ROUGE, couleur_texte=BLANC, bordure=ROUGE, taille=8, police=POLICE_GRAS,
    )
    fleche(d, accorde.x, 110, refuse.droite, 110, pointillee=True, libelle="non")

    note(
        d, 8, 14, 480, 46,
        "S'inscrire dépose une demande, cela n'ouvre rien. Le référentiel "
        "porte plus de quatre cent mille noms et numéros de téléphone : "
        "l'accès se donne, il ne se prend pas. Qui approuve dépend du profil "
        "demandé, et personne ne peut approuver son propre rang.",
    )
    texte(d, 500, 62, "Le mot de passe n'est jamais transmis par courriel,",
          taille=7.5, couleur=GRIS)
    texte(d, 500, 50, "ni à l'inscription ni à la réinitialisation :",
          taille=7.5, couleur=GRIS)
    texte(d, 500, 38, "seul un lien à usage unique circule.",
          taille=7.5, couleur=GRIS)
    return d


def parcours_connexion() -> Drawing:
    """Les trois temps de la connexion, et les cinq atterrissages."""
    d = Drawing(LARGEUR_PAYSAGE, 310)

    etapes = [
        ("1", "Je choisis mon profil",
         "super utilisateur, administrateur, superviseur, agent de terrain"),
        ("2", "Je choisis mon agence",
         "recherche parmi les 181 agences du référentiel"),
        ("3", "Je saisis mes identifiants",
         "le superviseur note au passage les itinéraires annoncés"),
    ]
    boites = []
    for index, (numero, titre_etape, detail) in enumerate(etapes):
        b = _etape(d, 8 + index * 243, 240, 218, numero, titre_etape, detail,
                   hauteur=58)
        boites.append(b)
        if index:
            fleche(d, boites[index - 1].droite, b.centre_y, b.x, b.centre_y)

    controle = boite(
        d, 230, 144, 300, 66,
        "Le serveur confronte la déclaration au compte",
        sous_titre=(
            "mot de passe, puis profil déclaré = profil du compte, "
            "puis agence déclarée compatible avec le périmètre"
        ),
        fond=BLEU, couleur_texte=BLANC, bordure=BLEU_SOMBRE,
        taille=8.5, police=POLICE_GRAS,
    )
    fleche(d, boites[1].centre_x, boites[1].y, controle.centre_x, controle.haut)

    # Le refus est posé à gauche, à bonne distance : collé au cadre central,
    # son étiquette de flèche venait mordre dessus.
    refus = boite(
        d, 8, 151, 160, 52, "Session refusée",
        sous_titre="profil ou agence incohérents, mot de passe faux",
        fond=BLANC, bordure=ROUGE, couleur_texte=ROUGE, taille=8,
        police=POLICE_GRAS,
    )
    fleche(d, controle.x, 177, refus.droite, 177, pointillee=True, libelle="non")

    arrivees = [
        ("Tableau de bord", "super utilisateur", "national, tout le pays"),
        ("Tableau de bord", "administrateur", "national, données SOCADEL"),
        ("Écran d'affectation", "superviseur", "son agence, sa journée"),
        ("Bordereau déjà cadré", "superviseur", "s'il a noté des itinéraires"),
        ("Mon espace", "agent de terrain", "sa seule production"),
    ]
    largeur = 134
    ecart = (LARGEUR_PAYSAGE - 16 - 5 * largeur) / 4
    for index, (ecran, qui, portee) in enumerate(arrivees):
        x = 8 + index * (largeur + ecart)
        b = boite(
            d, x, 22, largeur, 56, ecran, sous_titre=portee,
            fond=BLEU_CLAIR, bordure=BLEU, taille=8, police=POLICE_GRAS,
        )
        fleche(d, controle.centre_x, controle.y, b.centre_x, b.haut + 10,
               couleur=GRIS_CLAIR)
        texte(d, b.centre_x, b.haut + 4, qui, taille=7,
              couleur=GRIS, police=POLICE_GRAS, ancrage="middle")

    return d

def parcours_superviseur() -> Drawing:
    """La journee du superviseur, du briefing au recoupement."""
    d = Drawing(LARGEUR_PAYSAGE, 300)

    largeur = 164
    colonnes = [8, 194, 380, 566]

    haut = [
        ("1", "Se connecter", "profil superviseur, son agence, itinéraires annoncés"),
        ("2", "Affecter les itinéraires", "l'agent se présente, les codes sont saisis"),
        ("3", "Imprimer le bordereau", "PDF filigrané, dans l'ordre de marche des maisons"),
    ]
    boites_haut = []
    for index, (numero, titre_etape, detail) in enumerate(haut):
        b = _etape(d, colonnes[index], 206, largeur, numero, titre_etape, detail, hauteur=62)
        boites_haut.append(b)
        if index:
            fleche(d, boites_haut[index - 1].droite, b.centre_y, b.x, b.centre_y)

    terrain = boite(
        d, colonnes[3], 206, largeur, 62, "4. L'agent collecte",
        sous_titre="hors application, bordereau papier en main",
        fond=GRIS_FOND, bordure=GRIS_CLAIR, couleur_texte=GRIS,
        taille=8, police=POLICE_GRAS,
    )
    fleche(d, boites_haut[2].droite, terrain.centre_y, terrain.x, terrain.centre_y,
           pointillee=True)

    bas = [
        ("5", "Saisir la production", "ligne par ligne, en lot, ou par import du fichier"),
        ("6", "Vérifier au référentiel", "un verdict par ligne : confirmé, infirmé, introuvable"),
        ("7", "Suivre et exporter", "KPI, courbes, CSV et PDF du périmètre affiché"),
        ("8", "Gérer ses agents", "arrivée, changement, départ d'un collecteur"),
    ]
    boites_bas = []
    for index, (numero, titre_etape, detail) in enumerate(bas):
        # La rangee du bas se lit de droite a gauche : le parcours serpente,
        # ce qui evite huit colonnes illisibles sur une seule ligne.
        x = colonnes[3 - index]
        b = _etape(d, x, 96, largeur, numero, titre_etape, detail, hauteur=62)
        boites_bas.append(b)
        if index:
            fleche(d, boites_bas[index - 1].x, b.centre_y, b.droite, b.centre_y)

    fleche(d, terrain.centre_x, terrain.y, boites_bas[0].centre_x, boites_bas[0].haut,
           pointillee=True, libelle="au retour")

    # Boucle du lendemain : elle repart de la gestion des agents vers
    # l'affectation, ce qui montre que le cycle est quotidien.
    fleche(d, boites_bas[3].centre_x, boites_bas[3].haut,
           boites_haut[1].centre_x, boites_haut[1].y,
           pointillee=True, libelle="le lendemain", couleur=BLEU)

    note(
        d, 8, 14, 420, 50,
        "Les étapes 5 à 8 ne s'enchaînent pas dans un ordre imposé : le "
        "superviseur y revient au fil de la journée. Seules les quatre "
        "premières sont séquentielles, parce qu'on n'imprime pas un bordereau "
        "avant d'avoir affecté les itinéraires.",
    )
    return d


def parcours_agent() -> Drawing:
    """Le parcours le plus court du systeme, et c'est voulu."""
    d = Drawing(LARGEUR_PAYSAGE, 186)

    largeur = 200
    a = _etape(d, 8, 108, largeur, "1", "Se connecter",
               "profil agent de terrain, son agence", hauteur=58)
    b = _etape(d, 268, 108, largeur, "2", "Cocher les abonnés",
               "un clic ; date, statut et responsable suivent", hauteur=58)
    c = _etape(d, 528, 108, 184, "3", "Consulter ses chiffres",
               "production, taux de confirmation, évolution", hauteur=58)
    fleche(d, a.droite, a.centre_y, b.x, b.centre_y)
    fleche(d, b.droite, b.centre_y, c.x, c.centre_y)

    ferme = boite(
        d, 268, 34, 444, 42, "Un seul geste, sur sa seule tournée",
        sous_titre="ni import, ni export de masse, ni accès aux lignes d'un autre agent",
        fond=GRIS_FOND, bordure=GRIS_CLAIR, couleur_texte=GRIS,
        taille=8, police=POLICE_GRAS,
    )
    fleche(d, b.centre_x, b.y, ferme.centre_x, ferme.haut, pointillee=True,
           couleur=GRIS_CLAIR)

    note(
        d, 8, 20, 244, 70,
        "Il travaille debout, un téléphone à une main : chaque champ qu'on lui "
        "demanderait serait un champ mal rempli. Il coche, la plateforme "
        "déduit le reste, et sa seule écriture ne porte que sur sa tournée.",
    )
    return d


def parcours_gouvernance() -> Drawing:
    """Administrateur et super utilisateur : un tronc commun, deux gestes de plus."""
    d = Drawing(LARGEUR_PAYSAGE, 268)

    largeur = 222
    colonnes = [8, 249, 490]

    haut = [
        ("1", "Se connecter",
         "profil administrateur ou super utilisateur, portée nationale"),
        ("2", "Examiner les demandes d'accès",
         "approuver ou refuser, avec un motif communiqué au demandeur"),
        ("3", "Attribuer un périmètre",
         "une agence ou une région à un superviseur"),
    ]
    boites_haut = []
    for index, (numero, titre_etape, detail) in enumerate(haut):
        b = _etape(d, colonnes[index], 176, largeur, numero, titre_etape, detail,
                   hauteur=62)
        boites_haut.append(b)
        if index:
            fleche(d, boites_haut[index - 1].droite, b.centre_y, b.x, b.centre_y)

    # La rangée du bas se lit de droite à gauche, comme la journée du
    # superviseur : le parcours serpente au lieu de s'étirer sur six colonnes.
    commun = _etape(
        d, colonnes[2], 74, largeur,
        "4", "Réinitialiser un mot de passe",
        "un provisoire est remis de vive voix, jamais par courriel",
        hauteur=62,
    )
    fleche(d, boites_haut[2].centre_x, boites_haut[2].y, commun.centre_x, commun.haut)

    reserves = [
        ("5", "Changer le rôle d'un compte",
         "y compris promouvoir un administrateur"),
        ("6", "Administrer le référentiel",
         "la source sur laquelle repose toute la vérification"),
    ]
    precedent = commun
    boites_reservees = []
    for index, (numero, titre_etape, detail) in enumerate(reserves):
        b = _etape(
            d, colonnes[1 - index], 74, largeur, numero, titre_etape, detail,
            hauteur=62, fond=BLEU, bordure=BLEU_SOMBRE, encre=BLANC,
        )
        fleche(d, precedent.x, b.centre_y, b.droite, b.centre_y)
        boites_reservees.append(b)
        precedent = b

    # Un trait sous les deux boîtes pleines vaut mieux qu'une étiquette posée
    # sur une flèche : il dit d'un coup jusqu'où va la réserve.
    gauche, droite = boites_reservees[1].x, boites_reservees[0].droite
    d.add(Line(gauche, 56, droite, 56, strokeColor=BLEU_SOMBRE, strokeWidth=1.2))
    d.add(Line(gauche, 56, gauche, 62, strokeColor=BLEU_SOMBRE, strokeWidth=1.2))
    d.add(Line(droite, 56, droite, 62, strokeColor=BLEU_SOMBRE, strokeWidth=1.2))
    texte(d, (gauche + droite) / 2, 38,
          "Réservé au super utilisateur NEXT LTD", taille=8,
          couleur=BLEU_SOMBRE, police=POLICE_GRAS, ancrage="middle")

    note(
        d, 490, 6, 222, 52,
        "L'administrateur SOCADEL exploite la plateforme, le super utilisateur "
        "NEXT LTD en répond. Aucun des deux ne peut agir sur son propre rang.",
    )
    return d