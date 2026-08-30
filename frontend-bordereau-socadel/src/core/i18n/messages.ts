/**
 * Dictionnaires de traduction.
 *
 * Le français est la langue de référence : c'est celle du métier SOCADEL et
 * celle dans laquelle les libellés sont pensés. L'anglais en est la traduction.
 *
 * Le type `Cle` est dérivé du dictionnaire français : oublier une clé en
 * anglais devient une erreur de compilation, pas une chaîne manquante
 * découverte en production.
 */

export const LANGUES = ["fr", "en"] as const;
export type Langue = (typeof LANGUES)[number];

export const NOMS_LANGUES: Record<Langue, string> = {
  fr: "Français",
  en: "English",
};

const fr = {
  // --- Général -------------------------------------------------------------
  "app.nom": "Bordereau SOCADEL",
  "app.marque": "SOCADEL × NEXT",
  "app.editeur": "Une solution NEXT LTD",
  "app.editeurComplet": "NEXT LTD — Numeric Export Technologies",
  "app.societe": "Société Camerounaise d'Electricité",

  "commun.chargement": "Chargement…",
  "commun.chargementSession": "Chargement de la session…",
  "commun.annuler": "Annuler",
  "commun.enregistrer": "Enregistrer",
  "commun.modifier": "Modifier",
  "commun.supprimer": "Supprimer",
  "commun.fermer": "Fermer",
  "commun.rechercher": "Rechercher",
  "commun.reinitialiser": "Réinitialiser",
  "commun.precedent": "Précédent",
  "commun.suivant": "Suivant",
  "commun.parPage": "{n} / page",
  "commun.aucunResultat": "Aucun résultat",
  "commun.oui": "Oui",
  "commun.non": "Non",
  "commun.du": "Du",
  "commun.au": "Au",
  "commun.erreurGenerique": "Une erreur est survenue.",
  "commun.actif": "Actif",
  "commun.inactif": "Désactivé",

  // --- Navigation ----------------------------------------------------------
  "nav.affectations": "Affectations",
  "nav.affectations.aide": "Confier les itinéraires du jour",
  "nav.dashboard": "Tableau de bord",
  "nav.dashboard.aide": "KPI et évolution",
  "nav.bordereau": "Bordereau",
  "nav.bordereau.aide": "Saisir la production des agents",
  "nav.itineraires": "Itinéraires",
  "nav.itineraires.aide": "Rechercher et imprimer",
  "nav.agents": "Agents",
  "nav.agents.aide": "Répertoire des collecteurs",
  "nav.imports": "Import / Export",
  "nav.imports.aide": "Fichiers et modèles",
  "nav.comptes": "Comptes",
  "nav.comptes.aide": "Accès à la plateforme",
  "nav.monEspace": "Mon espace",
  "nav.monEspace.aide": "Mes itinéraires et mes chiffres",
  "nav.replier": "Replier le menu",
  "nav.deplier": "Déplier le menu",
  "nav.ouvrirMenu": "Ouvrir le menu",
  "nav.sessionActive": "Session active",
  "nav.deconnexion": "Déconnexion",

  // --- Rôles ---------------------------------------------------------------
  "role.SUPER_UTILISATEUR": "Super utilisateur",
  "role.ADMINISTRATEUR": "Administrateur",
  "role.SUPERVISEUR": "Superviseur",
  "role.AGENT_TERRAIN": "Agent de terrain",

  // --- Connexion -----------------------------------------------------------
  "login.titre": "Bordereau intelligent de collecte WhatsApp",
  "login.sousTitre":
    "Suivez le travail des agents de terrain, itinéraire par itinéraire, et confrontez chaque déclaration au référentiel SOCADEL.",
  "login.formulaireTitre": "Connexion",
  "login.formulaireSousTitre":
    "Identifiez-vous pour accéder au bordereau de collecte.",
  "login.identifiant": "Identifiant",
  "login.motDePasse": "Mot de passe",
  "login.seConnecter": "Se connecter",
  "login.connexionEnCours": "Connexion…",
  "login.echec":
    "Connexion impossible. Vérifiez que le serveur est démarré.",
  "login.mentionAcces": "Accès réservé aux utilisateurs autorisés SOCADEL.",
  "login.mentionContact":
    "En cas de difficulté, contactez l'administrateur NEXT LTD.",
  "login.etape1.titre": "Affecter les itinéraires",
  "login.etape1.texte":
    "L'agent se présente, vous notez les itinéraires que vous lui confiez et imprimez son bordereau de terrain.",
  "login.etape2.titre": "Saisir la production",
  "login.etape2.texte":
    "Au retour, vous reportez ce que l'agent a réalisé : abonnements obtenus, absents, refus.",
  "login.etape3.titre": "Vérifier et payer",
  "login.etape3.texte":
    "Le référentiel SOCADEL confirme les abonnements réellement enregistrés : c'est lui qui fait foi.",

  "login.creerCompte": "Demander un accès",
  "login.motDePasseOublie": "Mot de passe oublié ?",
  // --- Connexion, choix du poste de travail --------------------------------
  "poste.etape": "Étape {n} sur 3",
  "poste.retour": "Retour",
  "poste.continuer": "Continuer",

  "poste.profil.titre": "Qui êtes-vous ?",
  "poste.profil.aide":
    "Choisissez le profil sous lequel vous travaillez. Il est vérifié à la connexion : si votre compte est enregistré autrement, l'accès est refusé.",
  "poste.profil.SUPER_UTILISATEUR": "exploite et répond de la plateforme",
  "poste.profil.ADMINISTRATEUR": "gouverne les accès et les périmètres",
  "poste.profil.SUPERVISEUR": "pilote les agents d'une agence",
  "poste.profil.AGENT_TERRAIN": "consulte sa production",

  "poste.agence.titre": "Où travaillez-vous aujourd'hui ?",
  "poste.agence.aide":
    "Votre agence cadre l'écran d'accueil. Elle ne donne aucun droit supplémentaire : votre périmètre reste celui de votre compte.",
  "poste.agence.recherche": "Rechercher une agence",
  "poste.agence.placeholder": "Tapez les premières lettres, par exemple ESSOS",
  "poste.agence.nationale": "Portée nationale, toutes les agences",
  "poste.agence.aucune": "Aucune agence ne correspond",
  "poste.agence.chargement": "Chargement de l'annuaire…",
  "poste.agence.indisponible":
    "Annuaire indisponible. Vous pouvez continuer sans choisir d'agence.",
  "poste.agence.nombre": "{n} agences",

  "poste.identifiants.titre": "Vos identifiants",
  "poste.itineraires.libelle": "Itinéraires annoncés par l'agent",
  "poste.itineraires.aide":
    "Facultatif. Saisissez les codes que l'agent vous donne de mémoire, séparés par un espace ou une virgule : vous arriverez directement sur son bordereau.",
  "poste.itineraires.placeholder": "42422 42423",
  "poste.itineraires.compte": "{n} itinéraire(s) retenu(s)",
  "poste.itineraires.invalide": "Un code d'itinéraire est un nombre.",

  "poste.recapitulatif": "{profil}, {agence}",
  "poste.changer": "Changer",


  // --- Cycle de vie des comptes --------------------------------------------
  "statutCompte.EN_ATTENTE_VERIFICATION": "Adresse à confirmer",
  "statutCompte.EN_ATTENTE_APPROBATION": "En attente d'approbation",
  "statutCompte.ACTIF": "Actif",
  "statutCompte.SUSPENDU": "Suspendu",
  "statutCompte.REFUSE": "Refusé",

  "inscription.titre": "Demander un accès",
  "inscription.chapeau":
    "S'inscrire dépose une demande, cela n'ouvre rien. La plateforme porte le référentiel clients de SOCADEL : un responsable examinera votre demande et vous attribuera vos droits.",
  "inscription.nomComplet": "Nom complet",
  "inscription.identifiant": "Identifiant",
  "inscription.identifiantAide": "Celui que vous saisirez à la connexion.",
  "inscription.email": "Adresse électronique",
  "inscription.telephone": "Téléphone",
  "inscription.roleSouhaite": "Profil souhaité",
  "inscription.roleAide":
    "Souhaité, pas acquis : c'est le responsable qui attribue le profil définitif.",
  "inscription.motDePasse": "Mot de passe",
  "inscription.confirmation": "Confirmer le mot de passe",
  "inscription.discordance": "Les deux saisies diffèrent.",
  "inscription.envoyer": "Déposer ma demande",
  "inscription.echec": "La demande n'a pas pu être enregistrée.",
  "inscription.deposeeTitre": "Demande enregistrée",
  "inscription.deposeeSuite":
    "En développement, aucun serveur de messagerie n'est configuré : les courriels sont écrits dans backend-bordereau-socadel/courriels/, un fichier .html et un fichier .txt par message.",
  "inscription.retourConnexion": "Revenir à la connexion",
  "inscription.dejaInscrit": "Vous avez déjà un compte ?",

  "adresse.titre": "Confirmation de votre adresse",
  "adresse.enCours": "Vérification du lien…",
  "adresse.jetonAbsent":
    "Ce lien est incomplet. Ouvrez celui reçu par courriel, sans le modifier.",
  "adresse.echec":
    "Ce lien est expiré ou a déjà servi. Déposez une nouvelle demande.",

  "oubli.titre": "Mot de passe oublié",
  "oubli.chapeau":
    "Indiquez l'adresse de votre compte. Un lien valable deux heures vous sera envoyé.",
  "oubli.envoyer": "Envoyer le lien",
  "oubli.confirmationNeutre":
    "Si un compte actif correspond à cette adresse, un lien de réinitialisation vient d'être envoyé.",

  "reinitialisation.titre": "Choisir un nouveau mot de passe",
  "reinitialisation.chapeau":
    "Ce lien ne fonctionne qu'une fois. Choisissez un mot de passe que vous n'utilisez nulle part ailleurs.",
  "reinitialisation.nouveau": "Nouveau mot de passe",
  "reinitialisation.envoyer": "Enregistrer",
  "reinitialisation.echec":
    "Le lien est expiré ou a déjà servi. Demandez-en un nouveau.",
  "reinitialisation.faitTitre": "Mot de passe enregistré",
  "reinitialisation.faitTexte":
    "Vous pouvez vous connecter avec votre nouveau mot de passe.",

  "comptes.titre": "Comptes et accès",
  "comptes.sousTitre":
    "Approuver les demandes, attribuer les périmètres, débloquer un mot de passe.",
  "comptes.filtrer": "Filtrer par statut",
  "comptes.tous": "Tous les statuts",
  "comptes.videTitre": "Aucun compte dans ce statut",
  "comptes.videTexte":
    "Changez de filtre, ou attendez qu'une demande d'accès soit déposée.",
  "comptes.examiner": "Examiner",
  "comptes.approuver": "Approuver",
  "comptes.refuser": "Refuser",
  "comptes.suspendre": "Suspendre",
  "comptes.reactiver": "Réactiver",
  "comptes.reinitialiser": "Réinitialiser le mot de passe",
  "comptes.horsPortee": "Hors de votre portée",
  "comptes.roleAttribue": "Profil attribué",
  "comptes.agentRattache": "Agent de terrain rattaché",
  "comptes.choisirAgent": "Choisir un agent",
  "comptes.agence": "Agence",
  "comptes.region": "Région",
  "comptes.motifRefus": "Motif, en cas de refus",
  "comptes.motifAide": "Il figurera dans le courriel adressé au demandeur.",
  "comptes.perimetreManquant":
    "Sans agence ni région, ce superviseur verrait la production des 181 agences. La plateforme refusera ses requêtes tant qu'un périmètre ne lui est pas attribué.",
  "comptes.approuve": "Accès ouvert pour {nom}.",
  "comptes.refuse": "Demande de {nom} refusée.",
  "comptes.suspendu": "Compte de {nom} suspendu.",
  "comptes.reactive": "Compte de {nom} réactivé.",
  "comptes.provisoire":
    "Mot de passe provisoire de {nom} : {motDePasse}. Communiquez-le de vive voix, il devra être remplacé à la prochaine connexion.",
  "comptes.echec": "L'opération a échoué.",

  // --- Affectations --------------------------------------------------------
  "affectation.titre": "Affectation des itinéraires",
  "affectation.sousTitre":
    "L'agent se présente : notez les itinéraires que vous lui confiez, puis imprimez son bordereau de terrain.",
  "affectation.agentEtJournee": "Agent et journée",
  "affectation.agent": "Agent de terrain",
  "affectation.choisirAgent": "Sélectionner un agent",
  "affectation.aucunAgentActif":
    "Aucun agent actif n'est enregistré. Créez-en un depuis l'écran « Agents » avant d'affecter un itinéraire.",
  "affectation.journee": "Journée de travail",
  "affectation.consignes": "Consignes (facultatif)",
  "affectation.consignesExemple": "Quartier prioritaire, point de rendez-vous…",
  "affectation.itinerairesConfies": "Itinéraires confiés",
  "affectation.rechercheAide": "Recherchez par code, agence ou libellé.",
  "affectation.recherchePlaceholder":
    "Code de l'itinéraire, ex. 131227 — ou nom d'agence",
  "affectation.aucunSelectionne": "Aucun itinéraire sélectionné",
  "affectation.aucunSelectionneAide":
    "Recherchez un itinéraire ci-dessus pour le confier à l'agent.",
  "affectation.valider": "Affecter et générer le bordereau",
  "affectation.validerAide":
    "Une ligne de bordereau sera créée pour chaque client des itinéraires retenus.",
  "affectation.enregistree": "Affectation enregistrée",
  "affectation.imprimer": "Imprimer le bordereau",
  "affectation.retirer": "Retirer",
  "affectation.clients": "{n} client(s)",
  "affectation.resume": "{i} itinéraire(s) · {c} client(s) à démarcher",
  "affectation.dejaPortes": "Itinéraires déjà portés par cet agent",
  "affectation.dejaPortesAide":
    "Un bon collecteur en reçoit plusieurs : ajoutez-en autant que nécessaire, ses données se mettront à jour.",

  // --- Bordereau -----------------------------------------------------------
  "bordereau.titre": "Bordereau de collecte",
  "bordereau.sousTitre":
    "Reportez ici ce que chaque agent a réalisé sur le terrain.",
  "bordereau.cadreSurItineraires":
    "Bordereau cadré sur les itinéraires {codes}, annoncés à la connexion.",
  "bordereau.toutAfficher": "Tout afficher",
  "bordereau.verifier": "Vérifier auprès du référentiel",
  "bordereau.exporterCsv": "Exporter CSV",
  "bordereau.exporterPdf": "Exporter PDF",
  "bordereau.client": "Client",
  "bordereau.refGeo": "Réf. géo",
  "bordereau.itineraire": "Itin.",
  "bordereau.compteur": "Compteur",
  "bordereau.numeroCollecte": "N° collecté",
  "bordereau.statut": "Statut",
  "bordereau.verification": "Vérification",
  "bordereau.date": "Date",
  "bordereau.action": "Action",
  "bordereau.saisir": "Saisir",
  "bordereau.vide": "Aucune ligne à afficher",
  "bordereau.videAide":
    "Affinez vos filtres, ou affectez un itinéraire à un agent pour générer son bordereau.",
  "bordereau.selection": "{n} ligne(s) sélectionnée(s)",
  "bordereau.appliquer": "Appliquer",
  "bordereau.annulerSelection": "Annuler la sélection",
  "bordereau.rechercheePlaceholder":
    "Nom, contrat, compteur ou référence géographique…",
  "bordereau.total": "{premier}–{dernier} sur {total} ligne(s)",

  // --- Saisie --------------------------------------------------------------
  "saisie.titre": "Saisir le passage de l'agent",
  "saisie.resultat": "Résultat du passage",
  "saisie.numero": "Numéro WhatsApp relevé",
  "saisie.numeroObligatoire": "Numéro WhatsApp relevé (obligatoire)",
  "saisie.numeroAide": "Le numéro sera normalisé au format international.",
  "saisie.numeroManquant":
    "Un client déclaré abonné doit être accompagné du numéro collecté.",
  "saisie.origine": "Origine de l'abonnement",
  "saisie.observation": "Observation",
  "saisie.observationExemple":
    "Remarque de l'agent, précision sur la visite…",
  "saisie.echec": "L'enregistrement a échoué.",

  // --- Tableau de bord -----------------------------------------------------
  "dashboard.titre": "Tableau de bord",
  "dashboard.sousTitre": "L'avancement de la campagne de collecte WhatsApp.",
  "dashboard.periode": "Période observée",
  "dashboard.jours7": "7 jours",
  "dashboard.jours14": "14 jours",
  "dashboard.jours30": "30 jours",
  "dashboard.mois3": "3 mois",
  "dashboard.chargement": "Chargement des indicateurs…",
  "dashboard.vsPrecedent": "vs période précédente",
  "dashboard.stable": "stable",
  "dashboard.pasDeComparaison": "Pas de comparaison possible",

  "kpi.lignes_traitees": "Clients démarchés",
  "kpi.abonnements": "Abonnements déclarés",
  "kpi.abonnements_confirmes": "Abonnements confirmés",
  "kpi.taux_conversion": "Taux de conversion",
  "kpi.taux_fiabilite": "Fiabilité des déclarations",

  "graphique.evolution.titre": "Évolution de la collecte",
  "graphique.evolution.sousTitre":
    "Ce que les agents ont démarché, déclaré, et ce que le référentiel confirme.",
  "graphique.voirDonnees": "Voir les données",
  "graphique.voirGraphique": "Voir le graphique",
  "graphique.jour": "Jour",
  "serie.collectes": "Clients démarchés",
  "serie.abonnements": "Abonnements déclarés",
  "serie.confirmes": "Abonnements confirmés",

  "repartition.titre": "Répartition par statut",
  "repartition.sousTitre": "{n} ligne(s) sur la période",
  "repartition.vide": "Aucune donnée sur la période",
  "repartition.videAide":
    "Élargissez la période ou saisissez la production des agents.",

  "couverture.titre": "Couverture des itinéraires",
  "couverture.sousTitre":
    "Part des clients déjà démarchés sur chaque tournée.",
  "couverture.vide": "Aucun itinéraire travaillé",
  "couverture.videAide":
    "Affectez un itinéraire à un agent pour suivre sa couverture ici.",
  "couverture.restants": "{n} client(s) restant(s)",
  "couverture.termine": "itinéraire terminé",
  "couverture.abonnements": "{n} abonnement(s)",

  "classement.titre": "Performance des agents",
  "classement.sousTitre":
    "Base de l'entretien de suivi : volume, conversion et fiabilité.",
  "classement.agent": "Agent",
  "classement.demarches": "Démarchés",
  "classement.abonnements": "Abonnements",
  "classement.confirmes": "Confirmés",
  "classement.conversion": "Conversion",
  "classement.fiabilite": "Fiabilité",
  "classement.vide": "Aucune production sur la période",
  "classement.videAide":
    "Les chiffres apparaîtront dès la première saisie de bordereau.",
  "classement.fiabiliteFaible":
    "Une part importante des abonnements déclarés n'est pas confirmée par le référentiel.",

  // --- Agents --------------------------------------------------------------
  "agents.titre": "Agents de terrain",
  "agents.sousTitre": "Les collecteurs à qui vous confiez des itinéraires.",
  "agents.enregistrer": "Enregistrer un agent",
  "agents.repertoire": "Répertoire",
  "agents.nombre": "{n} agent(s) enregistré(s)",
  "agents.matricule": "Matricule",
  "agents.nomComplet": "Nom complet",
  "agents.telephone": "Téléphone",
  "agents.zone": "Zone de rattachement",
  "agents.region": "Région",
  "agents.photo": "Photo de profil",
  "agents.photoAide": "JPEG, PNG ou WebP — 4 Mo maximum.",
  "agents.desactiver": "Retirer du service",
  "agents.reactiver": "Remettre en service",
  "agents.vide": "Aucun agent enregistré",
  "agents.videAide":
    "Créez un premier agent pour pouvoir lui affecter des itinéraires.",
  "agents.mentionHistorique":
    "Un agent n'est jamais supprimé : ses bordereaux passés servent de base à sa rémunération.",
  "agents.voirPortefeuille": "Voir le portefeuille",

  // --- Portefeuille / espace agent ----------------------------------------
  "portefeuille.titre": "Mon espace",
  "portefeuille.titreAutre": "Portefeuille de {nom}",
  "portefeuille.sousTitre":
    "Vos itinéraires et vos chiffres sur la période.",
  "portefeuille.itineraires": "Itinéraires confiés",
  "portefeuille.aucun": "Aucun itinéraire sur la période",
  "portefeuille.aucunAide":
    "Votre superviseur vous en confiera lors du prochain briefing.",
  "portefeuille.traites": "Démarchés",
  "portefeuille.affectes": "Clients confiés",
  "portefeuille.enAttente": "En attente de vérification",
  "portefeuille.mentionSaisie":
    "Vos chiffres sont saisis par votre superviseur d'après le bordereau papier, puis confrontés au référentiel SOCADEL.",

  // --- Import / export -----------------------------------------------------
  "import.titre": "Import et export",
  "import.sousTitre":
    "Distribuez le modèle aux agents, puis importez leurs bordereaux remplis.",
  "import.modeleTitre": "Modèle de bordereau terrain",
  "import.modeleSousTitre": "Le classeur vierge que les agents remplissent.",
  "import.modeleTexte":
    "Ses en-têtes sont exactement ceux que l'import sait relire, et les colonnes Statut et Responsable proposent des listes fermées : un fichier issu de ce modèle ne sera jamais refusé pour cause de colonnes inattendues.",
  "import.telechargerModele": "Télécharger le modèle (.xlsx)",
  "import.deposerTitre": "Importer un bordereau rempli",
  "import.deposerSousTitre":
    "Un aperçu vous sera présenté avant tout enregistrement.",
  "import.journee": "Journée de collecte",
  "import.journeeAide": "Date à laquelle les visites ont eu lieu.",
  "import.agentFacultatif": "Agent concerné (facultatif)",
  "import.nonPrecise": "Non précisé",
  "import.fichier": "Fichier du bordereau",
  "import.formats":
    "Formats acceptés : Excel (.xlsx, .xls) et CSV. 25 Mo maximum.",
  "import.analyse": "Analyse en cours…",
  "import.apercuTitre": "Vérifier avant d'importer",
  "import.lignesLues": "Lignes lues",
  "import.lignesRetenues": "Lignes retenues",
  "import.lignesRejetees": "Lignes rejetées",
  "import.importer": "Importer {n} ligne(s)",
  "import.apercuLignes": "Aperçu des {n} première(s) ligne(s)",
  "import.controle": "Contrôle",
  "import.ok": "OK",
  "import.rejet": "Rejet",
  "import.avertissement": "Avertissement",
  "import.colonnesDetectees": "Colonnes détectées : {liste}",
  "import.colonnesManquantes":
    "Colonne(s) obligatoire(s) absente(s) : {liste}. Repartez du modèle de bordereau pour être sûr des en-têtes attendus.",
  "import.aucuneLigne":
    "Aucune ligne exploitable dans ce fichier : l'import est impossible en l'état.",
  "import.rejetsAvertis":
    "{n} ligne(s) seront ignorées. Les autres seront importées normalement.",
  "import.termine": "Import terminé : {creees} ligne(s) enregistrée(s)",
  "import.ignorees": ", {n} ignorée(s)",
  "import.voirAnomalies": "Voir les {n} anomalie(s)",
  "import.echec": "L'import a échoué.",
  "import.echecAnalyse": "Le fichier n'a pas pu être analysé.",
  "export.tronque":
    "L'export a atteint le plafond de lignes. Affinez vos filtres pour obtenir un fichier complet.",
  "export.echec": "L'export a échoué.",

  // --- Itinéraires ---------------------------------------------------------
  "itineraires.titre": "Itinéraires",
  "itineraires.sousTitre":
    "Retrouvez un itinéraire et imprimez son bordereau de relevé.",
  "itineraires.recherchePlaceholder":
    "Code de l'itinéraire, agence ou libellé — au moins 2 caractères",
  "itineraires.invite": "Recherchez un itinéraire",
  "itineraires.inviteAide":
    "Saisissez son code — par exemple 131227 — ou le nom de son agence.",
  "itineraires.bordereauPdf": "Bordereau terrain (PDF)",
  "itineraires.territoireInconnu": "Territoire non renseigné",
  "itineraires.echecPdf": "Le bordereau n'a pas pu être généré.",

  // --- Vérification --------------------------------------------------------
  "verification.resultat":
    "{examinees} ligne(s) vérifiée(s) : {confirmees} confirmée(s), {infirmees} infirmée(s), {introuvables} introuvable(s) au référentiel.",
  "verification.echec": "La vérification a échoué.",
  "lot.resultat": "{n} ligne(s) mise(s) à jour.",
  "lot.resultatPartiel":
    "{modifiees} ligne(s) mise(s) à jour. {ignorees} ligne(s) demandent une saisie individuelle (un abonnement exige le numéro collecté).",
  "lot.echec": "La mise à jour groupée a échoué.",

  // --- Statuts -------------------------------------------------------------
  "statut.A_TRAITER": "À traiter",
  "statut.A_TRAITER.aide": "L'agent n'est pas encore passé chez ce client",
  "statut.ABONNE": "Abonné",
  "statut.ABONNE.aide":
    "Le client s'est abonné à la réception de facture par WhatsApp",
  "statut.NON_ABONNE": "Non abonné",
  "statut.NON_ABONNE.aide": "Client rencontré, mais pas d'abonnement obtenu",
  "statut.INJOIGNABLE": "Injoignable",
  "statut.INJOIGNABLE.aide": "Numéro ou domicile inaccessible",
  "statut.ABSENT": "Absent",
  "statut.ABSENT.aide": "Personne au domicile lors du passage",
  "statut.REFUS": "Refus",
  "statut.REFUS.aide": "Le client a refusé de communiquer son numéro",
  "statut.DOUBLON": "Doublon",
  "statut.DOUBLON.aide": "Client déjà traité sur un autre itinéraire",

  "verdict.NON_VERIFIE": "Non vérifié",
  "verdict.NON_VERIFIE.aide":
    "Déclaration pas encore confrontée au référentiel SOCADEL",
  "verdict.CONFIRME": "Confirmé",
  "verdict.CONFIRME.aide":
    "Le référentiel corrobore la déclaration : la ligne est payable",
  "verdict.INFIRME": "Infirmé",
  "verdict.INFIRME.aide": "Le référentiel contredit la déclaration",
  "verdict.INTROUVABLE": "Introuvable",
  "verdict.INTROUVABLE.aide":
    "Ce contrat ne figure pas au référentiel SOCADEL",

  "responsable.TERRAIN": "Agent de terrain",
  "responsable.CHATBOT": "Chatbot WhatsApp",
  "responsable.CSC": "Centre de service client",
  "responsable.AUTRES": "Autre canal",

  // --- Thème et langue -----------------------------------------------------
  "theme.clair": "Clair",
  "theme.sombre": "Sombre",
  "theme.systeme": "Système",
  "theme.basculer": "Changer de thème",
  "langue.basculer": "Changer de langue",
} as const;

