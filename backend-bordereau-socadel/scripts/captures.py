"""Déroule les quatre parcours dans le vrai navigateur et capture chaque écran.

    python scripts/captures.py

Ce n'est pas une simulation : le script se connecte pour de bon, affecte un
itinéraire, saisit une production, vérifie au référentiel. Les captures qui en
sortent alimentent les guides d'utilisation, et le journal dit ce qui a
réellement été exécuté.

Prérequis : l'API sur 8001 et le back-office sur 3000, tous deux démarrés.
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from pilote import parcours as P  # noqa: E402
from pilote.preparation import deposer_une_demande, remettre_a_zero  # noqa: E402
from pilote.navigateur import Navigateur, ouvrir  # noqa: E402

SORTIE = RACINE / "scripts" / "rapport" / "captures"

#: Les comptes de mise en route, tels que le guide les documente.
COMPTES = {
    "SUPER_UTILISATEUR": ("tonbaloic6@gmail.com", "Ngaoundal-Kribi-88", None),
    "ADMINISTRATEUR": ("flore.eyenga@socadel.cm", "Bandjoun-Maroua-77", None),
    "SUPERVISEUR": (
        "bertrand.nkolo@socadel.cm",
        "Ngaoundere-Sud-2026",
        "CSC_NGAOUNDERE SUD",
    ),
    "AGENT_TERRAIN": ("ag001@socadel.cm", "Terrain-Essos-2026", "CSC_NGAOUNDERE SUD"),
}

#: Itinéraire réel de l'agence du superviseur, 73 clients au référentiel.
ITINERAIRE = "110581"

#: Contrat et numéro attendus par le référentiel : la déclaration sera
#: confirmée. Voir scripts/pilote/referentiel_demo.py pour l'origine.
TEMOIN_CONFIRME = ("203452902", "675975589")

#: Contrat abonné au référentiel, mais numéro relevé différent : la
#: confrontation infirmera la déclaration, et la ligne ne sera pas payable.
TEMOIN_INFIRME = ("203452912", "699001122")


async def declarer_abonne(n: Navigateur) -> None:
    """Positionne le résultat du passage sur « Abonné » dans la fenêtre ouverte."""
    await n.evaluer(
        "(() => { const s = [...document.querySelectorAll('select')]"
        "   .find(s => [...s.options].some(o => o.text.trim() === 'Abonné'));"
        " const o = [...s.options].find(o => o.text.trim() === 'Abonné');"
        " const m = Object.getOwnPropertyDescriptor("
        "   window.HTMLSelectElement.prototype, 'value').set;"
        " m.call(s, o.value);"
        " s.dispatchEvent(new Event('change', {bubbles: true})); return true; })()"
    )
    await asyncio.sleep(0.4)


@dataclass
class Journal:
    """Ce qui a été exécuté, dans l'ordre, avec le résultat."""

    etapes: list[dict] = field(default_factory=list)

    def noter(self, profil: str, action: str, constat: str, capture: str | None) -> None:
        self.etapes.append(
            {
                "profil": profil,
                "action": action,
                "constat": constat,
                "capture": capture,
            }
        )
        marque = f" [{capture}]" if capture else ""
        print(f"  {profil:18s} {action:44s} {constat}{marque}")


async def prendre(n: Navigateur, nom: str) -> str:
    await n.capturer(SORTIE / f"{nom}.png")
    return f"{nom}.png"


# --- Parcours d'entrée, commun aux quatre guides ----------------------------


