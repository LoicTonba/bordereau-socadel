"""Tests de la politique d'habilitation : RBAC et ABAC."""

from __future__ import annotations

from uuid import uuid4

import pytest

from bordereau.application.dto import FiltreBordereau
from bordereau.domain.enums import Role
from bordereau.domain.errors import RegleMetierViolee
from bordereau.domain.securite import (
    AccesRefuse,
    ContexteAcces,
    Permission,
    peut_agir_sur_agent,
    peut_agir_sur_compte,
    restreindre,
)
from bordereau.domain.entities import Utilisateur

AGENT = uuid4()


def _contexte(role: Role, **kwargs) -> ContexteAcces:
    return ContexteAcces(utilisateur_id=uuid4(), role=role, **kwargs)


class TestRbac:
    def test_l_administrateur_a_tout(self) -> None:
        contexte = _contexte(Role.ADMINISTRATEUR)
        assert all(contexte.a(p) for p in Permission)

    def test_le_superviseur_pilote_mais_ne_gere_pas_les_comptes(self) -> None:
        contexte = _contexte(Role.SUPERVISEUR)

        assert contexte.a(Permission.ITINERAIRE_AFFECTER)
        assert contexte.a(Permission.BORDEREAU_DECLARER)
        assert contexte.a(Permission.AGENT_CREER)
        assert contexte.a(Permission.AGENT_SUPPRIMER)
        # La gestion des comptes de connexion reste à l'administrateur.
        assert not contexte.a(Permission.COMPTE_CREER)
        assert not contexte.a(Permission.COMPTE_SUPPRIMER)

    def test_l_agent_ne_fait_que_consulter(self) -> None:
        contexte = _contexte(Role.AGENT_TERRAIN, agent_id=AGENT)

        assert contexte.a(Permission.BORDEREAU_LIRE)
        assert contexte.a(Permission.ANALYTICS_CONSULTER)
        assert contexte.a(Permission.PROFIL_CONSULTER)

        # Tout le reste lui est fermé : sur la plateforme il ne fait que
        # regarder ses chiffres.
        for interdite in (
            Permission.BORDEREAU_DECLARER,
            Permission.BORDEREAU_EXPORTER,
            Permission.ITINERAIRE_AFFECTER,
            Permission.AGENT_CREER,
            Permission.AGENT_MODIFIER,
            Permission.IMPORT_EXECUTER,
            Permission.COMPTE_CREER,
        ):
            assert not contexte.a(interdite), interdite

    def test_exiger_leve_quand_la_permission_manque(self) -> None:
        contexte = _contexte(Role.AGENT_TERRAIN, agent_id=AGENT)
        with pytest.raises(AccesRefuse, match="AGENT_TERRAIN"):
            contexte.exiger(Permission.BORDEREAU_DECLARER)


class TestAbac:
    def test_l_agent_est_enferme_dans_sa_propre_production(self) -> None:
        contexte = _contexte(Role.AGENT_TERRAIN, agent_id=AGENT)

        # Il demande explicitement la production d'un autre agent.
        demande = FiltreBordereau(agent_ids=(uuid4(), uuid4()))
        obtenu = restreindre(contexte, demande)

        assert obtenu.agent_ids == (AGENT,), (
            "le périmètre demandé est écrasé, pas complété"
        )

    def test_le_perimetre_territorial_du_superviseur_prime(self) -> None:
        contexte = _contexte(Role.SUPERVISEUR, region="DRNEA")

        obtenu = restreindre(contexte, FiltreBordereau(region="DCUY"))

        assert obtenu.region == "DRNEA"

    def test_un_superviseur_national_garde_sa_demande(self) -> None:
        contexte = _contexte(Role.SUPERVISEUR)
        demande = FiltreBordereau(region="DCUY", recherche="MBALLA")

        assert restreindre(contexte, demande) == demande

    def test_l_administrateur_n_est_jamais_restreint(self) -> None:
        contexte = _contexte(Role.ADMINISTRATEUR)
        demande = FiltreBordereau(agent_ids=(uuid4(),), region="DCUY")

        assert restreindre(contexte, demande) == demande

    def test_un_compte_agent_sans_rattachement_ne_voit_rien(self) -> None:
        """Défense en profondeur : l'entité interdit déjà ce cas, mais si un
        tel contexte parvenait jusqu'ici, il ne doit pas tout ouvrir."""
        contexte = _contexte(Role.AGENT_TERRAIN, agent_id=None)

        with pytest.raises(AccesRefuse):
            restreindre(contexte, FiltreBordereau())


class TestPorteeSurLesFiches:
    def test_l_agent_ne_touche_pas_au_repertoire(self) -> None:
        contexte = _contexte(Role.AGENT_TERRAIN, agent_id=AGENT)
        # Pas même sa propre fiche : c'est le superviseur qui la tient.
        assert not peut_agir_sur_agent(contexte, AGENT)

    def test_le_superviseur_gere_le_repertoire(self) -> None:
        assert peut_agir_sur_agent(_contexte(Role.SUPERVISEUR), uuid4())

    def test_chacun_agit_sur_son_propre_compte(self) -> None:
        contexte = _contexte(Role.SUPERVISEUR)
        assert peut_agir_sur_compte(contexte, contexte.utilisateur_id)
        assert not peut_agir_sur_compte(contexte, uuid4())

    def test_l_administrateur_agit_sur_tous_les_comptes(self) -> None:
        assert peut_agir_sur_compte(_contexte(Role.ADMINISTRATEUR), uuid4())


class TestCompteAgent:
    def test_un_compte_agent_exige_un_rattachement(self) -> None:
        with pytest.raises(RegleMetierViolee, match="rattaché"):
            Utilisateur(
                identifiant="ag001",
                nom_complet="MBALLA Jean Pierre",
                empreinte_mot_de_passe="x",
                role=Role.AGENT_TERRAIN,
            )

    def test_le_contexte_porte_les_attributs_du_compte(self) -> None:
        utilisateur = Utilisateur(
            identifiant="sup-est",
            nom_complet="Superviseur Est",
            empreinte_mot_de_passe="x",
            role=Role.SUPERVISEUR,
            region="DRE",
        )

        contexte = utilisateur.contexte_acces()

        assert contexte.role is Role.SUPERVISEUR
        assert contexte.region == "DRE"
        assert contexte.utilisateur_id == utilisateur.id
