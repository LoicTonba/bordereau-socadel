"""Initialisation de la base : compte superviseur et référentiel clients.

Usage :

    python scripts/seed.py --compte
    python scripts/seed.py --referentiel ../Documents/bordereau2.xlsx
    python scripts/seed.py --agents-demo

Le référentiel compte plus de 400 000 lignes : la lecture se fait en mode
streaming et l'écriture par paquets, pour ne jamais charger le classeur entier
en mémoire.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Iterator

# Le script s'exécute hors du package installé : on ajoute `src` au chemin.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import openpyxl  # noqa: E402

from bordereau.domain.entities import AgentTerrain, Client, Itineraire, Utilisateur  # noqa: E402
from bordereau.domain.enums import (  # noqa: E402
    CategorieClient,
    Role,
    StatutCompte,
    WhatsappStatus,
)
from bordereau.domain.value_objects import (  # noqa: E402
    CodeItineraire,
    NumeroTelephone,
    RefGeo,
    ServiceNo,
)
from bordereau.infrastructure.config.settings import get_settings  # noqa: E402
from bordereau.infrastructure.container import Container  # noqa: E402
from bordereau.infrastructure.db.base import Base  # noqa: E402

#: Paquet d'écriture. Compromis entre nombre d'allers-retours et mémoire.
TAILLE_LOT = 5_000


async def creer_tables(container: Container) -> None:
    """Crée le schéma si la base est vierge.

    En production, c'est Alembic qui fait foi ; cette création directe sert au
    démarrage rapide en développement.
    """
    async with container.moteur.begin() as connexion:
        await connexion.run_sync(Base.metadata.create_all)
    print("Schéma créé (ou déjà présent).")


async def semer_compte(container: Container) -> None:
    """Crée le compte superviseur défini dans la configuration."""
    settings = container.settings

    async with container.unit_of_work() as uow:
        existant = await uow.utilisateurs.par_identifiant(
            settings.superviseur_identifiant
        )
        if existant is not None:
            print(f"Compte « {existant.identifiant} » déjà présent, rien à faire.")
            return

        utilisateur = Utilisateur(
            identifiant=settings.superviseur_identifiant,
            nom_complet=settings.superviseur_nom,
            empreinte_mot_de_passe=container.hacheur.hacher(
                settings.superviseur_mot_de_passe
            ),
            role=Role.SUPERVISEUR,
        )
        await uow.utilisateurs.enregistrer(utilisateur)
        await uow.valider()

    print(
        f"Compte superviseur créé :\n"
        f"  identifiant  : {settings.superviseur_identifiant}\n"
        f"  mot de passe : {settings.superviseur_mot_de_passe}\n"
        f"Changez ce mot de passe avant toute mise en production."
    )


def _lire_referentiel(chemin: Path) -> Iterator[dict[str, Any]]:
    """Parcourt le classeur ligne à ligne, sans le charger entièrement."""
    classeur = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    try:
        feuille = classeur.worksheets[0]
        iterateur = feuille.iter_rows(values_only=True)

        entetes_brutes = next(iterateur, None)
        if entetes_brutes is None:
            return
        entetes = [str(e).strip().upper() if e else "" for e in entetes_brutes]

        for valeurs in iterateur:
            if valeurs[0] is None:
                continue
            yield dict(zip(entetes, valeurs, strict=False))
    finally:
        classeur.close()


def _vers_client(brute: dict[str, Any]) -> Client | None:
    """Construit un client depuis une ligne du référentiel.

    Les lignes sans identifiant de contrat exploitable sont écartées : elles
    ne pourraient être rattachées à aucune déclaration.
    """
    service_no = ServiceNo.parse_ou_none(
        brute.get("NIS_RAD") or brute.get("NUMERO_CONTRAT")
    )
    if service_no is None:
        return None

    statut_brut = str(brute.get("WHATSAPP_STATUS") or "not_checked").strip().lower()
    try:
        statut = WhatsappStatus(statut_brut)
    except ValueError:
        statut = WhatsappStatus.NOT_CHECKED

    return Client(
        service_no=service_no,
        nom=str(brute.get("FIRSTNAME") or "").strip() or "SANS NOM",
        ref_geo=RefGeo.parse_ou_none(brute.get("REF_GEO")),
        code_itineraire=CodeItineraire.parse_ou_none(brute.get("NUM_ITIN")),
        telephone=NumeroTelephone.parse_ou_none(
            brute.get("NUMERO_TELEPHONE") or brute.get("TELEPHONE")
        ),
        numero_compteur=_texte(brute.get("METER_NO")),
        region=_texte(brute.get("NOM_AREA")),
        division=_texte(brute.get("NOM_ZONA")),
        agence=_texte(brute.get("NOM_UNICOM")),
        mrc=_texte(brute.get("MRC")),
        categorie=CategorieClient.parse(brute.get("MARQUE_CLIENT")),
        segment=_texte(brute.get("SEGMENT_ZR")),
        whatsapp_status=statut,
    )


async def semer_referentiel(container: Container, chemin: Path) -> None:
    """Importe le référentiel clients et en déduit les itinéraires."""
    if not chemin.exists():
        print(f"Fichier introuvable : {chemin}")
        return

    print(f"Lecture de {chemin.name} (cela peut prendre plusieurs minutes)…")

    lot: list[Client] = []
    total = ignorees = 0
    # Les itinéraires ne figurent pas dans un onglet dédié : on les reconstruit
    # à la volée depuis les clients, avec leur rattachement territorial.
    itineraires: dict[int, dict[str, Any]] = {}

    async with container.unit_of_work() as uow:
        for brute in _lire_referentiel(chemin):
            client = _vers_client(brute)
            if client is None:
                ignorees += 1
                continue

            lot.append(client)

            if client.code_itineraire is not None:
                code = client.code_itineraire.valeur
                agregat = itineraires.setdefault(
                    code,
                    {
                        "region": client.region,
                        "division": client.division,
                        "agence": client.agence,
                        "mrc": client.mrc,
                        "nombre": 0,
                    },
                )
                agregat["nombre"] += 1

            if len(lot) >= TAILLE_LOT:
                total += await uow.clients.enregistrer_en_lot(lot)
                await uow.valider()
                lot.clear()
                print(f"  {total:>7} clients écrits…", end="\r")

        if lot:
            total += await uow.clients.enregistrer_en_lot(lot)
            await uow.valider()

        print(f"  {total} clients écrits, {ignorees} ligne(s) ignorée(s).")

        entites = [
            Itineraire(
                code=CodeItineraire(code),
                libelle=f"{donnees['agence'] or 'Itinéraire'} — {code}",
                region=donnees["region"],
                division=donnees["division"],
                agence=donnees["agence"],
                mrc=donnees["mrc"],
                nombre_clients=donnees["nombre"],
            )
            for code, donnees in itineraires.items()
        ]
        await uow.itineraires.enregistrer_en_lot(entites)
        await uow.valider()

    print(f"  {len(entites)} itinéraires déduits du référentiel.")


async def semer_comptes_acteurs(container: Container) -> None:
    """Ouvre un compte pour chacun des trois rôles.

    Les mots de passe sont ceux de la mise en route : chaque titulaire devra
    les remplacer à sa première connexion (drapeau `doit_changer_mot_de_passe`).
    """
    # L'adresse est portee ici plutot que deduite de l'identifiant : c'est
    # elle que l'ecran de connexion demande, elle doit donc etre lisible et
    # ressembler a une vraie adresse de service.
    comptes = [
        ("sudo", "TONBA Loic", Role.SUPER_UTILISATEUR,
         "tonbaloic6@gmail.com", "Ngaoundal-Kribi-88", None, None),
        ("admin", "EYENGA Flore", Role.ADMINISTRATEUR,
         "flore.eyenga@socadel.cm", "Bandjoun-Maroua-77", None, None),
        # Le superviseur recoit un perimetre : sans lui, la plateforme le
        # bloque plutot que de lui ouvrir les 181 agences.
        ("superviseur", "NKOLO Bertrand", Role.SUPERVISEUR,
         "bertrand.nkolo@socadel.cm", "Ngaoundere-Sud-2026", None,
         "CSC_NGAOUNDERE SUD"),
    ]

    async with container.unit_of_work() as uow:
        # Le compte agent est rattaché au premier agent du répertoire : sans
        # rattachement, la politique ABAC ne saurait pas quoi lui montrer.
        agents = await uow.agents.lister(actifs_seulement=True)
        if agents:
            comptes.append(
                (
                    agents[0].matricule.lower(),
                    agents[0].nom_complet,
                    Role.AGENT_TERRAIN,
                    f"{agents[0].matricule.lower()}@socadel.cm",
                    "Terrain-Essos-2026",
                    agents[0].id,
                    None,
                )
            )

        crees = []
        for identifiant, nom, role, email, mot_de_passe, agent_id, agence in comptes:
            if await uow.utilisateurs.par_identifiant(identifiant) is not None:
                continue
            await uow.utilisateurs.enregistrer(
                Utilisateur(
                    identifiant=identifiant,
                    nom_complet=nom,
                    email=email,
                    empreinte_mot_de_passe=container.hacheur.hacher(mot_de_passe),
                    role=role,
                    statut=StatutCompte.ACTIF,
                    agent_id=agent_id,
                    agence=agence,
                    doit_changer_mot_de_passe=True,
                )
            )
            crees.append((email, role.value, mot_de_passe))
        await uow.valider()

    if crees:
        print("Comptes ouverts :")
        for email, role, mot_de_passe in crees:
            print(f"  {role:18s} {email:28s} {mot_de_passe}")
    else:
        print("Comptes deja presents, rien a faire.")


async def semer_agents_demo(container: Container) -> None:
    """Crée quelques agents, pour disposer d'un jeu d'essai immédiat."""
    demos = (
        ("AG001", "MBALLA Jean Pierre", "+237677123456", "CSC_NSAM"),
        ("AG002", "NGONO Marie Claire", "+237696234567", "CSC_KRIBI"),
        ("AG003", "TCHOUMI Alain", "+237655345678", "CSC_BANDJOUN"),
    )

    cree = 0
    async with container.unit_of_work() as uow:
        for matricule, nom, telephone, zone in demos:
            if await uow.agents.par_matricule(matricule) is not None:
                continue
            await uow.agents.enregistrer(
                AgentTerrain(
                    matricule=matricule,
                    nom_complet=nom,
                    telephone=NumeroTelephone.parse_ou_none(telephone),
                    zone_rattachement=zone,
                )
            )
            cree += 1
        await uow.valider()

    print(f"{cree} agent(s) de démonstration créé(s).")


def _texte(valeur: Any) -> str | None:
    if valeur is None:
        return None
    texte = str(valeur).strip()
    return texte or None


async def principal() -> None:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument(
        "--tables", action="store_true", help="Créer le schéma de base"
    )
    analyseur.add_argument(
        "--compte", action="store_true", help="Créer le compte superviseur"
    )
    analyseur.add_argument(
        "--referentiel", type=Path, help="Chemin du classeur du référentiel clients"
    )
    analyseur.add_argument(
        "--agents-demo", action="store_true", help="Créer des agents d'essai"
    )
    analyseur.add_argument(
        "--acteurs",
        action="store_true",
        help="Ouvrir un compte pour chacun des trois rôles",
    )
    analyseur.add_argument(
        "--tout",
        action="store_true",
        help="Schéma + comptes + agents d'essai (sans le référentiel)",
    )
    arguments = analyseur.parse_args()

    container = Container(get_settings())
    try:
        if arguments.tables or arguments.tout:
            await creer_tables(container)
        if arguments.agents_demo or arguments.tout:
            await semer_agents_demo(container)
        if arguments.acteurs or arguments.tout:
            await semer_comptes_acteurs(container)
        if arguments.referentiel:
            await semer_referentiel(container, arguments.referentiel)

        if not any(
            (
                arguments.tables,
                arguments.compte,
                arguments.referentiel,
                arguments.agents_demo,
                arguments.acteurs,
                arguments.tout,
            )
        ):
            analyseur.print_help()
    finally:
        await container.fermer()


if __name__ == "__main__":
    asyncio.run(principal())