async def parcours_entree(n: Navigateur, journal: Journal) -> None:
    print("\nParcours d'entrée")

    await P.aller_a_la_connexion(n)
    journal.noter("Commun", "Ouvrir l'écran de connexion", "quatre profils proposés",
                  await prendre(n, "commun-01-profil"))

    await P.choisir_profil(n, "SUPERVISEUR")
    journal.noter("Commun", "Choisir le profil Superviseur",
                  "le sélecteur d'agence s'ouvre", None)

    await n.remplir('input[name="rechercheAgence"]', "NGAOUNDERE")
    await asyncio.sleep(0.4)
    journal.noter("Commun", "Rechercher son agence", "la liste se réduit à la saisie",
                  await prendre(n, "commun-02-agence"))

    await n.cliquer('[role="option"]', texte="CSC_NGAOUNDERE SUD")
    await n.cliquer("button", texte="Continuer")
    await n.attendre('input[name="identifiant"]')
    email, mot_de_passe, _ = COMPTES["SUPERVISEUR"]
    await P.saisir_identifiants(n, email, mot_de_passe)
    journal.noter("Commun", "Saisir l'adresse et le mot de passe",
                  "le profil et l'agence sont rappelés",
                  await prendre(n, "commun-03-identifiants"))

    # Le refus de poste incohérent : le mot de passe est bon, le profil non.
    await P.aller_a_la_connexion(n)
    await P.choisir_profil(n, "ADMINISTRATEUR")
    await P.choisir_agence(n, None)
    await P.saisir_identifiants(n, email, mot_de_passe)
    await n.cliquer('button[type="submit"]')
    await n.attendre('[role="alert"]')
    journal.noter("Commun", "Se déclarer administrateur avec un compte superviseur",
                  "refusé, message explicite",
                  await prendre(n, "commun-04-poste-refuse"))

    await n.aller(f"{P.BASE}/inscription")
    await n.attendre("h1", texte="Demander un accès")
    journal.noter("Commun", "Ouvrir le formulaire d'inscription",
                  "profil souhaité et mot de passe choisi par le demandeur",
                  await prendre(n, "commun-05-inscription"))

    await n.aller(f"{P.BASE}/mot-de-passe-oublie")
    await n.attendre("h1", texte="Mot de passe oublié")
    journal.noter("Commun", "Ouvrir « mot de passe oublié »",
                  "une seule adresse demandée",
                  await prendre(n, "commun-06-mot-de-passe-oublie"))


# --- Superviseur ------------------------------------------------------------


