"""Diagrammes UML du dossier de conception.

Chaque fonction renvoie un `Drawing` prêt à être inséré dans le flux du
document. Les dimensions sont calées sur la largeur utile d'une page A4 en
portrait (environ 470 pt) ou en paysage (environ 720 pt).
"""

from __future__ import annotations

from reportlab.graphics.shapes import Drawing, Line, Rect

from .dessin import (
    BLANC,
    BLEU,
    BLEU_CLAIR,
    BLEU_SOMBRE,
    BLEU_TRES_CLAIR,
    GRIS,
    GRIS_CLAIR,
    GRIS_FOND,
    ORANGE,
    POLICE_GRAS,
    ROUGE,
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
    d = Drawing(LARGEUR, 300)

    centre = boite(
        d, 155, 130, 160, 52,
        "Bordereau SOCADEL",
        sous_titre="Back-office de pilotage",
        fond=BLEU, couleur_texte=BLANC, bordure=BLEU_SOMBRE,
        taille=9.5, police=POLICE_GRAS,
    )

    acteur(d, 45, 235, "Administrateur", role="NEXT LTD")
    acteur(d, 45, 150, "Superviseur", role="SOCADEL")
    acteur(d, 45, 55, "Agent de terrain", role="Distributeur")

    chatbot = boite(
        d, 355, 232, 105, 40, "ChatBot WhatsApp",
        sous_titre="NEXT LTD · Meta",
        fond=BLEU_TRES_CLAIR, taille=8,
    )
    mra = boite(
        d, 355, 140, 105, 40, "Plateforme MRA",
        sous_titre="SOCADEL · facturation",
        fond=BLEU_TRES_CLAIR, taille=8,
    )
    referentiel = boite(
        d, 355, 48, 105, 40, "Référentiel clients",
        sous_titre="Base de test aujourd'hui",
        fond=BLEU_TRES_CLAIR, taille=8,
    )

    for y_acteur, libelle in (
        (245, "gère comptes"),
        (160, "pilote"),
        (65, "consulte"),
    ):
        fleche(d, 62, y_acteur, 155, 160, libelle=libelle)

    fleche(d, centre.droite, 168, chatbot.x, 250, pointillee=True,
           libelle="hors périmètre")
    fleche(d, centre.droite, 158, mra.x, 158, pointillee=True,
           libelle="hors périmètre")
    fleche(d, centre.droite, 148, referentiel.x, 68,
           libelle="vérifie")

    fleche(d, chatbot.centre_x, chatbot.y, mra.centre_x, mra.haut,
           libelle="enrôlement")
    fleche(d, mra.centre_x, mra.y, referentiel.centre_x, referentiel.haut,
           libelle="alimente")

    note(
        d, 130, 20, 210, 44,
        "L'API de recoupement NEXT / MRA n'est pas encore ouverte : "
        "la vérification s'appuie aujourd'hui sur une base de test.",
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
        ("Consulter ses itinéraires confiés", 116),
        ("Consulter ses KPI et son évolution", 84),
        ("Consulter sa fiche", 52),
    ):
        b = cas_utilisation(d, 145, y, 280, 24, libelle)
        fleche(d, 58, 105, b.x, b.centre_y, pointe=False, couleur=GRIS_CLAIR)

    note(
        d, 145, 16, 280, 30,
        "Portée volontairement réduite : l'agent travaille sur papier. "
        "Il ne saisit rien, n'exporte rien, ne modifie rien.",
    )
    return d


def cas_administrateur() -> Drawing:
    d = Drawing(LARGEUR, 250)
    cadre_systeme(d, 110, 10, 350, 230, "Bordereau SOCADEL")
    acteur(d, 45, 115, "Administrateur")

    for libelle, y in (
        ("Créer / modifier / désactiver un compte", 188),
        ("Rattacher un compte agent à sa fiche", 156),
        ("Définir le périmètre d'un superviseur", 124),
        ("Accéder à toutes les données, sans limite", 92),
        ("Exercer tous les droits du superviseur", 60),
    ):
        b = cas_utilisation(d, 145, y, 280, 24, libelle)
        fleche(d, 58, 125, b.x, b.centre_y, pointe=False, couleur=GRIS_CLAIR)

    note(
        d, 145, 16, 280, 30,
        "Seul rôle non territorialisé. C'est aussi le seul qui puisse "
        "ouvrir un accès à la plateforme.",
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

    message(d, sup, api, 248, "PATCH /bordereau/{id} — statut ABONNE")
    message(d, api, dom, 230, "ligne.declarer(ABONNE, numéro)")
    message(d, dom, api, 212, "verdict remis à NON_VERIFIE", retour=True)
    message(d, api, bd, 194, "UPDATE de la ligne")

    trait = Line(40, 178, 660, 178, strokeColor=GRIS_CLAIR, strokeWidth=0.8)
    trait.strokeDashArray = [4, 3]
    d.add(trait)
    texte(d, 40, 182, "— plus tard : le contrôle —", taille=6.5, couleur=GRIS)

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
    texte(d, 40, 132, "— rien n'est encore écrit —", taille=6.5, couleur=GRIS)

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
        ("interfaces/ — routes HTTP, schémas Pydantic", 240, BLEU_TRES_CLAIR, BLEU),
        ("application/ — cas d'usage, ports, DTO", 180, BLEU_CLAIR, BLEU),
        ("domain/ — entités, objets-valeurs, règles", 120, BLEU, BLEU_SOMBRE),
    ]
    for libelle, y, fond, bordure in couches:
        blanc = fond == BLEU
        boite(d, 90, y, 290, 46, libelle,
              fond=fond, bordure=bordure,
              couleur_texte=BLANC if blanc else None or BLEU_SOMBRE,
              taille=8.5, police=POLICE_GRAS)

    boite(d, 90, 40, 290, 46,
          "infrastructure/ — PostgreSQL, bcrypt, JWT, openpyxl, reportlab",
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
                 "RBAC — exiger(permission)",
                 sous_titre="Le rôle porte-t-il ce droit ? Réponse booléenne.",
                 fond=BLANC, bordure=BLEU, taille=8.5, police=POLICE_GRAS)
    abac = boite(d, 250, 110, 180, 62,
                 "ABAC — restreindre(filtre)",
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
