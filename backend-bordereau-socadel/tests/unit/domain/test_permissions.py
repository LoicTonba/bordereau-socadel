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
    def test_le_super_utilisateur_a_tout(self) -> None:
        contexte = _contexte(Role.SUPER_UTILISATEUR)
        assert all(contexte.a(p) for p in Permission)

    def test_l_administrateur_gouverne_sans_tout_pouvoir(self) -> None:
        contexte = _contexte(Role.ADMINISTRATEUR)
        assert contexte.a(Permission.COMPTE_APPROUVER)
        assert contexte.a(Permission.COMPTE_REINITIALISER)
        assert contexte.a(Permission.PERIMETRE_DEFINIR)
        # Changer un role et administrer le referentiel engagent le
        # fonctionnement de la plateforme : cela reste chez NEXT LTD.
        assert not contexte.a(Permission.COMPTE_CHANGER_ROLE)
        assert not contexte.a(Permission.REFERENTIEL_ADMINISTRER)

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

    def test_un_superviseur_sans_perimetre_est_bloque(self) -> None:
        """SOCADEL compte 181 agences : un superviseur sans perimetre verrait
        la production de tout le pays."""
        contexte = _contexte(Role.SUPERVISEUR)

        with pytest.raises(AccesRefuse, match="rim"):
            restreindre(contexte, FiltreBordereau())

    def test_les_roles_a_portee_nationale_ne_sont_pas_restreints(self) -> None:
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
        assert peut_agir_sur_compte(
            contexte, contexte.utilisateur_id, Role.SUPERVISEUR
        )
        # Sur un pair, en revanche, non : la hierarchie est stricte.
        assert not peut_agir_sur_compte(contexte, uuid4(), Role.SUPERVISEUR)

    def test_la_hierarchie_est_strictement_descendante(self) -> None:
        admin = _contexte(Role.ADMINISTRATEUR)
        assert peut_agir_sur_compte(admin, uuid4(), Role.SUPERVISEUR)
        assert peut_agir_sur_compte(admin, uuid4(), Role.AGENT_TERRAIN)
        # Un administrateur SOCADEL ne touche ni a un pair, ni au super
        # utilisateur NEXT LTD qui lui a ouvert l'acces.
        assert not peut_agir_sur_compte(admin, uuid4(), Role.ADMINISTRATEUR)
        assert not peut_agir_sur_compte(admin, uuid4(), Role.SUPER_UTILISATEUR)

    def test_le_super_utilisateur_atteint_tous_les_rangs_inferieurs(self) -> None:
        sudo = _contexte(Role.SUPER_UTILISATEUR)
        for role in (Role.ADMINISTRATEUR, Role.SUPERVISEUR, Role.AGENT_TERRAIN):
            assert peut_agir_sur_compte(sudo, uuid4(), role)


class TestCompteAgent:
    def test_un_compte_agent_exige_un_rattachement(self) -> None:
        with pytest.raises(RegleMetierViolee, match="rattaché"):
            Utilisateur(
                identifiant="ag001",
                nom_complet="MBALLA Jean Pierre",
                email="ag001@socadel.cm",
                empreinte_mot_de_passe="x",
                role=Role.AGENT_TERRAIN,
            )

    def test_le_contexte_porte_les_attributs_du_compte(self) -> None:
        utilisateur = Utilisateur(
            identifiant="sup-est",
            nom_complet="Superviseur Est",
            email="sup.est@socadel.cm",
            empreinte_mot_de_passe="x",
            role=Role.SUPERVISEUR,
            region="DRE",
        )

        contexte = utilisateur.contexte_acces()

        assert contexte.role is Role.SUPERVISEUR
        assert contexte.region == "DRE"
        assert contexte.utilisateur_id == utilisateur.id