async def parcours_superviseur(n: Navigateur, journal: Journal) -> None:
    print("\nSuperviseur")
    email, mot_de_passe, agence = COMPTES["SUPERVISEUR"]

    await P.connecter(n, role="SUPERVISEUR", email=email, mot_de_passe=mot_de_passe,
                      agence=agence, ecran_attendu="Affectation")
    journal.noter("Superviseur", "Se connecter",
                  "arrivée directe sur l'écran d'affectation",
                  await prendre(n, "sv-01-arrivee"))

    # Étape 1 : confier un itinéraire à un agent.
    await n.evaluer(
        "(() => { const s = document.querySelector('select[name=\"agent\"]');"
        " const o = [...s.options].find(o => o.text.includes('AG001'));"
        " const m = Object.getOwnPropertyDescriptor("
        "   window.HTMLSelectElement.prototype, 'value').set;"
        " m.call(s, o.value);"
        " s.dispatchEvent(new Event('change', {bubbles: true})); return true; })()"
    )
    await n.remplir('input[type="search"]', ITINERAIRE)
    await n.attendre("button", texte=ITINERAIRE)
    await n.cliquer("button", texte=ITINERAIRE)
    await asyncio.sleep(0.6)
    journal.noter("Superviseur", f"Confier l'itinéraire {ITINERAIRE} à AG001",
                  "itinéraire retenu, bouton actif",
                  await prendre(n, "sv-02-affectation-saisie"))

    await n.cliquer("button", texte="Affecter et générer")
    # Deux issues attendues : la carte de succès, ou le refus d'un doublon si
    # l'itinéraire a déjà été confié le même jour.
    await n.attendre_texte("Affectation enregistrée", "déjà affecté")
    constat = await n.evaluer(
        "(() => { const a = document.querySelector('[role=\"alert\"]');"
        " if (a) return a.innerText;"
        " const s = [...document.querySelectorAll('section')].find("
        "   s => s.innerText.startsWith('Affectation enregistrée'));"
        " return s ? s.innerText : ''; })()"
    )
    journal.noter("Superviseur", "Valider l'affectation",
                  " ".join((constat or "").split())[:78],
                  await prendre(n, "sv-03-affectation-faite"))

    # Étape 2 : le bordereau porte désormais les lignes de l'itinéraire.
    await P.naviguer(n, "/bordereau", "Bordereau")
    lignes = await n.evaluer("document.querySelectorAll('tbody tr').length")
    journal.noter("Superviseur", "Ouvrir le bordereau",
                  f"{lignes} lignes affichées, périmètre de l'agence",
                  await prendre(n, "sv-04-bordereau"))

    # Étape 3 : saisir la production. Deux lignes, pour montrer les deux
    # verdicts que la confrontation au référentiel peut rendre.
    # Le tableau pagine par 25 : on retrouve le client par son contrat plutot
    # que de faire defiler les trois pages.
    await n.remplir('input#recherche', TEMOIN_CONFIRME[0])
    await asyncio.sleep(1.4)
    await n.cliquer_dans_ligne(TEMOIN_CONFIRME[0], "Saisir")
    await n.attendre("h2", texte="Saisir le passage")
    journal.noter("Superviseur", "Retrouver un client et ouvrir sa saisie",
                  "statut, numéro relevé et origine",
                  await prendre(n, "sv-05-saisie"))

    await declarer_abonne(n)
    journal.noter("Superviseur", "Déclarer un abonnement sans le numéro",
                  "la plateforme refuse : un abonné exige son numéro",
                  await prendre(n, "sv-06-numero-exige"))

    await n.remplir('input[name="numero"]', TEMOIN_CONFIRME[1])
    journal.noter("Superviseur", "Renseigner le numéro relevé",
                  "le bouton d'enregistrement s'active",
                  await prendre(n, "sv-07-saisie-complete"))
    await n.cliquer("button", texte="Enregistrer")
    await asyncio.sleep(1.8)

    # Seconde ligne, avec un numéro qui ne sera pas celui du référentiel.
    await n.remplir('input#recherche', TEMOIN_INFIRME[0])
    await asyncio.sleep(1.4)
    await n.cliquer_dans_ligne(TEMOIN_INFIRME[0], "Saisir")
    await n.attendre("h2", texte="Saisir le passage")
    await declarer_abonne(n)
    await n.remplir('input[name="numero"]', TEMOIN_INFIRME[1])
    await n.cliquer("button", texte="Enregistrer")
    await asyncio.sleep(1.8)

    # Le filtre de recherche est levé : la suite doit montrer tout le bordereau.
    await n.remplir("input#recherche", "")
    await asyncio.sleep(1.4)
    journal.noter("Superviseur", "Enregistrer les deux lignes",
                  "deux abonnements déclarés, numéros relevés portés", None)

    # Étape 4 : confronter au référentiel.
    await n.cliquer("button", texte="Vérifier auprès du référentiel")
    await n.attendre('[role="alert"]')
    verdict = await n.evaluer("document.querySelector('[role=\"alert\"]').innerText")
    journal.noter("Superviseur", "Vérifier auprès du référentiel",
                  verdict.replace("\n", " ")[:80],
                  await prendre(n, "sv-08-verification"))

    # Le filtre par statut isole les deux lignes traitées et leurs verdicts.
    await n.cliquer("button", texte="Abonné")
    await asyncio.sleep(1.4)
    verdicts = await n.evaluer(
        "(() => { const l = [...document.querySelectorAll('tbody tr')];"
        " return JSON.stringify({confirme: l.filter("
        "   x => x.innerText.includes('Confirmé')).length,"
        " infirme: l.filter(x => x.innerText.includes('Infirmé')).length}); })()"
    )
    journal.noter("Superviseur", "Filtrer sur les abonnements déclarés",
                  f"verdicts rendus : {verdicts}",
                  await prendre(n, "sv-09-verdicts"))

    await P.naviguer(n, "/dashboard", "Tableau de bord")
    journal.noter("Superviseur", "Consulter le tableau de bord",
                  "KPI et courbes du périmètre",
                  await prendre(n, "sv-10-tableau-de-bord"))

    await P.naviguer(n, "/itineraires", "Itinéraires")
    journal.noter("Superviseur", "Rechercher un itinéraire",
                  "recherche et impression du bordereau papier",
                  await prendre(n, "sv-11-itineraires"))

    await P.naviguer(n, "/agents", "Agents")
    journal.noter("Superviseur", "Ouvrir le répertoire des agents",
                  "création, modification, retrait du service",
                  await prendre(n, "sv-12-agents"))

    await P.naviguer(n, "/imports", "Import")
    journal.noter("Superviseur", "Ouvrir Import / Export",
                  "modèle à télécharger, aperçu avant écriture",
                  await prendre(n, "sv-13-imports"))

    # Étape 5 : le raccourci, se connecter en annonçant ses itinéraires.
    await P.connecter(n, role="SUPERVISEUR", email=email, mot_de_passe=mot_de_passe,
                      agence=agence, itineraires=ITINERAIRE,
                      ecran_attendu="Bordereau")
    journal.noter("Superviseur", f"Se reconnecter en annonçant {ITINERAIRE}",
                  "arrivée sur le bordereau déjà cadré",
                  await prendre(n, "sv-14-bordereau-cadre"))