export type Cle = keyof typeof fr;

const en: Record<Cle, string> = {
  "app.nom": "SOCADEL Collection Sheet",
  "app.marque": "SOCADEL × NEXT",
  "app.editeur": "A NEXT LTD solution",
  "app.editeurComplet": "NEXT LTD — Numeric Export Technologies",
  "app.societe": "Cameroon Electricity Company",

  "commun.chargement": "Loading…",
  "commun.chargementSession": "Loading session…",
  "commun.annuler": "Cancel",
  "commun.enregistrer": "Save",
  "commun.modifier": "Edit",
  "commun.supprimer": "Delete",
  "commun.fermer": "Close",
  "commun.rechercher": "Search",
  "commun.reinitialiser": "Reset",
  "commun.precedent": "Previous",
  "commun.suivant": "Next",
  "commun.parPage": "{n} / page",
  "commun.aucunResultat": "No results",
  "commun.oui": "Yes",
  "commun.non": "No",
  "commun.du": "From",
  "commun.au": "To",
  "commun.erreurGenerique": "Something went wrong.",
  "commun.actif": "Active",
  "commun.inactif": "Deactivated",

  "nav.affectations": "Assignments",
  "nav.affectations.aide": "Hand out today's routes",
  "nav.dashboard": "Dashboard",
  "nav.dashboard.aide": "KPIs and trends",
  "nav.bordereau": "Collection sheet",
  "nav.bordereau.aide": "Record what agents achieved",
  "nav.itineraires": "Routes",
  "nav.itineraires.aide": "Search and print",
  "nav.agents": "Agents",
  "nav.agents.aide": "Field collector directory",
  "nav.imports": "Import / Export",
  "nav.imports.aide": "Files and templates",
  "nav.comptes": "Accounts",
  "nav.comptes.aide": "Platform access",
  "nav.monEspace": "My space",
  "nav.monEspace.aide": "My routes and figures",
  "nav.replier": "Collapse menu",
  "nav.deplier": "Expand menu",
  "nav.ouvrirMenu": "Open menu",
  "nav.sessionActive": "Active session",
  "nav.deconnexion": "Sign out",

  "role.SUPER_UTILISATEUR": "Super user",
  "role.ADMINISTRATEUR": "Administrator",
  "role.SUPERVISEUR": "Supervisor",
  "role.AGENT_TERRAIN": "Field agent",

  "login.titre": "Smart WhatsApp number collection sheet",
  "login.sousTitre":
    "Track your field agents route by route, and check every declaration against the SOCADEL reference data.",
  "login.formulaireTitre": "Sign in",
  "login.formulaireSousTitre": "Sign in to access the collection sheet.",
  "login.identifiant": "Username",
  "login.motDePasse": "Password",
  "login.seConnecter": "Sign in",
  "login.connexionEnCours": "Signing in…",
  "login.echec": "Sign-in failed. Check that the server is running.",
  "login.mentionAcces": "Restricted to authorised SOCADEL users.",
  "login.mentionContact": "If you have trouble, contact the NEXT LTD administrator.",
  "login.etape1.titre": "Assign routes",
  "login.etape1.texte":
    "The agent reports in, you record the routes you hand over and print their field sheet.",
  "login.etape2.titre": "Record the work",
  "login.etape2.texte":
    "On their return, you enter what the agent achieved: sign-ups, absentees, refusals.",
  "login.etape3.titre": "Verify and pay",
  "login.etape3.texte":
    "The SOCADEL reference data confirms which sign-ups were actually recorded, it is the one that counts.",

  "login.creerCompte": "Request access",
  "login.motDePasseOublie": "Forgotten password?",
  "poste.etape": "Step {n} of 3",
  "poste.retour": "Back",
  "poste.continuer": "Continue",

  "poste.profil.titre": "Who are you?",
  "poste.profil.aide":
    "Pick the profile you work under. It is checked at sign-in: if your account is registered otherwise, access is refused.",
  "poste.profil.SUPER_UTILISATEUR": "runs and answers for the platform",
  "poste.profil.ADMINISTRATEUR": "governs access and scopes",
  "poste.profil.SUPERVISEUR": "runs the agents of one branch",
  "poste.profil.AGENT_TERRAIN": "looks up their own output",

  "poste.agence.titre": "Where are you working today?",
  "poste.agence.aide":
    "Your branch frames the landing screen. It grants nothing extra: your scope stays the one on your account.",
  "poste.agence.recherche": "Search for a branch",
  "poste.agence.placeholder": "Type the first letters, for instance ESSOS",
  "poste.agence.nationale": "National scope, every branch",
  "poste.agence.aucune": "No branch matches",
  "poste.agence.chargement": "Loading the directory…",
  "poste.agence.indisponible":
    "Directory unavailable. You can continue without picking a branch.",
  "poste.agence.nombre": "{n} branches",

  "poste.identifiants.titre": "Your credentials",
  "poste.itineraires.libelle": "Routes the agent announced",
  "poste.itineraires.aide":
    "Optional. Type the codes the agent gives you from memory, separated by a space or a comma: you will land straight on their sheet.",
  "poste.itineraires.placeholder": "42422 42423",
  "poste.itineraires.compte": "{n} route(s) kept",
  "poste.itineraires.invalide": "A route code is a number.",

  "poste.recapitulatif": "{profil}, {agence}",
  "poste.changer": "Change",


  "statutCompte.EN_ATTENTE_VERIFICATION": "Address to confirm",
  "statutCompte.EN_ATTENTE_APPROBATION": "Awaiting approval",
  "statutCompte.ACTIF": "Active",
  "statutCompte.SUSPENDU": "Suspended",
  "statutCompte.REFUSE": "Refused",

  "inscription.titre": "Request access",
  "inscription.chapeau":
    "Signing up files a request, it opens nothing. The platform holds SOCADEL customer reference data: a manager will review your request and grant your rights.",
  "inscription.nomComplet": "Full name",
  "inscription.identifiant": "Username",
  "inscription.identifiantAide": "The one you will type at sign-in.",
  "inscription.email": "Email address",
  "inscription.telephone": "Phone",
  "inscription.roleSouhaite": "Requested profile",
  "inscription.roleAide":
    "Requested, not granted: the manager assigns the final profile.",
  "inscription.motDePasse": "Password",
  "inscription.confirmation": "Confirm password",
  "inscription.discordance": "The two entries differ.",
  "inscription.envoyer": "File my request",
  "inscription.echec": "The request could not be recorded.",
  "inscription.deposeeTitre": "Request recorded",
  "inscription.deposeeSuite":
    "In development no mail server is configured: emails are written to backend-bordereau-socadel/courriels/, one .html and one .txt file per message.",
  "inscription.retourConnexion": "Back to sign-in",
  "inscription.dejaInscrit": "Already have an account?",

  "adresse.titre": "Confirming your address",
  "adresse.enCours": "Checking the link…",
  "adresse.jetonAbsent":
    "This link is incomplete. Open the one you received by email, unchanged.",
  "adresse.echec":
    "This link has expired or was already used. File a new request.",

  "oubli.titre": "Forgotten password",
  "oubli.chapeau":
    "Enter your account address. A link valid for two hours will be sent to you.",
  "oubli.envoyer": "Send the link",
  "oubli.confirmationNeutre":
    "If an active account matches this address, a reset link has just been sent.",

  "reinitialisation.titre": "Choose a new password",
  "reinitialisation.chapeau":
    "This link works only once. Choose a password you use nowhere else.",
  "reinitialisation.nouveau": "New password",
  "reinitialisation.envoyer": "Save",
  "reinitialisation.echec":
    "The link has expired or was already used. Request a new one.",
  "reinitialisation.faitTitre": "Password saved",
  "reinitialisation.faitTexte": "You can sign in with your new password.",

  "comptes.titre": "Accounts and access",
  "comptes.sousTitre":
    "Approve requests, assign scopes, unblock a password.",
  "comptes.filtrer": "Filter by status",
  "comptes.tous": "All statuses",
  "comptes.videTitre": "No account with this status",
  "comptes.videTexte": "Change the filter, or wait for an access request.",
  "comptes.examiner": "Review",
  "comptes.approuver": "Approve",
  "comptes.refuser": "Refuse",
  "comptes.suspendre": "Suspend",
  "comptes.reactiver": "Reactivate",
  "comptes.reinitialiser": "Reset password",
  "comptes.horsPortee": "Outside your reach",
  "comptes.roleAttribue": "Assigned profile",
  "comptes.agentRattache": "Linked field agent",
  "comptes.choisirAgent": "Select an agent",
  "comptes.agence": "Branch",
  "comptes.region": "Region",
  "comptes.motifRefus": "Reason, if refused",
  "comptes.motifAide": "It will appear in the email sent to the applicant.",
  "comptes.perimetreManquant":
    "With no branch or region, this supervisor would see the output of all 181 branches. The platform will refuse their requests until a scope is assigned.",
  "comptes.approuve": "Access opened for {nom}.",
  "comptes.refuse": "Request from {nom} refused.",
  "comptes.suspendu": "Account of {nom} suspended.",
  "comptes.reactive": "Account of {nom} reactivated.",
  "comptes.provisoire":
    "Temporary password for {nom}: {motDePasse}. Pass it on verbally, it must be replaced at the next sign-in.",
  "comptes.echec": "The operation failed.",

  "affectation.titre": "Route assignment",
  "affectation.sousTitre":
    "The agent reports in: record the routes you hand over, then print their field sheet.",
  "affectation.agentEtJournee": "Agent and working day",
  "affectation.agent": "Field agent",
  "affectation.choisirAgent": "Select an agent",
  "affectation.aucunAgentActif":
    "No active agent is registered. Create one from the “Agents” screen before assigning a route.",
  "affectation.journee": "Working day",
  "affectation.consignes": "Instructions (optional)",
  "affectation.consignesExemple": "Priority area, meeting point…",
  "affectation.itinerairesConfies": "Assigned routes",
  "affectation.rechercheAide": "Search by code, branch or label.",
  "affectation.recherchePlaceholder": "Route code, e.g. 131227 — or branch name",
  "affectation.aucunSelectionne": "No route selected",
  "affectation.aucunSelectionneAide":
    "Search for a route above to hand it to the agent.",
  "affectation.valider": "Assign and generate the sheet",
  "affectation.validerAide":
    "One sheet line will be created for every customer on the selected routes.",
  "affectation.enregistree": "Assignment saved",
  "affectation.imprimer": "Print the sheet",
  "affectation.retirer": "Remove",
  "affectation.clients": "{n} customer(s)",
  "affectation.resume": "{i} route(s) · {c} customer(s) to canvass",
  "affectation.dejaPortes": "Routes this agent already carries",
  "affectation.dejaPortesAide":
    "A strong collector takes several: add as many as needed, their figures will update.",

  "bordereau.titre": "Collection sheet",
  "bordereau.sousTitre": "Record here what each agent achieved in the field.",
  "bordereau.cadreSurItineraires":
    "Sheet framed on routes {codes}, announced at sign-in.",
  "bordereau.toutAfficher": "Show everything",
  "bordereau.verifier": "Check against reference data",
  "bordereau.exporterCsv": "Export CSV",
  "bordereau.exporterPdf": "Export PDF",
  "bordereau.client": "Customer",
  "bordereau.refGeo": "Geo ref.",
  "bordereau.itineraire": "Route",
  "bordereau.compteur": "Meter",
  "bordereau.numeroCollecte": "Collected no.",
  "bordereau.statut": "Status",
  "bordereau.verification": "Verification",
  "bordereau.date": "Date",
  "bordereau.action": "Action",
  "bordereau.saisir": "Record",
  "bordereau.vide": "Nothing to show",
  "bordereau.videAide":
    "Narrow your filters, or assign a route to an agent to generate their sheet.",
  "bordereau.selection": "{n} line(s) selected",
  "bordereau.appliquer": "Apply",
  "bordereau.annulerSelection": "Clear selection",
  "bordereau.rechercheePlaceholder": "Name, contract, meter or geographic reference…",
  "bordereau.total": "{premier}–{dernier} of {total} line(s)",

  "saisie.titre": "Record the agent's visit",
  "saisie.resultat": "Visit outcome",
  "saisie.numero": "WhatsApp number collected",
  "saisie.numeroObligatoire": "WhatsApp number collected (required)",
  "saisie.numeroAide": "The number will be normalised to international format.",
  "saisie.numeroManquant":
    "A customer recorded as signed up must come with the collected number.",
  "saisie.origine": "Sign-up channel",
  "saisie.observation": "Note",
  "saisie.observationExemple": "Agent's remark, detail about the visit…",
  "saisie.echec": "Saving failed.",

  "dashboard.titre": "Dashboard",
  "dashboard.sousTitre": "Progress of the WhatsApp collection campaign.",
  "dashboard.periode": "Observed period",
  "dashboard.jours7": "7 days",
  "dashboard.jours14": "14 days",
  "dashboard.jours30": "30 days",
  "dashboard.mois3": "3 months",
  "dashboard.chargement": "Loading indicators…",
  "dashboard.vsPrecedent": "vs previous period",
  "dashboard.stable": "steady",
  "dashboard.pasDeComparaison": "No comparison available",

  "kpi.lignes_traitees": "Customers canvassed",
  "kpi.abonnements": "Sign-ups declared",
  "kpi.abonnements_confirmes": "Sign-ups confirmed",
  "kpi.taux_conversion": "Conversion rate",
  "kpi.taux_fiabilite": "Declaration reliability",

  "graphique.evolution.titre": "Collection trend",
  "graphique.evolution.sousTitre":
    "What agents canvassed, what they declared, and what the reference data confirms.",
  "graphique.voirDonnees": "View data",
  "graphique.voirGraphique": "View chart",
  "graphique.jour": "Day",
  "serie.collectes": "Customers canvassed",
  "serie.abonnements": "Sign-ups declared",
  "serie.confirmes": "Sign-ups confirmed",

  "repartition.titre": "Breakdown by status",
  "repartition.sousTitre": "{n} line(s) over the period",
  "repartition.vide": "No data for this period",
  "repartition.videAide": "Widen the period or record the agents' work.",

  "couverture.titre": "Route coverage",
  "couverture.sousTitre": "Share of customers already canvassed on each round.",
  "couverture.vide": "No route worked yet",
  "couverture.videAide": "Assign a route to an agent to track its coverage here.",
  "couverture.restants": "{n} customer(s) left",
  "couverture.termine": "route complete",
  "couverture.abonnements": "{n} sign-up(s)",

  "classement.titre": "Agent performance",
  "classement.sousTitre":
    "Basis for the review meeting: volume, conversion and reliability.",
  "classement.agent": "Agent",
  "classement.demarches": "Canvassed",
  "classement.abonnements": "Sign-ups",
  "classement.confirmes": "Confirmed",
  "classement.conversion": "Conversion",
  "classement.fiabilite": "Reliability",
  "classement.vide": "No activity over the period",
  "classement.videAide": "Figures appear as soon as the first sheet is recorded.",
  "classement.fiabiliteFaible":
    "A large share of declared sign-ups is not confirmed by the reference data.",

  "agents.titre": "Field agents",
  "agents.sousTitre": "The collectors you hand routes to.",
  "agents.enregistrer": "Register an agent",
  "agents.repertoire": "Directory",
  "agents.nombre": "{n} agent(s) registered",
  "agents.matricule": "Staff ID",
  "agents.nomComplet": "Full name",
  "agents.telephone": "Phone",
  "agents.zone": "Home branch",
  "agents.region": "Region",
  "agents.photo": "Profile photo",
  "agents.photoAide": "JPEG, PNG or WebP — 4 MB maximum.",
  "agents.desactiver": "Take out of service",
  "agents.reactiver": "Put back in service",
  "agents.vide": "No agent registered",
  "agents.videAide": "Create a first agent so you can assign routes to them.",
  "agents.mentionHistorique":
    "An agent is never deleted: their past sheets are the basis of their pay.",
  "agents.voirPortefeuille": "View portfolio",

  "portefeuille.titre": "My space",
  "portefeuille.titreAutre": "{nom}'s portfolio",
  "portefeuille.sousTitre": "Your routes and figures for the period.",
  "portefeuille.itineraires": "Assigned routes",
  "portefeuille.aucun": "No route over the period",
  "portefeuille.aucunAide":
    "Your supervisor will hand you some at the next briefing.",
  "portefeuille.traites": "Canvassed",
  "portefeuille.affectes": "Customers assigned",
  "portefeuille.enAttente": "Awaiting verification",
  "portefeuille.mentionSaisie":
    "Your figures are entered by your supervisor from the paper sheet, then checked against the SOCADEL reference data.",

  "import.titre": "Import and export",
  "import.sousTitre":
    "Hand the template to your agents, then import their completed sheets.",
  "import.modeleTitre": "Field sheet template",
  "import.modeleSousTitre": "The blank workbook agents fill in.",
  "import.modeleTexte":
    "Its headers are exactly the ones the importer reads, and the Status and Channel columns offer closed lists: a file produced from this template will never be rejected for unexpected columns.",
  "import.telechargerModele": "Download the template (.xlsx)",
  "import.deposerTitre": "Import a completed sheet",
  "import.deposerSousTitre": "You will see a preview before anything is saved.",
  "import.journee": "Collection day",
  "import.journeeAide": "The date the visits took place.",
  "import.agentFacultatif": "Agent concerned (optional)",
  "import.nonPrecise": "Not specified",
  "import.fichier": "Sheet file",
  "import.formats": "Accepted formats: Excel (.xlsx, .xls) and CSV. 25 MB maximum.",
  "import.analyse": "Analysing…",
  "import.apercuTitre": "Check before importing",
  "import.lignesLues": "Lines read",
  "import.lignesRetenues": "Lines kept",
  "import.lignesRejetees": "Lines rejected",
  "import.importer": "Import {n} line(s)",
  "import.apercuLignes": "Preview of the first {n} line(s)",
  "import.controle": "Check",
  "import.ok": "OK",
  "import.rejet": "Rejected",
  "import.avertissement": "Warning",
  "import.colonnesDetectees": "Columns detected: {liste}",
  "import.colonnesManquantes":
    "Required column(s) missing: {liste}. Start again from the sheet template to be sure of the expected headers.",
  "import.aucuneLigne":
    "No usable line in this file: the import cannot proceed as is.",
  "import.rejetsAvertis":
    "{n} line(s) will be skipped. The others will be imported normally.",
  "import.termine": "Import complete: {creees} line(s) saved",
  "import.ignorees": ", {n} skipped",
  "import.voirAnomalies": "View the {n} issue(s)",
  "import.echec": "The import failed.",
  "import.echecAnalyse": "The file could not be analysed.",
  "export.tronque":
    "The export hit the line ceiling. Narrow your filters for a complete file.",
  "export.echec": "The export failed.",

  "itineraires.titre": "Routes",
  "itineraires.sousTitre": "Find a route and print its collection sheet.",
  "itineraires.recherchePlaceholder":
    "Route code, branch or label — at least 2 characters",
  "itineraires.invite": "Search for a route",
  "itineraires.inviteAide": "Enter its code — 131227 for example — or its branch name.",
  "itineraires.bordereauPdf": "Field sheet (PDF)",
  "itineraires.territoireInconnu": "Territory not recorded",
  "itineraires.echecPdf": "The sheet could not be generated.",

  "verification.resultat":
    "{examinees} line(s) checked: {confirmees} confirmed, {infirmees} contradicted, {introuvables} not found in the reference data.",
  "verification.echec": "The check failed.",
  "lot.resultat": "{n} line(s) updated.",
  "lot.resultatPartiel":
    "{modifiees} line(s) updated. {ignorees} line(s) need individual entry (a sign-up requires the collected number).",
  "lot.echec": "The bulk update failed.",

  "statut.A_TRAITER": "To do",
  "statut.A_TRAITER.aide": "The agent has not visited this customer yet",
  "statut.ABONNE": "Signed up",
  "statut.ABONNE.aide":
    "The customer signed up to receive their bill on WhatsApp",
  "statut.NON_ABONNE": "Not signed up",
  "statut.NON_ABONNE.aide": "Customer met, but no sign-up obtained",
  "statut.INJOIGNABLE": "Unreachable",
  "statut.INJOIGNABLE.aide": "Number or address not reachable",
  "statut.ABSENT": "Absent",
  "statut.ABSENT.aide": "Nobody home at the time of the visit",
  "statut.REFUS": "Refused",
  "statut.REFUS.aide": "The customer declined to give their number",
  "statut.DOUBLON": "Duplicate",
  "statut.DOUBLON.aide": "Customer already handled on another route",

  "verdict.NON_VERIFIE": "Not checked",
  "verdict.NON_VERIFIE.aide":
    "Declaration not yet checked against SOCADEL reference data",
  "verdict.CONFIRME": "Confirmed",
  "verdict.CONFIRME.aide":
    "The reference data backs the declaration: the line is payable",
  "verdict.INFIRME": "Contradicted",
  "verdict.INFIRME.aide": "The reference data contradicts the declaration",
  "verdict.INTROUVABLE": "Not found",
  "verdict.INTROUVABLE.aide":
    "This contract does not appear in the SOCADEL reference data",

  "responsable.TERRAIN": "Field agent",
  "responsable.CHATBOT": "WhatsApp chatbot",
  "responsable.CSC": "Customer service centre",
  "responsable.AUTRES": "Other channel",

  "theme.clair": "Light",
  "theme.sombre": "Dark",
  "theme.systeme": "System",
  "theme.basculer": "Switch theme",
  "langue.basculer": "Switch language",
};

export const MESSAGES: Record<Langue, Record<Cle, string>> = { fr, en };

/**
 * Remplace les jetons `{nom}` par leur valeur.
 *
 * Volontairement minimal : pas de pluriel automatique ni de format ICU. Les
 * libellés portent « (s) », ce qui reste correct en français comme en anglais
 * et évite d'embarquer une bibliothèque pour une poignée de chaînes.
 */
export function interpoler(
  modele: string,
  valeurs?: Record<string, string | number>,
): string {
  if (!valeurs) return modele;
  return modele.replace(/\{(\w+)\}/g, (correspondance, cle) =>
    cle in valeurs ? String(valeurs[cle]) : correspondance,
  );
}