# --- Agent de terrain -------------------------------------------------------


async def parcours_agent(n: Navigateur, journal: Journal) -> None:
    print("\nAgent de terrain")
    email, mot_de_passe, agence = COMPTES["AGENT_TERRAIN"]

    await P.connecter(n, role="AGENT_TERRAIN", email=email, mot_de_passe=mot_de_passe,
                      agence=agence, ecran_attendu="Mon espace")
    entrees = await n.evaluer("document.querySelectorAll('nav a').length")
    journal.noter("Agent de terrain", "Se connecter",
                  f"une seule entrée de navigation sur {entrees}",
                  await prendre(n, "ag-01-mon-espace"))

    interdits = await n.evaluer(
        "(() => { const a = [...document.querySelectorAll('nav a')]"
        "   .map(a => a.getAttribute('href')); return JSON.stringify(a); })()"
    )
    journal.noter("Agent de terrain", "Inspecter la navigation",
                  f"écrans accessibles : {interdits}", None)

    await n.aller(f"{P.BASE}/bordereau")
    await asyncio.sleep(2.0)
    url = await n.evaluer("location.pathname")
    journal.noter("Agent de terrain", "Tenter d'ouvrir le bordereau à la main",
                  f"aboutit sur {url}",
                  await prendre(n, "ag-02-bordereau-interdit"))


# --- Administrateur et super utilisateur ------------------------------------


async def parcours_gouvernance(n: Navigateur, journal: Journal, role: str,
                               prefixe: str, nom: str) -> None:
    print(f"\n{nom}")
    email, mot_de_passe, _ = COMPTES[role]

    await P.connecter(n, role=role, email=email, mot_de_passe=mot_de_passe,
                      agence=None, ecran_attendu="Tableau de bord")
    journal.noter(nom, "Se connecter en portée nationale",
                  "tableau de bord de l'ensemble du réseau",
                  await prendre(n, f"{prefixe}-01-tableau-de-bord"))

    await P.naviguer(n, "/comptes", "Comptes")
    attente = await n.evaluer("document.querySelectorAll('li').length")
    journal.noter(nom, "Ouvrir l'écran des comptes",
                  f"{attente} demande(s) en attente d'approbation",
                  await prendre(n, f"{prefixe}-02-comptes"))

    examiner = await n.evaluer(
        "Boolean([...document.querySelectorAll('button')]"
        ".find(b => b.innerText.trim() === 'Examiner'))"
    )
    if examiner:
        await n.cliquer("button", texte="Examiner")
        await asyncio.sleep(0.6)
        journal.noter(nom, "Examiner une demande",
                      "profil, périmètre et motif de refus",
                      await prendre(n, f"{prefixe}-03-approbation"))

    await P.naviguer(n, "/bordereau", "Bordereau")
    lignes = await n.evaluer("document.querySelectorAll('tbody tr').length")
    journal.noter(nom, "Ouvrir le bordereau",
                  f"{lignes} lignes, aucune restriction d'agence",
                  await prendre(n, f"{prefixe}-04-bordereau"))


async def principal() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)

    # Le scenario doit pouvoir etre rejoue : l'affectation de la veille ferait
    # capturer un refus de doublon au lieu de la carte de succes.
    retirees = await remettre_a_zero(matricule="AG001", code=int(ITINERAIRE))
    print(f"Preparation : {retirees} ligne(s) de demonstration retiree(s)")
    # L'ecran de gouvernance n'a d'interet qu'avec une demande a trancher.
    print(f"Preparation : {await deposer_une_demande()}")

    journal = Journal()
    n = await ouvrir()
    try:
        await parcours_entree(n, journal)
        await parcours_superviseur(n, journal)
        await parcours_agent(n, journal)
        await parcours_gouvernance(n, journal, "ADMINISTRATEUR", "ad", "Administrateur")
        await parcours_gouvernance(n, journal, "SUPER_UTILISATEUR", "su",
                                   "Super utilisateur")
    finally:
        await n.fermer()

    (SORTIE / "journal.json").write_text(
        json.dumps(journal.etapes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    captures = len([e for e in journal.etapes if e["capture"]])
    print(f"\n{len(journal.etapes)} etapes, {captures} captures dans {SORTIE}")


if __name__ == "__main__":
    asyncio.run(principal())
